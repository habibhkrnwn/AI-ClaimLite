#!/bin/bash

# ============================================================
# 🛑 AI-ClaimLite Docker Stop Script
# ============================================================

echo "🛑 Stopping AI-ClaimLite containers..."
docker-compose down

echo ""
echo "✅ All containers stopped!"
echo ""
echo "📝 To start again, run:"
echo "   ./docker-start.sh"
echo ""
