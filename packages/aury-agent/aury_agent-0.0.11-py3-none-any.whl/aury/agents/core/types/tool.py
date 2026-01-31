"""Tool-related type definitions."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable

from .session import generate_id


@dataclass
class ToolInfo:
    """Tool metadata for LLM."""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema
    
    def to_llm_schema(self) -> dict[str, Any]:
        """Convert to LLM API format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }


@dataclass
class ToolContext:
    """Context passed to tool execution."""
    session_id: str
    invocation_id: str
    block_id: str
    call_id: str
    agent: str
    abort_signal: asyncio.Event
    update_metadata: Callable[[dict[str, Any]], Awaitable[None]]
    
    # Optional usage tracker
    usage: Any | None = None  # UsageTracker
    
    # Branch for sub-agent isolation
    branch: str | None = None
    
    # Caller's middleware chain (for sub-agent inheritance)
    middleware: Any | None = None  # MiddlewareChain
    
    async def emit(self, block: Any) -> None:
        """Emit a block event.
        
        Uses the global emit function via ContextVar.
        Works automatically when called within agent.run() context.
        
        Args:
            block: BlockEvent to emit
        """
        from ..context import emit as global_emit
        
        # Fill in IDs if not set
        if hasattr(block, 'session_id') and not block.session_id:
            block.session_id = self.session_id
        if hasattr(block, 'invocation_id') and not block.invocation_id:
            block.invocation_id = self.invocation_id
        
        await global_emit(block)
    
    async def emit_hitl(self, request_id: str, data: dict[str, Any]) -> None:
        """Emit a HITL request block.
        
        Convenience method for tools that need user interaction.
        The data format is flexible - can be anything the frontend understands:
        - Choice selection (choices, radio, checkbox)
        - Text input (text, textarea, number)
        - Confirmation (yes/no, approve/reject)
        - Rich content (product cards, file selection, etc.)
        
        Args:
            request_id: Unique ID for this HITL request
            data: Arbitrary data dict for frontend to render.
                  Common fields: type, question, choices, default, context
        """
        from .block import BlockEvent, BlockKind
        
        await self.emit(BlockEvent(
            kind=BlockKind.HITL_REQUEST,
            data={"request_id": request_id, **data},
        ))


@dataclass
class ToolResult:
    """Tool execution result for LLM.
    
    Supports dual output for context management:
    - output: Complete output (raw), for storage and recall
    - truncated_output: Shortened output for context window
    
    If truncated_output is not provided, it defaults to output.
    """
    output: str  # Complete output (raw)
    is_error: bool = False
    truncated_output: str | None = None  # Shortened output (defaults to output)
    
    def __post_init__(self):
        # Default truncated to output if not provided
        if self.truncated_output is None:
            self.truncated_output = self.output
    
    @classmethod
    def success(
        cls,
        output: str,
        *,
        truncated_output: str | None = None,
    ) -> ToolResult:
        """Create a successful result.
        
        Args:
            output: Complete output (raw)
            truncated_output: Shortened output for context (defaults to output)
        """
        return cls(
            output=output,
            is_error=False,
            truncated_output=truncated_output,
        )
    
    @classmethod
    def error(cls, message: str) -> ToolResult:
        """Create an error result."""
        return cls(output=message, is_error=True)


class ToolInvocationState(Enum):
    """Tool invocation state machine."""
    PARTIAL_CALL = "partial-call"  # Arguments streaming
    CALL = "call"  # Arguments complete, ready to execute
    RESULT = "result"  # Execution complete


@dataclass
class ToolInvocation:
    """Tool invocation tracking (state machine)."""
    tool_call_id: str
    tool_name: str
    state: ToolInvocationState = ToolInvocationState.PARTIAL_CALL
    args: dict[str, Any] = field(default_factory=dict)
    args_raw: str = ""  # Raw JSON string for streaming
    result: str | None = None
    truncated_result: str | None = None  # Shortened result for context window
    is_error: bool = False
    
    # Timing
    time: dict[str, datetime | None] = field(
        default_factory=lambda: {"start": None, "end": None}
    )
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def mark_call_complete(self) -> None:
        """Mark arguments as complete."""
        self.state = ToolInvocationState.CALL
        self.time["start"] = datetime.now()
    
    def mark_result(
        self,
        result: str,
        is_error: bool = False,
        truncated_result: str | None = None,
    ) -> None:
        """Mark execution complete.
        
        Args:
            result: Complete result (raw)
            is_error: Whether this is an error result
            truncated_result: Shortened result for context window (defaults to result)
        """
        self.state = ToolInvocationState.RESULT
        self.result = result
        self.truncated_result = truncated_result if truncated_result is not None else result
        self.is_error = is_error
        self.time["end"] = datetime.now()
    
    @property
    def duration_ms(self) -> int | None:
        """Get execution duration."""
        if self.time["start"] and self.time["end"]:
            return int((self.time["end"] - self.time["start"]).total_seconds() * 1000)
        return None


class BaseTool:
    """Base class for tools with common functionality."""
    
    _name: str = "base_tool"
    _description: str = "Base tool"
    _parameters: dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": [],
    }
    _config: ToolConfig | None = None
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def parameters(self) -> dict[str, Any]:
        return self._parameters
    
    @property
    def config(self) -> ToolConfig:
        """Get tool config. Returns default config if not set."""
        return self._config or ToolConfig()
    
    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        """Override this method."""
        raise NotImplementedError("Subclass must implement execute()")
    
    def get_info(self) -> ToolInfo:
        """Get tool info."""
        return ToolInfo(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )


@dataclass
class ToolConfig:
    """Tool configuration."""
    is_resumable: bool = False  # Supports pause/resume
    timeout: float | None = None  # Execution timeout in seconds
    requires_permission: bool = False  # Needs HITL approval
    permission_message: str | None = None
    stream_arguments: bool = False  # Stream tool arguments to client
    
    # Retry configuration
    max_retries: int = 0  # 0 = no retry
    retry_delay: float = 1.0  # Base delay between retries (seconds)
    retry_backoff: float = 2.0  # Exponential backoff multiplier