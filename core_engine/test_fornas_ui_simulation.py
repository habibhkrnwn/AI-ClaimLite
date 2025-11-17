"""
Test FORNAS Service - UI Simulation
Simulasi flow UI lengkap untuk test sebelum implementasi

Test scenarios:
1. Generate AI / Rekomendasi - input typo/English
2. Generate AI / Rekomendasi - input Indonesian partial
3. Analisis Klinis / Validasi - nama obat valid
4. Analisis Klinis / Validasi - mixed valid + invalid
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.fornas_smart_service import recommend_drug, validate_fornas
from database_connection import get_db

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def print_section(title):
    """Print section divider"""
    print("\n" + "-"*80)
    print(f"  {title}")
    print("-"*80)

def test_scenario_1_typo_english():
    """
    SCENARIO 1: User input dengan typo/English
    Flow: User ketik "ceftriaxone" → Klik Generate AI → Dapat rekomendasi
    """
    print_header("SCENARIO 1: Generate AI - Input English (ceftriaxone)")
    
    user_input = "ceftriaxone"
    print(f"📝 User Input: '{user_input}'")
    print(f"🎯 Expected: AI normalisasi ke 'seftriakson' + rekomendasi obat sejenis")
    
    print("\n⏳ Processing...")
    result = recommend_drug(user_input, max_recommend=5)
    
    print(f"\n✅ Original Input: {result['original_input']}")
    print(f"📊 Total Recommendations: {len(result['recommendations'])}")
    
    if result['recommendations']:
        print("\n🎯 REKOMENDASI OBAT (untuk ditampilkan di UI):")
        print("-" * 80)
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"\n{i}. {rec['recommended_name'].upper()}")
            print(f"   Alasan: {rec['reason']}")
            if rec.get('db_match'):
                db = rec['db_match']
                # db_match bisa dict atau object
                kelas = db.get('kelas_terapi') if isinstance(db, dict) else getattr(db, 'kelas_terapi', '-')
                subkelas = db.get('subkelas_terapi') if isinstance(db, dict) else getattr(db, 'subkelas_terapi', '-')
                sediaan = db.get('sediaan_kekuatan') if isinstance(db, dict) else getattr(db, 'sediaan_kekuatan', '-')
                print(f"   Kelas: {kelas}")
                print(f"   Subkelas: {subkelas}")
                print(f"   Sediaan: {sediaan}")
    else:
        print("❌ Tidak ada rekomendasi")
    
    return result

def test_scenario_2_indonesian_partial():
    """
    SCENARIO 2: User input Indonesian dengan typo
    Flow: User ketik "parasetaml" (typo) → Klik Generate AI → Dapat rekomendasi
    """
    print_header("SCENARIO 2: Generate AI - Input Typo (parasetaml)")
    
    user_input = "parasetaml"
    print(f"📝 User Input: '{user_input}'")
    print(f"🎯 Expected: AI koreksi ke 'parasetamol' + rekomendasi obat sejenis")
    
    print("\n⏳ Processing...")
    result = recommend_drug(user_input, max_recommend=5)
    
    print(f"\n✅ Original Input: {result['original_input']}")
    print(f"📊 Total Recommendations: {len(result['recommendations'])}")
    
    if result['recommendations']:
        print("\n🎯 REKOMENDASI OBAT (untuk ditampilkan di UI):")
        print("-" * 80)
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"\n{i}. {rec['recommended_name'].upper()}")
            print(f"   Alasan: {rec['reason']}")
            if rec.get('db_match'):
                db = rec['db_match']
                # db_match bisa dict atau object
                kelas = db.get('kelas_terapi') if isinstance(db, dict) else getattr(db, 'kelas_terapi', '-')
                subkelas = db.get('subkelas_terapi') if isinstance(db, dict) else getattr(db, 'subkelas_terapi', '-')
                print(f"   Kelas: {kelas}")
                print(f"   Subkelas: {subkelas}")
    else:
        print("❌ Tidak ada rekomendasi")
    
    return result

def test_scenario_3_validation_valid():
    """
    SCENARIO 3: Validasi dengan nama obat yang valid
    Flow: User pilih obat dari rekomendasi → Input diagnosis → Klik Analisis Klinis
    """
    print_header("SCENARIO 3: Analisis Klinis - Obat Valid")
    
    # Simulasi: User sudah pilih dari rekomendasi
    selected_drugs = ["seftriakson", "parasetamol", "levofloksasin"]
    diagnosis_icd10 = "J18.9"
    diagnosis_name = "Pneumonia, unspecified organism"
    
    print(f"📝 Selected Drugs (dari rekomendasi):")
    for i, drug in enumerate(selected_drugs, 1):
        print(f"   {i}. {drug}")
    
    print(f"\n🩺 Diagnosis:")
    print(f"   ICD-10: {diagnosis_icd10}")
    print(f"   Name: {diagnosis_name}")
    
    print("\n⏳ Processing Validasi FORNAS...")
    result = validate_fornas(
        drug_list=selected_drugs,
        diagnosis_icd10=diagnosis_icd10,
        diagnosis_name=diagnosis_name
    )
    
    print_section("HASIL VALIDASI FORNAS")
    
    if result.get('fornas_validation'):
        for item in result['fornas_validation']:
            print(f"\n{item['no']}. {item['nama_obat'].upper()}")
            print(f"   Status: {item['status_fornas']}")
            print(f"   Kelas: {item.get('kelas_terapi', '-')}")
            print(f"   Catatan AI: {item.get('catatan_ai', '-')}")
            print(f"   Regulasi: {item.get('sumber_regulasi', '-')}")
    
    if result.get('summary'):
        summary = result['summary']
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80)
        print(f"Total Obat: {summary.get('total_obat', 0)}")
        print(f"✅ Sesuai: {summary.get('sesuai', 0)}")
        print(f"⚠️  Perlu Justifikasi: {summary.get('perlu_justifikasi', 0)}")
        print(f"❌ Non-Fornas: {summary.get('non_fornas', 0)}")
        print(f"Update: {summary.get('update_date', '-')}")
    
    return result

def test_scenario_4_validation_mixed():
    """
    SCENARIO 4: Validasi dengan mixed valid + invalid
    Flow: User input manual + pilihan → Ada yang tidak ada di DB
    """
    print_header("SCENARIO 4: Analisis Klinis - Mixed Valid + Invalid")
    
    # Simulasi: User mix input manual dan pilihan
    selected_drugs = ["parasetamol", "unknown-drug-123", "ibuprofen"]
    diagnosis_icd10 = "R50.9"
    diagnosis_name = "Fever, unspecified"
    
    print(f"📝 Selected Drugs:")
    for i, drug in enumerate(selected_drugs, 1):
        print(f"   {i}. {drug}")
    
    print(f"\n🩺 Diagnosis:")
    print(f"   ICD-10: {diagnosis_icd10}")
    print(f"   Name: {diagnosis_name}")
    
    print("\n⏳ Processing Validasi FORNAS...")
    result = validate_fornas(
        drug_list=selected_drugs,
        diagnosis_icd10=diagnosis_icd10,
        diagnosis_name=diagnosis_name
    )
    
    print_section("HASIL VALIDASI FORNAS")
    
    if result.get('fornas_validation'):
        for item in result['fornas_validation']:
            print(f"\n{item['no']}. {item['nama_obat'].upper()}")
            print(f"   Status: {item['status_fornas']}")
            print(f"   Kelas: {item.get('kelas_terapi', '-')}")
            print(f"   Catatan AI: {item.get('catatan_ai', '-')}")
    
    if result.get('summary'):
        summary = result['summary']
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80)
        print(f"Total Obat: {summary.get('total_obat', 0)}")
        print(f"✅ Sesuai: {summary.get('sesuai', 0)}")
        print(f"⚠️  Perlu Justifikasi: {summary.get('perlu_justifikasi', 0)}")
        print(f"❌ Non-Fornas: {summary.get('non_fornas', 0)}")
    
    return result

def test_db_connection():
    """Test koneksi database"""
    print_section("Testing Database Connection")
    try:
        db = next(get_db())
        print("✅ Database connection: OK")
        
        # Count fornas_drugs
        from models import FornasDrug
        count = db.query(FornasDrug).count()
        print(f"📊 Total drugs in FORNAS DB: {count:,}")
        
        # Sample data
        sample = db.query(FornasDrug).limit(3).all()
        print(f"\n📋 Sample Data:")
        for drug in sample:
            print(f"   - {drug.obat_name} ({drug.kelas_terapi})")
        
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Run all test scenarios"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "FORNAS SERVICE - UI SIMULATION TEST" + " "*23 + "║")
    print("║" + " "*30 + f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + " "*29 + "║")
    print("╚" + "="*78 + "╝")
    
    # Test DB connection first
    if not test_db_connection():
        print("\n❌ Cannot proceed without database connection")
        return
    
    try:
        # Scenario 1: Generate AI - English input
        test_scenario_1_typo_english()
        
        # Scenario 2: Generate AI - Typo input
        test_scenario_2_indonesian_partial()
        
        # Scenario 3: Validasi - Valid drugs
        test_scenario_3_validation_valid()
        
        # Scenario 4: Validasi - Mixed valid/invalid
        test_scenario_4_validation_mixed()
        
        print_header("ALL TESTS COMPLETED")
        print("✅ Service ready for UI implementation")
        print("\n💡 Tips untuk UI:")
        print("   1. Generate AI → Tampilkan rekomendasi dalam list/dropdown")
        print("   2. User pilih → Simpan ke selected drugs")
        print("   3. Analisis Klinis → Validasi + tampilkan status")
        print("   4. Handle Non-Fornas dengan pesan yang jelas")
        
    except Exception as e:
        print_header("ERROR OCCURRED")
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
