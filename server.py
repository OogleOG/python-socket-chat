#!/usr/bin/env python3
import argparse
import socket
import threading
import time

ENCODING = "utf-8"
BUFSIZE = 4096

class ChatServer:
    def __init__(self, host="127.0.0.1", port=5050):
        self.host = host
        self.port = port
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}  # sock -> {"nick": str, "addr": (host, port)}
        self.lock = threading.Lock()
        self.running = False

    def start(self):
        self.server_sock.bind((self.host, self.port))
        self.server_sock.listen(50)
        self.running = True
        print(f"[SERVER] Listening on {self.host}:{self.port}")
        try:
            while self.running:
                try:
                    client_sock, addr = self.server_sock.accept()
                    client_sock.settimeout(300)
                    with self.lock:
                        self.clients[client_sock] = {"nick": None, "addr": addr}
                    threading.Thread(target=self.handle_client, args=(client_sock,), daemon=True).start()
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

    def broadcast(self, msg, exclude_sock=None):
        dead = []
        with self.lock:
            for sock in self.clients:
                if sock is exclude_sock:
                    continue
                try:
                    sock.sendall(msg.encode(ENCODING) + b"\n")
                except Exception:
                    dead.append(sock)
            for d in dead:
                self._drop_client(d)

    def send(self, sock, msg):
        try:
            sock.sendall(msg.encode(ENCODING) + b"\n")
        except Exception:
            self._drop_client(sock)

    def _drop_client(self, sock):
        info = self.clients.pop(sock, None)
        try:
            sock.close()
        except Exception:
            pass
        if info and info["nick"]:
            self.broadcast(f"[server] {info['nick']} has disconnected.")

    def _unique_nick(self, desired):
        with self.lock:
            existing = {info["nick"] for info in self.clients.values() if info["nick"]}
        nick = desired
        i = 1
        while nick in existing:
            i += 1
            nick = f"{desired}{i}"
        return nick

    def handle_client(self, sock):
        addr = self.clients[sock]["addr"]
        self.send(sock, "[server] Welcome to the chat! Set a nickname with /nick <name>.")
        self.send(sock, "[server] Commands: /nick, /list, /me, /msg, /quit")
        nick = None
        try:
            file = sock.makefile("r", encoding=ENCODING, newline="\n")
            for line in file:
                line = line.rstrip("\n\r")
                if not line:
                    continue

                if line.startswith("/"):
                    parts = line.split(" ", 2)
                    cmd = parts[0].lower()

                    if cmd == "/nick":
                        if len(parts) < 2 or not parts[1].strip():
                            self.send(sock, "[server] Usage: /nick <name>")
                            continue
                        new_nick = self._unique_nick(parts[1].strip())
                        old_nick = self.clients[sock]["nick"]
                        self.clients[sock]["nick"] = new_nick
                        nick = new_nick
                        if not old_nick:
                            self.send(sock, f"[server] Your nickname is now {new_nick}.")
                            self.broadcast(f"[server] {new_nick} has joined the chat.", exclude_sock=sock)
                        else:
                            self.send(sock, f"[server] Nick changed to {new_nick}.")
                            self.broadcast(f"[server] {old_nick} is now known as {new_nick}.", exclude_sock=sock)

                    elif cmd == "/list":
                        with self.lock:
                            names = [info["nick"] or f"{info['addr'][0]}:{info['addr'][1]}" for info in self.clients.values()]
                        self.send(sock, "[server] Users: " + ", ".join(names))

                    elif cmd == "/me":
                        if len(parts) < 2 or not parts[1].strip():
                            self.send(sock, "[server] Usage: /me <action>")
                            continue
                        who = self.clients[sock]["nick"] or f"{addr[0]}:{addr[1]}"
                        self.broadcast(f"* {who} {parts[1].strip()}")

                    elif cmd == "/msg":
                        if len(parts) < 3 or not parts[1].strip() or not parts[2].strip():
                            self.send(sock, "[server] Usage: /msg <nick> <message>")
                            continue
                        target_nick = parts[1].strip()
                        msg = parts[2].strip()
                        target_sock = None
                        with self.lock:
                            for s, info in self.clients.items():
                                if info["nick"] == target_nick:
                                    target_sock = s
                                    break
                        if target_sock is None:
                            self.send(sock, f"[server] User '{target_nick}' not found.")
                        else:
                            sender = self.clients[sock]["nick"] or f"{addr[0]}:{addr[1]}"
                            self.send(target_sock, f"[pm] {sender}: {msg}")
                            self.send(sock, f"[pm -> {target_nick}] {msg}")

                    elif cmd == "/quit":
                        self.send(sock, "[server] Goodbye!")
                        break

                    else:
                        self.send(sock, f"[server] Unknown command: {cmd}")

                else:
                    who = self.clients[sock]["nick"] or f"{addr[0]}:{addr[1]}"
                    self.broadcast(f"[{who}] {line}")
        except Exception as e:
            # Log silently to server console
            print(f"[SERVER] Error with client {addr}: {e}")
        finally:
            self._drop_client(sock)

def main():
    ap = argparse.ArgumentParser(description="Minimal Python TCP chat server.")
    ap.add_argument("--host", default="127.0.0.1", help="Host/IP to bind (default: 127.0.0.1)")
    ap.add_argument("--port", type=int, default=5050, help="Port to listen on (default: 5050)")
    args = ap.parse_args()

    srv = ChatServer(args.host, args.port)
    try:
        srv.start()
    except KeyboardInterrupt:
        print("\n[SERVER] KeyboardInterrupt, shutting down...")
        srv.shutdown()

if __name__ == "__main__":
    main()
