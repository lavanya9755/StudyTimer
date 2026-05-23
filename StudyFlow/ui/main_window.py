import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from datetime import datetime, date
import threading
import time
from PIL import Image, ImageTk

from ui.theme import *
from ui.session_card import SessionCard
from ui.analytics_window import AnalyticsWindow
from database.db_manager import DatabaseManager
from analytics.engine import (
    get_remark,
    compute_daily_stats,
    compute_weekly_stats,
    generate_bar_chart,
    generate_pie_chart,
    generate_weekly_chart,
)
from models.session import StudySession


class StudyFlowApp(ctk.CTk):
    _elapsed: int = 0
    _session_start_abs: int = 0
    _total_elapsed_before: int = 0
    _running: bool = False
    _day_started: bool = False

    def __init__(self):
        super().__init__()
        self.title("\U0001f431 StudyFlow")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        self.configure(fg_color=BG_MID)

        self.db = DatabaseManager()
        self._sessions: list[StudySession] = []
        self._session_start_time: str = "00:00:00"
        self._timer_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        self._analytics_sessions = []
        self._analytics_chart_refs = {}
        self._analytics_stats = None
        self._analytics_week_stats = None

        self._build_ui()
        self._load_today_sessions()
        self._update_clock()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_left_panel()
        self._build_right_panel()

    def _build_left_panel(self):
        import tkinter as tk

        PANEL_W = 420
        c1 = "#FFE4EC"
        c2 = "#FFC8D6"

        self._gradient_canvas = tk.Canvas(self, width=PANEL_W, highlightthickness=0)
        self._gradient_canvas.grid(row=0, column=0, sticky="nsew")
        self._gradient_canvas.grid_propagate(False)

        left = ctk.CTkFrame(self._gradient_canvas, fg_color="transparent")
        self._left_win = self._gradient_canvas.create_window(
            PANEL_W // 2, 0, window=left, anchor="n"
        )

        def on_configure(e):
            self._draw_gradient(self._gradient_canvas, c1, c2)
            cw = e.width
            self._gradient_canvas.coords(self._left_win, cw // 2, 0)

        self._gradient_canvas.bind("<Configure>", on_configure)

        cat_frame = ctk.CTkFrame(left, fg_color="transparent")
        cat_frame.pack(pady=(28, 0))

        cat_art = ctk.CTkLabel(
            cat_frame,
            text=(
                "       \u250c_/\u256d\u3000\u3000\n"
                "      \u300e\uff9f\uff61\uff87 \uff57\uff56\u3000\uff57\uff56\n"
                "      \u3000\uff9f\u3000\uff9f\uff9f\uff9f\u3000\uff9f\n"
                "       \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\n"
                "    \u2570\u02d1\u02d1\u02d1\u02d1\u02d1\u02d1\u02d1\u02d1\u256f"
            ),
            font=ctk.CTkFont(family="Courier New", size=14),
            text_color=ACCENT1,
            justify="left",
        )
        cat_art.pack()

        ctk.CTkLabel(
            left,
            text="StudyFlow",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=ACCENT1,
        ).pack(pady=(8, 2))
        ctk.CTkLabel(
            left,
            text="Your purr-fect study companion \ud83d\udc3e",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_MUTED,
        ).pack()

        timer_card = ctk.CTkFrame(
            left,
            fg_color=CARD_BG,
            corner_radius=CARD_RADIUS,
            border_color=ACCENT1,
            border_width=3,
        )
        timer_card.pack(fill="x", padx=24, pady=24)

        self.timer_label = ctk.CTkLabel(
            timer_card,
            text="00:00:00",
            font=ctk.CTkFont(family="Courier New", size=72, weight="bold"),
            text_color=ACCENT1,
        )
        self.timer_label.pack(pady=(22, 6))

        self.status_label = ctk.CTkLabel(
            timer_card,
            text="\u25cf Ready to study",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_MUTED,
        )
        self.status_label.pack(pady=(0, 22))

        btn_grid = ctk.CTkFrame(left, fg_color="transparent")
        btn_grid.pack(fill="x", padx=24)

        self.start_btn = ctk.CTkButton(
            btn_grid,
            text="\u25b6  Start",
            fg_color=BTN_START[0],
            hover_color=BTN_START[1],
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=BTN_HEIGHT,
            corner_radius=BTN_RADIUS,
            command=self._on_start,
        )
        self.start_btn.grid(row=0, column=0, padx=(0, 6), pady=6, sticky="ew")

        self.pause_btn = ctk.CTkButton(
            btn_grid,
            text="\u23f8  Pause",
            fg_color=BTN_PAUSE[0],
            hover_color=BTN_PAUSE[1],
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=BTN_HEIGHT,
            corner_radius=BTN_RADIUS,
            command=self._on_pause,
            state="disabled",
        )
        self.pause_btn.grid(row=0, column=1, padx=(6, 0), pady=6, sticky="ew")

        self.reset_btn = ctk.CTkButton(
            btn_grid,
            text="\U0001f504  Reset",
            fg_color=BTN_RESET[0],
            hover_color=BTN_RESET[1],
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=BTN_HEIGHT,
            corner_radius=BTN_RADIUS,
            command=self._on_reset,
        )
        self.reset_btn.grid(row=1, column=0, padx=(0, 6), pady=6, sticky="ew")

        self.end_btn = ctk.CTkButton(
            btn_grid,
            text="\U0001f3c1  End Day",
            fg_color=BTN_END[0],
            hover_color=BTN_END[1],
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=BTN_HEIGHT,
            corner_radius=BTN_RADIUS,
            command=self._on_end_day,
        )
        self.end_btn.grid(row=1, column=1, padx=(6, 0), pady=6, sticky="ew")

        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)

        summary_card = ctk.CTkFrame(
            left,
            fg_color=CARD_BG,
            corner_radius=CARD_RADIUS,
            border_color=ACCENT1,
            border_width=1,
        )
        summary_card.pack(fill="x", padx=24, pady=(20, 8))

        ctk.CTkLabel(
            summary_card,
            text="\U0001f4c8 Today's Progress",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=ACCENT1,
        ).pack(pady=(12, 4))

        self.sessions_count_lbl = ctk.CTkLabel(
            summary_card,
            text="Sessions: 0   |   Total: 0h 00m",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_SECONDARY,
        )
        self.sessions_count_lbl.pack(pady=(0, 12))

        self.date_label = ctk.CTkLabel(
            left,
            text=date.today().strftime("%A, %B %d, %Y"),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_MUTED,
        )
        self.date_label.pack(side="bottom", pady=8)

        ctk.CTkLabel(
            left,
            text="\ud83d\udc3e  \ud83d\udc3e  \ud83d\udc3e  \u2728",
            font=ctk.CTkFont(size=16),
            text_color=ACCENT1,
        ).pack(side="bottom", pady=4)

    def _draw_gradient(self, canvas, c1, c2):
        canvas.delete("gradient")
        w = canvas.winfo_width() or 420
        h = canvas.winfo_height() or 800
        steps = 64
        for i in range(steps):
            r = int(
                int(c1[1:3], 16) + (int(c2[1:3], 16) - int(c1[1:3], 16)) * i / steps
            )
            g = int(
                int(c1[3:5], 16) + (int(c2[3:5], 16) - int(c1[3:5], 16)) * i / steps
            )
            b = int(
                int(c1[5:7], 16) + (int(c2[5:7], 16) - int(c1[5:7], 16)) * i / steps
            )
            color = f"#{r:02x}{g:02x}{b:02x}"
            y0 = h * i // steps
            y1 = h * (i + 1) // steps
            canvas.create_rectangle(
                0, y0, w, y1, fill=color, outline="", tags="gradient"
            )
        canvas.tag_lower("gradient")

    def _build_right_panel(self):
        right = ctk.CTkFrame(self, fg_color=BG_MID, corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(
            right,
            fg_color=CARD_BG,
            corner_radius=0,
            border_color=ACCENT1,
            border_width=1,
        )
        hdr.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            hdr,
            text="\U0001f4da Study Sessions",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=ACCENT1,
        ).pack(side="left", padx=20, pady=14)

        self.history_btn = ctk.CTkButton(
            hdr,
            text="\U0001f4cb Session History",
            fg_color=SURFACE,
            hover_color=CARD_BORDER,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            height=32,
            corner_radius=6,
            command=self._toggle_history,
        )
        self.history_btn.pack(side="right", padx=20, pady=14)

        tab_row = ctk.CTkFrame(right, fg_color=BG_DARK, height=40, corner_radius=0)
        tab_row.grid(row=0, column=0, sticky="ew", pady=(56, 0))

        self.tabview = ctk.CTkTabview(
            right,
            fg_color=BG_MID,
            segmented_button_fg_color=BG_DARK,
            segmented_button_selected_color=ACCENT1,
            segmented_button_selected_hover_color=ACCENT2,
            segmented_button_unselected_color=BG_DARK,
            segmented_button_unselected_hover_color=SURFACE,
            text_color=TEXT_PRIMARY,
            corner_radius=0,
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

        self.tabview.add("Today")
        self.tabview.add("History")
        self.tabview.add("\u2728 Analytics")
        self.tabview.set("Today")

        self._build_today_tab()
        self._build_history_tab()
        self._build_analytics_tab()

    def _build_today_tab(self):
        tab = self.tabview.tab("Today")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        self.sessions_scroll = ctk.CTkScrollableFrame(
            tab,
            fg_color=BG_MID,
            scrollbar_button_color=CARD_BORDER,
            scrollbar_button_hover_color=ACCENT1,
        )
        self.sessions_scroll.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.sessions_scroll.grid_columnconfigure(0, weight=1)

        self.empty_label = ctk.CTkLabel(
            self.sessions_scroll,
            text=(
                "\ud83d\udc3e  No sessions yet!\n\n"
                "Click \u25b6 Start to begin your first study session.\n"
                "Sessions are automatically saved when you pause."
            ),
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=TEXT_MUTED,
            justify="center",
        )
        self.empty_label.grid(row=0, column=0, pady=60)

    def _build_history_tab(self):
        tab = self.tabview.tab("History")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        table_scroll = ctk.CTkScrollableFrame(
            tab,
            fg_color=BG_MID,
            scrollbar_button_color=CARD_BORDER,
            scrollbar_button_hover_color=ACCENT1,
        )
        table_scroll.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        table_scroll.grid_columnconfigure(0, weight=1)

        self._history_scroll = table_scroll
        self._rebuild_history_table()

    def _build_analytics_tab(self):
        tab = self.tabview.tab("\u2728 Analytics")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        self.analytics_scroll = ctk.CTkScrollableFrame(
            tab,
            fg_color=BG_MID,
            scrollbar_button_color=CARD_BORDER,
            scrollbar_button_hover_color=ACCENT1,
        )
        self.analytics_scroll.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.analytics_scroll.grid_columnconfigure(0, weight=1)

        self.analytics_content = ctk.CTkFrame(
            self.analytics_scroll, fg_color="transparent"
        )
        self.analytics_content.grid(row=0, column=0, sticky="nsew")
        self.analytics_content.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.analytics_content,
            text="\ud83d\udc3e  Click \u2018End Day\u2019 to view your analytics",
            font=ctk.CTkFont(family="Segoe UI", size=16),
            text_color=TEXT_MUTED,
        ).pack(pady=80)

    # ── Data loading ───────────────────────────────────────────────────────────

    def _load_today_sessions(self):
        self._sessions = self.db.get_today_sessions()
        self._rebuild_session_cards()
        self._update_summary()

    def _rebuild_session_cards(self):
        for widget in self.sessions_scroll.winfo_children():
            widget.destroy()

        if not self._sessions:
            self.empty_label = ctk.CTkLabel(
                self.sessions_scroll,
                text=(
                    "\ud83d\udc3e  No sessions yet!\n\n"
                    "Click \u25b6 Start to begin your first study session.\n"
                    "Sessions are automatically saved when you pause."
                ),
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=TEXT_MUTED,
                justify="center",
            )
            self.empty_label.grid(row=0, column=0, pady=60)
            return

        for i, session in enumerate(self._sessions, 1):
            card = SessionCard(
                self.sessions_scroll,
                session=session,
                index=i,
                db=self.db,
                on_notes_saved=self._rebuild_history_table,
            )
            card.grid(row=i - 1, column=0, sticky="ew", padx=8, pady=6)

    def _rebuild_history_table(self):
        for widget in self._history_scroll.winfo_children():
            widget.destroy()

        all_sessions = self.db.get_all_sessions()

        if not all_sessions:
            ctk.CTkLabel(
                self._history_scroll,
                text="No sessions recorded yet.",
                text_color=TEXT_MUTED,
                font=ctk.CTkFont(family="Segoe UI", size=13),
            ).pack(pady=40)
            return

        col_defs = [
            ("Session", 60),
            ("Date", 110),
            ("Start", 90),
            ("End", 90),
            ("Duration", 100),
            ("Notes", 200),
            ("Remark", 180),
        ]
        header_row = ctk.CTkFrame(
            self._history_scroll, fg_color=SURFACE, corner_radius=8
        )
        header_row.pack(fill="x", padx=8, pady=(8, 2))

        for col_name, width in col_defs:
            ctk.CTkLabel(
                header_row,
                text=col_name,
                width=width,
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                text_color=ACCENT1,
                anchor="w",
            ).pack(side="left", padx=6, pady=8)

        for i, session in enumerate(all_sessions):
            row_bg = CARD_BG if i % 2 == 0 else SURFACE
            row = ctk.CTkFrame(self._history_scroll, fg_color=row_bg, corner_radius=6)
            row.pack(fill="x", padx=8, pady=1)

            values = [
                str(i + 1),
                session.date,
                session.start_time,
                session.end_time,
                session.duration_display(),
                (
                    session.notes[:30] + "\u2026"
                    if len(session.notes) > 30
                    else session.notes
                )
                or "\u2014",
                session.remark[:30] + "\u2026"
                if len(session.remark) > 30
                else session.remark,
            ]
            widths = [w for _, w in col_defs]

            for val, width in zip(values, widths):
                ctk.CTkLabel(
                    row,
                    text=val,
                    width=width,
                    font=ctk.CTkFont(family="Segoe UI", size=10),
                    text_color=TEXT_SECONDARY,
                    anchor="w",
                ).pack(side="left", padx=6, pady=6)

    def _update_summary(self):
        total = sum(s.duration_seconds for s in self._sessions)
        h = total // 3600
        m = (total % 3600) // 60
        self.sessions_count_lbl.configure(
            text=f"Sessions: {len(self._sessions)}   |   Total: {h}h {m:02d}m"
        )

    # ── Timer logic ───────────────────────────────────────────────────────────

    def _on_start(self):
        if self._running:
            return

        self._running = True
        self._day_started = True
        self._session_start_time = datetime.now().strftime("%H:%M:%S")

        self.status_label.configure(
            text="\u25cf Studying\u2026", text_color=BTN_START[0]
        )
        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")

        self._stop_event.clear()
        self._timer_thread = threading.Thread(target=self._tick, daemon=True)
        self._timer_thread.start()

    def _on_pause(self):
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        end_time = datetime.now().strftime("%H:%M:%S")
        elapsed = self._elapsed

        self.status_label.configure(
            text="\u23f8 Paused \u2014 session saved", text_color=BTN_PAUSE[0]
        )
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled")

        self._save_session(self._session_start_time, end_time, elapsed)

        self._total_elapsed_before += elapsed
        self._elapsed = 0

    def _on_reset(self):
        if self._running:
            self._running = False
            self._stop_event.set()

        self._elapsed = 0
        self._total_elapsed_before = 0
        self._update_timer_display(0)
        self.status_label.configure(text="\u25cf Ready to study", text_color=TEXT_MUTED)
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled")

    def _on_end_day(self):
        if self._running:
            self._on_pause()

        sessions = self.db.get_today_sessions()
        if not sessions:
            messagebox.showinfo(
                "No Sessions", "You haven't recorded any sessions today!"
            )
            return

        self._refresh_analytics(sessions)
        self.tabview.set("\u2728 Analytics")

    def _refresh_analytics(self, sessions):
        for widget in self.analytics_content.winfo_children():
            widget.destroy()
        self._analytics_chart_refs.clear()

        weekly = self.db.get_weekly_data()
        stats = compute_daily_stats(sessions)
        week_stats = compute_weekly_stats(weekly)

        self._analytics_stats = stats
        self._analytics_week_stats = week_stats
        self._analytics_sessions = sessions

        f = self.analytics_content

        title_frame = ctk.CTkFrame(
            f,
            fg_color=CARD_BG,
            corner_radius=CARD_RADIUS,
            border_color=ACCENT1,
            border_width=2,
        )
        title_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))

        ctk.CTkLabel(
            title_frame,
            text="\U0001f431  StudyFlow Daily Report",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=ACCENT1,
        ).pack(pady=(14, 2))

        ctk.CTkLabel(
            title_frame,
            text=f"\U0001f4c5  {date.today().strftime('%A, %B %d, %Y')}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_SECONDARY,
        ).pack(pady=(0, 14))

        summary_frame = ctk.CTkFrame(
            f,
            fg_color=SURFACE,
            corner_radius=CARD_RADIUS,
            border_color=ACCENT1,
            border_width=1,
        )
        summary_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=6)

        ctk.CTkLabel(
            summary_frame,
            text=f"{stats['summary_emoji']}  {stats['summary_title']}",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=ACCENT2,
        ).pack(pady=(14, 4))
        ctk.CTkLabel(
            summary_frame,
            text=stats.get("summary_body", ""),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_SECONDARY,
        ).pack(pady=(0, 14))

        stats_row = ctk.CTkFrame(f, fg_color="transparent")
        stats_row.grid(row=2, column=0, sticky="ew", padx=8, pady=6)

        stat_items = [
            ("\u23f1", "Total Study Time", stats["total_display"]),
            ("\U0001f4da", "Sessions", str(stats["session_count"])),
            ("\U0001f3c6", "Longest Session", stats["longest_display"]),
            ("\U0001f4ca", "Average Session", stats["avg_display"]),
        ]
        for emoji, label, value in stat_items:
            card = ctk.CTkFrame(
                stats_row,
                fg_color=CARD_BG,
                corner_radius=CARD_RADIUS,
                border_color=ACCENT1,
                border_width=1,
            )
            card.pack(side="left", expand=True, fill="both", padx=6)
            ctk.CTkLabel(card, text=emoji, font=ctk.CTkFont(size=24)).pack(pady=(14, 2))
            ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
                text_color=ACCENT1,
            ).pack()
            ctk.CTkLabel(
                card,
                text=label,
                font=ctk.CTkFont(family="Segoe UI", size=9),
                text_color=TEXT_MUTED,
            ).pack(pady=(0, 14))

        score_frame = ctk.CTkFrame(
            f,
            fg_color=CARD_BG,
            corner_radius=CARD_RADIUS,
            border_color=ACCENT2,
            border_width=1,
        )
        score_frame.grid(row=3, column=0, sticky="ew", padx=8, pady=6)
        score = stats["productivity_score"]
        ctk.CTkLabel(
            score_frame,
            text=f"\u26a1 Productivity Score: {score}/100",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=ACCENT2,
        ).pack(side="left", padx=PAD, pady=14)
        bar_frame = ctk.CTkFrame(
            score_frame, fg_color=BG_DARK, corner_radius=6, height=18
        )
        bar_frame.pack(side="left", fill="x", expand=True, padx=(0, PAD), pady=14)
        bar_fill = ctk.CTkFrame(
            bar_frame,
            fg_color=ACCENT2,
            corner_radius=6,
            height=18,
            width=int(4 * score),
        )
        bar_fill.pack(side="left", fill="y")

        bar_card = ctk.CTkFrame(
            f,
            fg_color=CARD_BG,
            corner_radius=CARD_RADIUS,
            border_color=ACCENT1,
            border_width=1,
        )
        bar_card.grid(row=4, column=0, sticky="ew", padx=8, pady=6)
        ctk.CTkLabel(
            bar_card,
            text="\U0001f4ca Study Hours per Session",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=ACCENT1,
        ).pack(pady=(12, 4))
        self._bar_chart_lbl = ctk.CTkLabel(
            bar_card, text="Loading chart\u2026", text_color=TEXT_MUTED
        )
        self._bar_chart_lbl.pack(padx=12, pady=(0, 12), fill="both", expand=True)

        pie_card = ctk.CTkFrame(
            f,
            fg_color=CARD_BG,
            corner_radius=CARD_RADIUS,
            border_color=ACCENT1,
            border_width=1,
        )
        pie_card.grid(row=5, column=0, sticky="ew", padx=8, pady=6)
        ctk.CTkLabel(
            pie_card,
            text="\U0001f370 Productivity Distribution",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=ACCENT1,
        ).pack(pady=(12, 4))
        self._pie_chart_lbl = ctk.CTkLabel(
            pie_card, text="Loading chart\u2026", text_color=TEXT_MUTED
        )
        self._pie_chart_lbl.pack(padx=12, pady=(0, 12), fill="both", expand=True)

        week_card = ctk.CTkFrame(
            f,
            fg_color=CARD_BG,
            corner_radius=CARD_RADIUS,
            border_color=ACCENT1,
            border_width=1,
        )
        week_card.grid(row=6, column=0, sticky="ew", padx=8, pady=6)
        ctk.CTkLabel(
            week_card,
            text="\U0001f4c5 Weekly Analytics",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=ACCENT1,
        ).pack(pady=(12, 4))

        week_stats_row = ctk.CTkFrame(week_card, fg_color="transparent")
        week_stats_row.pack(fill="x", padx=PAD, pady=(0, 8))
        week_items = [
            ("Total Hours This Week", f"{week_stats['total_hours']:.1f}h"),
            ("Avg Daily Hours", f"{week_stats['avg_daily_hours']:.1f}h"),
            ("Best Day", week_stats["best_day"]),
            ("Worst Day", week_stats["worst_day"]),
        ]
        for label, val in week_items:
            wc = ctk.CTkFrame(week_stats_row, fg_color=SURFACE, corner_radius=8)
            wc.pack(side="left", expand=True, fill="both", padx=4)
            ctk.CTkLabel(
                wc,
                text=val,
                font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
                text_color=ACCENT3,
            ).pack(pady=(8, 2))
            ctk.CTkLabel(
                wc,
                text=label,
                font=ctk.CTkFont(family="Segoe UI", size=9),
                text_color=TEXT_MUTED,
            ).pack(pady=(0, 8))

        self._week_chart_lbl = ctk.CTkLabel(
            week_card, text="Loading weekly chart\u2026", text_color=TEXT_MUTED
        )
        self._week_chart_lbl.pack(padx=12, pady=(0, 12), fill="both", expand=True)

        export_frame = ctk.CTkFrame(f, fg_color="transparent")
        export_frame.grid(row=7, column=0, sticky="ew", padx=8, pady=(8, 16))

        ctk.CTkButton(
            export_frame,
            text="\U0001f4c4 Export PDF Report",
            fg_color=ACCENT2,
            hover_color=BTN_END[1],
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=40,
            corner_radius=BTN_RADIUS,
            command=self._export_pdf,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            export_frame,
            text="\U0001f4ca Export Excel Report",
            fg_color=ACCENT3,
            hover_color="#9B1B5E",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=40,
            corner_radius=BTN_RADIUS,
            command=self._export_excel,
        ).pack(side="left")

        ctk.CTkButton(
            export_frame,
            text="\U0001f4dd Open in New Window",
            fg_color=SURFACE,
            hover_color=CARD_BORDER,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=40,
            corner_radius=BTN_RADIUS,
            command=self._open_analytics_window,
        ).pack(side="right")

        threading.Thread(target=self._load_analytics_charts, daemon=True).start()

    def _load_analytics_charts(self):
        sessions = self._analytics_sessions

        if sessions:
            bar_buf = generate_bar_chart(sessions)
            pie_buf = generate_pie_chart(sessions)
            bar_img = ImageTk.PhotoImage(Image.open(bar_buf))
            pie_img = ImageTk.PhotoImage(Image.open(pie_buf))
            self.after(0, lambda: self._set_analytics_chart("bar", bar_img))
            self.after(0, lambda: self._set_analytics_chart("pie", pie_img))

        weekly = self.db.get_weekly_data()
        if weekly:
            week_buf = generate_weekly_chart(weekly)
            week_img = ImageTk.PhotoImage(Image.open(week_buf))
            self.after(0, lambda: self._set_analytics_chart("week", week_img))

    def _set_analytics_chart(self, key: str, img):
        lbl_map = {
            "bar": "_bar_chart_lbl",
            "pie": "_pie_chart_lbl",
            "week": "_week_chart_lbl",
        }
        attr = lbl_map.get(key)
        if attr and hasattr(self, attr):
            lbl = getattr(self, attr)
            lbl.configure(image=img, text="")
            self._analytics_chart_refs[key] = img

    def _export_pdf(self):
        try:
            from reports.generator import generate_pdf_report

            bar_buf = (
                generate_bar_chart(self._analytics_sessions)
                if self._analytics_sessions
                else None
            )
            pie_buf = (
                generate_pie_chart(self._analytics_sessions)
                if self._analytics_sessions
                else None
            )
            path = generate_pdf_report(
                self._analytics_sessions, self._analytics_stats, bar_buf, pie_buf
            )
            if path.startswith("ERROR"):
                messagebox.showerror("Export Error", path)
            else:
                messagebox.showinfo("PDF Exported", f"Saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _export_excel(self):
        try:
            from reports.generator import generate_excel_report

            path = generate_excel_report(
                self._analytics_sessions, self._analytics_stats
            )
            if path.startswith("ERROR"):
                messagebox.showerror("Export Error", path)
            else:
                messagebox.showinfo("Excel Exported", f"Saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _open_analytics_window(self):
        if self._analytics_sessions:
            weekly = self.db.get_weekly_data()
            win = AnalyticsWindow(
                self, sessions=self._analytics_sessions, weekly_data=weekly
            )
            win.after(100, win.lift)

    # ── Timer sub ─────────────────────────────────────────────────────────────

    def _tick(self):
        while not self._stop_event.is_set() and self._running:
            time.sleep(1)
            if self._running:
                self._elapsed += 1
                display = self._total_elapsed_before + self._elapsed
                self.after(0, lambda d=display: self._update_timer_display(d))

    def _update_timer_display(self, seconds: int):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        self.timer_label.configure(text=f"{h:02d}:{m:02d}:{s:02d}")

    def _save_session(self, start: str, end: str, duration_secs: int):
        from analytics.engine import get_remark

        h = duration_secs // 3600
        m = (duration_secs % 3600) // 60
        s = duration_secs % 60
        duration_str = f"{h:02d}:{m:02d}:{s:02d}"

        remark = get_remark(duration_secs)

        session = StudySession(
            date=date.today().isoformat(),
            start_time=start,
            end_time=end,
            duration=duration_str,
            duration_seconds=duration_secs,
            notes="",
            remark=remark,
        )
        session.id = self.db.save_session(session)
        self._sessions.append(session)

        self._rebuild_session_cards()
        self._rebuild_history_table()
        self._update_summary()

    # ── Misc ──────────────────────────────────────────────────────────────────

    def _toggle_history(self):
        self.tabview.set("History")

    def _update_clock(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.title(f"\U0001f431 StudyFlow  \u2014  {now}")
        self.after(1000, self._update_clock)

    def on_close(self):
        if self._running:
            answer = messagebox.askyesno(
                "Session Active",
                "You have an active study session. Save it before closing?",
            )
            if answer:
                self._on_pause()
        self._stop_event.set()
        self.destroy()
