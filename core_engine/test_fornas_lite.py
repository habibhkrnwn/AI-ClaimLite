"""
Test FORNAS Lite Validation

Test script untuk validasi FORNAS Lite integration
"""

import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.fornas_lite_service import validate_fornas_lite, FornasLiteValidator
from lite_endpoints import endpoint_validate_fornas, endpoint_analyze_single


def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_fornas_lite_service():
    """Test FORNAS Lite Service directly"""
    print_section("TEST 1: FORNAS Lite Service (Direct)")
    
    test_data = {
        "diagnosis_icd10": "J18.9",
        "diagnosis_name": "Pneumonia berat",
        "drug_list": [
            "Ceftriaxone 1g IV",
            "Paracetamol 500mg",
            "Levofloxacin 500mg"
        ]
    }
    
    print(f"\n📋 Input:")
    print(f"   Diagnosis: {test_data['diagnosis_name']} ({test_data['diagnosis_icd10']})")
    print(f"   Obat: {', '.join(test_data['drug_list'])}")
    
    try:
        result = validate_fornas_lite(
            drug_list=test_data["drug_list"],
            diagnosis_icd10=test_data["diagnosis_icd10"],
            diagnosis_name=test_data["diagnosis_name"]
        )
        
        print("\n✅ Validation Success!")
        print("\n📊 FORNAS VALIDATION TABLE:")
        print("-" * 80)
        
        for v in result["fornas_validation"]:
            print(f"\n{v['no']}. {v['nama_obat']}")
            print(f"   Kelas Terapi  : {v['kelas_terapi']}")
            print(f"   Status        : {v['status_fornas']}")
            print(f"   Catatan AI    : {v['catatan_ai']}")
            print(f"   Sumber        : {v['sumber_regulasi']}")
        
        print("\n" + "-" * 80)
        summary = result["summary"]
        print(f"📈 SUMMARY:")
        print(f"   Total obat            : {summary['total_obat']}")
        print(f"   ✅ Sesuai             : {summary['sesuai']}")
        print(f"   ⚠️ Perlu Justifikasi  : {summary['perlu_justifikasi']}")
        print(f"   ❌ Non-Fornas         : {summary['non_fornas']}")
        print(f"   Update                : {summary['update_date']}")
        print(f"   Status DB             : {summary['status_database']}")
        
        return True
    
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fornas_endpoint():
    """Test FORNAS endpoint"""
    print_section("TEST 2: FORNAS Endpoint (Standalone)")
    
    request = {
        "diagnosis_icd10": "E11.9",
        "diagnosis_name": "Diabetes Mellitus Tipe 2",
        "obat": ["Metformin 500mg", "Glimepiride 2mg", "Insulin Aspart"]
    }
    
    print(f"\n📋 Request:")
    print(json.dumps(request, indent=2, ensure_ascii=False))
    
    try:
        response = endpoint_validate_fornas(request)
        
        print(f"\n✅ Response Status: {response['status']}")
        
        if response['status'] == 'success':
            print("\n📊 Validation Results:")
            for v in response["fornas_validation"]:
                status_emoji = v['status_fornas'][:2]  # Extract emoji
                print(f"   {status_emoji} {v['nama_obat']} - {v['catatan_ai'][:50]}...")
            
            summary = response["summary"]
            print(f"\n📈 Summary: {summary['sesuai']} sesuai, {summary['perlu_justifikasi']} perlu justifikasi, {summary['non_fornas']} non-fornas")
        
        return response['status'] == 'success'
    
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integrated_analyze():
    """Test integrated analysis dengan FORNAS"""
    print_section("TEST 3: Integrated Analysis (Full Flow)")
    
    request = {
        "mode": "form",
        "diagnosis": "Pneumonia berat (J18.9)",
        "tindakan": "Nebulisasi, Rontgen Thorax",
        "obat": "Ceftriaxone 1g IV, Paracetamol 500mg, Salbutamol nebul"
    }
    
    print(f"\n📋 Request (Form Mode):")
    print(f"   Diagnosis: {request['diagnosis']}")
    print(f"   Tindakan: {request['tindakan']}")
    print(f"   Obat: {request['obat']}")
    
    try:
        response = endpoint_analyze_single(request)
        
        print(f"\n✅ Analysis Status: {response.get('status', 'unknown')}")
        
        if response.get('status') == 'success':
            result = response['result']
            
            # Check if FORNAS validation is included
            if 'fornas_validation' in result:
                print(f"\n📊 FORNAS Validation Found: {len(result['fornas_validation'])} obat")
                
                for v in result['fornas_validation']:
                    print(f"   • {v['nama_obat']}: {v['status_fornas']}")
                
                if 'fornas_summary' in result:
                    summary = result['fornas_summary']
                    print(f"\n📈 FORNAS Summary:")
                    print(f"   Total: {summary.get('total_obat', 0)}")
                    print(f"   Sesuai: {summary.get('sesuai', 0)}")
            else:
                print("\n⚠️ FORNAS validation NOT found in result")
            
            print(f"\n💡 AI Insight: {result.get('insight_ai', 'N/A')}")
        
        return response.get('status') == 'success'
    
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test edge cases"""
    print_section("TEST 4: Edge Cases")
    
    # Test 1: Empty drug list
    print("\n🔹 Test 4.1: Empty drug list")
    try:
        result = validate_fornas_lite([], "J18.9", "Pneumonia")
        print(f"   Result: {result['summary']}")
        print("   ✅ Handled gracefully")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 2: Non-FORNAS drug
    print("\n🔹 Test 4.2: Non-FORNAS drug")
    try:
        result = validate_fornas_lite(
            ["UnknownDrug999"],
            "J18.9",
            "Pneumonia"
        )
        v = result["fornas_validation"][0]
        print(f"   Status: {v['status_fornas']}")
        print(f"   Catatan: {v['catatan_ai']}")
        print("   ✅ Handled gracefully")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 3: Drug with dosage variations
    print("\n🔹 Test 4.3: Drug with various dosage formats")
    try:
        result = validate_fornas_lite(
            [
                "Ceftriaxone 1g IV",
                "Ceftriaxone injeksi 2g/24jam",
                "Ceftriaxone"
            ],
            "J18.9",
            "Pneumonia"
        )
        print(f"   Matched: {len(result['fornas_validation'])} variants")
        print("   ✅ All variants handled")
    except Exception as e:
        print(f"   ❌ Failed: {e}")


def main():
    """Run all tests"""
    print("\n" + "🧪" * 40)
    print("  FORNAS LITE VALIDATION - COMPREHENSIVE TEST")
    print("🧪" * 40)
    
    results = {}
    
    # Run tests
    results["Test 1: Direct Service"] = test_fornas_lite_service()
    results["Test 2: Standalone Endpoint"] = test_fornas_endpoint()
    results["Test 3: Integrated Analysis"] = test_integrated_analyze()
    
    # Edge cases
    test_edge_cases()
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_flag in results.items():
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"   {status}  {test_name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n   🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f"\n   ⚠️ {total - passed} test(s) failed")
    
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
