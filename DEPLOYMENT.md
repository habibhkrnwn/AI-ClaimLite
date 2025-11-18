# 🚀 AI-ClaimLite Production Deployment Guide

## 📋 Prerequisites

1. **Docker Hub Account**: `habibhkrnwn`
2. **VPS**: IP `103.179.56.158`
3. **Docker & Docker Compose** installed di VPS

---

## 🏗️ Step 1: Build & Push Images (Di Laptop)

```bash
# 1. Login ke Docker Hub
docker login

# 2. Build & Push semua images
./build-and-push.sh
```

**Images yang akan di-push:**
- `habibhkrnwn/aiclaimlite-core:latest`
- `habibhkrnwn/aiclaimlite-backend:latest`
- `habibhkrnwn/aiclaimlite-frontend:latest`

---

## 📤 Step 2: Copy Files ke VPS

```bash
# Copy production files ke VPS
scp docker-compose.prod.yml globalaimeta@103.179.56.158:~/aiclaim_lite/AI-ClaimLite/
scp deploy-vps.sh globalaimeta@103.179.56.158:~/aiclaim_lite/AI-ClaimLite/
scp core_engine/.env.production globalaimeta@103.179.56.158:~/aiclaim_lite/AI-ClaimLite/core_engine/
scp web/.env.production globalaimeta@103.179.56.158:~/aiclaim_lite/AI-ClaimLite/web/
```

---

## 🚀 Step 3: Deploy di VPS

```bash
# SSH ke VPS
ssh globalaimeta@103.179.56.158

# Masuk ke directory
cd ~/aiclaim_lite/AI-ClaimLite

# Make script executable
chmod +x deploy-vps.sh

# Deploy (pull images & run)
./deploy-vps.sh
```

---

## 🌐 Access Aplikasi

**Dari HP/Browser:**
```
http://103.179.56.158:5173
```

**API Endpoints:**
- Backend: `http://103.179.56.158:3001`
- Core Engine: `http://103.179.56.158:8000`

---

## 🔧 Useful Commands (Di VPS)

### Check Status
```bash
docker compose -f docker-compose.prod.yml ps
```

### View Logs
```bash
# All containers
docker compose -f docker-compose.prod.yml logs -f

# Specific container
docker compose -f docker-compose.prod.yml logs -f core_engine
docker compose -f docker-compose.prod.yml logs -f web_backend
docker compose -f docker-compose.prod.yml logs -f web_frontend
```

### Restart Services
```bash
# Restart all
docker compose -f docker-compose.prod.yml restart

# Restart specific service
docker compose -f docker-compose.prod.yml restart core_engine
```

### Stop Services
```bash
docker compose -f docker-compose.prod.yml down
```

### Update to Latest Version
```bash
# Pull latest images
docker compose -f docker-compose.prod.yml pull

# Restart with new images
docker compose -f docker-compose.prod.yml up -d
```

---

## 🔄 Update Process

**Di Laptop:**
```bash
# 1. Commit & push code changes
git add .
git commit -m "Update features"
git push origin Production-V2

# 2. Build & push new images
./build-and-push.sh
```

**Di VPS:**
```bash
# 1. Pull latest code (optional if only docker images changed)
git pull origin Production-V2

# 2. Deploy latest images
./deploy-vps.sh
```

---

## 🛡️ Security Checklist

- [ ] Change `JWT_SECRET` in `.env.production`
- [ ] Change database password
- [ ] Setup firewall (allow ports: 5173, 3001, 8000)
- [ ] Enable HTTPS with Nginx reverse proxy (recommended)
- [ ] Setup domain name (optional)

---

## 🐛 Troubleshooting

### Issue: Container tidak start
```bash
# Check logs
docker compose -f docker-compose.prod.yml logs

# Check container status
docker ps -a
```

### Issue: Cannot access from HP
```bash
# 1. Check firewall di VPS
sudo ufw status
sudo ufw allow 5173
sudo ufw allow 3001
sudo ufw allow 8000

# 2. Check container port binding
docker port aiclaimlite-web-frontend
```

### Issue: Database connection failed
```bash
# Test database connectivity
docker exec -it aiclaimlite-core-engine python -c "import psycopg2; conn = psycopg2.connect('postgresql://postgres:user@103.179.56.158:5434/aiclaimlite'); print('✅ Connected')"
```

---

## 📊 Resource Limits

**Current limits per container:**
- Core Engine: 1 CPU, 1GB RAM
- Web Backend: 0.5 CPU, 512MB RAM
- Web Frontend: 0.5 CPU, 512MB RAM

**Total:** ~2 CPUs, ~2GB RAM

---

## 🎯 Production Checklist

- [x] Images built & pushed to Docker Hub
- [x] Production env files created
- [x] docker-compose.prod.yml configured
- [x] Scripts created (build-and-push.sh, deploy-vps.sh)
- [x] Use VPS IP instead of localhost
- [ ] Test from HP
- [ ] Setup monitoring (optional)
- [ ] Setup backup strategy (database)
