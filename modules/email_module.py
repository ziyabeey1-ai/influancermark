import base64
import re
from email.mime.text import MIMEText
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import GMAIL_CREDENTIALS_PATH, GMAIL_SENDER_EMAIL, GMAIL_TOKEN_PATH

SCOPES = ["https://www.googleapis.com/auth/gmail.modify", "https://www.googleapis.com/auth/gmail.send"]


def find_email(profile: dict) -> str | None:
    """Hunter yerine sadece profil bio/website metninden email çıkarır."""
    blobs = [profile.get("bio", "") or "", profile.get("website", "") or ""]
    combined = "\n".join(blobs)
    match = re.search(r"[\w.\-+]+@[\w\-]+(?:\.[\w\-]+)+", combined, re.IGNORECASE)
    return match.group(0).lower() if match else None


def _gmail_service():
    token_path = Path(GMAIL_TOKEN_PATH)
    creds_path = Path(GMAIL_CREDENTIALS_PATH)

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())

    if not creds or not creds.valid:
        if not creds_path.exists():
            raise FileNotFoundError(f"Gmail credentials dosyası yok: {creds_path}")
        flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
        creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def send_email(to_email: str, to_name: str, subject: str, body: str) -> str | None:
    sender = GMAIL_SENDER_EMAIL or "me"
    message = MIMEText(body, "plain", "utf-8")
    message["to"] = f"{to_name} <{to_email}>" if to_name else to_email
    message["from"] = sender
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        service = _gmail_service()
        sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return sent.get("id")
    except Exception as exc:
        print(f"  ❌ Gmail gönderim hatası: {exc}")
        return None


def get_inbox_messages(query: str = "is:unread", max_results: int = 20) -> list[dict]:
    service = _gmail_service()
    response = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    ids = response.get("messages", [])
    messages = []
    for item in ids:
        msg = service.users().messages().get(userId="me", id=item["id"], format="full").execute()
        messages.append(msg)
    return messages


def mark_as_read(message_id: str):
    service = _gmail_service()
    service.users().messages().modify(userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}).execute()
