# AIClaimLite - Smart Clinical Analyzer

Aplikasi web untuk analisis klaim medis dengan sistem authentication berbasis PostgreSQL.

## 🏗️ Arsitektur

```
AIClaimLite/
├── api/          # Backend API (Express.js + PostgreSQL)
└── web/          # Frontend (React + TypeScript + Vite)
```

## 🔐 Fitur Security

- ✅ Password hashing dengan bcrypt (10 salt rounds)
- ✅ JWT authentication (Access Token + Refresh Token)
- ✅ Token expiration management (24h access, 7d refresh)
- ✅ Protected routes dengan middleware authentication
- ✅ SQL injection protection dengan parameterized queries
- ✅ CORS configuration
- ✅ Session management dengan refresh token rotation
- ✅ Secure logout dengan token revocation

## 📋 Prerequisites

Pastikan sudah terinstall:
- **Node.js** (v18 atau lebih baru)
- **PostgreSQL** (v12 atau lebih baru)
- **npm** atau **yarn**

## 🚀 Setup & Installation

### 1. Clone Repository

```bash
cd d:/Kerja/AIClaimLite
```

### 2. Setup Database

#### a. Login ke PostgreSQL
```bash
psql -U postgres
```

#### b. Buat Database
```sql
CREATE DATABASE aiclaimlite;
\q
```

#### c. Run Database Migration
```bash
cd api
psql -U postgres -d aiclaimlite -f src/database/init.sql
```

### 3. Setup Backend API

```bash
cd api

# Install dependencies
npm install

# Copy environment file
cp .env.example .env
```

#### Edit file `api/.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aiclaimlite
DB_USER=postgres
DB_PASSWORD=your_postgres_password

# Generate strong random string for production!
JWT_SECRET=your_super_secret_jwt_key_change_this

PORT=3001
NODE_ENV=development

FRONTEND_URL=http://localhost:5173
```

**⚠️ PENTING:** Ganti `JWT_SECRET` dengan string random yang kuat untuk production!

#### Start Backend Server
```bash
npm run dev
```

Server akan berjalan di `http://localhost:3001`

### 4. Setup Frontend

```bash
cd web

# Install dependencies (jika belum)
npm install

# Copy environment file
cp .env.example .env
```

#### Edit file `web/.env`:
```env
VITE_API_URL=http://localhost:3001
```

### 5. Install Root Dependencies

```bash
cd d:/Kerja/AIClaimLite

# Install concurrently untuk menjalankan backend + frontend sekaligus
npm install
```

### 6. Start Aplikasi

#### Opsi 1: Single Command (Recommended) ⭐

```bash
cd d:/Kerja/AIClaimLite

# Start backend + frontend sekaligus
npm run dev
```

Atau install semua sekaligus:
```bash
npm run install:all  # Install dependencies root, api, dan web
npm run dev          # Start backend + frontend
```

#### Opsi 2: Manual (Terpisah)

**Terminal 1 - Backend:**
```bash
cd api
npm run dev
```

**Terminal 2 - Frontend:**
```bash
cd web
npm run dev
```

Frontend akan berjalan di `http://localhost:5173`  
Backend akan berjalan di `http://localhost:3001`

## 📱 Cara Menggunakan

1. **Buka browser** ke `http://localhost:5173`
2. **Register akun baru** dengan mengisi:
   - Nama lengkap
   - Email
   - Password (minimal 6 karakter)
3. Setelah registrasi berhasil, Anda akan otomatis login
4. **Gunakan aplikasi** untuk menganalisis data medis
5. **Logout** menggunakan tombol di kanan atas

## 🗄️ Database Schema

### Tabel: `users`
```sql
- id (SERIAL PRIMARY KEY)
- email (VARCHAR UNIQUE)
- password_hash (VARCHAR)
- full_name (VARCHAR)
- role (VARCHAR, default: 'user')
- is_active (BOOLEAN, default: true)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- last_login (TIMESTAMP)
```

### Tabel: `refresh_tokens`
```sql
- id (SERIAL PRIMARY KEY)
- user_id (INTEGER, FK to users)
- token (VARCHAR UNIQUE)
- expires_at (TIMESTAMP)
- created_at (TIMESTAMP)
- revoked (BOOLEAN, default: false)
```

## 🔌 API Endpoints

### Authentication

#### Register
```
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe"
}
```

#### Login
```
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:
```json
{
  "success": true,
  "message": "Login berhasil",
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": "user"
    },
    "accessToken": "jwt_token_here",
    "refreshToken": "refresh_token_here"
  }
}
```

#### Get Current User (Protected)
```
GET /api/auth/me
Authorization: Bearer <access_token>
```

#### Refresh Token
```
POST /api/auth/refresh
Content-Type: application/json

{
  "refreshToken": "refresh_token_here"
}
```

#### Logout
```
POST /api/auth/logout
Content-Type: application/json

{
  "refreshToken": "refresh_token_here"
}
```

## 🛠️ Development

### Backend
```bash
cd api
npm run dev    # Development dengan hot-reload
npm run build  # Build untuk production
npm start      # Run production build
```

### Frontend
```bash
cd web
npm run dev       # Development server
npm run build     # Build untuk production
npm run preview   # Preview production build
```

## 📦 Production Deployment

### Backend

1. Set environment variables:
   ```
   NODE_ENV=production
   JWT_SECRET=<strong_random_string>
   DB_HOST=<production_db_host>
   DB_PASSWORD=<secure_password>
   ```

2. Build dan jalankan:
   ```bash
   npm run build
   npm start
   ```

### Frontend

1. Update `VITE_API_URL` di `.env` dengan URL production API
2. Build:
   ```bash
   npm run build
   ```
3. Deploy folder `dist/` ke hosting (Netlify, Vercel, dll)

## 🔧 Troubleshooting

### Backend tidak bisa connect ke database
- Pastikan PostgreSQL sudah berjalan
- Cek credentials di `.env` sudah benar
- Pastikan database `aiclaimlite` sudah dibuat

### Token tidak valid / expired
- Access token expires dalam 24 jam
- Gunakan refresh token untuk mendapat access token baru
- Jika refresh token juga expired, user harus login ulang

### CORS Error
- Pastikan `FRONTEND_URL` di backend `.env` sesuai dengan URL frontend
- Pastikan backend server sudah berjalan

## 📄 Tech Stack

### Backend
- **Express.js** - Web framework
- **PostgreSQL** - Database
- **bcrypt** - Password hashing
- **jsonwebtoken** - JWT authentication
- **pg** - PostgreSQL client
- **TypeScript** - Type safety

### Frontend
- **React** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Lucide React** - Icons

## 📝 Notes

- Lint errors di folder `api/` akan hilang setelah `npm install`
- Aplikasi menggunakan localStorage untuk menyimpan tokens
- Refresh token disimpan di database untuk security
- Password di-hash dengan bcrypt sebelum disimpan
- Semua API routes di-protect dengan JWT authentication
