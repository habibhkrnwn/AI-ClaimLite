"""
Test CP Ringkas Panel
Mengecek mengapa CP ringkas selalu return warning/gagal
"""

import os
import sys
import asyncio
import json
from datetime import datetime
import asyncpg

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from services.lite_service import analyze_lite_single, get_parser
from services.pnpk_summary_service import PNPKSummaryService


async def create_db_pool():
    """Create asyncpg pool for testing"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("⚠️ DATABASE_URL not set in environment")
        return None
    
    try:
        # Convert SQLAlchemy URL to asyncpg format if needed
        asyncpg_url = database_url.replace("postgresql://", "postgresql://")
        
        pool = await asyncpg.create_pool(
            asyncpg_url,
            min_size=1,
            max_size=5,
            command_timeout=60
        )
        print(f"✓ AsyncPG pool created")
        return pool
    except Exception as e:
        print(f"✗ Failed to create pool: {e}")
        return None


async def test_pnpk_fetch():
    """Test 1: Cek apakah PNPK data bisa di-fetch dari DB"""
    print("\n" + "="*80)
    print("TEST 1: Fetch PNPK Data dari Database")
    print("="*80)
    
    try:
        db_pool = await create_db_pool()
        if not db_pool:
            print("✗ Cannot proceed without database pool")
            return
        
        print(f"✓ Database connection pool created")
        
        pnpk_service = PNPKSummaryService(db_pool)
        print(f"✓ PNPKSummaryService initialized")
        
        # Test beberapa diagnosis
        test_diagnoses = [
            "Pneumonia",
            "Hospital-Acquired Pneumonia",
            "HAP",
            "Pneumonia komunitas",
            "Community-Acquired Pneumonia"
        ]
        
        for diagnosis in test_diagnoses:
            print(f"\n--- Testing diagnosis: '{diagnosis}' ---")
            
            # Test search
            search_results = await pnpk_service.search_diagnoses(diagnosis, limit=3)
            print(f"Search results: {len(search_results)} matches")
            for i, result in enumerate(search_results[:3], 1):
                print(f"  {i}. {result['diagnosis_name']} (score: {result['match_score']:.2f})")
            
            # Test get summary
            pnpk_data = await pnpk_service.get_pnpk_summary(diagnosis, auto_match=True)
            if pnpk_data:
                print(f"✓ PNPK summary found!")
                print(f"  Diagnosis: {pnpk_data['diagnosis']}")
                print(f"  Total stages: {pnpk_data['total_stages']}")
                print(f"  Stages:")
                for stage in pnpk_data['stages'][:3]:  # Show first 3
                    print(f"    - {stage['stage_name']}: {stage['description'][:60]}...")
            else:
                print(f"✗ No PNPK summary found")
        
        await db_pool.close()
        print(f"\n✓ Database connection closed")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


def test_analyze_single_without_db():
    """Test 2: Analyze single tanpa DB pool (untuk lihat fallback)"""
    print("\n" + "="*80)
    print("TEST 2: Analyze Single TANPA DB Pool (Fallback ke AI)")
    print("="*80)
    
    payload = {
        "mode": "form",
        "diagnosis": "Pneumonia",
        "tindakan": "Nebulisasi, Rontgen Thorax",
        "obat": "Ceftriaxone 1g, Paracetamol 500mg"
    }
    
    print(f"\nInput payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        # Call WITHOUT db_pool
        result = analyze_lite_single(payload, db_pool=None)
        
        print(f"\n✓ Analysis completed")
        print(f"\nCP Ringkas result:")
        cp_ringkas = result.get("cp_ringkas", [])
        for i, step in enumerate(cp_ringkas, 1):
            print(f"  {i}. {step}")
        
        # Check if it's warning
        if any("⚠️" in step for step in cp_ringkas):
            print(f"\n⚠️ WARNING: CP Ringkas returned error/warning!")
            print(f"Expected: AI should generate CP ringkas as fallback")
        else:
            print(f"\n✓ CP Ringkas successfully generated")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_analyze_single_with_db():
    """Test 3: Analyze single dengan DB pool (untuk lihat DB fetch)"""
    print("\n" + "="*80)
    print("TEST 3: Analyze Single DENGAN DB Pool (Priority 1: DB PNPK)")
    print("="*80)
    
    payload = {
        "mode": "form",
        "diagnosis": "Pneumonia",
        "tindakan": "Nebulisasi, Rontgen Thorax",
        "obat": "Ceftriaxone 1g, Paracetamol 500mg"
    }
    
    print(f"\nInput payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        db_pool = await create_db_pool()
        if not db_pool:
            print("✗ Cannot proceed without database pool")
            return
        
        print(f"✓ Database pool created")
        
        # Call WITH db_pool
        result = analyze_lite_single(payload, db_pool=db_pool)
        
        print(f"\n✓ Analysis completed")
        print(f"\nCP Ringkas result:")
        cp_ringkas = result.get("cp_ringkas", [])
        for i, step in enumerate(cp_ringkas, 1):
            print(f"  {i}. {step}")
        
        # Check if it's warning
        if any("⚠️" in step for step in cp_ringkas):
            print(f"\n⚠️ WARNING: CP Ringkas returned error/warning!")
            print(f"This means:")
            print(f"  1. DB PNPK fetch failed")
            print(f"  2. DB rules (rawat_inap) not available")
            print(f"  3. AI fallback also failed")
        else:
            print(f"\n✓ CP Ringkas successfully generated")
            
            # Check source
            if "Tahap" in cp_ringkas[0] and ":" in cp_ringkas[0]:
                if len(cp_ringkas[0]) > 50:
                    print(f"Source: Likely from DB PNPK (detailed description)")
                else:
                    print(f"Source: Could be from AI or DB rules")
            elif "Hari" in cp_ringkas[0]:
                print(f"Source: Likely from AI (uses 'Hari' format)")
        
        await db_pool.close()
        print(f"\n✓ Database connection closed")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_diagnoses_in_db():
    """Test 4: Cek diagnosis apa saja yang ada di DB PNPK"""
    print("\n" + "="*80)
    print("TEST 4: List All Diagnoses in PNPK Database")
    print("="*80)
    
    try:
        db_pool = await create_db_pool()
        if not db_pool:
            print("✗ Cannot proceed without database pool")
            return
        
        print(f"✓ Database pool created")
        
        pnpk_service = PNPKSummaryService(db_pool)
        
        # Get all diagnoses
        all_diagnoses = await pnpk_service.get_all_diagnoses()
        
        print(f"\nTotal diagnoses in PNPK DB: {len(all_diagnoses)}")
        print(f"\nList of diagnoses:")
        for i, diag in enumerate(all_diagnoses, 1):
            print(f"  {i}. {diag['diagnosis_name']} ({diag['stage_count']} stages)")
        
        await db_pool.close()
        print(f"\n✓ Database connection closed")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


def test_openai_client():
    """Test 5: Cek apakah OpenAI client tersedia"""
    print("\n" + "="*80)
    print("TEST 5: Check OpenAI Client Availability")
    print("="*80)
    
    try:
        parser = get_parser()
        print(f"✓ Parser initialized")
        
        if hasattr(parser, 'client'):
            print(f"✓ OpenAI client available")
            print(f"  Client type: {type(parser.client)}")
            
            # Check API key
            if parser.api_key:
                print(f"✓ API key configured (length: {len(parser.api_key)})")
            else:
                print(f"✗ No API key configured")
        else:
            print(f"✗ OpenAI client NOT available")
            print(f"  Parser type: {type(parser)}")
        
        # Check OPENAI_AVAILABLE flag
        from services.lite_service import OPENAI_AVAILABLE
        print(f"\nOPENAI_AVAILABLE flag: {OPENAI_AVAILABLE}")
        
        # Check environment
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            print(f"✓ OPENAI_API_KEY env var set (length: {len(openai_key)})")
        else:
            print(f"✗ OPENAI_API_KEY env var NOT set")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


def test_full_analysis_structure():
    """Test 6: Cek struktur full_analysis untuk rawat_inap"""
    print("\n" + "="*80)
    print("TEST 6: Check full_analysis Structure (rawat_inap)")
    print("="*80)
    
    payload = {
        "mode": "form",
        "diagnosis": "Pneumonia",
        "tindakan": "Nebulisasi",
        "obat": "Ceftriaxone 1g"
    }
    
    try:
        result = analyze_lite_single(payload, db_pool=None)
        
        # Try to access internal parsed detail
        parsed_detail = result.get("_parsed_detail", {})
        print(f"\nParsed diagnosis: {parsed_detail.get('diagnosis', 'N/A')}")
        
        # Check metadata
        metadata = result.get("metadata", {})
        print(f"\nMetadata:")
        print(f"  Engine: {metadata.get('engine', 'N/A')}")
        print(f"  Mode: {metadata.get('mode', 'N/A')}")
        print(f"  Parsing method: {metadata.get('parsing_method', 'N/A')}")
        
        # Check cp_ringkas
        cp_ringkas = result.get("cp_ringkas", [])
        print(f"\nCP Ringkas ({len(cp_ringkas)} items):")
        for i, step in enumerate(cp_ringkas, 1):
            print(f"  {i}. {step}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("CP RINGKAS COMPREHENSIVE TEST SUITE")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 5: OpenAI client (sync test first)
    test_openai_client()
    
    # Test 1: PNPK fetch
    await test_pnpk_fetch()
    
    # Test 4: List diagnoses
    await test_diagnoses_in_db()
    
    # Test 2: Without DB
    test_analyze_single_without_db()
    
    # Test 3: With DB
    await test_analyze_single_with_db()
    
    # Test 6: Full analysis structure
    test_full_analysis_structure()
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)
    
    print("\n📋 DIAGNOSIS CHECKLIST:")
    print("1. ✓ Database connection works?")
    print("2. ✓ PNPK data exists in database?")
    print("3. ✓ OpenAI client configured?")
    print("4. ✓ API key available?")
    print("5. ✓ db_pool passed to analyze_lite_single?")
    print("6. ✓ PNPK fetch logic executed?")
    print("7. ✓ AI fallback triggered when DB fails?")
    print("\nCheck logs above to identify which step failed!")


if __name__ == "__main__":
    asyncio.run(main())
