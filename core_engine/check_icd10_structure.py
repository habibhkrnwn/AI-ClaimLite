# Quick check untuk struktur icd10_master
from database_connection import engine
import sqlalchemy

insp = sqlalchemy.inspect(engine)
tables = insp.get_table_names()

print("=== DATABASE TABLES ===")
print("All tables:", tables)

if 'icd10_master' in tables:
    print("\n=== ICD10_MASTER STRUCTURE ===")
    cols = insp.get_columns('icd10_master')
    for col in cols:
        print(f"  - {col['name']}: {col['type']}")
    
    # Sample data
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM icd10_master"))
        count = result.scalar()
        print(f"\n=== DATA COUNT ===")
        print(f"Total records: {count}")
        
        result = conn.execute(text("SELECT * FROM icd10_master LIMIT 5"))
        print(f"\n=== SAMPLE DATA ===")
        for row in result:
            print(f"  {row}")
else:
    print("\n❌ Table icd10_master NOT FOUND!")
