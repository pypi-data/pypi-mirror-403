"""Control flow signals for agent execution.

These are NOT exceptions - they are control flow signals that inherit from
BaseException to avoid being caught by generic `except Exception` handlers.

Similar to KeyboardInterrupt and SystemExit, these signals control execution
flow rather than indicate errors.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class SuspendSignal(BaseException):
    """Base class for suspension signals.
    
    Signals that execution should be suspended (not failed).
    Inherits from BaseException so `except Exception` won't catch it.
    
    Usage:
        try:
            await agent.run()
        except SuspendSignal as s:
            # Handle suspension (HITL, pause, etc.)
            handle_suspend(s)
        except Exception as e:
            # Handle actual errors
            handle_error(e)
    """
    pass


@dataclass
class HITLSuspend(SuspendSignal):
    """Signal for Human-in-the-Loop suspension.
    
    Raised when agent needs human input to continue.
    Contains all information needed to:
    1. Display the request to user
    2. Resume execution after user responds
    
    Attributes:
        request_id: Unique ID for matching response
        request_type: Type of request (ask_user, confirm, form, etc.)
        message: Display message for user
        options: Optional list of choices
        node_id: Workflow node ID if triggered from workflow
        tool_name: Tool name if triggered from tool
        block_id: Associated UI block ID
        metadata: Additional context
    """
    request_id: str
    request_type: str = "ask_user"
    message: str | None = None
    options: list[str] | None = None
    node_id: str | None = None
    tool_name: str | None = None
    block_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Initialize BaseException with a message
        super().__init__(f"HITL suspend: {self.request_type} ({self.request_id})")
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage/transmission."""
        return {
            "request_id": self.request_id,
            "request_type": self.request_type,
            "message": self.message,
            "options": self.options,
            "node_id": self.node_id,
            "tool_name": self.tool_name,
            "block_id": self.block_id,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HITLSuspend":
        """Create from dictionary."""
        return cls(
            request_id=data["request_id"],
            request_type=data.get("request_type", "ask_user"),
            message=data.get("message"),
            options=data.get("options"),
            node_id=data.get("node_id"),
            tool_name=data.get("tool_name"),
            block_id=data.get("block_id"),
            metadata=data.get("metadata", {}),
        )


class PauseSuspend(SuspendSignal):
    """Signal for manual pause (user-initiated).
    
    Raised when user requests to pause execution.
    """
    
    def __init__(self, reason: str = "User requested pause"):
        self.reason = reason
        super().__init__(reason)


__all__ = [
    "SuspendSignal",
    "HITLSuspend",
    "PauseSuspend",
]
