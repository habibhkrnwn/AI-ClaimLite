# 🚀 ICD-9 Smart Service - Implementation Guide (FINAL SIMPLIFIED)

**Status:** 🟢 READY TO IMPLEMENT  
**Timeline:** 3 Days (Backend Only)  
**Date:** 2025-11-14

---

## 📋 Quick Overview

### **Problem:**
- Old service uses JSON files (not database)
- No user interaction for ambiguous cases
- Fuzzy matching adds complexity

### **Solution:**
- ✅ Database-first (exact match)
- ✅ AI normalization (if exact fails)
- ✅ Standalone service (decoupled)
- ❌ NO fuzzy matching
- ❌ NO JSON files

---

## 🔄 Flow Diagram (SIMPLE)

```
Input: "x-ray thorax" atau "rontgen dada"
   ↓
┌─────────────────────────────────────┐
│ STEP 1: Exact DB Search             │
│ SELECT * FROM icd9cm_master         │
│ WHERE LOWER(name) = LOWER(input)    │
└─────────────────────────────────────┘
   │
   ├─ FOUND → Return (100% confidence)
   │
   ↓
┌─────────────────────────────────────┐
│ STEP 2: AI Normalization            │
│ OpenAI: Normalize to ICD-9 WHO      │
│ Response: ["Routine chest X-ray",  │
│            "Other chest X-ray"]     │
└─────────────────────────────────────┘
   ↓
┌─────────────────────────────────────┐
│ STEP 3: Validate AI Suggestions     │
│ For each: SELECT * FROM icd9cm_master
│ WHERE LOWER(name) = LOWER(ai_term) │
└─────────────────────────────────────┘
   │
   ├─ 1 match → Return (95% confidence)
   ├─ Multiple → Return suggestions for modal
   └─ None → Return "not found"
```

---

## 📁 Implementation Checklist

### **Day 1: Service Creation**

#### 1. Create `core_engine/services/icd9_smart_service.py`

```python
"""
ICD-9 Smart Service - Standalone
Database-first approach with AI normalization fallback
"""

from sqlalchemy import text
from database_connection import get_db_session
from openai import OpenAI
import os
from typing import Dict, List, Optional
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def exact_search_icd9(procedure_input: str) -> Optional[Dict]:
    """
    Exact search di database icd9cm_master.
    
    Returns:
        {
            "code": "87.44",
            "name": "Routine chest X-ray",
            "source": "database",
            "valid": True,
            "confidence": 100
        } atau None
    """
    session = get_db_session()
    try:
        query = text("""
            SELECT code, name 
            FROM icd9cm_master 
            WHERE LOWER(name) = LOWER(:input)
            LIMIT 1
        """)
        result = session.execute(query, {"input": procedure_input.strip()}).fetchone()
        
        if result:
            return {
                "code": result[0],
                "name": result[1],
                "source": "database_exact",
                "valid": True,
                "confidence": 100
            }
        return None
    finally:
        session.close()


def normalize_procedure_with_ai(procedure_input: str) -> List[str]:
    """
    AI normalization ke WHO ICD-9-CM terminology.
    
    Returns:
        List of procedure names (3-5 items)
    """
    prompt = f"""You are a medical coding expert. Normalize the procedure to ICD-9-CM terminology.

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

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Fast & cost-effective
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Low temp for consistent results
            max_tokens=200
        )
        
        content = response.choices[0].message.content.strip()
        data = json.loads(content)
        return data.get("procedures", [])
    except Exception as e:
        print(f"[ICD9_AI] Error: {e}")
        return []


def validate_ai_suggestions(ai_suggestions: List[str]) -> List[Dict]:
    """
    Validate AI suggestions dengan exact search di database.
    
    Returns:
        List of valid matches
    """
    valid_matches = []
    session = get_db_session()
    
    try:
        for suggestion in ai_suggestions:
            query = text("""
                SELECT code, name 
                FROM icd9cm_master 
                WHERE LOWER(name) = LOWER(:input)
                LIMIT 1
            """)
            result = session.execute(query, {"input": suggestion.strip()}).fetchone()
            
            if result:
                valid_matches.append({
                    "code": result[0],
                    "name": result[1],
                    "source": "ai_validated",
                    "valid": True,
                    "confidence": 95
                })
    finally:
        session.close()
    
    return valid_matches


def lookup_icd9_procedure(procedure_input: str) -> Dict:
    """
    Main orchestrator - Simple 2-step flow.
    
    Returns:
        {
            "status": "success" | "suggestions" | "not_found",
            "result": {...} atau None,
            "suggestions": [...],
            "needs_selection": True/False
        }
    """
    if not procedure_input or procedure_input.strip() == "":
        return {
            "status": "not_found",
            "result": None,
            "suggestions": [],
            "needs_selection": False,
            "message": "No input provided"
        }
    
    # STEP 1: Exact search
    exact_match = exact_search_icd9(procedure_input)
    if exact_match:
        print(f"[ICD9] ✅ Exact match: {exact_match['name']}")
        return {
            "status": "success",
            "result": exact_match,
            "suggestions": [],
            "needs_selection": False
        }
    
    # STEP 2: AI normalization
    print(f"[ICD9] 🤖 No exact match, using AI normalization...")
    ai_suggestions = normalize_procedure_with_ai(procedure_input)
    
    if not ai_suggestions:
        return {
            "status": "not_found",
            "result": None,
            "suggestions": [],
            "needs_selection": False,
            "message": "AI could not normalize input"
        }
    
    # STEP 3: Validate AI suggestions
    valid_matches = validate_ai_suggestions(ai_suggestions)
    
    if len(valid_matches) == 0:
        return {
            "status": "not_found",
            "result": None,
            "suggestions": [],
            "needs_selection": False,
            "message": "No valid ICD-9 procedures found"
        }
    elif len(valid_matches) == 1:
        # Auto-select jika hanya 1 match
        print(f"[ICD9] ✅ Single AI match: {valid_matches[0]['name']}")
        return {
            "status": "success",
            "result": valid_matches[0],
            "suggestions": [],
            "needs_selection": False
        }
    else:
        # Multiple matches → frontend shows modal
        print(f"[ICD9] 🔍 Multiple matches ({len(valid_matches)}), needs user selection")
        return {
            "status": "suggestions",
            "result": None,
            "suggestions": valid_matches,
            "needs_selection": True
        }
```

#### 2. Add Database Index

```sql
-- Run this in PostgreSQL
CREATE INDEX IF NOT EXISTS idx_icd9cm_name_lower 
ON icd9cm_master(LOWER(name));
```

#### 3. Create `core_engine/test_icd9_smart_service.py`

```python
"""Unit tests for ICD-9 Smart Service"""

from services.icd9_smart_service import (
    exact_search_icd9,
    normalize_procedure_with_ai,
    validate_ai_suggestions,
    lookup_icd9_procedure
)

def test_exact_search():
    """Test exact database search"""
    # Test exact match
    result = exact_search_icd9("Routine chest X-ray")
    assert result is not None
    assert result["code"] == "87.44"
    assert result["confidence"] == 100
    
    # Test not found
    result = exact_search_icd9("random procedure xyz")
    assert result is None
    print("✅ Exact search test passed")


def test_ai_normalization():
    """Test AI normalization"""
    suggestions = normalize_procedure_with_ai("x-ray thorax")
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0
    print(f"✅ AI returned {len(suggestions)} suggestions: {suggestions}")


def test_lookup_flow():
    """Test main lookup function"""
    # Test 1: Exact match
    result = lookup_icd9_procedure("Routine chest X-ray")
    assert result["status"] == "success"
    assert result["needs_selection"] == False
    print(f"✅ Test 1 passed: {result['result']['name']}")
    
    # Test 2: AI normalization
    result = lookup_icd9_procedure("rontgen dada")
    assert result["status"] in ["success", "suggestions"]
    print(f"✅ Test 2 passed: {result['status']}")
    
    # Test 3: Not found
    result = lookup_icd9_procedure("random xyz")
    assert result["status"] == "not_found"
    print(f"✅ Test 3 passed: {result['message']}")


if __name__ == "__main__":
    print("🧪 Testing ICD-9 Smart Service...\n")
    test_exact_search()
    test_ai_normalization()
    test_lookup_flow()
    print("\n✅ All tests passed!")
```

---

### **Day 2: Integration**

#### 4. Add Endpoint in `core_engine/lite_endpoints.py`

```python
# Add this function

def endpoint_get_icd9_suggestions(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/icd9/suggestions
    
    Get ICD-9 suggestions untuk procedure input.
    
    Request:
    {
        "procedure_input": "x-ray thorax"
    }
    
    Response:
    {
        "status": "success",
        "result": {...} atau null,
        "suggestions": [...],
        "needs_selection": true/false
    }
    """
    from services.icd9_smart_service import lookup_icd9_procedure
    
    procedure_input = request_data.get("procedure_input", "")
    
    if not procedure_input:
        return {
            "status": "error",
            "message": "procedure_input is required"
        }
    
    result = lookup_icd9_procedure(procedure_input)
    
    return {
        "status": "success",
        "data": result
    }
```

#### 5. Add Route in `core_engine/main.py`

```python
# Add this endpoint

@app.post("/api/lite/icd9/suggestions")
async def get_icd9_suggestions(request: Request):
    """Get ICD-9 procedure suggestions"""
    try:
        data = await request.json()
        result = endpoint_get_icd9_suggestions(data)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"ICD-9 suggestions error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
```

#### 6. Modify `analyze_diagnosis_service.py`

```python
# REPLACE this line (around line 20):
# from services.icd9_mapping_service import map_icd9_smart

# WITH this:
from services.icd9_smart_service import lookup_icd9_procedure

# REPLACE the ICD-9 mapping logic (around line 721):
# OLD:
# icd9_mapped = map_icd9_smart(
#     procedure_name=nama_tindakan,
#     ai_code=None,
#     use_fuzzy=True,
#     threshold=85
# )

# NEW:
icd9_result = lookup_icd9_procedure(nama_tindakan)

if icd9_result["status"] == "success":
    icd9_data = icd9_result["result"]
    tindakan_item["icd9_code"] = icd9_data["code"]
    tindakan_item["icd9_desc"] = icd9_data["name"]
    tindakan_item["icd9_valid"] = icd9_data["valid"]
    tindakan_item["icd9_confidence"] = icd9_data["confidence"]
    tindakan_item["icd9_source"] = icd9_data["source"]
elif icd9_result["status"] == "suggestions":
    # Multiple matches - frontend will handle
    tindakan_item["needs_icd9_selection"] = True
    tindakan_item["icd9_suggestions"] = icd9_result["suggestions"]
else:
    # Not found
    tindakan_item["icd9_code"] = "-"
    tindakan_item["icd9_desc"] = nama_tindakan
    tindakan_item["icd9_valid"] = False
    tindakan_item["icd9_confidence"] = 0
```

---

### **Day 3: Cleanup**

#### 7. Delete Old Files

```powershell
# Run in PowerShell
cd e:\SOFTWARE\GitHub\repo\AIClaimLite\AI-ClaimLite\core_engine

# Delete old service
Remove-Item services\icd9_mapping_service.py

# Delete JSON files
Remove-Item rules\icd9_mapping.json
Remove-Item rules\icd9_indonesian_aliases.json
```

#### 8. Update `requirements.txt`

```bash
# Check if rapidfuzz is used elsewhere
grep -r "rapidfuzz" core_engine/

# If NOT used, remove from requirements.txt
# Edit requirements.txt and remove line:
# rapidfuzz==3.x.x
```

#### 9. Test Complete Flow

```python
# Test script: test_complete_icd9_flow.py

import requests

BASE_URL = "http://localhost:8000"

def test_icd9_suggestions_endpoint():
    """Test new ICD-9 suggestions endpoint"""
    
    # Test 1: Exact match
    response = requests.post(f"{BASE_URL}/api/lite/icd9/suggestions", json={
        "procedure_input": "Routine chest X-ray"
    })
    data = response.json()
    print(f"Test 1 (Exact): {data['data']['status']}")
    assert data['data']['status'] == 'success'
    
    # Test 2: AI normalization
    response = requests.post(f"{BASE_URL}/api/lite/icd9/suggestions", json={
        "procedure_input": "rontgen thorax"
    })
    data = response.json()
    print(f"Test 2 (AI): {data['data']['status']}")
    
    # Test 3: Not found
    response = requests.post(f"{BASE_URL}/api/lite/icd9/suggestions", json={
        "procedure_input": "random xyz abc"
    })
    data = response.json()
    print(f"Test 3 (Not Found): {data['data']['status']}")
    assert data['data']['status'] == 'not_found'
    
    print("✅ All endpoint tests passed!")

if __name__ == "__main__":
    test_icd9_suggestions_endpoint()
```

---

## 📊 Performance Targets

| Metric | Target | How to Achieve |
|--------|--------|----------------|
| Exact Search | <100ms | Database index on LOWER(name) |
| AI Normalization | <2s | GPT-3.5-turbo, optimized prompt |
| Total Response | <2.5s | Combined (worst case) |
| Accuracy | >95% | AI + database validation |

---

## 🧪 Testing Checklist

- [ ] Unit test: `exact_search_icd9()`
- [ ] Unit test: `normalize_procedure_with_ai()`
- [ ] Unit test: `validate_ai_suggestions()`
- [ ] Unit test: `lookup_icd9_procedure()`
- [ ] API test: `/api/lite/icd9/suggestions` endpoint
- [ ] Integration test: Analyze flow dengan ICD-9
- [ ] Performance test: Response time <2.5s
- [ ] Edge cases: Empty input, invalid input, AI failure

---

## 📝 Documentation Updates

1. Update `README.md` - Remove references to old service
2. Update API docs - Add new endpoint documentation
3. Add inline comments in code
4. Update deployment notes

---

## ✅ Success Criteria

- [ ] Service berfungsi dengan exact search
- [ ] AI normalization works untuk Indonesian input
- [ ] Response time <2.5 seconds
- [ ] Old files deleted
- [ ] All tests passing
- [ ] No dependencies on JSON files
- [ ] Standalone service (no coupling)

---

## 🚀 Deployment Notes

```bash
# 1. Backup database
pg_dump -U postgres -d your_db > backup_before_icd9.sql

# 2. Add database index
psql -U postgres -d your_db -c "CREATE INDEX IF NOT EXISTS idx_icd9cm_name_lower ON icd9cm_master(LOWER(name));"

# 3. Deploy code
git add .
git commit -m "feat: ICD-9 smart service with database-first approach"
git push origin main

# 4. Restart service
# (your deployment process)

# 5. Run smoke tests
python test_icd9_smart_service.py
python test_complete_icd9_flow.py
```

---

**Ready to implement? Let's go! 🚀**
