"""
Test Clinical Consistency Module
Validates analyze_clinical_consistency() function with various scenarios
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.consistency_service import analyze_clinical_consistency
import json

print("=" * 80)
print("TESTING CLINICAL CONSISTENCY MODULE")
print("=" * 80)

# Test Case 1: Full Match (Pneumonia)
print("\n[TEST 1] Pneumonia - Full Match Expected [OK]")
print("-" * 80)
result1 = analyze_clinical_consistency(
    dx="J18.9",  # Pneumonia
    tx_list=["87.44", "93.96", "96.01"],  # Chest X-ray, Inhalation therapy, Intubation
    drug_list=["ceftriaxone", "amoxicillin", "salbutamol"]
)
print(json.dumps(result1, indent=2, ensure_ascii=False))

# Test Case 2: Partial Match (Pneumonia with some mismatched drugs)
print("\n[TEST 2] Pneumonia - Partial Match Expected [WARNING]")
print("-" * 80)
result2 = analyze_clinical_consistency(
    dx="J18.9",
    tx_list=["87.44", "93.96"],
    drug_list=["ceftriaxone", "metformin", "atorvastatin"]  # metformin/atorvastatin = mismatch
)
print(json.dumps(result2, indent=2, ensure_ascii=False))

# Test Case 3: No Match (Completely wrong)
print("\n[TEST 3] Pneumonia - No Match Expected [ERROR]")
print("-" * 80)
result3 = analyze_clinical_consistency(
    dx="J18.9",
    tx_list=["51.23", "45.13"],  # Random procedures (not related to pneumonia)
    drug_list=["insulin", "metformin"]  # Diabetes drugs (not for pneumonia)
)
print(json.dumps(result3, indent=2, ensure_ascii=False))

# Test Case 4: Empty inputs
print("\n[TEST 4] Empty Inputs - Low Consistency Expected")
print("-" * 80)
result4 = analyze_clinical_consistency(
    dx="Z00.0",  # General exam (no procedures/drugs expected)
    tx_list=[],
    drug_list=[]
)
print(json.dumps(result4, indent=2, ensure_ascii=False))

# Test Case 5: Unknown Diagnosis
print("\n[TEST 5] Unknown Diagnosis - Warning Expected")
print("-" * 80)
result5 = analyze_clinical_consistency(
    dx="X99.9",  # Non-existent code
    tx_list=["87.44"],
    drug_list=["ceftriaxone"]
)
print(json.dumps(result5, indent=2, ensure_ascii=False))

print("\n" + "=" * 80)
print("SUMMARY OF RESULTS")
print("=" * 80)
print(f"Test 1 (Full Match):       {result1['konsistensi']['tingkat_konsistensi']}")
print(f"Test 2 (Partial Match):    {result2['konsistensi']['tingkat_konsistensi']}")
print(f"Test 3 (No Match):         {result3['konsistensi']['tingkat_konsistensi']}")
print(f"Test 4 (Empty):            {result4['konsistensi']['tingkat_konsistensi']}")
print(f"Test 5 (Unknown Dx):       {result5['konsistensi']['tingkat_konsistensi']}")
print("=" * 80)
