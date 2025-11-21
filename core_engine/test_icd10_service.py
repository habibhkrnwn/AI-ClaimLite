"""
Test script for icd10_service.py
Tests db_search_partial, lookup_icd10_basic, and select_icd10_code functions
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.icd10_service import (
    db_search_partial,
    lookup_icd10_basic,
    select_icd10_code,
    get_icd10_statistics
)


def test_db_search_partial():
    """Test partial search with various inputs"""
    print("\n" + "="*80)
    print("TEST 1: db_search_partial() - Partial Matching")
    print("="*80)
    
    test_cases = [
        ("heart", "English medical term"),
        ("jantung", "Indonesian medical term"),
        ("diabetes", "Common disease"),
        ("I25", "ICD-10 code"),
        ("fracture", "Procedure-like term"),
        ("demam", "Indonesian symptom"),
        ("hypertension", "Medical condition"),
    ]
    
    for search_term, description in test_cases:
        print(f"\n📝 Test: '{search_term}' ({description})")
        print("-" * 80)
        
        try:
            results = db_search_partial(search_term, limit=5)
            
            if results:
                print(f"✅ Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. [{result['code']}] {result['name']}")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()


def test_lookup_icd10_basic():
    """Test main lookup function with ranking"""
    print("\n" + "="*80)
    print("TEST 2: lookup_icd10_basic() - Smart Ranking & Matching")
    print("="*80)
    
    test_cases = [
        ("heart attack", "Complex English phrase"),
        ("heart", "Single word"),
        ("I21", "Exact ICD-10 code"),
        ("diabetes", "Common disease"),
        ("pneumonia", "Medical term"),
    ]
    
    for user_input, description in test_cases:
        print(f"\n📝 Test: '{user_input}' ({description})")
        print("-" * 80)
        
        try:
            result = lookup_icd10_basic(user_input)
            
            # Result format: {"flow": "direct|suggestion|not_found", ...}
            flow = result.get("flow", "unknown")
            print(f"✅ Flow: {flow}")
            print(f"   AI Used: {result.get('ai_used', False)}")
            
            if flow == "direct":
                print(f"   Selected Code: {result['selected_code']}")
                print(f"   Selected Name: {result['selected_name']}")
                print(f"   Subcategories: {result['subcategories']['total_subcategories']}")
            elif flow == "suggestion":
                suggestions = result.get("suggestions", [])
                print(f"   Total Suggestions: {len(suggestions)}")
                for i, s in enumerate(suggestions[:3], 1):
                    print(f"  {i}. [{s['code']}] {s['name']}")
            else:
                print(f"   Message: {result.get('message', 'N/A')}")
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()


def test_select_icd10_code():
    """Test code selection and subcategory retrieval"""
    print("\n" + "="*80)
    print("TEST 3: select_icd10_code() - Get Subcategories")
    print("="*80)
    
    test_cases = [
        ("I25", "Chronic ischemic heart disease - has subcategories"),
        ("I21", "Acute myocardial infarction - has subcategories"),
        ("E11", "Type 2 diabetes mellitus - has subcategories"),
        ("I25.1", "Specific code - may not have subcategories"),
        ("J18", "Pneumonia - has subcategories"),
    ]
    
    for code, description in test_cases:
        print(f"\n📝 Test: '{code}' ({description})")
        print("-" * 80)
        
        try:
            result = select_icd10_code(code)
            
            if result.get("status") == "success":
                print(f"✅ Selected: [{result.get('selected_code')}] {result.get('selected_name')}")
                
                subcats = result.get("subcategories", {})
                children = subcats.get("children", [])
                
                if children:
                    print(f"   Found {len(children)} subcategories:")
                    for i, sub in enumerate(children[:5], 1):  # Show first 5
                        print(f"  {i}. [{sub['code']}] {sub['name']}")
                else:
                    print("   No subcategories (likely most specific code)")
            else:
                print(f"❌ Status: {result['status']}")
                print(f"   Message: {result.get('message', 'N/A')}")
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()


def test_get_icd10_statistics():
    """Test statistics retrieval"""
    print("\n" + "="*80)
    print("TEST 4: get_icd10_statistics() - Database Stats")
    print("="*80)
    
    try:
        result = get_icd10_statistics()
        
        # Result format: {"total_codes": ..., "total_categories": ..., ...}
        if result:
            print("✅ Statistics retrieved:")
            print(f"   Total codes: {result.get('total_codes', 0):,}")
            print(f"   Total categories: {result.get('total_categories', 0):,}")
            print(f"   Total subcategories: {result.get('total_subcategories', 0):,}")
            print(f"   Database source: {result.get('database_source', 'N/A')}")
        else:
            print("❌ No statistics returned")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests"""
    print("\n" + "🧪"*40)
    print("ICD-10 SERVICE TEST SUITE")
    print("Testing: services/icd10_service.py")
    print("🧪"*40)
    
    try:
        # Test 1: Partial search
        test_db_search_partial()
        
        # Test 2: Main lookup with ranking
        test_lookup_icd10_basic()
        
        # Test 3: Code selection
        test_select_icd10_code()
        
        # Test 4: Statistics
        test_get_icd10_statistics()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
