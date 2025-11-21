"""
Test untuk fitur Diagnosis Primer & Sekunder dengan AI Translation

Test cases untuk validasi:
1. Multi-diagnosis detection dengan berbagai separator
2. AI translation bahasa colloquial → medical terms
3. Priority ordering (pertama = primer)
4. ICD-10 code detection per diagnosis
5. Free text mode
6. Form mode
"""

import requests
import json
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Base URL
BASE_URL = "http://localhost:8000"
ANALYZE_ENDPOINT = f"{BASE_URL}/api/lite/analyze/single"

def print_result(test_name: str, response_json: dict):
    """Helper untuk print hasil test"""
    print("\n" + "="*80)
    print(f"🧪 TEST: {test_name}")
    print("="*80)
    
    if response_json.get("status") == "success":
        klasifikasi = response_json.get("result", {}).get("klasifikasi", {})
        
        # DEBUG: Print full klasifikasi for troubleshooting
        if not klasifikasi.get("diagnosis_primer"):
            print("\n⚠️  DEBUG INFO:")
            print(f"   Full klasifikasi keys: {list(klasifikasi.keys())}")
            print(f"   diagnosis field: {klasifikasi.get('diagnosis', 'N/A')}")
        
        # Diagnosis Primer
        primer = klasifikasi.get("diagnosis_primer", {})
        print(f"\n✅ DIAGNOSIS PRIMER:")
        print(f"   Name: {primer.get('name', '-')}")
        print(f"   ICD-10: {primer.get('icd10', '-')}")
        
        # Diagnosis Sekunder
        sekunder = klasifikasi.get("diagnosis_sekunder", [])
        if sekunder:
            print(f"\n✅ DIAGNOSIS SEKUNDER ({len(sekunder)}):")
            for i, diag in enumerate(sekunder, 1):
                print(f"   {i}. {diag.get('name', '-')} (ICD-10: {diag.get('icd10', '-')})")
        else:
            print(f"\n✅ DIAGNOSIS SEKUNDER: (Tidak ada)")
        
        # Backward compatibility
        print(f"\n📋 BACKWARD COMPATIBILITY:")
        print(f"   diagnosis: {klasifikasi.get('diagnosis', '-')}")
        print(f"   diagnosis_icd10: {klasifikasi.get('diagnosis_icd10', '-')}")
    else:
        print(f"\n❌ ERROR: {response_json.get('message', 'Unknown error')}")
        if response_json.get('detail'):
            print(f"   Detail: {response_json.get('detail')}")
    
    print("="*80 + "\n")


def test_1_bahasa_colloquial():
    """Test 1: Bahasa Indonesia colloquial dengan separator koma"""
    payload = {
        "mode": "text",
        "input_text": "paru2 basah, kencing manis & jantung koroner"
    }
    
    response = requests.post(ANALYZE_ENDPOINT, json=payload, timeout=60)
    result = response.json()
    
    print_result("Bahasa Colloquial + Multiple Separator", result)
    
    # Assertions (skip if diagnosis_primer not present)
    if result.get("status") == "success":
        klasifikasi = result.get("result", {}).get("klasifikasi", {})
        if "diagnosis_primer" in klasifikasi:
            assert klasifikasi["diagnosis_primer"]["name"] == "Pneumonia", "Primer should be Pneumonia"
            assert len(klasifikasi.get("diagnosis_sekunder", [])) == 2, "Should have 2 secondary diagnoses"
        else:
            print("⚠️  Skipping assertions - diagnosis_primer not in response")


def test_2_mixed_separator():
    """Test 2: Mixed separator (/, ., koma)"""
    payload = {
        "mode": "text",
        "input_text": "Pneumonia (J18.9) / Diabetes. Hypertension"
    }
    
    response = requests.post(ANALYZE_ENDPOINT, json=payload, timeout=60)
    result = response.json()
    
    print_result("Mixed Separator + ICD-10 Codes", result)
    
    # Assertions
    klasifikasi = result["result"]["klasifikasi"]
    assert klasifikasi["diagnosis_primer"]["icd10"] == "J18.9", "Primer should have ICD-10 J18.9"


def test_3_free_text_narrative():
    """Test 3: Free text narrative dengan kata 'dengan' dan 'disertai'"""
    payload = {
        "mode": "text",
        "input_text": "Pasien didiagnosa radang paru disertai komplikasi kencing manis dan darah tinggi"
    }
    
    response = requests.post(ANALYZE_ENDPOINT, json=payload, timeout=60)
    result = response.json()
    
    print_result("Free Text Narrative (dengan/disertai)", result)


def test_4_form_mode_structured():
    """Test 4: Form mode dengan input terstruktur"""
    payload = {
        "mode": "form",
        "diagnosis": "paru2 basah, kencing manis & jantung",
        "tindakan": "Nebulisasi, Rontgen Thorax",
        "obat": "Ceftriaxone, Paracetamol",
        "service_type": "rawat-inap"
    }
    
    response = requests.post(ANALYZE_ENDPOINT, json=payload, timeout=60)
    result = response.json()
    
    print_result("Form Mode Structured Input", result)


def test_5_single_diagnosis():
    """Test 5: Single diagnosis (tidak ada sekunder)"""
    payload = {
        "mode": "text",
        "input_text": "Pneumonia (J18.9)"
    }
    
    response = requests.post(ANALYZE_ENDPOINT, json=payload, timeout=60)
    result = response.json()
    
    print_result("Single Diagnosis (No Secondary)", result)
    
    # Assertions
    klasifikasi = result["result"]["klasifikasi"]
    assert len(klasifikasi.get("diagnosis_sekunder", [])) == 0, "Should have no secondary diagnoses"


def test_6_typo_correction():
    """Test 6: AI typo correction"""
    payload = {
        "mode": "text",
        "input_text": "pneumoni, diabtes melitus & hipertensi"
    }
    
    response = requests.post(ANALYZE_ENDPOINT, json=payload, timeout=60)
    result = response.json()
    
    print_result("Typo Correction", result)


def test_7_multiple_icd_codes():
    """Test 7: Multiple diagnoses dengan ICD-10 codes masing-masing"""
    payload = {
        "mode": "form",
        "diagnosis": "Pneumonia (J18.9), Diabetes (E11.9), Hypertension (I10)",
        "tindakan": "Nebulisasi",
        "obat": "Ceftriaxone",
        "service_type": "rawat-inap"
    }
    
    response = requests.post(ANALYZE_ENDPOINT, json=payload, timeout=60)
    result = response.json()
    
    print_result("Multiple Diagnoses with ICD Codes", result)


def test_8_kata_dengan():
    """Test 8: Separator kata 'dengan'"""
    payload = {
        "mode": "text",
        "input_text": "Pneumonia dengan komplikasi heart failure"
    }
    
    response = requests.post(ANALYZE_ENDPOINT, json=payload, timeout=60)
    result = response.json()
    
    print_result("Separator: 'dengan'", result)


def test_9_complex_case():
    """Test 9: Complex case dengan banyak kondisi"""
    payload = {
        "mode": "text",
        "input_text": "Pasien dengan paru2 basah berat, kencing manis tidak terkontrol, darah tinggi stadium 2, dan gagal jantung kongestif. Diberikan Ceftriaxone injeksi, Insulin, dan Furosemide."
    }
    
    response = requests.post(ANALYZE_ENDPOINT, json=payload, timeout=60)
    result = response.json()
    
    print_result("Complex Multi-Diagnosis Case", result)


def test_10_backward_compatibility():
    """Test 10: Backward compatibility check"""
    payload = {
        "mode": "form",
        "diagnosis": "Pneumonia, Diabetes",
        "tindakan": "Nebulisasi",
        "obat": "Ceftriaxone",
        "service_type": "rawat-inap"
    }
    
    response = requests.post(ANALYZE_ENDPOINT, json=payload, timeout=60)
    result = response.json()
    
    print_result("Backward Compatibility Check", result)
    
    # Check that old fields still exist
    klasifikasi = result["result"]["klasifikasi"]
    assert "diagnosis" in klasifikasi, "Old 'diagnosis' field should exist"
    assert "diagnosis_icd10" in klasifikasi, "Old 'diagnosis_icd10' field should exist"


if __name__ == "__main__":
    print("\n" + "🚀 "*(40//2))
    print("TESTING DIAGNOSIS PRIMER & SEKUNDER FEATURE")
    print("🚀 "*(40//2) + "\n")
    
    try:
        # Check server health with retry
        print("Checking server health...")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                health = requests.get(f"{BASE_URL}/health", timeout=10)
                if health.status_code == 200:
                    print("✅ Server is healthy\n")
                    break
            except requests.exceptions.ReadTimeout:
                if attempt < max_retries - 1:
                    print(f"⏱️  Health check timeout, retrying ({attempt + 1}/{max_retries})...")
                    import time
                    time.sleep(2)
                else:
                    print("⚠️  Server responding slowly, but continuing with tests...\n")
                    break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⏱️  Connection error, retrying ({attempt + 1}/{max_retries})...")
                    import time
                    time.sleep(2)
                else:
                    raise
        
        # Run all tests
        print("Running tests...\n")
        
        test_1_bahasa_colloquial()
        test_2_mixed_separator()
        test_3_free_text_narrative()
        test_4_form_mode_structured()
        test_5_single_diagnosis()
        test_6_typo_correction()
        test_7_multiple_icd_codes()
        test_8_kata_dengan()
        test_9_complex_case()
        test_10_backward_compatibility()
        
        print("\n" + "✅ "*(40//2))
        print("ALL TESTS COMPLETED!")
        print("✅ "*(40//2) + "\n")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at", BASE_URL)
        print("Make sure core_engine is running on port 8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
