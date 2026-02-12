"""Right sidebar: online user list with status indicators."""

import customtkinter as ctk
from client_app.ui.theme import (
    BG_DARK, TEXT_PRIMARY, TEXT_SECONDARY, SEPARATOR,
    STATUS_ONLINE, STATUS_OFFLINE,
    FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_SMALL, USER_SIDEBAR_WIDTH,
)


class SidebarUsers(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=BG_DARK, width=USER_SIDEBAR_WIDTH, corner_radius=0)
        self.pack_propagate(False)
        self._user_frames: dict[str, ctk.CTkFrame] = {}

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=48)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="Online",
            font=(FONT_FAMILY, 12, "bold"),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).pack(side="left", padx=16, pady=12)

        self.count_label = ctk.CTkLabel(
            header, text="0",
            font=(FONT_FAMILY, 12),
            text_color=TEXT_SECONDARY,
        )
        self.count_label.pack(side="right", padx=16)

        # Separator
        ctk.CTkFrame(self, fg_color=SEPARATOR, height=1, corner_radius=0).pack(fill="x")

        # Scrollable user list
        self.user_list = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color="#3f4147",
            scrollbar_button_hover_color="#5c5f63",
        )
        self.user_list.pack(fill="both", expand=True, padx=8, pady=8)

    def set_users(self, users: list[dict]):
        """Update the user list. Each user dict has 'username' and 'status'."""
        # Clear existing
        for frame in self._user_frames.values():
            frame.destroy()
        self._user_frames.clear()

        for user in users:
            self._add_user(user["username"], user.get("status", "online"))

        self.count_label.configure(text=str(len(users)))

    def add_user(self, username: str, status: str = "online"):
        if username not in self._user_frames:
            self._add_user(username, status)
            self._update_count()

    def remove_user(self, username: str):
        frame = self._user_frames.pop(username, None)
        if frame:
            frame.destroy()
            self._update_count()

    def _add_user(self, username: str, status: str):
        frame = ctk.CTkFrame(self.user_list, fg_color="transparent", height=36)
        frame.pack(fill="x", pady=1)
        frame.pack_propagate(False)

        # Status dot
        dot_color = STATUS_ONLINE if status == "online" else STATUS_OFFLINE
        dot = ctk.CTkLabel(
            frame, text="\u25cf",  # Filled circle
            font=(FONT_FAMILY, 10),
            text_color=dot_color,
            width=20,
        )
        dot.pack(side="left", padx=(4, 0))

        # Username
        ctk.CTkLabel(
            frame, text=username,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            text_color=TEXT_PRIMARY if status == "online" else TEXT_SECONDARY,
            anchor="w",
        ).pack(side="left", padx=(4, 0), fill="x", expand=True)

        self._user_frames[username] = frame

    def _update_count(self):
        self.count_label.configure(text=str(len(self._user_frames)))
