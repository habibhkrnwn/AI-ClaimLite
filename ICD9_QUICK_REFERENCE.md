# ⚡ ICD-9 Quick Reference - SIMPLIFIED VERSION

## 🎯 What Changed

**BEFORE (Complex):**
- Fuzzy matching with RapidFuzz ❌
- JSON files (icd9_mapping.json, aliases.json) ❌
- Manual Indonesian aliases ❌
- Tightly coupled in analyze_diagnosis_service.py ❌

**AFTER (Simple):**
- Database exact search → AI normalization ✅
- No JSON files (database only) ✅
- AI handles Indonesian ✅
- Standalone service ✅

---

## 📝 Summary

### **Flow:** 
```
Input → Exact DB Search → (if not found) → AI Normalize → Validate → Return
```

### **Timeline:** 
3 days (backend only, frontend handled separately)

### **Files:**
- **NEW:** `icd9_smart_service.py` (standalone)
- **MODIFIED:** `analyze_diagnosis_service.py`, `lite_endpoints.py`, `main.py`
- **DELETE:** `icd9_mapping_service.py`, `icd9_mapping.json`, `icd9_indonesian_aliases.json`

---

## 🚀 Quick Start

### **1. Create Service** (Day 1)
```python
# icd9_smart_service.py
exact_search_icd9()          # DB exact match
normalize_procedure_with_ai() # OpenAI GPT-3.5-turbo
validate_ai_suggestions()     # Validate AI vs DB
lookup_icd9_procedure()       # Main function
```

### **2. Add Endpoint** (Day 2)
```python
# POST /api/lite/icd9/suggestions
Request:  {"procedure_input": "x-ray thorax"}
Response: {"status": "success", "result": {...}, "needs_selection": false}
```

### **3. Clean Up** (Day 3)
- Delete old files
- Remove rapidfuzz dependency
- Update docs

---

## 🧪 Test Commands

```bash
# Unit tests
python test_icd9_smart_service.py

# Endpoint test
curl -X POST http://localhost:8000/api/lite/icd9/suggestions \
  -H "Content-Type: application/json" \
  -d '{"procedure_input": "rontgen thorax"}'

# Complete flow test
python test_complete_icd9_flow.py
```

---

## ⚙️ AI Prompt (Optimized)

```python
PROMPT = """You are a medical coding expert. Normalize the procedure to ICD-9-CM terminology.

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

IMPORTANT: Return ONLY valid JSON. No explanation needed."""
```

**Model:** GPT-3.5-turbo (fast & cost-effective)  
**Target Response Time:** <2 seconds

---

## 📊 Decision Matrix

| Input Type | Flow | Modal Needed? |
|------------|------|---------------|
| Exact match in DB | Return langsung | ❌ No |
| AI returns 1 valid | Return langsung | ❌ No |
| AI returns multiple | Return suggestions | ✅ Yes |
| AI returns none | Return not found | ❌ No |

---

## 🔍 Key Points

1. **NO Fuzzy Matching** - Langsung dari exact → AI
2. **NO JSON Files** - Database adalah source of truth
3. **Standalone Service** - Tidak gabung dengan services lain
4. **AI for Indonesian** - Tidak perlu manual aliases
5. **Frontend Separate** - Backend ready, frontend oleh teman

---

## 📌 Critical Settings

```python
# Database
INDEX: LOWER(name) on icd9cm_master

# OpenAI
MODEL: gpt-3.5-turbo
TEMPERATURE: 0.3 (consistency)
MAX_TOKENS: 200 (concise)

# Auto-Select
THRESHOLD: 1 match = auto assign
```

---

## ✅ Checklist

**Day 1:**
- [ ] Create `icd9_smart_service.py`
- [ ] Add DB index
- [ ] Unit tests passing

**Day 2:**
- [ ] Add endpoint `/api/lite/icd9/suggestions`
- [ ] Modify `analyze_diagnosis_service.py`
- [ ] API tests passing

**Day 3:**
- [ ] Delete old files
- [ ] Remove unused dependencies
- [ ] Documentation updated
- [ ] All tests passing

---

**Status:** 🟢 Ready to implement  
**Docs:** See `ICD9_IMPLEMENTATION_FINAL.md` for detailed steps
