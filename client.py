#!/usr/bin/env python3
import argparse
import socket
import threading
import sys

ENCODING = "utf-8"
BUFSIZE = 4096

def recv_loop(sock):
    try:
        file = sock.makefile("r", encoding=ENCODING, newline="\n")
        for line in file:
            line = line.rstrip("\n\r")
            if line:
                print(line)
    except Exception:
        pass
    finally:
        print("[client] Disconnected from server.")
        try:
            sock.close()
        except Exception:
            pass
        # Exit the whole process when reader ends
        try:
            sys.exit(0)
        except SystemExit:
            pass

def main():
    ap = argparse.ArgumentParser(description="Minimal Python TCP chat client.")
    ap.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    ap.add_argument("--port", type=int, default=5050, help="Server port (default: 5050)")
    ap.add_argument("--nick", default=None, help="Nickname to set on connect")
    args = ap.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((args.host, args.port))
    except Exception as e:
        print(f"[client] Could not connect to {args.host}:{args.port} - {e}")
        return

    threading.Thread(target=recv_loop, args=(sock,), daemon=True).start()

    # Set nickname if provided
    if args.nick:
        try:
            sock.sendall(f"/nick {args.nick}\n".encode(ENCODING))
        except Exception:
            print("[client] Failed to send nick command.")
    
    print("[client] Connected. Type messages and press Enter. Use /quit to exit.")

    try:
        for line in sys.stdin:
            line = line.rstrip("\n\r")
            if not line:
                continue
            try:
                sock.sendall((line + "\n").encode(ENCODING))
            except Exception:
                print("[client] Send failed; connection closed?")
                break
            if line.strip().lower() == "/quit":
                break
    except KeyboardInterrupt:
        pass
    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
