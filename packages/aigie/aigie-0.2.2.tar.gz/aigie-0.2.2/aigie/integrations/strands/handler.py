"""
Strands Agents hook handler for Aigie SDK.

Implements HookProvider to automatically trace Strands agent invocations,
tool calls, LLM calls, and multi-agent orchestrations.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ...buffer import EventType
from .config import StrandsConfig
from .cost_tracking import calculate_strands_cost

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    try:
        from strands.hooks import (
            HookProvider,
            HookRegistry,
            BeforeInvocationEvent,
            AfterInvocationEvent,
            BeforeToolCallEvent,
            AfterToolCallEvent,
            BeforeModelCallEvent,
            AfterModelCallEvent,
            MessageAddedEvent,
            BeforeMultiAgentInvocationEvent,
            AfterMultiAgentInvocationEvent,
            BeforeNodeCallEvent,
            AfterNodeCallEvent,
        )
        from strands.agent.agent_result import AgentResult
        from strands.types.tools import ToolUse, ToolResult
    except ImportError:
        pass


class StrandsHandler:
    """
    Strands Agents handler for Aigie tracing.

    Implements HookProvider to automatically trace:
    - Agent invocations (BeforeInvocationEvent → AfterInvocationEvent)
    - Tool calls (BeforeToolCallEvent → AfterToolCallEvent)
    - LLM calls (BeforeModelCallEvent → AfterModelCallEvent)
    - Multi-agent orchestrations (BeforeMultiAgentInvocationEvent → AfterMultiAgentInvocationEvent)
    - Node executions (BeforeNodeCallEvent → AfterNodeCallEvent)

    Example:
        >>> from strands import Agent
        >>> from aigie.integrations.strands import StrandsHandler
        >>>
        >>> handler = StrandsHandler()
        >>> agent = Agent(tools=[...], hooks=[handler])
        >>> result = agent("What is the capital of France?")
    """

    def __init__(
        self,
        config: Optional[StrandsConfig] = None,
        trace_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """
        Initialize Strands handler.

        Args:
            config: Configuration for tracing behavior
            trace_name: Name for the trace (default: agent name)
            metadata: Additional metadata to attach
            tags: Tags to apply to trace and spans
            user_id: User ID for the trace
            session_id: Session ID for the trace
        """
        self.config = config or StrandsConfig.from_env()
        self.trace_name = trace_name
        self.metadata = metadata or {}
        self.tags = tags or []
        self.user_id = user_id
        self.session_id = session_id

        # State tracking
        self.trace_id: Optional[str] = None
        self.agent_span_id: Optional[str] = None
        self.tool_map: Dict[str, Dict[str, Any]] = {}  # tool_use_id -> {spanId, startTime}
        self.model_span_id: Optional[str] = None
        self.model_start_time: Optional[datetime] = None
        self.multi_agent_map: Dict[str, Dict[str, Any]] = {}  # orchestrator_id -> {spanId, startTime}
        self.node_map: Dict[str, Dict[str, Any]] = {}  # node_id -> {spanId, startTime}

        # Current context for parent relationships
        self._current_parent_span_id: Optional[str] = None
        self._parent_span_stack: List[str] = []  # Stack for nested multi-agent/nodes
        self._aigie = None

        # Statistics
        self._total_tool_calls = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost = 0.0
        
        # Error tracking
        self._has_errors = False
        self._error_messages: List[str] = []

    def _get_aigie(self):
        """Lazy load Aigie client."""
        if self._aigie is None:
            from ...client import get_aigie
            self._aigie = get_aigie()
        return self._aigie

    def register_hooks(self, registry: "HookRegistry") -> None:
        """
        Register hook callbacks with the Strands hook registry.

        This method is called by Strands when the handler is added to an agent.

        Args:
            registry: The hook registry to register callbacks with
        """
        if not self.config.enabled:
            return

        try:
            from strands.hooks import (
                BeforeInvocationEvent,
                AfterInvocationEvent,
                BeforeToolCallEvent,
                AfterToolCallEvent,
                BeforeModelCallEvent,
                AfterModelCallEvent,
                MessageAddedEvent,
                BeforeMultiAgentInvocationEvent,
                AfterMultiAgentInvocationEvent,
                BeforeNodeCallEvent,
                AfterNodeCallEvent,
            )
        except ImportError:
            logger.warning("[AIGIE] Strands hooks not available - cannot register callbacks")
            return

        # Core agent lifecycle
        if self.config.trace_agents:
            registry.add_callback(BeforeInvocationEvent, self._on_before_invocation)
            registry.add_callback(AfterInvocationEvent, self._on_after_invocation)
            registry.add_callback(MessageAddedEvent, self._on_message_added)

        # Tool execution
        if self.config.trace_tools:
            registry.add_callback(BeforeToolCallEvent, self._on_before_tool_call)
            registry.add_callback(AfterToolCallEvent, self._on_after_tool_call)

        # Model invocation
        if self.config.trace_llm_calls:
            registry.add_callback(BeforeModelCallEvent, self._on_before_model_call)
            registry.add_callback(AfterModelCallEvent, self._on_after_model_call)

        # Multi-agent
        if self.config.trace_multi_agent:
            registry.add_callback(BeforeMultiAgentInvocationEvent, self._on_before_multi_agent)
            registry.add_callback(AfterMultiAgentInvocationEvent, self._on_after_multi_agent)
            registry.add_callback(BeforeNodeCallEvent, self._on_before_node_call)
            registry.add_callback(AfterNodeCallEvent, self._on_after_node_call)

    # Core agent lifecycle hooks

    async def _on_before_invocation(self, event: "BeforeInvocationEvent") -> None:
        """Handle BeforeInvocationEvent - create trace and agent span."""
        if not self.config.enabled or not self.config.trace_agents:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            # Check if we're already in a trace (from context or previous invocation)
            # This allows multiple agent invocations to share the same trace
            existing_trace_id = None
            
            # Check Aigie context for existing trace
            try:
                from ...auto_instrument.trace import get_current_trace
                current_trace = get_current_trace()
                if current_trace and hasattr(current_trace, 'id'):
                    existing_trace_id = current_trace.id
            except Exception:
                pass  # Context not available, continue
            
            # If we already have a trace_id (from previous invocation or context), reuse it
            if existing_trace_id:
                self.trace_id = existing_trace_id
                trace_already_exists = True
            elif self.trace_id:
                # Reuse existing trace_id from handler (for nested invocations)
                trace_already_exists = True
            else:
                # Generate new trace ID only if we don't have one
                self.trace_id = str(uuid.uuid4())
                trace_already_exists = False
            
            # Reset invocation-specific state (but keep trace_id)
            self._has_errors = False
            self._error_messages = []
            self._total_tool_calls = 0
            self._total_input_tokens = 0
            self._total_output_tokens = 0
            self._total_cost = 0.0
            self.agent_span_id = None
            self.model_span_id = None
            self.model_start_time = None
            self.tool_map.clear()
            self.multi_agent_map.clear()
            self.node_map.clear()
            self._current_parent_span_id = None
            self._parent_span_stack.clear()

            # Determine trace name
            agent_name = getattr(event.agent, 'name', 'Strands Agent')
            trace_name = self.trace_name or agent_name

            # Only create trace if it doesn't already exist
            if not trace_already_exists:
                # Create trace
                trace_data = {
                    "id": self.trace_id,
                    "name": trace_name,
                    "metadata": {
                        "framework": "strands",
                        "agent_id": getattr(event.agent, 'agent_id', None),
                        "agent_name": agent_name,
                        **self.metadata,
                    },
                    "tags": self.tags,
                    "start_time": datetime.utcnow().isoformat(),
                }

                if self.user_id:
                    trace_data["user_id"] = self.user_id
                if self.session_id:
                    trace_data["session_id"] = self.session_id

                # Create trace first
                await aigie._buffer.add(EventType.TRACE_CREATE, trace_data)
                
                # Set trace in context so other handlers can reuse it
                try:
                    from ...auto_instrument.trace import set_current_trace
                    # Create a simple trace context object with the trace_id
                    # This allows subsequent agent invocations to find and reuse the trace
                    class SimpleTraceContext:
                        def __init__(self, trace_id: str, trace_name: str):
                            self.id = trace_id
                            self.name = trace_name
                    set_current_trace(SimpleTraceContext(self.trace_id, trace_name))
                except Exception as e:
                    logger.debug(f"[AIGIE] Could not set trace in context: {e}")
                
                # Flush immediately to ensure trace is created before spans
                # This prevents orphan spans
                await aigie._buffer.flush()
            else:
                logger.debug(f"[AIGIE] Reusing existing trace: {self.trace_id}")

            # Create agent span (root span for this invocation - no parent)
            self.agent_span_id = str(uuid.uuid4())
            agent_span_data = {
                "id": self.agent_span_id,
                "trace_id": self.trace_id,
                "parent_id": None,  # Root span under trace - use parent_id not parent_span_id
                "name": f"Agent: {agent_name}",
                "type": "agent",
                "start_time": datetime.utcnow().isoformat(),
                "metadata": {
                    "agent_id": getattr(event.agent, 'agent_id', None),
                    "agent_name": agent_name,
                },
                "tags": self.tags,
                "status": "running",
            }

            if self.user_id:
                agent_span_data["user_id"] = self.user_id
            if self.session_id:
                agent_span_data["session_id"] = self.session_id

            # Capture input if enabled
            if self.config.capture_inputs and event.messages:
                # Truncate messages if needed
                messages_repr = str(event.messages)
                if len(messages_repr) > self.config.max_content_length:
                    messages_repr = messages_repr[:self.config.max_content_length] + "..."
                agent_span_data["input"] = messages_repr
                agent_span_data["metadata"]["input_messages"] = messages_repr

            await aigie._buffer.add(EventType.SPAN_CREATE, agent_span_data)
            self._current_parent_span_id = self.agent_span_id

            logger.debug(f"[AIGIE] Trace started: {trace_name} (id={self.trace_id})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_before_invocation: {e}")

    async def _on_after_invocation(self, event: "AfterInvocationEvent") -> None:
        """Handle AfterInvocationEvent - complete agent span and trace."""
        if not self.config.enabled or not self.config.trace_agents:
            return

        if not self.agent_span_id:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            # Determine if invocation succeeded or failed
            result: Optional["AgentResult"] = event.result
            has_error = result is None or self._has_errors or len(self._error_messages) > 0
            
            # Extract metrics from result
            if result and hasattr(result, 'metrics'):
                metrics = result.metrics
                if hasattr(metrics, 'accumulated_usage'):
                    usage = metrics.accumulated_usage
                    if usage:
                        # Usage is a TypedDict with keys: inputTokens, outputTokens, totalTokens
                        self._total_input_tokens = usage.get("inputTokens", 0) or 0
                        self._total_output_tokens = usage.get("outputTokens", 0) or 0

                        # Calculate cost - extract model_id
                        model_id = None
                        if hasattr(event.agent, 'model'):
                            model_id = self._extract_model_id(event.agent.model)

                        self._total_cost = calculate_strands_cost(
                            model_id=model_id,
                            input_tokens=self._total_input_tokens,
                            output_tokens=self._total_output_tokens,
                        )

            # Determine status
            status = "error" if has_error else "success"
            error_message = None
            if self._error_messages:
                error_message = "; ".join(self._error_messages[:3])  # Limit to first 3 errors
            elif result is None:
                error_message = "Agent invocation returned no result"

            # Update agent span
            update_data = {
                "id": self.agent_span_id,
                "trace_id": self.trace_id,
                "end_time": datetime.utcnow().isoformat(),
                "status": status,
                "metadata": {
                    "total_tool_calls": self._total_tool_calls,
                    "total_input_tokens": self._total_input_tokens,
                    "total_output_tokens": self._total_output_tokens,
                    "total_tokens": self._total_input_tokens + self._total_output_tokens,
                    "total_cost": self._total_cost,
                },
            }

            if error_message:
                update_data["error"] = error_message
                update_data["error_message"] = error_message
                update_data["metadata"]["error"] = error_message

            # Capture output if enabled
            if self.config.capture_outputs and result:
                output_repr = str(result)
                if len(output_repr) > self.config.max_content_length:
                    output_repr = output_repr[:self.config.max_content_length] + "..."
                update_data["output"] = output_repr
                update_data["metadata"]["result"] = output_repr

            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

            # Update trace with aggregated metrics
            # Note: We update the trace but don't set end_time if this is part of a larger workflow
            # The trace will be finalized when the entire workflow completes
            trace_output = {}
            if self.config.capture_outputs and result:
                output_repr = str(result)
                if len(output_repr) > self.config.max_content_length:
                    output_repr = output_repr[:self.config.max_content_length] + "..."
                trace_output["response"] = output_repr

            # Update trace with metrics from this invocation
            # Note: If multiple invocations share the same trace, each will update it
            # The backend should aggregate or the last update will be the final state
            trace_update = {
                "id": self.trace_id,
                "status": status,  # Status from this invocation
                "end_time": datetime.utcnow().isoformat(),  # Update end_time on each invocation
                "output": trace_output,
                # Token/cost fields for backend aggregation display
                "total_tokens": self._total_input_tokens + self._total_output_tokens,
                "prompt_tokens": self._total_input_tokens,
                "completion_tokens": self._total_output_tokens,
                "total_cost": self._total_cost,
                "metadata": {
                    "total_tool_calls": self._total_tool_calls,
                    "total_input_tokens": self._total_input_tokens,
                    "total_output_tokens": self._total_output_tokens,
                    "total_tokens": self._total_input_tokens + self._total_output_tokens,
                    "total_cost": self._total_cost,
                    "last_agent": getattr(event.agent, 'name', 'Strands Agent'),
                },
            }

            if error_message:
                trace_update["error"] = error_message
                trace_update["error_message"] = error_message

            await aigie._buffer.add(EventType.TRACE_UPDATE, trace_update)

            # Clean up any pending spans (tools, models, nodes, multi-agent)
            await self._complete_pending_spans()

            logger.debug(f"[AIGIE] Trace completed: {self.trace_id} (status={status})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_after_invocation: {e}")
            # Still try to complete trace with error status
            try:
                if self.agent_span_id and self.trace_id:
                    error_update = {
                        "id": self.agent_span_id,
                        "trace_id": self.trace_id,
                        "end_time": datetime.utcnow().isoformat(),
                        "status": "error",
                        "error": str(e),
                        "error_message": str(e),
                    }
                    await aigie._buffer.add(EventType.SPAN_UPDATE, error_update)
                    
                    trace_error = {
                        "id": self.trace_id,
                        "status": "error",
                        "end_time": datetime.utcnow().isoformat(),
                        "error": str(e),
                        "error_message": str(e),
                    }
                    await aigie._buffer.add(EventType.TRACE_UPDATE, trace_error)
            except Exception:
                pass  # Best effort

    async def _on_message_added(self, event: "MessageAddedEvent") -> None:
        """Handle MessageAddedEvent - track message additions."""
        if not self.config.enabled or not self.config.capture_messages:
            return

        # Messages are tracked as part of the agent span
        # This hook can be used for fine-grained message tracking if needed
        pass

    # Tool execution hooks

    async def _on_before_tool_call(self, event: "BeforeToolCallEvent") -> None:
        """Handle BeforeToolCallEvent - create tool span."""
        if not self.config.enabled or not self.config.trace_tools:
            return

        if not self._current_parent_span_id or not self.trace_id:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            tool_use: "ToolUse" = event.tool_use
            tool_use_id = tool_use.get('toolUseId', str(uuid.uuid4()))
            tool_name = tool_use.get('name', 'unknown_tool')

            span_id = str(uuid.uuid4())
            start_time = datetime.utcnow()

            self.tool_map[tool_use_id] = {
                'spanId': span_id,
                'startTime': start_time,
                'toolName': tool_name,
            }

            span_data = {
                "id": span_id,
                "trace_id": self.trace_id,
                "parent_id": self._current_parent_span_id,  # Use parent_id not parent_span_id
                "name": f"Tool: {tool_name}",
                "type": "tool",
                "start_time": start_time.isoformat(),
                "metadata": {
                    "tool_name": tool_name,
                    "tool_use_id": tool_use_id,
                },
                "tags": self.tags,
                "status": "running",
            }

            if self.user_id:
                span_data["user_id"] = self.user_id
            if self.session_id:
                span_data["session_id"] = self.session_id

            # Capture tool input if enabled
            if self.config.capture_inputs:
                tool_input = tool_use.get('input', {})
                input_repr = str(tool_input)
                if len(input_repr) > self.config.max_content_length:
                    input_repr = input_repr[:self.config.max_content_length] + "..."
                span_data["input"] = input_repr
                span_data["metadata"]["tool_input"] = input_repr

            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)
            self._total_tool_calls += 1

            logger.debug(f"[AIGIE] Tool span created: {tool_name} (id={span_id})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_before_tool_call: {e}")

    async def _on_after_tool_call(self, event: "AfterToolCallEvent") -> None:
        """Handle AfterToolCallEvent - complete tool span."""
        if not self.config.enabled or not self.config.trace_tools:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            tool_use: "ToolUse" = event.tool_use
            tool_use_id = tool_use.get('toolUseId', 'unknown')

            tool_data = self.tool_map.get(tool_use_id)
            if not tool_data:
                return

            span_id = tool_data['spanId']
            tool_name = tool_data['toolName']

            # Determine status
            status = "success"
            if event.exception:
                status = "error"
                self._has_errors = True
                error_msg = str(event.exception)
                if error_msg and error_msg not in self._error_messages:
                    self._error_messages.append(error_msg)
            elif event.cancel_message:
                status = "cancelled"

            # Calculate duration
            start_time = tool_data['startTime']
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            update_data = {
                "id": span_id,
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": status,
                "metadata": {
                    "tool_name": tool_name,
                },
            }

            # Capture tool output if enabled
            if self.config.capture_outputs:
                if event.result:
                    result_repr = str(event.result)
                    if len(result_repr) > self.config.max_tool_result_length:
                        result_repr = result_repr[:self.config.max_tool_result_length] + "..."
                    update_data["output"] = result_repr
                    update_data["metadata"]["tool_result"] = result_repr

                if event.exception:
                    error_str = str(event.exception)
                    update_data["error"] = error_str
                    update_data["error_message"] = error_str
                    update_data["metadata"]["error"] = error_str

            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

            # Clean up
            del self.tool_map[tool_use_id]

            logger.debug(f"[AIGIE] Tool span completed: {tool_name} (id={span_id}, status={status})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_after_tool_call: {e}")

    # Model invocation hooks

    async def _on_before_model_call(self, event: "BeforeModelCallEvent") -> None:
        """Handle BeforeModelCallEvent - create LLM span."""
        if not self.config.enabled or not self.config.trace_llm_calls:
            return

        if not self._current_parent_span_id or not self.trace_id:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            self.model_span_id = str(uuid.uuid4())
            self.model_start_time = datetime.utcnow()

            # Get model info - handle different model types
            model_id = None
            if hasattr(event.agent, 'model'):
                model_id = self._extract_model_id(event.agent.model)

            span_data = {
                "id": self.model_span_id,
                "trace_id": self.trace_id,
                "parent_id": self._current_parent_span_id,  # Use parent_id not parent_span_id
                "name": f"LLM: {model_id or 'unknown'}",
                "type": "llm",
                "start_time": self.model_start_time.isoformat(),
                "metadata": {
                    "model_id": model_id,
                },
                "tags": self.tags,
                "status": "running",
            }

            if self.user_id:
                span_data["user_id"] = self.user_id
            if self.session_id:
                span_data["session_id"] = self.session_id

            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)

            logger.debug(f"[AIGIE] LLM span created: {model_id} (id={self.model_span_id})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_before_model_call: {e}")

    async def _on_after_model_call(self, event: "AfterModelCallEvent") -> None:
        """Handle AfterModelCallEvent - complete LLM span."""
        if not self.config.enabled or not self.config.trace_llm_calls:
            return

        if not self.model_span_id:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            # Determine status
            status = "success"
            if event.exception:
                status = "error"
                self._has_errors = True
                error_msg = str(event.exception)
                if error_msg and error_msg not in self._error_messages:
                    self._error_messages.append(error_msg)

            # Extract model info for cost calculation
            model_id = None
            if hasattr(event.agent, 'model'):
                model_id = self._extract_model_id(event.agent.model)

            # Try to extract usage from agent metrics if available
            model_input_tokens = 0
            model_output_tokens = 0
            if hasattr(event.agent, 'event_loop_metrics'):
                metrics = event.agent.event_loop_metrics
                if hasattr(metrics, 'accumulated_usage'):
                    usage = metrics.accumulated_usage
                    if usage:
                        model_input_tokens = usage.get("inputTokens", 0) or 0
                        model_output_tokens = usage.get("outputTokens", 0) or 0

            # Calculate cost for this model call
            model_cost = calculate_strands_cost(
                model_id=model_id,
                input_tokens=model_input_tokens,
                output_tokens=model_output_tokens,
            )

            # Calculate duration
            end_time = datetime.utcnow()
            duration = 0.0
            if self.model_start_time:
                duration = (end_time - self.model_start_time).total_seconds()

            update_data = {
                "id": self.model_span_id,
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": status,
                "metadata": {
                    "model_id": model_id,
                    "input_tokens": model_input_tokens,
                    "output_tokens": model_output_tokens,
                    "total_tokens": model_input_tokens + model_output_tokens,
                    "cost": model_cost,
                },
                # Token fields for backend aggregation
                "prompt_tokens": model_input_tokens,
                "completion_tokens": model_output_tokens,
                "total_tokens": model_input_tokens + model_output_tokens,
            }

            if event.stop_response:
                if self.config.capture_outputs:
                    message_repr = str(event.stop_response.message)
                    if len(message_repr) > self.config.max_content_length:
                        message_repr = message_repr[:self.config.max_content_length] + "..."
                    update_data["output"] = message_repr
                    update_data["metadata"]["stop_reason"] = str(event.stop_response.stop_reason)

            if event.exception:
                error_str = str(event.exception)
                update_data["error"] = error_str
                update_data["error_message"] = error_str
                update_data["metadata"]["error"] = error_str

            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

            # Store span_id before cleanup for logging
            completed_span_id = self.model_span_id

            logger.debug(f"[AIGIE] LLM span completed: {completed_span_id} (status={status})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_after_model_call: {e}")
        finally:
            # Always clean up model span state
            self.model_span_id = None
            self.model_start_time = None

    # Multi-agent hooks

    async def _on_before_multi_agent(self, event: "BeforeMultiAgentInvocationEvent") -> None:
        """Handle BeforeMultiAgentInvocationEvent - create orchestrator span."""
        if not self.config.enabled or not self.config.trace_multi_agent:
            return

        if not self.trace_id:
            # If no trace_id, create one (for nested multi-agent scenarios)
            self.trace_id = str(uuid.uuid4())

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            orchestrator = event.source
            orchestrator_id = id(orchestrator)
            orchestrator_type = type(orchestrator).__name__

            span_id = str(uuid.uuid4())
            start_time = datetime.utcnow()

            self.multi_agent_map[orchestrator_id] = {
                'spanId': span_id,
                'startTime': start_time,
                'type': orchestrator_type,
            }

            span_data = {
                "id": span_id,
                "trace_id": self.trace_id or str(uuid.uuid4()),
                "parent_id": self._current_parent_span_id,  # Use parent_id not parent_span_id
                "name": f"Multi-Agent: {orchestrator_type}",
                "type": "multi_agent",
                "start_time": start_time.isoformat(),
                "metadata": {
                    "orchestrator_type": orchestrator_type,
                    "orchestrator_id": str(orchestrator_id),
                },
                "tags": self.tags,
                "status": "running",
            }

            if self.user_id:
                span_data["user_id"] = self.user_id
            if self.session_id:
                span_data["session_id"] = self.session_id

            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)
            
            # Store previous parent and push to stack
            if self._current_parent_span_id:
                self._parent_span_stack.append(self._current_parent_span_id)
            self._current_parent_span_id = span_id

            logger.debug(f"[AIGIE] Multi-agent orchestrator span created: {orchestrator_type} (id={span_id})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_before_multi_agent: {e}")

    async def _on_after_multi_agent(self, event: "AfterMultiAgentInvocationEvent") -> None:
        """Handle AfterMultiAgentInvocationEvent - complete orchestrator span."""
        if not self.config.enabled or not self.config.trace_multi_agent:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            orchestrator = event.source
            orchestrator_id = id(orchestrator)

            orchestrator_data = self.multi_agent_map.get(orchestrator_id)
            if not orchestrator_data:
                return

            span_id = orchestrator_data['spanId']
            orchestrator_type = orchestrator_data['type']
            start_time = orchestrator_data['startTime']
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Check for errors - AfterMultiAgentInvocationEvent might have error info
            status = "success"
            error_message = None
            # Note: AfterMultiAgentInvocationEvent doesn't have exception field in Strands
            # but we track errors from child nodes/agents
            if self._has_errors:
                status = "error"
                if self._error_messages:
                    error_message = "; ".join(self._error_messages[:2])

            update_data = {
                "id": span_id,
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": status,
                "metadata": {
                    "orchestrator_type": orchestrator_type,
                },
            }

            if error_message:
                update_data["error"] = error_message
                update_data["error_message"] = error_message
                update_data["metadata"]["error"] = error_message

            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

            # Restore previous parent from stack
            if self._parent_span_stack:
                self._current_parent_span_id = self._parent_span_stack.pop()
            else:
                # Fallback to agent span
                self._current_parent_span_id = self.agent_span_id

            # Clean up
            del self.multi_agent_map[orchestrator_id]

            logger.debug(f"[AIGIE] Multi-agent orchestrator span completed: {orchestrator_type} (id={span_id}, status={status})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_after_multi_agent: {e}")

    async def _on_before_node_call(self, event: "BeforeNodeCallEvent") -> None:
        """Handle BeforeNodeCallEvent - create node span."""
        if not self.config.enabled or not self.config.trace_multi_agent:
            return

        if not self._current_parent_span_id or not self.trace_id:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            node_id = event.node_id
            orchestrator = event.source
            orchestrator_type = type(orchestrator).__name__

            span_id = str(uuid.uuid4())
            start_time = datetime.utcnow()

            self.node_map[node_id] = {
                'spanId': span_id,
                'startTime': start_time,
                'nodeId': node_id,
            }

            span_data = {
                "id": span_id,
                "trace_id": self.trace_id,
                "parent_id": self._current_parent_span_id,  # Use parent_id not parent_span_id
                "name": f"Node: {node_id}",
                "type": "node",
                "start_time": start_time.isoformat(),
                "metadata": {
                    "node_id": node_id,
                    "orchestrator_type": orchestrator_type,
                },
                "tags": self.tags,
                "status": "running",
            }

            if self.user_id:
                span_data["user_id"] = self.user_id
            if self.session_id:
                span_data["session_id"] = self.session_id

            await aigie._buffer.add(EventType.SPAN_CREATE, span_data)

            logger.debug(f"[AIGIE] Node span created: {node_id} (id={span_id})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_before_node_call: {e}")

    async def _on_after_node_call(self, event: "AfterNodeCallEvent") -> None:
        """Handle AfterNodeCallEvent - complete node span."""
        if not self.config.enabled or not self.config.trace_multi_agent:
            return

        aigie = self._get_aigie()
        if not aigie or not aigie._initialized:
            return

        try:
            node_id = event.node_id

            node_data = self.node_map.get(node_id)
            if not node_data:
                return

            span_id = node_data['spanId']
            start_time = node_data['startTime']
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Check for errors - AfterNodeCallEvent might have error info
            status = "success"
            error_message = None
            # Note: AfterNodeCallEvent doesn't have exception field in Strands
            # but we track errors from child agents
            if self._has_errors:
                status = "error"
                if self._error_messages:
                    error_message = "; ".join(self._error_messages[:2])

            update_data = {
                "id": span_id,
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": status,
                "metadata": {
                    "node_id": node_id,
                },
            }

            if error_message:
                update_data["error"] = error_message
                update_data["error_message"] = error_message
                update_data["metadata"]["error"] = error_message

            await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)

            # Clean up
            del self.node_map[node_id]

            logger.debug(f"[AIGIE] Node span completed: {node_id} (id={span_id}, status={status})")

        except Exception as e:
            logger.warning(f"[AIGIE] Error in _on_after_node_call: {e}")

    # Helper methods

    def _extract_model_id(self, model: Any) -> Optional[str]:
        """Extract model ID from various model types."""
        if not model:
            return None
        
        # Try different ways to get model_id
        if hasattr(model, 'model_id'):
            return model.model_id
        elif hasattr(model, '_model_id'):
            return model._model_id
        elif hasattr(model, 'config'):
            if isinstance(model.config, dict):
                return model.config.get('model_id')
            elif hasattr(model.config, 'model_id'):
                return model.config.model_id
        # For GeminiModel and similar, check client_args
        elif hasattr(model, 'client_args') and isinstance(model.client_args, dict):
            # Fallback to model type name
            return type(model).__name__.replace('Model', '').lower()
        
        return None

    async def _complete_pending_spans(self) -> None:
        """Complete any pending spans that weren't explicitly closed."""
        aigie = self._get_aigie()
        if not aigie or not aigie._initialized or not self.trace_id:
            return

        end_time = datetime.utcnow()

        # Complete pending tool spans
        pending_tool_ids = list(self.tool_map.keys())
        for tool_use_id in pending_tool_ids:
            tool_data = self.tool_map.get(tool_use_id)
            if not tool_data:
                continue

            duration = (end_time - tool_data['startTime']).total_seconds()
            update_data = {
                "id": tool_data['spanId'],
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": "success",  # Assume success if not explicitly failed
                "metadata": {
                    "tool_name": tool_data['toolName'],
                    "pending_cleanup": True,  # Mark as cleanup
                },
            }
            try:
                await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)
            except Exception:
                pass  # Best effort
            del self.tool_map[tool_use_id]

        # Complete pending model span
        if self.model_span_id:
            if self.model_start_time:
                duration = (end_time - self.model_start_time).total_seconds()
            else:
                duration = 0.0
            
            update_data = {
                "id": self.model_span_id,
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": "success",  # Assume success if not explicitly failed
                "metadata": {
                    "pending_cleanup": True,  # Mark as cleanup
                },
            }
            try:
                await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)
            except Exception:
                pass  # Best effort
            self.model_span_id = None
            self.model_start_time = None

        # Complete pending multi-agent spans
        pending_orchestrator_ids = list(self.multi_agent_map.keys())
        for orchestrator_id in pending_orchestrator_ids:
            orchestrator_data = self.multi_agent_map.get(orchestrator_id)
            if not orchestrator_data:
                continue

            duration = (end_time - orchestrator_data['startTime']).total_seconds()
            update_data = {
                "id": orchestrator_data['spanId'],
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": "success",  # Assume success if not explicitly failed
                "metadata": {
                    "orchestrator_type": orchestrator_data['type'],
                    "pending_cleanup": True,  # Mark as cleanup
                },
            }
            try:
                await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)
            except Exception:
                pass  # Best effort
            del self.multi_agent_map[orchestrator_id]

        # Complete pending node spans
        pending_node_ids = list(self.node_map.keys())
        for node_id in pending_node_ids:
            node_data = self.node_map.get(node_id)
            if not node_data:
                continue

            duration = (end_time - node_data['startTime']).total_seconds()
            update_data = {
                "id": node_data['spanId'],
                "trace_id": self.trace_id,
                "end_time": end_time.isoformat(),
                "duration_ns": int(duration * 1_000_000_000),
                "status": "success",  # Assume success if not explicitly failed
                "metadata": {
                    "node_id": node_id,
                    "pending_cleanup": True,  # Mark as cleanup
                },
            }
            try:
                await aigie._buffer.add(EventType.SPAN_UPDATE, update_data)
            except Exception:
                pass  # Best effort
            del self.node_map[node_id]
