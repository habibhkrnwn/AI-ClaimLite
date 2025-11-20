

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from services.lite_service_ultra_fast import analyze_lite_single_ultra_fast
import asyncpg


async def get_db_pool():
    """Create database connection pool"""
    import os
    return await asyncpg.create_pool(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        min_size=1,
        max_size=5
    )


def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


async def test_insight():
    print("🚀 Testing Insight AI Generation\n")
    
    # Initialize DB pool as None (will use fallback)
    db_pool = None
    
    # ============================================================================
    # TEST 1: Kasus Normal - Pneumonia dengan Tindakan Lengkap
    # ============================================================================
    print_section("TEST 1: Pneumonia dengan Tindakan Lengkap")
    
    payload1 = {
        "mode": "form",
        "diagnosis": "Pneumonia",
        "tindakan": "Rontgen Thorax, Pemeriksaan Lab Darah",
        "obat": "Ceftriaxone, Paracetamol, Ambroxol",
        "icd10_code": "J18.9",
        "icd9_code": "87.44",
        "claim_id": "TEST-INSIGHT-001"
    }
    
    result1 = await analyze_lite_single_ultra_fast(payload1, db_pool)
    
    print(f"\n📊 HASIL ANALISIS:")
    print(f"Status: {result1.get('status', 'N/A')}")
    
    if 'result' in result1:
        data = result1['result']
        print(f"\n💡 Insight AI:")
        print(f"   {data.get('insight_ai', 'N/A')}")
        
        print(f"\n📋 CP Ringkas:")
        for i, step in enumerate(data.get('cp_ringkas', []), 1):
            print(f"   {i}. {step}")
        
        print(f"\n📄 Checklist Dokumen:")
        for i, doc in enumerate(data.get('checklist_dokumen', []), 1):
            print(f"   {i}. {doc}")
        
        print(f"\n🔍 Konsistensi:")
        konsistensi = data.get('konsistensi', {})
        print(f"   Tingkat: {konsistensi.get('tingkat_konsistensi', 'N/A')}")
        print(f"   Score: {konsistensi.get('_score', 'N/A')}")
        
        print(f"\n⏱️  Processing Time: {data.get('metadata', {}).get('processing_time_seconds', 'N/A')}s")
    
    # ============================================================================
    # TEST 2: Free Text Input
    # ============================================================================
    print_section("TEST 2: Free Text - Diabetes dengan Komplikasi")
    
    payload2 = {
        "mode": "text",
        "input_text": """Pasien dengan Diabetes Mellitus Type 2 tidak terkontrol,
        GDS 350 mg/dL, HbA1c 10.5%. Dilakukan pemeriksaan gula darah, funduskopi,
        dan edukasi diet. Terapi: Metformin 500mg 3x1, Glimepiride 2mg 1x1.""",
        "claim_id": "TEST-INSIGHT-002"
    }
    
    result2 = await analyze_lite_single_ultra_fast(payload2, db_pool)
    
    print(f"\n📊 HASIL ANALISIS:")
    print(f"Status: {result2.get('status', 'N/A')}")
    
    if 'result' in result2:
        data = result2['result']
        print(f"\n💡 Insight AI:")
        print(f"   {data.get('insight_ai', 'N/A')}")
        
        print(f"\n📋 Klasifikasi:")
        klasifikasi = data.get('klasifikasi', {})
        print(f"   Diagnosis: {klasifikasi.get('diagnosis', 'N/A')}")
        
        print(f"\n🔍 Konsistensi:")
        konsistensi = data.get('konsistensi', {})
        print(f"   DX→TX: {konsistensi.get('dx_tx', {}).get('status', 'N/A')}")
        print(f"   DX→DRUG: {konsistensi.get('dx_drug', {}).get('status', 'N/A')}")
        print(f"   TX→DRUG: {konsistensi.get('tx_drug', {}).get('status', 'N/A')}")
        print(f"   Tingkat: {konsistensi.get('tingkat_konsistensi', 'N/A')}")
    
    # ============================================================================
    # TEST 3: Kasus dengan Konsistensi Rendah
    # ============================================================================
    print_section("TEST 3: Kasus dengan Konsistensi Rendah")
    
    payload3 = {
        "mode": "form",
        "diagnosis": "Diabetes Mellitus",
        "tindakan": "Appendectomy",  # Tidak sesuai!
        "obat": "Paracetamol",  # Hanya paracetamol untuk diabetes
        "claim_id": "TEST-INSIGHT-003"
    }
    
    result3 = await analyze_lite_single_ultra_fast(payload3, db_pool)
    
    print(f"\n📊 HASIL ANALISIS:")
    print(f"Status: {result3.get('status', 'N/A')}")
    
    if 'result' in result3:
        data = result3['result']
        print(f"\n💡 Insight AI:")
        print(f"   {data.get('insight_ai', 'N/A')}")
        
        print(f"\n🔍 Konsistensi:")
        konsistensi = data.get('konsistensi', {})
        print(f"   DX→TX: {konsistensi.get('dx_tx', {}).get('status', 'N/A')}")
        print(f"   Catatan: {konsistensi.get('dx_tx', {}).get('catatan', 'N/A')}")
        print(f"   DX→DRUG: {konsistensi.get('dx_drug', {}).get('status', 'N/A')}")
        print(f"   Catatan: {konsistensi.get('dx_drug', {}).get('catatan', 'N/A')}")
        print(f"   Tingkat: {konsistensi.get('tingkat_konsistensi', 'N/A')}")
        print(f"   Score: {konsistensi.get('_score', 'N/A')}/3.0")
    
    # ============================================================================
    # RINGKASAN
    # ============================================================================
    print_section("RINGKASAN EVALUASI INSIGHT AI")
    
    print("\n📊 COMPARISON TABLE:")
    print("-" * 80)
    print(f"{'Test Case':<30} {'Konsistensi':<15} {'Insight Length':<20}")
    print("-" * 80)
    
    if 'result' in result1:
        insight1 = result1['result'].get('insight_ai', '')
        konsist1 = result1['result'].get('konsistensi', {}).get('tingkat_konsistensi', '-')
        print(f"{'1. Pneumonia Lengkap':<30} {konsist1:<15} {len(insight1)} chars")
    
    if 'result' in result2:
        insight2 = result2['result'].get('insight_ai', '')
        konsist2 = result2['result'].get('konsistensi', {}).get('tingkat_konsistensi', '-')
        print(f"{'2. Diabetes Free Text':<30} {konsist2:<15} {len(insight2)} chars")
    
    if 'result' in result3:
        insight3 = result3['result'].get('insight_ai', '')
        konsist3 = result3['result'].get('konsistensi', {}).get('tingkat_konsistensi', '-')
        print(f"{'3. Kasus Tidak Konsisten':<30} {konsist3:<15} {len(insight3)} chars")
    
    print("-" * 80)
    
    print("\n✅ EVALUASI KUALITAS INSIGHT:")
    
    def evaluate_insight(insight, konsistensi, test_name):
        print(f"\n{test_name}:")
        print(f"  Insight: \"{insight}\"")
        
        # Check if insight is actionable
        actionable_keywords = ['perlu', 'pastikan', 'verifikasi', 'periksa', 'pertimbangkan', 'evaluasi']
        is_actionable = any(keyword in insight.lower() for keyword in actionable_keywords)
        
        # Check if insight mentions key issues
        has_status = '✅' in insight or '⚠️' in insight or '❌' in insight
        
        # Check length (should be concise)
        is_concise = len(insight) < 150
        
        print(f"  ✓ Actionable: {'✅' if is_actionable else '❌'}")
        print(f"  ✓ Has Status Icon: {'✅' if has_status else '❌'}")
        print(f"  ✓ Concise (<150 chars): {'✅' if is_concise else '❌'}")
        print(f"  ✓ Konsistensi Level: {konsistensi}")
    
    if 'result' in result1:
        evaluate_insight(
            result1['result'].get('insight_ai', ''),
            result1['result'].get('konsistensi', {}).get('tingkat_konsistensi', '-'),
            "Test 1 (Pneumonia)"
        )
    
    if 'result' in result2:
        evaluate_insight(
            result2['result'].get('insight_ai', ''),
            result2['result'].get('konsistensi', {}).get('tingkat_konsistensi', '-'),
            "Test 2 (Diabetes)"
        )
    
    if 'result' in result3:
        evaluate_insight(
            result3['result'].get('insight_ai', ''),
            result3['result'].get('konsistensi', {}).get('tingkat_konsistensi', '-'),
            "Test 3 (Tidak Konsisten)"
        )
    
    print("\n" + "="*80)
    print("TEST SELESAI")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_insight())
