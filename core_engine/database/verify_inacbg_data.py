"""Verify all INA-CBG tables are populated correctly"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
engine = create_engine(DATABASE_URL)
conn = engine.connect()

print("="*80)
print("INA-CBG TABLES VERIFICATION")
print("="*80)

# 1. Check all tables exist and have data
tables = [
    'inacbg_tarif',
    'cleaned_mapping_inacbg',
    'icd10_cmg_mapping',
    'icd9_procedure_info',
    'icd10_severity_info'
]

print("\n1. TABLE ROW COUNTS:")
print("-" * 80)
print(f"{'Table Name':<30} {'Row Count':<15} {'Status':<10}")
print("-" * 80)

for table in tables:
    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
    count = result.fetchone()[0]
    status = "✓ OK" if count > 0 else "⚠ EMPTY"
    print(f"{table:<30} {count:<15} {status:<10}")

# 2. Sample data from icd10_cmg_mapping
print("\n2. SAMPLE ICD10 → CMG MAPPING:")
print("-" * 80)
result = conn.execute(text("""
    SELECT icd10_chapter_start, icd10_chapter_end, cmg, cmg_description
    FROM icd10_cmg_mapping
    ORDER BY cmg
    LIMIT 10
"""))
print(f"{'Chapter Range':<20} {'CMG':<5} {'Description':<40}")
print("-" * 80)
for row in result:
    chapter_range = f"{row[0]}-{row[1]}"
    print(f"{chapter_range:<20} {row[2]:<5} {row[3]:<40}")

# 3. Sample data from icd9_procedure_info
print("\n3. SAMPLE ICD9 PROCEDURE INFO:")
print("-" * 80)
result = conn.execute(text("""
    SELECT icd9_code, chapter_range, category, is_major_procedure
    FROM icd9_procedure_info
    ORDER BY icd9_code
    LIMIT 10
"""))
print(f"{'ICD9 Code':<15} {'Chapter':<12} {'Category':<30} {'Major':<8}")
print("-" * 80)
for row in result:
    major = "Yes" if row[3] else "No"
    print(f"{row[0]:<15} {row[1]:<12} {row[2]:<30} {major:<8}")

# 4. Sample matching test
print("\n4. SAMPLE MATCHING TEST:")
print("-" * 80)
result = conn.execute(text("""
    SELECT 
        m.icd10_primary,
        m.icd9_signature,
        m.layanan,
        m.inacbg_code,
        t.deskripsi,
        t.tarif_kelas_1
    FROM cleaned_mapping_inacbg m
    JOIN inacbg_tarif t ON m.inacbg_code = t.kode_ina_cbg
    WHERE t.regional = '1' AND t.kelas_rs = 'B' AND t.tipe_rs = 'Pemerintah'
    LIMIT 5
"""))

print(f"{'ICD10':<10} {'ICD9':<15} {'Layanan':<8} {'CBG Code':<12} {'Tarif Kelas 1':<15}")
print("-" * 80)
for row in result:
    print(f"{row[0]:<10} {row[1] or '-':<15} {row[2]:<8} {row[3]:<12} {row[5]:>14,.0f}")

# 5. Statistics
print("\n5. STATISTICS:")
print("-" * 80)

# Unique CBG codes
result = conn.execute(text("SELECT COUNT(DISTINCT inacbg_code) FROM cleaned_mapping_inacbg"))
unique_cbg = result.fetchone()[0]

# Unique ICD10
result = conn.execute(text("SELECT COUNT(DISTINCT icd10_primary) FROM cleaned_mapping_inacbg"))
unique_icd10 = result.fetchone()[0]

# Unique ICD9
result = conn.execute(text("SELECT COUNT(DISTINCT icd9_code) FROM icd9_procedure_info"))
unique_icd9 = result.fetchone()[0]

# CMG coverage
result = conn.execute(text("SELECT COUNT(DISTINCT cmg) FROM icd10_cmg_mapping"))
cmg_count = result.fetchone()[0]

print(f"  Unique INA-CBG codes in mapping : {unique_cbg}")
print(f"  Unique ICD10 diagnoses          : {unique_icd10}")
print(f"  Unique ICD9 procedures          : {unique_icd9}")
print(f"  CMG covered                     : {cmg_count}")

print("\n" + "="*80)
print("✓ VERIFICATION COMPLETED")
print("="*80)

conn.close()
