"""Custom exceptions for Claude Mux iTerm."""


class ClaudeMuxItermError(Exception):
    """Base exception for Claude Mux iTerm."""

    pass


class ITermNotAvailableError(ClaudeMuxItermError):
    """Raised when iTerm2 is not running or not available."""

    pass


class AppleScriptError(ClaudeMuxItermError):
    """Raised when an AppleScript command fails."""

    def __init__(self, message: str, stderr: str = "", returncode: int = 1) -> None:
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode


class SessionNotFoundError(ClaudeMuxItermError):
    """Raised when a specified session doesn't exist."""

    pass


class SessionExistsError(ClaudeMuxItermError):
    """Raised when trying to register a session that already exists."""

    pass


class InvalidTaskIdError(ClaudeMuxItermError):
    """Raised when a task ID is invalid."""

    pass


class MessageDeliveryError(ClaudeMuxItermError):
    """Raised when a message cannot be delivered to a session."""

    pass


class InvalidMessageError(ClaudeMuxItermError):
    """Raised when a message is malformed or invalid."""

    pass
