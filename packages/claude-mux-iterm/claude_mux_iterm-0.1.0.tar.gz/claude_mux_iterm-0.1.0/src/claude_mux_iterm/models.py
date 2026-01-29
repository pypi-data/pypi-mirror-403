"""Pydantic models for Claude Mux iTerm."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class MessageType(str, Enum):
    """Types of inter-session messages."""

    TEXT = "text"
    BROADCAST = "broadcast"


class MessagePriority(str, Enum):
    """Message priority levels."""

    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageMetadata(BaseModel):
    """Metadata for inter-session messages."""

    priority: MessagePriority = Field(default=MessagePriority.NORMAL)
    ttl_seconds: int = Field(default=3600, description="Time to live in seconds")


class Message(BaseModel):
    """Complete inter-session message structure."""

    protocol_version: str = Field(default="1.0")
    message_id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:16]}")
    message_type: MessageType
    source_task_id: str = Field(description="Source task ID")
    target_task_id: str | None = Field(
        default=None, description="Target task ID (None for broadcasts)"
    )
    timestamp: datetime = Field(default_factory=utcnow)
    content: str = Field(description="Message content")
    metadata: MessageMetadata = Field(default_factory=MessageMetadata)
    acknowledged: bool = Field(default=False, description="Whether message was acknowledged")

    def to_wire_format(self) -> str:
        """Convert message to human-readable format for injection.

        Creates a clear message that Claude can understand and respond to.
        """
        priority_prefix = ""
        if self.metadata.priority == MessagePriority.URGENT:
            priority_prefix = "[URGENT] "
        elif self.metadata.priority == MessagePriority.HIGH:
            priority_prefix = "[HIGH PRIORITY] "

        return f"{priority_prefix}Message from {self.source_task_id}: {self.content}"

    @classmethod
    def from_wire_format(cls, wire_str: str) -> "Message":
        """Parse message from wire format."""
        import json

        start_tag = "[CLAUDE-MUX-ITERM-MESSAGE]"
        end_tag = "[/CLAUDE-MUX-ITERM-MESSAGE]"
        start_idx = wire_str.find(start_tag) + len(start_tag)
        end_idx = wire_str.find(end_tag)
        json_str = wire_str[start_idx:end_idx].strip()
        return cls.model_validate(json.loads(json_str))


class Session(BaseModel):
    """Registered iTerm2 session information."""

    task_id: str = Field(description="Task identifier for this session")
    iterm_session_id: str = Field(description="iTerm2 session unique ID")
    registered_at: datetime = Field(default_factory=utcnow)
    last_seen: datetime = Field(default_factory=utcnow)


# ============================================================================
# Result Models
# ============================================================================


class RegisterSessionResult(BaseModel):
    """Result of registering a session."""

    success: bool = Field(description="Whether the registration succeeded")
    task_id: str = Field(default="", description="The registered task ID")
    session_id: str = Field(default="", description="The iTerm2 session ID")
    message: str = Field(description="Human-readable status message")


class ListSessionsResult(BaseModel):
    """Result of listing sessions."""

    sessions: list[Session] = Field(default_factory=list, description="List of active sessions")
    total_count: int = Field(default=0, description="Total number of sessions")
    message: str = Field(default="", description="Human-readable status message")


class SendMessageResult(BaseModel):
    """Result of sending a message."""

    success: bool = Field(description="Whether the message was sent")
    message_id: str = Field(default="", description="ID of the sent message")
    target_task_id: str | None = Field(default=None, description="Target task ID")
    delivered_to: list[str] = Field(
        default_factory=list, description="List of task IDs message was delivered to"
    )
    message: str = Field(description="Human-readable status message")


class MessageInfo(BaseModel):
    """Information about a message for listing."""

    message_id: str = Field(description="Message ID")
    message_type: MessageType = Field(description="Type of message")
    source_task_id: str = Field(description="Task ID that sent the message")
    content: str = Field(description="Message content or summary")
    received_at: datetime = Field(description="When the message was received")
    priority: MessagePriority = Field(default=MessagePriority.NORMAL)
    acknowledged: bool = Field(default=False, description="Whether message was acknowledged")


class ListMessagesResult(BaseModel):
    """Result of listing messages in inbox."""

    messages: list[MessageInfo] = Field(default_factory=list)
    unread_count: int = Field(default=0)
    message: str = Field(description="Human-readable status message")


class AcknowledgeMessageResult(BaseModel):
    """Result of acknowledging a message."""

    success: bool = Field(description="Whether the acknowledgement succeeded")
    message_id: str = Field(default="", description="The acknowledged message ID")
    message: str = Field(description="Human-readable status message")
