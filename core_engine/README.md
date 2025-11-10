# 🏥 AI-CLAIM Lite Core Engine

Core engine untuk AI-CLAIM Lite dengan PostgreSQL eksternal.

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env dengan konfigurasi Anda
nano .env
```

**Minimal configuration:**
```env
DATABASE_URL=postgresql://postgres:password@host:port/database
OPENAI_API_KEY=sk-your-key-here
SECRET_KEY=generate-with-openssl-rand-hex-32
```

### 2. Start Service

```bash
# Build dan start
docker-compose up -d

# Check logs
docker-compose logs -f core_engine

# Verify
curl http://localhost:8003/health
```

---

## 🌐 Access

- **API:** http://localhost:8003
- **API Docs:** http://localhost:8003/docs
- **Health Check:** http://localhost:8003/health

---

## 📋 API Endpoints

### Analyze Single Claim
```bash
POST /api/lite/analyze/single
Content-Type: application/json

{
  "mode": "text",
  "input_text": "Pneumonia berat, Ceftriaxone injeksi"
}
```

### Analyze Batch
```bash
POST /api/lite/analyze/batch
Content-Type: application/json

{
  "batch_data": [
    {
      "Nama": "Ahmad S.",
      "Diagnosis": "Pneumonia",
      "Tindakan": "Nebulisasi",
      "Obat": "Ceftriaxone"
    }
  ]
}
```

---

## 🛠️ Common Commands

```bash
# Start service
docker-compose up -d

# Stop service
docker-compose down

# View logs
docker-compose logs -f core_engine

# Restart service
docker-compose restart core_engine

# Rebuild
docker-compose build --no-cache
docker-compose up -d

# Execute command in container
docker-compose exec core_engine bash
```

---

## 📁 Project Structure

```
core_engine/
├── services/              # Business logic
│   ├── lite_service.py
│   ├── analyze_diagnosis_service.py
│   ├── rules_loader.py
│   └── ...
├── rules/                 # JSON rules files
├── logs/                  # Application logs
├── temp/                  # Temporary files
├── main.py               # FastAPI entry point
├── config.py             # Configuration
├── models.py             # Database models
├── database_connection.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env
```

---

## 🔧 Configuration

### Database (PostgreSQL)
```env
DATABASE_URL=postgresql://user:password@host:port/database
```

### OpenAI
```env
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini
```

### Port
```env
APP_PORT=8003
```

---

## 🐛 Troubleshooting

### Container won't start
```bash
docker-compose logs core_engine
docker-compose build --no-cache
```

### Database connection error
```bash
# Test connection
docker-compose exec core_engine python -c "from database_connection import engine; print(engine.connect())"
```

### Port already in use
```bash
# Change port in .env
APP_PORT=8004

# Or stop conflicting service
sudo lsof -i :8003
```

---

## 📊 Monitoring

```bash
# Container stats
docker stats ai_claim_core_engine

# Health check
curl http://localhost:8003/health

# Logs
docker-compose logs --tail=100 -f core_engine
```

---

**Version:** 1.0.0  
**Port:** 8003  
**Database:** PostgreSQL (External)
