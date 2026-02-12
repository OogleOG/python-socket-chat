#!/usr/bin/env python3
"""Chat server entry point."""

import argparse
from server_app.chat_server import ChatServer


def main():
    ap = argparse.ArgumentParser(description="Chat server")
    ap.add_argument("--host", default="127.0.0.1", help="Host/IP to bind (default: 127.0.0.1)")
    ap.add_argument("--port", type=int, default=5050, help="Port to listen on (default: 5050)")
    ap.add_argument("--db", default="chat_data.db", help="Database file path (default: chat_data.db)")
    ap.add_argument("--no-tls", action="store_true", help="Disable TLS (development only)")
    ap.add_argument("--cert", default="certs/server.crt", help="TLS certificate file")
    ap.add_argument("--key", default="certs/server.key", help="TLS private key file")
    args = ap.parse_args()

    use_tls = not args.no_tls
    srv = ChatServer(
        host=args.host,
        port=args.port,
        db_path=args.db,
        use_tls=use_tls,
        certfile=args.cert if use_tls else None,
        keyfile=args.key if use_tls else None,
    )
    try:
        srv.start()
    except KeyboardInterrupt:
        print("\n[SERVER] KeyboardInterrupt, shutting down...")
        srv.shutdown()


if __name__ == "__main__":
    main()
