"""
Debug test: Kenapa ceftriaxone tidak dinormalisasi ke seftriakson?
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.fornas_smart_service import db_exact_match, FornasAINormalizer

def test_normalization_debug():
    print("="*80)
    print("DEBUG: Testing Normalization Flow")
    print("="*80)
    
    # Test 1: Cek apakah "seftriakson" ada di DB
    print("\n1. Cek DB untuk 'seftriakson':")
    match = db_exact_match("seftriakson")
    if match:
        print(f"   ✅ Found: {match.obat_name}")
        print(f"   Kelas: {match.kelas_terapi}")
        print(f"   Subkelas: {match.subkelas_terapi}")
    else:
        print("   ❌ Not found in DB")
    
    # Test 2: Cek apakah "ceftriaxone" ada di DB
    print("\n2. Cek DB untuk 'ceftriaxone':")
    match = db_exact_match("ceftriaxone")
    if match:
        print(f"   ✅ Found: {match.obat_name}")
    else:
        print("   ❌ Not found in DB (expected)")
    
    # Test 3: AI Normalization
    print("\n3. Test AI Normalization 'ceftriaxone':")
    normalizer = FornasAINormalizer()
    
    try:
        result = normalizer.normalize_to_indonesian("ceftriaxone")
        print(f"   Input: ceftriaxone")
        print(f"   AI Result: {result.get('normalized_name')}")
        print(f"   Match Strategy: {result.get('match_strategy')}")
        print(f"   Confidence: {result.get('confidence_score', 0)}")
        
        # Cek apakah hasil AI cocok dengan DB
        if result.get('normalized_name'):
            db_check = db_exact_match(result['normalized_name'])
            if db_check:
                print(f"   ✅ DB Validation: Found '{db_check.obat_name}'")
            else:
                print(f"   ❌ DB Validation: '{result['normalized_name']}' not in DB")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Cek variants di DB
    print("\n4. Cek variants 'seftriakson' di DB:")
    from database_connection import get_db
    from models import FornasDrug
    
    db = next(get_db())
    variants = db.query(FornasDrug).filter(
        FornasDrug.obat_name.ilike('%triaks%')
    ).limit(10).all()
    
    print(f"   Found {len(variants)} variants:")
    for v in variants:
        print(f"   - {v.obat_name} ({v.kelas_terapi})")
    
    db.close()

if __name__ == "__main__":
    test_normalization_debug()
