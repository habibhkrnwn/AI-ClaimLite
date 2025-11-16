# 🚀 Quick Deployment Guide

## Local Development

```bash
# Clone repository
git clone https://github.com/habibhkrnwn/AI-ClaimLite.git
cd AI-ClaimLite

# Setup environment files
cp core_engine/.env.example core_engine/.env
cp web/.env.example web/.env

# Edit .env files with your settings
nano core_engine/.env  # Add your OPENAI_API_KEY
nano web/.env          # Update VITE_API_URL if needed

# Deploy with script
chmod +x deploy.sh
./deploy.sh dev

# Or manually
docker compose up -d --build
```

**Access:**
- Frontend: http://localhost:5173
- Backend: http://localhost:3001
- Core Engine: http://localhost:8000

---

## VPS Production Deployment

### Prerequisites on VPS:
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose (if not included)
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

### Deploy Steps:

```bash
# 1. SSH to VPS
ssh root@103.179.56.158

# 2. Clone repository
cd /opt
git clone https://github.com/habibhkrnwn/AI-ClaimLite.git aiclaimlite
cd aiclaimlite

# 3. Setup environment files
cp core_engine/.env.example core_engine/.env
cp web/.env.example web/.env

# Edit with your actual values
nano core_engine/.env
# Update: OPENAI_API_KEY

nano web/.env
# Update: VITE_API_URL=http://YOUR_VPS_IP:3001

# 4. Deploy
chmod +x deploy.sh
./deploy.sh prod

# Or manually
docker compose -f docker-compose.prod.yml up -d --build
```

**Access:**
- Frontend: http://YOUR_VPS_IP (port 80)
- Backend: http://YOUR_VPS_IP:3001
- Core Engine: http://YOUR_VPS_IP:8000

---

## Environment Variables

### Core Engine (.env)
```bash
DATABASE_URL=postgresql://postgres:user@103.179.56.158:5434/aiclaimlite
OPENAI_API_KEY=sk-proj-YOUR-KEY
```

### Web (.env)
```bash
VITE_API_URL=http://YOUR_VPS_IP:3001
DATABASE_URL=postgresql://postgres:user@103.179.56.158:5434/aiclaimlite
JWT_SECRET=YOUR-SECRET-KEY
CORE_ENGINE_URL=http://core_engine:8000
```

---

## Useful Commands

```bash
# View logs
docker compose logs -f
docker compose logs -f core_engine

# Restart services
docker compose restart

# Stop services
docker compose down

# Debug
chmod +x debug.sh
./debug.sh

# Check status
docker compose ps

# Rebuild specific service
docker compose up -d --build core_engine
```

---

## Troubleshooting

### Container keeps restarting:
```bash
# Check logs
docker compose logs web_backend --tail=50
docker compose logs core_engine --tail=50

# Check health
curl http://localhost:8000/health
curl http://localhost:3001/api/health
```

### Cannot connect to database:
```bash
# Test connection from container
docker compose exec core_engine python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://postgres:user@103.179.56.158:5434/aiclaimlite')
conn = engine.connect()
print('OK')
"
```

### Port already in use:
```bash
# Find and stop conflicting process
sudo lsof -i :8000
sudo kill -9 PID

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Change host port
```

---

## File Structure

```
AI-ClaimLite/
├── core_engine/          # Python FastAPI backend
│   ├── Dockerfile
│   ├── .env
│   └── main.py
├── web/                  # Node.js + React frontend
│   ├── Dockerfile        # Frontend build
│   ├── server/Dockerfile # Backend API
│   ├── nginx.conf
│   └── .env
├── docker-compose.yml    # Development
├── docker-compose.prod.yml # Production
├── deploy.sh             # Deployment script
└── debug.sh              # Debug script
```

---

## Security Notes (Production)

1. **Change default credentials:**
   - JWT_SECRET
   - Database password
   - Admin password

2. **Enable firewall:**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

3. **SSL Certificate (recommended):**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

4. **Regular updates:**
```bash
cd /opt/aiclaimlite
git pull
./deploy.sh prod
```

---

For detailed guide, see: [VPS_DEPLOYMENT_GUIDE.md](VPS_DEPLOYMENT_GUIDE.md)
