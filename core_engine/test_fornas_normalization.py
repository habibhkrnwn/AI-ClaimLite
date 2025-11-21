"""
Test FORNAS New Normalization Flow

Test alur baru:
1. Input (English/typo) → AI normalize ke Indonesian
2. Search DB → Return drug names (PANEL KIRI)  
3. User pilih drug → Get details sediaan_kekuatan + restriksi (PANEL KANAN)

Expected:
- Input: "ceftriaxone" → AI: "seftriakson" → DB: semua obat dengan "seftriakson"
- Input: "paracetamol" → AI: "parasetamol" → DB: semua obat dengan "parasetamol"
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.fornas_normalize_service import lookup_fornas_smart, get_drug_details

print("=" * 80)
print("🧪 TEST FORNAS NEW NORMALIZATION FLOW")
print("=" * 80)

test_cases = [
    {
        "input": "ceftriaxone",
        "expected_indonesian": "seftriakson",
        "description": "English → Indonesian transliteration"
    },
    {
        "input": "paracetamol",
        "expected_indonesian": "parasetamol",
        "description": "English → Indonesian (c→s transliteration)"
    },
    {
        "input": "fentanyl",
        "expected_indonesian": "fentanil",
        "description": "English → Indonesian (y→i)"
    },
    {
        "input": "metformin",
        "expected_indonesian": "metformin",
        "description": "Already correct Indonesian"
    },
]

for i, test in enumerate(test_cases, 1):
    print(f"\n{'=' * 80}")
    print(f"TEST {i}: '{test['input']}' ({test['description']})")
    print(f"Expected normalized: '{test['expected_indonesian']}'")
    print("=" * 80)
    
    # PANEL KIRI: Get recommendations
    result = lookup_fornas_smart(test["input"])
    
    print(f"\n📊 PANEL KIRI (Recommendations):")
    print(f"   Flow: {result.get('flow')}")
    print(f"   AI Used: {result.get('ai_used')}")
    
    if result.get('normalized_name'):
        print(f"   Normalized: '{result['normalized_name']}'")
        print(f"   AI Confidence: {result.get('ai_confidence')}%")
    
    if result.get('suggestions'):
        suggestions = result['suggestions']
        print(f"\n   ✅ Found {len(suggestions)} drug names:")
        print(f"   {'No':<4} {'Drug Name':<40} {'Variants'}")
        print(f"   {'-' * 70}")
        for j, sugg in enumerate(suggestions[:10], 1):
            print(f"   {j:<4} {sugg['obat_name']:<40} {sugg.get('variant_count', 1)}")
        
        # PANEL KANAN: Get details for first drug
        if suggestions:
            selected_drug = suggestions[0]['obat_name']
            print(f"\n📊 PANEL KANAN (Details for '{selected_drug}'):")
            
            details = get_drug_details(selected_drug)
            
            if details:
                print(f"   Found {len(details)} sediaan_kekuatan variants:")
                print(f"   {'No':<4} {'Sediaan & Kekuatan':<35} {'Restriksi'}")
                print(f"   {'-' * 70}")
                for k, detail in enumerate(details[:5], 1):
                    sediaan = detail['sediaan_kekuatan'] or 'N/A'
                    restriksi = detail['restriksi_penggunaan'] or 'Tidak ada'
                    print(f"   {k:<4} {sediaan:<35} {restriksi[:25]}")
            else:
                print("   ⚠️ No details found")
    else:
        print(f"\n   ⚠️ No suggestions found")
    
    if result.get('message'):
        print(f"\n   Message: {result['message']}")

print("\n" + "=" * 80)
print("✅ TESTING COMPLETED!")
print("=" * 80)
print("\nKEY POINTS:")
print("- AI normalizes English/typo → Indonesian drug name")
print("- PANEL KIRI: List of drug names (unique names with variant count)")
print("- PANEL KANAN: Details of sediaan_kekuatan + restriksi for selected drug")
print("- Database already in Indonesian, no need for further translation")
