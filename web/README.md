# AIClaimLite - All-in-One Setup

Semua backend dan frontend sekarang dalam satu folder `web/` - tinggal satu command!

## 🚀 Quick Start

### 1. Setup Database

```bash
# Buat database
psql -U postgres
CREATE DATABASE aiclaimlite;
\q

# Jalankan migration
cd d:/Kerja/AIClaimLite/web
psql -U postgres -d aiclaimlite -f server/database/init.sql
```

### 2. Install Dependencies & Start

```bash
cd d:/Kerja/AIClaimLite/web

# Install dependencies
npm install

# Start everything (backend + frontend)
npm run dev
```

**Selesai!** Aplikasi berjalan di:
- 🎨 Frontend: http://localhost:5173
- 🔌 Backend API: http://localhost:3001

## 📁 Struktur Folder

```
web/
├── src/              # Frontend React code
├── server/           # Backend Express API
│   ├── config/       # Database & JWT config
│   ├── services/     # Business logic
│   ├── middleware/   # Auth middleware
│   ├── routes/       # API routes
│   └── database/     # SQL migrations
├── package.json      # Dependencies & scripts
└── .env              # Config (frontend + backend)
```

## ⚙️ Configuration

Edit `.env` untuk menyesuaikan database password:

```env
VITE_API_URL=http://localhost:3001

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aiclaimlite
DB_USER=postgres
DB_PASSWORD=postgres  # ← Sesuaikan ini!

# JWT Secret
JWT_SECRET=your_secret_key

# Server
API_PORT=3001
NODE_ENV=development
```

## 📜 Available Scripts

```bash
npm run dev          # Start backend + frontend
npm run dev:server   # Start backend saja
npm run dev:vite     # Start frontend saja
npm run build        # Build untuk production
npm run preview      # Preview production build
```

## 🔐 Security Features

- ✅ Password hashing dengan bcrypt
- ✅ JWT authentication (access + refresh tokens)
- ✅ Protected routes
- ✅ SQL injection protection
- ✅ CORS configuration

## 📝 Notes

- Lint errors akan hilang setelah `npm install`
- Backend dan frontend berjalan bersamaan dengan satu command
- Database migration ada di `server/database/init.sql`
- Semua dependencies (frontend + backend) ada di satu `package.json`
