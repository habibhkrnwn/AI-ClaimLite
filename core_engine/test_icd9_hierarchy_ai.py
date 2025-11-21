"""
Test ICD-9 Hierarchy Endpoint dengan AI Normalization
Purpose: Verify Indonesian → English translation works for ICD-9 procedures

Test Cases:
1. Indonesian terms: "rontgen thorax", "suntik antibiotik", "infus"
2. Informal terms: "nebulizer", "cuci darah"
3. English terms: "chest x-ray" (should work directly)

Expected Flow:
- Input Indonesian → AI normalize → English medical terms → Database search → Results
"""

import requests
import json

# Config
API_URL = "http://localhost:8000/api/lite/icd9-hierarchy"

def test_icd9_hierarchy(search_term: str, description: str):
    """
    Test ICD-9 hierarchy endpoint dengan AI normalization.
    
    Args:
        search_term: Input untuk test
        description: Deskripsi test case
    """
    print(f"\n{'='*80}")
    print(f"TEST: {description}")
    print(f"Input: '{search_term}'")
    print(f"{'='*80}")
    
    try:
        payload = {
            "search_term": search_term,
            "synonyms": []
        }
        
        response = requests.post(API_URL, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") == "success":
                result_data = data.get("data", {})
                categories = result_data.get("categories", [])
                
                # Count total procedures across all categories
                total_procedures = sum(cat.get('count', 0) for cat in categories)
                
                print(f"\n✅ SUCCESS")
                print(f"Found {len(categories)} categories with {total_procedures} total procedures")
                
                # Show top 5 categories
                if categories:
                    print(f"\nTop Categories:")
                    for i, cat in enumerate(categories[:5], 1):
                        print(f"  {i}. [{cat['headCode']}] {cat['headName']}")
                        print(f"     Count: {cat['count']}, Confidence: {cat['total_confidence']}")
                        
                        # Show sample details from this category
                        details = cat.get('details', [])
                        if details:
                            print(f"     Sample procedures in this category:")
                            for j, proc in enumerate(details[:3], 1):
                                print(f"       - {proc['code']}: {proc['name'][:60]}{'...' if len(proc['name']) > 60 else ''}")
                else:
                    print(f"\nNo categories found (empty result)")
                
            else:
                print(f"\n⚠️ Status: {data.get('status')}")
                print(f"Message: {data.get('message', 'No message')}")
                
                # Check if suggestions available
                suggestions = result_data.get("suggestions", []) if result_data else []
                if suggestions:
                    print(f"\nGot {len(suggestions)} suggestions:")
                    for i, sug in enumerate(suggestions[:5], 1):
                        print(f"  {i}. {sug.get('code')} - {sug.get('name')}")
        else:
            print(f"\n❌ HTTP Error {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except requests.Timeout:
        print(f"\n⏱️ TIMEOUT - Request took longer than 30 seconds")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


def main():
    """Run all test cases."""
    
    print("\n" + "="*80)
    print("ICD-9 HIERARCHY AI NORMALIZATION TEST SUITE")
    print("="*80)
    
    test_cases = [
        # Indonesian terms (should trigger AI normalization)
        ("rontgen thorax", "Indonesian - Chest X-ray"),
        ("rontgen dada", "Indonesian - Chest X-ray (alternative)"),
        ("suntik antibiotik", "Indonesian - Antibiotic Injection"),
        ("infus", "Indonesian - Infusion/IV"),
        ("nebulizer", "Indonesian/Informal - Nebulizer"),
        ("cuci darah", "Indonesian - Hemodialysis"),
        
        # Partial English terms (should work with database search)
        ("chest x-ray", "English - Chest X-ray"),
        ("injection", "English - Injection procedures"),
        ("ct scan", "English - CT Scan"),
        
        # Short/vague terms (AI should suggest multiple options)
        ("rontgen", "Vague - X-ray only (should suggest multiple body parts)"),
        ("operasi", "Indonesian - Surgery (should suggest multiple types)"),
    ]
    
    for search_term, description in test_cases:
        test_icd9_hierarchy(search_term, description)
        input("\nPress Enter to continue to next test...")
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETED")
    print("="*80)
    
    print("\n📊 SUMMARY:")
    print("- If Indonesian terms return results → AI normalization working ✅")
    print("- If Indonesian terms fail → Check OpenAI API key ⚠️")
    print("- If English terms work → Database search working ✅")
    print("- Check Docker logs: docker-compose logs -f core_engine")


if __name__ == "__main__":
    main()
