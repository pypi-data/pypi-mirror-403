"""Session registration and management for Claude Mux iTerm."""

import json
from pathlib import Path

from .exceptions import InvalidTaskIdError, SessionExistsError, SessionNotFoundError
from .iterm import get_all_session_ids, get_current_session_id, session_exists
from .models import Session

# Storage location for session registrations
SESSIONS_DIR = Path.home() / ".claude-mux-iterm" / "sessions"


def ensure_sessions_dir() -> Path:
    """Ensure the sessions directory exists.

    Returns:
        Path to the sessions directory.
    """
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return SESSIONS_DIR


def validate_task_id(task_id: str) -> None:
    """Validate a task ID.

    Args:
        task_id: The task ID to validate.

    Raises:
        InvalidTaskIdError: If the task ID is invalid.
    """
    if not task_id:
        raise InvalidTaskIdError("Task ID cannot be empty")
    if not task_id.replace("-", "").replace("_", "").isalnum():
        raise InvalidTaskIdError(
            f"Task ID must be alphanumeric with hyphens/underscores: {task_id}"
        )
    if len(task_id) > 64:
        raise InvalidTaskIdError(f"Task ID too long (max 64 chars): {task_id}")


def get_session_file(task_id: str) -> Path:
    """Get the file path for a session registration.

    Args:
        task_id: The task ID.

    Returns:
        Path to the session file.
    """
    return ensure_sessions_dir() / f"{task_id}.json"


def register_session(task_id: str, iterm_session_id: str | None = None) -> Session:
    """Register the current iTerm2 session with a task ID.

    Args:
        task_id: Unique identifier for this session/task.
        iterm_session_id: Optional specific session ID. If not provided,
            uses the current session.

    Returns:
        The registered Session.

    Raises:
        InvalidTaskIdError: If the task ID is invalid.
        SessionExistsError: If a session with this task ID already exists.
    """
    validate_task_id(task_id)

    # Get the current session ID if not provided
    session_id = iterm_session_id or get_current_session_id()

    # Check if task ID already registered
    session_file = get_session_file(task_id)
    if session_file.exists():
        existing = load_session(task_id)
        if existing and session_exists(existing.iterm_session_id):
            raise SessionExistsError(f"Task ID '{task_id}' already registered to an active session")

    # Create session record
    session = Session(
        task_id=task_id,
        iterm_session_id=session_id,
    )

    # Save to file
    session_file.write_text(session.model_dump_json(indent=2))

    return session


def load_session(task_id: str) -> Session | None:
    """Load a session by task ID.

    Args:
        task_id: The task ID to load.

    Returns:
        The Session if found, None otherwise.
    """
    session_file = get_session_file(task_id)
    if not session_file.exists():
        return None

    try:
        data = json.loads(session_file.read_text())
        return Session.model_validate(data)
    except Exception:
        return None


def get_session_by_task_id(task_id: str) -> Session:
    """Get a session by task ID.

    Args:
        task_id: The task ID.

    Returns:
        The Session.

    Raises:
        SessionNotFoundError: If no session found for this task ID.
    """
    session = load_session(task_id)
    if session is None:
        raise SessionNotFoundError(f"No session found for task ID: {task_id}")

    # Verify the session is still active
    if not session_exists(session.iterm_session_id):
        # Clean up stale registration
        unregister_session(task_id)
        raise SessionNotFoundError(f"Session for task '{task_id}' is no longer active")

    return session


def unregister_session(task_id: str) -> bool:
    """Unregister a session.

    Args:
        task_id: The task ID to unregister.

    Returns:
        True if the session was unregistered, False if not found.
    """
    session_file = get_session_file(task_id)
    if session_file.exists():
        session_file.unlink()
        return True
    return False


def list_active_sessions() -> list[Session]:
    """List all active registered sessions.

    Returns:
        List of active Sessions.
    """
    ensure_sessions_dir()
    active_sessions: list[Session] = []
    current_iterm_sessions = set(get_all_session_ids())

    for session_file in SESSIONS_DIR.glob("*.json"):
        try:
            session = load_session(session_file.stem)
            if session and session.iterm_session_id in current_iterm_sessions:
                active_sessions.append(session)
            elif session:
                # Clean up stale registration
                session_file.unlink()
        except Exception:
            continue

    return active_sessions


def get_session_id_for_task(task_id: str) -> str:
    """Get the iTerm2 session ID for a task.

    Args:
        task_id: The task ID.

    Returns:
        The iTerm2 session ID.

    Raises:
        SessionNotFoundError: If no active session for this task.
    """
    session = get_session_by_task_id(task_id)
    return session.iterm_session_id


def cleanup_stale_sessions() -> int:
    """Clean up registrations for sessions that no longer exist.

    Returns:
        Count of cleaned up sessions.
    """
    ensure_sessions_dir()
    count = 0
    current_iterm_sessions = set(get_all_session_ids())

    for session_file in SESSIONS_DIR.glob("*.json"):
        try:
            session = load_session(session_file.stem)
            if session and session.iterm_session_id not in current_iterm_sessions:
                session_file.unlink()
                count += 1
        except Exception:
            continue

    return count
