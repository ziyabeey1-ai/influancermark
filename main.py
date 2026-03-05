"""Influencer Hunter Bot - Google Altyapı Odaklı Ana Orkestratör."""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from config import (
    APIFY_TOKEN,
    DAILY_EMAIL_LIMIT,
    EMAIL_DELAY_SECONDS,
    FIREBASE_CREDENTIALS_PATH,
    GMAIL_CREDENTIALS_PATH,
    MAX_FOLLOWERS,
    MIN_AI_SCORE,
    MIN_FOLLOWERS,
)
from modules.ai_engine import analyze_profile, generate_strategy_email
from modules.database import (
    find_candidate_pool,
    get_outbound_count_today,
    get_partners,
    get_stats,
    init_db,
    log_email,
    update_influencer,
    upsert_influencer,
)
from modules.email_module import find_email, send_email
from modules.instagram_scraper import search_by_hashtag, search_by_keyword
from modules.reply_handler import check_and_process_replies

BANNER = """
╔══════════════════════════════════════════════════════╗
║     🎯 INFLUENCER HUNTER — Google Stack             ║
║     Vertex AI + Gmail API + Firebase                ║
╚══════════════════════════════════════════════════════╝
"""


def _check_config():
    issues = []
    if not APIFY_TOKEN:
        issues.append("APIFY_TOKEN eksik (Instagram verisi gelmez)")
    if not GMAIL_CREDENTIALS_PATH or not Path(GMAIL_CREDENTIALS_PATH).exists():
        issues.append("GMAIL_CREDENTIALS_PATH eksik/geçersiz")
    if not FIREBASE_CREDENTIALS_PATH:
        issues.append("FIREBASE_CREDENTIALS_PATH eksik (yalnızca lokal cache)")
    if issues:
        print("⚠️ Eksik konfigürasyon:")
        for issue in issues:
            print(f"   • {issue}")
        print("   → .env dosyasını kontrol et\n")


def _daily_quota_remaining() -> int:
    sent_today = get_outbound_count_today()
    remaining = max(0, DAILY_EMAIL_LIMIT - sent_today)
    print(f"📨 Günlük kota: {sent_today}/{DAILY_EMAIL_LIMIT} kullanıldı | kalan: {remaining}")
    return remaining


def run_search(hashtags: list[str] = None, keywords: list[str] = None, max_results: int = 100, dry_run: bool = False):
    print(BANNER)
    _check_config()
    init_db()

    all_keywords = (hashtags or []) + (keywords or [])
    print(f"🚀 Arama başlıyor: {all_keywords}")
    print(f"   Filtreler: {MIN_FOLLOWERS:,}-{MAX_FOLLOWERS:,} takipçi | min skor: {MIN_AI_SCORE}")
    print(f"   Dry run: {dry_run}\n")

    quota_remaining = _daily_quota_remaining() if not dry_run else max_results
    if quota_remaining <= 0 and not dry_run:
        print("⛔ Günlük email limiti doldu, yarın tekrar deneyin.")
        return

    profiles = []
    if hashtags:
        profiles.extend(search_by_hashtag(hashtags, max_per_tag=max(1, max_results // max(len(hashtags), 1))))
    if keywords:
        profiles.extend(search_by_keyword(keywords, max_results=max_results))

    if not profiles:
        print("❌ Profil bulunamadı.")
        return

    profiles = [p for p in profiles if MIN_FOLLOWERS <= (p.get("followers") or 0) <= MAX_FOLLOWERS]
    print(f"📋 Filtre sonrası profil sayısı: {len(profiles)}")

    stats = {"analyzed": 0, "suitable": 0, "email_found": 0, "sent": 0}

    for i, profile in enumerate(profiles, 1):
        username = profile["username"]
        print(f"\n[{i}/{len(profiles)}] @{username}")

        inf_id = upsert_influencer(profile)
        analysis = analyze_profile(profile, all_keywords)
        stats["analyzed"] += 1

        score = float(analysis.get("score", 0))
        suitable = bool(analysis.get("suitable", False)) and score >= MIN_AI_SCORE

        update_influencer(
            username,
            ai_score=score,
            ai_summary=analysis.get("summary", ""),
            niche_tags=json.dumps(analysis.get("niches", []), ensure_ascii=False),
        )

        if not suitable:
            update_influencer(username, status="rejected")
            print(f"  ⏭ Uygun değil (score={score})")
            continue

        stats["suitable"] += 1
        email = profile.get("email") or find_email(profile)
        if not email:
            print("  ⚠️ Email bulunamadı")
            continue

        stats["email_found"] += 1
        update_influencer(username, email=email)

        email_content = generate_strategy_email(
            profile=profile,
            ai_analysis=analysis,
            product_or_service="Yeni iş birliği fırsatı",
            strategy_type="standard",
        )

        if dry_run:
            print(f"  [DRY-RUN] {email} adresine gönderim simüle edildi")
            continue

        if quota_remaining <= 0:
            print("⛔ Günlük email kotası doldu, gönderim durduruldu.")
            break

        message_id = send_email(
            to_email=email,
            to_name=profile.get("full_name") or username,
            subject=email_content["subject"],
            body=email_content["body"],
        )
        if message_id:
            update_influencer(username, status="emailed")
            log_email(
                influencer_id=inf_id,
                direction="outbound",
                subject=email_content["subject"],
                body=email_content["body"],
                gmail_message_id=message_id,
            )
            stats["sent"] += 1
            quota_remaining -= 1

        if i < len(profiles):
            time.sleep(EMAIL_DELAY_SECONDS)

    print(
        f"\n✅ Pipeline tamamlandı | analyzed={stats['analyzed']} suitable={stats['suitable']} email_found={stats['email_found']} sent={stats['sent']}"
    )


def run_campaign(
    offer: str,
    strategy: str,
    budget: str,
    sample_offer: str,
    limit: int,
    dry_run: bool,
):
    print(BANNER)
    _check_config()
    init_db()

    candidates = find_candidate_pool(offer_text=offer, limit=limit, min_ai_score=MIN_AI_SCORE)
    if not candidates:
        print("❌ Havuzda uygun influencer bulunamadı.")
        return

    quota_remaining = _daily_quota_remaining() if not dry_run else len(candidates)
    sent = 0

    print(f"🎯 Kampanya: {offer}")
    print(f"📌 Strateji: {strategy} | Bütçe: {budget or '-'} | Deneme: {sample_offer or '-'}")
    print(f"👥 Eşleşen influencer: {len(candidates)}")

    for idx, influencer in enumerate(candidates, 1):
        username = influencer["username"]
        email = influencer.get("email")
        if not email:
            continue

        analysis = {
            "score": influencer.get("ai_score", 0),
            "niches": influencer.get("niche_tags", "[]"),
            "summary": influencer.get("ai_summary", ""),
        }
        email_content = generate_strategy_email(
            profile=influencer,
            ai_analysis=analysis,
            product_or_service=offer,
            strategy_type=strategy,
            budget_info=budget,
            sample_offer=sample_offer,
        )

        print(f"\n[{idx}/{len(candidates)}] @{username} -> {email}")
        if dry_run:
            print(f"  [DRY-RUN] {email_content['subject']}")
            continue

        if quota_remaining <= 0:
            print("⛔ Günlük email kotası doldu, kampanya durduruldu.")
            break

        message_id = send_email(
            to_email=email,
            to_name=influencer.get("full_name") or username,
            subject=email_content["subject"],
            body=email_content["body"],
        )
        if message_id:
            update_influencer(username, status="emailed", last_campaign=offer, last_strategy=strategy)
            log_email(
                direction="outbound",
                subject=email_content["subject"],
                body=email_content["body"],
                gmail_message_id=message_id,
                influencer_username=username,
                campaign_name=offer,
                strategy_type=strategy,
            )
            sent += 1
            quota_remaining -= 1

        time.sleep(EMAIL_DELAY_SECONDS)

    print(f"\n✅ Kampanya tamamlandı | gönderilen: {sent}")


def show_stats():
    init_db()
    s = get_stats()
    total = sum(s.values())
    print(
        f"""
{BANNER}
📊 HAVUZ DURUMU ({datetime.now().strftime('%d.%m.%Y %H:%M')})
  discovered: {s.get('discovered',0)}
  emailed   : {s.get('emailed',0)}
  replied   : {s.get('replied',0)}
  partner   : {s.get('partner',0)}
  rejected  : {s.get('rejected',0)}
  total     : {total}
"""
    )


def show_partners():
    init_db()
    partners = get_partners()
    if not partners:
        print("Henüz partner yok.")
        return
    for p in partners:
        print(f"@{p['username']} | skor={p.get('ai_score',0)} | email={p.get('email','-')}")


def main():
    parser = argparse.ArgumentParser(description="Influencer Hunter Bot")
    sub = parser.add_subparsers(dest="command")

    p_search = sub.add_parser("search", help="Influencer ara ve email gönder")
    p_search.add_argument("--hashtags", type=str)
    p_search.add_argument("--keywords", type=str)
    p_search.add_argument("--max", type=int, default=50)
    p_search.add_argument("--dry-run", action="store_true")

    p_campaign = sub.add_parser("campaign", help="Havuzdan kampanya için uygun influencerlara ulaş")
    p_campaign.add_argument("--offer", type=str, required=True, help="Pazarlanacak ürün/hizmet")
    p_campaign.add_argument("--strategy", type=str, default="standard", choices=["standard", "budget", "sample", "hybrid"])
    p_campaign.add_argument("--budget", type=str, default="", help="Bütçe teklifi")
    p_campaign.add_argument("--sample-offer", type=str, default="", help="Deneme ürünü/servisi")
    p_campaign.add_argument("--limit", type=int, default=100)
    p_campaign.add_argument("--dry-run", action="store_true")

    p_replies = sub.add_parser("replies", help="Gelen yanıtları işle")
    p_replies.add_argument("--dry-run", action="store_true")

    sub.add_parser("stats", help="Havuz istatistikleri")
    sub.add_parser("partners", help="Partner listesi")

    args = parser.parse_args()

    if args.command == "search":
        hashtags = [h.strip() for h in args.hashtags.split(",")] if args.hashtags else []
        keywords = [k.strip() for k in args.keywords.split(",")] if args.keywords else []
        if not hashtags and not keywords:
            print("❌ En az --hashtags veya --keywords gerekli.")
            sys.exit(1)
        run_search(hashtags=hashtags, keywords=keywords, max_results=args.max, dry_run=args.dry_run)
    elif args.command == "campaign":
        run_campaign(
            offer=args.offer,
            strategy=args.strategy,
            budget=args.budget,
            sample_offer=args.sample_offer,
            limit=args.limit,
            dry_run=args.dry_run,
        )
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
