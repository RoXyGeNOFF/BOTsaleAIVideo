
import sqlite3
from datetime import datetime, timedelta

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        is_premium INTEGER DEFAULT 0,
        expires_at TEXT,
        free_generations INTEGER DEFAULT 3,
        videos_left INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

def get_user(telegram_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT telegram_id, is_premium, expires_at, free_generations, videos_left FROM users WHERE telegram_id = ?", (telegram_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "telegram_id": row[0],
            "is_premium": bool(row[1]),
            "expires_at": row[2],
            "free_generations": row[3],
            "videos_left": row[4]
        }
    return None

def add_user(telegram_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (telegram_id, free_generations) VALUES (?, 3)", (telegram_id,))
    conn.commit()
    conn.close()

def update_subscription(telegram_id, days=30):
    expires = datetime.now() + timedelta(days=days)
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        "UPDATE users SET is_premium = 1, expires_at = ? WHERE telegram_id = ?",
        (expires.isoformat(), telegram_id)
    )
    conn.commit()
    conn.close()

def remove_premium(telegram_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET is_premium = 0, expires_at = NULL WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()

def decrement_free_generation(telegram_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET free_generations = free_generations - 1 WHERE telegram_id = ? AND free_generations > 0", (telegram_id,))
    conn.commit()
    conn.close()

def get_users_with_expiring_premium(days=3):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    from datetime import datetime, timedelta
    now = datetime.now()
    soon = now + timedelta(days=days)
    c.execute("SELECT telegram_id, expires_at FROM users WHERE is_premium = 1 AND expires_at IS NOT NULL")
    users = []
    for row in c.fetchall():
        expires = datetime.fromisoformat(row[1])
        if now < expires <= soon:
            users.append(row[0])
    conn.close()
    return users

def get_all_users():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT telegram_id, is_premium, expires_at FROM users")
    users = [
        {"telegram_id": row[0], "is_premium": bool(row[1]), "expires_at": row[2]} for row in c.fetchall()
    ]
    conn.close()
    return users

def add_videos(telegram_id, count):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET videos_left = videos_left + ? WHERE telegram_id = ?", (count, telegram_id))
    conn.commit()
    conn.close()

def decrement_video(telegram_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET videos_left = videos_left - 1 WHERE telegram_id = ? AND videos_left > 0", (telegram_id,))
    conn.commit()
    conn.close()
