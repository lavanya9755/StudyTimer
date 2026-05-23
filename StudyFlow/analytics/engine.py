"""
StudyFlow - Analytics Engine
Computes study statistics and generates charts.
"""

import random
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from typing import List, Dict, Tuple
from models.session import StudySession
from io import BytesIO


# ── Remark tiers ──────────────────────────────────────────────────────────────

TIER1_REMARKS = [
    "🔥 Outstanding! Looks like a highly productive session.",
    "🚀 Amazing focus. You're building serious momentum.",
    "⭐ Excellent work. Consistency like this creates success.",
]

TIER2_REMARKS = [
    "💪 Nice effort. Keep pushing.",
    "📚 Good session. One more study block could make today great.",
    "✨ You're progressing well. Stay consistent.",
]

TIER3_REMARKS = [
    "😤 Girl, seriously? Only this much? Lock in.",
    "☕ Take a break and come back stronger.",
    "🎯 Focus mode needed. The next session is yours.",
]


def get_remark(duration_seconds: int) -> str:
    """Return a motivational remark based on session duration."""
    hours = duration_seconds / 3600
    if hours >= 4:
        return random.choice(TIER1_REMARKS)
    elif hours >= 2:
        return random.choice(TIER2_REMARKS)
    else:
        return random.choice(TIER3_REMARKS)


def get_remark_category(duration_seconds: int) -> str:
    """Return category label for pie chart."""
    hours = duration_seconds / 3600
    if hours >= 4:
        return "Excellent"
    elif hours >= 2:
        return "Good"
    else:
        return "Needs Focus"


# ── Daily stats ────────────────────────────────────────────────────────────────


def compute_daily_stats(sessions: List[StudySession]) -> Dict:
    """Compute daily summary statistics."""
    if not sessions:
        return {
            "total_seconds": 0,
            "total_display": "0h 00m",
            "session_count": 0,
            "longest_seconds": 0,
            "longest_display": "0h 00m",
            "avg_display": "0h 00m",
            "productivity_score": 0,
            "summary_message": "",
            "summary_emoji": "🌱",
            "summary_title": "No sessions yet",
        }

    total = sum(s.duration_seconds for s in sessions)
    longest = max(s.duration_seconds for s in sessions)
    avg = total // len(sessions)
    total_hours = total / 3600

    score = min(100, int(total_hours * 10))

    if total_hours >= 8:
        emoji, title, body = (
            "🏆",
            "Champion Day!",
            (
                f"You studied for {total_hours:.1f}+ hours today.\nKeep this momentum going."
            ),
        )
    elif total_hours >= 4:
        emoji, title, body = "🎯", "Productive Day!", ("Solid progress made today.")
    else:
        emoji, title, body = (
            "🌱",
            "Tomorrow is a New Opportunity",
            ("Rest well and come back stronger."),
        )

    def fmt(secs):
        h = secs // 3600
        m = (secs % 3600) // 60
        return f"{h}h {m:02d}m"

    return {
        "total_seconds": total,
        "total_display": fmt(total),
        "session_count": len(sessions),
        "longest_seconds": longest,
        "longest_display": fmt(longest),
        "avg_display": fmt(avg),
        "productivity_score": score,
        "summary_emoji": emoji,
        "summary_title": title,
        "summary_body": body,
    }


def compute_weekly_stats(weekly_data: List[Dict]) -> Dict:
    """Compute weekly summary statistics."""
    if not weekly_data:
        return {
            "total_hours": 0,
            "avg_daily_hours": 0,
            "best_day": "N/A",
            "worst_day": "N/A",
        }

    total_secs = sum(d["total_seconds"] for d in weekly_data)
    avg_secs = total_secs / max(len(weekly_data), 1)
    best = max(weekly_data, key=lambda d: d["total_seconds"])
    worst = min(weekly_data, key=lambda d: d["total_seconds"])

    return {
        "total_hours": total_secs / 3600,
        "avg_daily_hours": avg_secs / 3600,
        "best_day": best["date"],
        "worst_day": worst["date"],
    }


# ── Chart generation ───────────────────────────────────────────────────────────

CAT_PALETTE = {
    "bg": "#FFF0F5",  # lavender blush
    "card": "#FFE8EF",  # soft pink
    "accent1": "#FF69B4",  # hot pink
    "accent2": "#DB7093",  # pale violet red
    "accent3": "#C71585",  # medium violet red
    "text": "#4A0E4E",  # dark purple
    "muted": "#C080A0",  # muted pink
}


def _apply_cat_style(fig, ax):
    """Apply the cat/purple theme to a matplotlib figure."""
    fig.patch.set_facecolor(CAT_PALETTE["bg"])
    ax.set_facecolor(CAT_PALETTE["card"])
    ax.tick_params(colors=CAT_PALETTE["text"], labelsize=9)
    ax.xaxis.label.set_color(CAT_PALETTE["text"])
    ax.yaxis.label.set_color(CAT_PALETTE["text"])
    ax.title.set_color(CAT_PALETTE["accent1"])
    for spine in ax.spines.values():
        spine.set_edgecolor(CAT_PALETTE["muted"])


def generate_bar_chart(sessions: List[StudySession]) -> BytesIO:
    """Generate a bar chart of study hours per session."""
    fig, ax = plt.subplots(figsize=(7, 3.5), dpi=100)
    _apply_cat_style(fig, ax)

    labels = [f"S{i + 1}" for i in range(len(sessions))]
    hours = [s.duration_seconds / 3600 for s in sessions]

    colors = [CAT_PALETTE["accent1"], CAT_PALETTE["accent2"], CAT_PALETTE["accent3"]]
    bar_colors = [colors[i % len(colors)] for i in range(len(sessions))]

    bars = ax.bar(
        labels,
        hours,
        color=bar_colors,
        edgecolor=CAT_PALETTE["muted"],
        linewidth=0.5,
        width=0.5,
    )

    for bar, h in zip(bars, hours):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.05,
            f"{h:.1f}h",
            ha="center",
            va="bottom",
            color=CAT_PALETTE["text"],
            fontsize=8,
        )

    ax.set_title("📊 Study Hours per Session", pad=10, fontsize=11, fontweight="bold")
    ax.set_ylabel("Hours", fontsize=9)
    ax.set_xlabel("Session", fontsize=9)
    ax.set_ylim(0, max(hours + [1]) * 1.25)
    ax.grid(axis="y", color=CAT_PALETTE["muted"], alpha=0.3, linestyle="--")

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(
        buf, format="png", bbox_inches="tight", facecolor=CAT_PALETTE["bg"], dpi=100
    )
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_pie_chart(sessions: List[StudySession]) -> BytesIO:
    """Generate a productivity distribution pie chart."""
    categories = {"Excellent": 0, "Good": 0, "Needs Focus": 0}
    for s in sessions:
        cat = get_remark_category(s.duration_seconds)
        categories[cat] += 1

    labels = [k for k, v in categories.items() if v > 0]
    sizes = [v for v in categories.values() if v > 0]
    pie_colors = [
        CAT_PALETTE["accent1"],
        CAT_PALETTE["accent2"],
        CAT_PALETTE["accent3"],
    ]
    used_colors = pie_colors[: len(labels)]

    fig, ax = plt.subplots(figsize=(5, 3.5), dpi=100)
    fig.patch.set_facecolor(CAT_PALETTE["bg"])
    ax.set_facecolor(CAT_PALETTE["bg"])

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=used_colors,
        autopct="%1.0f%%",
        startangle=140,
        wedgeprops={"edgecolor": CAT_PALETTE["bg"], "linewidth": 2},
        textprops={"color": CAT_PALETTE["text"], "fontsize": 9},
    )
    for at in autotexts:
        at.set_color(CAT_PALETTE["bg"])
        at.set_fontweight("bold")

    ax.set_title(
        "🍰 Productivity Distribution",
        pad=10,
        fontsize=11,
        fontweight="bold",
        color=CAT_PALETTE["accent1"],
    )

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(
        buf, format="png", bbox_inches="tight", facecolor=CAT_PALETTE["bg"], dpi=100
    )
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_weekly_chart(weekly_data: List[Dict]) -> BytesIO:
    """Generate a weekly study hours bar chart."""
    fig, ax = plt.subplots(figsize=(8, 3.5), dpi=100)
    _apply_cat_style(fig, ax)

    from datetime import datetime

    dates = [d["date"] for d in weekly_data]
    hours = [d["total_seconds"] / 3600 for d in weekly_data]
    short_dates = [
        datetime.strptime(d, "%Y-%m-%d").strftime("%a\n%m/%d") for d in dates
    ]

    bars = ax.bar(
        short_dates,
        hours,
        color=CAT_PALETTE["accent1"],
        edgecolor=CAT_PALETTE["muted"],
        linewidth=0.5,
        width=0.5,
    )

    for bar, h in zip(bars, hours):
        if h > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.05,
                f"{h:.1f}h",
                ha="center",
                va="bottom",
                color=CAT_PALETTE["text"],
                fontsize=8,
            )

    ax.set_title("📅 Weekly Study Hours", pad=10, fontsize=11, fontweight="bold")
    ax.set_ylabel("Hours", fontsize=9)
    ax.set_ylim(0, max(hours + [1]) * 1.3)
    ax.grid(axis="y", color=CAT_PALETTE["muted"], alpha=0.3, linestyle="--")

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(
        buf, format="png", bbox_inches="tight", facecolor=CAT_PALETTE["bg"], dpi=100
    )
    plt.close(fig)
    buf.seek(0)
    return buf
