# 🚀 Quick Start Guide

## 🐳 **RECOMMENDED: Jalankan dengan Docker (Sekali Klik!)**

### Opsi 1: Docker Compose (Mudah & Cepat)

```powershell
# Dari root folder AIClaimLite
docker-compose up
```

**Background mode:**
```powershell
docker-compose up -d
```

**Stop semua:**
```powershell
docker-compose down
```

✅ **Otomatis menjalankan:**
- PostgreSQL Database (port 5432)
- Core Engine Python API (port 8000)
- Web Backend Node.js (port 3001)
- Web Frontend Vite (port 5173)

📖 **Dokumentasi lengkap:** Lihat [DOCKER.md](./DOCKER.md)

---

## 🔧 **ALTERNATIF: Manual (2 Terminal Terpisah)**

### 1️⃣ Start Core Engine (Python API) - Port 8000
```bash
cd core_engine
start.bat
```
Atau manual:
```bash
cd core_engine
python main.py
```

### 2️⃣ Start Web App (Frontend + Backend) - Port 5173 & 3001
```bash
cd web
npm run dev
```

## ✅ Selesai!

- Frontend: http://localhost:5173
- Backend Node.js: http://localhost:3001  
- Core Engine API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🔍 Check Status

```bash
# Check core_engine
curl http://localhost:8000/health

# Check backend
curl http://localhost:3001/api/health
```

## ⚠️ Troubleshooting

**Error "Failed to analyze claim"**
- Pastikan core_engine sudah running di port 8000
- Check terminal core_engine untuk error log

**Port sudah digunakan**
- Core engine: Edit `APP_PORT` di `core_engine/.env`
- Backend: Edit `API_PORT` di `web/.env`

**Docker Issues**
- Lihat troubleshooting di [DOCKER.md](./DOCKER.md)
- Rebuild: `docker-compose build --no-cache`
- Reset database: `docker-compose down -v`
