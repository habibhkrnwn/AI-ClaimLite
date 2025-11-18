#!/bin/bash

# Quick Test for "paru-paru basah" translation fix

echo "=========================================="
echo "🧪 Testing Translation Service Fix"
echo "=========================================="
echo ""

# Test endpoint
CORE_ENGINE_URL="http://localhost:8000"

echo "📍 Testing Core Engine Health..."
curl -s $CORE_ENGINE_URL/health | jq '.' || echo "❌ Core engine not responding"

echo ""
echo "=========================================="
echo "🔬 Test Case 1: paru-paru basah"
echo "=========================================="

curl -s -X POST $CORE_ENGINE_URL/api/lite/analyze/single \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "form",
    "diagnosis": "paru-paru basah",
    "tindakan": "nebulisasi",
    "obat": "ceftriaxone"
  }' | jq '.result.klasifikasi' || echo "❌ Test failed"

echo ""
echo "=========================================="
echo "🔬 Test Case 2: paru2 basah (dengan angka)"
echo "=========================================="

curl -s -X POST $CORE_ENGINE_URL/api/lite/analyze/single \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "form",
    "diagnosis": "paru2 basah",
    "tindakan": "rontgen thorax",
    "obat": "amoxicillin"
  }' | jq '.result.klasifikasi' || echo "❌ Test failed"

echo ""
echo "=========================================="
echo "🔬 Test Case 3: radang paru"
echo "=========================================="

curl -s -X POST $CORE_ENGINE_URL/api/lite/analyze/single \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "form",
    "diagnosis": "radang paru",
    "tindakan": "nebulisasi",
    "obat": "antibiotik"
  }' | jq '.result.klasifikasi' || echo "❌ Test failed"

echo ""
echo "=========================================="
echo "✅ Test Completed!"
echo "=========================================="
echo ""
echo "Expected Results:"
echo "  - No 'Error: No translation available' messages"
echo "  - All tests should return klasifikasi data"
echo "  - Translation should show 'pneumonia' or similar"
echo ""
