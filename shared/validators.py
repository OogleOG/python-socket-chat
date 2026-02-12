"""Input validation and sanitization for the chat application."""

import re
from .constants import (
    USERNAME_MIN_LEN, USERNAME_MAX_LEN,
    PASSWORD_MIN_LEN,
    MESSAGE_MAX_LEN,
    CHANNEL_NAME_MIN_LEN, CHANNEL_NAME_MAX_LEN,
)

_USERNAME_RE = re.compile(r'^[a-zA-Z0-9_]+$')
_CHANNEL_RE = re.compile(r'^[a-z0-9\-]+$')


def validate_username(username: str) -> tuple[bool, str]:
    """Validate a username. Returns (ok, error_message)."""
    if not username or not username.strip():
        return False, "Username cannot be empty."
    username = username.strip()
    if len(username) < USERNAME_MIN_LEN:
        return False, f"Username must be at least {USERNAME_MIN_LEN} characters."
    if len(username) > USERNAME_MAX_LEN:
        return False, f"Username must be at most {USERNAME_MAX_LEN} characters."
    if not _USERNAME_RE.match(username):
        return False, "Username can only contain letters, numbers, and underscores."
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """Validate a password. Returns (ok, error_message)."""
    if not password:
        return False, "Password cannot be empty."
    if len(password) < PASSWORD_MIN_LEN:
        return False, f"Password must be at least {PASSWORD_MIN_LEN} characters."
    return True, ""


def validate_message(content: str) -> tuple[bool, str]:
    """Validate a chat message. Returns (ok, error_message)."""
    if not content or not content.strip():
        return False, "Message cannot be empty."
    if len(content) > MESSAGE_MAX_LEN:
        return False, f"Message must be at most {MESSAGE_MAX_LEN} characters."
    return True, ""


def validate_channel_name(name: str) -> tuple[bool, str]:
    """Validate a channel name. Returns (ok, error_message)."""
    if not name or not name.strip():
        return False, "Channel name cannot be empty."
    name = name.strip().lower()
    if len(name) < CHANNEL_NAME_MIN_LEN:
        return False, f"Channel name must be at least {CHANNEL_NAME_MIN_LEN} characters."
    if len(name) > CHANNEL_NAME_MAX_LEN:
        return False, f"Channel name must be at most {CHANNEL_NAME_MAX_LEN} characters."
    if not _CHANNEL_RE.match(name):
        return False, "Channel name can only contain lowercase letters, numbers, and hyphens."
    return True, ""


def sanitize_content(text: str) -> str:
    """Strip control characters except newlines and tabs."""
    return "".join(ch for ch in text if ch in ('\n', '\t') or (ord(ch) >= 32))
