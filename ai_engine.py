"""
Influencer Hunter - Email Modülü
- Hunter.io ile email bulma
- SendGrid ile gönderme
"""
import re
import requests
from config import HUNTER_API_KEY, SENDGRID_API_KEY, SENDER_EMAIL, SENDER_NAME


# ─────────────────────────────────────────────
# Hunter.io - Email Bulma
# ─────────────────────────────────────────────
def find_email(profile: dict) -> str | None:
    """
    Önce bio'dan email yakala.
    Yoksa Hunter.io ile web sitesinden bul.
    """
    # 1. Bio'dan direkt email
    bio = profile.get("bio", "") or ""
    bio_match = re.search(r"[\w.\-+]+@[\w.\-]+\.[a-z]{2,}", bio)
    if bio_match:
        print(f"  📧 Bio'dan bulundu: {bio_match.group(0)}")
        return bio_match.group(0)

    # 2. Web sitesi varsa Hunter.io domain search
    website = profile.get("website", "") or ""
    if website and HUNTER_API_KEY:
        domain = _extract_domain(website)
        if domain:
            email = _hunter_domain_search(domain, profile.get("full_name", ""))
            if email:
                return email

    # 3. Hunter.io author search (isim + site)
    if HUNTER_API_KEY and profile.get("full_name") and website:
        domain = _extract_domain(website)
        if domain:
            return _hunter_email_finder(
                domain=domain,
                first_name=profile["full_name"].split()[0],
                last_name=" ".join(profile["full_name"].split()[1:]) if len(profile["full_name"].split()) > 1 else ""
            )

    return None


def _extract_domain(url: str) -> str | None:
    url = url.strip().lower()
    if not url.startswith("http"):
        url = "https://" + url
    match = re.search(r"https?://(?:www\.)?([^/?\s]+)", url)
    return match.group(1) if match else None


def _hunter_domain_search(domain: str, full_name: str = "") -> str | None:
    """Hunter.io domain search - o sitedeki email adreslerini bul"""
    try:
        resp = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={"domain": domain, "api_key": HUNTER_API_KEY, "limit": 5}
        )
        data = resp.json()
        emails = data.get("data", {}).get("emails", [])
        if emails:
            # En yüksek confidence'lı ilk email'i al
            best = max(emails, key=lambda e: e.get("confidence", 0))
            if best.get("confidence", 0) > 50:
                print(f"  📧 Hunter.io (domain): {best['value']} (güven: {best['confidence']}%)")
                return best["value"]
    except Exception as e:
        print(f"  ⚠️ Hunter domain search hata: {e}")
    return None


def _hunter_email_finder(domain: str, first_name: str, last_name: str) -> str | None:
    """Hunter.io email finder - isim + domain"""
    try:
        resp = requests.get(
            "https://api.hunter.io/v2/email-finder",
            params={
                "domain": domain,
                "first_name": first_name,
                "last_name": last_name,
                "api_key": HUNTER_API_KEY
            }
        )
        data = resp.json()
        email = data.get("data", {}).get("email")
        confidence = data.get("data", {}).get("score", 0)
        if email and confidence > 40:
            print(f"  📧 Hunter.io (finder): {email} (güven: {confidence}%)")
            return email
    except Exception as e:
        print(f"  ⚠️ Hunter email finder hata: {e}")
    return None


# ─────────────────────────────────────────────
# SendGrid - Email Gönderme
# ─────────────────────────────────────────────
def send_email(to_email: str, to_name: str, subject: str, body: str) -> str | None:
    """
    SendGrid ile email gönder.
    Döndürür: message_id veya None
    """
    payload = {
        "personalizations": [{
            "to": [{"email": to_email, "name": to_name}],
            "subject": subject
        }],
        "from": {"email": SENDER_EMAIL, "name": SENDER_NAME},
        "reply_to": {"email": SENDER_EMAIL, "name": SENDER_NAME},
        "content": [{"type": "text/plain", "value": body}],
        "tracking_settings": {
            "click_tracking": {"enable": False},
            "open_tracking": {"enable": True}
        }
    }

    try:
        resp = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        if resp.status_code == 202:
            msg_id = resp.headers.get("X-Message-Id", "")
            print(f"  ✉️ Gönderildi → {to_email} (ID: {msg_id})")
            return msg_id
        else:
            print(f"  ❌ SendGrid hata {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"  ❌ Send hatası: {e}")
        return None
