#!/bin/bash

# Test analyze API with sample data

echo "=== Testing Core Engine API ==="
echo ""

# Test 1: Form mode with ICD codes
echo "Test 1: Form mode dengan ICD-10 (B01.2) dan ICD-9 (99.21)"
curl -X POST http://localhost:8000/api/lite/analyze/single \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "form",
    "diagnosis": "Pneumonia varicella",
    "tindakan": "Injeksi antibiotik",
    "obat": "Ceftriaxone 1g, Paracetamol 500mg",
    "icd10_code": "B01.2",
    "icd9_code": "99.21",
    "use_optimized": true,
    "save_history": false
  }' 2>/dev/null | jq '.status, .result.klasifikasi.diagnosis, .result.klasifikasi.tindakan[0]' || echo "FAILED"

echo ""
echo "=== Test Complete ==="
