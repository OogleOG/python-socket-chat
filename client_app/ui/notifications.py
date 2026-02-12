"""Desktop notification support."""

_PLYER_AVAILABLE = False
try:
    from plyer import notification as _plyer_notification
    _PLYER_AVAILABLE = True
except ImportError:
    _plyer_notification = None


def notify(title: str, message: str, timeout: int = 5):
    """Send a desktop notification. Fails silently if plyer is not available."""
    if not _PLYER_AVAILABLE:
        return
    try:
        _plyer_notification.notify(
            title=title,
            message=message,
            timeout=timeout,
            app_name="Chat",
        )
    except Exception:
        pass
