# 🎯 Influencer Hunter Bot — Google Stack

Instagram influencer bulma, Gmail ile otomatik outreach, Firebase partner havuzu ve Streamlit dashboard.

## Mimari

```
Instagram (Apify)
  ↓
Profil Filtresi + AI Skorlama (Vertex AI / Gemini)
  ↓
Email çıkarımı (bio/website)
  ↓
Gmail API → outreach email gönderimi
  ↓
Gmail API → gelen yanıtları okuma + AI analiz + otomatik dönüş
  ↓
Firebase Firestore (cloud sync) + lokal SQLite cache
  ↓
Streamlit Dashboard
```

## Neden bu sürüm?
- ✅ Hunter/SendGrid kaldırıldı.
- ✅ Tamamen Google altyapısı (Gmail + Firebase + Vertex).
- ✅ Firestore ile bulut senkron.
- ✅ Dashboard eklendi.

## Kurulum

```bash
pip install -r requirements.txt
cp env.example .env
```

### Gerekli API ve kimlikler
1. **Apify Token** (instagram scraping için)
2. **Google Cloud Project** (Vertex AI + Gmail API)
3. **Firebase service account JSON**
4. **Gmail OAuth credentials JSON**

## Kullanım

### Arama / Outreach
```bash
python main.py search --hashtags "dijitalpazarlama,girişimci" --max 30
python main.py search --keywords "sosyal medya uzmanı" --max 20 --dry-run
```

### Gelen yanıtları işle
```bash
python main.py replies
python main.py replies --dry-run
```

### Havuz çıktıları
```bash
python main.py stats
python main.py partners
```

### Dashboard
```bash
streamlit run dashboard.py
```

## Maliyet (en düşük senaryo)
- Gmail API: ücretsiz kota içinde
- Firestore: Spark plan (küçük hacimde ücretsiz)
- Vertex AI: çok düşük trafikle ücretsiz krediler + düşük maliyet
- Apify: ücretsiz kredi bitince ücretli olabilir

> Gerçekten “maliyetsiz” için: düşük günlük istek, düşük email hacmi, sıkı cron planı önerilir.
