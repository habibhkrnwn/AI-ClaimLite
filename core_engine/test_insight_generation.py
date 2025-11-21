"""
Test untuk melihat output dan logic flow dari _generate_ai_insight
"""

import json
from services.lite_service import _generate_ai_insight
from openai import OpenAI
import os

# Setup OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("="*80)
print("TEST: _generate_ai_insight - Output & Logic Flow Analysis")
print("="*80)

# Test Case 1: Pneumonia case dengan konsistensi Tinggi
print("\n[TEST 1] Pneumonia - Konsistensi Tinggi")
print("-"*80)

full_analysis_1 = {
    "icd10": {
        "kode_icd": "J18.9"
    },
    "konsistensi": {
        "tingkat": "Tinggi"
    }
}

diagnosis_1 = "Pneumonia"
tindakan_1 = ["Rontgen Thorax", "Nebulisasi"]
obat_1 = ["Ceftriaxone", "Paracetamol"]

insight_1 = _generate_ai_insight(full_analysis_1, diagnosis_1, tindakan_1, obat_1, client)

print(f"Input:")
print(f"  - Diagnosis: {diagnosis_1} ({full_analysis_1['icd10']['kode_icd']})")
print(f"  - Tindakan: {', '.join(tindakan_1)}")
print(f"  - Obat: {', '.join(obat_1)}")
print(f"  - Konsistensi: {full_analysis_1['konsistensi']['tingkat']}")
print(f"\nOutput Insight AI:")
print(f"  ➜ {insight_1}")
print(f"\nLength: {len(insight_1)} characters")

# Test Case 2: Diabetes dengan konsistensi Rendah
print("\n" + "="*80)
print("[TEST 2] Diabetes - Konsistensi Rendah")
print("-"*80)

full_analysis_2 = {
    "icd10": {
        "kode_icd": "E11.9"
    },
    "konsistensi": {
        "tingkat": "Rendah"
    }
}

diagnosis_2 = "Diabetes Mellitus Type 2"
tindakan_2 = ["Rontgen Thorax"]  # Tidak sesuai dengan diabetes
obat_2 = ["Paracetamol"]  # Tidak sesuai

insight_2 = _generate_ai_insight(full_analysis_2, diagnosis_2, tindakan_2, obat_2, client)

print(f"Input:")
print(f"  - Diagnosis: {diagnosis_2} ({full_analysis_2['icd10']['kode_icd']})")
print(f"  - Tindakan: {', '.join(tindakan_2)}")
print(f"  - Obat: {', '.join(obat_2)}")
print(f"  - Konsistensi: {full_analysis_2['konsistensi']['tingkat']}")
print(f"\nOutput Insight AI:")
print(f"  ➜ {insight_2}")
print(f"\nLength: {len(insight_2)} characters")

# Test Case 3: No OpenAI client (fallback mode)
print("\n" + "="*80)
print("[TEST 3] Fallback Mode - No OpenAI Client")
print("-"*80)

full_analysis_3 = {
    "icd10": {
        "kode_icd": "J18.9"
    },
    "konsistensi": {
        "tingkat": "Rendah"
    }
}

diagnosis_3 = "Pneumonia"
tindakan_3 = ["Rontgen Thorax"]
obat_3 = ["Ceftriaxone"]

insight_3 = _generate_ai_insight(full_analysis_3, diagnosis_3, tindakan_3, obat_3, client=None)

print(f"Input:")
print(f"  - Diagnosis: {diagnosis_3}")
print(f"  - Tindakan: {', '.join(tindakan_3)}")
print(f"  - Obat: {', '.join(obat_3)}")
print(f"  - Konsistensi: {full_analysis_3['konsistensi']['tingkat']}")
print(f"  - OpenAI Client: None (fallback mode)")
print(f"\nOutput Insight AI:")
print(f"  ➜ {insight_3}")

# Test Case 4: Konsistensi Sedang
print("\n" + "="*80)
print("[TEST 4] Pneumonia - Konsistensi Sedang")
print("-"*80)

full_analysis_4 = {
    "icd10": {
        "kode_icd": "J18.9"
    },
    "konsistensi": {
        "tingkat": "Sedang"
    }
}

diagnosis_4 = "Pneumonia"
tindakan_4 = ["Rontgen Thorax", "Nebulisasi", "Lab Darah"]
obat_4 = ["Ceftriaxone", "Paracetamol", "Salbutamol"]

insight_4 = _generate_ai_insight(full_analysis_4, diagnosis_4, tindakan_4, obat_4, client)

print(f"Input:")
print(f"  - Diagnosis: {diagnosis_4} ({full_analysis_4['icd10']['kode_icd']})")
print(f"  - Tindakan: {', '.join(tindakan_4)}")
print(f"  - Obat: {', '.join(obat_4)}")
print(f"  - Konsistensi: {full_analysis_4['konsistensi']['tingkat']}")
print(f"\nOutput Insight AI:")
print(f"  ➜ {insight_4}")
print(f"\nLength: {len(insight_4)} characters")

print("\n" + "="*80)
print("LOGIC FLOW SUMMARY")
print("="*80)
print("""
1. Check OpenAI client availability:
   - If client=None or OPENAI_AVAILABLE=False → Use rule-based fallback
   - If konsistensi='Rendah' → "⚠️ Inkonsistensi ditemukan"
   - Else → "✅ Dokumentasi lengkap dan sesuai CP/PNPK"

2. Prepare context for AI prompt:
   - diagnosis + ICD-10 code
   - tindakan_list (max 3 items)
   - obat_list (max 3 items)
   - konsistensi tingkat

3. Call OpenAI GPT-4o-mini:
   - System prompt: "AI expert verifikasi klaim BPJS"
   - User prompt: Data + request for insight (max 100 chars)
   - Temperature: 0.5 (balanced creativity)
   - Max tokens: 100

4. Return insight string:
   - Success: AI-generated actionable insight
   - Error: Fallback to "✅ Dokumentasi lengkap dan sesuai CP/PNPK"

KEY OBSERVATIONS:
- ✅ AI generates contextual insights based on diagnosis, treatments, drugs
- ✅ Includes konsistensi level in prompt
- ✅ Has fallback mechanism for errors
- ⚠️ Max 100 characters limit (sometimes AI exceeds this)
- ⚠️ Konsistensi is included but AI may not always emphasize it
""")

print("\n" + "="*80)
print("TEST COMPLETED")
print("="*80)
