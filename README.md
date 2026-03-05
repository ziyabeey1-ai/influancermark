# 🎯 Influencer Hunter Bot — yzt.digital

Vertex AI (Gemini) destekli Instagram influencer arama, email outreach ve işbirliği havuzu yönetim sistemi.

---

## Mimari

```
Instagram (Apify)
       ↓
  Profil Filtresi (takipçi aralığı)
       ↓
  Vertex AI / Gemini  →  Alaka Skoru + Niche Tespiti
       ↓
  Hunter.io           →  Email Bulma (bio + domain)
       ↓
  Vertex AI / Gemini  →  Kişiselleştirilmiş Email Üretimi
       ↓
  SendGrid            →  Email Gönderme
       ↓
  Gmail API           →  Yanıt Okuma
       ↓
  Vertex AI / Gemini  →  Yanıt Analizi + Otomatik Cevap
       ↓
  SQLite              →  Partner Havuzu
```

---

## Kurulum

### 1. Gereksinimler
```bash
pip install -r requirements.txt
```

### 2. .env dosyasını oluştur
```bash
cp .env.example .env
# .env dosyasını düzenle, API anahtarlarını gir
```

### 3. API Anahtarları

| Servis | Nereden alınır | Ücretsiz plan |
|--------|---------------|---------------|
| **Apify** | console.apify.com/account/integrations | $5 free kredi |
| **Vertex AI** | console.cloud.google.com → IAM → Service Account | $300 free kredi |
| **Hunter.io** | hunter.io/api-keys | 25 arama/ay |
| **SendGrid** | app.sendgrid.com/settings/api_keys | 100 email/gün |
| **Gmail API** | Aşağıya bak | Ücretsiz |

### 4. Vertex AI kurulumu
```bash
# Google Cloud SDK kur
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# Vertex AI API'yi etkinleştir
gcloud services enable aiplatform.googleapis.com
```

### 5. Gmail API kurulumu
1. Google Cloud Console → APIs → Gmail API → Etkinleştir
2. OAuth2 credentials oluştur (Desktop App)
3. `credentials.json` dosyasını `data/` klasörüne koy
4. İlk çalıştırmada tarayıcı açılır, izin ver → `data/gmail_token.json` otomatik oluşur

---

## Kullanım

### Hashtag ile arama
```bash
python main.py search --hashtags "dijitalpazarlama,girişimci,esnafsosyal" --max 100
```

### Keyword ile arama
```bash
python main.py search --keywords "sosyal medya uzmanı istanbul,küçük işletme sahibi" --max 50
```

### Önce test et (email gönderme)
```bash
python main.py search --hashtags "dijitalpazarlama" --max 10 --dry-run
```

### Yanıtları işle
```bash
python main.py replies          # Gerçek mod (otomatik yanıt gönderir)
python main.py replies --dry-run # Sadece logla
```

### İstatistikler
```bash
python main.py stats
python main.py partners
```

### Otomatik zamanlayıcı (7/24)
```bash
python scheduler.py
# Arka planda çalıştırmak için:
nohup python scheduler.py > logs/scheduler.log 2>&1 &
```

---

## Veritabanı

`data/influencer_pool.db` — SQLite

| Tablo | İçerik |
|-------|--------|
| `influencers` | Tüm profiller, skorlar, emailler, status |
| `email_log` | Gönderilen/alınan tüm emailler |
| `search_sessions` | Arama geçmişi |

**Status akışı:**
`discovered` → `emailed` → `replied` → `partner` / `rejected`

---

## Tahmini Maliyetler (aylık)

| Servis | Plan | Maliyet |
|--------|------|---------|
| Apify | Starter | ~$49/ay (100K istek) |
| Vertex AI (Gemini Flash) | Kullanım bazlı | ~$5-15/ay |
| Hunter.io | Starter | $49/ay (500 arama) |
| SendGrid | Free | $0 (100/gün) |
| Gmail API | Free | $0 |
| **TOPLAM** | | **~$103-113/ay** |

---

## Dosya Yapısı

```
influencer_hunter/
├── main.py              # CLI ve ana pipeline
├── scheduler.py         # Otomatik zamanlayıcı
├── config.py            # Konfigürasyon
├── requirements.txt
├── .env.example
├── modules/
│   ├── database.py      # SQLite yönetimi
│   ├── instagram_scraper.py  # Apify entegrasyonu
│   ├── ai_engine.py     # Vertex AI (Gemini)
│   ├── email_module.py  # Hunter.io + SendGrid
│   └── reply_handler.py # Gmail API yanıt yönetimi
├── data/
│   ├── influencer_pool.db    # SQLite (otomatik oluşur)
│   ├── gmail_credentials.json # Manuel koy
│   └── gmail_token.json      # Otomatik oluşur
└── logs/
```
