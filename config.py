"""
Influencer Hunter - Konfigürasyon
Tüm API anahtarları ve marka ayarları burada.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Apify ────────────────────────────────────
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")

# ── Google Cloud / Vertex AI ─────────────────
GCP_PROJECT  = os.getenv("GCP_PROJECT", "your-project-id")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")

# ── Hunter.io ────────────────────────────────
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")

# ── SendGrid ─────────────────────────────────
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDER_EMAIL     = os.getenv("SENDER_EMAIL", "outreach@yzt.digital")
SENDER_NAME      = os.getenv("SENDER_NAME", "yzt.digital Ekibi")

# ── Marka & Kampanya Ayarları ─────────────────
BRAND_NAME   = os.getenv("BRAND_NAME", "yzt.digital")
BRAND_DESC   = os.getenv(
    "BRAND_DESC",
    "yzt.digital, KOBİ ve esnaf odaklı dijital pazarlama ajansı. "
    "İşletmelerin dijital dünyada güçlü bir varlık oluşturmasına yardımcı oluyoruz."
)
CAMPAIGN_BRIEF = os.getenv(
    "CAMPAIGN_BRIEF",
    "Dijital dönüşüm, sosyal medya yönetimi ve yapay zeka destekli pazarlama araçları "
    "konusunda içerik üreticileriyle uzun vadeli işbirliği arıyoruz."
)

# ── Bot Davranış Ayarları ─────────────────────
MIN_FOLLOWERS         = int(os.getenv("MIN_FOLLOWERS", "1000"))
MAX_FOLLOWERS         = int(os.getenv("MAX_FOLLOWERS", "500000"))
MIN_AI_SCORE          = float(os.getenv("MIN_AI_SCORE", "6.0"))
EMAIL_DELAY_SECONDS   = int(os.getenv("EMAIL_DELAY_SECONDS", "30"))  # Rate limiting
REPLY_CHECK_INTERVAL  = int(os.getenv("REPLY_CHECK_INTERVAL", "3600"))  # 1 saat
