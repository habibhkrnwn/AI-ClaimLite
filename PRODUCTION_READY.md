# ✅ AI-ClaimLite Production Setup - Complete

## 📋 Summary

Docker configuration sudah **PRODUCTION READY** dengan improvements berikut:

### ✅ 1. No Localhost - Use VPS IP
- Frontend API URL: `http://103.179.56.158:3001`
- Accessible dari HP/browser manapun

### ✅ 2. Docker Hub Integration
**Image names:**
- `habibhkrnwn/aiclaimlite-core:latest`
- `habibhkrnwn/aiclaimlite-backend:latest`
- `habibhkrnwn/aiclaimlite-frontend:latest`

### ✅ 3. Build di Laptop, Deploy di VPS

**Di Laptop (Development):**
```bash
# Build & push images
./build-and-push.sh
```

**Di VPS (Production):**
```bash
# Pull & run (no build needed!)
./deploy-vps.sh
```

---

## 🚀 Quick Start

### Step 1: Setup .env.production Files (Local)

```bash
# 1. Copy example files
cp web/.env.production.example web/.env.production
cp core_engine/.env.production.example core_engine/.env.production

# 2. Edit dengan nilai sebenarnya
nano web/.env.production
nano core_engine/.env.production
```

**Important:** `.env.production` files **TIDAK** di-commit ke Git (sudah di .gitignore)

### Step 2: Build & Push Images (Di Laptop)

```bash
# Login Docker Hub
docker login

# Build & Push
./build-and-push.sh
```

### Step 3: Deploy di VPS

```bash
# 1. Copy files ke VPS
scp docker-compose.prod.yml globalaimeta@103.179.56.158:~/aiclaim_lite/AI-ClaimLite/
scp deploy-vps.sh globalaimeta@103.179.56.158:~/aiclaim_lite/AI-ClaimLite/

# 2. SSH ke VPS
ssh globalaimeta@103.179.56.158

# 3. Setup .env.production di VPS
cd ~/aiclaim_lite/AI-ClaimLite

# Copy example files
cp web/.env.production.example web/.env.production
cp core_engine/.env.production.example core_engine/.env.production

# Edit dengan nilai sebenarnya
nano web/.env.production
nano core_engine/.env.production

# 4. Deploy
chmod +x deploy-vps.sh
./deploy-vps.sh
```

### Step 4: Access from HP

```
http://103.179.56.158:5173
```

---

## 📁 Files Created

1. **docker-compose.prod.yml** - Production compose file (no volumes, use Docker Hub images)
2. **build-and-push.sh** - Script untuk build & push images ke Docker Hub
3. **deploy-vps.sh** - Script untuk deploy di VPS (pull & run)
4. **DEPLOYMENT.md** - Full deployment guide
5. **.env.production.example** - Template untuk production env
6. **.gitignore** - Updated untuk exclude sensitive files

---

## 🔐 Security

✅ `.env.production` files **NOT in Git**
✅ OpenAI API key aman (local only)
✅ Database credentials aman (local only)
✅ Resource limits configured
✅ Healthchecks enabled

---

## 🎯 Key Benefits

### Development (Laptop)
- Build with volumes (live reload)
- Debug mode enabled
- Use localhost

### Production (VPS)
- No volumes (faster startup)
- Production mode
- Use VPS IP (accessible from HP)
- Pull images from Docker Hub (no build needed)

---

## 📊 Resource Usage

**Total:** ~2 CPUs, ~2GB RAM
- Core Engine: 1 CPU, 1GB RAM
- Web Backend: 0.5 CPU, 512MB RAM
- Web Frontend: 0.5 CPU, 512MB RAM

---

## 🔄 Update Process

**Workflow:**

1. **Development di laptop** → Commit → Push to GitHub
2. **Build images di laptop** → `./build-and-push.sh`
3. **Pull images di VPS** → `./deploy-vps.sh`

**No build needed di VPS!** ⚡

---

## ✅ Checklist

- [x] Docker compose production ready
- [x] No localhost, use VPS IP
- [x] Docker Hub integration
- [x] Build scripts created
- [x] Deploy scripts created
- [x] .gitignore updated
- [x] Security: sensitive files excluded
- [ ] **Next:** Build & push images
- [ ] **Next:** Deploy to VPS
- [ ] **Next:** Test from HP

---

## 📞 Support

Jika ada masalah, check:
- `DEPLOYMENT.md` - Full guide
- `docker-compose.prod.yml` - Production config
- Container logs: `docker compose -f docker-compose.prod.yml logs -f`
