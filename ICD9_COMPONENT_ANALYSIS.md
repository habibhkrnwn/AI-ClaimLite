# 🔍 ICD-9 Component Analysis Summary

## 📂 Current Architecture Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React/TypeScript)                     │
│                         web/src/components/                              │
├─────────────────────────────────────────────────────────────────────────┤
│  InputPanel.tsx                                                          │
│  ├─ Form fields: diagnosis, procedure (tindakan), medication            │
│  ├─ Button: "Generate AI"                                               │
│  └─ Calls: POST /api/analyze                                            │
└────────────────────────┬────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     WEB BACKEND (Node.js/Express)                        │
│                     web/server/routes/aiRoutes.ts                        │
├─────────────────────────────────────────────────────────────────────────┤
│  POST /api/analyze                                                       │
│  ├─ Validates: diagnosis, procedure, medication                         │
│  ├─ Checks: AI usage limit                                              │
│  ├─ Forwards to: CORE_ENGINE_URL/api/lite/analyze/single                │
│  └─ Returns: Analysis results to frontend                               │
└────────────────────────┬────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CORE ENGINE (FastAPI/Python)                          │
│                    core_engine/main.py                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  POST /api/lite/analyze/single                                           │
│  ├─ Calls: endpoint_analyze_single() from lite_endpoints.py             │
│  └─ Returns: Full analysis result                                       │
└────────────────────────┬────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        ENDPOINTS LAYER                                   │
│                  core_engine/lite_endpoints.py                           │
├─────────────────────────────────────────────────────────────────────────┤
│  endpoint_analyze_single()                                               │
│  ├─ Parses input (mode: 'form' or 'text')                               │
│  ├─ Calls: process_analyze_diagnosis() from analyze_diagnosis_service   │
│  └─ Returns: Structured result with ICD-10, ICD-9, tindakan, etc.       │
└────────────────────────┬────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      BUSINESS LOGIC LAYER                                │
│              core_engine/services/analyze_diagnosis_service.py           │
├─────────────────────────────────────────────────────────────────────────┤
│  process_analyze_diagnosis()                                             │
│  ├─ Calls OpenAI: gpt_analyze_diagnosis()                               │
│  ├─ Processes: diagnosis, tindakan, obat                                │
│  └─ For tindakan processing:                                             │
│     ├─ Line 721: icd9_mapped = map_icd9_smart()  ❌ CURRENT             │
│     ├─ Uses: icd9_mapping_service.py                                    │
│     └─ Returns: tindakan with ICD-9 code, desc, confidence              │
└────────────────────────┬────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       ICD-9 SERVICE LAYER (CURRENT)                      │
│                core_engine/services/icd9_mapping_service.py              │
├─────────────────────────────────────────────────────────────────────────┤
│  map_icd9_smart()                                                        │
│  ├─ Strategy 1: map_icd9_by_name() → Exact match dari JSON              │
│  ├─ Strategy 2: Fuzzy match dengan RapidFuzz                            │
│  ├─ Strategy 3: validate_icd9_code() → Reverse lookup                   │
│  └─ Data Source: JSON FILES ❌                                          │
│     ├─ rules/icd9_mapping.json (4,626 entries)                          │
│     └─ rules/icd9_indonesian_aliases.json                               │
│                                                                          │
│  ❌ PROBLEMS:                                                           │
│  • Tidak pakai database icd9cm_master                                   │
│  • Tidak ada AI normalization untuk ambiguous input                     │
│  • Tidak ada user selection mechanism                                   │
│  • Hardcoded di analyze_diagnosis_service.py (coupled)                  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA SOURCES                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  DATABASE (PostgreSQL)                                                   │
│  ├─ icd9cm_master (4,626 records) ✅ EXISTS                             │
│  │  ├─ id, code, name, source, validation_status, created_at           │
│  │  └─ Example: code="87.44", name="Routine chest X-ray"               │
│  │                                                                       │
│  ├─ icd10_master (18,543 records) ✅ USED                               │
│  └─ fornas_drugs ✅ USED                                                │
│                                                                          │
│  JSON FILES (Fallback/Legacy)                                            │
│  ├─ rules/icd9_mapping.json ❌ CURRENTLY USED (should be deprecated)    │
│  └─ rules/icd9_indonesian_aliases.json ❌ CURRENTLY USED                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Analysis

### **Current Flow (OLD):**

```
User Input: "x-ray thorax"
    ↓
analyze_diagnosis_service.py
    ↓
map_icd9_smart(procedure_name="x-ray thorax")
    ↓
icd9_mapping_service.py
    ↓
1. Check Indonesian aliases (JSON) → "x-ray thorax" not found
2. Exact match in icd9_mapping.json → not found
3. Fuzzy match with RapidFuzz → finds "Radiography of chest" (similarity 75%)
    ↓
Return: {
    "kode": "87.44",
    "deskripsi": "Radiography of chest",
    "source": "WHO Official (Fuzzy Match)",
    "valid": true,
    "confidence": 75
}
    ↓
Frontend receives result
    ↓
❌ NO USER INTERACTION → Auto-assigned even if confidence low
```

### **New Flow (PROPOSED):**

```
User Input: "x-ray thorax"
    ↓
Frontend calls: POST /api/lite/icd9/suggestions
    ↓
icd9_smart_service.py (NEW)
    ↓
Step 1: Exact search in DATABASE (icd9cm_master)
    SELECT * FROM icd9cm_master 
    WHERE LOWER(name) LIKE '%x-ray%thorax%'
    ↓
    Result: Multiple matches found
    - "Routine chest X-ray" (87.44)
    - "Other chest X-ray" (87.49)
    ↓
Step 2: Fuzzy ranking (if multiple results)
    Calculate similarity scores
    ↓
    Return TOP 5 with scores
    ↓
Step 3: Check auto_select threshold
    IF highest confidence ≥ 85% AND only 1 match → auto_select = true
    ELSE → auto_select = false
    ↓
Frontend receives: {
    "status": "success",
    "result_type": "multiple",
    "suggestions": [
        {"code": "87.44", "name": "Routine chest X-ray", "confidence": 90},
        {"code": "87.49", "name": "Other chest X-ray", "confidence": 75}
    ],
    "auto_select": false
}
    ↓
IF auto_select = false:
    ✅ Show Modal: "Apakah yang Anda maksud:"
        ○ Routine chest X-ray (87.44)
        ○ Other chest X-ray (87.49)
    User clicks selection
    ↓
Frontend sends selected code to analyze endpoint
ELSE:
    Direct assignment (no modal)
```

---

## 🎯 Key Differences: Old vs New

| Aspect | OLD (Current) | NEW (Proposed) |
|--------|---------------|----------------|
| **Data Source** | JSON files | Database `icd9cm_master` |
| **User Involvement** | None (auto-assign) | Modal for ambiguous cases |
| **AI Usage** | Never used | Used for normalization if DB search fails |
| **Confidence Handling** | Returns even low confidence (50%) | Shows suggestions if <85% |
| **Coupling** | Tightly coupled in `analyze_diagnosis_service.py` | Separate service + dedicated endpoint |
| **Performance** | Load JSON on every call | Database query with indexes |
| **Scalability** | Limited to JSON size | Scalable with DB |
| **UX** | Frustrating (wrong auto-assignment) | Better (user confirms ambiguous cases) |

---

## 📋 Component Dependencies

### **Files Currently Using ICD-9:**

1. **`analyze_diagnosis_service.py`** (Line 20, 721, 775)
   - Import: `from services.icd9_mapping_service import map_icd9_smart`
   - Usage: Mapping tindakan input/AI to ICD-9 codes
   - **Action:** Replace with new service

2. **`icd9_mapping_service.py`**
   - Functions: `map_icd9_smart()`, `map_icd9_by_name()`, `validate_icd9_code()`
   - **Action:** Deprecate, keep untuk backward compatibility

3. **`lite_endpoints.py`**
   - Calls: `process_analyze_diagnosis()` which uses ICD-9
   - **Action:** Add new endpoint `/api/lite/icd9/suggestions`

4. **`main.py`**
   - Routes: `/api/lite/analyze/single`
   - **Action:** Add new route for ICD-9 suggestions

5. **Frontend: `InputPanel.tsx`**
   - User input: `procedure` field
   - **Action:** Add modal component for suggestions

6. **Backend: `aiRoutes.ts`**
   - Forwards: `procedure` to core engine
   - **Action:** Add endpoint untuk ICD-9 suggestions

---

## 🚀 Implementation Priority

### **Phase 1: Core Service (CRITICAL)**
1. Create `icd9_smart_service.py`
2. Implement database search functions
3. Add AI normalization function
4. Unit test extensively

### **Phase 2: API Integration (HIGH)**
1. Add `/api/lite/icd9/suggestions` endpoint
2. Modify analyze flow untuk support new flow
3. API testing

### **Phase 3: Frontend (MEDIUM)**
1. Create suggestion modal component
2. Integrate dengan analyze flow
3. E2E testing

### **Phase 4: Optimization (LOW)**
1. Add database indexes
2. Implement caching
3. Performance testing

---

## ⚠️ Breaking Changes

### **Backward Compatibility Concerns:**

1. **API Response Structure:**
   - OLD: `tindakan` directly has `icd9_code`
   - NEW: `tindakan` might have `needs_icd9_selection: true`
   - **Mitigation:** Add feature flag `use_legacy_icd9=true/false`

2. **Service Import:**
   - OLD: `from services.icd9_mapping_service import map_icd9_smart`
   - NEW: `from services.icd9_smart_service import lookup_icd9_smart`
   - **Mitigation:** Keep old service, add deprecation warning

3. **JSON Files:**
   - OLD: Always loaded
   - NEW: Only as fallback
   - **Mitigation:** Keep files, add migration script

---

## 📊 Expected Impact

### **Positive:**
✅ Better UX (user controls ambiguous cases)  
✅ Higher accuracy (database-driven)  
✅ Cost reduction (less unnecessary AI calls)  
✅ Better maintainability (decoupled service)  
✅ Scalability (database > JSON)

### **Challenges:**
⚠️ Frontend complexity (modal handling)  
⚠️ Backend changes (new endpoint, service)  
⚠️ Testing overhead (more scenarios)  
⚠️ Migration effort (deprecate old code)

---

## 🎓 Recommendations

1. **DO IMPLEMENT** this new flow → significantly better UX
2. **DO SEPARATE** ICD-9 service dari analyze_diagnosis_service
3. **DO USE** database as primary source
4. **DO KEEP** JSON files as fallback untuk reliability
5. **DO ADD** feature flag untuk gradual rollout
6. **DO TEST** extensively sebelum production

---

**Analysis Status:** ✅ COMPLETE  
**Next Step:** Awaiting approval to proceed with implementation  
**Estimated Effort:** 5-6 days (1 developer)  
**Risk Level:** MEDIUM (good architecture, needs careful testing)
