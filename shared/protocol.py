"""Length-prefixed JSON message protocol.

Wire format: [4-byte big-endian uint32 payload length][UTF-8 JSON payload]
"""

import json
import struct
from .constants import ENCODING, HEADER_SIZE, MAX_MESSAGE_SIZE, RECV_BUFSIZE


def encode_message(msg: dict) -> bytes:
    """Serialize a message dict to wire format (length-prefixed JSON)."""
    payload = json.dumps(msg, ensure_ascii=False).encode(ENCODING)
    if len(payload) > MAX_MESSAGE_SIZE:
        raise ValueError(f"Message payload exceeds max size ({len(payload)} > {MAX_MESSAGE_SIZE})")
    header = struct.pack("!I", len(payload))
    return header + payload


def decode_message(data: bytes) -> dict:
    """Deserialize a JSON payload (without length prefix) to a dict."""
    return json.loads(data.decode(ENCODING))


class MessageReader:
    """Buffered reader that extracts complete length-prefixed JSON messages
    from a socket. Handles partial reads across multiple recv() calls.

    Usage:
        reader = MessageReader(sock)
        for msg in reader:
            handle(msg)  # msg is a dict
    """

    def __init__(self, sock):
        self.sock = sock
        self._buffer = b""

    def __iter__(self):
        return self

    def __next__(self) -> dict:
        """Read the next complete message from the socket.

        Returns:
            Decoded message dict.

        Raises:
            StopIteration: When the connection is closed.
            ConnectionError: On socket errors.
        """
        while True:
            # Try to extract a complete message from the buffer
            msg = self._try_extract()
            if msg is not None:
                return msg

            # Need more data
            try:
                chunk = self.sock.recv(RECV_BUFSIZE)
            except OSError:
                raise StopIteration
            if not chunk:
                raise StopIteration
            self._buffer += chunk

    def _try_extract(self):
        """Try to extract a complete message from the internal buffer.

        Returns:
            Decoded message dict, or None if not enough data yet.
        """
        if len(self._buffer) < HEADER_SIZE:
            return None

        payload_len = struct.unpack("!I", self._buffer[:HEADER_SIZE])[0]

        if payload_len > MAX_MESSAGE_SIZE:
            raise ConnectionError(f"Message too large: {payload_len} bytes")

        total_needed = HEADER_SIZE + payload_len
        if len(self._buffer) < total_needed:
            return None

        payload = self._buffer[HEADER_SIZE:total_needed]
        self._buffer = self._buffer[total_needed:]
        return decode_message(payload)

    def feed(self, data: bytes):
        """Manually feed data into the buffer (useful for testing)."""
        self._buffer += data

    def pending(self) -> bool:
        """Check if there might be a complete message in the buffer."""
        if len(self._buffer) < HEADER_SIZE:
            return False
        payload_len = struct.unpack("!I", self._buffer[:HEADER_SIZE])[0]
        return len(self._buffer) >= HEADER_SIZE + payload_len


def send_message(sock, msg: dict):
    """Encode and send a message dict over a socket."""
    sock.sendall(encode_message(msg))
