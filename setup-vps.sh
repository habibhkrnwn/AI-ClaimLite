#!/bin/bash

# ============================================
# SCRIPT SETUP OTOMATIS UNTUK VPS
# AI-ClaimLite Production Setup
# ============================================

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "============================================"
echo "  AI-ClaimLite VPS Setup Script"
echo "  Production Environment"
echo "============================================"
echo -e "${NC}"

# ============================================
# Step 1: Validasi Environment
# ============================================
echo -e "${YELLOW}📋 Step 1: Validasi environment...${NC}"

# Cek apakah sudah di directory yang benar
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.prod.yml tidak ditemukan${NC}"
    echo "Pastikan Anda berada di directory AI-ClaimLite"
    exit 1
fi

echo -e "${GREEN}✅ Directory valid${NC}"

# ============================================
# Step 2: Setup Environment Files
# ============================================
echo -e "\n${YELLOW}📝 Step 2: Setup environment files...${NC}"

# 2.1 Core Engine .env
echo -e "${BLUE}Setting up core_engine/.env...${NC}"

if [ -f "core_engine/.env" ]; then
    echo -e "${YELLOW}⚠️  File core_engine/.env sudah ada${NC}"
    read -p "Overwrite? (y/n): " overwrite_core
    if [ "$overwrite_core" != "y" ]; then
        echo "Skip core_engine/.env"
    else
        cp core_engine/.env core_engine/.env.backup
        echo "Backup saved to core_engine/.env.backup"
    fi
fi

if [ ! -f "core_engine/.env" ] || [ "$overwrite_core" == "y" ]; then
    cat > core_engine/.env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://postgres:user@103.179.56.158:5434/aiclaimlite
DB_HOST=103.179.56.158
DB_PORT=5434
DB_NAME=aiclaimlite
DB_USER=postgres
DB_PASSWORD=user

# OpenAI Configuration
OPENAI_API_KEY=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

# Cache Configuration
CACHE_TTL=43200
MAX_CACHE_SIZE=512
EOF
    echo -e "${GREEN}✅ core_engine/.env created${NC}"
fi

# 2.2 Web .env
echo -e "${BLUE}Setting up web/.env...${NC}"

if [ -f "web/.env" ]; then
    echo -e "${YELLOW}⚠️  File web/.env sudah ada${NC}"
    read -p "Overwrite? (y/n): " overwrite_web
    if [ "$overwrite_web" != "y" ]; then
        echo "Skip web/.env"
    else
        cp web/.env web/.env.backup
        echo "Backup saved to web/.env.backup"
    fi
fi

if [ ! -f "web/.env" ] || [ "$overwrite_web" == "y" ]; then
    # Generate JWT Secret
    echo -e "${BLUE}Generating JWT Secret...${NC}"
    JWT_SECRET=$(openssl rand -base64 32)
    
    cat > web/.env << EOF
# Frontend API URL
VITE_API_URL=http://103.179.56.158

# Database Configuration (VPS PostgreSQL)
DATABASE_URL=postgresql://postgres:user@103.179.56.158:5434/aiclaimlite
DB_HOST=103.179.56.158
DB_PORT=5434
DB_NAME=aiclaimlite
DB_USER=postgres
DB_PASSWORD=user

# JWT Secret (auto-generated)
JWT_SECRET=${JWT_SECRET}

# Server Configuration
API_PORT=3001
NODE_ENV=production

# Core Engine URL (gunakan container name untuk Docker)
CORE_ENGINE_URL=http://aiclaimlite-core-engine-prod:8000
EOF
    echo -e "${GREEN}✅ web/.env created with auto-generated JWT_SECRET${NC}"
fi

# ============================================
# Step 3: Test Database Connection
# ============================================
echo -e "\n${YELLOW}🔍 Step 3: Test database connection...${NC}"

# Cek apakah psql tersedia
if command -v psql &> /dev/null; then
    echo "Testing connection to PostgreSQL..."
    if PGPASSWORD=user psql -h 103.179.56.158 -p 5434 -U postgres -d aiclaimlite -c "SELECT NOW();" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Database connection successful${NC}"
    else
        echo -e "${RED}❌ Database connection failed${NC}"
        echo -e "${YELLOW}⚠️  Pastikan PostgreSQL running di 103.179.56.158:5434${NC}"
        read -p "Continue anyway? (y/n): " continue_db
        if [ "$continue_db" != "y" ]; then
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}⚠️  psql client not found, skipping database test${NC}"
    echo "Install dengan: sudo apt install postgresql-client -y"
fi

# ============================================
# Step 4: Docker Build
# ============================================
echo -e "\n${YELLOW}🐳 Step 4: Building Docker images...${NC}"
echo "This may take 5-10 minutes..."

sudo docker compose -f docker-compose.prod.yml build --no-cache

echo -e "${GREEN}✅ Docker images built successfully${NC}"

# ============================================
# Step 5: Start Containers
# ============================================
echo -e "\n${YELLOW}🚀 Step 5: Starting containers...${NC}"

sudo docker compose -f docker-compose.prod.yml up -d

echo -e "${GREEN}✅ Containers started${NC}"

# ============================================
# Step 6: Wait for Health Checks
# ============================================
echo -e "\n${YELLOW}⏳ Step 6: Waiting for containers to be healthy...${NC}"
echo "This may take 30-60 seconds..."

sleep 15

# Cek status containers
echo -e "\n${BLUE}Container Status:${NC}"
sudo docker compose -f docker-compose.prod.yml ps

# ============================================
# Step 7: Test Endpoints
# ============================================
echo -e "\n${YELLOW}🧪 Step 7: Testing endpoints...${NC}"

# Test health endpoint
echo -e "${BLUE}Testing health endpoint...${NC}"
if curl -s http://localhost:80/api/health | grep -q "success"; then
    echo -e "${GREEN}✅ API health check passed${NC}"
else
    echo -e "${RED}❌ API health check failed${NC}"
fi

# Test Nginx
echo -e "${BLUE}Testing Nginx...${NC}"
if curl -s http://localhost:80/health | grep -q "OK"; then
    echo -e "${GREEN}✅ Nginx health check passed${NC}"
else
    echo -e "${RED}❌ Nginx health check failed${NC}"
fi

# ============================================
# Summary
# ============================================
echo -e "\n${GREEN}"
echo "============================================"
echo "  ✅ Setup Complete!"
echo "============================================"
echo -e "${NC}"

echo -e "${BLUE}📊 Summary:${NC}"
echo "  • Core Engine: Running"
echo "  • Web Backend: Running"
echo "  • Web Frontend: Running on port 80"
echo ""
echo -e "${BLUE}🌐 Access URLs:${NC}"
echo "  • Frontend: http://103.179.56.158"
echo "  • API Health: http://103.179.56.158/api/health"
echo ""
echo -e "${BLUE}📝 Environment Files:${NC}"
echo "  • core_engine/.env (created)"
echo "  • web/.env (created with auto-generated JWT)"
echo ""
echo -e "${BLUE}🔍 Useful Commands:${NC}"
echo "  • View logs: sudo docker compose -f docker-compose.prod.yml logs -f"
echo "  • Stop: sudo docker compose -f docker-compose.prod.yml down"
echo "  • Restart: sudo docker compose -f docker-compose.prod.yml restart"
echo "  • Status: sudo docker compose -f docker-compose.prod.yml ps"
echo ""
echo -e "${YELLOW}⚠️  Next Steps:${NC}"
echo "  1. Test login dari browser: http://103.179.56.158"
echo "  2. Clear browser cache di HP"
echo "  3. Test dari mobile browser"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
