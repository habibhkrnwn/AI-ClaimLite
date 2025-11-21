"""Quick script to check table names"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
engine = create_engine(DATABASE_URL)
conn = engine.connect()

result = conn.execute(text("""
    SELECT tablename 
    FROM pg_tables 
    WHERE schemaname='public' 
    ORDER BY tablename
"""))

print("Tables in database:")
print("-" * 50)
for row in result:
    print(f"  - {row[0]}")
