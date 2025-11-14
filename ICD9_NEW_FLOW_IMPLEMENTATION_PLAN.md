# 📋 ICD-9 New Flow Implementation Plan

## 🎯 Tujuan Skema Baru
Implementasi alur ICD-9 yang lebih **user-centric** dan **database-driven** dengan normalisasi AI yang lebih pintar.

---

## 📊 Analisis Kondisi Saat Ini

### 1️⃣ **Komponen yang Ada**

#### A. Database
- ✅ **Tabel `icd9cm_master`** sudah ada dengan struktur:
  ```
  - id: INTEGER
  - code: VARCHAR(10)          # Kode ICD-9 (contoh: "87.44")
  - name: TEXT                 # Nama prosedur WHO (contoh: "Routine chest X-ray")
  - source: VARCHAR(100)       # "ICD9CM_2010"
  - validation_status: VARCHAR # "official"
  - created_at: TIMESTAMP
  ```
- ✅ Total records: **4,626 prosedur**

#### B. File Rules (JSON)
- `core_engine/rules/icd9_mapping.json` → Mapping manual (procedure name → code)
- `core_engine/rules/icd9_indonesian_aliases.json` → Alias Indonesia ke English WHO

#### C. Service Layer
- `core_engine/services/icd9_mapping_service.py` → Service saat ini
  - Load JSON mapping
  - Fuzzy matching dengan RapidFuzz
  - Validasi kode ICD-9
  - **❌ TIDAK menggunakan database `icd9cm_master`**

#### D. Integration Points
- `analyze_diagnosis_service.py` → Menggunakan `map_icd9_smart()` untuk mapping
- `lite_endpoints.py` → Endpoint analyze single/batch
- Frontend (web) → Form input `procedure` field

---

## 🆕 Skema Alur Baru (SIMPLIFIED)

### **Flow Diagram**

```
┌─────────────────────────────────────────────────────────────────┐
│ USER INPUT / PARSING                                             │
│ "x-ray thorax" atau "rontgen dada"                               │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1️⃣ EXACT SEARCH (Database icd9cm_master)                       │
│ Query: SELECT * FROM icd9cm_master                               │
│        WHERE LOWER(name) = LOWER('{input}')                      │
│ Hasil: FOUND / NOT FOUND                                         │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─── FOUND (Exact Match) ──────────────────┐
             │                                          │
             │                                          ▼
             │                              ┌────────────────────────┐
             │                              │ ✅ LANGSUNG RETURN    │
             │                              │ code: "87.44"          │
             │                              │ name: "Routine chest..." │
             │                              │ confidence: 100%       │
             │                              │ ❌ NO MODAL           │
             │                              │ ❌ NO AI CALL         │
             │                              └────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2️⃣ AI NORMALIZATION (OpenAI GPT)                               │
│ Prompt: "Given input 'x-ray thorax', provide ICD-9 procedure    │
│          names that match WHO ICD-9-CM terminology.             │
│          Return 3-5 specific procedure names."                   │
│                                                                  │
│ Response (JSON):                                                 │
│ {                                                                │
│   "suggestions": [                                               │
│     "Routine chest X-ray",                                       │
│     "Other chest X-ray",                                         │
│     "Bronchography"                                              │
│   ]                                                              │
│ }                                                                │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3️⃣ VALIDATE AI SUGGESTIONS (Database Lookup)                   │
│ For each AI suggestion:                                          │
│   SELECT * FROM icd9cm_master                                    │
│   WHERE LOWER(name) = LOWER('{ai_suggestion}')                   │
│                                                                  │
│ Filter: Keep only VALID matches (found in DB)                   │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─── FOUND (1 validated match) ────────┐
             │                                      │
             │                                      ▼
             │                          ┌────────────────────────┐
             │                          │ ✅ RETURN SINGLE      │
             │                          │ confidence: 95%        │
             │                          │ ❌ NO MODAL           │
             │                          └────────────────────────┘
             │
             ├─── FOUND (Multiple validated) ───────┐
             │                                      │
             │                                      ▼
             │                          ┌────────────────────────┐
             │                          │ ✅ RETURN SUGGESTIONS │
             │                          │ [                      │
             │                          │   {code, name},        │
             │                          │   {code, name}         │
             │                          │ ]                      │
             │                          │ ✅ SHOW MODAL         │
             │                          └────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4️⃣ NOT FOUND / NO VALID MATCH                                  │
│ Return: {                                                        │
│   "code": "-",                                                   │
│   "name": "{original_input}",                                    │
│   "valid": false,                                                │
│   "message": "No matching ICD-9 procedure found"                 │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘
```

**⚡ Perubahan Utama:**
- ❌ **HAPUS Fuzzy Search** (tidak perlu, langsung ke AI)
- ❌ **HAPUS JSON files** (icd9_mapping.json, indonesian_aliases.json)
- ✅ **Hanya 2 langkah:** Exact DB Search → AI Normalization
- ✅ **AI prompt sangat spesifik** untuk akurasi tinggi dan response cepat

---

## 🏗️ Implementasi Teknis

### **1️⃣ Service Layer Baru (SIMPLIFIED)**

#### File: `core_engine/services/icd9_smart_service.py` (NEW - STANDALONE)

**Responsibilities:**
- ✅ Database-first approach (exact match only)
- ✅ AI normalization jika tidak exact match
- ✅ Validate AI suggestions dengan database
- ❌ NO fuzzy matching
- ❌ NO JSON files dependency

**Functions:**

```python
# 1. Exact Search (Database Only)
def exact_search_icd9(procedure_input: str) -> Optional[Dict]:
    """
    Search exact di icd9cm_master dengan case-insensitive.
    
    Args:
        procedure_input: Input dari user (bisa Indonesia/English)
    
    Returns:
        {
            "code": "87.44",
            "name": "Routine chest X-ray",
            "source": "database",
            "valid": True,
            "confidence": 100
        } atau None jika tidak ditemukan
    """

# 2. AI Normalization (OpenAI GPT)
def normalize_procedure_with_ai(procedure_input: str) -> List[str]:
    """
    Normalize input ke WHO ICD-9-CM terminology dengan AI.
    
    OPTIMIZED PROMPT: Fast, accurate, specific.
    
    Args:
        procedure_input: Input dari user (bisa kurang lengkap/Indonesia)
    
    Returns:
        List of normalized WHO procedure names (3-5 items)
        Example: ["Routine chest X-ray", "Other chest X-ray"]
    """

# 3. Validate AI Suggestions (Database Lookup)
def validate_ai_suggestions(ai_suggestions: List[str]) -> List[Dict]:
    """
    Validate setiap AI suggestion dengan exact search di database.
    
    Args:
        ai_suggestions: List procedure names dari AI
    
    Returns:
        List of valid matches dengan metadata:
        [
            {"code": "87.44", "name": "Routine chest X-ray", ...},
            {"code": "87.49", "name": "Other chest X-ray", ...}
        ]
    """

# 4. Main Entry Point
def lookup_icd9_procedure(procedure_input: str) -> Dict:
    """
    Main orchestrator - SIMPLE FLOW.
    
    Flow:
        1. Exact search di database
        2. Jika tidak ada → AI normalization
        3. Validate AI suggestions
        4. Return results
    
    Args:
        procedure_input: Input dari user
    
    Returns:
        {
            "status": "success" | "suggestions" | "not_found",
            "result": {...} atau None,
            "suggestions": [...] atau [],
            "needs_selection": True/False
        }
    """
```

**⚡ Perbedaan dari Design Sebelumnya:**
- ❌ NO `fuzzy_search_icd9()` function
- ❌ NO dependency ke RapidFuzz library
- ❌ NO import dari icd9_mapping_service.py
- ✅ PURE: Database + AI only
- ✅ FAST: Exact match atau langsung AI (no fuzzy iteration)

---

### **2️⃣ Endpoint API Baru**

#### File: `core_engine/lite_endpoints.py` (MODIFY)

**New Endpoint:**

```python
@app.post("/api/lite/icd9/suggestions")
def endpoint_get_icd9_suggestions(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/icd9/suggestions
    
    Request:
    {
        "procedure_input": "x-ray thorax"
    }
    
    Response:
    {
        "status": "success",
        "result_type": "single" | "multiple" | "ai_normalized",
        "suggestions": [
            {
                "code": "87.44",
                "name": "Routine chest X-ray",
                "name_indonesia": "Rontgen Thorax Rutin",
                "confidence": 100,
                "source": "exact_match" | "fuzzy_match" | "ai_validated"
            },
            ...
        ],
        "auto_select": true | false  // true jika hanya 1 hasil dengan confidence tinggi
    }
    """
```

**Modified Endpoint:**

```python
@app.post("/api/lite/analyze/single")
def endpoint_analyze_single(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    MODIFICATION:
    - Tidak langsung mapping ICD-9
    - Return tindakan dengan flag "needs_icd9_selection"
    - Frontend akan call /api/lite/icd9/suggestions jika flag true
    """
```

---

### **3️⃣ Frontend Changes**

#### File: `web/src/components/InputPanel.tsx` (MODIFY)

**New Feature: ICD-9 Suggestion Modal**

```tsx
// State management
const [icd9Suggestions, setIcd9Suggestions] = useState<ICD9Suggestion[]>([]);
const [showIcd9Modal, setShowIcd9Modal] = useState(false);
const [pendingTindakanIndex, setPendingTindakanIndex] = useState<number | null>(null);

// Handler untuk Generate AI button
const handleGenerateAI = async () => {
  // 1. Call analyze endpoint
  const result = await analyzeAPI(diagnosis, tindakan, obat);
  
  // 2. Check jika ada tindakan yang butuh ICD-9 selection
  result.tindakan.forEach((t, idx) => {
    if (t.needs_icd9_selection) {
      // 3. Call ICD-9 suggestions endpoint
      const suggestions = await getICD9Suggestions(t.nama);
      
      if (suggestions.auto_select) {
        // Langsung assign jika hanya 1 hasil
        t.icd9_code = suggestions[0].code;
        t.icd9_name = suggestions[0].name;
      } else {
        // Show modal untuk multiple suggestions
        setIcd9Suggestions(suggestions);
        setPendingTindakanIndex(idx);
        setShowIcd9Modal(true);
      }
    }
  });
};

// Modal component
<ICD9SuggestionModal
  open={showIcd9Modal}
  suggestions={icd9Suggestions}
  onSelect={(selected) => {
    // Update tindakan dengan pilihan user
    updateTindakanWithICD9(pendingTindakanIndex, selected);
    setShowIcd9Modal(false);
  }}
  onCancel={() => setShowIcd9Modal(false)}
/>
```

---

### **4️⃣ Database Query Optimization**

#### Indexing untuk Performance

```sql
-- Create index untuk faster search
CREATE INDEX idx_icd9cm_name_lower ON icd9cm_master(LOWER(name));
CREATE INDEX idx_icd9cm_code ON icd9cm_master(code);

-- Full-text search index (optional untuk advanced search)
CREATE INDEX idx_icd9cm_name_fulltext ON icd9cm_master USING gin(to_tsvector('english', name));
```

---

### **5️⃣ AI Prompt Engineering (OPTIMIZED FOR SPEED & ACCURACY)**

#### OpenAI Prompt untuk Normalisasi

```python
PROMPT_ICD9_NORMALIZATION = """
You are a medical coding expert. Normalize the procedure to ICD-9-CM terminology.

Input: "{procedure_input}"

Rules:
1. Return 3-5 ICD-9-CM WHO procedure names (English)
2. Handle Indonesian terms (rontgen=X-ray, suntik=injection, etc)
3. If input vague (e.g., "x-ray" only), suggest common body parts
4. Use EXACT WHO ICD-9-CM procedure names
5. Order by likelihood (most common first)

Format (JSON only):
{{
  "procedures": [
    "Routine chest X-ray",
    "Other chest X-ray",
    "Bronchography"
  ]
}}

IMPORTANT: Return ONLY valid JSON. No explanation needed.
"""
```

**⚡ Optimizations:**
- ✅ **Shorter prompt** (reduced tokens = faster response)
- ✅ **JSON-only output** (no verbose explanation)
- ✅ **Clear rules** (no ambiguity)
- ✅ **Direct format** (easy to parse)
- ✅ **Performance target:** <2 seconds response time

---

## 🔄 Migration Strategy

### **Phase 1: Service Creation** (Day 1)
1. ✅ Create `icd9_smart_service.py` (STANDALONE)
   - `exact_search_icd9()` - Database exact match
   - `normalize_procedure_with_ai()` - AI normalization
   - `validate_ai_suggestions()` - Validate AI output
   - `lookup_icd9_procedure()` - Main orchestrator
2. ✅ Add database index (jika belum ada):
   ```sql
   CREATE INDEX IF NOT EXISTS idx_icd9cm_name_lower 
   ON icd9cm_master(LOWER(name));
   ```
3. ✅ Unit testing (test_icd9_smart_service.py)

### **Phase 2: Integration** (Day 2)
1. ✅ Add endpoint di `lite_endpoints.py`:
   - `POST /api/lite/icd9/suggestions`
2. ✅ Add route di `main.py`
3. ✅ Modify `analyze_diagnosis_service.py`:
   - Replace: `from services.icd9_mapping_service import map_icd9_smart`
   - With: `from services.icd9_smart_service import lookup_icd9_procedure`
   - Update logic untuk handle suggestions
4. ✅ API testing dengan Postman/curl

### **Phase 3: Cleanup** (Day 3)
1. ✅ Delete old files:
   - `icd9_mapping_service.py`
   - `rules/icd9_mapping.json`
   - `rules/icd9_indonesian_aliases.json`
2. ✅ Update `requirements.txt` (hapus rapidfuzz jika tidak dipakai di tempat lain)
3. ✅ Update documentation
4. ✅ Final testing

### **Phase 4: Frontend** (SKIPPED - Teman Anda Handle)
1. ⚠️ Modal component → Frontend team
2. ⚠️ Integration → Frontend team
3. ⚠️ E2E testing → Frontend team

**Total Backend Work: 3 Days** (simplified from 5-6 days)

---

## 📦 Files to Create/Modify

### **NEW FILES:**
1. ✅ `core_engine/services/icd9_smart_service.py` → **STANDALONE** service (no dependencies)
2. ✅ `core_engine/test_icd9_smart_service.py` → Unit tests
3. ⚠️ Frontend files → **SKIP** (dikerjakan teman Anda)

### **MODIFIED FILES:**
1. ✅ `core_engine/services/analyze_diagnosis_service.py` → Replace ICD-9 logic
2. ✅ `core_engine/lite_endpoints.py` → Add new endpoint `/api/lite/icd9/suggestions`
3. ✅ `core_engine/main.py` → Add route untuk endpoint baru
4. ⚠️ Frontend files → **SKIP** (bukan scope kita)

### **FILES TO DELETE:**
1. ❌ `core_engine/services/icd9_mapping_service.py` → **HAPUS** (tidak digunakan lagi)
2. ❌ `core_engine/rules/icd9_mapping.json` → **HAPUS** (diganti database)
3. ❌ `core_engine/rules/icd9_indonesian_aliases.json` → **HAPUS** (AI handle normalisasi)

**Note:** No backward compatibility needed karena service baru completely standalone.

---

## 🧪 Testing Scenarios

### **Test Cases:**

#### 1. **Exact Match (Single Result)**
```
Input: "Routine chest X-ray"
Expected: 
  - No modal
  - Direct assignment: code="87.44"
  - Confidence: 100%
```

#### 2. **Fuzzy Match (Single High Confidence)**
```
Input: "chest xray"
Expected:
  - No modal
  - Fuzzy match: code="87.44"
  - Confidence: 90%
```

#### 3. **Multiple Matches**
```
Input: "x-ray thorax"
Expected:
  - Show modal with 3-5 suggestions
  - User selects "Routine chest X-ray (87.44)"
  - System assigns selected code
```

#### 4. **AI Normalization**
```
Input: "rontgen dada"
Expected:
  - No database match
  - AI normalizes to "Routine chest X-ray"
  - Validate against database
  - Show modal with AI suggestions
```

#### 5. **Not Found**
```
Input: "random procedure xyz"
Expected:
  - No database match
  - AI cannot normalize
  - Return empty with suggestion to rephrase
```

---

## 📊 Success Metrics

1. **Accuracy:** ≥95% untuk exact match
2. **AI Call Reduction:** 70% (hanya call jika database search gagal)
3. **User Experience:** Modal hanya muncul jika perlu (ambiguous cases)
4. **Performance:** Response time <500ms untuk database search
5. **Cost Reduction:** Hemat OpenAI API calls dengan database-first approach

---

## 🚨 Risk Mitigation

### **Risk 1: Database Performance**
- **Mitigation:** Add proper indexes, implement caching
- **Fallback:** Use JSON file jika database slow

### **Risk 2: AI Hallucination**
- **Mitigation:** Always validate AI suggestions dengan database
- **Fallback:** Reject suggestions yang tidak ada di database

### **Risk 3: User Experience**
- **Mitigation:** Show modal hanya jika truly ambiguous
- **Fallback:** Allow "skip" option di modal

---

## 📝 Next Steps

1. **Review** dokumen ini dengan tim
2. **Approval** untuk proceed implementation
3. **Create** GitHub issues untuk setiap phase
4. **Start** Phase 1 development

---

## 📞 Questions & Clarifications

### **Q1:** Apakah Indonesian aliases perlu dimigrate ke database?
**A:** Optional. Bisa tetap di JSON atau create table `icd9_aliases` untuk better management.

### **Q2:** Bagaimana handle case ketika user input already contains code (e.g., "Rontgen Thorax (87.44)")?
**A:** Extract code dengan regex, validate di database, skip AI normalization.

### **Q3:** Apakah perlu cache AI normalization results?
**A:** YES. Create cache table untuk avoid duplicate AI calls.

### **Q4:** Bagaimana backward compatibility untuk API yang sudah ada?
**A:** Add feature flag `use_new_icd9_flow=true/false` di request.

---

**Status:** 📋 PLANNING PHASE - AWAITING APPROVAL

**Created:** 2025-11-14  
**Last Updated:** 2025-11-14  
**Author:** GitHub Copilot  
**Reviewer:** [Pending]
