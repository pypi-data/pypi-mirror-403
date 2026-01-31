"""LangChain integration using SDK Spans.

This module provides a callback handler that traces LangChain operations
using SDK Span objects, which are exported via OTLP.

Usage:
    from lumenova_beacon import BeaconClient
    from lumenova_beacon import BeaconCallbackHandler
    from langchain_openai import ChatOpenAI

    # Initialize BeaconClient (sets up TracerProvider)
    client = BeaconClient()

    # Create callback handler
    handler = BeaconCallbackHandler()

    # Use with LangChain
    llm = ChatOpenAI()
    response = llm.invoke("Hello", config={"callbacks": [handler]})

Environment Variables:
    BEACON_ENDPOINT - Beacon API endpoint (for OTLP export)
    BEACON_API_KEY - Beacon API key (for OTLP export)
    BEACON_SESSION_ID - Default session ID (optional)
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Sequence
from uuid import UUID

from lumenova_beacon.core.client import get_client
from lumenova_beacon.tracing.span import Span
from lumenova_beacon.tracing.trace import (
    get_current_span,
    set_current_span,
    clear_context,
)
from lumenova_beacon.types import SpanType, SpanKind, StatusCode

try:
    from langchain_core.callbacks import BaseCallbackHandler
    from langchain_core.agents import AgentAction, AgentFinish
    from langchain_core.documents import Document
    from langchain_core.messages import BaseMessage
    from langchain_core.outputs import LLMResult
except ImportError:
    raise ImportError(
        "langchain-core is required for LangChain OTLP integration. "
        "Install it with: pip install langchain-core"
    )

logger = logging.getLogger(__name__)


class BeaconCallbackHandler(BaseCallbackHandler):
    """Callback handler for tracing LangChain operations.

    Traces LangChain operations using SDK Span objects, which are exported
    via OTLP to the configured backend.

    Handles:
    - Chain operations (on_chain_start/end/error)
    - LLM calls (on_llm_start/end/error, on_chat_model_start)
    - Tool invocations (on_tool_start/end/error)
    - Retriever queries (on_retriever_start/end/error)
    - Agent actions (on_agent_action/finish)

    Example:
        >>> from lumenova_beacon import BeaconClient
        >>> from lumenova_beacon import BeaconCallbackHandler
        >>> from langchain_openai import ChatOpenAI
        >>>
        >>> # Initialize BeaconClient (sets up TracerProvider)
        >>> client = BeaconClient()
        >>>
        >>> # Create callback handler
        >>> handler = BeaconCallbackHandler()
        >>>
        >>> # Use with LangChain
        >>> llm = ChatOpenAI()
        >>> response = llm.invoke("Hello", config={"callbacks": [handler]})
    """

    # Span type attributes
    ATTR_SPAN_TYPE = "beacon.span_type"
    ATTR_COMPONENT_TYPE = "langchain.component_type"

    # GenAI semantic conventions
    # See: https://opentelemetry.io/docs/specs/semconv/gen-ai/
    ATTR_LLM_SYSTEM = "gen_ai.system"
    ATTR_LLM_MODEL = "gen_ai.request.model"
    ATTR_LLM_PROMPT = "gen_ai.prompt"
    ATTR_LLM_COMPLETION = "gen_ai.completion"
    ATTR_LLM_PROMPT_TOKENS = "gen_ai.usage.prompt_tokens"
    ATTR_LLM_COMPLETION_TOKENS = "gen_ai.usage.completion_tokens"
    ATTR_LLM_TOTAL_TOKENS = "gen_ai.usage.total_tokens"

    # TTFT (Time-to-First-Token) attributes
    ATTR_TTFT_MS = "gen_ai.response.time_to_first_token_ms"
    ATTR_STREAMING = "gen_ai.request.streaming"

    # LangChain-specific attributes
    ATTR_LANGCHAIN_INPUT = "langchain.input"
    ATTR_LANGCHAIN_OUTPUT = "langchain.output"

    # GenAI Agent attributes (OTEL standard)
    ATTR_AGENT_NAME = "gen_ai.agent.name"
    ATTR_AGENT_ID = "gen_ai.agent.id"
    ATTR_AGENT_DESCRIPTION = "gen_ai.agent.description"

    # Deployment attributes (OTEL standard)
    ATTR_DEPLOYMENT_ENVIRONMENT = "deployment.environment.name"

    # Model request parameters (OTEL standard)
    ATTR_REQUEST_TEMPERATURE = "gen_ai.request.temperature"
    ATTR_REQUEST_TOP_P = "gen_ai.request.top_p"
    ATTR_REQUEST_TOP_K = "gen_ai.request.top_k"
    ATTR_REQUEST_MAX_TOKENS = "gen_ai.request.max_tokens"
    ATTR_REQUEST_FREQUENCY_PENALTY = "gen_ai.request.frequency_penalty"
    ATTR_REQUEST_PRESENCE_PENALTY = "gen_ai.request.presence_penalty"

    # Beacon-specific attributes
    ATTR_BEACON_SESSION_ID = "beacon.session_id"
    ATTR_BEACON_METADATA_PREFIX = "beacon.metadata."

    # LangGraph-specific attributes
    ATTR_LANGGRAPH_INTERRUPT = "langgraph.interrupt"
    ATTR_LANGGRAPH_INTERRUPT_ID = "langgraph.interrupt.id"
    ATTR_LANGGRAPH_INTERRUPT_VALUE = "langgraph.interrupt.value"
    ATTR_LANGGRAPH_THREAD_ID = "langgraph.thread_id"
    ATTR_LANGGRAPH_RESUME = "langgraph.resume"
    ATTR_LANGGRAPH_RESUME_VALUE = "langgraph.resume.value"
    ATTR_LANGGRAPH_CANCELLED = "langgraph.cancelled"

    def __init__(
        self,
        session_id: str | None = None,
        environment: str | None = None,
        agent_name: str | None = None,
        agent_id: str | None = None,
        agent_description: str | None = None,
        metadata: dict[str, Any] | None = None,
        trace_id: str | None = None,
        parent_id: str | None = None,
        thread_trace_map: dict[str, str] | None = None,
    ):
        """Initialize the LangChain callback handler.

        Args:
            session_id: Default session ID for all spans (optional)
            environment: Environment name (e.g., "production", "staging", "development")
            agent_name: Human-readable name of the GenAI agent
            agent_id: Unique identifier of the GenAI agent
            agent_description: Description of the GenAI agent
            metadata: Custom metadata dict to add to all spans (key-value pairs)
            trace_id: Explicit trace ID for trace continuation (e.g., after LangGraph interrupt)
            parent_id: Explicit parent span ID for trace continuation. When set, resume spans
                will be placed under the original root span instead of creating a nested root.
            thread_trace_map: Dict mapping LangGraph thread_ids to trace_ids for automatic
                trace continuation across interrupt/resume cycles
        """
        super().__init__()

        # Cache the client instance to avoid creating duplicates in async contexts
        self._client = get_client()

        self._session_id = session_id if session_id is not None else self._client.config.session_id
        self._environment = environment
        self._agent_name = agent_name
        self._agent_id = agent_id
        self._agent_description = agent_description
        self._metadata = metadata or {}

        # Track active spans by run_id
        self._runs: dict[str, dict[str, Any]] = {}
        self._langgraph_parent_ids: set[str] = set()

        # TTFT tracking for streaming calls
        self._first_token_times: dict[str, float | None] = {}

        # Trace continuation support for LangGraph interrupts
        self._continuation_trace_id = trace_id
        self._continuation_parent_id = parent_id  # For flattening resume spans
        self._thread_trace_map = thread_trace_map.copy() if thread_trace_map else {}
        self._current_trace_id: str | None = trace_id  # Will be set when first span is created
        self._root_span_id: str | None = None  # First span's ID, for passing to resume handlers
        self._skipped_resume_roots: dict[str, dict[str, Any]] = {}  # run_id -> {parent_id, resume_value}
        self._reparented_spans: set[str] = set()  # run_ids of spans reparented under original root
        self._cancelled_span_id: str | None = None  # Track which span was actually cancelled (first to receive CancelledError)

        logger.debug("Initialized BeaconCallbackHandler")

    @property
    def client(self):
        """Get the cached BeaconClient instance."""
        return self._client

    def get_trace_id_for_thread(self, thread_id: str) -> str | None:
        """Get the trace ID associated with a LangGraph thread.

        Use this to continue a trace after an interrupt by passing the trace_id
        to a new handler instance or using thread_trace_map.

        Args:
            thread_id: The LangGraph thread_id (from config["configurable"]["thread_id"])

        Returns:
            The trace_id if found, None otherwise
        """
        return self._thread_trace_map.get(thread_id)

    def set_trace_id_for_thread(self, thread_id: str, trace_id: str) -> None:
        """Associate a trace ID with a LangGraph thread.

        Call this to enable trace continuation after interrupts when using
        a new handler instance.

        Args:
            thread_id: The LangGraph thread_id
            trace_id: The trace_id to associate
        """
        self._thread_trace_map[thread_id] = trace_id

    @property
    def thread_trace_map(self) -> dict[str, str]:
        """Get the current thread_id to trace_id mapping.

        Returns a copy to prevent external modification.

        Returns:
            Dict mapping LangGraph thread_ids to trace_ids
        """
        return self._thread_trace_map.copy()

    @property
    def trace_id(self) -> str | None:
        """Get the current trace ID.

        This is the trace_id of the root span, or the continuation trace_id
        if set. Use this to continue the trace in subsequent requests.

        Returns:
            The current trace_id, or None if no trace has been started
        """
        return self._current_trace_id

    @property
    def root_span_id(self) -> str | None:
        """Get the root span ID for trace flattening across resume cycles.

        Use this to pass to a resume handler so that resume spans are placed
        directly under the original root span, flattening the trace structure.

        When this handler was created with a `parent_id` for resume, this returns
        that original parent_id to maintain correct trace structure across resumes.
        This prevents cascading nesting where each resume would otherwise create
        its own "root" that becomes the parent for the next resume.

        Returns:
            The root span_id, or None if no spans have been created
        """
        # When resuming with parent_id, preserve the original root span ID
        # to prevent cascading nesting on subsequent resumes
        if self._continuation_parent_id:
            return self._continuation_parent_id
        return self._root_span_id

    def _serialize_for_json(self, obj: Any) -> Any:
        """Recursively serialize an object to ensure JSON compatibility.

        Args:
            obj: Object to serialize

        Returns:
            JSON-compatible representation of the object
        """
        if obj is None:
            return None

        if isinstance(obj, (str, int, float, bool)):
            return obj

        if isinstance(obj, UUID):
            return str(obj)

        if isinstance(obj, BaseMessage):
            result = {
                "role": obj.type if hasattr(obj, "type") else "unknown",
                "content": obj.content if hasattr(obj, "content") else str(obj),
            }
            if hasattr(obj, "additional_kwargs") and obj.additional_kwargs:
                result["additional_kwargs"] = self._serialize_for_json(obj.additional_kwargs)
            return result

        if isinstance(obj, Document):
            return {
                "page_content": obj.page_content,
                "metadata": self._serialize_for_json(obj.metadata) if hasattr(obj, "metadata") else {},
            }

        if isinstance(obj, dict):
            return {key: self._serialize_for_json(value) for key, value in obj.items()}

        if isinstance(obj, (list, tuple)):
            return [self._serialize_for_json(item) for item in obj]

        if isinstance(obj, set):
            return [self._serialize_for_json(item) for item in obj]

        # Handle Pydantic models
        if hasattr(obj, "model_dump"):
            try:
                return self._serialize_for_json(obj.model_dump())
            except Exception:
                pass
        elif hasattr(obj, "dict"):
            try:
                return self._serialize_for_json(obj.dict())
            except Exception:
                pass

        try:
            return str(obj)
        except Exception:
            return "<unserializable>"

    def _extract_name(self, serialized: dict[str, Any], **kwargs: Any) -> str:
        """Extract component name from serialized data.

        Args:
            serialized: Component's serialized definition
            **kwargs: Additional arguments

        Returns:
            Component name string
        """
        try:
            if "name" in kwargs and kwargs["name"] is not None:
                return str(kwargs["name"])
            if "name" in serialized:
                return serialized["name"]
            if "id" in serialized and isinstance(serialized["id"], list):
                return serialized["id"][-1] if serialized["id"] else "Unknown"
            return "Unknown"
        except Exception as e:
            logger.debug(f"Error extracting component name: {e}")
            return "Unknown"

    def _has_langgraph_metadata(
        self,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> bool:
        """Check if this span has LangGraph-specific metadata.

        Args:
            metadata: Callback metadata
            tags: Callback tags

        Returns:
            True if this span has LangGraph metadata
        """
        try:
            if metadata:
                for key in metadata.keys():
                    if key.startswith("langgraph_"):
                        return True

            if tags:
                for tag in tags:
                    if isinstance(tag, str) and tag.startswith("graph:step:"):
                        return True

            return False
        except Exception:
            return False

    def _is_langgraph_interrupt(self, error: BaseException) -> bool:
        """Check if an exception is a LangGraph Interrupt.

        LangGraph's interrupt() function raises an Interrupt exception for HITL flows.
        When propagated through callbacks, it may be wrapped in a GraphInterrupt.
        We detect this by class name to avoid a hard dependency on langgraph.

        Args:
            error: The exception to check

        Returns:
            True if this is a LangGraph Interrupt, False otherwise
        """
        error_type = type(error).__name__
        # Direct Interrupt exception
        if error_type == "Interrupt" and hasattr(error, "value"):
            return True
        # GraphInterrupt wrapper (contains interrupts list)
        if error_type == "GraphInterrupt":
            return True
        return False

    def _extract_interrupt_info(self, error: BaseException) -> dict[str, Any]:
        """Extract information from a LangGraph Interrupt or GraphInterrupt.

        Args:
            error: The Interrupt or GraphInterrupt exception

        Returns:
            Dict with 'value' (the prompt) and 'id' (interrupt checkpoint ID)
        """
        error_type = type(error).__name__

        # Direct Interrupt exception
        if error_type == "Interrupt":
            return {
                "value": getattr(error, "value", str(error)),
                "id": getattr(error, "id", None),
            }

        # GraphInterrupt wrapper - extract from interrupts list
        if error_type == "GraphInterrupt":
            interrupts = getattr(error, "interrupts", [])
            if interrupts:
                # Get first interrupt's info
                first_interrupt = interrupts[0]
                return {
                    "value": getattr(first_interrupt, "value", str(first_interrupt)),
                    "id": getattr(first_interrupt, "id", None),
                }
            # Fallback to string representation
            return {
                "value": str(error),
                "id": None,
            }

        # Fallback
        return {
            "value": str(error),
            "id": None,
        }

    def _is_cancelled_error(self, error: BaseException) -> bool:
        """Check if an exception is a CancelledError (user cancelled the stream).

        This occurs when the user cancels an in-progress agent execution via
        the UI or API. Unlike interrupts (HITL), this is not a deliberate pause
        but a user-initiated abort.

        Args:
            error: The exception to check

        Returns:
            True if this is a CancelledError, False otherwise
        """
        import asyncio
        # Check for asyncio.CancelledError or any CancelledError variant
        if isinstance(error, asyncio.CancelledError):
            return True
        # Also check by name for wrapped exceptions
        return type(error).__name__ == "CancelledError"

    def _set_model_parameters(self, span: Span, kwargs: dict[str, Any]) -> None:
        """Extract and set model parameters as standard attributes.

        Args:
            span: The span to set attributes on
            kwargs: The kwargs dict from serialized model data
        """
        # Map LangChain parameter names to OTEL standard attributes
        param_mapping = {
            "temperature": self.ATTR_REQUEST_TEMPERATURE,
            "top_p": self.ATTR_REQUEST_TOP_P,
            "top_k": self.ATTR_REQUEST_TOP_K,
            "max_tokens": self.ATTR_REQUEST_MAX_TOKENS,
            "max_output_tokens": self.ATTR_REQUEST_MAX_TOKENS,  # Alternative name
            "frequency_penalty": self.ATTR_REQUEST_FREQUENCY_PENALTY,
            "presence_penalty": self.ATTR_REQUEST_PRESENCE_PENALTY,
        }

        for param_name, attr_name in param_mapping.items():
            if param_name in kwargs and kwargs[param_name] is not None:
                span.set_attribute(attr_name, kwargs[param_name])

    def _start_span(
        self,
        run_id: UUID,
        parent_run_id: UUID | None,
        name: str,
        span_kind: SpanKind,
        span_type: SpanType,
    ) -> None:
        """Start a new SDK span for a LangChain operation.

        Args:
            run_id: Unique run identifier
            parent_run_id: Parent run identifier (for nesting)
            name: Span name
            span_kind: Span kind
            span_type: Beacon span type (SpanType enum)
        """
        # Determine parent from LangChain's parent_run_id
        parent_id = None
        trace_id = None
        if parent_run_id:
            parent_key = str(parent_run_id)
            if parent_key in self._runs:
                parent_span = self._runs[parent_key]["span"]
                parent_id = parent_span.span_id
                trace_id = parent_span.trace_id
                logger.warning(
                    f"_start_span found parent in _runs: name={name}, run_id={run_id}, "
                    f"parent_run_id={parent_run_id}, parent_span_id={parent_id}"
                )

        # If no parent trace, check for continuation trace_id (for LangGraph resume)
        if trace_id is None:
            trace_id = self._continuation_trace_id

        # If no parent span but we have continuation parent_id, use it
        # This flattens resume spans under the original root span
        if parent_id is None and self._continuation_parent_id:
            parent_id = self._continuation_parent_id
            logger.warning(
                f"_start_span using continuation_parent_id: name={name}, "
                f"parent_id={parent_id}, run_id={run_id}"
            )

        # Save previous span for context restoration
        previous_span = get_current_span()

        # Get timestamp override from client (for historical data seeding)
        timestamp_override = self.client._timestamp_override

        # Create SDK Span
        span = Span(
            name=name,
            trace_id=trace_id,  # None = generate new trace
            parent_id=parent_id,
            kind=span_kind,
            span_type=span_type,
            session_id=self._session_id,
        )
        span.start(timestamp_override)

        # Set common attributes
        span.set_attribute(self.ATTR_COMPONENT_TYPE, name)

        # Set deployment environment
        if self._environment:
            span.set_attribute(self.ATTR_DEPLOYMENT_ENVIRONMENT, self._environment)

        # Set agent attributes
        if self._agent_name:
            span.set_attribute(self.ATTR_AGENT_NAME, self._agent_name)
        if self._agent_id:
            span.set_attribute(self.ATTR_AGENT_ID, self._agent_id)
        if self._agent_description:
            span.set_attribute(self.ATTR_AGENT_DESCRIPTION, self._agent_description)

        # Set custom metadata
        if self._metadata:
            for key, value in self._metadata.items():
                attr_key = f"{self.ATTR_BEACON_METADATA_PREFIX}{key}"
                span.set_attribute(attr_key, value)

        # Set as current span using SDK's ContextVar (async-safe)
        set_current_span(span)

        # Store span and context info
        self._runs[str(run_id)] = {
            "span": span,
            "parent_run_id": str(parent_run_id) if parent_run_id else None,
            "previous_span": previous_span,
            "start_perf_time": time.perf_counter(),
            "timestamp_override": timestamp_override,
        }

        # Update current trace_id (for trace continuation support)
        if self._current_trace_id is None:
            self._current_trace_id = span.trace_id

        # Store root span ID (first span created, for flattening resume spans)
        if self._root_span_id is None:
            self._root_span_id = span.span_id

        logger.debug(
            f"Started LangChain span: name={name}, type={span_type.value}, "
            f"trace_id={span.trace_id}, span_id={span.span_id}"
        )

    def _end_span(self, run_id: UUID, error: BaseException | None = None) -> None:
        """End an SDK span.

        Args:
            run_id: Run identifier of the span to end
            error: Optional exception if the operation failed
        """
        run_id_str = str(run_id)
        if run_id_str not in self._runs:
            return

        run_data = self._runs[run_id_str]
        span = run_data["span"]

        # Set status and record error if present
        if error:
            if self._is_langgraph_interrupt(error):
                # Handle LangGraph interrupt - NOT an error, this is normal HITL flow
                interrupt_info = self._extract_interrupt_info(error)
                logger.info(
                    f"LangGraph interrupt detected: value={interrupt_info.get('value')}, "
                    f"id={interrupt_info.get('id')}, span={span.name}"
                )
                span.set_attribute(self.ATTR_LANGGRAPH_INTERRUPT, True)
                if interrupt_info.get("id"):
                    span.set_attribute(self.ATTR_LANGGRAPH_INTERRUPT_ID, interrupt_info["id"])
                if interrupt_info.get("value"):
                    span.set_attribute(self.ATTR_LANGGRAPH_INTERRUPT_VALUE, str(interrupt_info["value"]))
                span.set_status(StatusCode.OK, f"Interrupted: {interrupt_info.get('value', 'awaiting input')}")
            elif self._is_cancelled_error(error):
                # Handle user cancellation - NOT an error, user aborted the stream
                # Only mark the first span to receive CancelledError (the one actually executing)
                # Parent spans just end normally as cancellation propagates up
                if self._cancelled_span_id is None:
                    self._cancelled_span_id = span.span_id
                    logger.info(f"User cancellation detected: span={span.name} (marked as cancelled)")
                    span.set_attribute(self.ATTR_LANGGRAPH_CANCELLED, True)
                    span.set_status(StatusCode.OK, "Cancelled by user")
                else:
                    # Parent span - cancellation propagated up, just end normally
                    logger.debug(f"Cancellation propagated to parent span: {span.name}")
                    span.set_status(StatusCode.OK)
            else:
                span.record_exception(error)
                span.set_status(StatusCode.ERROR, str(error))
        else:
            if span.status_code == StatusCode.UNSET:
                span.set_status(StatusCode.OK)

        # Calculate end_time if using timestamp override
        end_time = None
        timestamp_override = run_data.get("timestamp_override")
        if timestamp_override is not None:
            start_perf_time = run_data.get("start_perf_time")
            if start_perf_time is not None:
                duration_seconds = time.perf_counter() - start_perf_time
                end_time = timestamp_override + timedelta(seconds=duration_seconds)

        span.end(end_time=end_time)

        # Export span via SDK's mechanism
        export_result = self.client.export_span(span)
        logger.debug(
            f"Ended LangChain span: name={span.name}, "
            f"trace_id={span.trace_id}, span_id={span.span_id}, "
            f"export_success={export_result}"
        )

        # Restore previous context
        previous_span = run_data.get("previous_span")
        if previous_span is not None:
            set_current_span(previous_span)
        elif run_data.get("parent_run_id") is None:
            # Root span ended - clear context entirely
            clear_context()

        del self._runs[run_id_str]

    # Chain callbacks

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle chain start event."""
        try:
            name = self._extract_name(serialized, **kwargs)

            # Debug logging for LangGraph metadata detection
            has_lg_metadata = self._has_langgraph_metadata(metadata=metadata, tags=tags)
            logger.warning(
                f"on_chain_start: name={name}, parent_run_id={parent_run_id is not None}, "
                f"has_langgraph_metadata={has_lg_metadata}, "
                f"metadata_keys={list(metadata.keys()) if metadata else []}, "
                f"tags={tags}"
            )

            # Check for LangGraph metadata
            if parent_run_id and has_lg_metadata:
                self._langgraph_parent_ids.add(str(parent_run_id))

            # Check for thread-based trace continuation (for LangGraph resume)
            thread_id = None
            if metadata:
                thread_id = metadata.get("langgraph_thread_id") or metadata.get("thread_id")
                if thread_id and thread_id in self._thread_trace_map and parent_run_id is None:
                    # This is a root span resuming an existing trace
                    self._continuation_trace_id = self._thread_trace_map[thread_id]

            # Skip the resume graph span entirely - reparent children under original root
            # Also skip nested graph roots whose parent is a reparented span
            # Only skip if it looks like a graph root (no LangGraph metadata), not a node
            is_nested_graph_root = (
                parent_run_id and
                str(parent_run_id) in self._reparented_spans and
                not has_lg_metadata  # Graph roots don't have LangGraph metadata, nodes do
            )
            should_skip_as_resume_root = (
                parent_run_id is None and self._continuation_parent_id
            ) or is_nested_graph_root

            if should_skip_as_resume_root:
                # This is a resume graph span - don't create a span for it
                # Capture the resume value from inputs (e.g. Command(resume=...))
                resume_value = str(self._serialize_for_json(inputs)) if inputs else None
                self._skipped_resume_roots[str(run_id)] = {
                    "parent_id": self._continuation_parent_id,
                    "resume_value": resume_value,
                }
                logger.info(
                    f"Skipping resume graph span: name={name}, run_id={run_id}, "
                    f"children will be reparented under {self._continuation_parent_id}"
                )
                return

            # If parent was a skipped resume root, reparent under the original root
            is_first_resume_child = False
            resume_value = None
            if parent_run_id and str(parent_run_id) in self._skipped_resume_roots:
                skipped_info = self._skipped_resume_roots[str(parent_run_id)]
                original_parent_id = skipped_info["parent_id"]
                # Only mark the first child as resume
                if not skipped_info.get("first_child_marked"):
                    resume_value = skipped_info.get("resume_value")
                    is_first_resume_child = True
                    skipped_info["first_child_marked"] = True
                # Override parent_run_id to None so _start_span uses continuation_parent_id
                # Track this span as reparented so nested graph roots also get skipped
                self._reparented_spans.add(str(run_id))
                parent_run_id = None
                self._continuation_parent_id = original_parent_id
            # Also reparent node spans whose parent is a reparented span (not a graph root)
            elif parent_run_id and str(parent_run_id) in self._reparented_spans:
                # This is a node span nested under a reparented node - also reparent it
                logger.warning(
                    f"Reparenting nested span: name={name}, run_id={run_id}, "
                    f"parent_run_id={parent_run_id} (in _reparented_spans), "
                    f"continuation_parent_id={self._continuation_parent_id}"
                )
                self._reparented_spans.add(str(run_id))
                parent_run_id = None
                # _continuation_parent_id is already set from when the parent was reparented
            else:
                # Not reparenting - log why
                parent_in_skipped = str(parent_run_id) in self._skipped_resume_roots if parent_run_id else False
                parent_in_reparented = str(parent_run_id) in self._reparented_spans if parent_run_id else False
                logger.warning(
                    f"NOT reparenting span: name={name}, run_id={run_id}, "
                    f"parent_run_id={parent_run_id}, "
                    f"parent_in_skipped={parent_in_skipped}, parent_in_reparented={parent_in_reparented}, "
                    f"_reparented_spans={list(self._reparented_spans)[:5]}"  # First 5 for brevity
                )

            self._start_span(run_id, parent_run_id, name, SpanKind.INTERNAL, SpanType.CHAIN)

            if str(run_id) in self._runs:
                span = self._runs[str(run_id)]["span"]
                serialized_inputs = self._serialize_for_json(inputs)
                span.set_attribute(self.ATTR_LANGCHAIN_INPUT, json.dumps(serialized_inputs, default=str))

                # Mark first resume span with resume attributes
                if is_first_resume_child:
                    span.set_attribute(self.ATTR_LANGGRAPH_RESUME, True)
                    if resume_value:
                        span.set_attribute(self.ATTR_LANGGRAPH_RESUME_VALUE, resume_value)

                # Set metadata as attributes
                if metadata:
                    for key, value in metadata.items():
                        if isinstance(value, (str, int, float, bool)):
                            span.set_attribute(f"langchain.metadata.{key}", value)
                        else:
                            span.set_attribute(f"langchain.metadata.{key}", json.dumps(value, default=str))

                if tags:
                    span.set_attribute("langchain.tags", json.dumps(tags))

                # Try to extract graph name from LangGraph metadata if agent_name not set
                if not self._agent_name and metadata:
                    graph_name = metadata.get("langgraph_checkpoint_ns") or metadata.get("name")
                    if graph_name:
                        span.set_attribute(self.ATTR_AGENT_NAME, graph_name)

                # Store thread_id -> trace_id mapping for future resume
                if thread_id and parent_run_id is None and not is_first_resume_child:
                    self._thread_trace_map[thread_id] = span.trace_id
                    span.set_attribute(self.ATTR_LANGGRAPH_THREAD_ID, thread_id)

        except Exception as e:
            logger.error(f"Error in on_chain_start: {e}")

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle chain end event."""
        try:
            # Skip if this was a skipped resume root span
            if str(run_id) in self._skipped_resume_roots:
                logger.info(f"Skipping on_chain_end for skipped resume root: run_id={run_id}")
                del self._skipped_resume_roots[str(run_id)]
                return

            if str(run_id) in self._runs:
                span = self._runs[str(run_id)]["span"]
                serialized_outputs = self._serialize_for_json(outputs)
                span.set_attribute(self.ATTR_LANGCHAIN_OUTPUT, json.dumps(serialized_outputs, default=str))

                # Handle LangGraph parent detection
                is_in_langgraph_parents = str(run_id) in self._langgraph_parent_ids
                logger.warning(
                    f"on_chain_end: name={span.name}, run_id={run_id}, "
                    f"parent_run_id={parent_run_id is not None}, "
                    f"is_in_langgraph_parents={is_in_langgraph_parents}, "
                    f"langgraph_parent_ids={list(self._langgraph_parent_ids)}"
                )
                if is_in_langgraph_parents:
                    if parent_run_id is None:
                        logger.warning(f"Setting span type to AGENT for {span.name}")
                        # Update both the span_type property and the span.type attribute
                        span.span_type = SpanType.AGENT
                        span.set_attribute("span.type", SpanType.AGENT.value)
                    self._langgraph_parent_ids.discard(str(run_id))

            self._end_span(run_id)

        except Exception as e:
            logger.error(f"Error in on_chain_end: {e}")

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle chain error event."""
        try:
            # Skip if this was a skipped resume root span
            if str(run_id) in self._skipped_resume_roots:
                logger.info(f"Skipping on_chain_error for skipped resume root: run_id={run_id}")
                del self._skipped_resume_roots[str(run_id)]
                return

            # Debug logging for interrupt/cancel detection (using warning to ensure visibility)
            is_interrupt = self._is_langgraph_interrupt(error)
            is_cancelled = self._is_cancelled_error(error)
            logger.warning(
                f"on_chain_error called: error_type={type(error).__name__}, "
                f"has_value={hasattr(error, 'value')}, "
                f"has_interrupts={hasattr(error, 'interrupts')}, "
                f"is_interrupt={is_interrupt}, is_cancelled={is_cancelled}"
            )
            if is_interrupt:
                interrupt_info = self._extract_interrupt_info(error)
                logger.warning(f"Interrupt info extracted: {interrupt_info}")

            # Handle LangGraph parent detection - set AGENT type even on error/interrupt/cancel
            # (mirrors the logic in on_chain_end)
            if str(run_id) in self._runs:
                span = self._runs[str(run_id)]["span"]
                is_in_langgraph_parents = str(run_id) in self._langgraph_parent_ids
                if is_in_langgraph_parents and parent_run_id is None:
                    logger.warning(f"Setting span type to AGENT for {span.name} (in on_chain_error)")
                    span.span_type = SpanType.AGENT
                    span.set_attribute("span.type", SpanType.AGENT.value)

            self._langgraph_parent_ids.discard(str(run_id))
            self._end_span(run_id, error)
        except Exception as e:
            logger.error(f"Error in on_chain_error: {e}")

    # LLM callbacks

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle LLM start event (for non-chat models)."""
        try:
            name = self._extract_name(serialized, **kwargs)
            self._start_span(run_id, parent_run_id, name, SpanKind.CLIENT, SpanType.GENERATION)

            # Initialize TTFT tracking (None means waiting for first token)
            self._first_token_times[str(run_id)] = None

            if str(run_id) in self._runs:
                span = self._runs[str(run_id)]["span"]
                span.set_attribute(self.ATTR_LLM_SYSTEM, "langchain")
                span.set_attribute(self.ATTR_LLM_PROMPT, json.dumps(prompts, default=str))

                # Extract model name and parameters from serialized kwargs
                if "kwargs" in serialized:
                    model_kwargs = serialized["kwargs"]
                    # Check for model_name first, then model (some providers use model)
                    model_name = model_kwargs.get("model_name") or model_kwargs.get("model")
                    if model_name:
                        span.set_attribute(self.ATTR_LLM_MODEL, model_name)
                        # Cache for fallback in on_llm_end (streaming may not have model in response)
                        self._runs[str(run_id)]["cached_model_name"] = model_name
                    # Extract model parameters (OTEL standard)
                    self._set_model_parameters(span, model_kwargs)

        except Exception as e:
            logger.error(f"Error in on_llm_start: {e}")

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle chat model start event."""
        try:
            name = self._extract_name(serialized, **kwargs)
            self._start_span(run_id, parent_run_id, name, SpanKind.CLIENT, SpanType.GENERATION)

            # Initialize TTFT tracking (None means waiting for first token)
            self._first_token_times[str(run_id)] = None

            if str(run_id) in self._runs:
                span = self._runs[str(run_id)]["span"]
                span.set_attribute(self.ATTR_LLM_SYSTEM, "langchain")

                # Serialize messages
                flat_messages = [msg for batch in messages for msg in batch]
                serialized_messages = [self._serialize_for_json(msg) for msg in flat_messages]
                span.set_attribute(self.ATTR_LLM_PROMPT, json.dumps(serialized_messages, default=str))

                # Extract model name and parameters from serialized kwargs
                if "kwargs" in serialized:
                    model_kwargs = serialized["kwargs"]
                    # Check for model_name first, then model (ChatAnthropic uses model)
                    model_name = model_kwargs.get("model_name") or model_kwargs.get("model")
                    if model_name:
                        span.set_attribute(self.ATTR_LLM_MODEL, model_name)
                        # Cache for fallback in on_llm_end (streaming may not have model in response)
                        self._runs[str(run_id)]["cached_model_name"] = model_name
                    # Extract model parameters (OTEL standard)
                    self._set_model_parameters(span, model_kwargs)

                # Include tools if present
                tools = kwargs.get("invocation_params", {}).get("tools")
                if tools:
                    span.set_attribute("langchain.tools", json.dumps(tools, default=str))

        except Exception as e:
            logger.error(f"Error in on_chat_model_start: {e}")

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle LLM end event."""
        try:
            run_id_str = str(run_id)
            if run_id_str in self._runs:
                span = self._runs[run_id_str]["span"]

                # Extract response
                if response.generations and response.generations[0]:
                    gen = response.generations[0][0]
                    if hasattr(gen, "message"):
                        serialized_output = self._serialize_for_json(gen.message)
                        span.set_attribute(self.ATTR_LLM_COMPLETION, json.dumps(serialized_output, default=str))
                    elif hasattr(gen, "text"):
                        span.set_attribute(self.ATTR_LLM_COMPLETION, json.dumps({"text": gen.text}, default=str))

                # Extract usage and model name - check multiple locations
                usage = None
                model_name = None

                # First try: llm_output (non-streaming)
                if response.llm_output:
                    usage = response.llm_output.get("token_usage") or response.llm_output.get("usage")
                    # Extract model name from llm_output (check both keys)
                    model_name = response.llm_output.get("model_name") or response.llm_output.get("model")

                # Second try: usage_metadata on the message (streaming)
                if not usage and response.generations and response.generations[0]:
                    gen = response.generations[0][0]
                    if hasattr(gen, "message") and hasattr(gen.message, "usage_metadata"):
                        usage_metadata = gen.message.usage_metadata
                        if usage_metadata:
                            # usage_metadata is a dict with input_tokens/output_tokens keys
                            usage = {
                                "prompt_tokens": usage_metadata.get("input_tokens", 0) or 0,
                                "completion_tokens": usage_metadata.get("output_tokens", 0) or 0,
                                "total_tokens": usage_metadata.get("total_tokens", 0) or 0,
                            }

                # Try to get model from response_metadata (streaming)
                if not model_name and response.generations and response.generations[0]:
                    gen = response.generations[0][0]
                    if hasattr(gen, "message") and hasattr(gen.message, "response_metadata"):
                        response_metadata = gen.message.response_metadata
                        if response_metadata:
                            model_name = response_metadata.get("model_name") or response_metadata.get("model")

                # Fallback: use cached model from on_chat_model_start/on_llm_start
                if not model_name:
                    model_name = self._runs[run_id_str].get("cached_model_name")

                if model_name:
                    span.set_attribute(self.ATTR_LLM_MODEL, model_name)

                if usage:
                    span.set_attribute(self.ATTR_LLM_PROMPT_TOKENS, usage.get("prompt_tokens", 0))
                    span.set_attribute(self.ATTR_LLM_COMPLETION_TOKENS, usage.get("completion_tokens", 0))
                    span.set_attribute(self.ATTR_LLM_TOTAL_TOKENS, usage.get("total_tokens", 0))

                # Calculate and set TTFT for streaming calls
                first_token_time = self._first_token_times.pop(run_id_str, None)
                if first_token_time is not None:
                    # Streaming call - calculate TTFT
                    start_perf_time = self._runs[run_id_str].get("start_perf_time")
                    if start_perf_time is not None:
                        ttft_ms = (first_token_time - start_perf_time) * 1000
                        span.set_attribute(self.ATTR_TTFT_MS, ttft_ms)
                        span.set_attribute(self.ATTR_STREAMING, True)
                else:
                    # Clean up tracking state even if no first token was received
                    self._first_token_times.pop(run_id_str, None)

            self._end_span(run_id)

        except Exception as e:
            logger.error(f"Error in on_llm_end: {e}")

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle LLM error event."""
        try:
            # Clean up TTFT tracking state
            self._first_token_times.pop(str(run_id), None)
            self._end_span(run_id, error)
        except Exception as e:
            logger.error(f"Error in on_llm_error: {e}")

    def on_llm_new_token(
        self,
        token: str,
        *,
        chunk: Any = None,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle new token event for streaming LLM calls.

        This callback captures the time-to-first-token (TTFT) metric by
        recording the timestamp when the first token is received.

        Args:
            token: The new token string
            chunk: Optional generation chunk object
            run_id: Unique run identifier
            parent_run_id: Parent run identifier (for nesting)
            **kwargs: Additional arguments
        """
        try:
            run_id_str = str(run_id)

            # Only record the first token time
            if run_id_str in self._first_token_times and self._first_token_times[run_id_str] is None:
                self._first_token_times[run_id_str] = time.perf_counter()

        except Exception as e:
            logger.debug(f"Error in on_llm_new_token: {e}")

    # Tool callbacks

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle tool start event."""
        try:
            name = self._extract_name(serialized, **kwargs)
            self._start_span(run_id, parent_run_id, name, SpanKind.INTERNAL, SpanType.TOOL)

            if str(run_id) in self._runs:
                span = self._runs[str(run_id)]["span"]
                input_data = inputs if inputs else input_str
                serialized_input = self._serialize_for_json(input_data)
                span.set_attribute("tool.input", json.dumps(serialized_input, default=str))

        except Exception as e:
            logger.error(f"Error in on_tool_start: {e}")

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle tool end event."""
        try:
            if str(run_id) in self._runs:
                span = self._runs[str(run_id)]["span"]
                serialized_output = self._serialize_for_json(output)
                # Truncate large outputs
                output_str = json.dumps(serialized_output, default=str)
                if len(output_str) > 10000:
                    output_str = output_str[:10000] + "..."
                span.set_attribute("tool.output", output_str)

            self._end_span(run_id)

        except Exception as e:
            logger.error(f"Error in on_tool_end: {e}")

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle tool error event."""
        try:
            self._end_span(run_id, error)
        except Exception as e:
            logger.error(f"Error in on_tool_error: {e}")

    # Retriever callbacks

    def on_retriever_start(
        self,
        serialized: dict[str, Any],
        query: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle retriever start event."""
        try:
            name = self._extract_name(serialized, **kwargs)
            self._start_span(run_id, parent_run_id, name, SpanKind.INTERNAL, SpanType.RETRIEVAL)

            if str(run_id) in self._runs:
                span = self._runs[str(run_id)]["span"]
                span.set_attribute("retriever.query", query)

        except Exception as e:
            logger.error(f"Error in on_retriever_start: {e}")

    def on_retriever_end(
        self,
        documents: Sequence[Document],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle retriever end event."""
        try:
            if str(run_id) in self._runs:
                span = self._runs[str(run_id)]["span"]
                span.set_attribute("retriever.document_count", len(documents))

                # Serialize documents
                serialized_docs = [self._serialize_for_json(doc) for doc in documents]
                docs_str = json.dumps(serialized_docs, default=str)
                if len(docs_str) > 10000:
                    docs_str = docs_str[:10000] + "..."
                span.set_attribute("retriever.documents", docs_str)

            self._end_span(run_id)

        except Exception as e:
            logger.error(f"Error in on_retriever_end: {e}")

    def on_retriever_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle retriever error event."""
        try:
            self._end_span(run_id, error)
        except Exception as e:
            logger.error(f"Error in on_retriever_error: {e}")

    # Agent callbacks

    def on_agent_action(
        self,
        action: AgentAction,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle agent action event."""
        try:
            parent_id = str(parent_run_id) if parent_run_id else None
            if parent_id and parent_id in self._runs:
                span = self._runs[parent_id]["span"]
                action_data = {
                    "tool": action.tool,
                    "tool_input": action.tool_input,
                    "log": action.log if hasattr(action, "log") else None,
                }
                span.set_attribute(f"agent.action.{str(run_id)[:8]}", json.dumps(action_data, default=str))

        except Exception as e:
            logger.error(f"Error in on_agent_action: {e}")

    def on_agent_finish(
        self,
        finish: AgentFinish,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle agent finish event."""
        try:
            parent_id = str(parent_run_id) if parent_run_id else None
            if parent_id and parent_id in self._runs:
                span = self._runs[parent_id]["span"]
                finish_data = {
                    "return_values": finish.return_values,
                    "log": finish.log if hasattr(finish, "log") else None,
                }
                span.set_attribute("agent.finish", json.dumps(finish_data, default=str))

        except Exception as e:
            logger.error(f"Error in on_agent_finish: {e}")