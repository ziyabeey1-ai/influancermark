"""
Influencer Hunter - Database Module
SQLite tabanlı influencer havuzu yönetimi
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "influencer_pool.db"


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Veritabanı tablolarını oluştur"""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS influencers (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT UNIQUE NOT NULL,
            full_name       TEXT,
            bio             TEXT,
            followers       INTEGER DEFAULT 0,
            following       INTEGER DEFAULT 0,
            post_count      INTEGER DEFAULT 0,
            engagement_rate REAL DEFAULT 0.0,
            email           TEXT,
            profile_url     TEXT,
            website         TEXT,
            niche_tags      TEXT,           -- JSON array
            ai_score        REAL DEFAULT 0.0,
            ai_summary      TEXT,
            status          TEXT DEFAULT 'discovered',
            -- discovered → emailed → replied → partner → rejected
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS email_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            influencer_id   INTEGER REFERENCES influencers(id),
            direction       TEXT NOT NULL,  -- 'outbound' | 'inbound'
            subject         TEXT,
            body            TEXT,
            sendgrid_id     TEXT,
            gmail_message_id TEXT,
            sent_at         TEXT DEFAULT (datetime('now')),
            ai_reply_sent   INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS search_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            keywords    TEXT,
            audience    TEXT,
            total_found INTEGER DEFAULT 0,
            emailed     INTEGER DEFAULT 0,
            started_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_status ON influencers(status);
        CREATE INDEX IF NOT EXISTS idx_email  ON influencers(email);
    """)
    conn.commit()
    conn.close()
    print("✅ Veritabanı hazır.")


def upsert_influencer(data: dict) -> int:
    """Influencer ekle ya da güncelle, id döndür"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO influencers (username, full_name, bio, followers, following,
            post_count, email, profile_url, website, niche_tags, status)
        VALUES (:username, :full_name, :bio, :followers, :following,
            :post_count, :email, :profile_url, :website, :niche_tags, 'discovered')
        ON CONFLICT(username) DO UPDATE SET
            full_name   = excluded.full_name,
            bio         = excluded.bio,
            followers   = excluded.followers,
            email       = COALESCE(excluded.email, influencers.email),
            updated_at  = datetime('now')
    """, {
        "username":    data.get("username"),
        "full_name":   data.get("full_name", ""),
        "bio":         data.get("bio", ""),
        "followers":   data.get("followers", 0),
        "following":   data.get("following", 0),
        "post_count":  data.get("post_count", 0),
        "email":       data.get("email"),
        "profile_url": data.get("profile_url", f"https://instagram.com/{data.get('username')}"),
        "website":     data.get("website", ""),
        "niche_tags":  json.dumps(data.get("niche_tags", []))
    })
    conn.commit()
    row_id = cur.lastrowid or cur.execute(
        "SELECT id FROM influencers WHERE username=?", (data["username"],)
    ).fetchone()["id"]
    conn.close()
    return row_id


def update_influencer(username: str, **kwargs):
    kwargs["updated_at"] = datetime.utcnow().isoformat()
    sets = ", ".join(f"{k}=:{k}" for k in kwargs)
    conn = get_connection()
    conn.execute(f"UPDATE influencers SET {sets} WHERE username=:username",
                 {**kwargs, "username": username})
    conn.commit()
    conn.close()


def log_email(influencer_id: int, direction: str, subject: str, body: str,
              sendgrid_id: str = None, gmail_message_id: str = None):
    conn = get_connection()
    conn.execute("""
        INSERT INTO email_log (influencer_id, direction, subject, body, sendgrid_id, gmail_message_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (influencer_id, direction, subject, body, sendgrid_id, gmail_message_id))
    conn.commit()
    conn.close()


def get_partners() -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM influencers WHERE status='partner' ORDER BY ai_score DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    conn = get_connection()
    stats = {}
    for status in ["discovered", "emailed", "replied", "partner", "rejected"]:
        stats[status] = conn.execute(
            "SELECT COUNT(*) FROM influencers WHERE status=?", (status,)
        ).fetchone()[0]
    conn.close()
    return stats
