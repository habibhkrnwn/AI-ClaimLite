"""
Test FORNAS Smart Service
Test AI normalization (English → Indonesian) dan matching
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.fornas_smart_service import (
    match_drug,
    validate_fornas
)


def test_english_to_indonesian():
    """Test AI normalization dari English ke Indonesian"""
    print("\n" + "="*80)
    print("TEST 1: English → Indonesian Normalization")
    print("="*80)
    
    test_drugs = [
        "ceftriaxone",
        "paracetamol",
        "levofloxacin",
        "metformin",
        "amoxicillin"
    ]
    
    for drug in test_drugs:
        print(f"\n📌 Input: {drug}")
        result = match_drug(drug, use_ai=True)
        
        if result["found"]:
            print(f"   ✅ Match found!")
            print(f"   → Database name: {result['drug'].obat_name}")
            print(f"   → Kode: {result['drug'].kode_fornas}")
            print(f"   → Strategy: {result['strategy']}")
            print(f"   → Confidence: {result['confidence']}%")
        else:
            print(f"   ❌ Not found in database")


def test_validation_with_english():
    """Test batch validation dengan input English"""
    print("\n" + "="*80)
    print("TEST 2: Batch Validation dengan English Input")
    print("="*80)
    
    drug_list = [
        "Ceftriaxone 1g IV",
        "Paracetamol 500mg",
        "Levofloxacin 500mg"
    ]
    
    print(f"\n📋 Input drugs:")
    for i, drug in enumerate(drug_list, 1):
        print(f"   {i}. {drug}")
    
    result = validate_fornas(
        drug_list=drug_list,
        diagnosis_icd10="J18.9",
        diagnosis_name="Pneumonia"
    )
    
    print(f"\n📊 Summary:")
    summary = result["summary"]
    print(f"   Total obat: {summary['total_obat']}")
    print(f"   ✅ Sesuai: {summary['sesuai']}")
    print(f"   ⚠️  Perlu Justifikasi: {summary['perlu_justifikasi']}")
    print(f"   ❌ Non-Fornas: {summary['non_fornas']}")
    
    print(f"\n📝 Validation Results:")
    for val in result["fornas_validation"]:
        print(f"\n   {val['no']}. {val['nama_obat']}")
        print(f"      Kelas: {val['kelas_terapi']}")
        print(f"      Status: {val['status_fornas']}")
        print(f"      Catatan: {val['catatan_ai']}")


def test_mixed_input():
    """Test dengan campuran English, Indonesian, dan typo"""
    print("\n" + "="*80)
    print("TEST 3: Mixed Input (English, Indonesian, Typo)")
    print("="*80)
    
    drug_list = [
        "ceftriaxone",      # English
        "Parasetamol",      # Indonesian
        "levofloxasin",     # Typo
        "Metformin",        # Same in both
        "amoksisilin"       # Indonesian
    ]
    
    print(f"\n📋 Input drugs:")
    for i, drug in enumerate(drug_list, 1):
        print(f"   {i}. {drug}")
    
    for drug in drug_list:
        print(f"\n📌 Testing: {drug}")
        result = match_drug(drug, use_ai=True)
        
        if result["found"]:
            print(f"   ✅ Found: {result['drug'].obat_name}")
            print(f"   Strategy: {result['strategy']}")
        else:
            print(f"   ❌ Not found")


if __name__ == "__main__":
    print("\n" + "🔬 FORNAS Smart Service Testing")
    print("Testing AI-powered English → Indonesian normalization")
    
    try:
        # Test 1: English to Indonesian
        test_english_to_indonesian()
        
        # Test 2: Batch validation
        test_validation_with_english()
        
        # Test 3: Mixed input
        test_mixed_input()
        
        print("\n" + "="*80)
        print("✅ All tests completed!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
