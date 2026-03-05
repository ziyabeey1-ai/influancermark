import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from config import FIREBASE_CREDENTIALS_PATH, FIREBASE_PROJECT_ID

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "influencer_pool.db"

_firestore = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _init_firestore():
    global _firestore
    if _firestore is not None:
        return _firestore
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not FIREBASE_CREDENTIALS_PATH:
            _firestore = False
            return _firestore

        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred, {"projectId": FIREBASE_PROJECT_ID or None})
        _firestore = firestore.client()
    except Exception:
        _firestore = False
    return _firestore


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(conn, table: str, column: str, definition: str):
    cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS influencers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT,
            bio TEXT,
            followers INTEGER DEFAULT 0,
            following INTEGER DEFAULT 0,
            post_count INTEGER DEFAULT 0,
            email TEXT,
            profile_url TEXT,
            website TEXT,
            niche_tags TEXT,
            ai_score REAL DEFAULT 0.0,
            ai_summary TEXT,
            status TEXT DEFAULT 'discovered',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            last_campaign TEXT,
            last_strategy TEXT
        );

        CREATE TABLE IF NOT EXISTS email_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            influencer_username TEXT,
            direction TEXT NOT NULL,
            subject TEXT,
            body TEXT,
            gmail_message_id TEXT,
            sent_at TEXT DEFAULT (datetime('now')),
            ai_reply_sent INTEGER DEFAULT 0,
            campaign_name TEXT,
            strategy_type TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_status ON influencers(status);
        CREATE INDEX IF NOT EXISTS idx_email ON influencers(email);
        CREATE INDEX IF NOT EXISTS idx_email_log_direction_sent_at ON email_log(direction, sent_at);
        """
    )

    _ensure_column(conn, "influencers", "last_campaign", "TEXT")
    _ensure_column(conn, "influencers", "last_strategy", "TEXT")
    _ensure_column(conn, "email_log", "campaign_name", "TEXT")
    _ensure_column(conn, "email_log", "strategy_type", "TEXT")

    conn.commit()
    conn.close()


def _sync_influencer_firestore(data: dict):
    db = _init_firestore()
    if not db:
        return
    username = data["username"].lower()
    db.collection("influencers").document(username).set(data, merge=True)


def upsert_influencer(data: dict) -> int:
    now = _now_iso()
    payload = {
        "username": data.get("username"),
        "full_name": data.get("full_name", ""),
        "bio": data.get("bio", ""),
        "followers": data.get("followers", 0),
        "following": data.get("following", 0),
        "post_count": data.get("post_count", 0),
        "email": data.get("email"),
        "profile_url": data.get("profile_url", f"https://instagram.com/{data.get('username')}"),
        "website": data.get("website", ""),
        "niche_tags": json.dumps(data.get("niche_tags", [])),
        "status": data.get("status", "discovered"),
        "updated_at": now,
        "last_campaign": data.get("last_campaign"),
        "last_strategy": data.get("last_strategy"),
    }

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO influencers (username, full_name, bio, followers, following, post_count, email,
            profile_url, website, niche_tags, status, updated_at, last_campaign, last_strategy)
        VALUES (:username, :full_name, :bio, :followers, :following, :post_count, :email,
            :profile_url, :website, :niche_tags, :status, :updated_at, :last_campaign, :last_strategy)
        ON CONFLICT(username) DO UPDATE SET
            full_name=excluded.full_name,
            bio=excluded.bio,
            followers=excluded.followers,
            following=excluded.following,
            post_count=excluded.post_count,
            email=COALESCE(excluded.email, influencers.email),
            profile_url=excluded.profile_url,
            website=excluded.website,
            niche_tags=excluded.niche_tags,
            updated_at=excluded.updated_at
        """,
        payload,
    )
    conn.commit()
    row = cur.lastrowid or cur.execute("SELECT id FROM influencers WHERE username=?", (payload["username"],)).fetchone()[0]
    conn.close()

    payload["id"] = row
    _sync_influencer_firestore(payload)
    return row


def update_influencer(username: str, **kwargs):
    if not kwargs:
        return
    kwargs["updated_at"] = _now_iso()
    sets = ", ".join(f"{k}=:{k}" for k in kwargs)
    conn = get_connection()
    conn.execute(f"UPDATE influencers SET {sets} WHERE username=:username", {**kwargs, "username": username})
    conn.commit()
    row = conn.execute("SELECT * FROM influencers WHERE username=?", (username,)).fetchone()
    conn.close()
    if row:
        _sync_influencer_firestore(dict(row))


def log_email(
    influencer_id: int = 0,
    direction: str = "outbound",
    subject: str = "",
    body: str = "",
    sendgrid_id: str = None,
    gmail_message_id: str = None,
    influencer_username: str = None,
    campaign_name: str = None,
    strategy_type: str = None,
):
    conn = get_connection()
    if not influencer_username and influencer_id:
        username = conn.execute("SELECT username FROM influencers WHERE id=?", (influencer_id,)).fetchone()
        influencer_username = username[0] if username else None
    conn.execute(
        """
        INSERT INTO email_log (influencer_username, direction, subject, body, gmail_message_id, campaign_name, strategy_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (influencer_username, direction, subject, body, gmail_message_id, campaign_name, strategy_type),
    )
    conn.commit()
    conn.close()

    db = _init_firestore()
    if db:
        db.collection("email_log").add(
            {
                "influencer_username": influencer_username,
                "direction": direction,
                "subject": subject,
                "body": body,
                "gmail_message_id": gmail_message_id,
                "campaign_name": campaign_name,
                "strategy_type": strategy_type,
                "created_at": _now_iso(),
            }
        )


def get_outbound_count_today() -> int:
    conn = get_connection()
    count = conn.execute(
        """
        SELECT COUNT(*) FROM email_log
        WHERE direction='outbound' AND date(sent_at)=date('now')
        """
    ).fetchone()[0]
    conn.close()
    return int(count)


def get_partners() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM influencers WHERE status='partner' ORDER BY ai_score DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    conn = get_connection()
    out = {}
    for status in ["discovered", "emailed", "replied", "partner", "rejected"]:
        out[status] = conn.execute("SELECT COUNT(*) FROM influencers WHERE status=?", (status,)).fetchone()[0]
    conn.close()
    return out


def get_emailed_influencers() -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT username, full_name, email FROM influencers WHERE email IS NOT NULL AND status IN ('emailed','replied')"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_influencers(limit: int = 100) -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM influencers ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def find_candidate_pool(offer_text: str, limit: int = 50, min_ai_score: float = 6.0) -> list:
    keywords = [k.strip().lower() for k in offer_text.split() if len(k.strip()) > 2]
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT * FROM influencers
        WHERE email IS NOT NULL
          AND ai_score >= ?
          AND status IN ('discovered','emailed','replied','partner')
        ORDER BY ai_score DESC, followers DESC
        """,
        (min_ai_score,),
    ).fetchall()
    conn.close()

    if not keywords:
        return [dict(r) for r in rows[:limit]]

    scored = []
    for row in rows:
        d = dict(row)
        text = " ".join(
            [
                (d.get("bio") or "").lower(),
                (d.get("niche_tags") or "").lower(),
                (d.get("ai_summary") or "").lower(),
            ]
        )
        match_score = sum(1 for k in keywords if k in text)
        scored.append((match_score, d))

    scored.sort(key=lambda x: (x[0], x[1].get("ai_score", 0), x[1].get("followers", 0)), reverse=True)
    return [item[1] for item in scored[:limit]]
