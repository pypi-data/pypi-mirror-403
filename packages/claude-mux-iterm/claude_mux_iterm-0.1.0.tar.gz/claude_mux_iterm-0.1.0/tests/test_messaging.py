"""Tests for Claude Mux iTerm messaging."""

from pathlib import Path

import pytest

from claude_mux_iterm.exceptions import InvalidMessageError
from claude_mux_iterm.messaging import (
    acknowledge_message,
    cleanup_expired_messages,
    create_message,
    get_messages,
    load_message,
    save_message,
)
from claude_mux_iterm.models import MessagePriority, MessageType


@pytest.fixture
def temp_message_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary message directory."""
    msg_dir = tmp_path / "messages"
    msg_dir.mkdir()
    monkeypatch.setattr("claude_mux_iterm.messaging.MESSAGE_QUEUE_DIR", msg_dir)
    return msg_dir


class TestMessageCreation:
    """Tests for message creation."""

    def test_create_text_message(self) -> None:
        """Test creating a text message."""
        msg = create_message(
            source_task_id="task-a",
            content="Hello",
            target_task_id="task-b",
        )

        assert msg.message_type == MessageType.TEXT
        assert msg.source_task_id == "task-a"
        assert msg.target_task_id == "task-b"
        assert msg.content == "Hello"

    def test_create_broadcast_message(self) -> None:
        """Test creating a broadcast message."""
        msg = create_message(
            source_task_id="task-a",
            content="Broadcast",
            target_task_id=None,
            message_type=MessageType.BROADCAST,
        )

        assert msg.message_type == MessageType.BROADCAST
        assert msg.target_task_id is None

    def test_create_message_with_priority(self) -> None:
        """Test creating a message with priority."""
        msg = create_message(
            source_task_id="task-a",
            content="Urgent!",
            priority=MessagePriority.URGENT,
        )

        assert msg.metadata.priority == MessagePriority.URGENT


class TestMessagePersistence:
    """Tests for message saving and loading."""

    def test_save_and_load_message(self, temp_message_dir: Path) -> None:
        """Test saving and loading a message."""
        msg = create_message(
            source_task_id="task-a",
            content="Test message",
            target_task_id="task-b",
        )

        # Save to inbox
        file_path = save_message(msg, "task-b", "inbox")
        assert file_path.exists()

        # Load it back
        loaded = load_message(file_path)
        assert loaded.message_id == msg.message_id
        assert loaded.content == msg.content

    def test_save_to_outbox(self, temp_message_dir: Path) -> None:
        """Test saving to outbox."""
        msg = create_message(
            source_task_id="task-a",
            content="Test",
        )

        file_path = save_message(msg, "task-a", "outbox")
        assert "outbox" in str(file_path)
        assert file_path.exists()

    def test_save_invalid_queue_type(self, temp_message_dir: Path) -> None:
        """Test saving with invalid queue type."""
        msg = create_message(source_task_id="task-a", content="Test")

        with pytest.raises(ValueError, match="Invalid queue type"):
            save_message(msg, "task-a", "invalid")

    def test_load_invalid_message(self, temp_message_dir: Path) -> None:
        """Test loading invalid message file."""
        invalid_file = temp_message_dir / "invalid.json"
        invalid_file.write_text("not valid json")

        with pytest.raises(InvalidMessageError):
            load_message(invalid_file)


class TestMessageRetrieval:
    """Tests for message retrieval."""

    def test_get_messages_empty(self, temp_message_dir: Path) -> None:
        """Test getting messages when empty."""
        messages = get_messages("task-a")
        assert messages == []

    def test_get_messages(self, temp_message_dir: Path) -> None:
        """Test getting messages."""
        # Create some messages
        msg1 = create_message(source_task_id="task-b", content="First", target_task_id="task-a")
        msg2 = create_message(source_task_id="task-c", content="Second", target_task_id="task-a")

        save_message(msg1, "task-a", "inbox")
        save_message(msg2, "task-a", "inbox")

        messages = get_messages("task-a")
        assert len(messages) == 2

    def test_get_unread_messages(self, temp_message_dir: Path) -> None:
        """Test getting only unread messages."""
        msg1 = create_message(source_task_id="task-b", content="Unread", target_task_id="task-a")
        msg2 = create_message(source_task_id="task-c", content="Read", target_task_id="task-a")
        msg2.acknowledged = True

        save_message(msg1, "task-a", "inbox")
        save_message(msg2, "task-a", "inbox")

        unread = get_messages("task-a", unread_only=True)
        assert len(unread) == 1
        assert unread[0].content == "Unread"


class TestMessageAcknowledgement:
    """Tests for message acknowledgement."""

    def test_acknowledge_message(self, temp_message_dir: Path) -> None:
        """Test acknowledging a message."""
        msg = create_message(source_task_id="task-b", content="Test", target_task_id="task-a")
        save_message(msg, "task-a", "inbox")

        success = acknowledge_message("task-a", msg.message_id)
        assert success is True

        # Message should be moved to delivered
        inbox_dir = temp_message_dir / "task-a" / "inbox"
        delivered_dir = temp_message_dir / "task-a" / "delivered"

        assert not (inbox_dir / f"{msg.message_id}.json").exists()
        assert (delivered_dir / f"{msg.message_id}.json").exists()

    def test_acknowledge_nonexistent_message(self, temp_message_dir: Path) -> None:
        """Test acknowledging a message that doesn't exist."""
        success = acknowledge_message("task-a", "msg_nonexistent")
        assert success is False


class TestMessageCleanup:
    """Tests for message cleanup."""

    def test_cleanup_expired_messages(self, temp_message_dir: Path) -> None:
        """Test cleaning up expired messages."""
        # Create a message
        msg = create_message(source_task_id="task-a", content="Old message")
        file_path = save_message(msg, "task-a", "inbox")

        # Make it old (modify mtime)
        import os
        import time

        old_time = time.time() - (25 * 3600)  # 25 hours ago
        os.utime(file_path, (old_time, old_time))

        # Cleanup
        count = cleanup_expired_messages(max_age_hours=24)
        assert count == 1
        assert not file_path.exists()
