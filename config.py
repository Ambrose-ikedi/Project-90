import os
from pathlib import Path

APP_NAME = "Project 90"
TAGLINE = "Recover. Learn. Grow."
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = os.getenv("PROJECT90_DB_PATH", str(DATA_DIR / "project90.db"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
MAX_CHAT_HISTORY = int(os.getenv("MAX_CHAT_HISTORY", "12"))
