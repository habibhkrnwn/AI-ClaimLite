"""
Integration Test - Full End-to-End with Consistency Module
Tests the complete analyze_lite_single flow including consistency validation
"""

import sys
import os
import json
import asyncio
sys.path.insert(0, os.path.dirname(__file__))

from services.lite_service import analyze_lite_single
from database_connection import get_async_pool

async def test_integration():
    print("=" * 80)
    print("INTEGRATION TEST: analyze_lite_single with Consistency Module")
    print("=" * 80)
    
    # Get database pool
    db_pool = await get_async_pool()
    
    # Sample payload for Pneumonia case
    payload = {
        "claim_id": "TEST-001",
        "patient_data": {
            "name": "John Doe",
            "age": 45,
            "gender": "M"
        },
        "medical_data": {
            "diagnosis": "Pneumonia",
            "tindakan": ["Chest X-Ray", "Inhalation Therapy", "Nebulizer"],
            "obat": ["Ceftriaxone 1g", "Amoxicillin 500mg", "Salbutamol inhaler"]
        },
        "mode": "full"
    }
    
    print("\n[TEST] Analyzing claim with consistency validation...")
    print(f"Diagnosis: {payload['medical_data']['diagnosis']}")
    print(f"Procedures: {payload['medical_data']['tindakan']}")
    print(f"Medications: {payload['medical_data']['obat']}")
    
    try:
        # Run analysis
        result = await analyze_lite_single(payload, db_pool)
        
        # Extract consistency results
        if "konsistensi" in result:
            print("\n" + "=" * 80)
            print("CONSISTENCY VALIDATION RESULTS")
            print("=" * 80)
            
            konsistensi = result["konsistensi"]
            
            print("\n1. Diagnosis → Tindakan:")
            print(f"   Status: {konsistensi.get('dx_tx', {}).get('status', 'N/A')}")
            print(f"   Catatan: {konsistensi.get('dx_tx', {}).get('catatan', 'N/A')}")
            
            print("\n2. Diagnosis → Obat:")
            print(f"   Status: {konsistensi.get('dx_drug', {}).get('status', 'N/A')}")
            print(f"   Catatan: {konsistensi.get('dx_drug', {}).get('catatan', 'N/A')}")
            
            print("\n3. Tindakan → Obat:")
            print(f"   Status: {konsistensi.get('tx_drug', {}).get('status', 'N/A')}")
            print(f"   Catatan: {konsistensi.get('tx_drug', {}).get('catatan', 'N/A')}")
            
            print("\n" + "-" * 80)
            print(f"Overall Consistency Level: {konsistensi.get('tingkat_konsistensi', 'N/A')}")
            print(f"Score: {konsistensi.get('_score', 0)}/3.0")
            print("-" * 80)
            
            # Validate result structure
            assert "dx_tx" in konsistensi, "Missing dx_tx validation"
            assert "dx_drug" in konsistensi, "Missing dx_drug validation"
            assert "tx_drug" in konsistensi, "Missing tx_drug validation"
            assert "tingkat_konsistensi" in konsistensi, "Missing overall consistency level"
            assert "_score" in konsistensi, "Missing score"
            
            print("\n✅ Integration test PASSED - Consistency module working correctly!")
            
        else:
            print("\n❌ ERROR: No 'konsistensi' field in result")
            print(f"Result keys: {list(result.keys())}")
        
    except Exception as e:
        print(f"\n❌ ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close database pool
        await db_pool.close()
        print("\n[INFO] Database connection closed")

if __name__ == "__main__":
    asyncio.run(test_integration())
