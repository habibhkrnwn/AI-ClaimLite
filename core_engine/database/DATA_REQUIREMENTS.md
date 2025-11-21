# INA-CBG Service - Data Requirements Summary

## 📊 DATA YANG PERLU KAMU MASUKKAN KE DATABASE

### ✅ 1. INACBG_TARIF (Sudah punya SQL file)
**Status**: ✅ Ready to import  
**File**: `inacbg_tarif_insert.sql` (yang kamu punya)  
**Records**: ~48,377 rows

**⚠️ PENTING - Perbaikan yang diperlukan:**
- Tabel `inacbg_tarif` TIDAK boleh punya constraint `UNIQUE(kode_ina_cbg)`
- Karena 1 kode CBG muncul berkali-kali (beda regional + kelas RS + tipe RS)
- Constraint yang benar: `UNIQUE(kode_ina_cbg, regional, kelas_rs, tipe_rs)`

**Struktur kolom:**
```
kode_ina_cbg     | K-1-14-III
deskripsi        | PROSEDUR HERNIA INGUINAL...
tarif_kelas_1    | 15736300 (untuk pasien BPJS kelas 1)
tarif_kelas_2    | 13784000 (untuk pasien BPJS kelas 2)
tarif_kelas_3    | 11831800 (untuk pasien BPJS kelas 3)
regional         | 1, 2, 3, 4, 5
kelas_rs         | A, B, C, D, dll
```

**Cara import:**
1. Jalankan `create_inacbg_tables.sql` dulu (drop & create table baru)
2. Baru import `inacbg_tarif_insert.sql`

---

### ✅ 2. CLEANED_MAPPING_CBG (Excel → Database)
**Status**: ⏳ Perlu diimport manual  
**File**: `cleaned_mapping_cbg.xlsx` (yang kamu punya)  
**Records**: ~3,000 patterns dari data RS

**Format Excel:**
```
layanan | icd10_primary | icd10_secondary | icd9_list | icd9_signature | inacbg_code
RI      | E87.1         | K30             | -         | -              | E-4-11-I
RI      | N21.0         | -               | 57        | 57             | N-1-40-I
```

**Cara import:**
- Via Python script (ada di README)
- Atau via pgAdmin import CSV/Excel
- Atau via DBeaver import

**Kolom yang penting:**
- `layanan` = RI atau RJ
- `icd10_primary` = kode ICD10 utama
- `icd10_secondary` = ICD10 sekunder (bisa kosong)
- `icd9_list` = kode ICD9 prosedur (bisa kosong, multiple separated by `;`)
- `icd9_signature` = signature untuk exact matching
- `inacbg_code` = KODE INA-CBG YANG BENAR (ini target output)

---

### 🤖 3. ICD10_CMG_MAPPING (Auto-generated)
**Status**: 🤖 Akan di-generate otomatis  
**Source**: Script Python `generate_mapping_data.py`  
**Records**: ~50 mappings

**Tidak perlu data manual** - script akan generate dari:
1. CMG rules di `cmg_mapping.json`
2. Pattern dari `inacbg_tarif` yang sudah ada

---

### 🤖 4. ICD9_PROCEDURE_INFO (Auto-generated)
**Status**: 🤖 Akan di-generate otomatis  
**Source**: Script Python `generate_mapping_data.py`  
**Records**: Tergantung unique ICD9 di `cleaned_mapping_cbg` (~250-500)

**Tidak perlu data manual** - script akan extract dari:
1. Unique ICD9 codes di `cleaned_mapping_cbg`
2. Grouping by chapter
3. Similarity mapping

---

## 📁 FILE JSON RULES (Sudah dibuat)

Semua file JSON sudah saya buatkan di `core_engine/rules/inacbg_rules/`:

### ✅ cmg_mapping.json
Mapping ICD10 chapter → CMG  
**Contoh:**
```json
{
  "I00-I99": {"cmg": "I", "description": "Cardiovascular system"},
  "K00-K93": {"cmg": "K", "description": "Digestive system"}
}
```

### ✅ case_type_rules.json
Rules untuk menentukan digit ke-2 kode INA-CBG  
**Contoh:**
```json
{
  "1": "Prosedur Rawat Inap",
  "4": "Rawat Inap Bukan Prosedur",
  "5": "Rawat Jalan Bukan Prosedur"
}
```

### ✅ icd9_chapter_mapping.json
Grouping ICD9 by chapter untuk similarity  
**Contoh:**
```json
{
  "42-54": {"category": "Digestive", "is_major": true},
  "87-99": {"category": "Diagnostic", "is_major": false}
}
```

---

## 🚀 URUTAN SETUP

### Step 1: Create Tables
```bash
psql -f core_engine/database/create_inacbg_tables.sql
```
✓ 5 tabel created

### Step 2: Import Master Tarif
```bash
psql -f inacbg_tarif_insert.sql
```
✓ ~48,000 rows inserted

### Step 3: Import Cleaned Mapping
```python
# Via Python script atau manual import Excel
```
✓ ~3,000 rows inserted

### Step 4: Generate Mapping Data
```bash
python core_engine/database/generate_mapping_data.py
```
✓ icd10_cmg_mapping generated (~50 rows)  
✓ icd9_procedure_info generated (~250 rows)

---

## 📋 CHECKLIST DATA YANG KAMU PERLU SEDIAKAN

- [x] `inacbg_tarif_insert.sql` ✅ Sudah ada
- [ ] `cleaned_mapping_cbg.xlsx` ⏳ Perlu diimport
- [x] `cmg_mapping.json` ✅ Sudah dibuat
- [x] `case_type_rules.json` ✅ Sudah dibuat
- [x] `icd9_chapter_mapping.json` ✅ Sudah dibuat
- [x] `create_inacbg_tables.sql` ✅ Sudah dibuat
- [x] `generate_mapping_data.py` ✅ Sudah dibuat
- [x] `SETUP_INACBG.md` ✅ Sudah dibuat (panduan lengkap)

---

## 🎯 YANG PERLU KAMU LAKUKAN SEKARANG

1. **Import Excel `cleaned_mapping_cbg.xlsx` ke database**
   - Bisa pakai Python script
   - Atau import manual via pgAdmin/DBeaver
   
2. **Fix dan re-import `inacbg_tarif`**
   - Drop table lama
   - Create table baru (pakai `create_inacbg_tables.sql`)
   - Import ulang SQL file kamu

3. **Run script generate_mapping_data.py**
   - Setelah kedua data di atas sudah masuk
   - Ini akan generate `icd10_cmg_mapping` dan `icd9_procedure_info`

---

## ✅ SETELAH DATA READY

Baru kita lanjut implementasi:
1. Service layer (`inacbg_grouper_service.py`)
2. FastAPI endpoint (`/api/v1/predict_inacbg`)
3. Unit testing
4. Integration

---

## 📞 PERTANYAAN?

Kalau ada yang bingung atau perlu bantuan import data, tanya aja!
