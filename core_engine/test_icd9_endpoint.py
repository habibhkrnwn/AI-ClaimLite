"""
Quick test for ICD-9 endpoint
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_icd9_endpoint():
    """Test ICD-9 lookup endpoint"""
    
    print("=" * 70)
    print("ICD-9 ENDPOINT TEST")
    print("=" * 70)
    
    # Test cases
    test_cases = [
        {
            "name": "Test 1: Exact Match (case-insensitive)",
            "input": "other chest x-ray",
            "expected_status": "success"
        },
        {
            "name": "Test 2: Indonesian Input (AI normalization)",
            "input": "rontgen thorax",
            "expected_status": "success"  # or "suggestions"
        },
        {
            "name": "Test 3: Vague Input (should get suggestions)",
            "input": "x-ray",
            "expected_status": "suggestions"  # Multiple body parts
        },
        {
            "name": "Test 4: Random invalid input",
            "input": "random xyz procedure 123",
            "expected_status": "not_found"
        }
    ]
    
    for test in test_cases:
        print(f"\n{test['name']}")
        print(f"Input: '{test['input']}'")
        print("-" * 70)
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/lite/icd9/lookup",
                json={"procedure_input": test['input']},
                timeout=30
            )
            
            data = response.json()
            
            if data['status'] == 'success':
                result_data = data['data']
                print(f"✅ Status: {result_data['status']}")
                
                if result_data['status'] == 'success':
                    print(f"   Code: {result_data['result']['code']}")
                    print(f"   Name: {result_data['result']['name']}")
                    print(f"   Confidence: {result_data['result']['confidence']}%")
                    print(f"   Source: {result_data['result']['source']}")
                elif result_data['status'] == 'suggestions':
                    print(f"   Needs Selection: {result_data['needs_selection']}")
                    print(f"   Suggestions ({len(result_data['suggestions'])} items):")
                    for i, sug in enumerate(result_data['suggestions'][:3], 1):
                        print(f"     {i}. {sug['name']} ({sug['code']})")
                else:
                    print(f"   Message: {result_data.get('message', 'N/A')}")
            else:
                print(f"❌ Error: {data.get('message', 'Unknown error')}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection error. Is the server running?")
            print("   Run: uvicorn main:app --reload")
            break
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    test_icd9_endpoint()
