"""
Test ICD-10 Hierarchy dengan AI Normalization
Input: Indonesian terms → Should normalize to medical terms
"""

from lite_endpoints import endpoint_icd10_hierarchy

print("=" * 70)
print("🧪 TEST ICD-10 HIERARCHY WITH AI NORMALIZATION")
print("=" * 70)

test_cases = [
    {"input": "hati", "expected": "hepatitis / liver disease"},
    {"input": "paru2 basah", "expected": "pneumonia"},
    {"input": "demam berdarah", "expected": "dengue"},
    {"input": "batuk pilek", "expected": "rhinitis / cough"},
]

for i, test in enumerate(test_cases, 1):
    print(f"\n{i}. TEST: '{test['input']}' → Expected: {test['expected']}")
    print("-" * 70)
    
    result = endpoint_icd10_hierarchy(
        {"search_term": test["input"]},
        db=None  # Service creates own session
    )
    
    if result["status"] == "success":
        categories = result["data"]["categories"]
        print(f"✅ Found {len(categories)} categories")
        
        if categories:
            top = categories[0]
            print(f"   Top result: [{top['headCode']}] {top['headName']}")
            print(f"   Subcategories: {top['count']}")
            if top.get('commonTerm'):
                print(f"   Common term: {top['commonTerm']}")
        else:
            print("⚠️  No categories returned")
    else:
        print(f"❌ Error: {result.get('message')}")

print("\n" + "=" * 70)
print("✅ Testing completed!")
print("=" * 70)
