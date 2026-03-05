import json

from config import BRAND_NAME, BRAND_DESC, CAMPAIGN_BRIEF, GCP_LOCATION, GCP_PROJECT

_model = None
_json_config = None


def _get_model():
    global _model, _json_config
    if _model is not None:
        return _model, _json_config
    try:
        import vertexai
        from vertexai.generative_models import GenerationConfig, GenerativeModel

        vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
        _model = GenerativeModel("gemini-1.5-flash-002")
        _json_config = GenerationConfig(response_mime_type="application/json", temperature=0.3)
    except Exception:
        _model = False
    return _model, _json_config


def analyze_profile(profile: dict, target_keywords: list[str]) -> dict:
    model, cfg = _get_model()
    if not model:
        score = 7 if (1000 <= (profile.get("followers") or 0) <= 100000) else 5
        return {
            "score": score,
            "niches": target_keywords[:2],
            "summary": "Vertex AI devre dışı; kural tabanlı ön değerlendirme kullanıldı.",
            "suitable": score >= 6,
            "rejection_reason": None if score >= 6 else "takipçi aralığı düşük/uyumsuz",
        }

    prompt = f"""
MARKA: {BRAND_NAME}
MARKA AÇIKLAMASI: {BRAND_DESC}
HEDEF KİTLE: {', '.join(target_keywords)}
PROFIL: {json.dumps(profile, ensure_ascii=False)}
Yalnızca JSON dön:
{{"score":0-10,"niches":[],"summary":"","suitable":true/false,"rejection_reason":null}}
"""
    response = model.generate_content(prompt, generation_config=cfg)
    try:
        result = json.loads(response.text)
        result.setdefault("score", 0)
        result.setdefault("niches", [])
        result.setdefault("suitable", False)
        return result
    except Exception:
        return {"score": 0, "niches": [], "summary": "", "suitable": False}


def generate_outreach_email(profile: dict, ai_analysis: dict) -> dict:
    return generate_strategy_email(
        profile=profile,
        ai_analysis=ai_analysis,
        product_or_service=CAMPAIGN_BRIEF,
        strategy_type="standard",
        budget_info="",
        sample_offer="",
    )


def generate_strategy_email(
    profile: dict,
    ai_analysis: dict,
    product_or_service: str,
    strategy_type: str,
    budget_info: str = "",
    sample_offer: str = "",
) -> dict:
    model, cfg = _get_model()

    if not model:
        strategy_line = {
            "budget": f"Bütçe aralığımız: {budget_info or 'görüşmeye göre belirlenecek'}.",
            "sample": f"Deneme ürünü/servisi sunabiliriz: {sample_offer or 'evet'}.",
            "hybrid": f"Hem bütçe ({budget_info or 'görüşmeye göre'}) hem deneme teklifimiz mevcut ({sample_offer or 'detayları paylaşırız'}).",
            "standard": "İş birliği detaylarını birlikte netleştirebiliriz.",
        }.get(strategy_type, "İş birliği detaylarını birlikte netleştirebiliriz.")
        return {
            "subject": f"{BRAND_NAME} x @{profile['username']} - {product_or_service[:40]}",
            "body": (
                f"Merhaba {profile.get('full_name') or profile.get('username')},\n\n"
                f"{BRAND_NAME} olarak {product_or_service} için sizinle iş birliği yapmak istiyoruz. "
                f"{strategy_line}\n\n"
                "Uygunsanız kısa bir görüşme planlayalım.\n\n"
                f"{BRAND_NAME} Ekibi"
            ),
        }

    prompt = f"""
MARKA: {BRAND_NAME}
MARKA AÇIKLAMASI: {BRAND_DESC}
ÜRÜN/HİZMET: {product_or_service}
STRATEJİ: {strategy_type}
BÜTÇE BİLGİSİ: {budget_info}
DENEME TEKLİFİ: {sample_offer}
INFLUENCER: {json.dumps(profile, ensure_ascii=False)}
ANALIZ: {json.dumps(ai_analysis, ensure_ascii=False)}

Görev: Türkçe kişiselleştirilmiş, kısa ve profesyonel işbirliği emaili üret.
Sadece JSON dön: {{"subject":"","body":""}}
"""
    response = model.generate_content(prompt, generation_config=cfg)
    try:
        return json.loads(response.text)
    except Exception:
        return {
            "subject": f"{BRAND_NAME} x @{profile['username']} - İşbirliği",
            "body": f"Merhaba, {product_or_service} için işbirliği konuşmak isteriz. {BRAND_NAME} Ekibi",
        }


def analyze_reply(email_body: str, influencer_name: str) -> dict:
    return {
        "sentiment": "neutral",
        "intent": "needs_followup",
        "key_points": [email_body[:120]],
        "suggested_reply": f"Merhaba {influencer_name}, ilginiz için teşekkürler. Detayları paylaşabiliriz.",
        "mark_as_partner": False,
    }
