"""Tests for Claude Mux iTerm models."""

from datetime import datetime, timezone

from claude_mux_iterm.models import (
    AcknowledgeMessageResult,
    ListMessagesResult,
    ListSessionsResult,
    Message,
    MessageInfo,
    MessageMetadata,
    MessagePriority,
    MessageType,
    RegisterSessionResult,
    SendMessageResult,
    Session,
)


class TestMessage:
    """Tests for Message model."""

    def test_message_creation(self) -> None:
        """Test creating a basic message."""
        msg = Message(
            message_type=MessageType.TEXT,
            source_task_id="task-a",
            target_task_id="task-b",
            content="Hello from task-a",
        )

        assert msg.message_type == MessageType.TEXT
        assert msg.source_task_id == "task-a"
        assert msg.target_task_id == "task-b"
        assert msg.content == "Hello from task-a"
        assert msg.message_id.startswith("msg_")
        assert msg.protocol_version == "1.0"
        assert msg.acknowledged is False

    def test_message_default_metadata(self) -> None:
        """Test message has default metadata."""
        msg = Message(
            message_type=MessageType.TEXT,
            source_task_id="task-a",
            content="Test",
        )

        assert msg.metadata.priority == MessagePriority.NORMAL
        assert msg.metadata.ttl_seconds == 3600

    def test_message_custom_metadata(self) -> None:
        """Test message with custom metadata."""
        metadata = MessageMetadata(
            priority=MessagePriority.URGENT,
            ttl_seconds=7200,
        )
        msg = Message(
            message_type=MessageType.TEXT,
            source_task_id="task-a",
            content="Urgent message",
            metadata=metadata,
        )

        assert msg.metadata.priority == MessagePriority.URGENT
        assert msg.metadata.ttl_seconds == 7200

    def test_message_to_wire_format(self) -> None:
        """Test message serialization to wire format."""
        msg = Message(
            message_type=MessageType.TEXT,
            source_task_id="task-a",
            target_task_id="task-b",
            content="Test message",
        )

        wire = msg.to_wire_format()
        assert wire == "Message from task-a: Test message"

    def test_message_to_wire_format_with_priority(self) -> None:
        """Test wire format includes priority prefix."""
        msg = Message(
            message_type=MessageType.TEXT,
            source_task_id="task-a",
            content="Urgent!",
            metadata=MessageMetadata(priority=MessagePriority.URGENT),
        )

        wire = msg.to_wire_format()
        assert wire == "[URGENT] Message from task-a: Urgent!"

    def test_broadcast_message(self) -> None:
        """Test broadcast message without target."""
        msg = Message(
            message_type=MessageType.BROADCAST,
            source_task_id="task-a",
            target_task_id=None,
            content="Broadcast to all",
        )

        assert msg.target_task_id is None
        assert msg.message_type == MessageType.BROADCAST


class TestSession:
    """Tests for Session model."""

    def test_session_creation(self) -> None:
        """Test creating a session."""
        session = Session(
            task_id="task-a",
            iterm_session_id="session-123-456",
        )

        assert session.task_id == "task-a"
        assert session.iterm_session_id == "session-123-456"
        assert isinstance(session.registered_at, datetime)
        assert isinstance(session.last_seen, datetime)


class TestResultModels:
    """Tests for result models."""

    def test_register_session_result(self) -> None:
        """Test RegisterSessionResult."""
        result = RegisterSessionResult(
            success=True,
            task_id="task-a",
            session_id="session-123",
            message="Session registered",
        )

        assert result.success is True
        assert result.task_id == "task-a"
        assert result.session_id == "session-123"

    def test_list_sessions_result(self) -> None:
        """Test ListSessionsResult."""
        sessions = [
            Session(task_id="task-a", iterm_session_id="s1"),
            Session(task_id="task-b", iterm_session_id="s2"),
        ]
        result = ListSessionsResult(
            sessions=sessions,
            total_count=2,
            message="Found 2 sessions",
        )

        assert result.total_count == 2
        assert len(result.sessions) == 2

    def test_send_message_result(self) -> None:
        """Test SendMessageResult."""
        result = SendMessageResult(
            success=True,
            message_id="msg_123",
            target_task_id="task-b",
            delivered_to=["task-b"],
            message="Message sent",
        )

        assert result.success is True
        assert result.delivered_to == ["task-b"]

    def test_list_messages_result(self) -> None:
        """Test ListMessagesResult."""
        messages = [
            MessageInfo(
                message_id="msg_1",
                message_type=MessageType.TEXT,
                source_task_id="task-a",
                content="Hello",
                received_at=datetime.now(timezone.utc),
                priority=MessagePriority.NORMAL,
                acknowledged=False,
            ),
        ]
        result = ListMessagesResult(
            messages=messages,
            unread_count=1,
            message="Found 1 message",
        )

        assert result.unread_count == 1
        assert len(result.messages) == 1

    def test_acknowledge_message_result(self) -> None:
        """Test AcknowledgeMessageResult."""
        result = AcknowledgeMessageResult(
            success=True,
            message_id="msg_123",
            message="Message acknowledged",
        )

        assert result.success is True
        assert result.message_id == "msg_123"
