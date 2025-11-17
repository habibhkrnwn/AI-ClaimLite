#!/bin/bash

# ====================================
# SAFE DEPLOYMENT SCRIPT
# Database AMAN - Tidak akan terhapus
# ====================================

set -e  # Exit on error

echo "🚀 Starting SAFE deployment to VPS..."
echo "⚠️  Database will NOT be affected (PostgreSQL di 103.179.56.158:5434)"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ====================================
# 1. Git Push ke GitHub
# ====================================
echo -e "${YELLOW}📦 Step 1: Pushing to GitHub...${NC}"
git add .
git commit -m "Fix mobile access - use VITE_API_URL from env" || echo "No changes to commit"
git push origin Production-V1

echo -e "${GREEN}✅ Pushed to GitHub${NC}"
echo ""

# ====================================
# 2. Deploy ke VPS
# ====================================
echo -e "${YELLOW}🌐 Step 2: Connecting to VPS and deploying...${NC}"

# Ganti dengan kredensial VPS Anda
VPS_USER="root"  # atau user lain
VPS_HOST="103.179.56.158"
PROJECT_DIR="~/aiclaimlite"  # sesuaikan path di VPS

ssh ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
  set -e
  
  echo "📂 Navigating to project directory..."
  cd ~/aiclaimlite
  
  echo "⬇️  Pulling latest code from GitHub..."
  git pull origin Production-V1
  
  echo "🛑 Stopping containers (DATABASE TETAP AMAN)..."
  sudo docker compose -f docker-compose.prod.yml down
  
  echo "🔨 Building fresh images (no cache untuk frontend)..."
  sudo docker compose -f docker-compose.prod.yml build --no-cache web_frontend
  sudo docker compose -f docker-compose.prod.yml build web_backend
  sudo docker compose -f docker-compose.prod.yml build core_engine
  
  echo "🚀 Starting containers..."
  sudo docker compose -f docker-compose.prod.yml up -d
  
  echo "⏳ Waiting for containers to be healthy..."
  sleep 10
  
  echo "📊 Container status:"
  sudo docker compose -f docker-compose.prod.yml ps
  
  echo ""
  echo "✅ Deployment complete!"
  echo "🌐 Access at: http://103.179.56.158"
  echo "📱 Test dari HP sekarang!"
ENDSSH

echo ""
echo -e "${GREEN}🎉 Deployment finished successfully!${NC}"
echo -e "${GREEN}Test login dari HP di: http://103.179.56.158${NC}"
