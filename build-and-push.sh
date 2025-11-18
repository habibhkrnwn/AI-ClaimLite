#!/bin/bash

# ============================================================
# 🚀 AI-ClaimLite - Build & Push to Docker Hub
# ============================================================
# Script untuk build images di laptop dan push ke Docker Hub
# Usage: ./build-and-push.sh
# ============================================================

set -e  # Exit on error

echo "🚀 Starting AI-ClaimLite Build & Push Process..."
echo ""

# ============================================================
# 1. Login to Docker Hub
# ============================================================
echo "🔐 Step 1: Login to Docker Hub..."
docker login

# ============================================================
# 2. Build All Images
# ============================================================
echo ""
echo "🏗️  Step 2: Building Docker images..."
echo ""

# Build dengan docker-compose (otomatis tag dengan image name yang ada di docker-compose.yml)
docker compose build --no-cache

echo ""
echo "✅ Build complete!"

# ============================================================
# 3. Tag Images (already tagged by docker-compose.yml)
# ============================================================
echo ""
echo "🏷️  Step 3: Images tagged:"
docker images | grep aiclaimlite

# ============================================================
# 4. Push to Docker Hub
# ============================================================
echo ""
echo "📤 Step 4: Pushing images to Docker Hub..."
echo ""

docker push habibhkrnwn/aiclaimlite-core:latest
docker push habibhkrnwn/aiclaimlite-backend:latest
docker push habibhkrnwn/aiclaimlite-frontend:latest

# ============================================================
# 5. Summary
# ============================================================
echo ""
echo "✅ ============================================================"
echo "✅ ALL IMAGES PUSHED SUCCESSFULLY!"
echo "✅ ============================================================"
echo ""
echo "📦 Images di Docker Hub:"
echo "   - habibhkrnwn/aiclaimlite-core:latest"
echo "   - habibhkrnwn/aiclaimlite-backend:latest"
echo "   - habibhkrnwn/aiclaimlite-frontend:latest"
echo ""
echo "📋 Next Steps di VPS:"
echo "   1. Copy docker-compose.prod.yml ke VPS"
echo "   2. Copy .env.production files ke VPS"
echo "   3. Run: docker compose -f docker-compose.prod.yml pull"
echo "   4. Run: docker compose -f docker-compose.prod.yml up -d"
echo ""
echo "🌐 Access aplikasi di:"
echo "   http://103.179.56.158:5173"
echo ""
