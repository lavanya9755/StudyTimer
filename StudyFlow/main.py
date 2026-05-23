"""
StudyFlow - Entry Point
🐱 Your purr-fect study companion.

Run: python main.py
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

import customtkinter as ctk
from ui.main_window import StudyFlowApp


def main():
    """Launch StudyFlow."""
    ctk.set_appearance_mode("light")

    app = StudyFlowApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()


if __name__ == "__main__":
    main()
