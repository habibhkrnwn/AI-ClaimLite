"""
Test AI-Powered Drug Name Transliteration

Test untuk memverifikasi AI transliteration English → Indonesian
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.fornas_matcher import FornasDrugMatcher


def test_transliteration():
    """Test AI transliteration dengan berbagai drug names"""
    
    print("=" * 80)
    print("  AI-POWERED DRUG NAME TRANSLITERATION TEST")
    print("=" * 80)
    
    test_cases = [
        # English names (should convert to Indonesian)
        ("Ceftriaxone", "seftriakson"),
        ("Paracetamol", "parasetamol"),
        ("Levofloxacin", "levofloksasin"),
        ("Ciprofloxacin", "siprofloksasin"),
        ("Amoxicillin", "amoksisilin"),
        ("Metformin", "metformin"),  # Same in both
        ("Omeprazole", "omeprazol"),
        ("Dexamethasone", "deksametason"),
        
        # Indonesian names (should stay as-is)
        ("Seftriakson", "seftriakson"),
        ("Parasetamol", "parasetamol"),
        
        # With dosage/route (should clean and transliterate)
        ("Ceftriaxone 1g IV", "seftriakson"),
        ("Paracetamol 500mg tablet", "parasetamol"),
        
        # Brand names / unusual
        ("Insulin Aspart", None),  # AI will figure it out
        ("Salbutamol nebul", "salbutamol"),
    ]
    
    matcher = FornasDrugMatcher()
    
    print(f"\n🤖 AI Transliteration: {'ENABLED' if matcher.ai_enabled else 'DISABLED'}")
    print("\n" + "-" * 80)
    
    success_count = 0
    total_count = 0
    
    for input_name, expected_output in test_cases:
        print(f"\n📝 Input: '{input_name}'")
        
        # Normalize with AI
        result = matcher.normalize_drug_name(input_name, use_ai=True)
        
        print(f"   → Output: '{result}'")
        
        if expected_output:
            if result == expected_output:
                print(f"   ✅ PASS (expected: '{expected_output}')")
                success_count += 1
            else:
                print(f"   ⚠️ MISMATCH (expected: '{expected_output}')")
            total_count += 1
        else:
            print(f"   ℹ️ INFO (no expected output)")
    
    print("\n" + "=" * 80)
    print(f"📊 RESULTS: {success_count}/{total_count} passed")
    print("=" * 80)


def test_matching_with_ai():
    """Test full matching dengan AI transliteration"""
    
    print("\n\n" + "=" * 80)
    print("  FULL MATCHING TEST WITH AI TRANSLITERATION")
    print("=" * 80)
    
    test_drugs = [
        "Ceftriaxone 1g IV",      # English
        "Paracetamol 500mg",      # English
        "Levofloxacin 500mg",     # English
        "Seftriakson injeksi",    # Indonesian
        "Parasetamol tablet",     # Indonesian
        "Metformin 500mg",        # Same in both
    ]
    
    matcher = FornasDrugMatcher()
    
    print(f"\n🔍 Testing {len(test_drugs)} drugs:")
    
    for drug_name in test_drugs:
        print(f"\n📋 Input: '{drug_name}'")
        
        # Normalize
        normalized = matcher.normalize_drug_name(drug_name, use_ai=True)
        print(f"   Normalized: '{normalized}'")
        
        # Match
        result = matcher.match(drug_name, threshold=80)
        
        if result["found"]:
            print(f"   ✅ MATCHED via {result['strategy']}")
            print(f"      DB Name: {result['drug'].obat_name}")
            print(f"      Confidence: {result['confidence']}%")
        else:
            print(f"   ❌ NOT FOUND (will show as Non-Fornas)")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n🧪 Starting AI Transliteration Tests...\n")
    
    try:
        # Test 1: Pure transliteration
        test_transliteration()
        
        # Test 2: Full matching
        test_matching_with_ai()
        
        print("\n✅ All tests completed!\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
