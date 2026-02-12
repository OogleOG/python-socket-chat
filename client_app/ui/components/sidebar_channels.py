"""Left sidebar: channel list with create button."""

import customtkinter as ctk
from client_app.ui.theme import (
    BG_DARK, BG_HOVER, BG_ACTIVE, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT, ACCENT_HOVER, SEPARATOR,
    FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_SMALL, SIDEBAR_WIDTH,
)


class SidebarChannels(ctk.CTkFrame):
    def __init__(self, parent, on_channel_select, on_channel_create):
        super().__init__(parent, fg_color=BG_DARK, width=SIDEBAR_WIDTH, corner_radius=0)
        self.pack_propagate(False)
        self._on_channel_select = on_channel_select
        self._on_channel_create = on_channel_create
        self._channel_buttons: dict[str, ctk.CTkButton] = {}
        self._current_channel = None

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=48)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="Channels",
            font=(FONT_FAMILY, 12, "bold"),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).pack(side="left", padx=16, pady=12)

        # Add channel button
        add_btn = ctk.CTkButton(
            header, text="+",
            font=(FONT_FAMILY, 16, "bold"),
            fg_color="transparent",
            hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY,
            width=28, height=28,
            corner_radius=4,
            command=self._create_channel_dialog,
        )
        add_btn.pack(side="right", padx=8)

        # Separator
        ctk.CTkFrame(self, fg_color=SEPARATOR, height=1, corner_radius=0).pack(fill="x")

        # Scrollable channel list
        self.channel_list = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=BG_HOVER,
            scrollbar_button_hover_color=BG_ACTIVE,
        )
        self.channel_list.pack(fill="both", expand=True, padx=8, pady=8)

    def set_channels(self, channels: list[dict]):
        """Update the channel list. Each channel dict has 'name' and 'description'."""
        # Clear existing
        for btn in self._channel_buttons.values():
            btn.destroy()
        self._channel_buttons.clear()

        for ch in channels:
            self._add_channel_button(ch["name"])

        # Re-highlight current
        if self._current_channel and self._current_channel in self._channel_buttons:
            self._highlight(self._current_channel)

    def _add_channel_button(self, name: str):
        btn = ctk.CTkButton(
            self.channel_list,
            text=f"# {name}",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            fg_color="transparent",
            hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY,
            anchor="w",
            height=32,
            corner_radius=4,
            command=lambda n=name: self._select(n),
        )
        btn.pack(fill="x", pady=1)
        self._channel_buttons[name] = btn

    def _select(self, channel_name: str):
        if channel_name == self._current_channel:
            return
        self._highlight(channel_name)
        self._on_channel_select(channel_name)

    def _highlight(self, channel_name: str):
        # Reset all
        for name, btn in self._channel_buttons.items():
            if name == channel_name:
                btn.configure(fg_color=BG_ACTIVE, text_color=TEXT_PRIMARY)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SECONDARY)
        self._current_channel = channel_name

    def set_active_channel(self, channel_name: str):
        self._highlight(channel_name)

    def add_channel(self, name: str):
        """Add a single new channel to the list."""
        if name not in self._channel_buttons:
            self._add_channel_button(name)

    def _create_channel_dialog(self):
        dialog = ctk.CTkInputDialog(
            text="Enter channel name (lowercase, hyphens allowed):",
            title="Create Channel",
        )
        name = dialog.get_input()
        if name and name.strip():
            self._on_channel_create(name.strip().lower())
