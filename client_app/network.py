"""Client-side network layer: connection, TLS, send/receive."""

import socket
import ssl
import threading

from shared.protocol import MessageReader, send_message
from shared.constants import SOCKET_TIMEOUT


class NetworkClient:
    def __init__(self):
        self.sock = None
        self._reader = None
        self._recv_thread = None
        self._connected = False
        self._callback = None

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self, host: str, port: int, use_tls: bool = False):
        """Connect to the chat server."""
        raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_sock.settimeout(SOCKET_TIMEOUT)
        raw_sock.connect((host, port))

        if use_tls:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE  # self-signed certs
            self.sock = context.wrap_socket(raw_sock, server_hostname=host)
        else:
            self.sock = raw_sock

        self._connected = True
        self._reader = MessageReader(self.sock)

    def start_recv_loop(self, callback):
        """Start a background thread that calls callback(msg_dict) for each message.

        The callback is called from the recv thread - if updating a GUI,
        use app.after() or equivalent to schedule on the main thread.
        """
        self._callback = callback
        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._recv_thread.start()

    def _recv_loop(self):
        try:
            for msg in self._reader:
                if self._callback:
                    self._callback(msg)
        except Exception:
            pass
        finally:
            self._connected = False
            if self._callback:
                self._callback({"type": "_disconnected"})

    def send(self, msg: dict):
        """Send a message dict to the server."""
        if not self._connected or not self.sock:
            raise ConnectionError("Not connected")
        send_message(self.sock, msg)

    def disconnect(self):
        """Disconnect from the server."""
        self._connected = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
