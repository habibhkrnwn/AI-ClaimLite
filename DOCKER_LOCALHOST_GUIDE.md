# 🚀 Panduan Menjalankan AI-ClaimLite di Localhost

## 📋 Prasyarat

Pastikan sudah terinstall:
- ✅ Docker Desktop (atau Docker Engine + Docker Compose)
- ✅ Git (opsional, untuk clone repository)

## 🎯 Cara Menjalankan dengan Docker (RECOMMENDED)

### Option 1: Menggunakan Script Otomatis (Paling Mudah!)

```bash
# 1. Jalankan semua container
./docker-start.sh

# 2. Lihat logs (opsional)
./docker-logs.sh

# 3. Stop semua container
./docker-stop.sh
```

### Option 2: Manual dengan Docker Compose

```bash
# Build dan jalankan semua container
docker-compose up --build -d

# Lihat status container
docker-compose ps

# Lihat logs
docker-compose logs -f

# Stop semua container
docker-compose down
```

## 🌐 Akses Aplikasi

Setelah container berjalan, akses:

- **Frontend (UI)**: http://localhost:5173
- **Backend API**: http://localhost:3001
- **Core Engine**: http://localhost:8000

### Test Endpoints:

```bash
# Test Core Engine
curl http://localhost:8000/health

# Test Backend API
curl http://localhost:3001/api/health
```

## 🔧 Konfigurasi untuk Docker

File `.env` sudah dikonfigurasi untuk mode Docker:

**`/web/.env`**:
```env
DEPLOYMENT_MODE=docker
CORE_ENGINE_URL=http://core_engine:8000  # Menggunakan nama service Docker
VITE_API_URL=http://localhost:3001
```

**`/core_engine/.env`**:
```env
DATABASE_URL=postgresql://postgres:user@103.179.56.158:5434/aiclaimlite
APP_HOST=0.0.0.0
APP_PORT=8000
```

## 🐛 Troubleshooting

### Container tidak start?

```bash
# Check Docker status
docker info

# Check logs untuk error
docker-compose logs

# Restart ulang
docker-compose down
docker-compose up --build -d
```

### Port sudah digunakan?

Jika port 5173, 3001, atau 8000 sudah digunakan, stop aplikasi yang menggunakan port tersebut:

```bash
# Check port yang digunakan
sudo lsof -i :5173
sudo lsof -i :3001
sudo lsof -i :8000

# Atau ubah port di docker-compose.yml
```

### Container restart terus-menerus?

```bash
# Check logs untuk error spesifik
docker-compose logs core_engine
docker-compose logs web_backend
docker-compose logs web_frontend
```

### Database connection error?

Pastikan:
- ✅ VPS PostgreSQL accessible dari network Anda
- ✅ Firewall tidak block port 5434
- ✅ Credentials di `.env` benar

Test koneksi:
```bash
psql -h 103.179.56.158 -p 5434 -U postgres -d aiclaimlite
```

## 📊 Docker Commands Berguna

```bash
# Lihat container yang berjalan
docker-compose ps

# Stop semua container
docker-compose down

# Restart satu container
docker-compose restart core_engine

# Rebuild satu container
docker-compose up --build -d core_engine

# Hapus semua dan rebuild dari awal
docker-compose down -v
docker-compose up --build -d

# Masuk ke container untuk debug
docker exec -it aiclaimlite-core-engine bash
docker exec -it aiclaimlite-web-backend sh
docker exec -it aiclaimlite-web-frontend sh

# Lihat logs real-time
docker-compose logs -f

# Lihat logs satu service
docker-compose logs -f core_engine
```

## 🔄 Development Workflow

### Setelah Update Code:

```bash
# Jika update core_engine
docker-compose restart core_engine

# Jika update web backend
docker-compose restart web_backend

# Jika update web frontend
docker-compose restart web_frontend

# Jika perlu rebuild (install package baru, dll)
docker-compose up --build -d
```

### Hot Reload:

- ✅ **Frontend**: Auto hot-reload (Vite)
- ✅ **Backend**: Auto-reload via nodemon (jika configured)
- ⚠️ **Core Engine**: Perlu manual restart

## 🧹 Cleanup

```bash
# Stop dan hapus container
docker-compose down

# Hapus container + volumes
docker-compose down -v

# Hapus semua (termasuk images)
docker-compose down --rmi all -v
```

## 📝 File Penting

```
AI-ClaimLite/
├── docker-compose.yml          # Konfigurasi multi-container
├── docker-start.sh             # Script start otomatis ✨
├── docker-stop.sh              # Script stop otomatis ✨
├── docker-logs.sh              # Script lihat logs ✨
├── web/
│   ├── .env                    # Config web (PENTING!)
│   ├── Dockerfile.backend      # Backend container
│   └── Dockerfile.frontend     # Frontend container
└── core_engine/
    ├── .env                    # Config core engine (PENTING!)
    └── Dockerfile              # Core engine container
```

## 🎯 Quick Start (Copy-Paste)

```bash
# Clone project (jika belum)
git clone <your-repo-url>
cd AI-ClaimLite

# Jalankan semua
./docker-start.sh

# Buka browser
# http://localhost:5173

# Selesai! 🎉
```

## 💡 Tips

1. **Gunakan `docker-start.sh`** untuk kemudahan
2. **Check logs** jika ada error: `./docker-logs.sh`
3. **Restart individual container** jika perlu: `docker-compose restart <service>`
4. **Database external** (VPS) - pastikan accessible
5. **Development mode** - code changes di volume akan auto-sync

## 🆘 Butuh Bantuan?

Check:
1. Docker logs: `./docker-logs.sh`
2. Container status: `docker-compose ps`
3. Health endpoints: `curl http://localhost:8000/health`

Happy coding! 🚀
