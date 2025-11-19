"""
Test Consistency Debug - Trace exact flow dari input ke output
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.consistency_service import (
    analyze_clinical_consistency,
    load_icd10_icd9_map,
    load_diagnosis_obat_map,
    load_tindakan_obat_map,
    normalize_icd_code,
    normalize_drug_name
)
import json

print("=" * 80)
print("DEBUG: CONSISTENCY SERVICE - STEP BY STEP")
print("=" * 80)

# Test Case: Pneumonia seperti di UI
print("\n[TEST CASE] Pneumonia dengan Nebulisasi, Ceftriaxone")
print("-" * 80)

# Step 1: Load mappings
print("\n[STEP 1] Loading Mapping Files")
dx_tx_map = load_icd10_icd9_map()
dx_drug_map = load_diagnosis_obat_map()
tx_drug_map = load_tindakan_obat_map()

print(f"✓ ICD10→ICD9 Map: {len(dx_tx_map)} entries")
print(f"✓ Diagnosis→Obat Map: {len(dx_drug_map)} entries")
print(f"✓ Tindakan→Obat Map: {len(tx_drug_map)} entries")

# Step 2: Define input (sesuai UI)
print("\n[STEP 2] Input Data (seperti dari UI)")
dx_input = "J18.9"
tx_input = ["93.96"]  # Nebulisasi
drug_input = ["ceftriaxone"]

print(f"Diagnosis: {dx_input}")
print(f"Tindakan: {tx_input}")
print(f"Obat: {drug_input}")

# Step 3: Check mapping existence
print("\n[STEP 3] Check if Mappings Exist")
dx_norm = normalize_icd_code(dx_input)
print(f"Normalized DX: {dx_norm}")

# Check DX→TX mapping
if dx_norm in dx_tx_map:
    expected_tx = dx_tx_map[dx_norm]
    print(f"✓ DX→TX Mapping FOUND: {len(expected_tx)} tindakan")
    print(f"  Expected Tindakan: {expected_tx[:5]}...")
else:
    print(f"✗ DX→TX Mapping NOT FOUND for {dx_norm}")
    expected_tx = []

# Check DX→DRUG mapping
if dx_norm in dx_drug_map:
    expected_drugs = dx_drug_map[dx_norm]
    print(f"✓ DX→DRUG Mapping FOUND: {len(expected_drugs)} obat")
    print(f"  Expected Obat: {expected_drugs[:5]}...")
else:
    print(f"✗ DX→DRUG Mapping NOT FOUND for {dx_norm}")
    expected_drugs = []

# Check TX→DRUG mapping
tx_norm = tx_input[0].strip().upper()
if tx_norm in tx_drug_map:
    tx_drugs = tx_drug_map[tx_norm]
    print(f"✓ TX→DRUG Mapping FOUND for {tx_norm}: {tx_drugs}")
else:
    print(f"✗ TX→DRUG Mapping NOT FOUND for {tx_norm}")

# Step 4: Run analysis
print("\n[STEP 4] Running analyze_clinical_consistency()")
result = analyze_clinical_consistency(
    dx=dx_input,
    tx_list=tx_input,
    drug_list=drug_input
)

print("\n[STEP 5] RESULT:")
print(json.dumps(result, indent=2, ensure_ascii=False))

# Step 6: Analyze score breakdown
print("\n[STEP 6] Score Breakdown:")
konsistensi = result["konsistensi"]
print(f"DX→TX Status: {konsistensi['dx_tx']['status']}")
print(f"DX→DRUG Status: {konsistensi['dx_drug']['status']}")
print(f"TX→DRUG Status: {konsistensi['tx_drug']['status']}")
print(f"Total Score: {konsistensi['_score']}/3.0")
print(f"Tingkat: {konsistensi['tingkat_konsistensi']}")

# Step 7: Check why always ⚠️ Parsial
print("\n[STEP 7] WHY ALWAYS ⚠️ Parsial?")
print("-" * 80)

# Check if input tindakan is in expected
if tx_input[0] in expected_tx:
    print(f"✓ Input tindakan '{tx_input[0]}' IS in expected list")
else:
    print(f"✗ Input tindakan '{tx_input[0]}' NOT in expected list")
    print(f"  Expected: {expected_tx[:10]}")

# Check if input drug is in expected
drug_norm = normalize_drug_name(drug_input[0])
expected_drug_norm = [normalize_drug_name(d) for d in expected_drugs]
if drug_norm in expected_drug_norm:
    print(f"✓ Input obat '{drug_norm}' IS in expected list")
else:
    print(f"✗ Input obat '{drug_norm}' NOT in expected list")
    print(f"  Expected (normalized): {expected_drug_norm[:10]}")

print("\n" + "=" * 80)
print("DIAGNOSIS:")
print("=" * 80)

# Test dengan berbagai variasi input
test_cases = [
    {
        "name": "Case 1: Exact match",
        "dx": "J18.9",
        "tx": ["87.44", "93.96"],
        "drug": ["ceftriaxone", "amoxicillin"]
    },
    {
        "name": "Case 2: Partial match",
        "dx": "J18.9",
        "tx": ["87.44"],
        "drug": ["ceftriaxone"]
    },
    {
        "name": "Case 3: Wrong inputs",
        "dx": "J18.9",
        "tx": ["51.23"],  # Wrong procedure
        "drug": ["metformin"]  # Wrong drug
    }
]

for case in test_cases:
    print(f"\n{case['name']}")
    print("-" * 40)
    result = analyze_clinical_consistency(
        dx=case['dx'],
        tx_list=case['tx'],
        drug_list=case['drug']
    )
    k = result['konsistensi']
    print(f"DX→TX: {k['dx_tx']['status']}")
    print(f"DX→DRUG: {k['dx_drug']['status']}")
    print(f"TX→DRUG: {k['tx_drug']['status']}")
    print(f"Overall: {k['tingkat_konsistensi']} ({k['_score']}/3.0)")
