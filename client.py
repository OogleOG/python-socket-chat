#!/usr/bin/env python3
"""Chat client entry point."""

from client_app.ui.app import ChatApp


def main():
    app = ChatApp()
    app.run()


if __name__ == "__main__":
    main()
