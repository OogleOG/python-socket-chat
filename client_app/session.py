"""Client-side session state."""


class Session:
    """Holds the current client session state after authentication."""

    def __init__(self):
        self.username = None
        self.token = None
        self.current_channel = None
        self.channels = []  # list of channel dicts
        self.authenticated = False

    def set_authenticated(self, username: str, token: str):
        self.username = username
        self.token = token
        self.authenticated = True

    def clear(self):
        self.username = None
        self.token = None
        self.current_channel = None
        self.channels = []
        self.authenticated = False
