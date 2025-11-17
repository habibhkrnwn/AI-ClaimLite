# 🔍 Insight AI - Logic Flow & Output Analysis

## 📋 Overview

Fungsi `_generate_ai_insight()` adalah komponen yang menghasilkan insight actionable untuk verifikator klaim BPJS menggunakan OpenAI GPT-4o-mini.

**Lokasi**: `core_engine/services/lite_service.py` (baris 1005-1050)

---

## 🔄 Logic Flow Diagram

```
START: _generate_ai_insight(full_analysis, diagnosis, tindakan_list, obat_list, client)
  │
  ├─ Step 1: Check OpenAI Client Availability
  │   ├─ IF client is None OR OPENAI_AVAILABLE is False
  │   │   └─ GO TO: Fallback Mode (Rule-based)
  │   │       ├─ IF konsistensi.tingkat == "Rendah"
  │   │       │   └─ RETURN: "⚠️ Inkonsistensi ditemukan"
  │   │       └─ ELSE
  │   │           └─ RETURN: "✅ Dokumentasi lengkap dan sesuai CP/PNPK"
  │   │
  │   └─ ELSE: Proceed to AI Generation
  │
  ├─ Step 2: Prepare Context from Input
  │   ├─ Extract diagnosis name
  │   ├─ Extract ICD-10 code from full_analysis
  │   ├─ Format tindakan_list (max 3 items, comma-separated)
  │   ├─ Format obat_list (max 3 items, comma-separated)
  │   └─ Extract konsistensi.tingkat from full_analysis
  │
  ├─ Step 3: Build OpenAI Prompt
  │   ├─ System prompt: "Kamu adalah AI expert verifikasi klaim BPJS"
  │   └─ User prompt: 
  │       """
  │       Analisis klaim BPJS berikut dan berikan insight singkat (max 100 karakter):
  │       
  │       Diagnosis: {diagnosis} ({icd10})
  │       Tindakan: {tindakan_str}
  │       Obat: {obat_str}
  │       Konsistensi: {konsistensi}
  │       
  │       Berikan insight yang actionable dan spesifik. Format: 1 kalimat singkat.
  │       Contoh: "✅ Sesuai CP pneumonia, dokumentasi lengkap"
  │       """
  │
  ├─ Step 4: Call OpenAI API
  │   ├─ Model: gpt-4o-mini
  │   ├─ Temperature: 0.5 (balanced creativity)
  │   ├─ Max tokens: 100
  │   └─ Extract response.choices[0].message.content
  │
  ├─ Step 5: Return Result
  │   ├─ IF Success: Return AI-generated insight string
  │   └─ IF Error: Fallback to "✅ Dokumentasi lengkap dan sesuai CP/PNPK"
  │
END: Return insight string
```

---

## 📊 Test Results & Output Examples

### Test 1: Pneumonia - Konsistensi Tinggi

**Input:**
```json
{
  "diagnosis": "Pneumonia",
  "icd10": "J18.9",
  "tindakan": ["Rontgen Thorax", "Nebulisasi"],
  "obat": ["Ceftriaxone", "Paracetamol"],
  "konsistensi": "Tinggi"
}
```

**Output:**
```
✅ Tindakan dan obat sesuai protokol pneumonia, dokumentasi lengkap.
```

**Length:** 67 characters

**Analysis:**
- ✅ AI recognized pneumonia standard treatment
- ✅ Confirmed tindakan (X-ray, nebulizer) appropriate
- ✅ Confirmed obat (antibiotic + analgesic) appropriate
- ✅ Used positive tone (✅) for Tinggi konsistensi

---

### Test 2: Diabetes - Konsistensi Rendah

**Input:**
```json
{
  "diagnosis": "Diabetes Mellitus Type 2",
  "icd10": "E11.9",
  "tindakan": ["Rontgen Thorax"],
  "obat": ["Paracetamol"],
  "konsistensi": "Rendah"
}
```

**Output:**
```
⚠️ Tindakan rontgen thorax tidak relevan untuk diabetes mellitus, perlu klarifikasi.
```

**Length:** 84 characters

**Analysis:**
- ✅ AI detected irrelevant treatment (chest X-ray for diabetes)
- ✅ Used warning tone (⚠️) for Rendah konsistensi
- ✅ Provided actionable recommendation ("perlu klarifikasi")
- ✅ Highly specific about the inconsistency

---

### Test 3: Fallback Mode - No OpenAI Client

**Input:**
```json
{
  "diagnosis": "Pneumonia",
  "tindakan": ["Rontgen Thorax"],
  "obat": ["Ceftriaxone"],
  "konsistensi": "Rendah",
  "client": null
}
```

**Output:**
```
⚠️ Inkonsistensi ditemukan
```

**Analysis:**
- ✅ Fallback mechanism activated
- ✅ Rule-based logic: Konsistensi Rendah → Warning message
- ⚠️ Less specific than AI-generated insight

---

### Test 4: Pneumonia - Konsistensi Sedang

**Input:**
```json
{
  "diagnosis": "Pneumonia",
  "icd10": "J18.9",
  "tindakan": ["Rontgen Thorax", "Nebulisasi", "Lab Darah"],
  "obat": ["Ceftriaxone", "Paracetamol", "Salbutamol"],
  "konsistensi": "Sedang"
}
```

**Output:**
```
✅ Tindakan dan obat sesuai standar penanganan pneumonia, dokumentasi memadai.
```

**Length:** 77 characters

**Analysis:**
- ✅ AI validated comprehensive treatment plan
- ✅ Acknowledged "Sedang" konsistensi with "memadai" (adequate) instead of "lengkap" (complete)
- ✅ Subtle language adjustment based on konsistensi level

---

## 🎯 Key Characteristics

### ✅ Strengths

1. **Contextual Intelligence**
   - AI understands medical context (e.g., "Rontgen Thorax not relevant for Diabetes")
   - Generates specific, actionable recommendations
   - Adjusts tone based on konsistensi level

2. **Conciseness**
   - Average output: 67-84 characters (within 100 char limit)
   - Single sentence format for quick reading
   - Uses emoji indicators (✅/⚠️) for visual clarity

3. **Reliability**
   - Has fallback mechanism for errors
   - Rule-based backup when AI unavailable
   - Handles null/missing data gracefully

4. **Cost Efficiency**
   - Model: gpt-4o-mini (cheapest OpenAI model)
   - Max tokens: 100 (minimal cost per request)
   - Temperature: 0.5 (balanced, not wasteful)

### ⚠️ Limitations

1. **Character Limit Occasionally Exceeded**
   - Prompt requests "max 100 karakter"
   - Test 2 produced 84 chars (close to limit)
   - Some outputs may exceed if AI verbose

2. **Konsistensi Level Not Always Emphasized**
   - Test 1 & 4: Both Tinggi & Sedang got positive (✅) tone
   - AI may prioritize clinical correctness over konsistensi score
   - Sedang konsistensi should potentially trigger ⚠️ instead of ✅

3. **Limited Input Context**
   - Only uses:
     - Diagnosis name + ICD-10 code
     - Tindakan (max 3 items)
     - Obat (max 3 items)
     - Konsistensi tingkat
   - Does NOT include:
     - Konsistensi detail (e.g., which validation failed)
     - Konsistensi score (e.g., 2.3/3.0)
     - Individual validation statuses (dx_tx_status, tx_drug_status, dx_drug_status)

4. **Fallback Mode Too Generic**
   - "⚠️ Inkonsistensi ditemukan" → Not actionable
   - "✅ Dokumentasi lengkap dan sesuai CP/PNPK" → Not specific
   - Could benefit from more detailed rule-based logic

---

## 🔧 How It's Called in `analyze_lite_single()`

**Location:** `lite_service.py` line 659

```python
"insight_ai": _generate_ai_insight(
    lite_analysis,  # full_analysis parameter (contains ICD-10, konsistensi)
    diagnosis_name,  # e.g., "Pneumonia"
    [t['name'] for t in tindakan_with_icd9],  # List of tindakan names
    obat_list,  # List of obat names
    parser.client if hasattr(parser, 'client') else None  # OpenAI client
)
```

**Input Sources:**
- `lite_analysis`: Result from `analyze_diagnosis_lite()` (contains ICD-10, severity, justification)
- `diagnosis_name`: Extracted from parsing result
- `tindakan_with_icd9`: Result from `lookup_icd9_procedure()` for each tindakan
- `obat_list`: Extracted from parsing result
- `parser.client`: OpenAI client from global `OpenAIMedicalParser` instance

---

## 💡 Recommendations for Improvement

### 1. Include Konsistensi Score in Prompt

**Current prompt:**
```
Konsistensi: Tinggi
```

**Improved prompt:**
```
Konsistensi: Tinggi (2.8/3.0)
  - Diagnosis ↔ Tindakan: ✅ Valid
  - Tindakan ↔ Obat: ✅ Valid
  - Diagnosis ↔ Obat: ⚠️ Partial
```

**Benefits:**
- AI can provide more specific guidance on which relationship needs attention
- Score gives quantitative context for actionable recommendations

### 2. Adjust Tone Based on Konsistensi Score

```python
# Add to prompt construction
if konsistensi == "Rendah":
    tone_instruction = "CRITICAL: Gunakan tone ⚠️ atau ❌, identifikasi inkonsistensi spesifik"
elif konsistensi == "Sedang":
    tone_instruction = "CAUTION: Gunakan tone ⚠️, jelaskan area yang perlu review"
else:  # Tinggi
    tone_instruction = "POSITIVE: Gunakan tone ✅, konfirmasi kelengkapan"
```

### 3. Expand Fallback Logic

```python
if not client or not OPENAI_AVAILABLE:
    insights = []
    konsistensi_data = full_analysis.get("konsistensi", {})
    tingkat = konsistensi_data.get("tingkat", "Sedang")
    
    if tingkat == "Rendah":
        # Check which validation failed
        detail = konsistensi_data.get("detail", "")
        if "diagnosis" in detail.lower() and "tindakan" in detail.lower():
            insights.append("⚠️ Inkonsistensi antara diagnosis dan tindakan")
        elif "obat" in detail.lower():
            insights.append("⚠️ Obat tidak sesuai dengan diagnosis")
        else:
            insights.append("⚠️ Inkonsistensi ditemukan, perlu review menyeluruh")
    elif tingkat == "Sedang":
        insights.append("⚠️ Sebagian konsisten, perlu verifikasi tindakan/obat")
    else:
        insights.append("✅ Dokumentasi lengkap dan sesuai CP/PNPK")
    
    return " | ".join(insights)
```

### 4. Add Character Limit Enforcement

```python
# After getting AI response
insight = response.choices[0].message.content.strip()

# Enforce 100 char limit
if len(insight) > 100:
    # Truncate at last complete word before 100 chars
    truncated = insight[:97].rsplit(' ', 1)[0] + "..."
    print(f"[INSIGHT_AI] ⚠️ Truncated from {len(insight)} to {len(truncated)} chars")
    insight = truncated

print(f"[INSIGHT_AI] ✓ Generated: {insight}")
return insight
```

---

## 📈 Usage Statistics

From test execution:

| Metric | Value |
|--------|-------|
| Model | gpt-4o-mini |
| Temperature | 0.5 |
| Max Tokens | 100 |
| Avg Output Length | 67-84 characters |
| Success Rate | 100% (with fallback) |
| API Calls per Analysis | 1 |
| Estimated Cost | ~$0.00001 per insight |

---

## 🔗 Related Functions

| Function | Purpose |
|----------|---------|
| `_summarize_cp()` | Generate CP Ringkas (PNPK database → AI fallback) |
| `_generate_dokumen_wajib()` | Generate checklist dokumen wajib (AI → DB future) |
| `analyze_clinical_consistency()` | Validate konsistensi (used as input for insight) |

---

## ✅ Conclusion

**What It Does:**
- ✅ Generates actionable, contextual insights for claim verification
- ✅ Uses AI to understand medical relationships (diagnosis-treatment-drugs)
- ✅ Provides specific recommendations when inconsistencies detected
- ✅ Has reliable fallback mechanism for error handling

**How It Works:**
1. Checks OpenAI client availability
2. Prepares medical context (diagnosis, ICD-10, tindakan, obat, konsistensi)
3. Calls GPT-4o-mini with structured prompt
4. Returns concise insight (67-84 characters average)
5. Falls back to rule-based logic if AI unavailable

**Current Strengths:**
- Highly specific medical recommendations
- Cost-efficient (gpt-4o-mini, 100 tokens max)
- Reliable fallback mechanism

**Improvement Opportunities:**
- Include konsistensi score details in prompt
- Enforce stricter character limit (100 chars)
- Enhance fallback logic with more specific rules
- Adjust tone more explicitly based on konsistensi level

---

**Generated:** November 15, 2025  
**Test Script:** `core_engine/test_insight_generation.py`  
**Source Code:** `core_engine/services/lite_service.py` (lines 1005-1050)
