#!/bin/bash

# ============================================================
# 🚀 AI-ClaimLite VPS - Production Deployment
# ============================================================
# Script untuk deploy di VPS (tanpa build, hanya pull & run)
# Usage: ./deploy-vps.sh
# ============================================================

set -e  # Exit on error

echo "🚀 Starting AI-ClaimLite VPS Deployment..."
echo ""

# ============================================================
# 1. Stop existing containers
# ============================================================
echo "🛑 Step 1: Stopping existing containers..."
docker compose -f docker-compose.prod.yml down || true

# ============================================================
# 2. Pull latest images from Docker Hub
# ============================================================
echo ""
echo "📥 Step 2: Pulling latest images from Docker Hub..."
docker compose -f docker-compose.prod.yml pull

# ============================================================
# 3. Start containers
# ============================================================
echo ""
echo "🚀 Step 3: Starting containers..."
docker compose -f docker-compose.prod.yml up -d

# ============================================================
# 4. Show status
# ============================================================
echo ""
echo "📊 Step 4: Container status..."
docker compose -f docker-compose.prod.yml ps

# ============================================================
# 5. Show logs
# ============================================================
echo ""
echo "📋 Step 5: Checking logs..."
sleep 5
docker compose -f docker-compose.prod.yml logs --tail=50

# ============================================================
# 6. Summary
# ============================================================
echo ""
echo "✅ ============================================================"
echo "✅ DEPLOYMENT SUCCESSFUL!"
echo "✅ ============================================================"
echo ""
echo "🌐 Access aplikasi di:"
echo "   http://103.179.56.158:5173 (dari browser/HP)"
echo ""
echo "📋 Useful commands:"
echo "   - Check logs: docker compose -f docker-compose.prod.yml logs -f"
echo "   - Restart: docker compose -f docker-compose.prod.yml restart"
echo "   - Stop: docker compose -f docker-compose.prod.yml down"
echo ""
