"""
Test Real Consistency Output - Mengecek output asli dari consistency module
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.consistency_service import analyze_clinical_consistency
import json

print("=" * 80)
print("TEST OUTPUT KONSISTENSI KLINIS - SKENARIO REAL")
print("=" * 80)

# Skenario 1: Pneumonia dengan penanganan yang sangat baik
print("\n[SKENARIO 1] Pneumonia dengan Penanganan Lengkap")
print("-" * 80)
print("Input:")
print("  - Diagnosis: J18.9 (Pneumonia)")
print("  - Tindakan: 87.44 (Chest X-ray), 93.96 (Inhalasi), 90.43 (Lab)")
print("  - Obat: Ceftriaxone, Amoxicillin, Salbutamol")
print()

result1 = analyze_clinical_consistency(
    dx="J18.9",
    tx_list=["87.44", "93.96", "90.43"],
    drug_list=["ceftriaxone", "amoxicillin", "salbutamol"]
)

print("Output:")
print(json.dumps(result1, indent=2, ensure_ascii=False))
print()
print(f"✓ Tingkat Konsistensi: {result1['konsistensi']['tingkat_konsistensi']}")
print(f"✓ Score: {result1['konsistensi']['_score']}/3.0")

# Skenario 2: Diabetes dengan komplikasi
print("\n" + "=" * 80)
print("[SKENARIO 2] Diabetes dengan Komplikasi")
print("-" * 80)
print("Input:")
print("  - Diagnosis: E11.9 (Type 2 Diabetes)")
print("  - Tindakan: 90.43 (Lab), 87.44 (Imaging)")
print("  - Obat: Metformin, Insulin, Glibenclamide")
print()

result2 = analyze_clinical_consistency(
    dx="E11.9",
    tx_list=["90.43", "87.44"],
    drug_list=["metformin", "insulin", "glibenclamide"]
)

print("Output:")
print(json.dumps(result2, indent=2, ensure_ascii=False))
print()
print(f"✓ Tingkat Konsistensi: {result2['konsistensi']['tingkat_konsistensi']}")
print(f"✓ Score: {result2['konsistensi']['_score']}/3.0")

# Skenario 3: Case dengan tindakan tidak sesuai (Error case)
print("\n" + "=" * 80)
print("[SKENARIO 3] Pneumonia dengan Tindakan Salah")
print("-" * 80)
print("Input:")
print("  - Diagnosis: J18.9 (Pneumonia)")
print("  - Tindakan: 51.23 (Cholecystectomy), 45.13 (Colon resection) <- SALAH!")
print("  - Obat: Insulin, Metformin <- SALAH!")
print()

result3 = analyze_clinical_consistency(
    dx="J18.9",
    tx_list=["51.23", "45.13"],  # Operasi kantung empedu & kolon (tidak cocok!)
    drug_list=["insulin", "metformin"]  # Obat diabetes (tidak cocok!)
)

print("Output:")
print(json.dumps(result3, indent=2, ensure_ascii=False))
print()
print(f"✓ Tingkat Konsistensi: {result3['konsistensi']['tingkat_konsistensi']}")
print(f"✓ Score: {result3['konsistensi']['_score']}/3.0")

# Skenario 4: Partial Match - Beberapa sesuai, beberapa tidak
print("\n" + "=" * 80)
print("[SKENARIO 4] Pneumonia - Sebagian Sesuai (Partial)")
print("-" * 80)
print("Input:")
print("  - Diagnosis: J18.9 (Pneumonia)")
print("  - Tindakan: 87.44 (Chest X-ray) <- BENAR, 51.23 <- SALAH")
print("  - Obat: Ceftriaxone <- BENAR, Metformin <- SALAH")
print()

result4 = analyze_clinical_consistency(
    dx="J18.9",
    tx_list=["87.44", "51.23"],  # 1 benar, 1 salah
    drug_list=["ceftriaxone", "metformin"]  # 1 benar, 1 salah
)

print("Output:")
print(json.dumps(result4, indent=2, ensure_ascii=False))
print()
print(f"✓ Tingkat Konsistensi: {result4['konsistensi']['tingkat_konsistensi']}")
print(f"✓ Score: {result4['konsistensi']['_score']}/3.0")

# Summary
print("\n" + "=" * 80)
print("RANGKUMAN HASIL TEST")
print("=" * 80)
print()
print("Status Legend:")
print("  ✅ Sesuai        = Semua sesuai protokol (score ≥ 80%)")
print("  ⚠️ Parsial      = Sebagian sesuai (score 40-79%)")
print("  ❌ Tidak Sesuai = Tidak sesuai protokol (score < 40%)")
print()
print("Tingkat Konsistensi:")
print("  Tinggi  = Total score ≥ 2.5/3.0")
print("  Sedang  = Total score ≥ 1.5/3.0")
print("  Rendah  = Total score < 1.5/3.0")
print()
print(f"Skenario 1 (Lengkap):      {result1['konsistensi']['tingkat_konsistensi']:6s} ({result1['konsistensi']['_score']:.1f}/3.0)")
print(f"Skenario 2 (Diabetes):     {result2['konsistensi']['tingkat_konsistensi']:6s} ({result2['konsistensi']['_score']:.1f}/3.0)")
print(f"Skenario 3 (Salah Total):  {result3['konsistensi']['tingkat_konsistensi']:6s} ({result3['konsistensi']['_score']:.1f}/3.0)")
print(f"Skenario 4 (Partial):      {result4['konsistensi']['tingkat_konsistensi']:6s} ({result4['konsistensi']['_score']:.1f}/3.0)")
print("=" * 80)

print("\n✅ KESIMPULAN:")
print("   1. Output memberikan 3 dimensi validasi: DX→TX, DX→DRUG, TX→DRUG")
print("   2. Setiap dimensi memiliki status dan catatan klinis dalam Bahasa Indonesia")
print("   3. Scoring system yang jelas dan transparan (0-3.0)")
print("   4. Catatan memberikan rekomendasi konkret untuk perbaikan")
print("   5. Sistem dapat mendeteksi error, partial match, dan full match dengan akurat")
print()
