"""Tests for Claude Mux iTerm AppleScript integration."""

from unittest.mock import MagicMock, patch

import pytest

from claude_mux_iterm.exceptions import AppleScriptError, ITermNotAvailableError
from claude_mux_iterm.iterm import (
    get_all_session_ids,
    get_current_session_id,
    is_iterm_running,
    run_applescript,
    session_exists,
    write_text_to_session,
)


class TestRunApplescript:
    """Tests for run_applescript function."""

    @patch("subprocess.run")
    def test_run_applescript_success(self, mock_run: MagicMock) -> None:
        """Test successful AppleScript execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="test output\n",
            stderr="",
        )

        result = run_applescript("return 'test'")
        assert result == "test output"

    @patch("subprocess.run")
    def test_run_applescript_failure(self, mock_run: MagicMock) -> None:
        """Test AppleScript failure."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="execution error",
        )

        with pytest.raises(AppleScriptError) as exc_info:
            run_applescript("invalid script")

        assert "execution error" in str(exc_info.value)

    @patch("subprocess.run")
    def test_run_applescript_timeout(self, mock_run: MagicMock) -> None:
        """Test AppleScript timeout."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("osascript", 10)

        with pytest.raises(AppleScriptError) as exc_info:
            run_applescript("slow script")

        assert "timed out" in str(exc_info.value)


class TestIsItermRunning:
    """Tests for is_iterm_running function."""

    @patch("claude_mux_iterm.iterm.run_applescript")
    def test_iterm_running(self, mock_applescript: MagicMock) -> None:
        """Test when iTerm2 is running."""
        mock_applescript.return_value = "true"

        assert is_iterm_running() is True

    @patch("claude_mux_iterm.iterm.run_applescript")
    def test_iterm_not_running(self, mock_applescript: MagicMock) -> None:
        """Test when iTerm2 is not running."""
        mock_applescript.return_value = "false"

        assert is_iterm_running() is False

    @patch("claude_mux_iterm.iterm.run_applescript")
    def test_iterm_check_error(self, mock_applescript: MagicMock) -> None:
        """Test when check fails."""
        mock_applescript.side_effect = AppleScriptError("error")

        assert is_iterm_running() is False


class TestGetCurrentSessionId:
    """Tests for get_current_session_id function."""

    @patch("claude_mux_iterm.iterm.is_iterm_running")
    def test_iterm_not_running(self, mock_running: MagicMock) -> None:
        """Test when iTerm2 is not running."""
        mock_running.return_value = False

        with pytest.raises(ITermNotAvailableError):
            get_current_session_id()

    @patch("claude_mux_iterm.iterm.is_iterm_running")
    @patch("claude_mux_iterm.iterm.run_applescript")
    def test_get_current_session(
        self, mock_applescript: MagicMock, mock_running: MagicMock
    ) -> None:
        """Test getting current session ID."""
        mock_running.return_value = True
        mock_applescript.return_value = "session-123-456"

        session_id = get_current_session_id()
        assert session_id == "session-123-456"


class TestGetAllSessionIds:
    """Tests for get_all_session_ids function."""

    @patch("claude_mux_iterm.iterm.is_iterm_running")
    @patch("claude_mux_iterm.iterm.run_applescript")
    def test_get_all_sessions(
        self, mock_applescript: MagicMock, mock_running: MagicMock
    ) -> None:
        """Test getting all session IDs."""
        mock_running.return_value = True
        mock_applescript.return_value = "session-1, session-2, session-3"

        sessions = get_all_session_ids()
        assert sessions == ["session-1", "session-2", "session-3"]

    @patch("claude_mux_iterm.iterm.is_iterm_running")
    @patch("claude_mux_iterm.iterm.run_applescript")
    def test_get_all_sessions_empty(
        self, mock_applescript: MagicMock, mock_running: MagicMock
    ) -> None:
        """Test when no sessions exist."""
        mock_running.return_value = True
        mock_applescript.return_value = ""

        sessions = get_all_session_ids()
        assert sessions == []


class TestWriteText:
    """Tests for write_text_to_session function."""

    @patch("claude_mux_iterm.iterm.run_applescript")
    def test_write_text_success(self, mock_applescript: MagicMock) -> None:
        """Test successful text write."""
        mock_applescript.return_value = "true"

        success = write_text_to_session("session-123", "Hello world")
        assert success is True

    @patch("claude_mux_iterm.iterm.run_applescript")
    def test_write_text_session_not_found(self, mock_applescript: MagicMock) -> None:
        """Test write when session not found."""
        mock_applescript.return_value = "false"

        success = write_text_to_session("nonexistent", "Hello")
        assert success is False


class TestSessionExists:
    """Tests for session_exists function."""

    @patch("claude_mux_iterm.iterm.get_all_session_ids")
    def test_session_exists(self, mock_get_all: MagicMock) -> None:
        """Test when session exists."""
        mock_get_all.return_value = ["session-1", "session-2", "session-3"]

        assert session_exists("session-2") is True

    @patch("claude_mux_iterm.iterm.get_all_session_ids")
    def test_session_not_exists(self, mock_get_all: MagicMock) -> None:
        """Test when session doesn't exist."""
        mock_get_all.return_value = ["session-1", "session-2"]

        assert session_exists("session-3") is False
