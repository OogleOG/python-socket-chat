"""Main chat screen layout - assembles all components."""

import customtkinter as ctk
from client_app.ui.theme import BG_MAIN
from client_app.ui.components.top_bar import TopBar
from client_app.ui.components.sidebar_channels import SidebarChannels
from client_app.ui.components.message_area import MessageArea
from client_app.ui.components.message_input import MessageInput
from client_app.ui.components.sidebar_users import SidebarUsers


class ChatScreen(ctk.CTkFrame):
    def __init__(self, parent, on_send_message, on_channel_select, on_channel_create):
        super().__init__(parent, fg_color=BG_MAIN, corner_radius=0)

        # Configure 3-column grid
        self.grid_columnconfigure(0, weight=0)  # Channel sidebar (fixed)
        self.grid_columnconfigure(1, weight=1)  # Main area (expands)
        self.grid_columnconfigure(2, weight=0)  # User sidebar (fixed)
        self.grid_rowconfigure(0, weight=1)

        # Left sidebar - channels
        self.sidebar_channels = SidebarChannels(
            self,
            on_channel_select=on_channel_select,
            on_channel_create=on_channel_create,
        )
        self.sidebar_channels.grid(row=0, column=0, sticky="nsew")

        # Center area (top bar + messages + input)
        center = ctk.CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
        center.grid(row=0, column=1, sticky="nsew")
        center.grid_rowconfigure(1, weight=1)  # Message area expands
        center.grid_columnconfigure(0, weight=1)

        # Top bar
        self.top_bar = TopBar(center)
        self.top_bar.grid(row=0, column=0, sticky="ew")

        # Message area
        self.message_area = MessageArea(center)
        self.message_area.grid(row=1, column=0, sticky="nsew")

        # Message input
        self.message_input = MessageInput(center, on_send=on_send_message)
        self.message_input.grid(row=2, column=0, sticky="ew")

        # Right sidebar - users
        self.sidebar_users = SidebarUsers(self)
        self.sidebar_users.grid(row=0, column=2, sticky="nsew")
