# 🐱 StudyFlow

> Your purr-fect study session tracker — cat-themed, glassmorphism-inspired, powered by Python.

---

## Features

- ⏱ **Live Stopwatch** — HH:MM:SS with Start / Pause / Reset / End Day
- 📋 **Auto-Lap on Pause** — Sessions saved automatically every time you pause
- ✏️ **Editable Notes** — Click to add notes to each session card
- 🔥 **Motivational Remarks** — Static tier-based remarks based on session length
- 📊 **Daily Analytics** — Total time, sessions, longest, average, productivity score
- 📅 **Weekly Analytics** — 7-day overview with best/worst day
- 📈 **Charts** — Bar chart (hours per session) + Pie chart (productivity distribution)
- 💾 **SQLite Storage** — All data persists between app restarts
- 📄 **PDF + Excel Export** — Beautiful reports saved to your home folder
- 🐾 **Cat Theme** — Purple glassmorphism with cat ASCII art & paw prints

---

## Tech Stack

| Component | Library |
|-----------|---------|
| UI | CustomTkinter |
| Database | SQLite (built-in) |
| Charts | Matplotlib |
| PDF Export | ReportLab |
| Excel Export | OpenPyXL |
| Data | Pandas |

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch the app
python main.py
```

> **Python 3.10+** recommended.

---

## Project Structure

```
StudyFlow/
├── main.py                  # Entry point
├── requirements.txt
├── studyflow.db             # Created on first run
├── models/
│   └── session.py           # StudySession dataclass
├── database/
│   └── db_manager.py        # SQLite CRUD operations
├── analytics/
│   └── engine.py            # Stats, remarks, chart generation
├── reports/
│   └── generator.py         # PDF and Excel export
└── ui/
    ├── theme.py             # Colour palette & font constants
    ├── main_window.py       # Main app window (Controller)
    ├── session_card.py      # Individual session card widget
    └── analytics_window.py  # Daily report popup
```

---

## Usage

1. Click **▶ Start** to begin a study session
2. Click **⏸ Pause** when you take a break — a session card is automatically created
3. Add notes directly in the card and they save automatically
4. Click **▶ Start** again to continue
5. Click **🏁 End Day** to see your full daily analytics and export reports

---

## Productivity Remark Tiers

| Duration | Tier | Example |
|----------|------|---------|
| ≥ 4 hours | 🔥 Outstanding | "Amazing focus. You're building serious momentum." |
| 2–4 hours | 💪 Good | "Nice effort. Keep pushing." |
| < 2 hours | 😤 Needs Focus | "Girl, seriously? Only this much? Lock in." |

---

## Productivity Score Formula

```
score = min(100, total_hours × 10)
```

8 hours = 80/100 · 10+ hours = 100/100

---

Made with 🐾 and Python
