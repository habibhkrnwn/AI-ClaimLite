# 🐳 Docker Setup untuk AI-ClaimLite

Dokumentasi untuk menjalankan seluruh aplikasi AI-ClaimLite menggunakan Docker Compose.

## 📋 Prerequisites

Pastikan sudah terinstall:
- Docker Desktop (Windows/Mac) atau Docker Engine (Linux)
- Docker Compose (biasanya sudah include di Docker Desktop)

## 🚀 Quick Start

### 1. Jalankan Semua Services Sekaligus

```powershell
# Dari root folder AIClaimLite
docker-compose up
```

**Atau jika ingin running di background:**
```powershell
docker-compose up -d
```

### 2. Stop Semua Services

```powershell
docker-compose down
```

### 3. Stop dan Hapus Volumes (Reset Database)

```powershell
docker-compose down -v
```

## 🔧 Services yang Berjalan

Setelah `docker-compose up`, services berikut akan berjalan:

| Service | Port | URL | Deskripsi |
|---------|------|-----|-----------|
| **PostgreSQL** | 5432 | `localhost:5432` | Database server |
| **Core Engine** | 8000 | http://localhost:8000 | Python FastAPI (AI Engine) |
| **Web Backend** | 3001 | http://localhost:3001 | Node.js Express API |
| **Web Frontend** | 5173 | http://localhost:5173 | React + Vite UI |

## 📊 Health Checks

Cek apakah services sudah ready:

```powershell
# Core Engine
curl http://localhost:8000/health

# Web Backend
curl http://localhost:3001/api/health

# Web Frontend
# Buka browser: http://localhost:5173
```

## 🛠️ Development Commands

### Rebuild Services (jika ada perubahan code)

```powershell
# Rebuild semua services
docker-compose up --build

# Rebuild service tertentu
docker-compose up --build core_engine
docker-compose up --build web_backend
docker-compose up --build web_frontend
```

### Lihat Logs

```powershell
# Semua services
docker-compose logs -f

# Service tertentu
docker-compose logs -f core_engine
docker-compose logs -f web_backend
docker-compose logs -f web_frontend
docker-compose logs -f postgres
```

### Restart Service Tertentu

```powershell
docker-compose restart core_engine
docker-compose restart web_backend
docker-compose restart web_frontend
```

### Masuk ke Container (Debug)

```powershell
# Core Engine (Python)
docker-compose exec core_engine sh

# Web Backend (Node.js)
docker-compose exec web_backend sh

# Web Frontend (Node.js)
docker-compose exec web_frontend sh

# PostgreSQL
docker-compose exec postgres psql -U postgres -d aiclaimlite
```

## 📁 Volume Mapping

Services menggunakan volume mounting untuk development:

- `./core_engine` → `/app` (Core Engine)
- `./web` → `/app` (Web Backend & Frontend)
- `postgres_data` → PostgreSQL data (persistent)

**Keuntungan:** Perubahan code langsung reflected tanpa rebuild!

## ⚙️ Environment Variables

Edit file `docker-compose.yml` untuk mengubah konfigurasi:

### Core Engine
- `PYTHONUNBUFFERED=1` - Output langsung ke console

### Web Backend
- `NODE_ENV=development`
- `DATABASE_URL` - PostgreSQL connection string
- `API_PORT=3001`
- `JWT_SECRET` - Secret key untuk JWT (ganti di production!)
- `CORE_ENGINE_URL=http://core_engine:8000`

### Web Frontend
- `VITE_API_URL=http://localhost:3001`

## 🔄 Development Workflow

### Workflow Standar (dengan Docker)

```powershell
# 1. Start semua services
docker-compose up -d

# 2. Lihat logs untuk monitoring
docker-compose logs -f

# 3. Develop seperti biasa
# - Edit code di /web atau /core_engine
# - Vite auto-reload untuk frontend
# - Nodemon auto-reload untuk backend (jika dikonfigurasi)
# - Uvicorn auto-reload untuk core_engine

# 4. Stop services saat selesai
docker-compose down
```

### Workflow Tanpa Docker (Manual)

Jika ingin run secara terpisah seperti biasa:

```powershell
# Terminal 1 - Core Engine
cd core_engine
python main.py

# Terminal 2 - Web Backend + Frontend
cd web
npm run dev
```

## 🐛 Troubleshooting

### Port Sudah Digunakan

```powershell
# Cek port yang digunakan
netstat -ano | findstr :8000
netstat -ano | findstr :3001
netstat -ano | findstr :5173
netstat -ano | findstr :5432

# Stop process yang menggunakan port tersebut
taskkill /PID <PID> /F
```

### Container Tidak Start

```powershell
# Lihat error logs
docker-compose logs core_engine
docker-compose logs web_backend
docker-compose logs web_frontend

# Rebuild dari scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Database Connection Error

```powershell
# Pastikan PostgreSQL sudah ready
docker-compose logs postgres

# Recreate database
docker-compose down -v
docker-compose up -d postgres
# Wait beberapa detik
docker-compose up web_backend web_frontend core_engine
```

### Node Modules / Python Packages Tidak Ter-install

```powershell
# Rebuild container
docker-compose down
docker-compose build --no-cache web_backend
docker-compose up web_backend
```

## 📝 Notes

1. **First Run:** Database akan otomatis ter-initialize dengan `init.sql`
2. **Hot Reload:** Frontend (Vite) support hot reload by default
3. **Backend Reload:** Tambahkan nodemon di package.json jika perlu auto-reload
4. **Production:** Jangan lupa ganti `JWT_SECRET` dan `JWT_REFRESH_SECRET`!

## 🎯 Recommended Workflow

**Development:**
```powershell
docker-compose up -d  # Background mode
docker-compose logs -f  # Monitor logs
```

**Production:**
- Gunakan `docker-compose.prod.yml` terpisah
- Build production images
- Gunakan environment variables dari file `.env`
- Setup reverse proxy (Nginx)

---

**Happy Coding! 🚀**
