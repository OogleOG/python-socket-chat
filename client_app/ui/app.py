"""Main CustomTkinter application - orchestrates screens and network."""

import threading
import customtkinter as ctk

from client_app.network import NetworkClient
from client_app.session import Session
from client_app.ui.theme import (
    BG_DARKEST, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT, FONT_FAMILY,
)
from client_app.ui.login_screen import LoginScreen
from client_app.ui.chat_screen import ChatScreen
from client_app.ui.notifications import notify
from shared.constants import (
    MSG_AUTH_LOGIN, MSG_AUTH_REGISTER, MSG_AUTH_RESULT,
    MSG_CHANNEL_JOIN, MSG_CHANNEL_CREATE, MSG_CHANNEL_LIST,
    MSG_CHANNEL_INFO, MSG_CHANNEL_JOINED, MSG_CHANNEL_CREATED,
    MSG_MESSAGE, MSG_PRIVATE_MESSAGE, MSG_ACTION,
    MSG_USER_LIST, MSG_USER_JOINED, MSG_USER_LEFT, MSG_STATUS_CHANGE,
    MSG_ERROR, MSG_SYSTEM,
)


class ChatApp:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.root = ctk.CTk()
        self.root.title("Chat")
        self.root.geometry(f"{MIN_WINDOW_WIDTH}x{MIN_WINDOW_HEIGHT}")
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.root.configure(fg_color=BG_DARKEST)

        self.network = NetworkClient()
        self.session = Session()

        self._login_screen = None
        self._chat_screen = None
        self._pending_auth_action = None  # "login" or "register"

        self._channel_descriptions = {}  # channel_name -> description

        self._show_login_screen()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def run(self):
        self.root.mainloop()

    # --- Screen management ---

    def _show_login_screen(self):
        if self._chat_screen:
            self._chat_screen.pack_forget()
            self._chat_screen.destroy()
            self._chat_screen = None

        self._login_screen = LoginScreen(
            self.root,
            on_login_callback=self._do_login,
            on_register_callback=self._do_register,
        )
        self._login_screen.pack(fill="both", expand=True)

    def _show_chat_screen(self):
        if self._login_screen:
            self._login_screen.pack_forget()
            self._login_screen.destroy()
            self._login_screen = None

        self._chat_screen = ChatScreen(
            self.root,
            on_send_message=self._on_send_message,
            on_channel_select=self._on_channel_select,
            on_channel_create=self._on_channel_create,
        )
        self._chat_screen.pack(fill="both", expand=True)
        self.root.title(f"Chat - {self.session.username}")

    # --- Auth actions ---

    def _do_login(self, username, password, host, port, use_tls):
        self._pending_auth_action = "login"
        self._connect_and_auth(username, password, host, port, use_tls, MSG_AUTH_LOGIN)

    def _do_register(self, username, password, host, port, use_tls):
        self._pending_auth_action = "register"
        self._connect_and_auth(username, password, host, port, use_tls, MSG_AUTH_REGISTER)

    def _connect_and_auth(self, username, password, host, port, use_tls, auth_type):
        def task():
            try:
                self.network.connect(host, port, use_tls)
                self.network.start_recv_loop(self._on_message_received)
                self.network.send({
                    "type": auth_type,
                    "username": username,
                    "password": password,
                })
            except Exception as e:
                self.root.after(0, lambda: self._on_connect_error(str(e)))
        threading.Thread(target=task, daemon=True).start()

    def _on_connect_error(self, error):
        if self._login_screen:
            self._login_screen.set_status(f"Connection failed: {error}")
            self._login_screen.reset_buttons()

    # --- Network message dispatcher (called from recv thread) ---

    def _on_message_received(self, msg: dict):
        """Called from the network recv thread. Schedules UI updates on main thread."""
        self.root.after(0, lambda: self._dispatch_message(msg))

    def _dispatch_message(self, msg: dict):
        msg_type = msg.get("type", "")

        if msg_type == MSG_AUTH_RESULT:
            self._handle_auth_result(msg)
        elif msg_type == MSG_CHANNEL_INFO:
            self._handle_channel_info(msg)
        elif msg_type == MSG_CHANNEL_JOINED:
            self._handle_channel_joined(msg)
        elif msg_type == MSG_CHANNEL_CREATED:
            self._handle_channel_created(msg)
        elif msg_type == MSG_MESSAGE:
            self._handle_chat_message(msg)
        elif msg_type == MSG_PRIVATE_MESSAGE:
            self._handle_private_message(msg)
        elif msg_type == MSG_ACTION:
            self._handle_action(msg)
        elif msg_type == MSG_USER_JOINED:
            self._handle_user_joined(msg)
        elif msg_type == MSG_USER_LEFT:
            self._handle_user_left(msg)
        elif msg_type == MSG_USER_LIST:
            self._handle_user_list(msg)
        elif msg_type == MSG_STATUS_CHANGE:
            self._handle_status_change(msg)
        elif msg_type == MSG_ERROR:
            self._handle_error(msg)
        elif msg_type == MSG_SYSTEM:
            self._handle_system(msg)
        elif msg_type == "_disconnected":
            self._handle_disconnect()

    # --- Message handlers ---

    def _handle_auth_result(self, msg):
        if msg.get("success"):
            self.session.set_authenticated(msg["username"], msg.get("token"))
            self._show_chat_screen()
        else:
            if self._login_screen:
                self._login_screen.set_status(msg.get("error", "Authentication failed."))
                self._login_screen.reset_buttons()

    def _handle_channel_info(self, msg):
        channels = msg.get("channels", [])
        self.session.channels = channels
        self._channel_descriptions = {ch["name"]: ch.get("description", "") for ch in channels}
        if self._chat_screen:
            self._chat_screen.sidebar_channels.set_channels(channels)

    def _handle_channel_joined(self, msg):
        channel = msg.get("channel", "")
        self.session.current_channel = channel
        if self._chat_screen:
            self._chat_screen.sidebar_channels.set_active_channel(channel)
            self._chat_screen.top_bar.set_channel(channel, self._channel_descriptions.get(channel, ""))
            self._chat_screen.message_area.load_history(msg.get("history", []))
            self._chat_screen.message_input.set_placeholder(channel)
            self._chat_screen.message_input.focus_input()

            users = msg.get("users", [])
            self._chat_screen.sidebar_users.set_users(users)

    def _handle_channel_created(self, msg):
        channel = msg.get("channel", {})
        name = channel.get("name", "")
        desc = channel.get("description", "")
        if name:
            self._channel_descriptions[name] = desc
            if self._chat_screen:
                self._chat_screen.sidebar_channels.add_channel(name)

    def _handle_chat_message(self, msg):
        if not self._chat_screen:
            return
        channel = msg.get("channel", "")
        sender = msg.get("sender", "")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")

        if channel == self.session.current_channel:
            self._chat_screen.message_area.add_message(sender, content, timestamp)
        else:
            # Notification for message in another channel
            notify(f"#{channel}", f"{sender}: {content}")

    def _handle_private_message(self, msg):
        if not self._chat_screen:
            return
        from_user = msg.get("from", "")
        to_user = msg.get("to", "")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")

        if to_user:
            # This is our sent message echoed back
            self._chat_screen.message_area.add_message(
                f"[PM -> {to_user}]", content, timestamp
            )
        else:
            # Incoming PM
            self._chat_screen.message_area.add_message(
                f"[PM] {from_user}", content, timestamp
            )
            notify(f"PM from {from_user}", content)

    def _handle_action(self, msg):
        if not self._chat_screen:
            return
        channel = msg.get("channel", "")
        if channel == self.session.current_channel:
            self._chat_screen.message_area.add_message(
                msg.get("sender", ""), msg.get("content", ""),
                msg.get("timestamp", ""), msg_type="action"
            )

    def _handle_user_joined(self, msg):
        if not self._chat_screen:
            return
        username = msg.get("username", "")
        channel = msg.get("channel", "")
        if channel == self.session.current_channel:
            self._chat_screen.sidebar_users.add_user(username, "online")
            self._chat_screen.message_area.add_system_message(f"{username} joined the channel.")

    def _handle_user_left(self, msg):
        if not self._chat_screen:
            return
        username = msg.get("username", "")
        channel = msg.get("channel", "")
        if channel == self.session.current_channel:
            self._chat_screen.sidebar_users.remove_user(username)
            self._chat_screen.message_area.add_system_message(f"{username} left the channel.")

    def _handle_user_list(self, msg):
        if not self._chat_screen:
            return
        self._chat_screen.sidebar_users.set_users(msg.get("users", []))

    def _handle_status_change(self, msg):
        pass  # Could update user status indicators globally

    def _handle_error(self, msg):
        error_text = msg.get("message", "Unknown error")
        if self._chat_screen:
            self._chat_screen.message_area.add_system_message(f"Error: {error_text}")
        elif self._login_screen:
            self._login_screen.set_status(error_text)

    def _handle_system(self, msg):
        if self._chat_screen:
            self._chat_screen.message_area.add_system_message(msg.get("message", ""))

    def _handle_disconnect(self):
        self.session.clear()
        if self._chat_screen:
            self._chat_screen.message_area.add_system_message("Disconnected from server.")

    # --- User actions ---

    def _on_send_message(self, text: str):
        """Handle user sending a message (from the input bar)."""
        if not self.network.connected:
            return

        # Parse slash commands
        if text.startswith("/"):
            self._handle_slash_command(text)
            return

        # Regular message
        if self.session.current_channel:
            try:
                self.network.send({
                    "type": MSG_MESSAGE,
                    "channel": self.session.current_channel,
                    "content": text,
                })
            except Exception:
                pass

    def _handle_slash_command(self, text: str):
        parts = text.split(" ", 2)
        cmd = parts[0].lower()

        if cmd == "/msg" and len(parts) >= 3:
            try:
                self.network.send({
                    "type": MSG_PRIVATE_MESSAGE,
                    "to": parts[1],
                    "content": parts[2],
                })
            except Exception:
                pass
        elif cmd == "/me" and len(parts) >= 2:
            action_text = " ".join(parts[1:])
            try:
                self.network.send({
                    "type": MSG_ACTION,
                    "channel": self.session.current_channel,
                    "content": action_text,
                })
            except Exception:
                pass
        elif cmd == "/quit":
            self._on_close()
        else:
            if self._chat_screen:
                self._chat_screen.message_area.add_system_message(f"Unknown command: {cmd}")

    def _on_channel_select(self, channel_name: str):
        try:
            self.network.send({
                "type": MSG_CHANNEL_JOIN,
                "channel": channel_name,
            })
        except Exception:
            pass

    def _on_channel_create(self, name: str):
        try:
            self.network.send({
                "type": MSG_CHANNEL_CREATE,
                "name": name,
                "description": "",
            })
        except Exception:
            pass

    def _on_close(self):
        try:
            self.network.disconnect()
        except Exception:
            pass
        self.root.destroy()
