# 🔗 Integration Guide - AI-CLAIM Lite dengan Core Engine

## 📋 Prerequisites

Pastikan Anda sudah menginstall:
- Node.js (v18+)
- Python (v3.9+)
- PostgreSQL (untuk database)

## 🚀 Cara Menjalankan Sistem Lengkap

### 1️⃣ Setup Core Engine (Python API)

```bash
# Masuk ke folder core_engine
cd core_engine

# Install dependencies (jika belum)
pip install -r requirements.txt

# Jalankan API server (port 8000)
python main.py
# atau
uvicorn main:app --reload --port 8000
```

Server akan berjalan di `http://localhost:8000`

### 2️⃣ Setup Web Backend (Node.js)

```bash
# Masuk ke folder web
cd web

# Install dependencies
npm install

# Jalankan backend server (port 3001)
npm run dev:server
```

Backend akan berjalan di `http://localhost:3001`

### 3️⃣ Setup Web Frontend (React + Vite)

```bash
# Di folder web (terminal baru)
npm run dev:vite
```

Frontend akan berjalan di `http://localhost:5173`

### Atau jalankan keduanya sekaligus:

```bash
cd web
npm run dev
```

## 🔄 Flow Integrasi

```
Frontend (React)
    ↓
Backend Node.js (http://localhost:3001)
    ↓ POST /api/ai/analyze
Core Engine Python (http://localhost:8000)
    ↓ POST /api/lite/analyze/single
AI Analysis Service
    ↓
Response dengan hasil analisis
```

## 📡 API Endpoints

### Backend Node.js → Core Engine

**Analyze Claim**
```
POST http://localhost:3001/api/ai/analyze
Headers: Authorization: Bearer <token>
Body:
{
  "diagnosis": "Pneumonia berat (J18.9)",
  "procedure": "Nebulisasi (93.96), Rontgen Thorax",
  "medication": "Ceftriaxone injeksi 1g, Paracetamol 500mg"
}
```

**Validate Input**
```
POST http://localhost:3001/api/ai/validate
Body: sama dengan analyze
```

### Core Engine Python Endpoints

**Endpoint 1A: Analyze Single (Form Mode)**
```
POST http://localhost:8000/api/lite/analyze/single
Body:
{
  "mode": "form",
  "diagnosis": "Pneumonia berat (J18.9)",
  "tindakan": "Nebulisasi (93.96)",
  "obat": "Ceftriaxone injeksi 1g",
  "save_history": true
}
```

**Response Structure:**
```json
{
  "status": "success",
  "result": {
    "klasifikasi": {
      "diagnosis": "Pneumonia berat",
      "icd10": "J18.9",
      "tindakan": ["Nebulisasi"],
      "icd9": ["93.96"],
      "obat": ["Ceftriaxone injeksi 1g"]
    },
    "validasi_klinis": {
      "status": "Valid",
      "keterangan": "...",
      "peringatan": [],
      "saran": []
    },
    "severity": {
      "tingkat": "Severe",
      "skor": 85,
      "deskripsi": "..."
    },
    "cp_ringkas": [
      {
        "nama_tindakan": "Nebulisasi",
        "kode": "93.96",
        "tarif_ringkas": "Rp 150.000"
      }
    ],
    "checklist_dokumen": [
      {
        "nama_dokumen": "Resume Medis",
        "wajib": true,
        "status": "Lengkap"
      }
    ],
    "fornas": {
      "tingkat_kepatuhan": 100,
      "obat_sesuai": ["Ceftriaxone"],
      "obat_tidak_sesuai": [],
      "catatan": "Semua obat sesuai Fornas"
    },
    "insight_ai": "...",
    "konsistensi": {
      "diagnosis_tindakan": 95,
      "diagnosis_obat": 90,
      "skor_keseluruhan": 92,
      "catatan": []
    }
  }
}
```

## 🛠️ Troubleshooting

### Error: "ERR_CONNECTION_REFUSED" pada frontend

**Penyebab:** Backend Node.js belum berjalan

**Solusi:**
```bash
cd web
npm run dev:server
```

### Error: "Failed to fetch" atau "net::ERR_CONNECTION_REFUSED :8000"

**Penyebab:** Core Engine Python belum berjalan

**Solusi:**
```bash
cd core_engine
python main.py
```

### Error: "axios" module not found

**Solusi:**
```bash
cd web
npm install axios
```

### Port sudah digunakan

**Solusi:**
- Core Engine: Edit port di `core_engine/main.py`
- Backend: Edit `API_PORT` di `web/.env`
- Frontend: Edit port di `web/vite.config.ts`

## 📝 Environment Variables

### web/.env
```env
# Database
DB_HOST=103.179.56.158
DB_PORT=5434
DB_NAME=aiclaimlite
DB_USER=postgres
DB_PASSWORD=user

# JWT
JWT_SECRET=SupeRrahasia123!@

# Server
API_PORT=3001
NODE_ENV=development

# Core Engine
CORE_ENGINE_URL=http://localhost:8000
```

## ✅ Checklist Deployment

- [ ] Core Engine berjalan di port 8000
- [ ] Backend Node.js berjalan di port 3001
- [ ] Frontend Vite berjalan di port 5173
- [ ] Database PostgreSQL terkoneksi
- [ ] Axios terinstall di web/package.json
- [ ] Environment variables sudah diset
- [ ] Login sebagai Admin RS berhasil
- [ ] Generate AI Analysis berhasil

## 🎯 Test Flow

1. **Login** sebagai Admin RS
2. **Input Data:**
   - Diagnosis: `Pneumonia berat (J18.9)`
   - Tindakan: `Nebulisasi (93.96), Rontgen Thorax`
   - Obat: `Ceftriaxone injeksi 1g, Paracetamol 500mg`
3. **Klik** "Generate AI Insight"
4. **Verifikasi** hasil muncul di panel kanan dengan 8 cards:
   - Classification
   - Clinical Validation
   - Severity Assessment
   - CP Nasional
   - Document Checklist
   - Fornas Compliance
   - AI Insight
   - Consistency Score

## 📞 Support

Jika ada masalah, cek:
1. Console browser (F12) untuk error frontend
2. Terminal backend untuk error Node.js
3. Terminal core_engine untuk error Python
4. Network tab di browser untuk melihat request/response API

---

Happy Coding! 🚀
