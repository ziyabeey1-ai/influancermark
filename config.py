"""Influencer Hunter - Konfigürasyon (Google Stack)."""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Data Source ─────────────────────────────
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")

# ── Google Cloud / Vertex AI ───────────────
GCP_PROJECT = os.getenv("GCP_PROJECT", "your-project-id")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")

# ── Firebase / Firestore ───────────────────
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "")

# ── Gmail API ───────────────────────────────
GMAIL_SENDER_EMAIL = os.getenv("GMAIL_SENDER_EMAIL", "")
GMAIL_CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "data/gmail_credentials.json")
GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "data/gmail_token.json")

# ── Marka & Kampanya Ayarları ──────────────
BRAND_NAME = os.getenv("BRAND_NAME", "yzt.digital")
BRAND_DESC = os.getenv(
    "BRAND_DESC",
    "yzt.digital, KOBİ ve esnaf odaklı dijital pazarlama ajansı.",
)
CAMPAIGN_BRIEF = os.getenv(
    "CAMPAIGN_BRIEF",
    "Dijital dönüşüm, sosyal medya yönetimi ve AI pazarlama konularında içerik ortakları arıyoruz.",
)

# ── Bot Davranış Ayarları ──────────────────
MIN_FOLLOWERS = int(os.getenv("MIN_FOLLOWERS", "1000"))
MAX_FOLLOWERS = int(os.getenv("MAX_FOLLOWERS", "500000"))
MIN_AI_SCORE = float(os.getenv("MIN_AI_SCORE", "6.0"))
EMAIL_DELAY_SECONDS = int(os.getenv("EMAIL_DELAY_SECONDS", "30"))
REPLY_CHECK_INTERVAL = int(os.getenv("REPLY_CHECK_INTERVAL", "3600"))
