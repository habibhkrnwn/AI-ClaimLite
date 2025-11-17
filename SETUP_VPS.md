# 🚀 Setup VPS dari Awal (Fresh Clone)

## 📋 Prerequisites

1. VPS dengan Docker & Docker Compose installed
2. PostgreSQL database sudah running di `103.179.56.158:5434`
3. Git installed
4. Port 80 terbuka untuk HTTP

---

## 🔧 Step 1: Clone Repository

```bash
# SSH ke VPS
ssh root@103.179.56.158

# Clone repository
cd ~
git clone https://github.com/habibhkrnwn/AI-ClaimLite.git
cd AI-ClaimLite

# Checkout production branch
git checkout Production-V1
```

---

## 📝 Step 2: Buat File Environment (.env)

### 2.1 Core Engine Environment

```bash
# Buat file .env untuk core_engine
nano core_engine/.env
```

**Isi dengan:**
```env
# Database Configuration
DATABASE_URL=postgresql://postgres:user@103.179.56.158:5434/aiclaimlite
DB_HOST=103.179.56.158
DB_PORT=5434
DB_NAME=aiclaimlite
DB_USER=postgres
DB_PASSWORD=user

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Cache Configuration
CACHE_TTL=43200
MAX_CACHE_SIZE=512
```

**Simpan:** `Ctrl + O`, `Enter`, `Ctrl + X`

---

### 2.2 Web Backend & Frontend Environment

```bash
# Buat file .env untuk web
nano web/.env
```

**Isi dengan:**
```env
# Frontend API URL (tanpa port, semua lewat Nginx port 80)
VITE_API_URL=http://103.179.56.158

# Database Configuration (VPS PostgreSQL)
DATABASE_URL=postgresql://postgres:user@103.179.56.158:5434/aiclaimlite
DB_HOST=103.179.56.158
DB_PORT=5434
DB_NAME=aiclaimlite
DB_USER=postgres
DB_PASSWORD=user

# JWT Secret (GANTI dengan random string yang aman!)
JWT_SECRET=SupeRrahasia123!@#$%^&*()

# Server Configuration
API_PORT=3001
NODE_ENV=production

# Core Engine URL (gunakan container name untuk Docker)
CORE_ENGINE_URL=http://aiclaimlite-core-engine-prod:8000
```

**Simpan:** `Ctrl + O`, `Enter`, `Ctrl + X`

---

## 🔐 Step 3: Ganti JWT Secret (PENTING!)

**Generate JWT secret yang aman:**

```bash
# Generate random string untuk JWT_SECRET
openssl rand -base64 32
```

**Copy output** (contoh: `xK9mP2nQ5rT8wV1yZ4aC7bD0eF3gH6iJ9kL2mN5oP8qR1sT4uV7wX0yZ3aB6cD9e`)

**Edit file .env:**
```bash
nano web/.env
```

**Ganti baris:**
```env
JWT_SECRET=xK9mP2nQ5rT8wV1yZ4aC7bD0eF3gH6iJ9kL2mN5oP8qR1sT4uV7wX0yZ3aB6cD9e
```

---

## 🗄️ Step 4: Setup Database (Jika Belum Ada)

### 4.1 Cek Koneksi Database

```bash
# Install psql client jika belum ada
sudo apt update
sudo apt install postgresql-client -y

# Test koneksi
psql -h 103.179.56.158 -p 5434 -U postgres -d aiclaimlite -c "SELECT NOW();"
# Password: user
```

### 4.2 Run Database Migrations

```bash
# Jika database kosong, run init.sql
psql -h 103.179.56.158 -p 5434 -U postgres -d aiclaimlite -f web/database/init.sql
# Password: user

# Run migrations (jika ada)
# Migrations ada di: web/database/migrations/
ls -la web/database/migrations/
```

### 4.3 Tambah ICD Indexes (Untuk Performa)

```bash
# Run SQL untuk create indexes
psql -h 103.179.56.158 -p 5434 -U postgres -d aiclaimlite -f core_engine/add_icd9_indexes.sql
# Password: user
```

---

## 🐳 Step 5: Build & Deploy Docker Containers

### 5.1 Cek Docker Compose File

```bash
# Pastikan menggunakan docker-compose.prod.yml
cat docker-compose.prod.yml
```

### 5.2 Build Images

```bash
# Build semua images dengan --no-cache
sudo docker compose -f docker-compose.prod.yml build --no-cache
```

**Expected output:**
```
[+] Building ...
 => [core_engine] ...
 => [web_backend] ...
 => [web_frontend] ...
```

### 5.3 Start Containers

```bash
# Start dalam detached mode
sudo docker compose -f docker-compose.prod.yml up -d
```

### 5.4 Verify Containers Running

```bash
# Cek status containers
sudo docker compose -f docker-compose.prod.yml ps

# Expected output:
# NAME                              STATUS              PORTS
# aiclaimlite-core-engine-prod      Up (healthy)        
# aiclaimlite-web-backend-prod      Up (healthy)        
# aiclaimlite-web-frontend-prod     Up                  0.0.0.0:80->80/tcp
```

---

## 🧪 Step 6: Testing

### 6.1 Test Health Endpoints

```bash
# Test dari VPS
curl http://localhost:80/api/health
# Expected: {"success":true,"message":"API Server is running",...}

curl http://localhost:80/health
# Expected: OK
```

### 6.2 Test dari Browser

**Dari laptop/HP:**
1. Buka browser
2. Akses: `http://103.179.56.158`
3. Seharusnya muncul halaman login

### 6.3 Test Login

**Default Admin Meta:**
- Email: `admin@jombang.go.id` (atau sesuai database Anda)
- Password: sesuai yang di-hash di database

---

## 📊 Step 7: Monitoring & Troubleshooting

### 7.1 View Logs

```bash
# Logs semua services
sudo docker compose -f docker-compose.prod.yml logs -f

# Logs specific service
sudo docker compose -f docker-compose.prod.yml logs -f web_frontend
sudo docker compose -f docker-compose.prod.yml logs -f web_backend
sudo docker compose -f docker-compose.prod.yml logs -f core_engine
```

### 7.2 Restart Containers

```bash
# Restart semua
sudo docker compose -f docker-compose.prod.yml restart

# Restart specific service
sudo docker compose -f docker-compose.prod.yml restart web_backend
```

### 7.3 Rebuild & Redeploy

```bash
# Stop containers
sudo docker compose -f docker-compose.prod.yml down

# Rebuild (jika ada perubahan)
sudo docker compose -f docker-compose.prod.yml build --no-cache

# Start ulang
sudo docker compose -f docker-compose.prod.yml up -d
```

---

## 🔍 Common Issues & Solutions

### Issue 1: Container tidak healthy

**Cek logs:**
```bash
sudo docker compose -f docker-compose.prod.yml logs web_backend
```

**Kemungkinan penyebab:**
- Database tidak bisa diakses
- Environment variables salah
- Port sudah digunakan

**Solusi:**
- Cek DATABASE_URL di `.env`
- Test koneksi database dengan `psql`
- Cek port dengan `sudo netstat -tlnp | grep :80`

### Issue 2: Failed to fetch di mobile

**Penyebab:**
- Frontend tidak rebuild setelah ubah VITE_API_URL
- Browser cache

**Solusi:**
```bash
# Rebuild frontend dengan --no-cache
sudo docker compose -f docker-compose.prod.yml build --no-cache web_frontend
sudo docker compose -f docker-compose.prod.yml up -d

# Clear browser cache di HP
```

### Issue 3: CORS Error

**Cek nginx config:**
```bash
sudo docker exec aiclaimlite-web-frontend-prod cat /etc/nginx/conf.d/default.conf
```

**Seharusnya ada:**
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: ...`

### Issue 4: Database connection failed

**Test dari container:**
```bash
# Exec ke backend container
sudo docker exec -it aiclaimlite-web-backend-prod sh

# Test koneksi dari dalam container
apk add postgresql-client
psql -h 103.179.56.158 -p 5434 -U postgres -d aiclaimlite -c "SELECT NOW();"
```

---

## 📝 Checklist Setup

- [ ] Clone repository
- [ ] Checkout branch Production-V1
- [ ] Buat `core_engine/.env`
- [ ] Buat `web/.env`
- [ ] Ganti JWT_SECRET dengan random string
- [ ] Test koneksi database
- [ ] Run database init.sql
- [ ] Run ICD indexes SQL
- [ ] Build Docker images
- [ ] Start containers
- [ ] Verify containers healthy
- [ ] Test health endpoints
- [ ] Test login dari browser

---

## 🆘 Need Help?

**Jika masih ada masalah, kirimkan:**

1. Output dari:
   ```bash
   sudo docker compose -f docker-compose.prod.yml ps
   ```

2. Logs dari container yang error:
   ```bash
   sudo docker compose -f docker-compose.prod.yml logs --tail=50 [service_name]
   ```

3. Screenshot error di browser (dengan console terbuka)

---

## 🔄 Update ke Versi Terbaru

```bash
# Pull latest code
cd ~/AI-ClaimLite
git pull origin Production-V1

# Rebuild & restart
sudo docker compose -f docker-compose.prod.yml down
sudo docker compose -f docker-compose.prod.yml build --no-cache
sudo docker compose -f docker-compose.prod.yml up -d
```
