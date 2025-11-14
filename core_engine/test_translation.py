#!/usr/bin/env python3
"""
Test OpenAI Translation Endpoint
"""

import requests
import json

# Test cases
test_cases = [
    {
        "term": "radang paru paru bakteri",
        "expected": "bacterial pneumonia"
    },
    {
        "term": "pneumonia cacar air",
        "expected": "varicella pneumonia"
    },
    {
        "term": "paru2 basah",
        "expected": "pneumonia"
    },
    {
        "term": "demam berdarah",
        "expected": "dengue hemorrhagic fever"
    }
]

def test_translation():
    """Test OpenAI translation endpoint"""
    
    print("🧪 Testing OpenAI Translation Endpoint\n")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    endpoint = "/api/lite/translate-medical"
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test['term']}")
        print(f"   Expected: {test['expected']}")
        
        try:
            response = requests.post(
                f"{base_url}{endpoint}",
                json={"term": test['term']},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    result = data.get('result', {})
                    medical_term = result.get('medical_term', '')
                    confidence = result.get('confidence', '')
                    
                    print(f"   ✅ Result: {medical_term}")
                    print(f"   📊 Confidence: {confidence}")
                    
                    # Check if result matches expected
                    if medical_term.lower() == test['expected'].lower():
                        print(f"   ✓ PASS - Exact match!")
                    elif test['expected'].lower() in medical_term.lower():
                        print(f"   ✓ PASS - Contains expected term")
                    else:
                        print(f"   ⚠ WARNING - Different result")
                else:
                    print(f"   ❌ FAILED: {data.get('message', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ ERROR: Cannot connect to {base_url}")
            print(f"   Make sure core_engine is running on port 8000")
            break
        except requests.exceptions.Timeout:
            print(f"   ❌ ERROR: Request timeout (>30s)")
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ Testing completed!\n")


if __name__ == "__main__":
    test_translation()
