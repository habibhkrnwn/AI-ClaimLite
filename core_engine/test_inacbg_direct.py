"""
Quick Test - INA-CBG Service (Direct Function Call)
====================================================

Test the InacbgGrouperService directly without needing to run the API server.
This is useful for quick debugging and verification.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.inacbg_grouper_service import predict_inacbg
import json


def test_ami_with_pci():
    """Test AMI dengan PCI - expected high confidence"""
    print("\n" + "="*80)
    print("TEST 1: AMI dengan PCI (I21.0 + 36.06, 36.07)")
    print("="*80)
    
    result = predict_inacbg(
        icd10_primary="I21.0",
        icd10_secondary=["E11.9", "I25.1"],
        icd9_list=["36.06", "36.07"],
        layanan="RI",
        regional="1",
        kelas_rs="B",
        tipe_rs="Pemerintah",
        kelas_bpjs=1
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("success"):
        print(f"\n[SUCCESS]")
        print(f"   CBG Code: {result.get('cbg_code')}")
        print(f"   Tarif: Rp {result.get('tarif'):,}")
        print(f"   Confidence: {result.get('matching_detail', {}).get('confidence', 0):.2%}")
        print(f"   Strategy: {result.get('matching_detail', {}).get('strategy')}")
    else:
        print(f"\n[FAILED]: {result.get('error')}")
    
    return result


def test_simple_gastro():
    """Test simple gastroenteritis RJ"""
    print("\n" + "="*80)
    print("TEST 2: Simple Gastroenteritis RJ (A09.0)")
    print("="*80)
    
    result = predict_inacbg(
        icd10_primary="A09.0",
        layanan="RJ",
        regional="2",
        kelas_rs="C",
        tipe_rs="Swasta",
        kelas_bpjs=2
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("success"):
        print(f"\nâœ… SUCCESS")
        print(f"   CBG Code: {result.get('cbg_code')}")
        print(f"   Tarif: Rp {result.get('tarif'):,}")
        print(f"   Confidence: {result.get('matching_detail', {}).get('confidence', 0):.2%}")
    else:
        print(f"\nâŒ FAILED: {result.get('error')}")
    
    return result


def test_appendicitis_with_surgery():
    """Test appendicitis with appendectomy"""
    print("\n" + "="*80)
    print("TEST 3: Appendicitis dengan Appendectomy (K35.8 + 47.09)")
    print("="*80)
    
    result = predict_inacbg(
        icd10_primary="K35.8",
        icd9_list=["47.09"],
        layanan="RI",
        regional="3",
        kelas_rs="B",
        tipe_rs="Pemerintah",
        kelas_bpjs=1
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("success"):
        print(f"\nâœ… SUCCESS")
        print(f"   CBG Code: {result.get('cbg_code')}")
        print(f"   Tarif: Rp {result.get('tarif'):,}")
        print(f"   Confidence: {result.get('matching_detail', {}).get('confidence', 0):.2%}")
    else:
        print(f"\nâŒ FAILED: {result.get('error')}")
    
    return result


def test_pneumonia_with_comorbid():
    """Test pneumonia with multiple comorbidities"""
    print("\n" + "="*80)
    print("TEST 4: Pneumonia dengan Comorbid (J18.9 + E11.9, I10, N18.9)")
    print("="*80)
    
    result = predict_inacbg(
        icd10_primary="J18.9",
        icd10_secondary=["E11.9", "I10", "N18.9"],
        layanan="RI",
        regional="1",
        kelas_rs="A",
        tipe_rs="Pemerintah",
        kelas_bpjs=1
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("success"):
        print(f"\nâœ… SUCCESS")
        print(f"   CBG Code: {result.get('cbg_code')}")
        print(f"   Severity: {result.get('breakdown', {}).get('severity')} ({result.get('classification', {}).get('severity_count')} comorbid)")
        print(f"   Tarif: Rp {result.get('tarif'):,}")
        print(f"   Confidence: {result.get('matching_detail', {}).get('confidence', 0):.2%}")
    else:
        print(f"\nâŒ FAILED: {result.get('error')}")
    
    return result


def test_database_connection():
    """Test database connection"""
    print("\n" + "="*80)
    print("TEST: Database Connection")
    print("="*80)
    
    try:
        from database_connection import get_db_session
        from sqlalchemy import text
        
        with get_db_session() as db:
            # Test query inacbg_tarif
            result = db.execute(text("SELECT COUNT(*) FROM inacbg_tarif")).scalar()
            print(f"âœ… inacbg_tarif: {result:,} rows")
            
            # Test query cleaned_mapping_inacbg
            result = db.execute(text("SELECT COUNT(*) FROM cleaned_mapping_inacbg")).scalar()
            print(f"âœ… cleaned_mapping_inacbg: {result:,} rows")
            
            # Test query icd10_cmg_mapping
            result = db.execute(text("SELECT COUNT(*) FROM icd10_cmg_mapping")).scalar()
            print(f"âœ… icd10_cmg_mapping: {result:,} rows")
            
            # Test query icd9_procedure_info
            result = db.execute(text("SELECT COUNT(*) FROM icd9_procedure_info")).scalar()
            print(f"âœ… icd9_procedure_info: {result:,} rows")
            
            print("\nâœ… All tables accessible")
            return True
            
    except Exception as e:
        print(f"\nâŒ Database connection failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n[TEST] QUICK TEST - INA-CBG SERVICE")
    print("="*80)
    
    # Test database first
    if not test_database_connection():
        print("\nâŒ Cannot proceed without database connection")
        return
    
    # Run tests
    tests = [
        test_ami_with_pci,
        test_simple_gastro,
        test_appendicitis_with_surgery,
        test_pneumonia_with_comorbid
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__doc__, result.get("success", False)))
        except Exception as e:
            print(f"\nâŒ Exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__doc__, False))
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! API is ready to use.")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Check logs for details.")


if __name__ == "__main__":
    main()

