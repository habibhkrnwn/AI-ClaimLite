"""
Simple test untuk CP Ringkas - Windows compatible
"""

import os
import sys
import asyncio
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from services.lite_service import analyze_lite_single
import asyncpg


async def test_with_async_pnpk():
    """Test dengan pre-fetch PNPK data dari async context"""
    print("\n" + "="*80)
    print("TEST: CP Ringkas dengan Pre-fetch PNPK (Async)")
    print("="*80)
    
    # Create DB pool
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return
    
    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=3)
    print("DB Pool created")
    
    # Pre-fetch PNPK
    from services.pnpk_summary_service import PNPKSummaryService
    pnpk_service = PNPKSummaryService(pool)
    pnpk_data = await pnpk_service.get_pnpk_summary("Pneumonia", auto_match=True)
    
    if pnpk_data:
        print(f"PNPK Data fetched: {pnpk_data['diagnosis']} ({pnpk_data['total_stages']} stages)")
    else:
        print("PNPK Data NOT found")
    
    # Inject to payload
    payload = {
        "mode": "form",
        "diagnosis": "Pneumonia",
        "tindakan": "Nebulisasi",
        "obat": "Ceftriaxone 1g",
        "_pnpk_data": pnpk_data  # Inject pre-fetched data
    }
    
    # Call analyzer (synchronous, but with pre-fetched data)
    result = analyze_lite_single(payload, db_pool=None)  # No db_pool needed, data already provided
    
    # Check CP Ringkas
    cp_ringkas = result.get("cp_ringkas", [])
    print(f"\nCP Ringkas ({len(cp_ringkas)} items):")
    for i, step in enumerate(cp_ringkas, 1):
        print(f"  {i}. {step[:80]}...")
    
    # Check if it's from DB or warning
    if any("Data Clinical Pathway tidak tersedia" in step for step in cp_ringkas):
        print("\nRESULT: FAILED - Got warning message")
    elif any("Tahap" in step and len(step) > 50 for step in cp_ringkas):
        print("\nRESULT: SUCCESS - Got detailed PNPK data from DB!")
    elif any("Indikasi" in step or "Kriteria" in step for step in cp_ringkas):
        print("\nRESULT: PARTIAL - Got data from rules_master rawat_inap")
    elif any("Hari" in step for step in cp_ringkas):
        print("\nRESULT: FALLBACK - Got data from AI")
    else:
        print("\nRESULT: UNKNOWN format")
    
    await pool.close()
    print("\nDB Pool closed")


if __name__ == "__main__":
    asyncio.run(test_with_async_pnpk())
