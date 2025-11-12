"""
Test script for PNPK Summary Service
Tests intelligent diagnosis matching and summary retrieval
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from services.pnpk_summary_service import PNPKSummaryService

load_dotenv()


async def test_pnpk_service():
    """Run comprehensive tests on PNPK service"""
    
    # Create database pool
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return
    
    print("🔗 Connecting to database...")
    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=2)
    
    try:
        service = PNPKSummaryService(pool)
        
        print("\n" + "="*70)
        print("TEST 1: Get All Diagnoses")
        print("="*70)
        diagnoses = await service.get_all_diagnoses()
        print(f"✅ Found {len(diagnoses)} diagnoses in database")
        for i, diag in enumerate(diagnoses[:5], 1):
            print(f"  {i}. {diag['diagnosis_name']} ({diag['stage_count']} stages)")
        if len(diagnoses) > 5:
            print(f"  ... and {len(diagnoses) - 5} more")
        
        print("\n" + "="*70)
        print("TEST 2: Exact Match")
        print("="*70)
        test_cases_exact = [
            "Pneumonia",
            "Hospital-Acquired Pneumonia (HAP)",
            "Gagal Jantung Pada Anak"
        ]
        
        for diagnosis in test_cases_exact:
            print(f"\n🔍 Testing: '{diagnosis}'")
            summary = await service.get_pnpk_summary(diagnosis, auto_match=True)
            if summary:
                print(f"✅ Found: {summary['diagnosis']}")
                print(f"   Stages: {summary['total_stages']}")
                if 'match_info' in summary:
                    print(f"   Confidence: {summary['match_info']['confidence']}")
                    print(f"   Matched by: {summary['match_info']['matched_by']}")
            else:
                print(f"❌ Not found")
        
        print("\n" + "="*70)
        print("TEST 3: Partial Match (without abbreviation)")
        print("="*70)
        test_cases_partial = [
            "Hospital-Acquired Pneumonia",  # Missing (HAP)
            "Penyakit Ginjal Kronik",       # Missing (PGK)
            "Glaukoma Primer Sudut Tertutup", # Missing (GPSTp)
        ]
        
        for diagnosis in test_cases_partial:
            print(f"\n🔍 Testing: '{diagnosis}'")
            summary = await service.get_pnpk_summary(diagnosis, auto_match=True)
            if summary:
                print(f"✅ Matched to: {summary['diagnosis']}")
                print(f"   Stages: {summary['total_stages']}")
                if 'match_info' in summary:
                    print(f"   Confidence: {summary['match_info']['confidence']}")
                    print(f"   Matched by: {summary['match_info']['matched_by']}")
            else:
                print(f"❌ Not found")
        
        print("\n" + "="*70)
        print("TEST 4: Abbreviation Match")
        print("="*70)
        test_cases_abbrev = [
            "HAP",   # Should match Hospital-Acquired Pneumonia
            "VAP",   # Should match Ventilator-Associated Pneumonia
            "PGK",   # Should match Penyakit Ginjal Kronik
            "KPKBSK", # Should match Karsinoma Bukan Sel Kecil
        ]
        
        for abbrev in test_cases_abbrev:
            print(f"\n🔍 Testing abbreviation: '{abbrev}'")
            summary = await service.get_pnpk_summary(abbrev, auto_match=True)
            if summary:
                print(f"✅ Matched to: {summary['diagnosis']}")
                if 'match_info' in summary:
                    print(f"   Confidence: {summary['match_info']['confidence']}")
                    print(f"   Matched by: {summary['match_info']['matched_by']}")
            else:
                print(f"❌ Not found")
        
        print("\n" + "="*70)
        print("TEST 5: Fuzzy Match (typos and variations)")
        print("="*70)
        test_cases_fuzzy = [
            "pneumoni",           # Missing 'a'
            "gagal jantung anak", # Simplified
            "retinopati diabetes", # Variation of Retinopati Diabetika
            "osteoporsis dewasa",  # Typo: osteoporsis -> osteoporosis
        ]
        
        for fuzzy in test_cases_fuzzy:
            print(f"\n🔍 Testing fuzzy: '{fuzzy}'")
            summary = await service.get_pnpk_summary(fuzzy, auto_match=True)
            if summary:
                print(f"✅ Matched to: {summary['diagnosis']}")
                if 'match_info' in summary:
                    print(f"   Confidence: {summary['match_info']['confidence']}")
                    print(f"   Matched by: {summary['match_info']['matched_by']}")
            else:
                print(f"❌ Not found")
        
        print("\n" + "="*70)
        print("TEST 6: Search with Ranking")
        print("="*70)
        search_terms = [
            "pneumonia",
            "gagal jantung",
            "glaukoma",
        ]
        
        for term in search_terms:
            print(f"\n🔍 Searching: '{term}'")
            results = await service.search_diagnoses(term, limit=5)
            print(f"✅ Found {len(results)} matches:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['diagnosis_name']}")
                print(f"     Score: {result['match_score']:.3f} | Method: {result['matched_by']}")
        
        print("\n" + "="*70)
        print("TEST 7: Get Complete Summary with Stages")
        print("="*70)
        diagnosis = "Pneumonia"
        print(f"\n🔍 Getting full summary for: '{diagnosis}'")
        summary = await service.get_pnpk_summary(diagnosis)
        
        if summary:
            print(f"\n✅ Diagnosis: {summary['diagnosis']}")
            print(f"   Total Stages: {summary['total_stages']}")
            print("\n   Clinical Pathway Stages:")
            print("   " + "-"*65)
            
            for stage in summary['stages']:
                print(f"\n   Stage {stage['order']}: {stage['stage_name']}")
                # Truncate description for display
                desc = stage['description']
                if len(desc) > 80:
                    desc = desc[:80] + "..."
                print(f"   └─ {desc}")
        else:
            print(f"❌ Not found")
        
        print("\n" + "="*70)
        print("TEST 8: Validation Check")
        print("="*70)
        validation_tests = [
            ("Pneumonia", True),
            ("Random Disease XYZ", False),
            ("gagal jantung", True),
        ]
        
        for test_diag, expected in validation_tests:
            print(f"\n🔍 Validating: '{test_diag}'")
            exists = await service.validate_diagnosis_exists(test_diag)
            status = "✅" if exists == expected else "❌"
            print(f"{status} Exists: {exists} (Expected: {expected})")
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await pool.close()
        print("\n🔒 Database connection closed")


if __name__ == "__main__":
    print("🧪 PNPK Summary Service Test Suite")
    print("="*70)
    asyncio.run(test_pnpk_service())
