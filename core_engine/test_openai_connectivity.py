"""
Quick test: Verify OpenAI API actually works (not just key loaded)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

print("\n" + "="*80)
print("TESTING: OpenAI API Connectivity")
print("="*80)

# Test 1: Simple ICD-9 partial search (no AI needed)
print("\n[TEST 1] ICD-9 Partial Search (Database only - no AI)")
try:
    from services.icd9_smart_service import partial_search_icd9
    results = partial_search_icd9("appendectomy", limit=3)
    if results:
        print(f"  Status: OK")
        print(f"  Found {len(results)} results:")
        for r in results[:3]:
            print(f"    - {r['code']}: {r['name'][:50]}")
    else:
        print(f"  Status: WARNING - No results")
except Exception as e:
    print(f"  Status: ERROR - {e}")

# Test 2: Try AI normalization (this will use OpenAI)
print("\n[TEST 2] ICD-9 AI Normalization (Uses OpenAI API)")
print("  Note: This test might fail if API key is invalid (401 error)")
try:
    from services.icd9_smart_service import normalize_procedure_with_ai
    
    # Try to normalize Indonesian term
    print("  Testing with: 'operasi usus buntu'")
    result = normalize_procedure_with_ai("operasi usus buntu", language="id")
    
    if result.get("suggestions"):
        print(f"  Status: OK - AI normalization works!")
        print(f"  AI suggested {len(result['suggestions'])} codes:")
        for s in result['suggestions'][:3]:
            print(f"    - {s['code']}: {s['name'][:50]}")
    else:
        print(f"  Status: WARNING - No suggestions from AI")
        if result.get("error"):
            print(f"  Error: {result['error']}")
            
except Exception as e:
    error_msg = str(e)
    if "401" in error_msg or "Unauthorized" in error_msg:
        print(f"  Status: FAILED - Invalid API Key (401 Unauthorized)")
        print(f"  Error: {error_msg}")
        print(f"\n  ACTION REQUIRED:")
        print(f"    1. Get new API key from: https://platform.openai.com/api-keys")
        print(f"    2. Update core_engine/.env file")
        print(f"    3. Restart services")
    else:
        print(f"  Status: ERROR - {error_msg}")

# Test 3: FORNAS recommendation
print("\n[TEST 3] FORNAS Drug Recommendation (Database + optional AI)")
try:
    from services.fornas_smart_service import recommend_drug
    
    print("  Testing with: 'paracetamol'")
    result = recommend_drug("paracetamol", max_recommend=3)
    
    if result.get("recommendations"):
        print(f"  Status: OK")
        print(f"  Found {len(result['recommendations'])} recommendations")
        for r in result['recommendations'][:3]:
            print(f"    - {r['obat_name']}")
    else:
        print(f"  Status: WARNING - No recommendations")
        
except Exception as e:
    print(f"  Status: ERROR - {e}")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
print("\nSUMMARY:")
print("  - If Test 1 passes: Database connection OK")
print("  - If Test 2 passes: OpenAI API key is VALID and working")
print("  - If Test 2 fails with 401: API key is INVALID (needs replacement)")
print("  - If Test 3 passes: FORNAS service OK")
