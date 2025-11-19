# 🐛 BUG FIX: Konsistensi Klinis Selalu Parsial/Sedang

## 📋 RINGKASAN

**Masalah**: Panel Konsistensi Klinis di UI selalu menampilkan hasil yang sama (⚠️ Parsial untuk semua dimensi dan Sedang untuk tingkat overall), tidak peduli input apapun yang diberikan.

**Root Cause**: Field name mismatch dalam ekstraksi ICD-9 codes, menyebabkan `tx_list` selalu kosong saat dikirim ke `analyze_clinical_consistency()`.

**Status**: ✅ **FIXED**

---

## 🔍 INVESTIGASI

### Problem Flow

```
UI Input (Pneumonia + Nebulisasi + Ceftriaxone)
    ↓
Backend (Express.js) - aiRoutes.ts
    ↓
Core Engine (FastAPI) - lite_endpoints.py
    ↓
lite_service_ultra_fast.py - analyze_lite_single_ultra_fast()
    ↓
_enrich_tindakan_parallel() → Returns [{icd9_code: "93.96", ...}]
    ↓
❌ Line 653: Extract using icd9_codes = [t.get("icd9", "")]  ← WRONG FIELD!
    ↓
Result: icd9_codes = []  (empty!)
    ↓
analyze_clinical_consistency(dx="J18.9", tx_list=[], drug_list=["ceftriaxone"])
    ↓
Result: Always ⚠️ Parsial because tx_list is empty
```

### Code Analysis

#### Bug #1: Field Mismatch (LINE 653)
**File**: `core_engine/services/lite_service_ultra_fast.py`

**Before**:
```python
# Line 653 (WRONG)
icd9_codes = [t.get("icd9", "") for t in tindakan_formatted if t.get("icd9") and t.get("icd9") != "-"]
```

**Struktur Data Actual** (from line 315-350):
```python
tindakan_with_icd9.append({
    "nama": tindakan_name,
    "icd9_code": first_suggestion.get("code", "-"),  # ← Uses icd9_code
    "icd9_desc": first_suggestion.get("name", "-"),
    "icd9_confidence": first_suggestion.get("confidence", 0),
    "status": "auto_selected"
})
```

**Impact**: 
- `icd9_codes` selalu `[]` (empty array)
- `consistency_service.analyze_clinical_consistency()` dipanggil dengan `tx_list=[]`
- Semua validasi DX→TX dan TX→DRUG return ⚠️ Parsial karena "tidak ada tindakan"

**After (FIXED)**:
```python
# Line 653 (CORRECT)
icd9_codes = [t.get("icd9_code", "") for t in tindakan_formatted if t.get("icd9_code") and t.get("icd9_code") != "-"]
logger.info(f"[CONSISTENCY] Extracted ICD-9 codes for validation: {icd9_codes}")
```

---

#### Bug #2: Unreachable Code (LINE 161)
**File**: `core_engine/services/consistency_service.py`

**Before**:
```python
# Line 160-162 (DUPLICATE RETURN)
return score, matched, total_actual
return score, matched, total_expected  # ← UNREACHABLE!
```

**Impact**: 
- Minor issue, tidak mempengaruhi logic karena return pertama sudah benar
- Menyebabkan warning di linters
- Variable `total_expected` tidak pernah direturn (misleading)

**After (FIXED)**:
```python
# Line 160 (CLEAN)
return score, matched, total_actual
```

---

## ✅ SOLUSI

### Changes Made

#### 1. Fix Field Name Mismatch
**File**: `core_engine/services/lite_service_ultra_fast.py` Line 653

```python
# OLD
icd9_codes = [t.get("icd9", "") for t in tindakan_formatted if t.get("icd9") and t.get("icd9") != "-"]

# NEW
icd9_codes = [t.get("icd9_code", "") for t in tindakan_formatted if t.get("icd9_code") and t.get("icd9_code") != "-"]
logger.info(f"[CONSISTENCY] Extracted ICD-9 codes for validation: {icd9_codes}")
```

**Benefit**:
- ICD-9 codes sekarang ter-ekstrak dengan benar
- `analyze_clinical_consistency()` menerima data lengkap
- Validasi klinis berfungsi sesuai expected

#### 2. Remove Duplicate Return
**File**: `core_engine/services/consistency_service.py` Line 161

```python
# OLD
return score, matched, total_actual
return score, matched, total_expected  # removed

# NEW
return score, matched, total_actual
```

---

## 🧪 TESTING

### Test Script
Created `test_consistency_debug.py` untuk trace exact flow:

```bash
cd core_engine
python test_consistency_debug.py
```

### Test Results

#### Case 1: Pneumonia dengan Nebulisasi + Ceftriaxone (Exact Match)
```json
{
  "dx_tx": {"status": "✅ Sesuai"},
  "dx_drug": {"status": "✅ Sesuai"},
  "tx_drug": {"status": "✅ Sesuai"},
  "tingkat_konsistensi": "Tinggi",
  "_score": 3.0
}
```

#### Case 2: Partial Match
```json
{
  "dx_tx": {"status": "✅ Sesuai"},
  "dx_drug": {"status": "✅ Sesuai"},
  "tx_drug": {"status": "⚠️ Parsial"},
  "tingkat_konsistensi": "Tinggi",
  "_score": 2.5
}
```

#### Case 3: Wrong Inputs
```json
{
  "dx_tx": {"status": "❌ Tidak Sesuai"},
  "dx_drug": {"status": "❌ Tidak Sesuai"},
  "tx_drug": {"status": "⚠️ Parsial"},
  "tingkat_konsistensi": "Rendah",
  "_score": 0.5
}
```

---

## 📊 LOGIC FLOW (CORRECT)

### Input → Output Flow

```
1. USER INPUT (UI - SmartInputPanel.tsx)
   ├─ Diagnosis: "Pneumonia"
   ├─ Tindakan: "Nebulisasi"
   ├─ Obat: "Ceftriaxone"
   └─ Service Type: "rawat-inap"

2. FRONTEND (AdminRSDashboard.tsx)
   └─ POST /api/ai/analyze
      {mode: 'form', diagnosis, tindakan, obat, service_type}

3. BACKEND (aiRoutes.ts)
   └─ Forward to core_engine
      POST http://localhost:8000/api/lite/analyze/single

4. CORE ENGINE (lite_endpoints.py)
   └─ Call analyze_lite_single_ultra_fast()

5. SERVICE LAYER (lite_service_ultra_fast.py)
   ├─ Parse input
   ├─ Lookup ICD-10: "Pneumonia" → J18.9
   ├─ Lookup ICD-9: "Nebulisasi" → 93.96
   ├─ _enrich_tindakan_parallel() returns:
   │  [{icd9_code: "93.96", nama: "Nebulisasi", ...}]
   │
   ├─ ✅ Extract ICD-9 codes (FIXED):
   │  icd9_codes = ["93.96"]
   │
   └─ Call analyze_clinical_consistency(
        dx="J18.9",
        tx_list=["93.96"],  ← NOW POPULATED!
        drug_list=["ceftriaxone"]
      )

6. CONSISTENCY SERVICE (consistency_service.py)
   ├─ Load mappings from JSON:
   │  ├─ icd10_icd9_map.json (DX→TX)
   │  ├─ diagnosis_obat_map.json (DX→DRUG)
   │  └─ tindakan_obat_map.json (TX→DRUG)
   │
   ├─ Validate DX→TX:
   │  ├─ J18.9 expected: [87.44, 90.43, 93.96, ...]
   │  ├─ Actual: [93.96]
   │  ├─ Match: 1/1 = 100% (>80%)
   │  └─ Status: ✅ Sesuai
   │
   ├─ Validate DX→DRUG:
   │  ├─ J18.9 expected: [ceftriaxone, amoxicillin, ...]
   │  ├─ Actual: [ceftriaxone]
   │  ├─ Match: 1/1 = 100% (>70%)
   │  └─ Status: ✅ Sesuai
   │
   ├─ Validate TX→DRUG:
   │  ├─ 93.96 expected: [ceftriaxone, azithromycin, ...]
   │  ├─ Actual: [ceftriaxone]
   │  ├─ Match: 1/1 = 100% (>50%)
   │  └─ Status: ✅ Sesuai
   │
   └─ Calculate overall:
      ├─ Total Score: 1.0 + 1.0 + 1.0 = 3.0
      └─ Tingkat: "Tinggi" (>=2.5)

7. RESPONSE TO UI (ResultsPanel.tsx)
   └─ Display:
      ├─ DX→TX: ✅ Sesuai
      ├─ DX→DRUG: ✅ Sesuai
      ├─ TX→DRUG: ✅ Sesuai
      └─ Tingkat Konsistensi: Tinggi
```

---

## 📁 FILES MODIFIED

1. **core_engine/services/consistency_service.py**
   - Line 161: Removed duplicate return statement

2. **core_engine/services/lite_service_ultra_fast.py**
   - Line 653-654: Fixed field name from `icd9` to `icd9_code`
   - Added logging untuk debugging

3. **core_engine/test_consistency_debug.py** (NEW)
   - Test script untuk validasi fix

---

## 🔍 VERIFICATION STEPS

### 1. Check Logs
Setelah fix, log akan menampilkan:
```
[CONSISTENCY] Extracted ICD-9 codes for validation: ['93.96']
[DX→TX] Validating: J18.9 → ['93.96']
[DX→DRUG] Validating: J18.9 → ['ceftriaxone']
[TX→DRUG] Validating: ['93.96'] → ['ceftriaxone']
[CONSISTENCY] Result: Tinggi (score=3.00)
```

**Before Fix**:
```
[CONSISTENCY] Extracted ICD-9 codes for validation: []  ← EMPTY!
[DX→TX] Validating: J18.9 → []
[TX→DRUG] Validating: [] → ['ceftriaxone']
[CONSISTENCY] Result: Sedang (score=1.5)
```

### 2. UI Testing
```
Input:
- Diagnosis: Pneumonia
- Tindakan: Nebulisasi, Rontgen Thorax
- Obat: Ceftriaxone, Amoxicillin

Expected Output:
✅ DX→TX: Sesuai
✅ DX→DRUG: Sesuai
✅ TX→DRUG: Sesuai
Tingkat: Tinggi
```

### 3. Docker Restart Required
```bash
docker compose down
docker compose up
```

Core engine akan auto-reload karena file changes detected.

---

## 📚 MAPPING FILES USED

1. **core_engine/rules/icd10_icd9_map.json** (57 entries)
   - Maps ICD-10 diagnosis → ICD-9 procedures
   - Example: `"J18.9": ["87.44", "90.43", "93.96", ...]`

2. **core_engine/rules/diagnosis_obat_map.json** (57 entries)
   - Maps ICD-10 diagnosis → Drug names
   - Example: `"J18.9": ["ceftriaxone", "amoxicillin", ...]`

3. **core_engine/rules/tindakan_obat_map.json** (56 entries)
   - Maps ICD-9 procedures → Related drugs
   - Example: `"93.96": ["ceftriaxone", "azithromycin", ...]`

---

## ⚡ IMPACT

### Before Fix
- ❌ Konsistensi klinis tidak berfungsi
- ❌ Selalu menampilkan ⚠️ Parsial / Sedang
- ❌ Tidak ada variasi hasil berdasarkan input
- ❌ Mapping JSON tidak terpakai

### After Fix
- ✅ Konsistensi klinis berfungsi dengan benar
- ✅ Hasil bervariasi sesuai input (Tinggi/Sedang/Rendah)
- ✅ Validasi 3 dimensi (DX→TX, DX→DRUG, TX→DRUG) akurat
- ✅ Mapping JSON terpakai dengan proper
- ✅ Catatan klinis memberikan feedback konkret

---

## 🎯 NEXT STEPS

1. ✅ **Test di UI** dengan berbagai case:
   - Exact match → expect Tinggi
   - Partial match → expect Sedang
   - Wrong input → expect Rendah

2. ⚠️ **Expand Mapping Files** (optional):
   - Tambah lebih banyak diagnosis ke JSON files
   - Cover more ICD-10 codes untuk RS

3. 📊 **Monitor Logs** di production:
   - Check apakah ICD-9 codes ter-ekstrak
   - Verify scoring logic bekerja

4. 🧪 **Add Unit Tests**:
   - Test consistency_service functions
   - Test edge cases (empty inputs, invalid codes)

---

## 📝 CATATAN TAMBAHAN

### Why This Bug Was Hard to Find

1. **Silent Failure**: Code tidak throw error, hanya return empty array
2. **Partial Results**: Masih ada output (⚠️ Parsial), jadi terlihat "bekerja"
3. **Complex Flow**: Data melalui 6+ layers (UI → Backend → Core → Service → Consistency)
4. **Field Name Similar**: `icd9` vs `icd9_code` mudah terlewat
5. **No Type Safety**: Python dict tidak enforce field names

### Preventive Measures

1. **Add Type Hints** (TypedDict):
   ```python
   class TindakanFormatted(TypedDict):
       nama: str
       icd9_code: str  # Not icd9!
       icd9_desc: str
       icd9_confidence: int
       status: str
   ```

2. **Add Logging**: Already added in fix
   ```python
   logger.info(f"[CONSISTENCY] Extracted ICD-9 codes: {icd9_codes}")
   ```

3. **Unit Tests**: Create test_consistency_service.py

---

**Last Updated**: 2025-11-18  
**Fixed By**: AI Assistant  
**Tested**: ✅ Passed (test_consistency_debug.py)  
**Deployed**: Pending Docker restart
