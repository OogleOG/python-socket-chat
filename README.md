# Python Socket Chat

A minimal **TCP chat application** using Python’s standard library. Includes a multi-client server and a simple terminal client with a few chat commands.

## Features
- Multi-client broadcast chat (threaded server)
- Commands: `/nick`, `/list`, `/me`, `/msg`, `/quit`
- Graceful disconnect handling
- No external dependencies (Python 3.8+)

---

## Quick Start

### 1) Start the server
```bash
python server.py --host 0.0.0.0 --port 5050
```
By default, it listens on `127.0.0.1:5050`.

### 2) Start a client (in a new terminal)
```bash
python client.py --host 127.0.0.1 --port 5050 --nick YourName
```
If `--nick` is omitted, you’ll be prompted on start.

### 3) Commands (in the client)
- `/nick NEWNAME` – change your nickname
- `/list` – list connected users
- `/me ACTION` – emote (`* YourName ACTION`)
- `/msg NAME message` – private message to NAME
- `/quit` – disconnect

---

## Example

**Terminal 1 (server):**
```
python server.py --port 5050
```

**Terminal 2 (client A):**
```
python client.py --nick Alice
```

**Terminal 3 (client B):**
```
python client.py --nick Bob
```

Then type messages in the client windows. Use `/list` to see users, `/msg Bob hi` for a private message, `/me waves`, and `/quit` to exit.

---

## Notes
- This is for learning/demo purposes. It does not implement TLS/SSL or complex moderation.
- NAT/Firewall rules may be required for LAN/WAN connections.
- Tested with Python 3.8+ on Windows/macOS/Linux.

## License
MIT
