"""FastMCP server with tool definitions for Claude Mux iTerm."""

from mcp.server.fastmcp import FastMCP

from . import messaging as msg
from . import session_registry as registry
from .exceptions import (
    ClaudeMuxItermError,
    ITermNotAvailableError,
    MessageDeliveryError,
    SessionExistsError,
    SessionNotFoundError,
)
from .models import (
    AcknowledgeMessageResult,
    ListMessagesResult,
    ListSessionsResult,
    MessageInfo,
    MessagePriority,
    RegisterSessionResult,
    SendMessageResult,
)

mcp = FastMCP(name="Claude Mux iTerm")


@mcp.tool()
def register_session(task_id: str) -> RegisterSessionResult:
    """Register the current iTerm2 session with a task ID.

    This allows other Claude Code sessions to find and communicate with
    this session using the task ID.

    Args:
        task_id: Unique identifier for this session (e.g., "task-a", "feature-auth").
            Must be alphanumeric with hyphens/underscores, max 64 chars.

    Returns:
        Result indicating whether registration succeeded.

    Example:
        >>> register_session("task-a")
        RegisterSessionResult(success=True, task_id="task-a", ...)
    """
    try:
        session = registry.register_session(task_id)
        return RegisterSessionResult(
            success=True,
            task_id=session.task_id,
            session_id=session.iterm_session_id,
            message=f"Session registered as '{task_id}'. "
            "Other sessions can now send messages to this task ID.",
        )
    except SessionExistsError as e:
        return RegisterSessionResult(
            success=False,
            message=str(e),
        )
    except ITermNotAvailableError:
        return RegisterSessionResult(
            success=False,
            message="iTerm2 is not running. Please run this from within iTerm2.",
        )
    except ClaudeMuxItermError as e:
        return RegisterSessionResult(
            success=False,
            message=str(e),
        )
    except Exception as e:
        return RegisterSessionResult(
            success=False,
            message=f"Unexpected error: {e}",
        )


@mcp.tool()
def list_sessions() -> ListSessionsResult:
    """List all registered active iTerm2 sessions.

    Use this to discover which other Claude Code sessions you can
    communicate with.

    Returns:
        List of active sessions with their task IDs.

    Example:
        >>> list_sessions()
        ListSessionsResult(
            sessions=[
                Session(task_id="task-a", ...),
                Session(task_id="task-b", ...),
            ],
            total_count=2,
            ...
        )
    """
    try:
        # Clean up stale sessions first
        registry.cleanup_stale_sessions()

        sessions = registry.list_active_sessions()
        return ListSessionsResult(
            sessions=sessions,
            total_count=len(sessions),
            message=f"Found {len(sessions)} active session(s).",
        )
    except ITermNotAvailableError:
        return ListSessionsResult(
            sessions=[],
            total_count=0,
            message="iTerm2 is not running.",
        )
    except Exception as e:
        return ListSessionsResult(
            sessions=[],
            total_count=0,
            message=f"Error listing sessions: {e}",
        )


@mcp.tool()
def send_message(
    target_task_id: str,
    content: str,
    source_task_id: str,
    priority: str = "normal",
) -> SendMessageResult:
    """Send a message to a specific Claude Code session.

    Use this to communicate with another Claude instance working on a
    related task. The message will be injected into the target session.

    Args:
        target_task_id: Task ID of the target session (e.g., "task-b").
        content: The message content to send.
        source_task_id: Your current task ID (the sender).
        priority: Message priority: "normal", "high", or "urgent".

    Returns:
        Result indicating whether the message was sent.

    Example:
        >>> send_message("task-b", "PR merged to main, please pull latest", "task-a")
        SendMessageResult(success=True, message_id="msg_abc123", ...)
    """
    try:
        priority_enum = MessagePriority(priority)
    except ValueError:
        priority_enum = MessagePriority.NORMAL

    try:
        message, delivered_to = msg.send_message(
            source_task_id=source_task_id,
            target_task_id=target_task_id,
            content=content,
            priority=priority_enum,
        )

        return SendMessageResult(
            success=True,
            message_id=message.message_id,
            target_task_id=target_task_id,
            delivered_to=delivered_to,
            message=f"Message sent to {target_task_id}",
        )

    except SessionNotFoundError:
        return SendMessageResult(
            success=False,
            message=f"Target session for task '{target_task_id}' not found. "
            "Make sure the session is registered and running.",
        )
    except MessageDeliveryError as e:
        return SendMessageResult(
            success=False,
            message=f"Failed to deliver message: {e}",
        )
    except Exception as e:
        return SendMessageResult(
            success=False,
            message=f"Unexpected error: {e}",
        )


@mcp.tool()
def broadcast_message(
    content: str,
    source_task_id: str,
    priority: str = "normal",
) -> SendMessageResult:
    """Broadcast a message to all other active Claude Code sessions.

    Use this to notify all other sessions about important events,
    like when a PR is merged to main.

    Args:
        content: The message content to broadcast.
        source_task_id: Your current task ID (the sender).
        priority: Message priority: "normal", "high", or "urgent".

    Returns:
        Result indicating how many sessions received the message.

    Example:
        >>> broadcast_message("PR #123 merged to main, please pull latest", "task-a")
        SendMessageResult(success=True, delivered_to=["task-b", "task-c"], ...)
    """
    try:
        priority_enum = MessagePriority(priority)
    except ValueError:
        priority_enum = MessagePriority.NORMAL

    try:
        message, delivered_to = msg.broadcast_message(
            source_task_id=source_task_id,
            content=content,
            priority=priority_enum,
        )

        if delivered_to:
            return SendMessageResult(
                success=True,
                message_id=message.message_id,
                target_task_id=None,
                delivered_to=delivered_to,
                message=f"Message broadcast to {len(delivered_to)} session(s): "
                f"{', '.join(delivered_to)}",
            )
        else:
            return SendMessageResult(
                success=True,
                message_id=message.message_id,
                target_task_id=None,
                delivered_to=[],
                message="No other active sessions to broadcast to.",
            )

    except Exception as e:
        return SendMessageResult(
            success=False,
            message=f"Unexpected error: {e}",
        )


@mcp.tool()
def list_messages(
    current_task_id: str,
    unread_only: bool = False,
) -> ListMessagesResult:
    """List messages received by this session.

    Use this to see what other sessions have communicated to you.

    Args:
        current_task_id: Your current task ID.
        unread_only: Only show messages not yet acknowledged.

    Returns:
        List of messages with metadata.

    Example:
        >>> list_messages("task-a", unread_only=True)
        ListMessagesResult(messages=[...], unread_count=3, ...)
    """
    try:
        messages = msg.get_messages(current_task_id, unread_only=unread_only)

        message_infos = [
            MessageInfo(
                message_id=m.message_id,
                message_type=m.message_type,
                source_task_id=m.source_task_id,
                content=m.content[:100] + "..." if len(m.content) > 100 else m.content,
                received_at=m.timestamp,
                priority=m.metadata.priority,
                acknowledged=m.acknowledged,
            )
            for m in messages
        ]

        unread_count = sum(1 for m in messages if not m.acknowledged)

        return ListMessagesResult(
            messages=message_infos,
            unread_count=unread_count,
            message=f"Found {len(message_infos)} message(s), {unread_count} unread.",
        )

    except Exception as e:
        return ListMessagesResult(
            messages=[],
            unread_count=0,
            message=f"Error listing messages: {e}",
        )


@mcp.tool()
def acknowledge_message(
    message_id: str,
    current_task_id: str,
) -> AcknowledgeMessageResult:
    """Mark a message as read/acknowledged.

    Use this after you've processed a message to remove it from your
    unread messages.

    Args:
        message_id: The ID of the message to acknowledge.
        current_task_id: Your current task ID.

    Returns:
        Result indicating whether acknowledgement succeeded.

    Example:
        >>> acknowledge_message("msg_abc123", "task-a")
        AcknowledgeMessageResult(success=True, ...)
    """
    try:
        success = msg.acknowledge_message(current_task_id, message_id)

        if success:
            return AcknowledgeMessageResult(
                success=True,
                message_id=message_id,
                message=f"Message {message_id} acknowledged.",
            )
        else:
            return AcknowledgeMessageResult(
                success=False,
                message_id=message_id,
                message=f"Message {message_id} not found in inbox.",
            )

    except Exception as e:
        return AcknowledgeMessageResult(
            success=False,
            message=f"Error acknowledging message: {e}",
        )
