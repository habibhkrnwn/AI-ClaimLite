"""
Test INA-CBG Prediction API
===========================

Script untuk testing endpoint INA-CBG prediction
Menguji berbagai skenario:
1. Request dengan data lengkap
2. Request minimal (hanya icd10_primary)
3. Request dengan ICD9 procedures
4. Request dengan secondary diagnoses
5. Different layanan (RI vs RJ)
6. Different regional/kelas

Usage:
    python test_inacbg_api.py
"""

import requests
import json
from datetime import datetime

# Base URL
BASE_URL = "http://localhost:8003"
ENDPOINT = f"{BASE_URL}/api/lite/predict-inacbg"


def print_result(test_name, response):
    """Print test result in readable format"""
    print("\n" + "="*80)
    print(f"TEST: {test_name}")
    print("="*80)
    print(f"Status Code: {response.status_code}")
    print(f"\nResponse:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


def test_complete_request():
    """Test dengan data lengkap - AMI dengan PCI"""
    payload = {
        "icd10_primary": "I21.0",
        "icd10_secondary": ["E11.9", "I25.1"],
        "icd9_list": ["36.06", "36.07"],
        "layanan": "RI",
        "regional": "1",
        "kelas_rs": "B",
        "tipe_rs": "Pemerintah",
        "kelas_bpjs": 1
    }
    
    response = requests.post(ENDPOINT, json=payload)
    print_result("Complete Request - AMI dengan PCI", response)
    return response


def test_minimal_request():
    """Test dengan data minimal"""
    payload = {
        "icd10_primary": "A09.0",
        "layanan": "RJ",
        "regional": "2",
        "kelas_rs": "C",
        "tipe_rs": "Swasta",
        "kelas_bpjs": 2
    }
    
    response = requests.post(ENDPOINT, json=payload)
    print_result("Minimal Request - Gastroenteritis RJ", response)
    return response


def test_with_procedures():
    """Test dengan ICD9 procedures"""
    payload = {
        "icd10_primary": "K35.8",
        "icd9_list": ["47.09"],  # Appendectomy
        "layanan": "RI",
        "regional": "3",
        "kelas_rs": "B",
        "tipe_rs": "Pemerintah",
        "kelas_bpjs": 1
    }
    
    response = requests.post(ENDPOINT, json=payload)
    print_result("With Procedures - Appendicitis dengan Appendectomy", response)
    return response


def test_with_secondary_diagnoses():
    """Test dengan multiple secondary diagnoses"""
    payload = {
        "icd10_primary": "J18.9",
        "icd10_secondary": ["E11.9", "I10", "N18.9"],
        "layanan": "RI",
        "regional": "1",
        "kelas_rs": "A",
        "tipe_rs": "Pemerintah",
        "kelas_bpjs": 1
    }
    
    response = requests.post(ENDPOINT, json=payload)
    print_result("Multiple Secondary Diagnoses - Pneumonia dengan comorbid", response)
    return response


def test_different_regional():
    """Test different regional tarifs"""
    base_payload = {
        "icd10_primary": "I21.0",
        "icd9_list": ["36.06"],
        "layanan": "RI",
        "kelas_rs": "B",
        "tipe_rs": "Pemerintah",
        "kelas_bpjs": 1
    }
    
    for regional in ["1", "2", "3", "4", "5"]:
        payload = {**base_payload, "regional": regional}
        response = requests.post(ENDPOINT, json=payload)
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            tarif = data.get("tarif", 0)
            print(f"\nRegional {regional}: Rp {tarif:,}")
        else:
            print(f"\nRegional {regional}: Error - {response.json()}")


def test_ri_vs_rj():
    """Test perbedaan RI vs RJ untuk diagnosis yang sama"""
    base_payload = {
        "icd10_primary": "A09.0",
        "regional": "1",
        "kelas_rs": "B",
        "tipe_rs": "Pemerintah",
        "kelas_bpjs": 1
    }
    
    print("\n" + "="*80)
    print("TEST: RI vs RJ - Gastroenteritis")
    print("="*80)
    
    for layanan in ["RI", "RJ"]:
        payload = {**base_payload, "layanan": layanan}
        response = requests.post(ENDPOINT, json=payload)
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            cbg_code = data.get("cbg_code", "N/A")
            tarif = data.get("tarif", 0)
            confidence = data.get("matching_detail", {}).get("confidence", 0)
            print(f"\n{layanan}:")
            print(f"  CBG Code: {cbg_code}")
            print(f"  Tarif: Rp {tarif:,}")
            print(f"  Confidence: {confidence:.2%}")
        else:
            print(f"\n{layanan}: Error - {response.json()}")


def test_kelas_bpjs_variation():
    """Test perbedaan tarif untuk kelas BPJS berbeda"""
    base_payload = {
        "icd10_primary": "I21.0",
        "icd9_list": ["36.06"],
        "layanan": "RI",
        "regional": "1",
        "kelas_rs": "B",
        "tipe_rs": "Pemerintah"
    }
    
    print("\n" + "="*80)
    print("TEST: Kelas BPJS Variation - AMI dengan PCI")
    print("="*80)
    
    for kelas in [1, 2, 3]:
        payload = {**base_payload, "kelas_bpjs": kelas}
        response = requests.post(ENDPOINT, json=payload)
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            tarif = data.get("tarif", 0)
            print(f"\nKelas {kelas}: Rp {tarif:,}")
        else:
            print(f"\nKelas {kelas}: Error - {response.json()}")


def test_error_handling():
    """Test error handling"""
    print("\n" + "="*80)
    print("TEST: Error Handling")
    print("="*80)
    
    # Test 1: Missing icd10_primary
    print("\n1. Missing icd10_primary:")
    payload = {
        "layanan": "RI",
        "regional": "1",
        "kelas_rs": "B",
        "tipe_rs": "Pemerintah",
        "kelas_bpjs": 1
    }
    response = requests.post(ENDPOINT, json=payload)
    print(f"   Status: {response.status_code}")
    print(f"   Message: {response.json().get('message')}")
    
    # Test 2: Invalid layanan
    print("\n2. Invalid layanan:")
    payload = {
        "icd10_primary": "I21.0",
        "layanan": "INVALID",
        "regional": "1",
        "kelas_rs": "B",
        "tipe_rs": "Pemerintah",
        "kelas_bpjs": 1
    }
    response = requests.post(ENDPOINT, json=payload)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test 3: Invalid regional
    print("\n3. Invalid regional:")
    payload = {
        "icd10_primary": "I21.0",
        "layanan": "RI",
        "regional": "99",
        "kelas_rs": "B",
        "tipe_rs": "Pemerintah",
        "kelas_bpjs": 1
    }
    response = requests.post(ENDPOINT, json=payload)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")


def main():
    """Run all tests"""
    print("\n🧪 TESTING INA-CBG PREDICTION API")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Endpoint: {ENDPOINT}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Check if server is running
        health_check = requests.get(f"{BASE_URL}/health")
        if health_check.status_code != 200:
            print("\n❌ Server is not running or not healthy!")
            return
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server. Is it running?")
        print("   Start with: python main.py")
        return
    
    print("\n✅ Server is running\n")
    
    # Run tests
    tests = [
        ("Complete Request", test_complete_request),
        ("Minimal Request", test_minimal_request),
        ("With Procedures", test_with_procedures),
        ("With Secondary Diagnoses", test_with_secondary_diagnoses),
        ("Different Regional", test_different_regional),
        ("RI vs RJ", test_ri_vs_rj),
        ("Kelas BPJS Variation", test_kelas_bpjs_variation),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            if isinstance(result, requests.Response):
                results.append((test_name, result.status_code == 200))
            else:
                results.append((test_name, True))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
