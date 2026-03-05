"""
Influencer Hunter - Vertex AI (Gemini) Modülü
- Profil alaka skoru
- Niche tespiti
- Outreach email üretimi
- Gelen yanıt analizi + otomatik reply
"""
import json
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from config import GCP_PROJECT, GCP_LOCATION, BRAND_NAME, BRAND_DESC, CAMPAIGN_BRIEF


vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
_model = GenerativeModel("gemini-1.5-flash-002")
_json_config = GenerationConfig(response_mime_type="application/json", temperature=0.3)
_text_config = GenerationConfig(temperature=0.7, max_output_tokens=600)


# ─────────────────────────────────────────────
# 1. Profil Alaka Analizi
# ─────────────────────────────────────────────
def analyze_profile(profile: dict, target_keywords: list[str]) -> dict:
    """
    Profili hedef kitleye göre değerlendir.
    Döndürür: {score: 0-10, niches: [...], summary: str, suitable: bool}
    """
    prompt = f"""
Sen bir influencer marketing uzmanısın.
Aşağıdaki Instagram profilini değerlendir.

MARKA: {BRAND_NAME}
MARKA AÇIKLAMASI: {BRAND_DESC}
HEDEF KİTLE / ANAHTAR KELİMELER: {', '.join(target_keywords)}

PROFIL:
- Kullanıcı adı: {profile.get('username')}
- Ad: {profile.get('full_name')}
- Bio: {profile.get('bio')}
- Takipçi: {profile.get('followers'):,}
- Post sayısı: {profile.get('post_count')}
- Web sitesi: {profile.get('website')}

GÖREV: Aşağıdaki JSON formatında yanıt ver (başka hiçbir şey yazma):
{{
  "score": <0-10 arası uygunluk puanı>,
  "niches": ["niche1", "niche2"],
  "summary": "<2 cümle Türkçe değerlendirme>",
  "suitable": <true/false>,
  "rejection_reason": "<uygun değilse neden, uygunsa null>"
}}

Kriterler:
- score >= 6 ise suitable=true
- Fake/bot hesaplar için score=0
- Micro influencer (1K-100K) için bonus puan
"""
    response = _model.generate_content(prompt, generation_config=_json_config)
    try:
        result = json.loads(response.text)
        result.setdefault("score", 0)
        result.setdefault("niches", [])
        result.setdefault("suitable", False)
        return result
    except Exception as e:
        print(f"  ⚠️ Analiz parse hatası ({profile['username']}): {e}")
        return {"score": 0, "niches": [], "summary": "", "suitable": False}


# ─────────────────────────────────────────────
# 2. Outreach Email Üretimi
# ─────────────────────────────────────────────
def generate_outreach_email(profile: dict, ai_analysis: dict) -> dict:
    """
    Kişiye özel işbirliği teklif emaili üret.
    Döndürür: {subject: str, body: str}
    """
    prompt = f"""
Sen {BRAND_NAME} adına influencer outreach emaili yazıyorsun.

MARKA: {BRAND_NAME}
MARKA AÇIKLAMASI: {BRAND_DESC}
KAMPANYa BRİFİNGİ: {CAMPAIGN_BRIEF}

INFLUENCER:
- Ad: {profile.get('full_name') or profile.get('username')}
- Kullanıcı adı: @{profile.get('username')}
- Niche: {', '.join(ai_analysis.get('niches', []))}
- AI Özet: {ai_analysis.get('summary')}

GÖREV: Kişiselleştirilmiş, samimi, kısa (max 150 kelime) bir işbirliği teklif emaili yaz.
Aşağıdaki JSON formatında yanıt ver (başka hiçbir şey yazma):
{{
  "subject": "<email konusu>",
  "body": "<email gövdesi - HTML değil, düz metin>"
}}

Kurallar:
- Türkçe yaz
- İsmi veya @kullanıcıadını kullan
- İşbirliğinin onlara ne kazandıracağını belirt
- Spammy, aşırı satışçı bir dil kullanma
- Sonunda "Bekliyorum / Görüşmek üzere" ile bitir
- Gönderen imzası: {BRAND_NAME} Ekibi
"""
    response = _model.generate_content(prompt, generation_config=_json_config)
    try:
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"  ⚠️ Email üretim hatası: {e}")
        return {
            "subject": f"{BRAND_NAME} x @{profile['username']} - İşbirliği Teklifi",
            "body": f"Merhaba,\n\nSize bir işbirliği teklifimiz var. Detayları konuşmak ister misiniz?\n\n{BRAND_NAME} Ekibi"
        }


# ─────────────────────────────────────────────
# 3. Gelen Yanıt Analizi
# ─────────────────────────────────────────────
def analyze_reply(email_body: str, influencer_name: str) -> dict:
    """
    Gelen yanıtı analiz et.
    Döndürür: {sentiment: positive/negative/neutral, intent: interested/not_interested/asking_info/..., suggested_reply: str}
    """
    prompt = f"""
Bir influencer'dan gelen email yanıtını analiz et.

INFLUENCER ADI: {influencer_name}
MARKA: {BRAND_NAME}
KAMPANYA: {CAMPAIGN_BRIEF}

GELEN EMAIL:
\"\"\"
{email_body}
\"\"\"

Aşağıdaki JSON formatında yanıt ver:
{{
  "sentiment": "positive" | "negative" | "neutral",
  "intent": "interested" | "not_interested" | "asking_price" | "asking_details" | "needs_followup",
  "key_points": ["<email'den çıkarılan önemli nokta>"],
  "suggested_reply": "<Türkçe, marka adına yazılmış hazır yanıt maili - max 100 kelime>",
  "mark_as_partner": <true/false - olumlu yanıt ise true>
}}
"""
    response = _model.generate_content(prompt, generation_config=_json_config)
    try:
        return json.loads(response.text)
    except Exception as e:
        print(f"  ⚠️ Yanıt analiz hatası: {e}")
        return {
            "sentiment": "neutral",
            "intent": "needs_followup",
            "key_points": [],
            "suggested_reply": "Teşekkürler, en kısa sürede size dönüş yapacağız.",
            "mark_as_partner": False
        }
