# 🚀 VPS Setup Commands - Copy Paste Ready

## ⚡ SUPER QUICK SETUP (Recommended)

**Satu script, semua otomatis!**

```bash
cd ~
git clone https://github.com/habibhkrnwn/AI-ClaimLite.git
cd AI-ClaimLite
git checkout Production-V1
chmod +x setup-vps.sh
./setup-vps.sh
```

✅ **SELESAI!** Aplikasi siap di `http://103.179.56.158`

---

## 📝 File yang Perlu Disiapkan

Jika setup manual, buat 2 file `.env`:

### 1️⃣ File: `core_engine/.env`

```bash
cat > core_engine/.env << 'EOF'
DATABASE_URL=postgresql://postgres:user@103.179.56.158:5434/aiclaimlite
DB_HOST=103.179.56.158
DB_PORT=5434
DB_NAME=aiclaimlite
DB_USER=postgres
DB_PASSWORD=user
OPENAI_API_KEY=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
CACHE_TTL=43200
MAX_CACHE_SIZE=512
EOF
```

### 2️⃣ File: `web/.env`

```bash
# Generate JWT secret dulu
JWT_SECRET=$(openssl rand -base64 32)

# Buat file
cat > web/.env << EOF
VITE_API_URL=http://103.179.56.158
DATABASE_URL=postgresql://postgres:user@103.179.56.158:5434/aiclaimlite
DB_HOST=103.179.56.158
DB_PORT=5434
DB_NAME=aiclaimlite
DB_USER=postgres
DB_PASSWORD=user
JWT_SECRET=${JWT_SECRET}
API_PORT=3001
NODE_ENV=production
CORE_ENGINE_URL=http://aiclaimlite-core-engine-prod:8000
EOF

echo "JWT_SECRET yang digunakan: ${JWT_SECRET}"
```

---

## 🐳 Docker Commands

```bash
# Build & Deploy
sudo docker compose -f docker-compose.prod.yml build --no-cache
sudo docker compose -f docker-compose.prod.yml up -d

# Cek Status
sudo docker compose -f docker-compose.prod.yml ps

# Lihat Logs
sudo docker compose -f docker-compose.prod.yml logs -f
```

---

## ✅ Checklist Setelah Clone

```bash
cd ~/AI-ClaimLite

# Cek file-file penting
ls -la docker-compose.prod.yml          # ✅ Harus ada
ls -la core_engine/.env                 # ❌ Harus dibuat
ls -la web/.env                         # ❌ Harus dibuat
ls -la setup-vps.sh                     # ✅ Script otomatis
```

**Status:**
- ✅ = Sudah ada dari git
- ❌ = Harus dibuat manual (atau pakai script)

---

## 🧪 Test Deployment

```bash
# Test API
curl http://localhost/api/health

# Test Nginx  
curl http://localhost/health

# Test dari luar VPS
curl http://103.179.56.158/api/health
```

**Expected Response:**
```json
{"success":true,"message":"API Server is running","timestamp":"..."}
```

---

## 📊 Monitoring

```bash
# Status containers
sudo docker compose -f docker-compose.prod.yml ps

# Logs real-time
sudo docker compose -f docker-compose.prod.yml logs -f

# Logs specific service
sudo docker compose -f docker-compose.prod.yml logs -f web_backend

# Restart service
sudo docker compose -f docker-compose.prod.yml restart web_backend
```

---

## 🔄 Update ke Versi Baru

```bash
cd ~/AI-ClaimLite
git pull origin Production-V1
sudo docker compose -f docker-compose.prod.yml down
sudo docker compose -f docker-compose.prod.yml build --no-cache
sudo docker compose -f docker-compose.prod.yml up -d
```

---

## 🆘 Troubleshooting

### Container tidak start?
```bash
sudo docker compose -f docker-compose.prod.yml logs
```

### Database tidak bisa connect?
```bash
PGPASSWORD=user psql -h 103.179.56.158 -p 5434 -U postgres -d aiclaimlite -c "SELECT NOW();"
```

### Rebuild dari awal?
```bash
sudo docker compose -f docker-compose.prod.yml down --rmi all
sudo docker compose -f docker-compose.prod.yml build --no-cache
sudo docker compose -f docker-compose.prod.yml up -d
```
