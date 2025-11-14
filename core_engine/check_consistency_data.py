"""
Check Data Coverage untuk Consistency Module
"""

import json
import os

RULES_DIR = os.path.join(os.path.dirname(__file__), "rules")

print("=" * 80)
print("DATA COVERAGE - CLINICAL CONSISTENCY MODULE")
print("=" * 80)

# 1. Check ICD10 → ICD9 Map
print("\n[1] ICD-10 → ICD-9 MAPPING (Diagnosis → Tindakan)")
print("-" * 80)
icd10_icd9_file = os.path.join(RULES_DIR, "icd10_icd9_map.json")
if os.path.exists(icd10_icd9_file):
    with open(icd10_icd9_file, 'r', encoding='utf-8') as f:
        icd10_icd9 = json.load(f)
    
    print(f"✓ File: {icd10_icd9_file}")
    print(f"✓ Total Diagnosis Codes: {len(icd10_icd9)}")
    
    # Sample entries
    print("\nSample Entries:")
    for i, (dx, procedures) in enumerate(list(icd10_icd9.items())[:5]):
        if isinstance(procedures, list):
            proc_list = procedures
        else:
            proc_list = procedures.get("tindakan", [])
        print(f"  {dx}: {proc_list}")
    
    # Total procedures mapped
    total_procs = 0
    for procedures in icd10_icd9.values():
        if isinstance(procedures, list):
            total_procs += len(procedures)
        else:
            total_procs += len(procedures.get("tindakan", []))
    
    print(f"\nTotal Procedure Mappings: {total_procs}")
else:
    print("❌ File not found!")

# 2. Check Diagnosis → Obat Map
print("\n[2] DIAGNOSIS → OBAT MAPPING")
print("-" * 80)
dx_obat_file = os.path.join(RULES_DIR, "diagnosis_obat_map.json")
if os.path.exists(dx_obat_file):
    with open(dx_obat_file, 'r', encoding='utf-8') as f:
        dx_obat = json.load(f)
    
    print(f"✓ File: {dx_obat_file}")
    print(f"✓ Total Diagnosis Codes: {len(dx_obat)}")
    
    # Sample entries
    print("\nSample Entries:")
    for i, (dx, drugs) in enumerate(list(dx_obat.items())[:5]):
        if isinstance(drugs, list):
            drug_list = drugs
        else:
            drug_list = drugs.get("obat", [])
        print(f"  {dx}: {drug_list[:3]}...")  # Show first 3 drugs
    
    # Total drugs mapped
    total_drugs = 0
    for drugs in dx_obat.values():
        if isinstance(drugs, list):
            total_drugs += len(drugs)
        else:
            total_drugs += len(drugs.get("obat", []))
    
    print(f"\nTotal Drug Mappings: {total_drugs}")
else:
    print("❌ File not found!")

# 3. Check Tindakan → Obat Map
print("\n[3] TINDAKAN → OBAT MAPPING (Procedures → Supporting Drugs)")
print("-" * 80)
tx_obat_file = os.path.join(RULES_DIR, "tindakan_obat_map.json")
if os.path.exists(tx_obat_file):
    with open(tx_obat_file, 'r', encoding='utf-8') as f:
        tx_obat = json.load(f)
    
    print(f"✓ File: {tx_obat_file}")
    print(f"✓ Total Procedure Codes: {len(tx_obat)}")
    
    # Sample entries
    print("\nSample Entries:")
    for i, (tx, drugs) in enumerate(list(tx_obat.items())[:5]):
        if isinstance(drugs, list):
            drug_list = drugs
        else:
            drug_list = drugs.get("obat", [])
        print(f"  {tx}: {drug_list}")
    
    # Total drugs
    total_drugs = 0
    for drugs in tx_obat.values():
        if isinstance(drugs, list):
            total_drugs += len(drugs)
        else:
            total_drugs += len(drugs.get("obat", []))
    
    print(f"\nTotal Drug Mappings: {total_drugs}")
else:
    print("❌ File not found!")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if os.path.exists(icd10_icd9_file):
    print(f"✓ ICD-10 → ICD-9:    {len(icd10_icd9)} diagnosis codes covered")
else:
    print("❌ ICD-10 → ICD-9 mapping missing")

if os.path.exists(dx_obat_file):
    print(f"✓ Diagnosis → Obat:  {len(dx_obat)} diagnosis codes covered")
else:
    print("❌ Diagnosis → Obat mapping missing")

if os.path.exists(tx_obat_file):
    print(f"✓ Tindakan → Obat:   {len(tx_obat)} procedure codes covered")
else:
    print("❌ Tindakan → Obat mapping missing")

print("\n💡 CATATAN:")
print("   - Untuk diagnosis/procedures yang tidak ada di mapping, sistem akan")
print("     memberikan status '✅ Sesuai' dengan catatan 'Tidak ada aturan khusus'")
print("   - Ini adalah pendekatan 'benefit of doubt' untuk menghindari false positive")
print("   - Coverage dapat diperluas dengan menambah data ke file JSON")
print("=" * 80)
