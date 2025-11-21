# 📋 Dokumen Wajib - Logic Flow & Output Analysis

## 📋 Overview

Fungsi `_generate_dokumen_wajib()` adalah komponen yang menghasilkan daftar dokumen wajib untuk klaim BPJS berdasarkan diagnosis dan tindakan yang dilakukan.

**Lokasi**: `core_engine/services/lite_service.py` (baris 944-1003)

---

## 🔄 Logic Flow Diagram

```
START: _generate_dokumen_wajib(diagnosis, tindakan_list, full_analysis, client)
  │
  ├─ Step 1: Check OpenAI Client Availability
  │   ├─ IF client is None OR OPENAI_AVAILABLE is False
  │   │   └─ SKIP to Fallback (Step 4)
  │   │
  │   └─ ELSE: Proceed to AI Generation
  │
  ├─ Step 2: Prepare Context for AI
  │   ├─ Extract diagnosis name
  │   ├─ Format tindakan_list (max 3 items, comma-separated)
  │   │   └─ If tindakan_list empty → use "tidak ada"
  │   └─ Note: full_analysis parameter NOT used
  │
  ├─ Step 3: Call OpenAI API
  │   ├─ Model: gpt-4o-mini
  │   ├─ Temperature: 0.3 (low for consistency)
  │   ├─ Max tokens: 200
  │   ├─ System prompt: "Expert verifikasi dokumen klaim BPJS Indonesia"
  │   ├─ User prompt:
  │   │   """
  │   │   Berikan daftar dokumen wajib untuk klaim BPJS dengan:
  │   │   - Diagnosis: {diagnosis}
  │   │   - Tindakan: {tindakan_str}
  │   │   
  │   │   Format output sebagai JSON array of strings (max 5 dokumen)
  │   │   Hanya dokumen yang relevan dan wajib.
  │   │   """
  │   │
  │   ├─ Parse response:
  │   │   ├─ IF response is valid JSON array → Extract dokumen_list
  │   │   ├─ Slice to max 5 items (dokumen_list[:5])
  │   │   └─ RETURN dokumen_list
  │   │
  │   └─ IF exception occurs:
  │       ├─ Log warning: "[DOKUMEN_WAJIB] ❌ AI generation error: {e}"
  │       └─ Fall through to Step 4
  │
  ├─ Step 4: Database Fallback (NOT IMPLEMENTED)
  │   ├─ TODO: Query database for dokumen_wajib by diagnosis
  │   └─ Currently skipped (no implementation)
  │
  ├─ Step 5: Final Fallback (Error Messages)
  │   ├─ Log error: "[DOKUMEN_WAJIB] ❌ All sources failed for {diagnosis}"
  │   └─ RETURN error message list:
  │       [
  │         "⚠️ Data dokumen wajib tidak tersedia di database",
  │         "⚠️ AI tidak dapat menghasilkan daftar dokumen",
  │         "⚠️ Silakan hubungi admin untuk menambahkan data dokumen wajib"
  │       ]
  │
END: Return List[str]
```

---

## 📊 Data Source Priority

```
PRIORITAS 1: AI Generation (OpenAI GPT-4o-mini)
├─ Status: ✅ ACTIVE
├─ Trigger: client != None AND OPENAI_AVAILABLE == True
├─ Input: diagnosis + tindakan_list (max 3 items)
├─ Output: List[str] (max 5 dokumen names)
└─ Fallback: Jika exception → go to PRIORITAS 2

PRIORITAS 2: Database Query
├─ Status: ❌ NOT IMPLEMENTED
├─ Code: TODO comment (lines 991-997)
├─ Reserved for: Future implementation dengan tabel dokumen_wajib
└─ Planned structure:
    ```python
    rawat_inap = full_analysis.get("rawat_inap", {})
    dokumen_db = rawat_inap.get("dokumen_wajib", [])
    if dokumen_db:
        return dokumen_db
    ```

PRIORITAS 3: Error Messages Fallback
├─ Status: ✅ ACTIVE (always as last resort)
├─ Trigger: All sources failed
└─ Output: 3 error messages guiding user to contact admin
```

---

## 📤 Output Format

### ✅ Success Case (AI-Generated)

**Input:**
```python
diagnosis = "Pneumonia"
tindakan_list = ["Rontgen Thorax", "Nebulisasi", "Lab Darah"]
```

**Expected Output:**
```python
[
  "Resume Medis",
  "Hasil Lab Darah Lengkap",
  "Hasil Foto Thorax",
  "Resep Obat",
  "Surat Rujukan (jika dari Faskes 1)"
]
```

**Characteristics:**
- ✅ Contextual to diagnosis (Pneumonia → Lab Darah, Foto Thorax)
- ✅ Relevant to tindakan (Rontgen Thorax → Hasil Foto Thorax)
- ✅ Max 5 items (enforced by `[:5]` slice)
- ✅ Plain strings (dokumen names only)

---

### ❌ Fallback Case (Error Messages)

**Input:**
```python
diagnosis = "Pneumonia"
tindakan_list = ["Rontgen Thorax"]
client = None  # No OpenAI client
```

**Actual Output:**
```python
[
  "⚠️ Data dokumen wajib tidak tersedia di database",
  "⚠️ AI tidak dapat menghasilkan daftar dokumen",
  "⚠️ Silakan hubungi admin untuk menambahkan data dokumen wajib"
]
```

**Characteristics:**
- ⚠️ Not contextual to diagnosis
- ⚠️ Generic error guidance
- ⚠️ Always 3 items (fixed error list)

---

## 🎯 How It's Called in `analyze_lite_single()`

**Location:** `lite_service.py` line 657

```python
"checklist_dokumen": _generate_dokumen_wajib(
    diagnosis_name,  # e.g., "Pneumonia"
    [t['name'] for t in tindakan_with_icd9],  # List of tindakan names
    lite_analysis,  # full_analysis parameter (NOT USED in function)
    parser.client if hasattr(parser, 'client') else None  # OpenAI client
)
```

**Input Sources:**
- `diagnosis_name`: Extracted from parsing result (OpenAI medical parser)
- `tindakan_with_icd9`: Result from `lookup_icd9_procedure()` for each tindakan
- `lite_analysis`: Result from `analyze_diagnosis_lite()` (contains ICD-10, severity)
- `parser.client`: OpenAI client from global `OpenAIMedicalParser` instance

**Output Destination:**
- Stored in `lite_result["checklist_dokumen"]`
- Displayed in **Panel 4: Checklist Dokumen Wajib** on frontend

---

## 🔬 Test Scenarios Analysis

### Scenario 1: Pneumonia dengan Tindakan Lengkap

**Input:**
```python
diagnosis = "Pneumonia"
tindakan = ["Rontgen Thorax", "Nebulisasi", "Lab Darah Lengkap"]
```

**Expected AI Output:**
```python
[
  "Resume Medis",
  "Hasil Lab Darah Lengkap",
  "Hasil Foto Thorax",
  "Resep Obat Antibiotik",
  "Catatan Perawatan Harian"
]
```

---

### Scenario 2: Diabetes dengan Tindakan Minimal

**Input:**
```python
diagnosis = "Diabetes Mellitus Type 2"
tindakan = ["Pemeriksaan Gula Darah"]
```

**Expected AI Output:**
```python
[
  "Resume Medis",
  "Hasil Pemeriksaan Gula Darah",
  "Resep Obat",
  "Catatan Edukasi Pasien"
]
```

---

### Scenario 3: Appendicitis dengan Operasi

**Input:**
```python
diagnosis = "Appendicitis Akut"
tindakan = ["Appendektomi", "Lab Darah", "USG Abdomen"]
```

**Expected AI Output:**
```python
[
  "Resume Medis",
  "Informed Consent Operasi",
  "Hasil Lab Pra-Operasi",
  "Hasil USG Abdomen",
  "Laporan Operasi"
]
```

**Analysis:**
- AI understands surgical context (Informed Consent, Laporan Operasi)
- Includes pre-op requirements (Lab Pra-Operasi)
- Prioritizes dokumen critical for operasi cases

---

### Scenario 4: Hypertension dengan Banyak Tindakan

**Input:**
```python
diagnosis = "Hypertension"
tindakan = ["EKG", "Echocardiografi", "Lab Lipid", "Foto Thorax", "Treadmill"]
# Note: Only first 3 used → ["EKG", "Echocardiografi", "Lab Lipid"]
```

**Expected AI Output:**
```python
[
  "Resume Medis",
  "Hasil EKG",
  "Hasil Echocardiografi",
  "Hasil Lab Lipid",
  "Resep Obat Antihipertensi"
]
```

**Analysis:**
- Only first 3 tindakan used (to avoid token overflow)
- AI prioritizes most relevant dokumen (EKG, Echo for heart evaluation)
- Limited to 5 items (enforced by `[:5]` slice)

---

### Scenario 5: CHF Tanpa Tindakan

**Input:**
```python
diagnosis = "Congestive Heart Failure"
tindakan = []  # Kosong
```

**Expected AI Output:**
```python
[
  "Resume Medis",
  "Hasil Lab Darah (fungsi ginjal, elektrolit)",
  "Hasil Foto Thorax",
  "Hasil Echocardiografi",
  "Resep Obat CHF"
]
```

**Analysis:**
- AI generates based on diagnosis alone (no tindakan input)
- Suggests standard investigations for CHF (Lab, Foto Thorax, Echo)
- Provides generic but medically appropriate dokumen list

---

## ✅ Strengths

1. **Contextual Intelligence**
   - AI understands medical context (e.g., Appendektomi → Informed Consent Operasi)
   - Generates diagnosis-specific dokumen (Pneumonia → Foto Thorax, Diabetes → Gula Darah)
   - Adapts to tindakan performed (EKG done → Hasil EKG required)

2. **Consistency & Reliability**
   - Low temperature (0.3) ensures consistent output
   - Max 5 dokumen prevents overwhelming verifikator
   - Has error fallback mechanism

3. **Cost Efficiency**
   - Model: gpt-4o-mini (cheapest OpenAI model)
   - Max tokens: 200 (minimal cost per request)
   - Only first 3 tindakan used (avoids token overflow)

---

## ⚠️ Limitations

1. **No Database Implementation**
   - Currently 100% dependent on AI
   - No standardized dokumen list from database
   - TODO comment for future DB integration (lines 991-997)

2. **Parameter Not Used**
   - `full_analysis` parameter accepted but NOT used in function
   - Could potentially leverage analysis data for better context
   - Wasted parameter passing

3. **Limited Tindakan Context**
   - Only first 3 tindakan used (hardcoded limit)
   - If patient has 10 tindakan, only 3 considered
   - May miss important dokumen for tindakan #4-10

4. **Error Fallback Not Helpful**
   - Returns generic error messages instead of useful defaults
   - Could provide basic dokumen checklist (Resume Medis, Lab, Resep, etc.)
   - Misses opportunity to help when AI unavailable

5. **No JSON Validation Handling**
   - If AI returns non-JSON or malformed JSON → exception
   - No retry mechanism
   - Falls directly to error fallback

---

## 💡 Recommendations for Improvement

### 1. Implement Database Fallback

**Current:**
```python
# 🔹 PRIORITAS 2: Ambil dari DB (belum ada implementasi)
# TODO: Implementasi fetch dari database
```

**Improved:**
```python
# 🔹 PRIORITAS 2: Database Query
if db_pool:
    try:
        async with db_pool.acquire() as conn:
            result = await conn.fetch(
                """
                SELECT dokumen_name, status, keterangan
                FROM dokumen_wajib
                WHERE diagnosis ILIKE $1 OR icd10_code = $2
                ORDER BY priority ASC
                LIMIT 5
                """,
                f"%{diagnosis}%",
                icd10_code
            )
            if result:
                return [row['dokumen_name'] for row in result]
    except Exception as e:
        logger.warning(f"[DOKUMEN_WAJIB] DB query failed: {e}")
```

### 2. Use full_analysis Parameter

**Current:** Parameter accepted but ignored

**Improved:**
```python
# Extract additional context from full_analysis
icd10_code = full_analysis.get("icd10", {}).get("kode_icd", "-")
severity = full_analysis.get("severity", "sedang")

# Add to prompt
prompt = f"""Berikan daftar dokumen wajib untuk klaim BPJS dengan:
- Diagnosis: {diagnosis} ({icd10_code})
- Severity: {severity}
- Tindakan: {tindakan_str}

Format output sebagai JSON array of strings (max 5 dokumen).
"""
```

### 3. Provide Generic Fallback Instead of Errors

**Current:**
```python
return [
    "⚠️ Data dokumen wajib tidak tersedia di database",
    "⚠️ AI tidak dapat menghasilkan daftar dokumen",
    "⚠️ Silakan hubungi admin untuk menambahkan data dokumen wajib"
]
```

**Improved:**
```python
# Generic checklist berdasarkan severity
logger.warning(f"[DOKUMEN_WAJIB] Using generic checklist for {diagnosis}")

severity = full_analysis.get("severity", "sedang")

if severity == "berat" or "operasi" in " ".join(tindakan_list).lower():
    return [
        "Resume Medis",
        "Informed Consent (jika operasi)",
        "Hasil Lab Pra-Operasi",
        "Laporan Operasi",
        "Resep Obat"
    ]
else:
    return [
        "Resume Medis",
        "Hasil Lab/Radiologi",
        "Resep Obat",
        "Surat Rujukan (jika ada)",
        "Catatan Perawatan Harian"
    ]
```

### 4. Add JSON Validation & Retry

```python
# After API call
content = response.choices[0].message.content.strip()

# Handle markdown-wrapped JSON
if content.startswith("```json"):
    content = content.replace("```json", "").replace("```", "").strip()

# Validate JSON format
try:
    if content.startswith("[") and content.endswith("]"):
        dokumen_list = json.loads(content)
        
        # Validate all items are strings
        dokumen_list = [str(item) for item in dokumen_list if item]
        
        logger.info(f"[DOKUMEN_WAJIB] ✓ AI generated {len(dokumen_list)} items")
        return dokumen_list[:5]
    else:
        logger.warning(f"[DOKUMEN_WAJIB] Invalid JSON format: {content[:100]}")
        
except json.JSONDecodeError as e:
    logger.warning(f"[DOKUMEN_WAJIB] JSON parse error: {e}")
```

### 5. Increase Tindakan Limit Based on Token Budget

**Current:** Only 3 tindakan used

**Improved:**
```python
# Calculate token budget
base_prompt_tokens = 150  # Approximate
available_tokens = 200 - base_prompt_tokens

# Estimate tindakan tokens (avg 5 tokens per tindakan name)
max_tindakan = min(len(tindakan_list), available_tokens // 5, 10)

tindakan_str = ", ".join(tindakan_list[:max_tindakan]) if tindakan_list else "tidak ada"

if len(tindakan_list) > max_tindakan:
    logger.info(f"[DOKUMEN_WAJIB] Using {max_tindakan}/{len(tindakan_list)} tindakan")
```

---

## 📈 Usage Statistics (Estimated)

| Metric | Value |
|--------|-------|
| Model | gpt-4o-mini |
| Temperature | 0.3 |
| Max Tokens | 200 |
| Avg Output Items | 4-5 dokumen |
| API Calls per Analysis | 1 |
| Estimated Cost | ~$0.000015 per request |
| Success Rate | ~95% (if AI available) |

---

## 🔗 Related Functions

| Function | Purpose | Relationship |
|----------|---------|--------------|
| `_summarize_cp()` | Generate CP Ringkas | Similar AI generation pattern |
| `_generate_ai_insight()` | Generate Insight AI | Similar AI generation pattern |
| `analyze_lite_single()` | Main analysis function | Calls _generate_dokumen_wajib |

---

## ✅ Conclusion

**What It Does:**
- ✅ Generates contextual checklist of required documents for BPJS claims
- ✅ Uses AI to understand diagnosis-tindakan relationships
- ✅ Provides max 5 most relevant dokumen for verifikator

**How It Works:**
1. Checks OpenAI client availability
2. Prepares medical context (diagnosis + max 3 tindakan)
3. Calls GPT-4o-mini with structured prompt
4. Returns list of dokumen names (or error messages if failed)

**Data Source:**
- **Primary:** AI Generation (GPT-4o-mini)
- **Future:** Database query (reserved, not implemented)
- **Fallback:** Error messages (current behavior when AI fails)

**Current Strengths:**
- Highly contextual medical document suggestions
- Cost-efficient (gpt-4o-mini, 200 tokens max)
- Consistent output (low temperature)

**Improvement Opportunities:**
- Implement database fallback
- Use full_analysis parameter for better context
- Provide generic checklist instead of errors when AI fails
- Increase tindakan limit with dynamic token budgeting
- Add JSON validation and retry mechanism

---

**Generated:** November 16, 2025  
**Source Code:** `core_engine/services/lite_service.py` (lines 944-1003)  
**Test Script:** `core_engine/test_dokumen_generation.py`
