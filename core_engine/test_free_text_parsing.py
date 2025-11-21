"""
Test Free Text Parsing
Menguji berbagai skenario parsing dari input teks bebas
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.lite_service import get_parser
import json


def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_result(parsed_result):
    print(f"\n📋 Diagnosis: {parsed_result.get('diagnosis')}")
    print(f"   ICD-10: {parsed_result.get('diagnosis_icd10') or 'Tidak terdeteksi'}")
    
    print(f"\n🔧 Tindakan ({len(parsed_result.get('tindakan', []))}):")
    for i, t in enumerate(parsed_result.get('tindakan', []), 1):
        if isinstance(t, dict):
            print(f"   {i}. {t.get('name')} → ICD-9: {t.get('icd9') or '-'}")
        else:
            print(f"   {i}. {t}")
    
    print(f"\n💊 Obat ({len(parsed_result.get('obat', []))}):")
    for i, o in enumerate(parsed_result.get('obat', []), 1):
        if isinstance(o, dict):
            dosis = f" ({o.get('dosis')})" if o.get('dosis') else ""
            print(f"   {i}. {o.get('name')}{dosis}")
        else:
            print(f"   {i}. {o}")
    
    print(f"\n📊 Confidence: {parsed_result.get('confidence')}")
    print(f"💬 Notes: {parsed_result.get('notes') or '-'}")


# Initialize parser
print("🚀 Initializing OpenAI Parser...")
parser = get_parser()
print("✅ Parser ready\n")

# ============================================================================
# SKENARIO 1: Narrative Text - Tanpa Kode
# ============================================================================
print_section("SKENARIO 1: Narrative Text - Tanpa Kode ICD")

text1 = """Pasien laki-laki 45 tahun datang dengan keluhan demam tinggi 3 hari,
batuk berdahak, dan sesak napas. Dari pemeriksaan fisik didapatkan ronki basah
halus di kedua paru. Diagnosis kerja Pneumonia Komunitas.

Tindakan:
- Rontgen thorax AP/Lateral
- Pemeriksaan laboratorium darah lengkap
- Pemberian oksigen 3 lpm via nasal kanul

Terapi:
- IVFD RL 20 tpm
- Inj. Ceftriaxone 1 gram/12 jam
- Paracetamol 500mg 3x1 tablet
- Ambroxol syrup 3x1 sendok
"""

result1 = parser.parse(text1, "text")
print_result(result1)

# ============================================================================
# SKENARIO 2: Structured Text - Dengan Kode ICD dalam Kurung
# ============================================================================
print_section("SKENARIO 2: Text dengan Kode ICD dalam Kurung")

text2 = """Diagnosis: Pneumonia (J18.9)
Tindakan: 
  - Rontgen Thorax (87.44)
  - Pemeriksaan Lab Darah (90.59)
Obat:
  - Ceftriaxone 1g IV
  - Paracetamol 500mg
  - Ambroxol 30mg"""

result2 = parser.parse(text2, "text")
print_result(result2)

# ============================================================================
# SKENARIO 3: Mixed Format - Sebagian Ada Kode
# ============================================================================
print_section("SKENARIO 3: Mixed - Diagnosis Ada Kode, Tindakan Tidak")

text3 = """Diagnosis kerja: Diabetes Mellitus Tipe 2 dengan komplikasi (E11.9)

Pemeriksaan yang dilakukan:
- Cek gula darah puasa dan 2 jam PP
- Pemeriksaan HbA1c
- Funduskopi

Terapi yang diberikan:
- Metformin 500mg 2x1
- Glimepiride 2mg 1x1
- Vitamin B complex
"""

result3 = parser.parse(text3, "text")
print_result(result3)

# ============================================================================
# SKENARIO 4: Singkat - Catatan Minimal
# ============================================================================
print_section("SKENARIO 4: Catatan Singkat/Minimal")

text4 = "Pneumonia, kasih antibiotik ceftriaxone sama paracetamol, rontgen dulu"

result4 = parser.parse(text4, "text")
print_result(result4)

# ============================================================================
# SKENARIO 5: Abbreviations & Typo
# ============================================================================
print_section("SKENARIO 5: Dengan Abbreviations & Typo")

text5 = """Dx: DM type 2 + HT
Tx: - CEK GDS, GDP, HbA1c
    - Monitor TD
Rx: - Metformin tab 2x500mg
    - Amlodipine tab 1x5mg
    - ASA tab 1x80mg"""

result5 = parser.parse(text5, "text")
print_result(result5)

# ============================================================================
# SKENARIO 6: Multiple Diagnosis
# ============================================================================
print_section("SKENARIO 6: Multiple Diagnosis (Hanya Ambil Utama)")

text6 = """Diagnosis:
1. Pneumonia Komunitas (J18.9) - Diagnosis Utama
2. Hipertensi Stage 2 (I10)
3. Anemia ringan

Dilakukan rontgen thorax, pasang IVFD, berikan antibiotik ceftriaxone dan amlodipin untuk hipertensi."""

result6 = parser.parse(text6, "text")
print_result(result6)

# ============================================================================
# RINGKASAN EVALUASI
# ============================================================================
print_section("RINGKASAN EVALUASI PARSING")

results = [
    ("Skenario 1 (Narrative)", result1),
    ("Skenario 2 (Kode ICD)", result2),
    ("Skenario 3 (Mixed)", result3),
    ("Skenario 4 (Singkat)", result4),
    ("Skenario 5 (Abbreviations)", result5),
    ("Skenario 6 (Multiple Dx)", result6)
]

print("\n📊 SUMMARY TABLE:")
print("-" * 70)
print(f"{'Skenario':<25} {'Dx':<6} {'ICD-10':<8} {'Tindakan':<10} {'Obat':<6} {'Conf'}")
print("-" * 70)

for name, result in results:
    dx = "✓" if result.get('diagnosis') != "Tidak terdeteksi" else "✗"
    icd10 = "✓" if result.get('diagnosis_icd10') else "✗"
    tindakan = len(result.get('tindakan', []))
    obat = len(result.get('obat', []))
    conf = f"{result.get('confidence'):.2f}"
    
    print(f"{name:<25} {dx:<6} {icd10:<8} {tindakan:<10} {obat:<6} {conf}")

print("-" * 70)

# ============================================================================
# EVALUASI KESESUAIAN
# ============================================================================
print("\n🔍 EVALUASI KESESUAIAN:")

print("\n1. ✅ Deteksi Kode ICD dalam Kurung:")
print(f"   Skenario 2: {'✅ BENAR' if result2.get('diagnosis_icd10') == 'J18.9' else '❌ SALAH'}")
print(f"   Skenario 3: {'✅ BENAR' if result3.get('diagnosis_icd10') == 'E11.9' else '❌ SALAH'}")

print("\n2. ✅ Extract Diagnosis Utama (bukan kalimat panjang):")
dx1 = result1.get('diagnosis', '')
print(f"   Skenario 1: {'✅ BENAR' if len(dx1) < 50 and 'Pasien' not in dx1 else '❌ SALAH'} → '{dx1}'")

print("\n3. ✅ Deteksi Tindakan dari Narrative:")
print(f"   Skenario 1: {len(result1.get('tindakan', []))} tindakan terdeteksi")

print("\n4. ✅ Normalize Obat ke Generik:")
obat1_names = [o.get('name') if isinstance(o, dict) else o for o in result1.get('obat', [])]
print(f"   Skenario 1: {obat1_names}")

print("\n5. ✅ Handle Abbreviations:")
print(f"   Skenario 5: Diagnosis = '{result5.get('diagnosis')}'")

print("\n6. ⚠️  Handle Multiple Diagnosis (ambil utama):")
print(f"   Skenario 6: Diagnosis = '{result6.get('diagnosis')}'")
print(f"   Expected: 'Pneumonia Komunitas' atau 'Pneumonia'")

print("\n" + "="*70)
print("TEST SELESAI")
print("="*70)
