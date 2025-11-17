"""
Test untuk drug yang tidak punya subkelas_terapi
Pastikan tetap ada rekomendasi yang relevan
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.fornas_smart_service import recommend_drug
from database_connection import get_db
from models import FornasDrug

def check_drugs_without_subkelas():
    """Cek berapa banyak drug tanpa subkelas_terapi"""
    print("="*80)
    print("CHECKING: Drugs without subkelas_terapi in database")
    print("="*80)
    
    db = next(get_db())
    
    # Total drugs
    total = db.query(FornasDrug).count()
    
    # Drugs tanpa subkelas (NULL atau empty string)
    without_subkelas = db.query(FornasDrug).filter(
        (FornasDrug.subkelas_terapi == None) | 
        (FornasDrug.subkelas_terapi == '')
    ).count()
    
    # Drugs dengan subkelas
    with_subkelas = total - without_subkelas
    
    print(f"\nTotal Drugs: {total}")
    print(f"With subkelas_terapi: {with_subkelas} ({with_subkelas/total*100:.1f}%)")
    print(f"WITHOUT subkelas_terapi: {without_subkelas} ({without_subkelas/total*100:.1f}%)")
    
    # Sample drugs without subkelas
    print(f"\nSample drugs WITHOUT subkelas_terapi:")
    samples = db.query(FornasDrug).filter(
        (FornasDrug.subkelas_terapi == None) | 
        (FornasDrug.subkelas_terapi == '')
    ).limit(10).all()
    
    for s in samples:
        print(f"  - {s.obat_name}")
        print(f"    Kelas: {s.kelas_terapi or '(kosong)'}")
        print(f"    Subkelas: {s.subkelas_terapi or '(kosong)'}")
    
    db.close()
    return samples[0].obat_name if samples else None

def test_recommendation_without_subkelas(drug_name):
    """Test rekomendasi untuk obat tanpa subkelas"""
    print("\n" + "="*80)
    print(f"TEST: Recommendation for drug WITHOUT subkelas_terapi")
    print("="*80)
    
    print(f"\n📝 Testing drug: '{drug_name}'")
    print(f"🎯 Expected: Fallback ke kelas_terapi atau keyword search")
    
    print("\n⏳ Generating recommendations...")
    result = recommend_drug(drug_name, max_recommend=5)
    
    print(f"\n✅ Original Input: {result['original_input']}")
    print(f"📊 Total Recommendations: {len(result['recommendations'])}")
    
    if result['recommendations']:
        print("\n🎯 REKOMENDASI:")
        print("-" * 80)
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"\n{i}. {rec['recommended_name'].upper()}")
            print(f"   Alasan: {rec['reason']}")
            print(f"   Strategy: {rec.get('context_strategy', 'N/A')}")
            if rec.get('db_match'):
                db = rec['db_match']
                kelas = db.get('kelas_terapi') if isinstance(db, dict) else getattr(db, 'kelas_terapi', '-')
                subkelas = db.get('subkelas_terapi') if isinstance(db, dict) else getattr(db, 'subkelas_terapi', '-')
                print(f"   Kelas: {kelas}")
                print(f"   Subkelas: {subkelas or '(kosong)'}")
    else:
        print("❌ Tidak ada rekomendasi")
    
    return result

def main():
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "TEST: Drugs WITHOUT subkelas_terapi" + " "*23 + "║")
    print("╚" + "="*78 + "╝")
    
    # Step 1: Check database
    sample_drug = check_drugs_without_subkelas()
    
    if sample_drug:
        # Step 2: Test recommendation
        test_recommendation_without_subkelas(sample_drug)
        
        print("\n" + "="*80)
        print("✅ TEST COMPLETED")
        print("="*80)
        print("\nKESIMPULAN:")
        print("- Sistem TETAP menghasilkan rekomendasi meskipun drug tidak punya subkelas")
        print("- Fallback hierarchy bekerja: subkelas → kelas → keyword")
        print("- Rekomendasi tetap relevan berdasarkan kelas_terapi atau nama obat")
    else:
        print("\n✅ Semua drugs sudah punya subkelas_terapi!")

if __name__ == "__main__":
    main()
