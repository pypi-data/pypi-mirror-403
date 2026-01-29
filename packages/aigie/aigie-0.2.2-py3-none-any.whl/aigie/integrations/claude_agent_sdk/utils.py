"""
Utility functions for Claude Agent SDK integration.
"""

from typing import Any, Dict, List, Optional, Union


def extract_text_from_content(content: Any) -> str:
    """
    Extract text content from various Claude message content formats.

    Args:
        content: Message content (str, list of blocks, or other)

    Returns:
        Extracted text as string
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif hasattr(block, 'text'):
                text_parts.append(block.text)
            elif isinstance(block, dict) and 'text' in block:
                text_parts.append(block['text'])
            elif hasattr(block, 'type') and block.type == 'text':
                text_parts.append(getattr(block, 'text', ''))
        return '\n'.join(text_parts)

    if hasattr(content, 'text'):
        return content.text

    return str(content)


def extract_tool_uses(content: Any) -> List[Dict[str, Any]]:
    """
    Extract tool use blocks from message content.

    Args:
        content: Message content

    Returns:
        List of tool use dicts with id, name, input
    """
    tool_uses = []

    if not isinstance(content, list):
        return tool_uses

    for block in content:
        if hasattr(block, 'type') and block.type == 'tool_use':
            tool_uses.append({
                'id': getattr(block, 'id', ''),
                'name': getattr(block, 'name', ''),
                'input': getattr(block, 'input', {}),
            })
        elif isinstance(block, dict) and block.get('type') == 'tool_use':
            tool_uses.append({
                'id': block.get('id', ''),
                'name': block.get('name', ''),
                'input': block.get('input', {}),
            })

    return tool_uses


def extract_tool_results(content: Any) -> List[Dict[str, Any]]:
    """
    Extract tool result blocks from message content.

    Args:
        content: Message content

    Returns:
        List of tool result dicts with tool_use_id, content, is_error
    """
    tool_results = []

    if not isinstance(content, list):
        return tool_results

    for block in content:
        if hasattr(block, 'type') and block.type == 'tool_result':
            tool_results.append({
                'tool_use_id': getattr(block, 'tool_use_id', ''),
                'content': getattr(block, 'content', ''),
                'is_error': getattr(block, 'is_error', False),
            })
        elif isinstance(block, dict) and block.get('type') == 'tool_result':
            tool_results.append({
                'tool_use_id': block.get('tool_use_id', ''),
                'content': block.get('content', ''),
                'is_error': block.get('is_error', False),
            })

    return tool_results


def serialize_message(message: Any, max_length: int = 2000) -> Dict[str, Any]:
    """
    Serialize a Claude message for tracing.

    Args:
        message: Claude message object
        max_length: Maximum length for content fields

    Returns:
        Serialized message dict
    """
    result = {
        'role': getattr(message, 'role', 'unknown'),
    }

    if hasattr(message, 'content'):
        content = message.content
        if isinstance(content, str):
            result['content'] = content[:max_length]
        elif isinstance(content, list):
            serialized_blocks = []
            for block in content[:10]:  # Limit blocks
                if hasattr(block, 'type'):
                    block_dict = {'type': block.type}
                    if block.type == 'text':
                        block_dict['text'] = getattr(block, 'text', '')[:max_length]
                    elif block.type == 'tool_use':
                        block_dict['id'] = getattr(block, 'id', '')
                        block_dict['name'] = getattr(block, 'name', '')
                        block_dict['input'] = str(getattr(block, 'input', {}))[:500]
                    elif block.type == 'tool_result':
                        block_dict['tool_use_id'] = getattr(block, 'tool_use_id', '')
                        block_dict['is_error'] = getattr(block, 'is_error', False)
                        content_str = str(getattr(block, 'content', ''))
                        block_dict['content'] = content_str[:500]
                    serialized_blocks.append(block_dict)
                elif isinstance(block, dict):
                    serialized_blocks.append({
                        k: str(v)[:500] for k, v in block.items()
                    })
            result['content'] = serialized_blocks
        else:
            result['content'] = str(content)[:max_length]

    # Add usage if present (for ResultMessage)
    if hasattr(message, 'usage'):
        usage = message.usage
        result['usage'] = {
            'input_tokens': getattr(usage, 'input_tokens', 0),
            'output_tokens': getattr(usage, 'output_tokens', 0),
            'cache_read_input_tokens': getattr(usage, 'cache_read_input_tokens', 0),
            'cache_creation_input_tokens': getattr(usage, 'cache_creation_input_tokens', 0),
        }

    if hasattr(message, 'total_cost_usd'):
        result['total_cost_usd'] = message.total_cost_usd

    if hasattr(message, 'model'):
        result['model'] = message.model

    return result


def serialize_messages(messages: List[Any], max_length: int = 2000) -> List[Dict[str, Any]]:
    """
    Serialize a list of Claude messages for tracing.

    Args:
        messages: List of Claude message objects
        max_length: Maximum length for content fields

    Returns:
        List of serialized message dicts
    """
    return [serialize_message(m, max_length) for m in messages]


def extract_usage(result_message: Any) -> Dict[str, int]:
    """
    Extract usage information from a ResultMessage.

    Args:
        result_message: Claude ResultMessage object

    Returns:
        Usage dict with token counts
    """
    usage = {
        'input_tokens': 0,
        'output_tokens': 0,
        'cache_read_input_tokens': 0,
        'cache_creation_input_tokens': 0,
    }

    if not result_message:
        return usage

    if hasattr(result_message, 'usage'):
        usage_obj = result_message.usage
        usage['input_tokens'] = getattr(usage_obj, 'input_tokens', 0)
        usage['output_tokens'] = getattr(usage_obj, 'output_tokens', 0)
        usage['cache_read_input_tokens'] = getattr(usage_obj, 'cache_read_input_tokens', 0)
        usage['cache_creation_input_tokens'] = getattr(usage_obj, 'cache_creation_input_tokens', 0)

    return usage


def is_result_message(message: Any) -> bool:
    """
    Check if a message is a ResultMessage (final message with usage/cost).

    Args:
        message: Message to check

    Returns:
        True if message is a ResultMessage
    """
    return hasattr(message, 'usage') or hasattr(message, 'total_cost_usd')


def get_message_type(message: Any) -> str:
    """
    Get the type of a Claude message.

    Args:
        message: Claude message object

    Returns:
        Message type string
    """
    if hasattr(message, '__class__'):
        return message.__class__.__name__

    if isinstance(message, dict):
        return message.get('type', 'unknown')

    return 'unknown'


def truncate_text(text: str, max_length: int = 2000, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
