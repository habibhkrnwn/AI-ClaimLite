#!/bin/bash

set -e

echo "🚀 AI-ClaimLite Deployment Script"
echo "=================================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}Warning: Not running as root. Some operations might fail.${NC}"
fi

# Get environment (dev or prod)
ENV=${1:-dev}

if [ "$ENV" = "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    echo -e "${GREEN}📦 Production mode${NC}"
else
    COMPOSE_FILE="docker-compose.yml"
    echo -e "${YELLOW}🔧 Development mode${NC}"
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    echo "Please install Docker first:"
    echo "curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed!${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 1: Stopping existing containers...${NC}"
docker compose -f $COMPOSE_FILE down || true

echo ""
echo -e "${BLUE}Step 2: Removing old images (optional)...${NC}"
read -p "Remove old Docker images? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker compose -f $COMPOSE_FILE down --rmi all || true
fi

echo ""
echo -e "${BLUE}Step 3: Building Docker images...${NC}"
docker compose -f $COMPOSE_FILE build --no-cache

echo ""
echo -e "${BLUE}Step 4: Starting services...${NC}"
docker compose -f $COMPOSE_FILE up -d

echo ""
echo -e "${BLUE}Step 5: Waiting for services to be healthy...${NC}"
sleep 15

echo ""
echo -e "${BLUE}Step 6: Checking container status...${NC}"
docker compose -f $COMPOSE_FILE ps

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
if [ "$ENV" = "prod" ]; then
    echo "  Frontend: http://YOUR_VPS_IP"
    echo "  Backend API: http://YOUR_VPS_IP:3001/api"
    echo "  Core Engine: http://YOUR_VPS_IP:8000"
else
    echo "  Frontend: http://localhost:5173"
    echo "  Backend API: http://localhost:3001/api"
    echo "  Core Engine: http://localhost:8000"
fi
echo ""
echo -e "${YELLOW}View logs: docker compose -f $COMPOSE_FILE logs -f${NC}"
echo -e "${YELLOW}Stop services: docker compose -f $COMPOSE_FILE down${NC}"
echo ""
