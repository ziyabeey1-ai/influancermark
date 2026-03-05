# 🎯 Influencer Hunter Bot — Google Stack

Instagram influencer bulma, Gmail ile otomatik outreach, Firebase partner havuzu ve Streamlit dashboard.

## Mimari

```
Instagram (Apify)
  ↓
Profil Filtresi + AI Skorlama (Vertex AI / Gemini)
  ↓
Havuz (SQLite + Firestore sync)
  ↓
Kampanya eşleştirme (ürün/hizmet + strateji + bütçe/deneme)
  ↓
Gmail API → outreach email gönderimi (günlük limit: 1000 varsayılan)
  ↓
Gmail API → gelen yanıtları okuma + AI analiz + otomatik dönüş
  ↓
Streamlit Dashboard
```

## Özellikler
- ✅ Hunter/SendGrid yok, Google odaklı stack.
- ✅ Günlük email limiti kontrolü (`DAILY_EMAIL_LIMIT`, varsayılan 1000).
- ✅ Havuzdan ürün/hizmet bilgisine göre uygun influencer seçimi.
- ✅ Strateji bazlı iletişim (`standard`, `budget`, `sample`, `hybrid`).
- ✅ Firestore ile bulut senkron + lokal SQLite cache.

## Kurulum

```bash
pip install -r requirements.txt
cp env.example .env
```

## Kullanım

### 1) Havuz oluşturma (search)
```bash
python main.py search --hashtags "dijitalpazarlama,girişimci" --max 200 --dry-run
python main.py search --keywords "sosyal medya uzmanı" --max 100
```

### 2) Havuzdan kampanya outreach
```bash
python main.py campaign \
  --offer "Yeni restoran otomasyon SaaS hizmeti" \
  --strategy budget \
  --budget "5.000-15.000 TL" \
  --limit 300

python main.py campaign \
  --offer "Cilt bakım ürünü" \
  --strategy sample \
  --sample-offer "Ücretsiz deneme kiti + affiliate kodu" \
  --limit 150 --dry-run
```

### 3) Reply işleme
```bash
python main.py replies
python main.py replies --dry-run
```

### 4) İzleme
```bash
python main.py stats
python main.py partners
streamlit run dashboard.py
```

## Önemli konfigürasyon
- `DAILY_EMAIL_LIMIT=1000` → günlük üst sınır.
- `EMAIL_DELAY_SECONDS` → rate limit için mailler arası bekleme.
- `GMAIL_CREDENTIALS_PATH` ve `GMAIL_TOKEN_PATH` → Gmail OAuth.
- `FIREBASE_CREDENTIALS_PATH` → Firestore cloud sync.

## Yayına hazırlık checklist
- `.env` dosyasına tüm credential/path değerlerini gir.
- Gmail OAuth ilk login’i tamamla (`gmail_token.json` oluşmalı).
- `python -m unittest discover -s tests -v` ile testleri geç.
- Önce `--dry-run` ile kampanya dene, sonra gerçek gönderime geç.
- İlk gün düşük limitle başla (örn. 100), sonra 1000’e yükselt.
