#!/bin/bash

# ============================================================
# 📋 AI-ClaimLite Docker Logs Viewer
# ============================================================

if [ -z "$1" ]; then
    echo "📋 Showing logs from all containers..."
    echo "   (Press Ctrl+C to stop)"
    echo ""
    docker-compose logs -f
else
    echo "📋 Showing logs from: $1"
    echo "   (Press Ctrl+C to stop)"
    echo ""
    docker-compose logs -f "$1"
fi
