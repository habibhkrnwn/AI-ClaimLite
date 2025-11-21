"""Test tarif query"""
from database_connection import get_db_session
from sqlalchemy import text

with get_db_session() as session:
    # Test 1: Check if I-4-10-I exists with inap
    print("\n=== Test 1: I-4-10-I ===")
    result = session.execute(text("""
        SELECT kode_ina_cbg, layanan, regional, kelas_rs, tipe_rs, tarif_kelas_1
        FROM inacbg_tarif
        WHERE kode_ina_cbg = 'I-4-10-I'
        LIMIT 5
    """))
    
    for row in result:
        print(f"  {row[0]} | {row[1]} | Reg {row[2]} | {row[3]} | {row[4]} | Rp {float(row[5]):,.0f}")
    
    # Test 2: Check if Q-5-42-0 exists with jalan
    print("\n=== Test 2: Q-5-42-0 ===")
    result = session.execute(text("""
        SELECT kode_ina_cbg, layanan, regional, kelas_rs, tipe_rs, tarif_kelas_2
        FROM inacbg_tarif
        WHERE kode_ina_cbg = 'Q-5-42-0'
        LIMIT 5
    """))
    
    for row in result:
        print(f"  {row[0]} | {row[1]} | Reg {row[2]} | {row[3]} | {row[4]} | Rp {float(row[5]):,.0f}")
    
    # Test 3: What layanan values exist?
    print("\n=== Test 3: Distinct layanan values ===")
    result = session.execute(text("""
        SELECT DISTINCT layanan, COUNT(*)
        FROM inacbg_tarif
        GROUP BY layanan
    """))
    
    for row in result:
        print(f"  '{row[0]}' : {row[1]} records")
