# 🔑 Setup OpenAI API Key

## ⚠️ Penting!

Fitur **Diagnosis Primer & Sekunder** dan **AI Translation** memerlukan **OpenAI API Key** untuk berfungsi.

Tanpa API key, sistem akan error saat melakukan:
- AI parsing (extract diagnosis, tindakan, obat)
- AI translation (paru2 basah → Pneumonia)
- Multi-diagnosis detection
- Clinical consistency analysis

---

## 🚀 Cara Setup OpenAI API Key

### **Option 1: Melalui Environment Variable (Recommended)**

1. **Buat/Edit file `.env`** di root project:

```bash
cd d:\KERJA KERAS\LITE\AI-ClaimLite
notepad .env
```

2. **Tambahkan OpenAI API key:**

```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

3. **Restart containers:**

```bash
docker compose down
docker compose up -d
```

### **Option 2: Melalui config.py**

1. **Edit `core_engine/config.py`:**

```bash
cd core_engine
notepad config.py
```

2. **Tambahkan di bagian atas file:**

```python
import os

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-proj-xxxxxxxxxxxxxxxxxx")
```

3. **Restart core_engine container:**

```bash
docker compose restart core_engine
```

---

## 🧪 Verifikasi Setup

### **1. Check di container logs:**

```bash
docker logs aiclaimlite-core-engine --tail 20
```

❌ **Jika API key TIDAK ada:**
```
[OpenAI] Not available: module 'config' has no attribute 'OPENAI_API_KEY'
```

✅ **Jika API key SUDAH ada:**
```
[OpenAI] ✓ Initialized (model: gpt-4o-mini)
```

### **2. Test dengan curl:**

```bash
curl -X POST http://localhost:8000/api/lite/parse-text ^
  -H "Content-Type: application/json" ^
  -d "{\"input_text\": \"paru2 basah\"}"
```

✅ **Response sukses:**
```json
{
  "status": "success",
  "result": {
    "diagnosis": "Pneumonia",
    "tindakan": "",
    "obat": ""
  }
}
```

❌ **Response error (jika tidak ada API key):**
```json
{
  "status": "error",
  "message": "OpenAI API key not configured"
}
```

### **3. Run test suite:**

```bash
cd core_engine
python test_diagnosis_multi.py
```

---

## 📝 Mendapatkan OpenAI API Key

### **1. Buat akun OpenAI:**

https://platform.openai.com/signup

### **2. Generate API key:**

1. Login ke https://platform.openai.com/
2. Klik **API Keys** di sidebar
3. Klik **Create new secret key**
4. Copy key (format: `sk-proj-...`)

### **3. Top up balance (jika perlu):**

- Minimum $5 untuk mulai
- Model gpt-4o-mini: ~$0.0002 per analysis (sangat murah)
- $10 = ~50,000 analyses

---

## 💰 Cost Estimation

### **Per Analysis:**
- Input tokens: ~300 tokens = $0.00004
- Output tokens: ~500 tokens = $0.00030
- **Total: ~$0.00034 per analysis**

### **Monthly (1000 analyses):**
- 1000 analyses × $0.00034 = **$0.34/month**

### **Model: gpt-4o-mini**
- Input: $0.150 per 1M tokens
- Output: $0.600 per 1M tokens
- Fast, cheap, dan accurate untuk medical parsing

---

## 🔧 Troubleshooting

### **Error: "OpenAI API key not configured"**

**Solution:**
1. Check `.env` file ada dan berisi `OPENAI_API_KEY=...`
2. Restart containers: `docker compose restart`
3. Check logs: `docker logs aiclaimlite-core-engine`

### **Error: "Incorrect API key provided"**

**Solution:**
1. Verify API key di https://platform.openai.com/api-keys
2. Pastikan key format `sk-proj-...` (bukan `sk-...` yang lama)
3. Check tidak ada whitespace di awal/akhir key

### **Error: "You exceeded your current quota"**

**Solution:**
1. Top up balance di https://platform.openai.com/billing
2. Minimum $5 untuk mulai
3. Check usage di https://platform.openai.com/usage

### **Error: Rate limit exceeded**

**Solution:**
1. Tunggu 1 menit
2. Untuk production: upgrade tier di OpenAI dashboard
3. Free tier: 3 requests/minute
4. Tier 1 ($5+): 500 requests/minute

---

## 🎯 Production Checklist

- [ ] OpenAI API key sudah di-set via environment variable
- [ ] API key tersimpan di secret management (jangan hardcode)
- [ ] Balance OpenAI sudah top up (min $10 untuk production)
- [ ] Test parsing sudah sukses
- [ ] Monitoring OpenAI usage sudah di-setup
- [ ] Error handling untuk quota/rate limit sudah ada
- [ ] Backup API key di secure location

---

## 📞 Support

Jika masih ada masalah:
1. Check dokumentasi di `QUICKSTART.md`
2. Check logs: `docker logs aiclaimlite-core-engine`
3. Test health endpoint: `curl http://localhost:8000/health`

---

**Last Updated:** 2024-11-21  
**Version:** 1.0
