"""
Simple validation test to check if matching is working
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.consistency_service import analyze_clinical_consistency
import json

# Read the actual mapping to understand what's expected
import json

with open("rules/icd10_icd9_map.json", "r", encoding="utf-8") as f:
    icd10_icd9 = json.load(f)

with open("rules/diagnosis_obat_map.json", "r", encoding="utf-8") as f:
    dx_obat = json.load(f)

print("Expected procedures for J18.9:", icd10_icd9.get("J18.9", []))
print("\nExpected drugs for J18.9:", dx_obat.get("J18.9", []))

print("\n" + "=" * 80)
print("Testing with EXACT expected values")
print("=" * 80)

# Use ALL expected procedures and drugs
result = analyze_clinical_consistency(
    dx="J18.9",
    tx_list=icd10_icd9.get("J18.9", [])[:5],  # First 5 procedures
    drug_list=dx_obat.get("J18.9", [])[:5]     # First 5 drugs
)

print(json.dumps(result, indent=2, ensure_ascii=False))
