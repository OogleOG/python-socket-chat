"""Message input bar with send button."""

import customtkinter as ctk
from client_app.ui.theme import (
    BG_MAIN, BG_INPUT, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT, ACCENT_HOVER,
    FONT_FAMILY, FONT_SIZE_NORMAL, INPUT_HEIGHT,
)


class MessageInput(ctk.CTkFrame):
    def __init__(self, parent, on_send):
        super().__init__(parent, fg_color=BG_MAIN, height=INPUT_HEIGHT, corner_radius=0)
        self.pack_propagate(False)
        self._on_send = on_send

        # Inner container with padding
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=10)

        # Input container (rounded background)
        input_container = ctk.CTkFrame(inner, fg_color=BG_INPUT, corner_radius=8)
        input_container.pack(fill="both", expand=True)

        # Text entry
        self.entry = ctk.CTkEntry(
            input_container,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            fg_color="transparent",
            border_width=0,
            text_color=TEXT_PRIMARY,
            placeholder_text="Message #channel",
            placeholder_text_color=TEXT_SECONDARY,
            height=40,
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(12, 0))

        # Send button
        self.send_btn = ctk.CTkButton(
            input_container, text="Send",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
            width=60, height=32,
            corner_radius=4,
            command=self._do_send,
        )
        self.send_btn.pack(side="right", padx=6, pady=4)

        # Bind Enter key
        self.entry.bind("<Return>", lambda e: self._do_send())

    def _do_send(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self._on_send(text)

    def set_placeholder(self, channel: str):
        self.entry.configure(placeholder_text=f"Message #{channel}")

    def focus_input(self):
        self.entry.focus()
