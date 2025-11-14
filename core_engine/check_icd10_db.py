"""
Check ICD-10 Database Contents
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database_connection import SessionLocal
from sqlalchemy import text


def check_icd10_database():
    """Check ICD-10 database contents"""
    
    print("=" * 100)
    print("  ICD-10 DATABASE CHECK")
    print("=" * 100)
    
    db = SessionLocal()
    
    try:
        # Check J12 codes (Viral pneumonia)
        print("\n📋 J12 codes (Viral pneumonia):")
        print("-" * 100)
        
        result = db.execute(text("""
            SELECT code, name 
            FROM icd10_master 
            WHERE code LIKE 'J12%'
            ORDER BY code
        """))
        
        for row in result:
            print(f"{row.code:10} | {row.name}")
        
        # Check J15 codes (Bacterial pneumonia)
        print("\n📋 J15 codes (Bacterial pneumonia):")
        print("-" * 100)
        
        result = db.execute(text("""
            SELECT code, name 
            FROM icd10_master 
            WHERE code LIKE 'J15%'
            ORDER BY code
        """))
        
        for row in result:
            print(f"{row.code:10} | {row.name}")
        
        # Check J17 codes (Pneumonia in bacterial diseases)
        print("\n📋 J17 codes (Pneumonia in bacterial diseases classified elsewhere):")
        print("-" * 100)
        
        result = db.execute(text("""
            SELECT code, name 
            FROM icd10_master 
            WHERE code LIKE 'J17%'
            ORDER BY code
        """))
        
        for row in result:
            print(f"{row.code:10} | {row.name}")
        
        # Explain the difference
        print("\n" + "=" * 100)
        print("  EXPLANATION: VIRAL vs BACTERIAL PNEUMONIA")
        print("=" * 100)
        print("""
📌 IMPORTANT CLASSIFICATION:

1. J12 = VIRAL PNEUMONIA (Pneumonia karena virus)
   - J12.0 = Adenoviral pneumonia ← VIRUS, bukan bakteri!
   - J12.1 = Respiratory syncytial virus pneumonia
   - J12.8 = Other viral pneumonia
   - J12.9 = Viral pneumonia, unspecified

2. J13 = Streptococcus pneumoniae pneumonia ← BAKTERI SPESIFIK

3. J14 = Haemophilus influenzae pneumonia ← BAKTERI SPESIFIK

4. J15 = BACTERIAL PNEUMONIA (Pneumonia karena bakteri)
   - J15.0 = Pneumonia due to Klebsiella pneumoniae
   - J15.1 = Pneumonia due to Pseudomonas
   - J15.2 = Pneumonia due to staphylococcus
   - J15.3 = Pneumonia due to streptococcus, group B
   - J15.4 = Pneumonia due to other streptococci
   - J15.5 = Pneumonia due to Escherichia coli
   - J15.6 = Pneumonia due to other aerobic Gram-negative bacteria
   - J15.7 = Pneumonia due to Mycoplasma pneumoniae
   - J15.8 = Other bacterial pneumonia
   - J15.9 = Bacterial pneumonia, unspecified

5. J17 = Pneumonia in bacterial diseases classified elsewhere

🔍 KESIMPULAN:
   Adenoviral pneumonia TIDAK MUNCUL di hasil "bacterial pneumonia" karena:
   ✓ Adenovirus adalah VIRUS, bukan bakteri
   ✓ Adenoviral pneumonia ada di kode J12.0 (viral pneumonia)
   ✓ Bacterial pneumonia ada di J13, J14, J15, J17
        """)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()
    
    print("\n" + "=" * 100)


if __name__ == "__main__":
    check_icd10_database()
