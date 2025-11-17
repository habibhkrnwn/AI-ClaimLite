"""
Test Script untuk Dokumen Wajib Service
"""

from services.dokumen_wajib_service import get_dokumen_wajib_service
from lite_endpoints import (
    endpoint_get_dokumen_wajib,
    endpoint_get_all_diagnosis,
    endpoint_search_diagnosis
)
import json


def print_separator(title):
    """Print separator dengan title"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_service_get_dokumen_wajib():
    """Test service langsung"""
    print_separator("TEST 1: Service - Get Dokumen Wajib untuk Pneumonia")
    
    try:
        service = get_dokumen_wajib_service()
        result = service.get_dokumen_wajib_by_diagnosis("Pneumonia")
        
        print(f"\n✅ Diagnosis: {result['diagnosis']}")
        print(f"📊 Total Dokumen: {result['total_dokumen']}")
        
        print(f"\n📋 LIST DOKUMEN:")
        for dok in result['dokumen_list']:
            # Icon berdasarkan status
            if dok['status'].lower() == 'wajib':
                icon = "☑"
            elif dok['status'].lower() == 'opsional':
                icon = "○"
            else:
                icon = "◉"
            
            print(f"   {icon} {dok['nama_dokumen']} - {dok['status'].upper()}")
            print(f"      → {dok['keterangan'][:80]}...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def test_service_get_all_diagnosis():
    """Test get all diagnosis"""
    print_separator("TEST 2: Service - Get All Diagnosis")
    
    try:
        service = get_dokumen_wajib_service()
        diagnosis_list = service.get_all_diagnosis_list()
        
        print(f"\n✅ Total Diagnosis: {len(diagnosis_list)}")
        print(f"\n📋 List Diagnosis:")
        for i, diagnosis in enumerate(diagnosis_list, 1):
            print(f"   {i}. {diagnosis}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def test_service_search_diagnosis():
    """Test search diagnosis"""
    print_separator("TEST 3: Service - Search Diagnosis")
    
    keywords = ["pneumo", "HAP", "ventilator"]
    
    try:
        service = get_dokumen_wajib_service()
        
        for keyword in keywords:
            print(f"\n🔍 Searching for: '{keyword}'")
            results = service.search_diagnosis(keyword)
            
            if results:
                print(f"   ✅ Found {len(results)} result(s):")
                for diagnosis in results:
                    print(f"      - {diagnosis}")
            else:
                print(f"   ℹ️ No results found")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def test_endpoint_get_dokumen_wajib():
    """Test endpoint get dokumen wajib"""
    print_separator("TEST 4: Endpoint - Get Dokumen Wajib")
    
    test_cases = [
        {"diagnosis": "Pneumonia"},
        {"diagnosis": "Hospital-Acquired Pneumonia (HAP)"},
        {"diagnosis": "Ventilator-Associated Pneumonia (VAP)"}
    ]
    
    for test_data in test_cases:
        print(f"\n🧪 Testing with: {test_data['diagnosis']}")
        
        try:
            result = endpoint_get_dokumen_wajib(test_data)
            
            if result['status'] == 'success':
                print(f"   ✅ Status: {result['status']}")
                print(f"   📊 Total Dokumen: {result['total_dokumen']}")
                
                # Tampilkan 3 dokumen pertama saja
                print(f"   📋 List Dokumen:")
                for dok in result['dokumen_list']:
                    # Icon berdasarkan status
                    if dok['status'].lower() == 'wajib':
                        icon = "☑"
                    elif dok['status'].lower() == 'opsional':
                        icon = "○"
                    else:
                        icon = "◉"
                    print(f"      {icon} {dok['nama_dokumen']} - {dok['status'].upper()}")
            else:
                print(f"   ❌ Status: {result['status']}")
                print(f"   ❌ Message: {result.get('message')}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")


def test_endpoint_get_all_diagnosis():
    """Test endpoint get all diagnosis"""
    print_separator("TEST 5: Endpoint - Get All Diagnosis")
    
    try:
        result = endpoint_get_all_diagnosis()
        
        if result['status'] == 'success':
            print(f"\n✅ Status: {result['status']}")
            print(f"📊 Total: {result['total']}")
            print(f"\n📋 Diagnosis List (first 10):")
            for diagnosis in result['diagnosis_list'][:10]:
                print(f"   - {diagnosis}")
        else:
            print(f"❌ Status: {result['status']}")
            print(f"❌ Message: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def test_endpoint_search_diagnosis():
    """Test endpoint search diagnosis"""
    print_separator("TEST 6: Endpoint - Search Diagnosis")
    
    test_keywords = [
        {"keyword": "pneumo"},
        {"keyword": "HAP"},
        {"keyword": "ventilator"}
    ]
    
    for test_data in test_keywords:
        print(f"\n🔍 Testing search: '{test_data['keyword']}'")
        
        try:
            result = endpoint_search_diagnosis(test_data)
            
            if result['status'] == 'success':
                print(f"   ✅ Status: {result['status']}")
                print(f"   📊 Total Found: {result['total']}")
                if result['total'] > 0:
                    print(f"   📋 Results:")
                    for diagnosis in result['diagnosis_list']:
                        print(f"      - {diagnosis}")
            else:
                print(f"   ❌ Status: {result['status']}")
                print(f"   ❌ Message: {result.get('message')}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")


def test_error_handling():
    """Test error handling"""
    print_separator("TEST 7: Error Handling")
    
    # Test missing diagnosis
    print("\n🧪 Test 1: Missing diagnosis parameter")
    try:
        result = endpoint_get_dokumen_wajib({})
        print(f"   Status: {result['status']}")
        print(f"   Message: {result.get('message')}")
        print(f"   Error Code: {result.get('error_code')}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test diagnosis not found
    print("\n🧪 Test 2: Diagnosis tidak ditemukan")
    try:
        result = endpoint_get_dokumen_wajib({"diagnosis": "DiagnosisTidakAda123"})
        print(f"   Status: {result['status']}")
        print(f"   Message: {result.get('message', 'No message')}")
        print(f"   Total Dokumen: {result.get('total_dokumen', 0)}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test missing keyword
    print("\n🧪 Test 3: Missing keyword parameter")
    try:
        result = endpoint_search_diagnosis({})
        print(f"   Status: {result['status']}")
        print(f"   Message: {result.get('message')}")
        print(f"   Error Code: {result.get('error_code')}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  🧪 DOKUMEN WAJIB SERVICE - TEST SUITE")
    print("=" * 70)
    
    # Service tests
    test_service_get_dokumen_wajib()
    test_service_get_all_diagnosis()
    test_service_search_diagnosis()
    
    # Endpoint tests
    test_endpoint_get_dokumen_wajib()
    test_endpoint_get_all_diagnosis()
    test_endpoint_search_diagnosis()
    
    # Error handling tests
    test_error_handling()
    
    print("\n" + "=" * 70)
    print("  ✅ ALL TESTS COMPLETED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
