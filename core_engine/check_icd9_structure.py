# check_icd9_structure.py
from sqlalchemy import text, inspect
from database_connection import get_db_session

session = get_db_session()

# Get all tables
inspector = inspect(session.bind)
tables = inspector.get_table_names()
print("=== DATABASE TABLES ===")
print(f"All tables: {tables}")

# Check if icd9cm_master exists
if 'icd9cm_master' in tables:
    print("\n=== ICD9CM_MASTER STRUCTURE ===")
    columns = inspector.get_columns('icd9cm_master')
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")
    
    # Get count
    print("\n=== DATA COUNT ===")
    result = session.execute(text("SELECT COUNT(*) FROM icd9cm_master"))
    count = result.scalar()
    print(f"Total records: {count}")
    
    # Get sample data
    print("\n=== SAMPLE DATA ===")
    result = session.execute(text("SELECT * FROM icd9cm_master LIMIT 10"))
    for row in result:
        print(f"  {row}")
else:
    print("\n❌ icd9cm_master table NOT FOUND in database")

session.close()
