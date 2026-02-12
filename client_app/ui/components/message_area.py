"""Scrollable message display area."""

import customtkinter as ctk
from datetime import datetime
from client_app.ui.theme import (
    BG_MAIN, BG_HOVER, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT, ACCENT_GREEN,
    FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_SMALL,
)


class MessageArea(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=BG_MAIN, corner_radius=0)
        self._auto_scroll = True

        # Scrollable container
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color="#4a4d52",
            scrollbar_button_hover_color="#5c5f63",
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Track scroll position for auto-scroll
        self.scroll_frame.bind("<Configure>", self._on_configure)

    def _on_configure(self, event=None):
        pass  # Auto-scroll handled in add_message

    def clear(self):
        """Remove all messages."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

    def load_history(self, messages: list[dict]):
        """Load message history. Each msg has sender, content, timestamp, msg_type."""
        self.clear()
        for msg in messages:
            self._render_message(
                sender=msg.get("sender", ""),
                content=msg.get("content", ""),
                timestamp=msg.get("timestamp", ""),
                msg_type=msg.get("msg_type", "message"),
            )
        self._scroll_to_bottom()

    def add_message(self, sender: str, content: str, timestamp: str = "", msg_type: str = "message"):
        """Add a new message to the display."""
        self._render_message(sender, content, timestamp, msg_type)
        self._scroll_to_bottom()

    def add_system_message(self, text: str):
        """Add a system notification message."""
        frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        frame.pack(fill="x", padx=16, pady=2)

        ctk.CTkLabel(
            frame, text=text,
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "italic"),
            text_color=TEXT_SECONDARY,
            anchor="w",
            wraplength=600,
        ).pack(fill="x")
        self._scroll_to_bottom()

    def _render_message(self, sender: str, content: str, timestamp: str, msg_type: str):
        """Render a single message in the chat area."""
        # Message container
        msg_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        msg_frame.pack(fill="x", padx=16, pady=3)

        if msg_type == "action":
            # Action message: * username does something
            text = f"* {sender} {content}"
            ctk.CTkLabel(
                msg_frame, text=text,
                font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"),
                text_color=TEXT_SECONDARY,
                anchor="w",
                wraplength=600,
            ).pack(fill="x")
            return

        # Header line: username + timestamp
        header = ctk.CTkFrame(msg_frame, fg_color="transparent")
        header.pack(fill="x")

        # Username
        ctk.CTkLabel(
            header, text=sender,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            text_color=ACCENT_GREEN if sender else TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left")

        # Timestamp
        time_str = self._format_timestamp(timestamp)
        if time_str:
            ctk.CTkLabel(
                header, text=time_str,
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                text_color=TEXT_SECONDARY,
                anchor="w",
            ).pack(side="left", padx=(8, 0))

        # Message content
        ctk.CTkLabel(
            msg_frame, text=content,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            text_color=TEXT_PRIMARY,
            anchor="w",
            wraplength=600,
            justify="left",
        ).pack(fill="x")

    def _format_timestamp(self, timestamp: str) -> str:
        if not timestamp:
            return ""
        try:
            dt = datetime.fromisoformat(timestamp)
            now = datetime.now(dt.tzinfo)
            if dt.date() == now.date():
                return f"Today at {dt.strftime('%H:%M')}"
            return dt.strftime("%d/%m/%Y %H:%M")
        except (ValueError, TypeError):
            return timestamp

    def _scroll_to_bottom(self):
        """Scroll to the bottom of the message area."""
        self.scroll_frame.after(50, lambda: self.scroll_frame._parent_canvas.yview_moveto(1.0))
