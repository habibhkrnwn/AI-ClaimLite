"""
Debug script untuk melihat full JSON response dari API parsing
"""
import requests
import json
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

def test_parse_text():
    """Test /api/lite/parse-text endpoint dengan input sederhana"""
    
    print("="*80)
    print("🔍 DEBUG: Testing /api/lite/parse-text")
    print("="*80)
    
    payload = {
        "text": "pneumonia, diabetes & hipertensi",
        "input_mode": "text"
    }
    
    print(f"\n📤 REQUEST:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/lite/parse-text",
            json=payload,
            timeout=30
        )
        
        print(f"\n📥 RESPONSE STATUS: {response.status_code}")
        print(f"\n📥 FULL JSON RESPONSE:")
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Check for diagnosis_primer
        print(f"\n🔎 CHECKING FIELDS:")
        print(f"   - Has 'diagnosis_primer': {'diagnosis_primer' in result}")
        print(f"   - Has 'diagnosis_sekunder': {'diagnosis_sekunder' in result}")
        print(f"   - Has 'diagnosis': {'diagnosis' in result}")
        
        if 'diagnosis_primer' in result:
            print(f"\n✅ diagnosis_primer found:")
            print(json.dumps(result['diagnosis_primer'], indent=2, ensure_ascii=False))
        else:
            print(f"\n❌ diagnosis_primer NOT FOUND in response!")
        
        if 'diagnosis_sekunder' in result:
            print(f"\n✅ diagnosis_sekunder found:")
            print(json.dumps(result['diagnosis_sekunder'], indent=2, ensure_ascii=False))
        else:
            print(f"\n❌ diagnosis_sekunder NOT FOUND in response!")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

def test_analyze_single():
    """Test /api/lite/analyze/single endpoint"""
    
    print("\n" + "="*80)
    print("🔍 DEBUG: Testing /api/lite/analyze/single")
    print("="*80)
    
    payload = {
        "mode": "text",
        "input_text": "Pasien dengan pneumonia, diabetes & hipertensi"
    }
    
    print(f"\n📤 REQUEST:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/lite/analyze/single",
            json=payload,
            timeout=30
        )
        
        print(f"\n📥 RESPONSE STATUS: {response.status_code}")
        print(f"\n📥 FULL JSON RESPONSE:")
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Check klasifikasi section
        if 'klasifikasi' in result:
            klasifikasi = result['klasifikasi']
            print(f"\n🔎 CHECKING klasifikasi FIELDS:")
            print(f"   - Has 'diagnosis_primer': {'diagnosis_primer' in klasifikasi}")
            print(f"   - Has 'diagnosis_sekunder': {'diagnosis_sekunder' in klasifikasi}")
            
            if 'diagnosis_primer' in klasifikasi:
                print(f"\n✅ diagnosis_primer found in klasifikasi:")
                print(json.dumps(klasifikasi['diagnosis_primer'], indent=2, ensure_ascii=False))
            else:
                print(f"\n❌ diagnosis_primer NOT FOUND in klasifikasi!")
                
            if 'diagnosis_sekunder' in klasifikasi:
                print(f"\n✅ diagnosis_sekunder found in klasifikasi:")
                print(json.dumps(klasifikasi['diagnosis_sekunder'], indent=2, ensure_ascii=False))
            else:
                print(f"\n❌ diagnosis_sekunder NOT FOUND in klasifikasi!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_parse_text()
    test_analyze_single()
    print("\n" + "="*80)
    print("✅ DEBUG COMPLETE")
    print("="*80)
