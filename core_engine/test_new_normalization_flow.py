"""
Test New Normalization Flow
Test alur baru: Input → AI normalize ke medical term → DB search → Return semua recommendations

Expected behavior:
- Input: "jantung" → AI: "heart" → DB: semua diagnosis dengan "heart"
- Input: "paru basah" → AI: "pneumonia" → DB: semua diagnosis dengan "pneumonia"
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.icd10_ai_normalizer import lookup_icd10_smart_with_rag

print("=" * 80)
print("🧪 TEST NEW NORMALIZATION FLOW")
print("=" * 80)

test_cases = [
    {
        "input": "jantung",
        "expected_term": "heart",
        "description": "Indonesian word for heart"
    },
    {
        "input": "paru basah",
        "expected_term": "pneumonia",
        "description": "Indonesian for wet lung (pneumonia)"
    },
    {
        "input": "demam berdarah",
        "expected_term": "dengue",
        "description": "Indonesian for dengue hemorrhagic fever"
    },
    {
        "input": "diabetes",
        "expected_term": "diabetes",
        "description": "Already English medical term"
    },
]

for i, test in enumerate(test_cases, 1):
    print(f"\n{'=' * 80}")
    print(f"TEST {i}: '{test['input']}' ({test['description']})")
    print(f"Expected normalized term: '{test['expected_term']}'")
    print("=" * 80)
    
    result = lookup_icd10_smart_with_rag(test["input"])
    
    print(f"\n📊 RESULT:")
    print(f"   Flow: {result.get('flow')}")
    print(f"   AI Used: {result.get('ai_used')}")
    
    if result.get('normalized_term'):
        print(f"   Normalized Term: '{result['normalized_term']}'")
        print(f"   AI Confidence: {result.get('ai_confidence')}%")
        print(f"   AI Reasoning: {result.get('ai_reasoning')}")
    
    if result.get('suggestions'):
        suggestions = result['suggestions']
        print(f"\n   ✅ Found {len(suggestions)} recommendations:")
        print(f"   {'Code':<10} {'Diagnosis Name'}")
        print(f"   {'-' * 70}")
        for j, sugg in enumerate(suggestions[:10], 1):  # Show top 10
            print(f"   {j:2}. {sugg['code']:<10} {sugg['name'][:55]}")
    else:
        print(f"\n   ⚠️ No suggestions found")
    
    if result.get('message'):
        print(f"\n   Message: {result['message']}")

print("\n" + "=" * 80)
print("✅ TESTING COMPLETED!")
print("=" * 80)
print("\nKEY POINTS:")
print("- AI should ONLY normalize to medical term (not select specific diagnosis)")
print("- DB search should return ALL diagnoses containing normalized term")
print("- Results should NOT include subcategories (just main recommendations)")
