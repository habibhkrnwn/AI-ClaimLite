# INA-CBG Grouper Service - Setup Guide

## 📋 Overview

Service untuk memprediksi kode INA-CBG beserta tarifnya berdasarkan:
- ICD10 Primary & Secondary
- ICD9 Procedures
- Episode (RI/RJ)
- Kelas RS & Regional

## 🗂️ Struktur Data

### 1. Tabel Database

#### `inacbg_tarif` ✅
Master tarif INA-CBG dari Permenkes
- **Source**: File SQL yang sudah kamu punya (`inacbg_tarif_insert.sql`)
- **Records**: ~48,000 rows (kombinasi kode × regional × kelas RS)
- **Primary Key**: `id`
- **Unique Constraint**: `(kode_ina_cbg, regional, kelas_rs)`

#### `cleaned_mapping_cbg` ⏳
Data empiris ICD10+ICD9 → INA-CBG dari rumah sakit
- **Source**: Excel file dari kamu (perlu diimport)
- **Records**: ~3,000 unique patterns
- **Purpose**: Matching engine utama

#### `icd10_cmg_mapping` 🤖
Mapping ICD10 → CMG (Case Mix Group)
- **Source**: Auto-generated dari script
- **Purpose**: Fallback untuk rule-based grouping

#### `icd9_procedure_info` 🤖
Info ICD9 procedure untuk similarity matching
- **Source**: Auto-generated dari `cleaned_mapping_cbg`
- **Purpose**: Similar procedure matching

### 2. File JSON Rules

Sudah dibuat di `core_engine/rules/inacbg_rules/`:
- ✅ `cmg_mapping.json` - ICD10 chapter → CMG
- ✅ `case_type_rules.json` - Rules untuk case type
- ✅ `icd9_chapter_mapping.json` - ICD9 grouping & similarity

---

## 🚀 Setup Steps

### Step 1: Create Database Tables

```bash
cd core_engine
psql -U your_user -d your_database -f database/create_inacbg_tables.sql
```

Atau via DBeaver/pgAdmin:
1. Open `database/create_inacbg_tables.sql`
2. Execute all

**Output yang diharapkan:**
```
CREATE TABLE
CREATE INDEX
CREATE TABLE
...
✓ 5 tables created
✓ 15 indexes created
✓ 2 views created
```

---

### Step 2: Import Master Tarif INA-CBG

**PENTING**: Tabel `inacbg_tarif` TIDAK boleh punya `UNIQUE` constraint pada `kode_ina_cbg` karena 1 kode bisa muncul berkali-kali dengan kombinasi regional+kelas yang berbeda.

```bash
# Import file SQL kamu
psql -U your_user -d your_database -f /path/to/inacbg_tarif_insert.sql
```

**Verify:**
```sql
-- Total rows (should be ~48,000)
SELECT COUNT(*) FROM inacbg_tarif;

-- Check unique combinations
SELECT COUNT(DISTINCT kode_ina_cbg) as unique_codes,
       COUNT(DISTINCT regional) as regions,
       COUNT(DISTINCT kelas_rs) as classes,
       COUNT(DISTINCT tipe_rs) as tipe
FROM inacbg_tarif;

-- Example: 1 kode bisa punya banyak rows (beda regional, kelas, atau tipe RS)
SELECT kode_ina_cbg, regional, kelas_rs, tipe_rs, tarif_kelas_1 
FROM inacbg_tarif 
WHERE kode_ina_cbg = 'K-1-14-III' 
ORDER BY regional, kelas_rs, tipe_rs;
```

**Expected result:**
```
 kode_ina_cbg | regional | kelas_rs | tipe_rs    | tarif_kelas_1
--------------+----------+----------+------------+---------------
 K-1-14-III   | 1        | A        | Pemerintah | 18500000
 K-1-14-III   | 1        | A        | Swasta     | 19200000
 K-1-14-III   | 1        | B        | Pemerintah | 15736300
 K-1-14-III   | 1        | B        | Swasta     | ...
 K-1-14-III   | 2        | A        | Pemerintah | ...
 ...
```

---

### Step 3: Import Cleaned Mapping CBG

**Format Excel yang diharapkan:**

| layanan | icd10_primary | icd10_secondary | icd10_all | icd9_list | icd9_signature | kelas_raw | inacbg_code | diagnosis_raw | proclist_raw |
|---------|---------------|-----------------|-----------|-----------|----------------|-----------|-------------|---------------|--------------|
| RI | E87.1 | K30 | E87.1;K30 | - | - | 1 | E-4-11-I | E87.1;K30 | - |
| RI | N21.0 | - | N21.0 | 57 | 57 | 1 | N-1-40-I | N21.0 | 57 |

**Import via Python:**

```python
import pandas as pd
import psycopg2

# Read Excel
df = pd.read_excel('cleaned_mapping_cbg.xlsx')

# Connect to DB
conn = psycopg2.connect("dbname=... user=... password=...")
cursor = conn.cursor()

# Insert data
for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO cleaned_mapping_cbg 
        (layanan, icd10_primary, icd10_secondary, icd10_all, 
         icd9_list, icd9_signature, kelas_raw, inacbg_code, 
         diagnosis_raw, proclist_raw, frequency)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
    """, (
        row['layanan'],
        row['icd10_primary'],
        row['icd10_secondary'] if pd.notna(row['icd10_secondary']) else None,
        row['icd10_all'],
        row['icd9_list'] if pd.notna(row['icd9_list']) else None,
        row['icd9_signature'] if pd.notna(row['icd9_signature']) else None,
        row['kelas_raw'],
        row['inacbg_code'],
        row['diagnosis_raw'],
        row['proclist_raw'] if pd.notna(row['proclist_raw']) else None
    ))

conn.commit()
print(f"✓ Imported {len(df)} records")
```

**Verify:**
```sql
SELECT COUNT(*) FROM cleaned_mapping_cbg;

-- Check distribusi
SELECT layanan, COUNT(*) as total
FROM cleaned_mapping_cbg
GROUP BY layanan;

-- Sample data
SELECT * FROM cleaned_mapping_cbg LIMIT 10;
```

---

### Step 4: Generate Mapping Data

Jalankan script Python untuk auto-generate `icd10_cmg_mapping` dan `icd9_procedure_info`:

```bash
cd core_engine/database
python generate_mapping_data.py
```

**Output yang diharapkan:**
```
================================================================================
INA-CBG MAPPING DATA GENERATOR
================================================================================
✓ Connected to database

================================================================================
GENERATING ICD10 → CMG MAPPING
================================================================================
✓ Inserted 50 ICD10 → CMG mappings

Sample data:
  (1, None, 'A00', 'A99', 'A', 'Infectious & parasitic diseases', 1)
  (2, None, 'B00', 'B99', 'A', 'Infectious & parasitic diseases', 1)
  ...

================================================================================
GENERATING ICD9 PROCEDURE INFO
================================================================================
Found 250 unique ICD9 codes from mapping data
✓ Inserted 250 ICD9 procedure info records

ICD9 Distribution by Chapter:
Chapter      Category                       Total    Major    Minor
----------------------------------------------------------------------
42-54        Digestive                      80       80       0
55-59        Urinary                        15       0        15
...

================================================================================
DATA VERIFICATION
================================================================================
✓ icd10_cmg_mapping: 50 records
✓ icd9_procedure_info: 250 records
✓ cleaned_mapping_cbg: 3000 records
✓ inacbg_tarif: 48377 records

================================================================================
✓ DATA GENERATION COMPLETED SUCCESSFULLY
================================================================================
```

---

## ✅ Verification Checklist

Setelah semua step selesai, verify dengan query ini:

```sql
-- 1. Check all tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN (
    'inacbg_tarif', 
    'cleaned_mapping_cbg', 
    'icd10_cmg_mapping', 
    'icd9_procedure_info'
  );

-- 2. Check row counts
SELECT 
    (SELECT COUNT(*) FROM inacbg_tarif) as tarif_count,
    (SELECT COUNT(*) FROM cleaned_mapping_cbg) as mapping_count,
    (SELECT COUNT(*) FROM icd10_cmg_mapping) as cmg_count,
    (SELECT COUNT(*) FROM icd9_procedure_info) as icd9_count;

-- 3. Check sample matching
SELECT 
    m.icd10_primary,
    m.icd9_signature,
    m.layanan,
    m.inacbg_code,
    t.deskripsi,
    t.tarif_kelas_1
FROM cleaned_mapping_cbg m
JOIN inacbg_tarif t ON m.inacbg_code = t.kode_ina_cbg
WHERE t.regional = '1' AND t.kelas_rs = 'B'
LIMIT 10;
```

**Expected output:**
```
 table_name
-----------------------
 inacbg_tarif
 cleaned_mapping_cbg
 icd10_cmg_mapping
 icd9_procedure_info
(4 rows)

 tarif_count | mapping_count | cmg_count | icd9_count
-------------+---------------+-----------+------------
       48377 |          3000 |        50 |        250
```

---

## 📊 Data Summary

Setelah setup selesai, kamu akan punya:

| Tabel | Records | Source | Purpose |
|-------|---------|--------|---------|
| `inacbg_tarif` | ~48,000 | Permenkes SQL | Master tarif (truth source) |
| `cleaned_mapping_cbg` | ~3,000 | Excel RS | Empirical matching (highest accuracy) |
| `icd10_cmg_mapping` | ~50 | Auto-generated | CMG determination |
| `icd9_procedure_info` | ~250 | Auto-generated | Similarity matching |

**File JSON Rules:**
- ✅ `cmg_mapping.json` (31 CMGs mapped)
- ✅ `case_type_rules.json` (10 case types)
- ✅ `icd9_chapter_mapping.json` (16 chapters)

---

## 🐛 Troubleshooting

### Error: "duplicate key value violates unique constraint"

**Problem**: `kode_ina_cbg` marked as UNIQUE tapi 1 kode bisa muncul berkali-kali.

**Solution**: 
1. Drop existing table
2. Recreate dengan script baru (`create_inacbg_tables.sql`)
3. Re-import data

```sql
DROP TABLE IF EXISTS inacbg_tarif CASCADE;
-- Then run create_inacbg_tables.sql
```

### Error: "cleaned_mapping_cbg masih kosong"

Pastikan sudah import Excel data sebelum run `generate_mapping_data.py`.

### Error: "Module database_connection not found"

Make sure `database_connection.py` exists di `core_engine/` dan sudah configured dengan benar.

---

## 📝 Next Steps

Setelah data siap:
1. ✅ Implement service layer (`inacbg_grouper_service.py`)
2. ✅ Create FastAPI endpoint (`/api/v1/predict_inacbg`)
3. ✅ Unit testing
4. ✅ Integration dengan frontend

---

## 📞 Support

Jika ada masalah saat setup, check:
- Log errors dari script Python
- PostgreSQL logs
- Data format Excel (pastikan sesuai expected format)
