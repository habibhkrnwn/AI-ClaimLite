# 🚀 Quick Start Guide

Panduan cepat untuk menjalankan AIClaimLite - Semua dalam satu folder `web/`!

## ⚡ Langkah Cepat (3 Langkah!)

### 1. Setup Database (3 menit)

```bash
# Login ke PostgreSQL
psql -U postgres

# Buat database
CREATE DATABASE aiclaimlite;
\q

# Jalankan migration
cd d:/Kerja/AIClaimLite/web
psql -U postgres -d aiclaimlite -f server/database/init.sql
```

✅ **Selesai!** Database siap digunakan.

### 2. Install & Start (1 command!)

```bash
cd d:/Kerja/AIClaimLite/web

# Install dependencies
npm install

# Start backend + frontend sekaligus
npm run dev
```

✅ Backend berjalan di `http://localhost:3001`  
✅ Frontend berjalan di `http://localhost:5173`

**Selesai! Hanya perlu 1 folder dan 1 command!** 🎉

### 4. Test Aplikasi

1. Buka browser: `http://localhost:5173`
2. Klik **"Belum punya akun? Daftar"**
3. Isi form registrasi:
   - Nama: Test User
   - Email: test@example.com
   - Password: test123
4. Klik **Daftar**
5. Anda akan otomatis login! ✨

## 🔧 Konfigurasi

File `.env` sudah dibuat otomatis dengan konfigurasi default:

### Backend (`api/.env`)
- Database: localhost:5432/aiclaimlite
- User: postgres
- Password: postgres ← **Sesuaikan dengan password PostgreSQL Anda!**

### Frontend (`web/.env`)
- API URL: http://localhost:3001 ← Sudah di-set

## 📝 Catatan Penting

1. **Password Database**: Edit `api/.env` dan sesuaikan `DB_PASSWORD` dengan password PostgreSQL Anda
2. **JWT Secret**: Untuk production, ganti `JWT_SECRET` di `api/.env` dengan string random yang kuat
3. **Lint Errors**: Error di folder `api/` akan hilang setelah `npm install`

## 🆘 Troubleshooting

### Backend Error: "connect ECONNREFUSED"
→ PostgreSQL belum berjalan atau password salah di `.env`

### Frontend Error: "Network Error"
→ Backend belum berjalan atau API URL salah

### Database Error: "database does not exist"
→ Jalankan step 1 (CREATE DATABASE)

## ✅ Checklist

- [ ] PostgreSQL sudah terinstall dan berjalan
- [ ] Database `aiclaimlite` sudah dibuat
- [ ] Migration SQL sudah dijalankan
- [ ] Backend dependencies sudah di-install
- [ ] Backend server berjalan di port 3001
- [ ] Frontend server berjalan di port 5173
- [ ] Bisa akses `http://localhost:5173` dan melihat halaman login

## 🎉 Berhasil!

Jika semua checklist di atas ✅, aplikasi sudah siap digunakan!

Lihat `README.md` untuk dokumentasi lengkap.
