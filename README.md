# Python Socket Chat

A **Discord-like desktop chat application** built with Python. Features a modern dark-themed GUI (CustomTkinter), user authentication, encrypted connections, multiple channels, message history, and real-time notifications.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **Discord-inspired UI** — Dark theme with channel sidebar, message area, and online user list
- **User Authentication** — Registration and login with bcrypt-hashed passwords
- **Multiple Channels** — Create and switch between chat rooms with persistent message history
- **Private Messaging** — Direct messages between users with `/msg`
- **TLS Encryption** — Optional SSL/TLS support for secure connections
- **SQLite Database** — Persistent storage for users, channels, and messages
- **Rate Limiting** — Flood protection (5 messages/second per user)
- **Input Validation** — Username, password, message, and channel name validation
- **Desktop Notifications** — Toast notifications for messages in other channels and PMs
- **Slash Commands** — `/msg`, `/me`, `/quit` still work from the message input

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the server

```bash
python server.py --no-tls
```

Use `--no-tls` for local development. The server listens on `127.0.0.1:5050` by default.

### 3. Launch the client

```bash
python client.py
```

A GUI window will open. Register a new account or log in, and you're chatting!

Open multiple client windows to test multi-user chat.

---

## Screenshots

The client features a three-panel layout inspired by Discord:

- **Left sidebar** — Channel list with a "+" button to create new channels
- **Center** — Message area with timestamps and a message input bar
- **Right sidebar** — Online user list with status indicators

---

## Server Options

```
python server.py [OPTIONS]

  --host HOST    Bind address (default: 127.0.0.1)
  --port PORT    Listen port (default: 5050)
  --db PATH      SQLite database file (default: chat_data.db)
  --no-tls       Disable TLS encryption (for development)
  --cert FILE    TLS certificate file (default: certs/server.crt)
  --key FILE     TLS private key file (default: certs/server.key)
```

### TLS Setup

To enable encrypted connections:

```bash
python certs/gen_certs.py    # Generate self-signed certificates
python server.py             # Start with TLS enabled
```

Then check "Use TLS" in the client's Advanced connection settings.

---

## Slash Commands

Type these in the message input bar:

| Command | Description |
|---|---|
| `/msg <user> <message>` | Send a private message |
| `/me <action>` | Send an action (e.g., `/me waves`) |
| `/quit` | Disconnect and close |

---

## Project Structure

```
python-socket-chat/
├── server.py                  # Server entry point
├── client.py                  # Client entry point (GUI)
├── requirements.txt
├── certs/
│   └── gen_certs.py           # Self-signed TLS certificate generator
├── shared/
│   ├── protocol.py            # Length-prefixed JSON wire protocol
│   ├── constants.py           # Shared constants and message types
│   └── validators.py          # Input validation and sanitization
├── server_app/
│   ├── chat_server.py         # Multi-threaded chat server
│   ├── auth.py                # bcrypt password hashing, session tokens
│   ├── database.py            # SQLite database layer
│   ├── rate_limiter.py        # Per-user rate limiting
│   └── channel_manager.py     # Channel membership tracking
└── client_app/
    ├── network.py             # Socket connection and TLS
    ├── session.py             # Client-side session state
    └── ui/
        ├── app.py             # Main application window
        ├── login_screen.py    # Login/registration screen
        ├── chat_screen.py     # Chat layout (3-column grid)
        ├── theme.py           # Discord dark theme colors and fonts
        ├── notifications.py   # Desktop notifications
        └── components/
            ├── sidebar_channels.py
            ├── message_area.py
            ├── sidebar_users.py
            ├── message_input.py
            └── top_bar.py
```

---

## Technical Details

### Protocol

Communication uses a **length-prefixed JSON** format over TCP:

```
[4-byte big-endian payload length][UTF-8 JSON payload]
```

This replaces newline-delimited text, correctly handling multiline messages and structured data.

### Database Schema

SQLite stores four tables:
- **users** — Accounts with bcrypt-hashed passwords
- **channels** — Chat rooms with descriptions
- **messages** — Message history (indexed by channel and timestamp)
- **sessions** — Authentication tokens with expiry

### Security

- Passwords hashed with **bcrypt** (12 rounds)
- Session tokens generated via `secrets.token_hex(32)`
- Optional **TLS/SSL** encryption for all traffic
- Input validation on usernames, passwords, messages, and channel names
- Rate limiting prevents message flooding

---

## Requirements

- Python 3.10+
- Dependencies: `customtkinter`, `bcrypt`, `plyer`, `Pillow`

---

## License

MIT
