import customtkinter as ctk
from ui.theme import *
from database.db_manager import DatabaseManager
from models.session import StudySession


class SessionCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        session: StudySession,
        index: int,
        db: DatabaseManager,
        on_notes_saved=None,
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=CARD_BG,
            border_color=ACCENT1,
            border_width=1,
            corner_radius=CARD_RADIUS,
            **kwargs,
        )
        self.session = session
        self.db = db
        self._on_notes_saved = on_notes_saved
        self._build(index)

    def _build(self, index: int):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD, pady=(PAD, 6))

        badge = ctk.CTkLabel(
            header,
            text=f"  \U0001f431 Session {index}  ",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=ACCENT1,
            text_color="#FFFFFF",
            corner_radius=BTN_RADIUS,
        )
        badge.pack(side="left", padx=(0, 12))

        remark_preview = (
            self.session.remark[:55] + "\u2026"
            if len(self.session.remark) > 55
            else self.session.remark
        )
        remark_lbl = ctk.CTkLabel(
            header,
            text=remark_preview,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=ACCENT2,
            wraplength=420,
            justify="left",
        )
        remark_lbl.pack(side="left", fill="x", expand=True)

        info = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=8)
        info.pack(fill="x", padx=PAD, pady=(0, 8))

        fields = [
            ("\ud83d\udd50 Start", self.session.start_time),
            ("\ud83d\udd51 End", self.session.end_time),
            ("\u23f1 Duration", self.session.duration_display()),
        ]
        for label, value in fields:
            col = ctk.CTkFrame(info, fg_color="transparent")
            col.pack(side="left", expand=True, fill="x", padx=12, pady=8)
            ctk.CTkLabel(
                col,
                text=label,
                font=ctk.CTkFont(family="Segoe UI", size=9),
                text_color=TEXT_MUTED,
            ).pack()
            ctk.CTkLabel(
                col,
                text=value,
                font=ctk.CTkFont(family="Courier New", size=12, weight="bold"),
                text_color=TEXT_PRIMARY,
            ).pack()

        notes_frame = ctk.CTkFrame(self, fg_color="transparent")
        notes_frame.pack(fill="x", padx=PAD, pady=(0, PAD))

        ctk.CTkLabel(
            notes_frame,
            text="\ud83d\udcdd Notes:",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(0, 8))

        self.notes_var = ctk.StringVar(value=self.session.notes or "")
        notes_entry = ctk.CTkEntry(
            notes_frame,
            textvariable=self.notes_var,
            placeholder_text="\u270f\ufe0f  Add your study notes here\u2026",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=CARD_BG,
            border_color=CARD_BORDER,
            text_color=TEXT_PRIMARY,
            height=32,
        )
        notes_entry.pack(side="left", fill="x", expand=True)
        notes_entry.bind("<FocusOut>", self._save_notes)
        notes_entry.bind("<Return>", self._save_notes)

    def _save_notes(self, event=None):
        notes = self.notes_var.get().strip()
        if self.session.id:
            self.session.notes = notes
            self.db.update_notes(self.session.id, notes)
            if self._on_notes_saved:
                self._on_notes_saved()
