from sqlalchemy import text
from database_connection import get_db_session

session = get_db_session()
result = session.execute(text("SELECT code, name FROM icd9cm_master WHERE LOWER(name) LIKE '%chest%' AND LOWER(name) LIKE '%x-ray%' LIMIT 10"))
print('Chest X-ray procedures in DB:')
for r in result.fetchall():
    print(f'{r[0]}: {r[1]}')
session.close()
