"""Login and registration screen."""

import customtkinter as ctk
from client_app.ui.theme import (
    BG_DARKEST, BG_DARK, BG_INPUT, BG_MAIN,
    TEXT_PRIMARY, TEXT_SECONDARY, ACCENT, ACCENT_HOVER, ACCENT_RED,
    FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_LARGE, FONT_SIZE_TITLE,
)


class LoginScreen(ctk.CTkFrame):
    def __init__(self, parent, on_login_callback, on_register_callback):
        super().__init__(parent, fg_color=BG_DARKEST)
        self._on_login = on_login_callback
        self._on_register = on_register_callback
        self._build_ui()

    def _build_ui(self):
        # Center container
        center = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=12, width=400, height=500)
        center.place(relx=0.5, rely=0.5, anchor="center")
        center.pack_propagate(False)

        # Inner padding
        inner = ctk.CTkFrame(center, fg_color="transparent")
        inner.pack(expand=True, fill="both", padx=40, pady=40)

        # Title
        ctk.CTkLabel(
            inner, text="Welcome Back!",
            font=(FONT_FAMILY, FONT_SIZE_TITLE, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            inner, text="We're so excited to see you again!",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            text_color=TEXT_SECONDARY,
        ).pack(pady=(0, 25))

        # Username
        ctk.CTkLabel(
            inner, text="USERNAME",
            font=(FONT_FAMILY, 11, "bold"),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 5))

        self.username_entry = ctk.CTkEntry(
            inner,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            fg_color=BG_INPUT,
            border_color=BG_INPUT,
            text_color=TEXT_PRIMARY,
            height=40,
            corner_radius=4,
        )
        self.username_entry.pack(fill="x", pady=(0, 15))

        # Password
        ctk.CTkLabel(
            inner, text="PASSWORD",
            font=(FONT_FAMILY, 11, "bold"),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 5))

        self.password_entry = ctk.CTkEntry(
            inner,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            fg_color=BG_INPUT,
            border_color=BG_INPUT,
            text_color=TEXT_PRIMARY,
            show="*",
            height=40,
            corner_radius=4,
        )
        self.password_entry.pack(fill="x", pady=(0, 20))

        # Login button
        self.login_btn = ctk.CTkButton(
            inner, text="Log In",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
            height=44,
            corner_radius=4,
            command=self._do_login,
        )
        self.login_btn.pack(fill="x", pady=(0, 10))

        # Register link
        reg_frame = ctk.CTkFrame(inner, fg_color="transparent")
        reg_frame.pack(fill="x")

        ctk.CTkLabel(
            reg_frame, text="Need an account?",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            text_color=TEXT_SECONDARY,
        ).pack(side="left")

        self.register_btn = ctk.CTkButton(
            reg_frame, text="Register",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            fg_color="transparent",
            hover_color=BG_INPUT,
            text_color=ACCENT,
            width=70,
            command=self._do_register,
        )
        self.register_btn.pack(side="left")

        # Status message
        self.status_label = ctk.CTkLabel(
            inner, text="",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            text_color=ACCENT_RED,
            wraplength=320,
        )
        self.status_label.pack(fill="x", pady=(10, 0))

        # Advanced section (host/port)
        advanced_toggle = ctk.CTkButton(
            inner, text="Advanced",
            font=(FONT_FAMILY, 11),
            fg_color="transparent",
            hover_color=BG_INPUT,
            text_color=TEXT_SECONDARY,
            width=70,
            height=25,
            command=self._toggle_advanced,
        )
        advanced_toggle.pack(pady=(10, 0))

        self.advanced_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self._advanced_visible = False

        # Host/Port in advanced
        host_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
        host_frame.pack(fill="x", pady=(5, 0))

        ctk.CTkLabel(host_frame, text="Host:", font=(FONT_FAMILY, 11),
                     text_color=TEXT_SECONDARY, width=40).pack(side="left")
        self.host_entry = ctk.CTkEntry(
            host_frame, font=(FONT_FAMILY, 11), fg_color=BG_INPUT,
            border_color=BG_INPUT, text_color=TEXT_PRIMARY, height=30, corner_radius=4,
        )
        self.host_entry.insert(0, "127.0.0.1")
        self.host_entry.pack(side="left", fill="x", expand=True, padx=(5, 10))

        ctk.CTkLabel(host_frame, text="Port:", font=(FONT_FAMILY, 11),
                     text_color=TEXT_SECONDARY, width=35).pack(side="left")
        self.port_entry = ctk.CTkEntry(
            host_frame, font=(FONT_FAMILY, 11), fg_color=BG_INPUT,
            border_color=BG_INPUT, text_color=TEXT_PRIMARY, height=30, width=70, corner_radius=4,
        )
        self.port_entry.insert(0, "5050")
        self.port_entry.pack(side="left")

        # TLS checkbox
        self.tls_var = ctk.BooleanVar(value=False)
        self.tls_check = ctk.CTkCheckBox(
            self.advanced_frame, text="Use TLS",
            font=(FONT_FAMILY, 11), text_color=TEXT_SECONDARY,
            variable=self.tls_var,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
        )
        self.tls_check.pack(pady=(5, 0))

        # Bind Enter key
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self._do_login())

    def _toggle_advanced(self):
        if self._advanced_visible:
            self.advanced_frame.pack_forget()
        else:
            self.advanced_frame.pack(fill="x")
        self._advanced_visible = not self._advanced_visible

    def _get_connection_info(self) -> tuple[str, int, bool]:
        host = self.host_entry.get().strip() or "127.0.0.1"
        try:
            port = int(self.port_entry.get().strip())
        except ValueError:
            port = 5050
        return host, port, self.tls_var.get()

    def _do_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            self.set_status("Please enter username and password.")
            return
        host, port, use_tls = self._get_connection_info()
        self.set_status("")
        self.login_btn.configure(state="disabled", text="Connecting...")
        self._on_login(username, password, host, port, use_tls)

    def _do_register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            self.set_status("Please enter username and password.")
            return
        host, port, use_tls = self._get_connection_info()
        self.set_status("")
        self.register_btn.configure(state="disabled")
        self._on_register(username, password, host, port, use_tls)

    def set_status(self, text: str, error: bool = True):
        color = ACCENT_RED if error else ACCENT
        self.status_label.configure(text=text, text_color=color)

    def reset_buttons(self):
        self.login_btn.configure(state="normal", text="Log In")
        self.register_btn.configure(state="normal")
