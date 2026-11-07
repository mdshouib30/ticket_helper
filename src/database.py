import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = "tickets.db"


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create the tickets table if it does not exist yet."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                message TEXT NOT NULL,
                sorted_by TEXT NOT NULL,
                category TEXT NOT NULL,
                urgency TEXT NOT NULL,
                reason TEXT NOT NULL,
                reply TEXT NOT NULL,
                reply_source TEXT NOT NULL,
                action TEXT NOT NULL,
                why TEXT NOT NULL
            )
            """
        )


def save_ticket(data: dict) -> int:
    """Save one processed ticket and return its new id."""
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tickets
            (created_at, message, sorted_by, category, urgency, reason,
             reply, reply_source, action, why)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                data["message"],
                data["sorted_by"],
                data["category"],
                data["urgency"],
                data["reason"],
                data["reply"],
                data["reply_source"],
                data["action"],
                data["why"],
            ),
        )
        return cursor.lastrowid


def get_ticket(ticket_id: int):
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
        ).fetchone()
    return dict(row) if row else None


def list_tickets(limit: int = 50) -> list:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM tickets ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]


def stats() -> dict:
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        to_human = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE action = 'SEND TO HUMAN'"
        ).fetchone()[0]
        by_rules = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE sorted_by = 'RULES'"
        ).fetchone()[0]
    return {
        "total": total,
        "sent_to_human": to_human,
        "sorted_by_rules": by_rules,
    }
