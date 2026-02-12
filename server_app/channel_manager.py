"""In-memory channel membership tracking."""

import threading


class ChannelManager:
    """Tracks which users are currently in which channels (online only)."""

    def __init__(self):
        self._channels: dict[str, set[str]] = {}  # channel_name -> set of usernames
        self._lock = threading.Lock()

    def join(self, username: str, channel: str):
        with self._lock:
            if channel not in self._channels:
                self._channels[channel] = set()
            self._channels[channel].add(username)

    def leave(self, username: str, channel: str):
        with self._lock:
            if channel in self._channels:
                self._channels[channel].discard(username)
                if not self._channels[channel]:
                    del self._channels[channel]

    def get_users(self, channel: str) -> list[str]:
        with self._lock:
            return sorted(self._channels.get(channel, set()))

    def get_user_channel(self, username: str) -> str | None:
        """Get the channel a user is currently in (first match)."""
        with self._lock:
            for channel, users in self._channels.items():
                if username in users:
                    return channel
        return None

    def remove_user(self, username: str):
        """Remove a user from all channels."""
        with self._lock:
            for channel in list(self._channels.keys()):
                self._channels[channel].discard(username)
                if not self._channels[channel]:
                    del self._channels[channel]
