"""
StudyFlow - Database Manager
Handles all SQLite operations for persistent storage.
"""

import sqlite3
import os
from datetime import datetime, date
from typing import List, Optional
from models.session import StudySession


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "studyflow.db")


class DatabaseManager:
    """Manages SQLite database operations for StudyFlow."""

    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database tables if they don't exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS study_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    duration TEXT NOT NULL,
                    duration_seconds INTEGER NOT NULL DEFAULT 0,
                    notes TEXT DEFAULT '',
                    remark TEXT DEFAULT ''
                )
            """)
            conn.commit()

    def save_session(self, session: StudySession) -> int:
        """Save a new session and return its ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO study_sessions (date, start_time, end_time, duration, duration_seconds, notes, remark)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session.date,
                session.start_time,
                session.end_time,
                session.duration,
                session.duration_seconds,
                session.notes,
                session.remark,
            ))
            conn.commit()
            return cursor.lastrowid

    def update_notes(self, session_id: int, notes: str):
        """Update notes for a specific session."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE study_sessions SET notes = ? WHERE id = ?",
                (notes, session_id)
            )
            conn.commit()

    def get_sessions_by_date(self, target_date: str) -> List[StudySession]:
        """Get all sessions for a specific date."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM study_sessions WHERE date = ? ORDER BY id",
                (target_date,)
            ).fetchall()
            return [StudySession(
                id=r["id"], date=r["date"], start_time=r["start_time"],
                end_time=r["end_time"], duration=r["duration"],
                duration_seconds=r["duration_seconds"], notes=r["notes"],
                remark=r["remark"]
            ) for r in rows]

    def get_today_sessions(self) -> List[StudySession]:
        """Get all sessions for today."""
        today = date.today().isoformat()
        return self.get_sessions_by_date(today)

    def get_all_sessions(self) -> List[StudySession]:
        """Get all sessions ever recorded."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM study_sessions ORDER BY date DESC, id DESC"
            ).fetchall()
            return [StudySession(
                id=r["id"], date=r["date"], start_time=r["start_time"],
                end_time=r["end_time"], duration=r["duration"],
                duration_seconds=r["duration_seconds"], notes=r["notes"],
                remark=r["remark"]
            ) for r in rows]

    def get_weekly_data(self) -> List[dict]:
        """Get aggregated study data for the past 7 days."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT date,
                       SUM(duration_seconds) as total_seconds,
                       COUNT(*) as session_count
                FROM study_sessions
                WHERE date >= date('now', '-6 days')
                GROUP BY date
                ORDER BY date
            """).fetchall()
            return [{"date": r["date"], "total_seconds": r["total_seconds"],
                     "session_count": r["session_count"]} for r in rows]

    def delete_session(self, session_id: int):
        """Delete a session by ID."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM study_sessions WHERE id = ?", (session_id,))
            conn.commit()
