from services.icd9_smart_service import lookup_icd9_procedure

tests = [
    ('rontgen thorax', 'Indonesian chest x-ray'),
    ('suntik antibiotik', 'Indonesian antibiotic injection'),
    ('nebulizer', 'Nebulizer therapy'),
    ('cuci darah', 'Indonesian hemodialysis'),
    ('Routine chest x-ray, so described', 'Exact English term')
]

print("\n" + "="*70)
print("  🧪 ICD-9 RAG ENHANCEMENT - QUICK TEST")
print("="*70)

for input_text, description in tests:
    print(f"\n📝 {description}: '{input_text}'")
    result = lookup_icd9_procedure(input_text)
    
    if result['status'] == 'success':
        print(f"   ✅ SUCCESS: {result['result']['code']} - {result['result']['name']}")
    elif result['status'] == 'suggestions':
        print(f"   🔍 SUGGESTIONS ({len(result['suggestions'])}): {result['suggestions'][0]['code']} - {result['suggestions'][0]['name']}, ...")
    else:
        print(f"   ❌ NOT FOUND")

print("\n" + "="*70)
print("✅ All tests completed!")
print("="*70 + "\n")
