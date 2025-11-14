# 🎯 PLAN IMPLEMENTASI ICD-10 SMART LOOKUP
# Version: 1.0
# Date: 2025-11-14
# Status: PLANNING PHASE

## 📊 KONDISI EXISTING

### Database:
- ✅ Tabel `icd10_master` sudah ada
- ✅ Total records: **18,543 kode ICD-10**
- ✅ Struktur kolom:
  ```
  - id (INTEGER, PRIMARY KEY)
  - code (VARCHAR(10)) → "J18.9"
  - name (TEXT) → "Pneumonia, unspecified"
  - source (VARCHAR(100)) → "ICD10_2010"
  - validation_status (VARCHAR(50)) → "official"
  - created_at (TIMESTAMP)
  ```

### Catatan Penting:
- ❌ **TIDAK ADA** kolom `category`, `parent_code`, `type`, `level`
- ❌ **TIDAK ADA** hierarki subcategory di struktur tabel
- ✅ Data sudah lengkap (18K+ records)
- ❌ Fuzzy search **TIDAK DIGUNAKAN** (sesuai request user)

---

## 🎯 KONSEP ALUR (User Requirements)

```
┌─────────────────────────────────────────────────────┐
│ 1. INPUT USER (dari UI / parsing)                  │
│    Contoh: "paru2 basah", "Pneumonia", "J18.9"     │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│ 2. NORMALISASI KE TERMINOLOGI MEDIS (AI)           │
│    - Jika input TIDAK ada di icd10_master          │
│    - OpenAI: "paru2 basah" → "Pneumonia"           │
│    - Skip jika sudah match dengan database         │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│ 3. TEKAN TOMBOL "GENERATE AI"                      │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
      ┌──────────┴──────────┐
      │                     │
   INPUT MATCH         INPUT TIDAK MATCH
   DI DATABASE         DI DATABASE
      │                     │
      ▼                     ▼
 SKIP MODAL          TAMPILKAN MODAL
 (langsung ke       SUGGESTION ICD-10
  subcategory)       "Apakah maksud Anda?"
      │                     │
      │              ┌──────┴───────┐
      │              │ USER PILIH   │
      │              │ SUGGESTION   │
      │              └──────┬───────┘
      │                     │
      └──────────┬──────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│ 4. TAMPILKAN SUBCATEGORY (TURUNAN)                 │
│    J18 → Pneumonia, unspecified organism           │
│      ├─ J18.0 Bronchopneumonia, unspecified        │
│      ├─ J18.1 Lobar pneumonia, unspecified         │
│      ├─ J18.2 Hypostatic pneumonia                 │
│      ├─ J18.8 Other pneumonia                      │
│      └─ J18.9 Pneumonia, unspecified               │
└─────────────────────────────────────────────────────┘
```

---

## 🏗️ ARSITEKTUR IMPLEMENTASI

### **Layer 1: Database Query (PostgreSQL)**

**Fungsi:** Exact match di database tanpa fuzzy search

**Query Strategy:**
```sql
-- Strategy 1: Exact code match
SELECT * FROM icd10_master 
WHERE UPPER(code) = UPPER(:input)
LIMIT 1;

-- Strategy 2: Exact name match (case-insensitive)
SELECT * FROM icd10_master 
WHERE LOWER(name) = LOWER(:input)
LIMIT 10;

-- Strategy 3: Partial name match (ILIKE)
SELECT * FROM icd10_master 
WHERE name ILIKE '%' || :input || '%'
ORDER BY 
  CASE 
    WHEN name ILIKE :input || '%' THEN 1  -- Start with input
    WHEN name ILIKE '%' || :input THEN 2  -- End with input
    ELSE 3                                 -- Contains input
  END,
  LENGTH(name) ASC  -- Shorter names first
LIMIT 10;
```

**Performance Optimization:**
```sql
-- Create indexes (jika belum ada)
CREATE INDEX IF NOT EXISTS idx_icd10_code_upper 
  ON icd10_master (UPPER(code));

CREATE INDEX IF NOT EXISTS idx_icd10_name_lower 
  ON icd10_master (LOWER(name));

CREATE INDEX IF NOT EXISTS idx_icd10_name_pattern 
  ON icd10_master (name text_pattern_ops);
```

---

### **Layer 2: AI Normalization (OpenAI GPT)**

**Kapan digunakan:**
- Input user TIDAK ditemukan di database (exact/partial match gagal)
- Input dalam bahasa Indonesia / istilah awam
- Input tidak jelas / typo

**Prompt Strategy:**

```python
PROMPT_TEMPLATE = """
You are a medical coding expert specializing in ICD-10 WHO classification.

TASK: Normalize user input to standard ICD-10 medical terminology.

INPUT: "{user_input}"

RULES:
1. If input is informal Indonesian term, translate to formal medical English
2. If input is already formal medical term, keep it
3. Return the MOST SPECIFIC diagnosis name that matches ICD-10
4. Use WHO standard terminology (not Indonesian)

EXAMPLES:
- "paru2 basah" → "Pneumonia, unspecified organism"
- "demam berdarah" → "Dengue haemorrhagic fever"
- "stroke" → "Cerebrovascular disease, unspecified"
- "Pneumonia" → "Pneumonia, unspecified organism"

OUTPUT (JSON):
{{
  "normalized_term": "ICD-10 standard medical term in English",
  "confidence": 85,
  "explanation": "Brief reason why this term was chosen (1 sentence)"
}}

IMPORTANT: Output must be VALID JSON only, no markdown.
"""
```

**Model Configuration:**
- Model: `gpt-4o-mini` (balance accuracy & cost)
- Temperature: `0.2` (low for consistency)
- Max tokens: `150` (short response)
- Response format: `json_object`

**Cost Estimation:**
- Per request: ~100 tokens input + 100 tokens output = 200 tokens
- Price: ~$0.0001 per request (GPT-4o-mini)
- Monthly (1000 users × 2 requests/day): $6/month

---

### **Layer 3: Subcategory Extraction (Pattern Matching)**

**Problem:** Tabel tidak punya kolom `parent_code`, `category`, atau `type`

**Solution:** Extract dari pattern kode ICD-10

**ICD-10 Code Structure:**
```
J18.9
│││ │
││└─── Sub-classification (3rd character)
││
│└──── Category (2nd character)
│
└───── Chapter (1st character)

Pattern:
- J18     → Category (parent)
- J18.0   → Subcategory (child of J18)
- J18.1   → Subcategory (child of J18)
- J18.9   → Subcategory (child of J18)
```

**Extraction Logic:**

```python
def extract_category_from_code(code: str) -> str:
    """
    Extract category dari kode ICD-10
    J18.9 → J18
    A90 → A90 (no subcategory)
    """
    if '.' in code:
        return code.split('.')[0]
    return code

def get_subcategories(selected_code: str) -> dict:
    """
    Get all subcategories dari selected code
    
    Flow:
    1. Extract category (J18.9 → J18)
    2. Query semua kode yang dimulai dengan category
    3. Group: parent + children
    """
    category = extract_category_from_code(selected_code)
    
    # Query database
    query = """
    SELECT code, name 
    FROM icd10_master 
    WHERE code LIKE :pattern
    ORDER BY code
    """
    # pattern: "J18%" untuk J18, J18.0, J18.1, dst
    
    # Group results
    parent = None
    children = []
    
    for row in results:
        if row.code == category:
            parent = row
        elif row.code.startswith(category + '.'):
            children.append(row)
    
    return {
        "parent": parent,
        "children": children
    }
```

**Tree Visualization:**
```
J18 → Pneumonia, unspecified organism
  ├─ J18.0 Bronchopneumonia, unspecified
  ├─ J18.1 Lobar pneumonia, unspecified
  ├─ J18.2 Hypostatic pneumonia
  ├─ J18.8 Other pneumonia
  └─ J18.9 Pneumonia, unspecified
```

---

## 🔄 FLOW LOGIC (Decision Tree)

```python
def smart_icd10_lookup(user_input: str) -> dict:
    """
    Main orchestrator untuk ICD-10 smart lookup
    """
    
    # ===== STEP 1: Database Exact Match =====
    exact_match = db_search_exact(user_input)
    
    if exact_match:
        # DIRECT FLOW: Skip modal, langsung subcategory
        category = extract_category_from_code(exact_match.code)
        subcategories = get_subcategories(category)
        
        return {
            "flow": "direct",
            "requires_modal": False,
            "selected_code": exact_match.code,
            "selected_name": exact_match.name,
            "subcategories": subcategories,
            "ai_used": False
        }
    
    # ===== STEP 2: Database Partial Match =====
    partial_matches = db_search_partial(user_input, limit=10)
    
    if partial_matches and len(partial_matches) <= 3:
        # SUGGESTION FLOW: Tampilkan modal dengan sedikit pilihan
        return {
            "flow": "suggestion",
            "requires_modal": True,
            "suggestions": partial_matches,
            "ai_used": False,
            "message": "Apakah yang Anda maksud salah satu dari berikut?"
        }
    
    # ===== STEP 3: AI Normalization =====
    ai_result = normalize_with_ai(user_input)
    normalized_term = ai_result["normalized_term"]
    
    # ===== STEP 4: Search Normalized Term =====
    matches = db_search_exact(normalized_term)
    
    if not matches:
        matches = db_search_partial(normalized_term, limit=10)
    
    if matches:
        # AI + SUGGESTION FLOW: Tampilkan modal dengan AI hint
        return {
            "flow": "ai_suggestion",
            "requires_modal": True,
            "suggestions": matches,
            "ai_used": True,
            "ai_normalized": normalized_term,
            "ai_confidence": ai_result["confidence"],
            "ai_explanation": ai_result["explanation"],
            "message": f"AI menyarankan: {normalized_term}. Apakah maksud Anda?"
        }
    
    # ===== STEP 5: No Match Found =====
    return {
        "flow": "not_found",
        "requires_modal": False,
        "ai_used": True,
        "message": "Diagnosis tidak ditemukan. Silakan coba kata kunci lain.",
        "suggestions": []
    }
```

---

## 📐 DATABASE FUNCTIONS

**Kenapa perlu functions:** Performance & consistency

```sql
-- Function 1: Exact search
CREATE OR REPLACE FUNCTION icd10_exact_search(input_text VARCHAR)
RETURNS TABLE (
    code VARCHAR,
    name TEXT,
    source VARCHAR,
    match_type VARCHAR
) AS $$
BEGIN
    -- Try code match first
    RETURN QUERY
    SELECT 
        i.code, 
        i.name, 
        i.source,
        'code'::VARCHAR as match_type
    FROM icd10_master i
    WHERE UPPER(i.code) = UPPER(input_text)
    LIMIT 1;
    
    -- If no code match, try name match
    IF NOT FOUND THEN
        RETURN QUERY
        SELECT 
            i.code, 
            i.name, 
            i.source,
            'name'::VARCHAR as match_type
        FROM icd10_master i
        WHERE LOWER(i.name) = LOWER(input_text)
        LIMIT 1;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function 2: Partial search with ranking
CREATE OR REPLACE FUNCTION icd10_partial_search(
    input_text VARCHAR, 
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    code VARCHAR,
    name TEXT,
    source VARCHAR,
    relevance INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.code,
        i.name,
        i.source,
        CASE 
            WHEN i.name ILIKE input_text || '%' THEN 1
            WHEN i.name ILIKE '%' || input_text THEN 2
            ELSE 3
        END as relevance
    FROM icd10_master i
    WHERE i.name ILIKE '%' || input_text || '%'
    ORDER BY relevance ASC, LENGTH(i.name) ASC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Function 3: Get subcategories
CREATE OR REPLACE FUNCTION icd10_get_subcategories(parent_code VARCHAR)
RETURNS TABLE (
    code VARCHAR,
    name TEXT,
    is_parent BOOLEAN
) AS $$
DECLARE
    category VARCHAR;
BEGIN
    -- Extract category (J18.9 → J18)
    category := SPLIT_PART(parent_code, '.', 1);
    
    RETURN QUERY
    SELECT 
        i.code,
        i.name,
        (i.code = category) as is_parent
    FROM icd10_master i
    WHERE i.code = category 
       OR i.code LIKE category || '.%'
    ORDER BY i.code;
END;
$$ LANGUAGE plpgsql;
```

---

## 🎨 API ENDPOINTS DESIGN

### **Endpoint 1: `/api/icd10/lookup`**

**Request:**
```json
POST /api/icd10/lookup
{
  "diagnosis_input": "paru2 basah"
}
```

**Response (Direct Flow):**
```json
{
  "flow": "direct",
  "requires_modal": false,
  "selected_code": "J18",
  "selected_name": "Pneumonia, unspecified organism",
  "subcategories": {
    "parent": {
      "code": "J18",
      "name": "Pneumonia, unspecified organism"
    },
    "children": [
      {"code": "J18.0", "name": "Bronchopneumonia, unspecified"},
      {"code": "J18.1", "name": "Lobar pneumonia, unspecified"},
      {"code": "J18.9", "name": "Pneumonia, unspecified"}
    ]
  },
  "ai_used": false
}
```

**Response (AI + Suggestion Flow):**
```json
{
  "flow": "ai_suggestion",
  "requires_modal": true,
  "suggestions": [
    {
      "code": "J18.9",
      "name": "Pneumonia, unspecified",
      "relevance": 1
    },
    {
      "code": "J18.0",
      "name": "Bronchopneumonia, unspecified",
      "relevance": 2
    }
  ],
  "ai_used": true,
  "ai_normalized": "Pneumonia, unspecified organism",
  "ai_confidence": 90,
  "ai_explanation": "Paru-paru basah adalah istilah awam untuk pneumonia",
  "message": "AI menyarankan: Pneumonia, unspecified organism. Apakah maksud Anda?"
}
```

---

### **Endpoint 2: `/api/icd10/select`**

**Request:**
```json
POST /api/icd10/select
{
  "selected_code": "J18.9"
}
```

**Response:**
```json
{
  "selected_code": "J18.9",
  "selected_name": "Pneumonia, unspecified",
  "subcategories": {
    "parent": {
      "code": "J18",
      "name": "Pneumonia, unspecified organism"
    },
    "children": [
      {"code": "J18.0", "name": "Bronchopneumonia, unspecified"},
      {"code": "J18.1", "name": "Lobar pneumonia, unspecified"},
      {"code": "J18.9", "name": "Pneumonia, unspecified"}
    ]
  }
}
```

---

## ⚡ PERFORMANCE OPTIMIZATION

### **1. Database Indexes**

```sql
-- Essential indexes untuk query performance
CREATE INDEX IF NOT EXISTS idx_icd10_code_upper 
  ON icd10_master (UPPER(code));

CREATE INDEX IF NOT EXISTS idx_icd10_name_lower 
  ON icd10_master (LOWER(name));

CREATE INDEX IF NOT EXISTS idx_icd10_name_pattern 
  ON icd10_master (name text_pattern_ops);

-- For subcategory queries (LIKE 'J18%')
CREATE INDEX IF NOT EXISTS idx_icd10_code_prefix 
  ON icd10_master (code varchar_pattern_ops);
```

**Expected Performance:**
- Exact match: < 10ms
- Partial match: < 50ms
- Subcategory query: < 20ms

---

### **2. Caching Strategy**

```python
# Cache AI normalization results (Redis)
from functools import lru_cache
import hashlib

def get_cache_key(user_input: str) -> str:
    return f"icd10_ai:{hashlib.md5(user_input.lower().encode()).hexdigest()}"

@cache(ttl=3600)  # 1 hour cache
def normalize_with_ai_cached(user_input: str):
    cache_key = get_cache_key(user_input)
    
    # Check cache first
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Call AI
    result = normalize_with_ai(user_input)
    
    # Store in cache
    redis_client.setex(cache_key, 3600, json.dumps(result))
    
    return result
```

**Cache Hit Rate Target:** > 70%

---

### **3. AI Call Optimization**

**Strategy:** Minimize AI calls dengan smart pre-checking

```python
def should_call_ai(user_input: str) -> bool:
    """
    Decision: Apakah perlu call AI?
    """
    # Skip AI jika:
    # 1. Input adalah kode ICD-10 (pattern: 1-3 huruf + 2-3 angka)
    if re.match(r'^[A-Z]{1,3}\d{2,3}(\.\d)?$', user_input.upper()):
        return False
    
    # 2. Input sudah bahasa Inggris formal (heuristic: > 50% kata ada di dictionary)
    words = user_input.split()
    english_words = sum(1 for w in words if is_english_medical_term(w))
    if len(words) > 0 and (english_words / len(words)) > 0.5:
        return False
    
    # 3. Partial match di database menghasilkan < 3 suggestions
    partial = db_search_partial(user_input, limit=3)
    if len(partial) <= 3:
        return False
    
    return True
```

---

## 🧪 TESTING STRATEGY

### **Test Cases:**

1. **Exact Code Match**
   - Input: "J18.9"
   - Expected: Direct flow, no modal, subcategories shown

2. **Exact Name Match (English)**
   - Input: "Pneumonia"
   - Expected: Direct flow atau suggestion dengan beberapa pilihan

3. **Indonesian Input**
   - Input: "paru2 basah"
   - Expected: AI normalization → Suggestion modal

4. **Partial Match**
   - Input: "Pneum"
   - Expected: Suggestion modal dengan 5-10 pilihan

5. **No Match**
   - Input: "xyz123"
   - Expected: Not found message

6. **Subcategory Extraction**
   - Input: "J18"
   - Expected: Parent J18 + all J18.x children

---

## 📊 METRICS & MONITORING

### **Key Metrics:**

1. **Performance Metrics:**
   - Database query time (p50, p95, p99)
   - AI call time (p50, p95, p99)
   - End-to-end latency

2. **Accuracy Metrics:**
   - Direct match rate (target: > 60%)
   - AI normalization success rate (target: > 85%)
   - User selection rate (modal accept vs reject)

3. **Cost Metrics:**
   - AI calls per day
   - Cost per request
   - Cache hit rate

### **Logging:**

```python
logger.info(f"[ICD10_LOOKUP] Input={user_input}, Flow={flow}, AI_Used={ai_used}, Duration={elapsed}ms")
```

---

## 🚀 IMPLEMENTATION ROADMAP

### **Phase 1: Core Service (Priority: HIGH)**
- [ ] Database functions (exact, partial, subcategory)
- [ ] Python service layer (`icd10_smart_service.py`)
- [ ] Flow logic implementation
- [ ] Unit tests (database, pattern extraction)

### **Phase 2: AI Integration (Priority: HIGH)**
- [ ] OpenAI normalization function
- [ ] Prompt optimization
- [ ] AI skip logic (smart pre-check)
- [ ] Caching (in-memory first, Redis later)

### **Phase 3: API Endpoints (Priority: HIGH)**
- [ ] `/api/icd10/lookup` endpoint
- [ ] `/api/icd10/select` endpoint
- [ ] Request validation (Pydantic)
- [ ] Error handling

### **Phase 4: Frontend Components (Priority: MEDIUM)**
- [ ] ICD10 Input field
- [ ] Suggestion Modal component
- [ ] Subcategory Tree component
- [ ] Integration dengan existing flow

### **Phase 5: Optimization (Priority: LOW)**
- [ ] Database indexes tuning
- [ ] Redis caching
- [ ] Performance monitoring
- [ ] Load testing

---

## 🎯 SUCCESS CRITERIA

1. **Performance:**
   - [ ] 95% requests < 2 seconds (end-to-end)
   - [ ] Database queries < 50ms
   - [ ] AI calls < 1.5 seconds

2. **Accuracy:**
   - [ ] Direct match rate > 60%
   - [ ] AI normalization success > 85%
   - [ ] Zero false positives (wrong diagnosis)

3. **Cost:**
   - [ ] AI cost < $10/month (1000 users)
   - [ ] Cache hit rate > 70%

4. **User Experience:**
   - [ ] Modal muncul hanya jika perlu
   - [ ] Suggestion relevant (< 10 pilihan)
   - [ ] Subcategory complete & accurate

---

## ✅ KONFIRMASI USER (2025-11-14)

1. **Subcategory Display:**
   - ✅ Tampilkan **SEMUA** subcategory dengan aturan 3 digit pertama sama
   - ✅ Format: **LIST** (untuk sementara, frontend belum jadi)
   - ✅ Ditampilkan dalam **MODAL TERSENDIRI**

2. **AI Strategy untuk Guarantee Match:**
   - ✅ **AI HARUS BELAJAR dari icd10_master DULU**
   - ✅ Strategy: **RAG (Retrieval-Augmented Generation)**
   - ✅ Alur: AI normalisasi → Cari di DB → Jika tidak ada, AI generate ulang dengan context DB
   - ✅ **TIDAK BOLEH** ada case "AI tidak match"

3. **Language Output:**
   - ✅ Tetap **BAHASA INGGRIS** (sesuai database)

4. **Suggestions Limit:**
   - ✅ **TIDAK ADA BATAS** - selama ada ya ditampilkan
   - ✅ UI akan handle pagination/scroll

5. **Integration:**
   - ✅ Service ICD-10 **TERPISAH** dari analyze_diagnosis_service.py
   - ✅ Endpoints di **lite_endpoints.py** dan **main.py**
   - ✅ **HAPUS** fungsi ICD-10 di analyze_diagnosis_service.py (map_icd10_who_to_bpjs, dll)

---

## 🔄 UPDATED IMPLEMENTATION STRATEGY

### **AI Guarantee Match Strategy (RAG Approach):**

```python
def smart_icd10_lookup_with_rag(user_input: str) -> dict:
    """
    GUARANTEED match dengan RAG (Retrieval-Augmented Generation)
    
    Alur:
    1. Database exact match → jika ada, return
    2. Database partial match → jika < 5, tampilkan suggestions
    3. AI Normalization DENGAN CONTEXT DATABASE:
       - Sample 50 diagnosis terdekat dari DB
       - Inject ke prompt sebagai reference
       - AI generate normalized term yang PASTI ada di DB
    4. Search normalized term di DB → HARUS MATCH
    5. Jika masih tidak match → AI regenerate dengan feedback loop
    """
    
    # Step 1: Exact match
    exact = db_search_exact(user_input)
    if exact:
        return {"flow": "direct", "result": exact}
    
    # Step 2: Partial match
    partial = db_search_partial(user_input, limit=10)
    if partial and len(partial) <= 5:
        return {"flow": "suggestion", "suggestions": partial}
    
    # Step 3: RAG - AI dengan context database
    # Sample database untuk AI reference
    db_samples = get_similar_diagnoses(user_input, limit=50)
    
    # AI normalization dengan RAG
    normalized = ai_normalize_with_rag(
        user_input=user_input,
        database_context=db_samples
    )
    
    # Step 4: Verify hasil AI
    verified = db_search_exact(normalized["term"])
    
    if verified:
        return {"flow": "ai_match", "result": verified}
    
    # Step 5: Feedback loop (jika masih tidak match)
    for attempt in range(3):  # Max 3 attempts
        normalized = ai_regenerate_with_feedback(
            user_input=user_input,
            previous_attempt=normalized["term"],
            available_options=db_samples
        )
        
        verified = db_search_exact(normalized["term"])
        if verified:
            return {"flow": "ai_match", "result": verified}
    
    # Last resort: Return closest partial matches
    return {
        "flow": "fallback_suggestions",
        "suggestions": db_samples[:10],
        "message": "Silakan pilih diagnosis yang paling sesuai"
    }
```

### **AI Prompt dengan RAG Context:**

```python
PROMPT_WITH_RAG = """
You are a medical coding expert. Your task is to normalize user input to match EXACTLY one diagnosis from our ICD-10 database.

USER INPUT: "{user_input}"

AVAILABLE ICD-10 DIAGNOSES (Database Context):
{database_context}

RULES:
1. You MUST return a diagnosis name that EXACTLY matches one from the database context above
2. Choose the MOST RELEVANT diagnosis based on user input
3. If user input is Indonesian/informal, find the English equivalent in the database
4. DO NOT create new diagnosis names - ONLY use names from the database context

EXAMPLES:
- "paru2 basah" → Look for "Pneumonia" variations in database → Return exact match
- "demam berdarah" → Look for "Dengue" variations in database → Return exact match

OUTPUT (JSON):
{{
  "matched_diagnosis": "EXACT diagnosis name from database",
  "matched_code": "ICD-10 code from database",
  "confidence": 95,
  "reasoning": "Brief explanation why this is the best match"
}}

CRITICAL: The "matched_diagnosis" MUST be an EXACT copy from the database context above.
"""
```

---

## 📝 REVISED IMPLEMENTATION PLAN

### **Phase 1: Database Layer (HIGH PRIORITY)**

**Files to create:**
- `services/icd10_service.py` - Core service (NEW)
- `services/icd10_rag_helper.py` - RAG logic (NEW)

**Database functions:**
```python
# 1. Exact search (code + name)
def db_search_exact(input_text: str) -> Optional[Dict]

# 2. Partial search with ranking
def db_search_partial(input_text: str, limit: int) -> List[Dict]

# 3. Get similar diagnoses for RAG context
def get_similar_diagnoses(input_text: str, limit: int) -> List[Dict]

# 4. Get subcategories by parent code
def get_subcategories(parent_code: str) -> Dict[str, List]

# 5. Extract category from code
def extract_category(code: str) -> str
```

---

### **Phase 2: AI Integration with RAG (HIGH PRIORITY)**

**Files:**
- `services/icd10_ai_normalizer.py` - AI normalization dengan RAG

**Functions:**
```python
# 1. AI normalize dengan database context
def ai_normalize_with_rag(user_input: str, database_context: List) -> Dict

# 2. Regenerate dengan feedback
def ai_regenerate_with_feedback(user_input: str, previous: str, options: List) -> Dict

# 3. Helper: Format database context untuk prompt
def format_db_context_for_prompt(db_samples: List) -> str
```

---

### **Phase 3: API Endpoints (HIGH PRIORITY)**

**File:** `lite_endpoints.py` (add new endpoints)

**New endpoints:**
```python
# 1. POST /api/icd10/lookup
def endpoint_icd10_lookup(request_data: Dict) -> Dict

# 2. POST /api/icd10/select
def endpoint_icd10_select(request_data: Dict) -> Dict

# 3. GET /api/icd10/subcategories/{code}
def endpoint_icd10_get_subcategories(request_data: Dict) -> Dict
```

---

### **Phase 4: Remove Old ICD-10 Logic (MEDIUM PRIORITY)**

**File:** `analyze_diagnosis_service.py`

**Functions to remove/refactor:**
- `map_icd10_who_to_bpjs()` - Remove completely
- ICD-10 logic in `gpt_analyze_diagnosis()` - Simplify
- ICD-10 logic in `process_analyze_diagnosis()` - Replace dengan call ke icd10_service

**Replacement:**
```python
# OLD (in analyze_diagnosis_service.py):
icd10_data = smart_merge("icd10", ...)

# NEW (call icd10_service):
from services.icd10_service import lookup_icd10_smart
icd10_result = lookup_icd10_smart(disease_name)
icd10_data = {
    "kode_icd": icd10_result["selected_code"],
    "struktur_icd10": icd10_result["selected_name"],
    ...
}
```

---

## 📝 NEXT STEPS (CONFIRMED)

1. ✅ **Phase 1A:** Create `icd10_service.py` dengan database functions
2. ✅ **Phase 1B:** Create `icd10_rag_helper.py` untuk RAG logic
3. ✅ **Phase 2:** Implement AI normalization dengan RAG
4. ✅ **Phase 3:** Add endpoints ke `lite_endpoints.py`
5. ✅ **Phase 4:** Refactor `analyze_diagnosis_service.py`
6. ✅ **Phase 5:** Testing & optimization

---

**Prepared by:** AI Assistant  
**Date:** 2025-11-14  
**Version:** 2.0 (REVISED)  
**Status:** ✅ APPROVED - READY FOR IMPLEMENTATION
