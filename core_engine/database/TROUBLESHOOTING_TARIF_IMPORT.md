# TROUBLESHOOTING: Duplicate Key Error saat Import inacbg_tarif

## ❌ Error yang Terjadi

```
ERROR: duplicate key value violates unique constraint "unique_cbg_regional_kelas"
Key (kode_ina_cbg, regional, kelas_rs)=(A-4-10-I, 1, A) already exists.
```

## 🔍 Root Cause Analysis

### Problem:
Data INA-CBG tarif punya struktur seperti ini:

| kode_ina_cbg | regional | kelas_rs | tipe_rs    | tarif_kelas_1 |
|--------------|----------|----------|------------|---------------|
| A-4-10-I     | 1        | A        | Pemerintah | 3,702,300     |
| A-4-10-I     | 1        | A        | Swasta     | 3,813,400     |

**Insight:**
- 1 kode CBG yang sama
- Regional sama (1)
- Kelas RS sama (A)
- **TAPI tipe_rs BEDA** (Pemerintah vs Swasta)

### Old Constraint (SALAH):
```sql
UNIQUE (kode_ina_cbg, regional, kelas_rs)
```

Ini akan error karena kombinasi `(A-4-10-I, 1, A)` muncul 2x (untuk Pemerintah dan Swasta).

### New Constraint (BENAR):
```sql
UNIQUE (kode_ina_cbg, regional, kelas_rs, tipe_rs)
```

Sekarang kombinasi lengkap:
- `(A-4-10-I, 1, A, Pemerintah)` ✓
- `(A-4-10-I, 1, A, Swasta)` ✓

Keduanya UNIK!

---

## ✅ SOLUSI

### Step 1: Drop Table Lama
```sql
DROP TABLE IF EXISTS inacbg_tarif CASCADE;
```

Atau via PowerShell + psql:
```powershell
psql -U your_user -d your_database -c "DROP TABLE IF EXISTS inacbg_tarif CASCADE;"
```

### Step 2: Recreate Table dengan Schema Baru
```powershell
cd E:\SOFTWARE\GitHub\repo\AIClaimLite\AI-ClaimLite
psql -U your_user -d your_database -f core_engine\database\create_inacbg_tables.sql
```

**Verify table created:**
```sql
\d inacbg_tarif
```

Should show:
```
Indexes:
    "inacbg_tarif_pkey" PRIMARY KEY, btree (id)
    "unique_cbg_regional_kelas_tipe" UNIQUE CONSTRAINT, btree (kode_ina_cbg, regional, kelas_rs, tipe_rs)
```

### Step 3: Import Data
```powershell
psql -U your_user -d your_database -f E:\Downloads\inacbg_tarif_insert.sql
```

**Expected output:**
```
INSERT 0 48377
```

### Step 4: Verify Import
```sql
-- Check total rows
SELECT COUNT(*) FROM inacbg_tarif;
-- Should return: 48377 (atau sesuai jumlah data kamu)

-- Check unique combinations
SELECT 
    COUNT(DISTINCT kode_ina_cbg) as unique_codes,
    COUNT(DISTINCT regional) as regions,
    COUNT(DISTINCT kelas_rs) as classes,
    COUNT(DISTINCT tipe_rs) as tipe
FROM inacbg_tarif;

-- Sample: 1 kode dengan berbagai kombinasi
SELECT kode_ina_cbg, regional, kelas_rs, tipe_rs, tarif_kelas_1 
FROM inacbg_tarif 
WHERE kode_ina_cbg = 'A-4-10-I' 
ORDER BY regional, kelas_rs, tipe_rs;
```

**Expected output:**
```
 kode_ina_cbg | regional | kelas_rs | tipe_rs    | tarif_kelas_1
--------------+----------+----------+------------+---------------
 A-4-10-I     | 1        | A        | Pemerintah |    4924100.00
 A-4-10-I     | 1        | A        | Swasta     |    5071800.00
 A-4-10-I     | 1        | B        | Pemerintah |    ...
 A-4-10-I     | 2        | A        | Pemerintah |    ...
 ...
```

---

## 📊 Data Structure Insight

Setelah analisis, struktur lengkap data INA-CBG tarif adalah:

```
1 Kode CBG × 5 Regional × ~7 Kelas RS × 2 Tipe RS = ~70 kombinasi per kode
```

**Breakdown:**
- **Regional**: 1, 2, 3, 4, 5
- **Kelas RS**: A, B, B Pendidikan, C, D, Khusus Rujukan Nasional, Umum Rujukan Nasional
- **Tipe RS**: Pemerintah, Swasta

Total rows dalam database: **~48,000 rows** untuk ~1,200 unique kode CBG.

---

## 🎯 Implikasi untuk Query Tarif

Saat memprediksi INA-CBG dan ambil tarif, perlu **4 parameter**:

```python
def get_tarif(kode_cbg, regional, kelas_rs, tipe_rs, kelas_bpjs):
    """
    Args:
        kode_cbg: "A-4-10-I"
        regional: 1-5
        kelas_rs: "A", "B", "C", "D", dll
        tipe_rs: "Pemerintah" atau "Swasta"
        kelas_bpjs: 1, 2, 3 (untuk pilih kolom tarif_kelas_1/2/3)
    """
    
    query = """
        SELECT 
            kode_ina_cbg,
            deskripsi,
            CASE 
                WHEN %s = 1 THEN tarif_kelas_1
                WHEN %s = 2 THEN tarif_kelas_2
                WHEN %s = 3 THEN tarif_kelas_3
            END as tarif
        FROM inacbg_tarif
        WHERE kode_ina_cbg = %s
          AND regional = %s
          AND kelas_rs = %s
          AND tipe_rs = %s
          AND is_active = TRUE
    """
    
    return execute_query(query, [
        kelas_bpjs, kelas_bpjs, kelas_bpjs,
        kode_cbg, regional, kelas_rs, tipe_rs
    ])
```

---

## 🐛 Common Errors & Solutions

### Error 1: "relation inacbg_tarif does not exist"
**Solution:** Run `create_inacbg_tables.sql` first.

### Error 2: "duplicate key value violates unique constraint"
**Solution:** Make sure you're using the LATEST `create_inacbg_tables.sql` yang sudah include `tipe_rs` di UNIQUE constraint.

### Error 3: "No rows returned from tarif query"
**Solution:** Check apakah kombinasi `(kode_cbg, regional, kelas_rs, tipe_rs)` ada di database.

```sql
-- Debug query
SELECT * FROM inacbg_tarif 
WHERE kode_ina_cbg = 'A-4-10-I' 
  AND regional = 1 
  AND kelas_rs = 'A';
-- Should return 2 rows (Pemerintah & Swasta)
```

---

## ✅ Verification Checklist

Setelah import berhasil:

- [ ] Table `inacbg_tarif` exists
- [ ] UNIQUE constraint include `tipe_rs`
- [ ] Total rows = ~48,377
- [ ] No duplicate errors
- [ ] Query sample data berhasil
- [ ] Tarif untuk Pemerintah ≠ Swasta (untuk kode yang sama)

---

## 📝 Next Steps

Setelah `inacbg_tarif` berhasil diimport:

1. ✅ Import `cleaned_mapping_cbg` (data empiris RS)
2. ✅ Run `generate_mapping_data.py` (auto-generate ICD10/ICD9 mapping)
3. ✅ Verify all tables populated
4. ✅ Ready untuk implementasi service!

---

## 💡 Tips

**Jika ingin re-import:**
```sql
-- Truncate instead of DROP (lebih cepat)
TRUNCATE TABLE inacbg_tarif RESTART IDENTITY CASCADE;

-- Then import
\i E:/Downloads/inacbg_tarif_insert.sql
```

**Check import progress:**
```sql
-- During import (in another terminal)
SELECT COUNT(*) FROM inacbg_tarif;
```

**Optimize after import:**
```sql
ANALYZE inacbg_tarif;
VACUUM ANALYZE inacbg_tarif;
```
