"""iTerm2 AppleScript integration for Claude Mux iTerm."""

import subprocess

from .exceptions import AppleScriptError, ITermNotAvailableError


def run_applescript(script: str) -> str:
    """Run an AppleScript and return the output.

    Args:
        script: The AppleScript code to execute.

    Returns:
        The script's output as a string.

    Raises:
        AppleScriptError: If the script fails to execute.
    """
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            raise AppleScriptError(
                f"AppleScript failed: {result.stderr}",
                stderr=result.stderr,
                returncode=result.returncode,
            )
        return result.stdout.strip()
    except subprocess.TimeoutExpired as e:
        raise AppleScriptError(f"AppleScript timed out: {e}") from e
    except FileNotFoundError as e:
        raise AppleScriptError(f"osascript not found: {e}") from e


def is_iterm_running() -> bool:
    """Check if iTerm2 is running.

    Returns:
        True if iTerm2 is running, False otherwise.
    """
    script = '''
    tell application "System Events"
        return (name of processes) contains "iTerm2"
    end tell
    '''
    try:
        result = run_applescript(script)
        return result.lower() == "true"
    except AppleScriptError:
        return False


def get_current_session_id() -> str:
    """Get the unique ID of the current iTerm2 session.

    Returns:
        The unique ID of the current session.

    Raises:
        ITermNotAvailableError: If iTerm2 is not running.
        AppleScriptError: If the script fails.
    """
    if not is_iterm_running():
        raise ITermNotAvailableError("iTerm2 is not running")

    script = '''
    tell application "iTerm2"
        tell current session of current tab of current window
            return unique id
        end tell
    end tell
    '''
    return run_applescript(script)


def get_all_session_ids() -> list[str]:
    """Get the unique IDs of all iTerm2 sessions.

    Returns:
        List of unique session IDs.

    Raises:
        ITermNotAvailableError: If iTerm2 is not running.
        AppleScriptError: If the script fails.
    """
    if not is_iterm_running():
        raise ITermNotAvailableError("iTerm2 is not running")

    script = '''
    tell application "iTerm2"
        set sessionIds to {}
        repeat with w in windows
            repeat with t in tabs of w
                repeat with s in sessions of t
                    set end of sessionIds to unique id of s
                end repeat
            end repeat
        end repeat
        set AppleScript's text item delimiters to ","
        return sessionIds as text
    end tell
    '''
    result = run_applescript(script)
    if not result:
        return []
    return [s.strip() for s in result.split(",") if s.strip()]


def get_session_name(session_id: str) -> str | None:
    """Get the name/title of an iTerm2 session.

    Args:
        session_id: The unique ID of the iTerm2 session.

    Returns:
        The session name, or None if not found.

    Raises:
        AppleScriptError: If the script fails.
    """
    script = f'''
    tell application "iTerm2"
        repeat with w in windows
            repeat with t in tabs of w
                repeat with s in sessions of t
                    if unique id of s is "{session_id}" then
                        return name of s
                    end if
                end repeat
            end repeat
        end repeat
        return ""
    end tell
    '''
    try:
        result = run_applescript(script)
        return result if result else None
    except AppleScriptError:
        return None


def write_text_to_session(session_id: str, text: str, submit: bool = True) -> bool:
    """Write text to an iTerm2 session and optionally submit it.

    Args:
        session_id: The unique ID of the iTerm2 session.
        text: The text to write.
        submit: Whether to press Enter after the text to submit it.

    Returns:
        True if successful.

    Raises:
        AppleScriptError: If the script fails.
    """
    # Escape special characters for AppleScript
    escaped_text = text.replace("\\", "\\\\").replace('"', '\\"')

    # Write text without newline, activate the session, then send Return
    script = f'''
    tell application "iTerm2"
        repeat with w in windows
            repeat with t in tabs of w
                repeat with s in sessions of t
                    if unique id of s is "{session_id}" then
                        -- Write the text without newline
                        tell s to write text "{escaped_text}" newline NO

                        -- If submit requested, select this session and press Return
                        if {str(submit).lower()} then
                            -- Select this tab and session
                            select t
                            select s
                            -- Brief delay then send Return via System Events
                            delay 0.15
                            tell application "System Events"
                                key code 36
                            end tell
                        end if

                        return "true"
                    end if
                end repeat
            end repeat
        end repeat
        return "false"
    end tell
    '''
    result = run_applescript(script)
    return result.lower() == "true"


def session_exists(session_id: str) -> bool:
    """Check if a session with the given ID exists.

    Args:
        session_id: The unique ID of the iTerm2 session.

    Returns:
        True if the session exists.
    """
    try:
        all_sessions = get_all_session_ids()
        return session_id in all_sessions
    except (ITermNotAvailableError, AppleScriptError):
        return False
