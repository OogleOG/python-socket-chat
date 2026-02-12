"""Main chat server using length-prefixed JSON protocol."""

import socket
import threading
from datetime import datetime, timezone

from shared.protocol import MessageReader, send_message
from shared.constants import (
    ENCODING, SOCKET_TIMEOUT, LISTEN_BACKLOG,
    MSG_AUTH_REGISTER, MSG_AUTH_LOGIN, MSG_AUTH_RESULT,
    MSG_CHANNEL_JOIN, MSG_CHANNEL_LEAVE, MSG_CHANNEL_CREATE,
    MSG_CHANNEL_LIST, MSG_CHANNEL_INFO, MSG_CHANNEL_JOINED,
    MSG_CHANNEL_CREATED,
    MSG_MESSAGE, MSG_PRIVATE_MESSAGE, MSG_ACTION,
    MSG_USER_LIST, MSG_USER_JOINED, MSG_USER_LEFT, MSG_STATUS_CHANGE,
    MSG_ERROR, MSG_SYSTEM,
    DEFAULT_CHANNEL, MESSAGE_HISTORY_LIMIT,
    RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW,
)
from shared.validators import validate_message, validate_channel_name, sanitize_content
from server_app.database import Database
from server_app.auth import hash_password, verify_password, generate_session_token
from server_app.rate_limiter import RateLimiter
from server_app.channel_manager import ChannelManager


class ClientConnection:
    """Represents a connected client's state."""

    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr
        self.username = None
        self.user_id = None
        self.session_token = None
        self.authenticated = False
        self.current_channel = None
        self.rate_limiter = RateLimiter(RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW)


class ChatServer:
    def __init__(self, host="127.0.0.1", port=5050, db_path="chat_data.db", use_tls=False, certfile=None, keyfile=None):
        self.host = host
        self.port = port
        self.use_tls = use_tls
        self.certfile = certfile
        self.keyfile = keyfile
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}  # sock -> ClientConnection
        self.lock = threading.Lock()
        self.running = False

        self.db = Database(db_path)
        self.channel_mgr = ChannelManager()

        self.ssl_context = None
        if self.use_tls:
            import ssl
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            self.ssl_context.load_cert_chain(certfile, keyfile)

    def start(self):
        self.server_sock.bind((self.host, self.port))
        self.server_sock.listen(LISTEN_BACKLOG)
        self.running = True
        tls_status = " (TLS)" if self.use_tls else ""
        print(f"[SERVER] Listening on {self.host}:{self.port}{tls_status}")
        try:
            while self.running:
                try:
                    client_sock, addr = self.server_sock.accept()
                    client_sock.settimeout(SOCKET_TIMEOUT)

                    if self.ssl_context:
                        try:
                            client_sock = self.ssl_context.wrap_socket(client_sock, server_side=True)
                        except Exception as e:
                            print(f"[SERVER] TLS handshake failed for {addr}: {e}")
                            client_sock.close()
                            continue

                    conn = ClientConnection(client_sock, addr)
                    with self.lock:
                        self.clients[client_sock] = conn
                    threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()
                except OSError:
                    break
        finally:
            self.shutdown()

    def shutdown(self):
        self.running = False
        with self.lock:
            for sock in list(self.clients.keys()):
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    sock.close()
                except Exception:
                    pass
            self.clients.clear()
        try:
            self.server_sock.close()
        except Exception:
            pass
        print("[SERVER] Shutdown complete.")

    def _send(self, conn: ClientConnection, msg: dict):
        try:
            send_message(conn.sock, msg)
        except Exception:
            self._drop_client(conn)

    def _broadcast_to_channel(self, channel: str, msg: dict, exclude=None):
        """Send a message to all authenticated users in a channel."""
        dead = []
        with self.lock:
            targets = [
                c for c in self.clients.values()
                if c.authenticated and c.current_channel == channel and c is not exclude
            ]
        for c in targets:
            try:
                send_message(c.sock, msg)
            except Exception:
                dead.append(c)
        for c in dead:
            self._drop_client(c)

    def _broadcast_global(self, msg: dict, exclude=None):
        """Send a message to all authenticated users."""
        dead = []
        with self.lock:
            targets = [c for c in self.clients.values() if c.authenticated and c is not exclude]
        for c in targets:
            try:
                send_message(c.sock, msg)
            except Exception:
                dead.append(c)
        for c in dead:
            self._drop_client(c)

    def _drop_client(self, conn: ClientConnection):
        with self.lock:
            self.clients.pop(conn.sock, None)
        try:
            conn.sock.close()
        except Exception:
            pass
        if conn.authenticated and conn.username:
            if conn.current_channel:
                self.channel_mgr.leave(conn.username, conn.current_channel)
                self._broadcast_to_channel(conn.current_channel, {
                    "type": MSG_USER_LEFT,
                    "channel": conn.current_channel,
                    "username": conn.username,
                })
            self._broadcast_global({
                "type": MSG_STATUS_CHANGE,
                "username": conn.username,
                "status": "offline",
            })
            print(f"[SERVER] {conn.username} disconnected.")

    def _send_error(self, conn: ClientConnection, code: str, message: str):
        self._send(conn, {"type": MSG_ERROR, "code": code, "message": message})

    def _handle_client(self, conn: ClientConnection):
        print(f"[SERVER] New connection from {conn.addr}")
        try:
            reader = MessageReader(conn.sock)
            for msg in reader:
                if not isinstance(msg, dict) or "type" not in msg:
                    self._send_error(conn, "invalid", "Invalid message format.")
                    continue

                msg_type = msg["type"]

                # Authentication phase
                if not conn.authenticated:
                    if msg_type == MSG_AUTH_REGISTER:
                        self._handle_register(conn, msg)
                    elif msg_type == MSG_AUTH_LOGIN:
                        self._handle_login(conn, msg)
                    else:
                        self._send_error(conn, "not_authenticated", "You must log in first.")
                    continue

                # Authenticated phase - rate limit check
                if msg_type in (MSG_MESSAGE, MSG_PRIVATE_MESSAGE, MSG_ACTION):
                    if not conn.rate_limiter.is_allowed():
                        self._send_error(conn, "rate_limited", "Slow down! Too many messages.")
                        continue

                # Dispatch by message type
                if msg_type == MSG_MESSAGE:
                    self._handle_message(conn, msg)
                elif msg_type == MSG_PRIVATE_MESSAGE:
                    self._handle_private_message(conn, msg)
                elif msg_type == MSG_ACTION:
                    self._handle_action(conn, msg)
                elif msg_type == MSG_CHANNEL_JOIN:
                    self._handle_channel_join(conn, msg)
                elif msg_type == MSG_CHANNEL_LEAVE:
                    self._handle_channel_leave(conn, msg)
                elif msg_type == MSG_CHANNEL_CREATE:
                    self._handle_channel_create(conn, msg)
                elif msg_type == MSG_CHANNEL_LIST:
                    self._handle_channel_list(conn)
                elif msg_type == MSG_USER_LIST:
                    self._handle_user_list(conn, msg)
                else:
                    self._send_error(conn, "unknown", f"Unknown message type: {msg_type}")

        except Exception as e:
            print(f"[SERVER] Error with client {conn.addr}: {e}")
        finally:
            self._drop_client(conn)

    # --- Auth handlers ---

    def _handle_register(self, conn, msg):
        username = msg.get("username", "").strip()
        password = msg.get("password", "")

        from shared.validators import validate_username, validate_password
        ok, err = validate_username(username)
        if not ok:
            self._send(conn, {"type": MSG_AUTH_RESULT, "success": False, "error": err})
            return
        ok, err = validate_password(password)
        if not ok:
            self._send(conn, {"type": MSG_AUTH_RESULT, "success": False, "error": err})
            return

        pw_hash = hash_password(password)
        success = self.db.create_user(username, pw_hash)
        if not success:
            self._send(conn, {"type": MSG_AUTH_RESULT, "success": False, "error": "Username already taken."})
            return

        user = self.db.get_user_by_username(username)
        token = generate_session_token()
        self.db.create_session(token, user["id"])

        conn.authenticated = True
        conn.username = user["username"]
        conn.user_id = user["id"]
        conn.session_token = token

        self._send(conn, {"type": MSG_AUTH_RESULT, "success": True, "token": token, "username": user["username"]})
        self._finalize_login(conn)

    def _handle_login(self, conn, msg):
        username = msg.get("username", "").strip()
        password = msg.get("password", "")

        user = self.db.get_user_by_username(username)
        if not user or not verify_password(password, user["password_hash"]):
            self._send(conn, {"type": MSG_AUTH_RESULT, "success": False, "error": "Invalid username or password."})
            return

        token = generate_session_token()
        self.db.create_session(token, user["id"])

        conn.authenticated = True
        conn.username = user["username"]
        conn.user_id = user["id"]
        conn.session_token = token

        self._send(conn, {"type": MSG_AUTH_RESULT, "success": True, "token": token, "username": user["username"]})
        self._finalize_login(conn)

    def _finalize_login(self, conn):
        """After successful auth, auto-join general and send channel list."""
        print(f"[SERVER] {conn.username} logged in.")
        # Send channel list
        self._handle_channel_list(conn)
        # Auto-join default channel
        self._handle_channel_join(conn, {"channel": DEFAULT_CHANNEL})
        # Notify others
        self._broadcast_global({
            "type": MSG_STATUS_CHANGE,
            "username": conn.username,
            "status": "online",
        }, exclude=conn)

    # --- Channel handlers ---

    def _handle_channel_join(self, conn, msg):
        channel_name = msg.get("channel", "").strip().lower()
        if not channel_name:
            self._send_error(conn, "invalid", "Channel name required.")
            return

        channel = self.db.get_channel_by_name(channel_name)
        if not channel:
            self._send_error(conn, "not_found", f"Channel '{channel_name}' not found.")
            return

        # Leave current channel first
        if conn.current_channel and conn.current_channel != channel_name:
            self._handle_channel_leave(conn, {"channel": conn.current_channel}, silent=True)

        conn.current_channel = channel_name
        self.channel_mgr.join(conn.username, channel_name)

        # Get message history
        history = self.db.get_message_history(channel["id"], limit=MESSAGE_HISTORY_LIMIT)
        history_msgs = [
            {
                "sender": h["username"],
                "content": h["content"],
                "timestamp": h["created_at"],
                "msg_type": h["msg_type"],
                "id": h["id"],
            }
            for h in history
        ]

        # Get online users in channel
        users = self.channel_mgr.get_users(channel_name)

        self._send(conn, {
            "type": MSG_CHANNEL_JOINED,
            "channel": channel_name,
            "history": history_msgs,
            "users": [{"username": u, "status": "online"} for u in users],
        })

        # Notify others in channel
        self._broadcast_to_channel(channel_name, {
            "type": MSG_USER_JOINED,
            "channel": channel_name,
            "username": conn.username,
        }, exclude=conn)

    def _handle_channel_leave(self, conn, msg, silent=False):
        channel_name = msg.get("channel", "").strip().lower()
        if not channel_name:
            return

        self.channel_mgr.leave(conn.username, channel_name)
        if conn.current_channel == channel_name:
            conn.current_channel = None

        if not silent:
            self._broadcast_to_channel(channel_name, {
                "type": MSG_USER_LEFT,
                "channel": channel_name,
                "username": conn.username,
            })

    def _handle_channel_create(self, conn, msg):
        name = msg.get("name", "").strip().lower()
        description = msg.get("description", "").strip()

        ok, err = validate_channel_name(name)
        if not ok:
            self._send_error(conn, "invalid", err)
            return

        channel_id = self.db.create_channel(name, description, conn.user_id)
        if not channel_id:
            self._send_error(conn, "exists", f"Channel '{name}' already exists.")
            return

        channel = {"id": channel_id, "name": name, "description": description}
        # Notify all users
        self._broadcast_global({
            "type": MSG_CHANNEL_CREATED,
            "channel": channel,
        })

    def _handle_channel_list(self, conn):
        channels = self.db.list_channels()
        self._send(conn, {
            "type": MSG_CHANNEL_INFO,
            "channels": [{"id": c["id"], "name": c["name"], "description": c["description"]} for c in channels],
        })

    # --- Chat handlers ---

    def _handle_message(self, conn, msg):
        content = msg.get("content", "")
        channel = msg.get("channel", conn.current_channel)

        ok, err = validate_message(content)
        if not ok:
            self._send_error(conn, "invalid", err)
            return

        content = sanitize_content(content)

        if not channel:
            self._send_error(conn, "no_channel", "You must join a channel first.")
            return

        ch = self.db.get_channel_by_name(channel)
        if not ch:
            self._send_error(conn, "not_found", f"Channel '{channel}' not found.")
            return

        timestamp = datetime.now(timezone.utc).isoformat()
        msg_id = self.db.save_message(ch["id"], conn.user_id, content, "message")

        self._broadcast_to_channel(channel, {
            "type": MSG_MESSAGE,
            "channel": channel,
            "sender": conn.username,
            "content": content,
            "timestamp": timestamp,
            "id": msg_id,
        })

    def _handle_private_message(self, conn, msg):
        to_user = msg.get("to", "").strip()
        content = msg.get("content", "")

        ok, err = validate_message(content)
        if not ok:
            self._send_error(conn, "invalid", err)
            return

        content = sanitize_content(content)

        # Find target user
        target_conn = None
        with self.lock:
            for c in self.clients.values():
                if c.authenticated and c.username and c.username.lower() == to_user.lower():
                    target_conn = c
                    break

        if not target_conn:
            self._send_error(conn, "not_found", f"User '{to_user}' not found or offline.")
            return

        timestamp = datetime.now(timezone.utc).isoformat()

        # Send to target
        self._send(target_conn, {
            "type": MSG_PRIVATE_MESSAGE,
            "from": conn.username,
            "content": content,
            "timestamp": timestamp,
        })
        # Echo back to sender
        self._send(conn, {
            "type": MSG_PRIVATE_MESSAGE,
            "from": conn.username,
            "to": to_user,
            "content": content,
            "timestamp": timestamp,
        })

    def _handle_action(self, conn, msg):
        content = msg.get("content", "")
        channel = msg.get("channel", conn.current_channel)

        ok, err = validate_message(content)
        if not ok:
            self._send_error(conn, "invalid", err)
            return

        content = sanitize_content(content)

        if not channel:
            self._send_error(conn, "no_channel", "You must join a channel first.")
            return

        ch = self.db.get_channel_by_name(channel)
        if not ch:
            return

        timestamp = datetime.now(timezone.utc).isoformat()
        self.db.save_message(ch["id"], conn.user_id, content, "action")

        self._broadcast_to_channel(channel, {
            "type": MSG_ACTION,
            "channel": channel,
            "sender": conn.username,
            "content": content,
            "timestamp": timestamp,
        })

    def _handle_user_list(self, conn, msg):
        channel = msg.get("channel", conn.current_channel)
        if not channel:
            return
        users = self.channel_mgr.get_users(channel)
        self._send(conn, {
            "type": MSG_USER_LIST,
            "channel": channel,
            "users": [{"username": u, "status": "online"} for u in users],
        })
