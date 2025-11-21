"""Quick test untuk verify OpenAI API key dan diagnosis multi feature"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("\n" + "="*80)
print("🧪 QUICK TEST - OpenAI & Diagnosis Multi Feature")
print("="*80 + "\n")

# Test 1: Simple parsing
print("Test 1: Simple AI Translation")
print("-" * 40)
payload = {
    "mode": "text",
    "input_text": "paru2 basah"
}

try:
    response = requests.post(f"{BASE_URL}/api/lite/parse-text", json=payload, timeout=30)
    result = response.json()
    
    if result.get("status") == "success":
        print("✅ OpenAI API Key WORKING!")
        print(f"   Input: paru2 basah")
        print(f"   Output: {result['result'].get('diagnosis', 'N/A')}")
    else:
        print(f"❌ Error: {result.get('message', 'Unknown error')}")
except Exception as e:
    print(f"❌ Connection error: {e}")

print("\n" + "-" * 40)

# Test 2: Multi-diagnosis detection
print("\nTest 2: Multi-Diagnosis Detection")
print("-" * 40)
payload2 = {
    "mode": "text",
    "input_text": "paru2 basah, kencing manis & jantung"
}

try:
    response2 = requests.post(f"{BASE_URL}/api/lite/analyze/single", json=payload2, timeout=60)
    result2 = response2.json()
    
    if result2.get("status") == "success":
        klasifikasi = result2["result"]["klasifikasi"]
        
        primer = klasifikasi.get("diagnosis_primer", {})
        sekunder = klasifikasi.get("diagnosis_sekunder", [])
        
        print("✅ Multi-Diagnosis Feature WORKING!")
        print(f"\n   📍 PRIMER: {primer.get('name', 'N/A')} (ICD-10: {primer.get('icd10', '-')})")
        
        if sekunder:
            print(f"   📍 SEKUNDER ({len(sekunder)}):")
            for i, diag in enumerate(sekunder, 1):
                print(f"      {i}. {diag.get('name', 'N/A')} (ICD-10: {diag.get('icd10', '-')})")
        else:
            print(f"   📍 SEKUNDER: None")
    else:
        print(f"❌ Error: {result2.get('message', 'Unknown error')}")
except Exception as e:
    print(f"❌ Connection error: {e}")

print("\n" + "="*80)
print("✅ QUICK TEST COMPLETED")
print("="*80 + "\n")
