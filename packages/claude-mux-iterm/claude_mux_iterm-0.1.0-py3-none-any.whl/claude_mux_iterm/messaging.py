"""Inter-session messaging operations for Claude Mux iTerm."""

import json
from datetime import datetime, timezone
from pathlib import Path

from .exceptions import InvalidMessageError, MessageDeliveryError, SessionNotFoundError
from .iterm import session_exists, write_text_to_session
from .models import Message, MessageMetadata, MessagePriority, MessageType
from .session_registry import get_session_id_for_task, list_active_sessions

# Default message queue location
MESSAGE_QUEUE_DIR = Path.home() / ".claude-mux-iterm" / "messages"


def get_task_queue_dir(task_id: str) -> Path:
    """Get the message queue directory for a task.

    Args:
        task_id: The task ID.

    Returns:
        Path to the task's message queue directory.
    """
    return MESSAGE_QUEUE_DIR / task_id


def ensure_queue_structure(task_id: str) -> None:
    """Ensure the queue directory structure exists for a task.

    Args:
        task_id: The task ID.
    """
    base_dir = get_task_queue_dir(task_id)
    for subdir in ["inbox", "outbox", "delivered"]:
        (base_dir / subdir).mkdir(parents=True, exist_ok=True)


def save_message(message: Message, task_id: str, queue_type: str) -> Path:
    """Save a message to the appropriate queue.

    Args:
        message: The message to save.
        task_id: The task ID whose queue to save to.
        queue_type: One of "inbox", "outbox", or "delivered".

    Returns:
        Path to the saved message file.

    Raises:
        ValueError: If queue_type is invalid.
    """
    if queue_type not in ("inbox", "outbox", "delivered"):
        raise ValueError(f"Invalid queue type: {queue_type}")

    queue_dir = get_task_queue_dir(task_id) / queue_type
    queue_dir.mkdir(parents=True, exist_ok=True)

    file_path = queue_dir / f"{message.message_id}.json"
    file_path.write_text(message.model_dump_json(indent=2))
    return file_path


def load_message(file_path: Path) -> Message:
    """Load a message from a file.

    Args:
        file_path: Path to the message file.

    Returns:
        The loaded message.

    Raises:
        InvalidMessageError: If the message cannot be parsed.
    """
    try:
        data = json.loads(file_path.read_text())
        return Message.model_validate(data)
    except Exception as e:
        raise InvalidMessageError(f"Failed to load message from {file_path}: {e}") from e


def create_message(
    source_task_id: str,
    content: str,
    target_task_id: str | None = None,
    message_type: MessageType = MessageType.TEXT,
    priority: MessagePriority = MessagePriority.NORMAL,
) -> Message:
    """Create a new message.

    Args:
        source_task_id: Task ID of the sender.
        content: The message content.
        target_task_id: Task ID of the recipient (None for broadcasts).
        message_type: Type of message.
        priority: Message priority.

    Returns:
        The created message.
    """
    return Message(
        message_type=message_type,
        source_task_id=source_task_id,
        target_task_id=target_task_id,
        content=content,
        metadata=MessageMetadata(priority=priority),
    )


def deliver_message_to_session(message: Message, target_session_id: str) -> bool:
    """Deliver a message to an iTerm2 session via write text.

    Args:
        message: The message to deliver.
        target_session_id: The iTerm2 session ID to deliver to.

    Returns:
        True if delivery succeeded.

    Raises:
        MessageDeliveryError: If delivery fails.
    """
    if not session_exists(target_session_id):
        raise MessageDeliveryError(f"Target session not found: {target_session_id}")

    # Format the message for injection
    wire_format = message.to_wire_format()

    try:
        success = write_text_to_session(target_session_id, wire_format)
        if not success:
            raise MessageDeliveryError(f"Failed to write to session: {target_session_id}")
        return True
    except Exception as e:
        raise MessageDeliveryError(f"Failed to deliver message: {e}") from e


def send_message(
    source_task_id: str,
    target_task_id: str,
    content: str,
    priority: MessagePriority = MessagePriority.NORMAL,
) -> tuple[Message, list[str]]:
    """Send a message to a specific task.

    Args:
        source_task_id: Task ID of the sender.
        target_task_id: Task ID of the recipient.
        content: The message content.
        priority: Message priority.

    Returns:
        Tuple of (message, list of task IDs delivered to).

    Raises:
        SessionNotFoundError: If target session not found.
        MessageDeliveryError: If delivery fails.
    """
    # Create the message
    message = create_message(
        source_task_id=source_task_id,
        content=content,
        target_task_id=target_task_id,
        message_type=MessageType.TEXT,
        priority=priority,
    )

    # Get target session ID
    target_session_id = get_session_id_for_task(target_task_id)

    # Save to sender's outbox
    ensure_queue_structure(source_task_id)
    save_message(message, source_task_id, "outbox")

    # Save to recipient's inbox
    ensure_queue_structure(target_task_id)
    save_message(message, target_task_id, "inbox")

    # Deliver via iTerm2
    deliver_message_to_session(message, target_session_id)

    return message, [target_task_id]


def broadcast_message(
    source_task_id: str,
    content: str,
    priority: MessagePriority = MessagePriority.NORMAL,
) -> tuple[Message, list[str]]:
    """Broadcast a message to all other active sessions.

    Args:
        source_task_id: Task ID of the sender.
        content: The message content.
        priority: Message priority.

    Returns:
        Tuple of (message, list of task IDs delivered to).
    """
    # Create the message
    message = create_message(
        source_task_id=source_task_id,
        content=content,
        target_task_id=None,  # Broadcast
        message_type=MessageType.BROADCAST,
        priority=priority,
    )

    # Get all active sessions except sender
    active_sessions = list_active_sessions()
    delivered_to: list[str] = []

    # Save to sender's outbox
    ensure_queue_structure(source_task_id)
    save_message(message, source_task_id, "outbox")

    for session in active_sessions:
        if session.task_id == source_task_id:
            continue

        try:
            # Save to recipient's inbox
            ensure_queue_structure(session.task_id)
            save_message(message, session.task_id, "inbox")

            # Deliver via iTerm2
            deliver_message_to_session(message, session.iterm_session_id)
            delivered_to.append(session.task_id)
        except (SessionNotFoundError, MessageDeliveryError):
            # Skip sessions that fail delivery
            continue

    return message, delivered_to


def get_messages(
    task_id: str,
    unread_only: bool = False,
) -> list[Message]:
    """Get messages for a task.

    Args:
        task_id: The task ID to get messages for.
        unread_only: Only return unacknowledged messages.

    Returns:
        List of messages, sorted by timestamp.
    """
    ensure_queue_structure(task_id)
    inbox_dir = get_task_queue_dir(task_id) / "inbox"

    messages: list[Message] = []
    for file_path in sorted(inbox_dir.glob("*.json")):
        try:
            message = load_message(file_path)
            if unread_only and message.acknowledged:
                continue
            messages.append(message)
        except InvalidMessageError:
            continue

    # Sort by timestamp
    messages.sort(key=lambda m: m.timestamp)
    return messages


def acknowledge_message(task_id: str, message_id: str) -> bool:
    """Mark a message as acknowledged.

    Args:
        task_id: The task ID.
        message_id: The message ID to acknowledge.

    Returns:
        True if message was acknowledged, False if not found.
    """
    inbox_dir = get_task_queue_dir(task_id) / "inbox"
    delivered_dir = get_task_queue_dir(task_id) / "delivered"
    delivered_dir.mkdir(parents=True, exist_ok=True)

    file_path = inbox_dir / f"{message_id}.json"
    if not file_path.exists():
        # Check if already in delivered
        delivered_path = delivered_dir / f"{message_id}.json"
        if delivered_path.exists():
            return True  # Already acknowledged
        return False

    try:
        message = load_message(file_path)
        message.acknowledged = True

        # Move to delivered
        delivered_path = delivered_dir / f"{message_id}.json"
        delivered_path.write_text(message.model_dump_json(indent=2))
        file_path.unlink()

        return True
    except Exception:
        return False


def cleanup_expired_messages(max_age_hours: int = 24) -> int:
    """Clean up messages older than max_age_hours.

    Args:
        max_age_hours: Maximum age in hours for messages to keep.

    Returns:
        Count of removed messages.
    """
    if not MESSAGE_QUEUE_DIR.exists():
        return 0

    count = 0
    cutoff = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)

    for task_dir in MESSAGE_QUEUE_DIR.iterdir():
        if not task_dir.is_dir():
            continue
        for queue_dir in task_dir.iterdir():
            if not queue_dir.is_dir():
                continue
            for msg_file in queue_dir.glob("*.json"):
                if msg_file.stat().st_mtime < cutoff:
                    msg_file.unlink()
                    count += 1

    return count
