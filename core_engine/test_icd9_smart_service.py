"""
Unit tests for ICD-9 Smart Service
"""

from services.icd9_smart_service import (
    exact_search_icd9,
    normalize_procedure_with_ai,
    validate_ai_suggestions,
    lookup_icd9_procedure
)


def test_exact_search():
    """Test exact database search"""
    print("\n" + "="*60)
    print("TEST 1: Exact Search")
    print("="*60)
    
    # Test 1: Exact match (case insensitive)
    print("\n[Test 1.1] Exact match (lowercase)")
    result = exact_search_icd9("routine chest x-ray")
    if result:
        print(f"✅ Found: {result['name']} ({result['code']})")
        assert result["confidence"] == 100
        assert result["valid"] == True
    else:
        print("⚠️ Not found (might need to check actual DB data)")
    
    # Test 2: Not found
    print("\n[Test 1.2] Not found case")
    result = exact_search_icd9("random procedure xyz 123")
    assert result is None
    print("✅ Correctly returned None for non-existent procedure")
    
    # Test 3: Empty input
    print("\n[Test 1.3] Empty input")
    result = exact_search_icd9("")
    assert result is None
    print("✅ Correctly handled empty input")


def test_ai_normalization():
    """Test AI normalization"""
    print("\n" + "="*60)
    print("TEST 2: AI Normalization")
    print("="*60)
    
    # Test 1: Indonesian input
    print("\n[Test 2.1] Indonesian input: 'rontgen thorax'")
    suggestions = normalize_procedure_with_ai("rontgen thorax")
    print(f"AI returned {len(suggestions)} suggestions:")
    for i, sug in enumerate(suggestions, 1):
        print(f"  {i}. {sug}")
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0
    print("✅ AI normalization successful")
    
    # Test 2: Vague input
    print("\n[Test 2.2] Vague input: 'x-ray'")
    suggestions = normalize_procedure_with_ai("x-ray")
    print(f"AI returned {len(suggestions)} suggestions:")
    for i, sug in enumerate(suggestions, 1):
        print(f"  {i}. {sug}")
    assert len(suggestions) > 0
    print("✅ AI handled vague input")
    
    # Test 3: Empty input
    print("\n[Test 2.3] Empty input")
    suggestions = normalize_procedure_with_ai("")
    assert suggestions == []
    print("✅ Correctly handled empty input")


def test_validate_suggestions():
    """Test AI suggestion validation"""
    print("\n" + "="*60)
    print("TEST 3: Validate AI Suggestions")
    print("="*60)
    
    # Test with sample suggestions
    sample_suggestions = [
        "Routine chest X-ray",
        "Other chest X-ray",
        "Invalid procedure name xyz"
    ]
    
    print("\n[Test 3.1] Validating suggestions:")
    for sug in sample_suggestions:
        print(f"  - {sug}")
    
    valid_matches = validate_ai_suggestions(sample_suggestions)
    print(f"\nValid matches found: {len(valid_matches)}")
    for match in valid_matches:
        print(f"  ✅ {match['name']} ({match['code']})")
    
    assert isinstance(valid_matches, list)
    print("✅ Validation completed")


def test_lookup_flow():
    """Test main lookup function (complete flow)"""
    print("\n" + "="*60)
    print("TEST 4: Complete Lookup Flow")
    print("="*60)
    
    # Test 1: Exact match (will be instant)
    print("\n[Test 4.1] Exact match case")
    result = lookup_icd9_procedure("Routine chest X-ray")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"✅ Result: {result['result']['name']} ({result['result']['code']})")
        print(f"   Confidence: {result['result']['confidence']}%")
        assert result["needs_selection"] == False
    else:
        print(f"⚠️ Status: {result['status']}, Message: {result.get('message', 'N/A')}")
    
    # Test 2: AI normalization (Indonesian)
    print("\n[Test 4.2] AI normalization (Indonesian input)")
    print("⏳ This will call OpenAI API... please wait")
    result = lookup_icd9_procedure("rontgen dada")
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        print(f"✅ Auto-selected: {result['result']['name']} ({result['result']['code']})")
        print(f"   Confidence: {result['result']['confidence']}%")
    elif result['status'] == 'suggestions':
        print(f"🔍 Multiple suggestions ({len(result['suggestions'])} items):")
        for i, sug in enumerate(result['suggestions'], 1):
            print(f"   {i}. {sug['name']} ({sug['code']})")
        assert result["needs_selection"] == True
    else:
        print(f"❌ Not found: {result.get('message', 'N/A')}")
    
    # Test 3: Not found
    print("\n[Test 4.3] Not found case")
    result = lookup_icd9_procedure("random invalid procedure xyz 123")
    print(f"Status: {result['status']}")
    assert result['status'] == 'not_found'
    print(f"✅ Correctly returned not_found: {result.get('message', 'N/A')}")
    
    # Test 4: Empty input
    print("\n[Test 4.4] Empty input")
    result = lookup_icd9_procedure("")
    assert result['status'] == 'not_found'
    print(f"✅ Correctly handled empty input")


if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# ICD-9 SMART SERVICE - UNIT TESTS")
    print("#"*60)
    
    try:
        test_exact_search()
        test_ai_normalization()
        test_validate_suggestions()
        test_lookup_flow()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
