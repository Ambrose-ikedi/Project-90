import re
import sqlite3
from pathlib import Path
from config import DB_PATH, DATA_DIR


def get_connection():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate_usernames(conn):
    """Add username login support without discarding existing user records."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "username" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN username TEXT")

    rows = conn.execute(
        "SELECT id, email, username FROM users ORDER BY id"
    ).fetchall()
    used = {
        row["username"].lower()
        for row in rows
        if row["username"] and row["username"].strip()
    }
    for row in rows:
        if row["username"] and row["username"].strip():
            continue
        email = row["email"] or ""
        base = email.split("@", 1)[0]
        base = re.sub(r"[^A-Za-z0-9_.-]", "", base)[:24]
        if len(base) < 3:
            base = f"user{row['id']}"
        candidate = base
        suffix = 1
        while candidate.lower() in used:
            tail = str(suffix)
            candidate = f"{base[:24-len(tail)]}{tail}"
            suffix += 1
        conn.execute("UPDATE users SET username=? WHERE id=?", (candidate, row["id"]))
        used.add(candidate.lower())

    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username COLLATE NOCASE)"
    )


def init_db():
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.executescript(schema)
        migrate_usernames(conn)
        conn.commit()
    from utils.authentication import ensure_initial_admin
    ensure_initial_admin()
