#!/bin/bash

echo "🔍 AI-ClaimLite Debug Information"
echo "=================================="
echo ""

# Check if docker compose file exists
if [ -f "docker-compose.yml" ]; then
    COMPOSE_FILE="docker-compose.yml"
elif [ -f "docker-compose.prod.yml" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
else
    echo "❌ No docker-compose file found!"
    exit 1
fi

echo "📦 Using: $COMPOSE_FILE"
echo ""

echo "📦 Docker Containers Status:"
docker compose -f $COMPOSE_FILE ps
echo ""

echo "📊 Container Resource Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}"
echo ""

echo "🔍 Recent Logs (Core Engine):"
echo "----------------------------"
docker compose -f $COMPOSE_FILE logs --tail=20 core_engine 2>/dev/null || echo "Container not running"
echo ""

echo "🔍 Recent Logs (Web Backend):"
echo "----------------------------"
docker compose -f $COMPOSE_FILE logs --tail=20 web_backend 2>/dev/null || echo "Container not running"
echo ""

echo "🔍 Recent Logs (Web Frontend):"
echo "----------------------------"
docker compose -f $COMPOSE_FILE logs --tail=20 web_frontend 2>/dev/null || echo "Container not running"
echo ""

echo "🌐 Health Check Endpoints:"
echo "-------------------------"
echo -n "Core Engine: "
curl -s http://localhost:8000/health 2>/dev/null && echo " ✅ OK" || echo " ❌ FAILED"
echo -n "Web Backend: "
curl -s http://localhost:3001/api/health 2>/dev/null && echo " ✅ OK" || echo " ❌ FAILED"
echo ""

echo "🔧 Environment Variables Check:"
echo "------------------------------"
echo "Core Engine:"
docker compose -f $COMPOSE_FILE exec core_engine env 2>/dev/null | grep -E "(OPENAI|DATABASE|DB_)" || echo "Container not running"
echo ""
echo "Web Backend:"
docker compose -f $COMPOSE_FILE exec web_backend env 2>/dev/null | grep -E "(DATABASE|DB_|NODE_ENV|API_PORT)" || echo "Container not running"
echo ""

echo "💾 Disk Usage:"
echo "-------------"
docker system df
echo ""

echo "🔗 Network Information:"
echo "----------------------"
docker network ls | grep aiclaimlite || echo "Network not found"
echo ""
