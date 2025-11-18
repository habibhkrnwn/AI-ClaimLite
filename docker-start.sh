#!/bin/bash

# ============================================================
# 🚀 AI-ClaimLite Docker Startup Script
# ============================================================
# Script ini untuk menjalankan semua container dengan Docker Compose
# ============================================================

echo "🚀 Starting AI-ClaimLite with Docker Compose..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "   Please start Docker first."
    exit 1
fi

# Check if docker-compose exists
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose not found!"
    echo "   Please install docker-compose first."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

echo ""
echo "🏗️  Building and starting containers..."
echo "   This may take a few minutes on first run..."
echo ""

# Build and start all containers
docker-compose up --build -d

# Wait for containers to be ready
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check container status
echo ""
echo "📊 Container Status:"
docker-compose ps

# Show logs from all containers
echo ""
echo "📋 Container Logs (last 20 lines):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker-compose logs --tail=20

echo ""
echo "✅ AI-ClaimLite is now running!"
echo ""
echo "🌐 Access URLs:"
echo "   Frontend:     http://localhost:5173"
echo "   Backend API:  http://localhost:3001"
echo "   Core Engine:  http://localhost:8000"
echo ""
echo "📝 Useful Commands:"
echo "   View logs:        docker-compose logs -f"
echo "   Stop containers:  docker-compose down"
echo "   Restart:          docker-compose restart"
echo ""
echo "🔍 To check health status:"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:3001/api/health"
echo ""
