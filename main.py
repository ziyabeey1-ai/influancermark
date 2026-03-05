"""
Influencer Hunter Bot - Ana Orkestratör
yzt.digital için Vertex AI destekli Instagram influencer arama & outreach sistemi

Kullanım:
  python main.py search  --hashtags "dijitalpazarlama,girişimci" --max 100
  python main.py search  --keywords "küçük işletme sahibi istanbul" --max 50
  python main.py replies --dry-run
  python main.py stats
  python main.py partners
"""
import argparse
import time
import sys
from datetime import datetime

from config import (
    MIN_FOLLOWERS, MAX_FOLLOWERS, MIN_AI_SCORE,
    EMAIL_DELAY_SECONDS, APIFY_TOKEN, SENDGRID_API_KEY, HUNTER_API_KEY
)
from modules.database      import init_db, upsert_influencer, update_influencer, log_email, get_stats, get_partners
from modules.instagram_scraper import search_by_hashtag, search_by_keyword, enrich_profiles
from modules.ai_engine     import analyze_profile, generate_outreach_email
from modules.email_module  import find_email, send_email
from modules.reply_handler import check_and_process_replies


BANNER = """
╔══════════════════════════════════════════════════════╗
║     🎯  INFLUENCER HUNTER  —  yzt.digital            ║
║     Vertex AI (Gemini) + Apify + Hunter.io           ║
╚══════════════════════════════════════════════════════╝
"""


def _check_config():
    issues = []
    if not APIFY_TOKEN:    issues.append("APIFY_TOKEN eksik")
    if not SENDGRID_API_KEY: issues.append("SENDGRID_API_KEY eksik")
    if not HUNTER_API_KEY: issues.append("HUNTER_API_KEY eksik (email bulma kısmi çalışır)")
    if issues:
        print("⚠️  Eksik konfigürasyon:")
        for i in issues: print(f"   • {i}")
        print("   → .env dosyasını kontrol et\n")


# ─────────────────────────────────────────────
# SEARCH PIPELINE
# ─────────────────────────────────────────────
def run_search(hashtags: list[str] = None, keywords: list[str] = None,
               max_results: int = 100, dry_run: bool = False):
    """
    Tam arama + analiz + email pipeline
    """
    print(BANNER)
    _check_config()
    init_db()

    all_keywords = (hashtags or []) + (keywords or [])
    print(f"🚀 Arama başlıyor: {all_keywords}")
    print(f"   Filtreler: {MIN_FOLLOWERS:,} – {MAX_FOLLOWERS:,} takipçi | min skor: {MIN_AI_SCORE}")
    print(f"   Dry run: {dry_run}\n")

    # 1. Instagram'dan profilleri çek
    profiles = []
    if hashtags:
        profiles += search_by_hashtag(hashtags, max_per_tag=max_results // max(len(hashtags), 1))
    if keywords:
        profiles += search_by_keyword(keywords, max_results=max_results)

    if not profiles:
        print("❌ Profil bulunamadı.")
        return

    print(f"\n📋 Toplam çekilen profil: {len(profiles)}")

    # 2. Takipçi filtresi
    profiles = [p for p in profiles
                if MIN_FOLLOWERS <= (p.get("followers") or 0) <= MAX_FOLLOWERS]
    print(f"   Takipçi filtresi sonrası: {len(profiles)}")

    # 3. Her profili işle
    stats = {"analyzed": 0, "suitable": 0, "email_found": 0, "sent": 0}

    for i, profile in enumerate(profiles, 1):
        username = profile["username"]
        print(f"\n[{i}/{len(profiles)}] @{username} ({profile.get('followers',0):,} takipçi)")

        # DB'ye kaydet
        inf_id = upsert_influencer(profile)

        # AI analizi
        analysis = analyze_profile(profile, all_keywords)
        stats["analyzed"] += 1

        score = analysis.get("score", 0)
        niches = analysis.get("niches", [])
        print(f"  🤖 Skor: {score}/10 | Niche: {', '.join(niches)}")

        # DB'yi güncelle
        update_influencer(username,
            ai_score=score,
            ai_summary=analysis.get("summary", ""),
            niche_tags=str(niches)
        )

        if not analysis.get("suitable"):
            reason = analysis.get("rejection_reason", "uygun değil")
            print(f"  ⏭ Atlandı: {reason}")
            update_influencer(username, status="rejected")
            continue

        stats["suitable"] += 1

        # Email bul
        email = profile.get("email") or find_email(profile)
        if not email:
            print(f"  ⚠️ Email bulunamadı, atlanıyor.")
            continue

        update_influencer(username, email=email)
        stats["email_found"] += 1

        # Email içeriği üret
        email_content = generate_outreach_email(profile, analysis)
        subject = email_content["subject"]
        body    = email_content["body"]

        print(f"  📝 Email: {subject[:60]}...")

        if dry_run:
            print(f"  [DRY RUN] Gönderilmedi → {email}")
            continue

        # Gönder
        msg_id = send_email(email, profile.get("full_name") or username, subject, body)
        if msg_id:
            update_influencer(username, status="emailed")
            log_email(inf_id, "outbound", subject, body, sendgrid_id=msg_id)
            stats["sent"] += 1

        # Rate limiting
        if i < len(profiles):
            print(f"  ⏳ {EMAIL_DELAY_SECONDS}s bekleniyor...")
            time.sleep(EMAIL_DELAY_SECONDS)

    # 4. Özet
    print(f"""
╔══════════════════════════════════════╗
║  📊  PIPELINE TAMAMLANDI             ║
╠══════════════════════════════════════╣
║  Analiz edilen  : {stats['analyzed']:>5}                ║
║  Uygun          : {stats['suitable']:>5}                ║
║  Email bulundu  : {stats['email_found']:>5}                ║
║  Email gönderildi: {stats['sent']:>4}                ║
╚══════════════════════════════════════╝
""")


# ─────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────
def show_stats():
    init_db()
    s = get_stats()
    total = sum(s.values())
    print(f"""
{BANNER}
📊 INFLUENCER HAVUZU DURUMU ({datetime.now().strftime('%d.%m.%Y %H:%M')})
{'─'*45}
  🔍 Keşfedilen    : {s.get('discovered', 0):>6}
  ✉️  Email gönderildi: {s.get('emailed', 0):>4}
  💬 Yanıt geldi   : {s.get('replied', 0):>6}
  🤝 Partner       : {s.get('partner', 0):>6}
  ❌ Reddedildi    : {s.get('rejected', 0):>6}
{'─'*45}
  TOPLAM           : {total:>6}
""")


def show_partners():
    init_db()
    partners = get_partners()
    if not partners:
        print("Henüz partner yok.")
        return
    print(f"\n🤝 PARTNER LİSTESİ ({len(partners)} kişi)\n{'─'*60}")
    for p in partners:
        print(f"  @{p['username']:<25} {p.get('followers',0):>8,} takipçi | "
              f"Skor: {p.get('ai_score',0):.1f} | {p.get('email','?')}")


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Influencer Hunter Bot")
    sub = parser.add_subparsers(dest="command")

    # search
    p_search = sub.add_parser("search", help="Influencer ara ve email gönder")
    p_search.add_argument("--hashtags", type=str, help="Virgülle ayrılmış hashtagler")
    p_search.add_argument("--keywords", type=str, help="Virgülle ayrılmış anahtar kelimeler")
    p_search.add_argument("--max", type=int, default=50, help="Max profil sayısı")
    p_search.add_argument("--dry-run", action="store_true", help="Email gönderme, sadece simüle et")

    # replies
    p_replies = sub.add_parser("replies", help="Gelen yanıtları işle")
    p_replies.add_argument("--dry-run", action="store_true")

    # stats
    sub.add_parser("stats", help="Havuz istatistikleri")

    # partners
    sub.add_parser("partners", help="Partner listesi")

    args = parser.parse_args()

    if args.command == "search":
        hashtags = [h.strip() for h in args.hashtags.split(",")] if args.hashtags else []
        keywords = [k.strip() for k in args.keywords.split(",")] if args.keywords else []
        if not hashtags and not keywords:
            print("❌ En az --hashtags veya --keywords gerekli.")
            sys.exit(1)
        run_search(hashtags=hashtags, keywords=keywords,
                   max_results=args.max, dry_run=args.dry_run)

    elif args.command == "replies":
        init_db()
        check_and_process_replies(dry_run=args.dry_run)

    elif args.command == "stats":
        show_stats()

    elif args.command == "partners":
        show_partners()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
