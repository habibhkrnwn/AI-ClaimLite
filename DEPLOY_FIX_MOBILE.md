# 🔧 Fix Mobile "Failed to Fetch" - Deploy Guide

## 📋 Perubahan yang Dilakukan

### 1. **CORS Configuration** (Nginx + Backend)
- ✅ Tambah CORS headers di Nginx untuk preflight requests
- ✅ Allow all origins dan methods di backend Express
- ✅ Handle OPTIONS request dengan benar

### 2. **Debug Logging**
- ✅ Console log API configuration saat app load
- ✅ Log setiap API request (URL, method, auth status)
- ✅ Detailed error logging untuk network issues

### 3. **Error Handling**
- ✅ Deteksi TypeError fetch = network/CORS issue
- ✅ User-friendly error messages dalam Bahasa Indonesia

---

## 🚀 Deployment ke VPS (103.179.56.158)

### Step 1: SSH ke VPS
```bash
ssh root@103.179.56.158
# atau dengan user lain sesuai setup Anda
```

### Step 2: Pull Latest Code
```bash
cd ~/aiclaimlite  # atau path project Anda
git pull origin Production-V1
```

### Step 3: Stop Container (DATABASE AMAN!)
```bash
sudo docker compose -f docker-compose.prod.yml down
```

### Step 4: Rebuild Images (No Cache)
**PENTING**: Rebuild **web_frontend** dan **web_backend** karena ada perubahan konfigurasi

```bash
# Rebuild semua dengan --no-cache untuk memastikan perubahan diterapkan
sudo docker compose -f docker-compose.prod.yml build --no-cache

# Atau rebuild per service:
sudo docker compose -f docker-compose.prod.yml build --no-cache web_frontend
sudo docker compose -f docker-compose.prod.yml build --no-cache web_backend
sudo docker compose -f docker-compose.prod.yml build core_engine
```

### Step 5: Start Containers
```bash
sudo docker compose -f docker-compose.prod.yml up -d
```

### Step 6: Verify Containers
```bash
# Cek status containers
sudo docker compose -f docker-compose.prod.yml ps

# Cek logs jika ada masalah
sudo docker compose -f docker-compose.prod.yml logs -f web_frontend
sudo docker compose -f docker-compose.prod.yml logs -f web_backend
```

---

## 🧪 Testing dari HP

### 1. **Clear Browser Cache di HP**
#### Chrome:
1. Buka `chrome://settings/privacy`
2. "Clear browsing data"
3. Pilih "All time"
4. Centang "Cached images and files"
5. Clear data

#### Firefox:
1. Menu → Settings → Privacy & Security
2. "Clear data"
3. Pilih "Cache"
4. Clear

### 2. **Test Login**
1. Buka browser di HP
2. Akses: `http://103.179.56.158`
3. **Buka Developer Console** (jika bisa):
   - Chrome: Menu → More tools → Developer tools → Console
   - Firefox: Menu → Developer tools → Console
4. **Lihat log console** untuk debug info:
   ```
   🔧 API Configuration: { VITE_API_URL: "...", API_BASE_URL: "..." }
   🌐 API Request: { endpoint: "/api/auth/login", url: "...", method: "POST" }
   ```
5. Login dengan: `admin@rumahsakit.id` / password Anda

### 3. **Jika Masih Error**
Screenshoot atau catat error di console, kemudian kirim ke saya:
- Error message lengkap
- URL yang dicoba diakses
- API_BASE_URL value dari console log

---

## 🔍 Troubleshooting

### Error: "Failed to fetch"
**Penyebab**: Network/CORS issue atau backend tidak bisa diakses

**Solusi**:
```bash
# Cek apakah backend bisa diakses dari dalam container
sudo docker exec aiclaimlite-web-frontend-prod wget -O- http://aiclaimlite-web-backend-prod:3001/api/health

# Cek logs backend
sudo docker logs aiclaimlite-web-backend-prod

# Cek nginx access log
sudo docker exec aiclaimlite-web-frontend-prod cat /var/log/nginx/access.log
```

### Error: "Network error when attempting to fetch resource"
**Penyebab**: CORS blocking atau SSL/TLS issue

**Solusi**:
1. Pastikan rebuild frontend dengan `--no-cache`
2. Clear browser cache di HP
3. Coba akses langsung health endpoint: `http://103.179.56.158/api/health`

### Frontend tidak update setelah rebuild
**Penyebab**: Browser cache atau build cache

**Solusi**:
```bash
# Hapus semua images dan rebuild dari awal
sudo docker compose -f docker-compose.prod.yml down --rmi all
sudo docker compose -f docker-compose.prod.yml build --no-cache
sudo docker compose -f docker-compose.prod.yml up -d
```

---

## 📊 Verifikasi Perubahan

### 1. Cek Environment Variable Masuk ke Build
```bash
# Exec ke container frontend
sudo docker exec -it aiclaimlite-web-frontend-prod sh

# Cek file index.html (VITE_API_URL akan di-inject saat build)
grep -r "103.179.56.158" /usr/share/nginx/html/assets/
```

### 2. Test API Endpoint dari Luar
```bash
# Dari laptop atau HP (gunakan termux/curl)
curl -v http://103.179.56.158/api/health

# Expected response:
# HTTP/1.1 200 OK
# {"success":true,"message":"API Server is running","timestamp":"..."}
```

### 3. Test CORS Headers
```bash
curl -v -X OPTIONS http://103.179.56.158/api/auth/login \
  -H "Origin: http://103.179.56.158" \
  -H "Access-Control-Request-Method: POST"

# Expected headers di response:
# Access-Control-Allow-Origin: *
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
```

---

## ⚠️ PENTING: Database AMAN

**Semua perintah di atas TIDAK akan menghapus database** karena:
- ✅ Database PostgreSQL di **server eksternal** (103.179.56.158:5434)
- ✅ Tidak ada volume database di `docker-compose.prod.yml`
- ✅ Tidak menggunakan flag `-v` atau `--volumes`

**Yang akan dihapus/rebuild:**
- Container images (aplikasi)
- Container logs
- Temporary cache

**Yang TETAP ADA:**
- Database (PostgreSQL di VPS)
- User accounts
- Analysis history
- Semua data aplikasi

---

## 📝 Next Steps After Deploy

1. ✅ Test login dari HP (Chrome & Firefox)
2. ✅ Kirim screenshot console log jika masih error
3. ✅ Test dari jaringan berbeda (WiFi lain, mobile data)
4. ✅ Verify analysis features masih berfungsi

---

## 🆘 Support

Jika masih ada masalah setelah deploy, kirimkan:
1. Screenshot error di HP (dengan console terbuka)
2. Output dari: `sudo docker compose -f docker-compose.prod.yml logs web_backend`
3. Output dari: `curl -v http://103.179.56.158/api/health`
