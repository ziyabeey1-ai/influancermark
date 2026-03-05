import base64

from modules.ai_engine import analyze_reply
from modules.database import get_emailed_influencers, log_email, update_influencer
from modules.email_module import get_inbox_messages, mark_as_read, send_email


def _header_map(payload: dict) -> dict:
    headers = payload.get("headers", [])
    return {h.get("name", "").lower(): h.get("value", "") for h in headers}


def _extract_text(payload: dict) -> str:
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"] + "===").decode(errors="ignore")
    for part in payload.get("parts", []) or []:
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"] + "===").decode(errors="ignore")
    return ""


def check_and_process_replies(dry_run: bool = False) -> int:
    contacts = get_emailed_influencers()
    if not contacts:
        print("ℹ️ Reply kontrolü için email gönderilmiş influencer yok.")
        return 0

    email_map = {c["email"].lower(): c for c in contacts if c.get("email")}
    try:
        messages = get_inbox_messages(query="is:unread newer_than:14d", max_results=30)
    except Exception as exc:
        print(f"⚠️ Gmail inbox okunamadı: {exc}")
        return 0
    processed = 0

    for msg in messages:
        payload = msg.get("payload", {})
        headers = _header_map(payload)
        from_header = headers.get("from", "").lower()
        sender_email = None
        for email in email_map:
            if email in from_header:
                sender_email = email
                break

        if not sender_email:
            continue

        influencer = email_map[sender_email]
        body = _extract_text(payload)
        if not body.strip():
            continue

        analysis = analyze_reply(body, influencer.get("full_name") or influencer["username"])
        print(f"📩 @{influencer['username']} -> intent={analysis.get('intent')} sentiment={analysis.get('sentiment')}")

        if dry_run:
            processed += 1
            continue

        update_influencer(influencer["username"], status="replied")
        log_email(direction="inbound", subject=headers.get("subject", ""), body=body, gmail_message_id=msg["id"], influencer_username=influencer["username"])

        suggested = analysis.get("suggested_reply")
        if suggested:
            message_id = send_email(
                to_email=sender_email,
                to_name=influencer.get("full_name") or influencer["username"],
                subject=f"Re: {headers.get('subject', 'İşbirliği Hakkında')}",
                body=suggested,
            )
            if message_id:
                log_email(direction="outbound", subject=f"Re: {headers.get('subject', '')}", body=suggested, gmail_message_id=message_id, influencer_username=influencer["username"])

        if analysis.get("mark_as_partner"):
            update_influencer(influencer["username"], status="partner")

        try:
            mark_as_read(msg["id"])
        except Exception as exc:
            print(f"⚠️ Mesaj okundu işaretlenemedi ({msg['id']}): {exc}")
        processed += 1

    print(f"✅ İşlenen yanıt sayısı: {processed}")
    return processed
