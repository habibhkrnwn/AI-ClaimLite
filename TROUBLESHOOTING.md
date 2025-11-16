# 🔧 Troubleshooting Guide - AI-ClaimLite

## ❌ Error: "Failed to analyze claim"

### Penyebab Umum & Solusi

---

### 1️⃣ **Timeout Error** (⏱️ Paling Sering)

**Gejala:**
- Error muncul setelah 1-5 menit
- Message: "Analisis memakan waktu terlalu lama"
- Error code: `ECONNABORTED` atau `504`

**Penyebab:**
- OpenAI API sedang lambat (server mereka sibuk)
- Core engine sedang memproses banyak request
- Data input terlalu kompleks
- Koneksi internet tidak stabil

**Solusi:**

✅ **Solusi Cepat (Recommended):**
```bash
# 1. Tunggu 10-30 detik
# 2. Klik "Generate AI Analysis" lagi
# 3. Biasanya request ke-2 lebih cepat karena cache
```

✅ **Jika Masih Timeout:**
```bash
# 1. Restart core_engine
cd /home/shunkazama/Documents/Kerja/AI-ClaimLite/core_engine
sudo docker-compose restart core_engine

# 2. Atau restart manual
sudo pkill -f "python main.py"
python main.py &
```

✅ **Cek Status Core Engine:**
```bash
# Test endpoint health
curl http://localhost:8000/health

# Jika tidak response, restart core_engine
```

✅ **Simplify Input Data:**
```
# Daripada:
Diagnosis: Pneumonia bakterial berat dengan sepsis dan ARDS
Tindakan: Intubasi, ventilator mekanik, kultur darah, AGD serial, foto thorax serial
Obat: Meropenem 1g IV 3x, Levofloxacin 750mg IV 1x, Dexamethasone 4mg...

# Lebih baik:
Diagnosis: Pneumonia bakterial
Tindakan: Ventilator, Foto thorax
Obat: Meropenem 1g, Levofloxacin 750mg
```

---

### 2️⃣ **Core Engine Tidak Berjalan** (🔌)

**Gejala:**
- Error langsung muncul (<1 detik)
- Message: "Tidak dapat terhubung ke Core Engine"
- Error code: `ECONNREFUSED`

**Solusi:**

```bash
# 1. Cek apakah core_engine berjalan
ps aux | grep "python main.py"

# 2. Jika tidak ada, jalankan core_engine
cd /home/shunkazama/Documents/Kerja/AI-ClaimLite/core_engine
python main.py &

# 3. Atau gunakan Docker
sudo docker-compose up -d core_engine

# 4. Verify core_engine running
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"AI-CLAIM Lite",...}
```

---

### 3️⃣ **OpenAI API Key Invalid** (🔑)

**Gejala:**
- Error: "OpenAI API error"
- Response mencantumkan "invalid API key"

**Solusi:**

```bash
# 1. Cek .env file
cd /home/shunkazama/Documents/Kerja/AI-ClaimLite/core_engine
cat .env | grep OPENAI_API_KEY

# 2. Pastikan API key valid
# Format: sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 3. Update API key jika perlu
nano .env
# Tambahkan/Update: OPENAI_API_KEY=sk-proj-your-key-here

# 4. Restart core_engine
sudo pkill -f "python main.py"
python main.py &
```

---

### 4️⃣ **Limit AI Habis** (📊)

**Gejala:**
- Error: "Limit penggunaan AI harian Anda sudah habis"
- Status code: 429

**Solusi:**

```bash
# 1. Tunggu hingga hari berikutnya (reset otomatis jam 00:00)

# 2. Atau hubungi Admin Meta untuk reset manual
# Admin Meta dapat menambah limit melalui dashboard

# 3. Cek usage saat ini
# Di UI: Lihat "AI Usage Today" indicator di dashboard
```

---

### 5️⃣ **Database Connection Error** (💾)

**Gejala:**
- Error: "Database connection failed"
- Tidak bisa save history

**Solusi:**

```bash
# 1. Cek PostgreSQL running
sudo systemctl status postgresql
# Atau jika pakai Docker:
sudo docker ps | grep postgres

# 2. Test database connection
cd /home/shunkazama/Documents/Kerja/AI-ClaimLite/core_engine
python -c "from database_connection import engine; engine.connect()"

# 3. Cek DATABASE_URL di .env
cat .env | grep DATABASE_URL
# Format: postgresql://user:password@localhost:5432/dbname

# 4. Restart database jika perlu
sudo systemctl restart postgresql
# Atau Docker:
sudo docker-compose restart db
```

---

## 🚀 Performance Optimization

### Mempercepat Analisis

**1. Gunakan Data Sederhana:**
```
✅ GOOD (Fast):
Diagnosis: Pneumonia
Tindakan: Foto thorax
Obat: Ceftriaxone 1g

❌ BAD (Slow):
Diagnosis: Pneumonia bakterial berat dengan komplikasi ARDS dan sepsis
Tindakan: Intubasi dengan ventilator mekanik, kultur darah aerob anaerob, AGD serial setiap 6 jam, foto thorax AP/PA serial, pemeriksaan elektrolit lengkap
Obat: Meropenem 1g IV 3x sehari, Levofloxacin 750mg IV 1x sehari, Dexamethasone 4mg IV 2x sehari, Norepinephrine drip, Propofol sedasi
```

**2. Pilih Kode ICD Spesifik:**
- Pilih kode ICD-10 dan ICD-9 yang paling tepat
- Jangan biarkan sistem auto-detect jika Anda sudah tahu kode nya

**3. Cache Warming:**
```bash
# Request pertama selalu lambat (8-12 detik)
# Request berikutnya dengan data sama lebih cepat (0.5-1 detik)
# Manfaatkan cache dengan menggunakan data yang mirip
```

---

## 📋 Quick Diagnostic Checklist

Jika ada error, cek dalam urutan ini:

```bash
# 1. Core Engine Running?
curl http://localhost:8000/health
✅ OK: {"status":"healthy"...}
❌ Error: Restart core_engine

# 2. Backend Running?
curl http://localhost:3001/api/auth/me
✅ OK: Response apapun (walau 401)
❌ Error: Restart backend (npm run dev)

# 3. Database Running?
sudo systemctl status postgresql
✅ OK: Active (running)
❌ Error: sudo systemctl start postgresql

# 4. OpenAI API Key Valid?
cd core_engine && cat .env | grep OPENAI_API_KEY
✅ OK: sk-proj-...
❌ Error: Update .env dengan key valid

# 5. Internet Connection?
ping api.openai.com
✅ OK: Response received
❌ Error: Cek koneksi internet
```

---

## 🔍 Log Locations

**Backend Logs:**
```bash
# Terminal output dari npm run dev
cd /home/shunkazama/Documents/Kerja/AI-ClaimLite/web
npm run dev
# Lihat output di terminal
```

**Core Engine Logs:**
```bash
# File log
cat /home/shunkazama/Documents/Kerja/AI-ClaimLite/core_engine/logs/app.log

# Live log
tail -f /home/shunkazama/Documents/Kerja/AI-ClaimLite/core_engine/logs/app.log
```

**Browser Console:**
```
1. Buka browser DevTools (F12)
2. Tab "Console"
3. Lihat error messages
4. Screenshot untuk bug report
```

---

## 🆘 Masih Error?

### Restart Semua Layanan

```bash
# 1. Stop semua
cd /home/shunkazama/Documents/Kerja/AI-ClaimLite
sudo pkill -f "python main.py"
sudo pkill -f "node.*vite"

# 2. Start core_engine
cd core_engine
python main.py > logs/core.log 2>&1 &

# 3. Wait 5 seconds
sleep 5

# 4. Test core_engine
curl http://localhost:8000/health

# 5. Start backend
cd ../web
npm run dev > logs/backend.log 2>&1 &

# 6. Wait 10 seconds
sleep 10

# 7. Open browser
# http://localhost:5173
```

---

## 📞 Contact Support

Jika masih mengalami masalah setelah mengikuti semua langkah di atas:

1. **Kumpulkan informasi:**
   - Screenshot error di browser
   - Log dari core_engine: `cat core_engine/logs/app.log | tail -50`
   - Log dari backend (terminal output)
   - Diagnostic checklist results

2. **Kirim ke:**
   - Email: support@ai-claimlite.com
   - WhatsApp: +62-XXX-XXXX-XXXX
   - Telegram: @aiclaimlite_support

---

## ✅ Preventive Maintenance

### Daily Checks
```bash
# 1. Cek services running
curl http://localhost:8000/health
curl http://localhost:3001/api/auth/me

# 2. Cek disk space
df -h

# 3. Cek logs untuk errors
tail -100 core_engine/logs/app.log | grep -i error
```

### Weekly Maintenance
```bash
# 1. Clear old logs
find core_engine/logs -name "*.log" -mtime +7 -delete

# 2. Clear analysis cache
curl -X POST http://localhost:8000/api/lite/cache/clear

# 3. Restart services
sudo pkill -f "python main.py"
python main.py &
```

---

**Last Updated:** November 15, 2025  
**Version:** 1.0
