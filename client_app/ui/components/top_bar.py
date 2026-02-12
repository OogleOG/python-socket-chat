"""Top bar showing current channel name and description."""

import customtkinter as ctk
from client_app.ui.theme import (
    BG_HEADER, TEXT_PRIMARY, TEXT_SECONDARY, SEPARATOR,
    FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_HEADER, TOP_BAR_HEIGHT,
)


class TopBar(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=BG_HEADER, height=TOP_BAR_HEIGHT, corner_radius=0)
        self.pack_propagate(False)

        # Hash + channel name
        self.channel_label = ctk.CTkLabel(
            self, text="# general",
            font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        self.channel_label.pack(side="left", padx=(16, 8), pady=8)

        # Separator line (vertical)
        sep = ctk.CTkFrame(self, fg_color=SEPARATOR, width=1, height=24)
        sep.pack(side="left", padx=(0, 12))

        # Channel description
        self.description_label = ctk.CTkLabel(
            self, text="General discussion",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            text_color=TEXT_SECONDARY,
            anchor="w",
        )
        self.description_label.pack(side="left", fill="x", expand=True)

        # Bottom border
        border = ctk.CTkFrame(self, fg_color=SEPARATOR, height=1, corner_radius=0)
        border.pack(side="bottom", fill="x")

    def set_channel(self, name: str, description: str = ""):
        self.channel_label.configure(text=f"# {name}")
        self.description_label.configure(text=description)
