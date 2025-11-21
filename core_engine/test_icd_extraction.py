"""
Test ICD-10 extraction dari input dengan kode dalam kurung
"""
import requests
import json
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

def test_icd_extraction():
    """Test apakah ICD-10 codes di-extract dari kurung"""
    
    test_cases = [
        {
            "name": "Single diagnosis with ICD-10",
            "input": "Pneumonia (J18.9)",
            "expected_primer": {"name": "Pneumonia", "icd10": "J18.9"}
        },
        {
            "name": "Multiple diagnosis with ICD-10",
            "input": "Pneumonia (J18.9), Diabetes (E11.9)",
            "expected_primer": {"name": "Pneumonia", "icd10": "J18.9"},
            "expected_sekunder": [
                {"name": "Diabetes", "icd10": "E11.9"}
            ]
        },
        {
            "name": "Mixed (with and without ICD-10)",
            "input": "Pneumonia (J18.9), Diabetes, Hypertension (I10)",
            "expected_primer": {"name": "Pneumonia", "icd10": "J18.9"},
            "expected_sekunder": [
                {"name": "Diabetes", "icd10": None},
                {"name": "Hypertension", "icd10": "I10"}
            ]
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"🧪 TEST {i}: {test['name']}")
        print(f"{'='*80}")
        print(f"📤 INPUT: {test['input']}")
        
        payload = {
            "mode": "text",
            "input_text": test['input']
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/lite/analyze/single",
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            if result.get("status") == "success":
                klasifikasi = result['result']['klasifikasi']
                primer = klasifikasi.get('diagnosis_primer', {})
                sekunder = klasifikasi.get('diagnosis_sekunder', [])
                
                print(f"\n📥 RESULT:")
                print(f"   Primer: {primer.get('name')} (ICD-10: {primer.get('icd10') or 'None'})")
                
                if sekunder:
                    print(f"   Sekunder ({len(sekunder)}):")
                    for j, diag in enumerate(sekunder, 1):
                        print(f"     {j}. {diag.get('name')} (ICD-10: {diag.get('icd10') or 'None'})")
                else:
                    print(f"   Sekunder: None")
                
                # Check results
                print(f"\n🔍 VALIDATION:")
                primer_ok = (
                    primer.get('name') == test['expected_primer']['name'] and
                    primer.get('icd10') == test['expected_primer']['icd10']
                )
                
                if primer_ok:
                    print(f"   ✅ Primer CORRECT")
                else:
                    print(f"   ❌ Primer WRONG")
                    print(f"      Expected: {test['expected_primer']}")
                    print(f"      Got: {primer}")
                
                if 'expected_sekunder' in test:
                    sekunder_ok = len(sekunder) == len(test['expected_sekunder'])
                    if sekunder_ok:
                        for exp, got in zip(test['expected_sekunder'], sekunder):
                            if exp['name'] != got.get('name') or exp['icd10'] != got.get('icd10'):
                                sekunder_ok = False
                                break
                    
                    if sekunder_ok:
                        print(f"   ✅ Sekunder CORRECT")
                    else:
                        print(f"   ❌ Sekunder WRONG")
                        print(f"      Expected: {test['expected_sekunder']}")
                        print(f"      Got: {sekunder}")
            else:
                print(f"\n❌ API Error: {result.get('message')}")
                
        except Exception as e:
            print(f"\n❌ Exception: {e}")
    
    print(f"\n{'='*80}")
    print(f"✅ TEST COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    test_icd_extraction()
