"""
Test ICD-9 Smart Service dengan RAG Enhancement

Test cases fokus pada:
1. Indonesian medical terms
2. Vague/incomplete input
3. Complex procedures
4. Database context injection
"""

from services.icd9_smart_service import lookup_icd9_procedure

def print_section(title: str):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_case(input_text: str, description: str):
    print(f"\n📝 TEST: {description}")
    print(f"   Input: '{input_text}'")
    print("-" * 70)
    
    result = lookup_icd9_procedure(input_text)
    
    print(f"   Status: {result['status']}")
    
    if result['status'] == 'success':
        print(f"   ✅ Matched:")
        print(f"      Code: {result['result']['code']}")
        print(f"      Name: {result['result']['name']}")
        print(f"      Source: {result['result']['source']}")
        print(f"      Confidence: {result['result']['confidence']}%")
    
    elif result['status'] == 'suggestions':
        print(f"   🔍 Multiple suggestions ({len(result['suggestions'])}):")
        for i, sug in enumerate(result['suggestions'][:3], 1):
            print(f"      {i}. {sug['code']} - {sug['name']}")
        print(f"   ⚠️  Needs user selection: {result['needs_selection']}")
    
    else:
        print(f"   ❌ Not found: {result.get('message', 'No match')}")
    
    print("-" * 70)
    return result

if __name__ == "__main__":
    print_section("🧪 ICD-9 RAG ENHANCEMENT TESTING")
    
    # Test 1: Indonesian medical terms (most common)
    print_section("TEST CATEGORY 1: Indonesian Medical Terms")
    
    test_case("rontgen thorax", "Chest X-ray (Indonesian)")
    test_case("rontgen dada", "Chest X-ray (Indonesian variant)")
    test_case("ct scan kepala", "CT scan head (Indonesian)")
    test_case("suntik antibiotik", "Antibiotic injection (Indonesian)")
    test_case("infus", "Intravenous infusion (Indonesian)")
    test_case("nebulizer", "Nebulization (Indonesian/English)")
    
    # Test 2: Vague/incomplete input
    print_section("TEST CATEGORY 2: Vague/Incomplete Input")
    
    test_case("x-ray", "Vague - just 'x-ray' (should suggest body parts)")
    test_case("injection", "Generic injection (should suggest types)")
    test_case("ct scan", "Generic CT scan (should suggest body parts)")
    
    # Test 3: Complex procedures
    print_section("TEST CATEGORY 3: Complex Medical Procedures")
    
    test_case("ventilator mekanik", "Mechanical ventilation (Indonesian)")
    test_case("cuci darah", "Hemodialysis (Indonesian slang)")
    test_case("transfusi darah", "Blood transfusion (Indonesian)")
    test_case("endoskopi", "Endoscopy (Indonesian)")
    test_case("ekg", "Electrocardiogram (abbreviation)")
    
    # Test 4: English exact terms
    print_section("TEST CATEGORY 4: English Medical Terms")
    
    test_case("Routine chest x-ray, so described", "Exact DB match (English)")
    test_case("Computerized axial tomography of head", "Exact CT scan term")
    test_case("Injection of antibiotic", "Exact injection term")
    
    # Test 5: Mixed/partial terms
    print_section("TEST CATEGORY 5: Mixed/Partial Terms")
    
    test_case("chest radiography", "Partial - radiography instead of x-ray")
    test_case("oxygen therapy", "English term")
    test_case("monitoring vital signs", "Common nursing procedure")
    
    print_section("✅ TESTING COMPLETED")
    
    print("\n📊 SUMMARY:")
    print("   - Indonesian terms should be normalized correctly")
    print("   - Vague inputs should return multiple relevant suggestions")
    print("   - Complex procedures should match with database context")
    print("   - Exact terms should match directly (100% confidence)")
    print("\n🎯 Expected improvement:")
    print("   - Better context awareness from database")
    print("   - More accurate Indonesian term mapping")
    print("   - Higher match rate with RAG enhancement")
