from datetime import datetime
from .database import get_connection


def start_task(task: str):
    conn = get_connection()

    running = conn.execute("SELECT 1 FROM sessions WHERE end_time IS NULL").fetchone()

    if running:
        raise RuntimeError("A task is already running")

    conn.execute(
        "INSERT INTO sessions (task, start_time) VALUES (?, ?)",
        (task, datetime.now().isoformat()),
    )

    conn.commit()


def stop_task():
    conn = get_connection()

    row = conn.execute(
        "SELECT id, task, start_time FROM sessions WHERE end_time IS NULL"
    ).fetchone()

    if not row:
        raise RuntimeError("No running task")

    session_id, task, start_time = row

    end_time = datetime.now()
    conn.execute(
        "UPDATE sessions SET end_time = ? WHERE id = ?",
        (end_time.isoformat(), session_id),
    )
    conn.commit()

    duration = end_time - datetime.fromisoformat(start_time)
    return task, duration


def get_summary():
    conn = get_connection()

    rows = conn.execute(
        "SELECT task, start_time, end_time FROM sessions WHERE end_time IS NOT NULL"
    ).fetchall()

    summary = {}

    for task, start, end in rows:
        duration = datetime.fromisoformat(end) - datetime.fromisoformat(start)
        summary[task] = summary.get(task, duration * 0) + duration

    return summary
