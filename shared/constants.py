"""Shared constants for the chat application."""

# Network
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5050
ENCODING = "utf-8"
HEADER_SIZE = 4  # 4-byte big-endian length prefix
MAX_MESSAGE_SIZE = 1_048_576  # 1 MB max message payload
RECV_BUFSIZE = 4096
SOCKET_TIMEOUT = 300  # seconds
LISTEN_BACKLOG = 50

# Message types - Authentication
MSG_AUTH_REGISTER = "auth_register"
MSG_AUTH_LOGIN = "auth_login"
MSG_AUTH_RESULT = "auth_result"

# Message types - Channels
MSG_CHANNEL_JOIN = "channel_join"
MSG_CHANNEL_LEAVE = "channel_leave"
MSG_CHANNEL_CREATE = "channel_create"
MSG_CHANNEL_LIST = "channel_list"
MSG_CHANNEL_INFO = "channel_info"
MSG_CHANNEL_JOINED = "channel_joined"
MSG_CHANNEL_CREATED = "channel_created"

# Message types - Chat
MSG_MESSAGE = "message"
MSG_PRIVATE_MESSAGE = "private_message"
MSG_ACTION = "action"

# Message types - Presence
MSG_USER_LIST = "user_list"
MSG_USER_JOINED = "user_joined"
MSG_USER_LEFT = "user_left"
MSG_STATUS_CHANGE = "status_change"

# Message types - System
MSG_ERROR = "error"
MSG_SYSTEM = "system"

# Validation limits
USERNAME_MIN_LEN = 3
USERNAME_MAX_LEN = 20
PASSWORD_MIN_LEN = 6
MESSAGE_MAX_LEN = 2000
CHANNEL_NAME_MIN_LEN = 2
CHANNEL_NAME_MAX_LEN = 30
MESSAGE_HISTORY_LIMIT = 50

# Rate limiting
RATE_LIMIT_MESSAGES = 5
RATE_LIMIT_WINDOW = 1.0  # seconds

# Session
SESSION_EXPIRY_HOURS = 24

# Default channel
DEFAULT_CHANNEL = "general"
