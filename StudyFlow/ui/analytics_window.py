import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import io
import threading

from ui.theme import *
from ui.widgets import create_cat_button, CAT_BG_ANALYTICS
from models.session import StudySession
from analytics.engine import (
    compute_daily_stats,
    compute_weekly_stats,
    generate_bar_chart,
    generate_pie_chart,
    generate_weekly_chart,
)
from typing import List, Dict


class AnalyticsWindow(ctk.CTkToplevel):
    def __init__(
        self, master, sessions: List[StudySession], weekly_data: List[Dict], **kwargs
    ):
        super().__init__(master, **kwargs)
        self.title("\U0001f431 StudyFlow \u2013 Daily Report")
        self.geometry("1000x800")
        self.resizable(True, True)
        self.configure(fg_color=BG_MID)
        self.grab_set()

        self.sessions = sessions
        self.weekly_data = weekly_data
        self.stats = compute_daily_stats(sessions)
        self.week_stats = compute_weekly_stats(weekly_data)

        self._chart_refs = {}
        self._build()

    def _build(self):
        self._bg_photo = None
        canvas = tk.Canvas(self, bg=BG_MID, highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(self, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _draw_window_bg(event=None):
            w = self.winfo_width()
            h = self.winfo_height()
            if w < 4 or h < 4:
                return
            try:
                base = Image.open(CAT_BG_ANALYTICS).convert("RGBA")
                base = base.resize((w, h), Image.Resampling.LANCZOS)
                overlay = Image.new("RGBA", (w, h), (255, 200, 220, 145))
                img = Image.alpha_composite(base, overlay)
                self._bg_photo = ImageTk.PhotoImage(img)
                canvas.delete("bg")
                canvas.create_image(0, 0, anchor="nw", image=self._bg_photo, tags="bg")
                canvas.tag_lower("bg")
            except OSError:
                pass

        self.bind("<Configure>", _draw_window_bg)
        self.after(80, _draw_window_bg)

        self.scroll_frame = ctk.CTkFrame(canvas, fg_color="transparent")
        self.scroll_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw", width=980)

        def _on_mousewheel(event):
            if canvas.winfo_exists():
                canvas.yview_scroll(-1 * (event.delta // 120), "units")

        self.bind("<MouseWheel>", _on_mousewheel)
        self.scroll_frame.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw", width=980)
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"),
        )

        f = self.scroll_frame

        title_frame = ctk.CTkFrame(
            f,
            fg_color=CARD_BG,
            corner_radius=CARD_RADIUS,
            border_color=ACCENT1,
            border_width=2,
        )
        title_frame.pack(fill="x", padx=PAD, pady=(PAD, 8))

        ctk.CTkLabel(
            title_frame,
            text="\U0001f431  StudyFlow Daily Report",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=ACCENT1,
        ).pack(pady=(14, 2))

        from datetime import date

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
        summary_frame.pack(fill="x", padx=PAD, pady=8)

        ctk.CTkLabel(
            summary_frame,
            text=f"{self.stats['summary_emoji']}  {self.stats['summary_title']}",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=ACCENT2,
        ).pack(pady=(14, 4))
        ctk.CTkLabel(
            summary_frame,
            text=self.stats.get("summary_body", ""),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_SECONDARY,
        ).pack(pady=(0, 14))

        stats_row = ctk.CTkFrame(f, fg_color="transparent")
        stats_row.pack(fill="x", padx=PAD, pady=8)

        stat_items = [
            ("\u23f1", "Total Study Time", self.stats["total_display"]),
            ("\U0001f4da", "Sessions", str(self.stats["session_count"])),
            ("\U0001f3c6", "Longest Session", self.stats["longest_display"]),
            ("\U0001f4ca", "Average Session", self.stats["avg_display"]),
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
        score_frame.pack(fill="x", padx=PAD, pady=8)
        score = self.stats["productivity_score"]
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

        # ── Charts: stacked vertically for maximum space ──────────────────────

        self._chart_labels = {}

        bar_card = ctk.CTkFrame(
            f,
            fg_color=CARD_BG,
            corner_radius=CARD_RADIUS,
            border_color=ACCENT1,
            border_width=1,
        )
        bar_card.pack(fill="x", padx=PAD, pady=8)
        ctk.CTkLabel(
            bar_card,
            text="\U0001f4ca Study Hours per Session",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=ACCENT1,
        ).pack(pady=(12, 4))
        self._chart_labels["bar"] = ctk.CTkLabel(
            bar_card, text="Loading chart\u2026", text_color=TEXT_MUTED
        )
        self._chart_labels["bar"].pack(padx=12, pady=(0, 12), fill="both", expand=True)

        pie_card = ctk.CTkFrame(
            f,
            fg_color=CARD_BG,
            corner_radius=CARD_RADIUS,
            border_color=ACCENT1,
            border_width=1,
        )
        pie_card.pack(fill="x", padx=PAD, pady=8)
        ctk.CTkLabel(
            pie_card,
            text="\U0001f370 Productivity Distribution",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=ACCENT1,
        ).pack(pady=(12, 4))
        self._chart_labels["pie"] = ctk.CTkLabel(
            pie_card, text="Loading chart\u2026", text_color=TEXT_MUTED
        )
        self._chart_labels["pie"].pack(padx=12, pady=(0, 12), fill="both", expand=True)

        week_card = ctk.CTkFrame(
            f,
            fg_color=CARD_BG,
            corner_radius=CARD_RADIUS,
            border_color=ACCENT1,
            border_width=1,
        )
        week_card.pack(fill="x", padx=PAD, pady=8)
        ctk.CTkLabel(
            week_card,
            text="\U0001f4c5 Weekly Analytics",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=ACCENT1,
        ).pack(pady=(12, 4))

        week_stats_row = ctk.CTkFrame(week_card, fg_color="transparent")
        week_stats_row.pack(fill="x", padx=PAD, pady=(0, 8))
        week_items = [
            ("Total Hours This Week", f"{self.week_stats['total_hours']:.1f}h"),
            ("Avg Daily Hours", f"{self.week_stats['avg_daily_hours']:.1f}h"),
            ("Best Day", self.week_stats["best_day"]),
            ("Worst Day", self.week_stats["worst_day"]),
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

        self._chart_labels["week"] = ctk.CTkLabel(
            week_card, text="Loading weekly chart\u2026", text_color=TEXT_MUTED
        )
        self._chart_labels["week"].pack(padx=12, pady=(0, 12), fill="both", expand=True)

        export_frame = ctk.CTkFrame(f, fg_color="transparent")
        export_frame.pack(fill="x", padx=PAD, pady=(8, PAD))

        create_cat_button(
            export_frame,
            "\U0001f4c4 Export PDF Report",
            BTN_EXPORT_PDF[0],
            BTN_EXPORT_PDF[1],
            command=self._export_pdf,
            height=40,
            font_size=12,
            pack_kwargs={"side": "left", "padx": (0, 8)},
        )

        create_cat_button(
            export_frame,
            "\U0001f4ca Export Excel Report",
            BTN_EXPORT_XLS[0],
            BTN_EXPORT_XLS[1],
            command=self._export_excel,
            height=40,
            font_size=12,
            pack_kwargs={"side": "left"},
        )

        create_cat_button(
            export_frame,
            "\u2715 Close",
            BTN_SECONDARY[0],
            BTN_SECONDARY[1],
            command=self.destroy,
            text_color=TEXT_PRIMARY,
            height=40,
            font_size=12,
            bold=False,
            pack_kwargs={"side": "right"},
        )

        threading.Thread(target=self._load_charts, daemon=True).start()

    def _load_charts(self):
        if self.sessions:
            bar_buf = generate_bar_chart(self.sessions)
            pie_buf = generate_pie_chart(self.sessions)
            bar_img = ImageTk.PhotoImage(Image.open(bar_buf))
            pie_img = ImageTk.PhotoImage(Image.open(pie_buf))
            self.after(0, lambda: self._set_chart("bar", bar_img))
            self.after(0, lambda: self._set_chart("pie", pie_img))

        if self.weekly_data:
            week_buf = generate_weekly_chart(self.weekly_data)
            week_img = ImageTk.PhotoImage(Image.open(week_buf))
            self.after(0, lambda: self._set_chart("week", week_img))

    def _set_chart(self, key: str, img):
        lbl = self._chart_labels.get(key)
        if lbl:
            lbl.configure(image=img, text="")
            self._chart_refs[key] = img

    def _export_pdf(self):
        try:
            from reports.generator import generate_pdf_report

            bar_buf = generate_bar_chart(self.sessions) if self.sessions else None
            pie_buf = generate_pie_chart(self.sessions) if self.sessions else None
            path = generate_pdf_report(self.sessions, self.stats, bar_buf, pie_buf)
            if path.startswith("ERROR"):
                messagebox.showerror("Export Error", path, parent=self)
            else:
                messagebox.showinfo("PDF Exported", f"Saved to:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _export_excel(self):
        try:
            from reports.generator import generate_excel_report

            path = generate_excel_report(self.sessions, self.stats)
            if path.startswith("ERROR"):
                messagebox.showerror("Export Error", path, parent=self)
            else:
                messagebox.showinfo("Excel Exported", f"Saved to:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
