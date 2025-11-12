"""
Check FORNAS Database Contents

Cek obat apa saja yang ada di database dan formatnya
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database_connection import SessionLocal
from models import FornasDrug


def check_fornas_database():
    """Check database contents"""
    
    print("=" * 80)
    print("  FORNAS DATABASE CHECK")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Count total drugs
        total = db.query(FornasDrug).count()
        print(f"\n📊 Total drugs in database: {total}")
        
        if total == 0:
            print("\n⚠️ DATABASE IS EMPTY!")
            print("   → You need to populate the fornas_drugs table first")
            return
        
        # Sample drugs
        print("\n📋 Sample drugs (first 20):")
        print("-" * 80)
        
        drugs = db.query(FornasDrug).limit(20).all()
        
        for i, drug in enumerate(drugs, 1):
            print(f"\n{i}. {drug.obat_name}")
            print(f"   Kode: {drug.kode_fornas}")
            print(f"   Kelas: {drug.kelas_terapi}")
            if drug.nama_obat_alias:
                print(f"   Alias: {drug.nama_obat_alias}")
        
        # Search specific drugs
        print("\n" + "=" * 80)
        print("  SEARCHING SPECIFIC DRUGS")
        print("=" * 80)
        
        search_terms = [
            "seftriakson",
            "ceftriaxone",
            "parasetamol",
            "paracetamol",
            "levofloksasin",
            "levofloxacin",
            "metformin"
        ]
        
        for term in search_terms:
            print(f"\n🔍 Searching for: '{term}'")
            
            # Exact match
            result = db.query(FornasDrug).filter(
                FornasDrug.obat_name.ilike(f"%{term}%")
            ).first()
            
            if result:
                print(f"   ✅ FOUND: {result.obat_name} ({result.kode_fornas})")
            else:
                print(f"   ❌ NOT FOUND")
        
        # Show drugs with specific patterns
        print("\n" + "=" * 80)
        print("  DRUGS CONTAINING 'CEFT' OR 'SEFT'")
        print("=" * 80)
        
        ceft_drugs = db.query(FornasDrug).filter(
            (FornasDrug.obat_name.ilike("%ceft%")) | 
            (FornasDrug.obat_name.ilike("%seft%"))
        ).limit(10).all()
        
        if ceft_drugs:
            for drug in ceft_drugs:
                print(f"   • {drug.obat_name}")
        else:
            print("   ❌ No drugs found with 'ceft' or 'seft'")
        
        # Show drugs with specific patterns
        print("\n" + "=" * 80)
        print("  DRUGS CONTAINING 'PARA'")
        print("=" * 80)
        
        para_drugs = db.query(FornasDrug).filter(
            FornasDrug.obat_name.ilike("%para%")
        ).limit(10).all()
        
        if para_drugs:
            for drug in para_drugs:
                print(f"   • {drug.obat_name}")
        else:
            print("   ❌ No drugs found with 'para'")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    check_fornas_database()
