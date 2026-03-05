"""
Influencer Hunter - Otomatik Zamanlayıcı
Arka planda çalıştır:  python scheduler.py

Görevler:
  - Her gün 09:00 → yeni influencer arama (tanımlı keyword listesiyle)
  - Her 1 saat   → gelen yanıtları kontrol et ve otomatik cevapla
"""
import schedule
import time
from datetime import datetime
from main import run_search, show_stats
from modules.reply_handler import check_and_process_replies
from modules.database import init_db

# ── Zamanlanmış arama konfigürasyonu ───────────
SCHEDULED_SEARCHES = [
    {
        "hashtags": ["dijitalpazarlama", "girişimci", "esnafsosyal", "kobipazarlama"],
        "keywords": [],
        "max": 80
    },
    {
        "hashtags": ["küçükişletme", "işletmesahibi", "instagrampazarlama"],
        "keywords": ["dijital pazarlama uzmanı", "sosyal medya yöneticisi"],
        "max": 60
    }
]


def daily_search():
    print(f"\n⏰ Günlük otomatik arama: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    for cfg in SCHEDULED_SEARCHES:
        run_search(
            hashtags=cfg.get("hashtags", []),
            keywords=cfg.get("keywords", []),
            max_results=cfg.get("max", 50),
            dry_run=False
        )
    show_stats()


def hourly_reply_check():
    print(f"\n⏰ Saatlik yanıt kontrolü: {datetime.now().strftime('%H:%M')}")
    check_and_process_replies(dry_run=False)


if __name__ == "__main__":
    print("🤖 Influencer Hunter Zamanlayıcı başlatıldı...")
    init_db()

    # Zamanlamaları ayarla
    schedule.every().day.at("09:00").do(daily_search)
    schedule.every(1).hours.do(hourly_reply_check)

    # İlk çalıştırmayı hemen yap (opsiyonel)
    hourly_reply_check()

    print("📅 Zamanlama:")
    print("   • Her gün 09:00 → Yeni influencer araması")
    print("   • Her 1 saat    → Yanıt kontrolü")
    print("   Durdurmak için: Ctrl+C\n")

    while True:
        schedule.run_pending()
        time.sleep(60)
