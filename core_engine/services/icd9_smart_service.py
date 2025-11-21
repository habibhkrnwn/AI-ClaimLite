"""
ICD-9 Smart Service - Standalone
Database-first approach with AI normalization fallback

Flow:
1. Smart keyword search di database icd9cm_master
2. Jika tidak ada → AI normalization (GPT-4o-mini)
3. Validate AI suggestions dengan database
4. Return results
"""

from sqlalchemy import text
from database_connection import get_db_session
from openai import OpenAI
from dotenv import load_dotenv
import os
from typing import Dict, List, Optional
import json

# Load environment variables
load_dotenv()

# ============================================
# LAZY CLIENT CREATION (Fix for invalid API key)
# ============================================
_openai_client_cache = None

def _get_openai_client():
    """
    Lazy creation of OpenAI client.
    Only creates client when AI normalization is actually needed.
    
    This prevents service crash when:
    - API key is invalid
    - OpenAI not needed (database search success)
    
    Returns:
        OpenAI client instance
    
    Raises:
        ValueError: If API key not found
        Exception: If client creation fails
    """
    global _openai_client_cache
    
    if _openai_client_cache is not None:
        return _openai_client_cache
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment. Please configure .env file.")
    
    try:
        _openai_client_cache = OpenAI(api_key=api_key)
        print("[ICD9] ✅ OpenAI client initialized successfully")
        return _openai_client_cache
    except Exception as e:
        print(f"[ICD9] ❌ OpenAI client initialization failed: {e}")
        raise

# Import smart matcher
try:
    from services.smart_icd_matcher import smart_search_icd9, auto_select_best_match
    SMART_MATCHER_AVAILABLE = True
except ImportError:
    print("[ICD9] Warning: Smart matcher not available")
    SMART_MATCHER_AVAILABLE = False


def exact_search_icd9(procedure_input: str) -> Optional[Dict]:
    """
    Exact search di database icd9cm_master (case-insensitive).
    
    Args:
        procedure_input: Input dari user (bisa Indonesia/English)
    
    Returns:
        {
            "code": "87.44",
            "name": "Routine chest X-ray",
            "source": "database_exact",
            "valid": True,
            "confidence": 100
        } atau None jika tidak ditemukan
    """
    if not procedure_input or procedure_input.strip() == "":
        return None
    
    with get_db_session() as session:
        try:
            query = text("""
                SELECT code, name 
                FROM icd9cm_master 
                WHERE LOWER(name) = LOWER(:input)
                LIMIT 1
            """)
            result = session.execute(query, {"input": procedure_input.strip()}).fetchone()
            
            if result:
                print(f"[ICD9] ✅ Exact match found: {result[1]} ({result[0]})")
                return {
                    "code": result[0],
                    "name": result[1],
                    "source": "database_exact",
                    "valid": True,
                    "confidence": 100
                }
            return None
        except Exception as e:
            print(f"[ICD9] ❌ Database search error: {e}")
            return None


def partial_search_icd9(procedure_input: str, limit: int = 10) -> List[Dict]:
    """
    Partial/fuzzy search di database icd9cm_master.
    Tries multiple search strategies to find best matches.
    
    Args:
        procedure_input: Input dari user
        limit: Max results to return
    
    Returns:
        List of {code, name, source, confidence} sorted by relevance
    """
    if not procedure_input or procedure_input.strip() == "":
        return []
    
    with get_db_session() as session:
        try:
            search_term = procedure_input.strip().lower()
            
            # Strategy 1: Name starts with input (highest relevance)
            query = text("""
                SELECT code, name,
                       CASE 
                           WHEN LOWER(name) LIKE :starts_with THEN 90
                           WHEN LOWER(name) LIKE :contains THEN 70
                           ELSE 50
                       END as confidence
                FROM icd9cm_master 
                WHERE LOWER(name) LIKE :contains
                ORDER BY confidence DESC, LENGTH(name) ASC
                LIMIT :limit
            """)
            
            results = session.execute(query, {
                "starts_with": f"{search_term}%",
                "contains": f"%{search_term}%",
                "limit": limit
            }).fetchall()
            
            if results:
                matches = [
                    {
                        "code": row[0],
                        "name": row[1],
                        "source": "database_partial",
                        "valid": True,
                        "confidence": row[2]
                    }
                    for row in results
                ]
                print(f"[ICD9] 🔍 Found {len(matches)} partial matches for '{procedure_input}'")
                return matches
            
            return []
            
        except Exception as e:
            print(f"[ICD9] ❌ Partial search error: {e}")
            return []


def get_similar_procedures_from_db(procedure_input: str, limit: int = 20) -> List[Dict]:
    """
    Get similar procedures dari database untuk RAG context.
    
    Args:
        procedure_input: Input dari user
        limit: Max results
    
    Returns:
        List of {code, name} dari database
    """
    if not procedure_input or procedure_input.strip() == "":
        return []
    
    with get_db_session() as session:
        try:
            # Extract keywords
            keywords = procedure_input.lower().split()
            
            # Build search condition (ILIKE untuk partial match)
            search_conditions = []
            params = {}
            
            for idx, keyword in enumerate(keywords[:3]):  # Max 3 keywords
                if len(keyword) > 2:  # Skip very short words
                    param_name = f"keyword{idx}"
                    search_conditions.append(f"LOWER(name) LIKE :{param_name}")
                    params[param_name] = f"%{keyword}%"
            
            if not search_conditions:
                # Fallback: return random common procedures
                query = text("SELECT code, name FROM icd9cm_master ORDER BY RANDOM() LIMIT :limit")
                results = session.execute(query, {"limit": limit}).fetchall()
            else:
                # Search dengan keywords
                where_clause = " OR ".join(search_conditions)
                query = text(f"""
                    SELECT code, name 
                    FROM icd9cm_master 
                    WHERE {where_clause}
                    ORDER BY 
                        CASE 
                            WHEN LOWER(name) LIKE :exact THEN 1
                            ELSE 2
                        END,
                        name
                    LIMIT :limit
                """)
                params["exact"] = f"%{procedure_input.lower()}%"
                params["limit"] = limit
                results = session.execute(query, params).fetchall()
            
            procedures = [{"code": row[0], "name": row[1]} for row in results]
            print(f"[ICD9] 📚 Found {len(procedures)} similar procedures in DB for context")
            return procedures
            
        except Exception as e:
            print(f"[ICD9] ⚠️ DB search error: {e}")
            return []


def format_db_context_for_rag(procedures: List[Dict]) -> str:
    """
    Format database procedures untuk RAG prompt.
    
    Args:
        procedures: List of {code, name}
    
    Returns:
        Formatted string untuk prompt
    """
    if not procedures:
        return "No procedures found in database."
    
    lines = []
    for i, proc in enumerate(procedures, 1):
        lines.append(f"{i}. {proc['code']} - {proc['name']}")
    
    return "\n".join(lines)


# =====================================================
# AI PROMPT FOR NORMALIZATION
# =====================================================

PROMPT_NORMALIZE_TO_MEDICAL_TERM = """
You are a medical terminology expert specializing in ICD-9-CM procedure classification.

Your task: Normalize user input to standard medical procedure terminology (English term ONLY).

USER INPUT: "{procedure_input}"

DATABASE CONTEXT (untuk referensi terminologi):
{database_context}

CRITICAL RULES:
1. Return ONLY the core medical procedure term (e.g., "chest x-ray", "ct scan", "injection")
2. DO NOT include specific procedure details
3. DO NOT include ICD-9 codes
4. If input is Indonesian/informal, translate to English medical term
5. Return the GENERAL procedure term for database search
6. Use lowercase

EXAMPLES:
Input: "rontgen thorax" / "rontgen dada" → Output: "chest x-ray"
Input: "ct scan kepala" → Output: "ct scan head"
Input: "suntik antibiotik" → Output: "injection antibiotic"
Input: "nebulizer" → Output: "nebulizer"
Input: "ekg" → Output: "electrocardiogram"
Input: "usg" → Output: "ultrasonography"

OUTPUT FORMAT (JSON):
{{
  "medical_term": "general procedure term in English (lowercase)",
  "confidence": 95,
  "reasoning": "Brief explanation (1 sentence)"
}}

IMPORTANT:
- Return ONLY general term, NOT specific procedure
- Lowercase
- Simple (2-4 words max)
- This term will search database for ALL matching procedures
"""

def ai_normalize_procedure_to_term(procedure_input: str) -> Dict:
    """
    Normalize user input ke medical procedure terminology (NOT specific procedure)
    
    Process:
    1. Get similar procedures dari database (RAG context) untuk referensi
    2. AI normalize input ke general medical term (e.g., "rontgen thorax" → "chest x-ray")
    3. Return medical term untuk database search
    
    Args:
        procedure_input: Input dari user (bisa Indonesia/informal)
    
    Returns:
        Dict: {
            "medical_term": str (e.g., "chest x-ray", "ct scan"),
            "confidence": int,
            "reasoning": str
        }
    """
    if not procedure_input or procedure_input.strip() == "":
        return {"medical_term": "", "confidence": 0, "reasoning": "Empty input"}
    
    print(f"[ICD9_NORMALIZER] Input: {procedure_input}")
    
    # Step 1: Get similar procedures untuk RAG context
    db_samples = get_similar_procedures_from_db(procedure_input, limit=30)
    
    if not db_samples:
        print(f"[ICD9_NORMALIZER] ⚠️ No database context for '{procedure_input}'")
        print(f"[ICD9_NORMALIZER] AI will normalize based on medical knowledge only")
        db_samples = []
    
    # Step 2: Format context
    if db_samples:
        db_context = format_db_context_for_rag(db_samples)
        print(f"[ICD9_NORMALIZER] Using {len(db_samples)} DB samples as context")
    else:
        db_context = (
            "No specific database matches found. "
            "Please suggest standard ICD-9-CM medical procedure terminology based on the input."
        )
        print("[ICD9_NORMALIZER] Using AI medical knowledge (no DB context)")
    
    # Step 3: Call AI with normalization prompt
    prompt = PROMPT_NORMALIZE_TO_MEDICAL_TERM.format(
        procedure_input=procedure_input,
        database_context=db_context
    )
    
    try:
        client = _get_openai_client()
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        print(f"[ICD9_NORMALIZER] AI normalized term: {result.get('medical_term', 'N/A')}")
        
        return result
    
    except Exception as e:
        print(f"[ICD9_NORMALIZER] ❌ Error: {e}")
        return {
            "medical_term": "",
            "confidence": 0,
            "reasoning": f"AI error: {str(e)}",
            "error": "ai_call_failed"
        }


# Legacy function - kept for backward compatibility but deprecated
def normalize_procedure_with_ai(procedure_input: str) -> List[str]:
    """
    DEPRECATED: Use ai_normalize_procedure_to_term() instead
    
    This function is kept for backward compatibility but now uses the new flow.
    Returns empty list to force fallback to new approach.
    """
    print("[ICD9] ⚠️ normalize_procedure_with_ai() is deprecated, use new flow")
    return []  # Force fallback to new approach


def validate_ai_suggestions(ai_suggestions: List[str]) -> List[Dict]:
    """
    Validate AI suggestions dengan exact search di database.
    
    Handles both formats:
    - Clean names: "Routine chest x-ray, so described"
    - With codes: "87.44 - Routine chest x-ray, so described"
    
    Args:
        ai_suggestions: List procedure names dari AI
    
    Returns:
        List of valid matches dengan metadata:
        [
            {"code": "87.44", "name": "Routine chest x-ray, so described", ...},
            {"code": "87.49", "name": "Other chest x-ray", ...}
        ]
    """
    if not ai_suggestions:
        return []
    
    valid_matches = []
    
    with get_db_session() as session:
        try:
            for suggestion in ai_suggestions:
                if not suggestion or suggestion.strip() == "":
                    continue
                
                # Clean suggestion - remove code if present
                cleaned_suggestion = suggestion.strip()
                
                # Check if format is "code - name" (e.g., "87.44 - Routine chest x-ray")
                if " - " in cleaned_suggestion:
                    parts = cleaned_suggestion.split(" - ", 1)
                    if len(parts) == 2:
                        # Extract code and name
                        suggested_code = parts[0].strip()
                        suggested_name = parts[1].strip()
                        
                        # Try exact match with name
                        cleaned_suggestion = suggested_name
                        
                        print(f"[ICD9] 🔍 Cleaned AI suggestion: '{suggested_code} - {suggested_name}' → '{suggested_name}'")
                
                # Exact search di database
                query = text("""
                    SELECT code, name 
                    FROM icd9cm_master 
                    WHERE LOWER(name) = LOWER(:input)
                    LIMIT 1
                """)
                result = session.execute(query, {"input": cleaned_suggestion}).fetchone()
                
                if result:
                    valid_matches.append({
                        "code": result[0],
                        "name": result[1],
                        "source": "ai_validated",
                        "valid": True,
                        "confidence": 95
                    })
                    print(f"[ICD9] ✅ Validated: {result[1]} ({result[0]})")
                else:
                    print(f"[ICD9] ⚠️ AI suggestion not found in DB: '{suggestion}'")
        
        except Exception as e:
            print(f"[ICD9] ❌ Validation error: {e}")
    
    return valid_matches


def lookup_icd9_procedure(procedure_input: str) -> Dict:
    """
    Main orchestrator - Enhanced 4-step flow with SMART MATCHER.
    
    Flow:
        1. Exact search di database
        2. Smart keyword search (NEW!)
        3. Partial/fuzzy search di database
        4. Jika tidak ada → AI normalization
        5. Validate AI suggestions
        6. Return results
    
    Args:
        procedure_input: Input dari user
    
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
    
    print(f"\n[ICD9] 🔍 Looking up: '{procedure_input}'")
    
    # STEP 1: Exact search
    exact_match = exact_search_icd9(procedure_input)
    if exact_match:
        return {
            "status": "success",
            "result": exact_match,
            "suggestions": [],
            "needs_selection": False
        }
    
    # STEP 2: SMART KEYWORD SEARCH (NEW!)
    if SMART_MATCHER_AVAILABLE:
        try:
            print(f"[ICD9] 🔍 No exact match, trying smart keyword search...")
            smart_matches = smart_search_icd9(procedure_input, limit=10)
            
            if smart_matches:
                # Try auto-select best match
                best_match = auto_select_best_match(smart_matches)
                
                if best_match:
                    print(f"[ICD9] ✅ Smart match (auto-selected): {best_match['name']} ({best_match['confidence']}%)")
                    return {
                        "status": "success",
                        "result": best_match,
                        "suggestions": [],
                        "needs_selection": False
                    }
                else:
                    # Multiple matches, high confidence but needs selection
                    print(f"[ICD9] 🔍 Found {len(smart_matches)} smart matches, needs selection")
                    return {
                        "status": "suggestions",
                        "result": None,
                        "suggestions": smart_matches,
                        "needs_selection": True,
                        "message": f"Found {len(smart_matches)} possible matches. Please select:"
                    }
        except Exception as e:
            print(f"[ICD9] ⚠️ Smart matcher failed: {e}")
    
    # STEP 3: Partial/fuzzy search (fallback)
    print(f"[ICD9] 🔍 Trying partial search...")
    partial_matches = partial_search_icd9(procedure_input, limit=10)
    
    if partial_matches:
        if len(partial_matches) == 1:
            # Auto-select if only 1 match
            print(f"[ICD9] ✅ Single partial match (auto-selected): {partial_matches[0]['name']}")
            return {
                "status": "success",
                "result": partial_matches[0],
                "suggestions": [],
                "needs_selection": False
            }
        else:
            # Multiple matches → show to user
            print(f"[ICD9] 🔍 Found {len(partial_matches)} partial matches, needs selection")
            return {
                "status": "suggestions",
                "result": None,
                "suggestions": partial_matches,
                "needs_selection": True,
                "message": f"Found {len(partial_matches)} possible matches. Please select:"
            }
    
    # STEP 4: AI normalization (last resort)
    print(f"[ICD9] 🤖 No matches, using AI normalization...")
    ai_suggestions = normalize_procedure_with_ai(procedure_input)
    
    if not ai_suggestions:
        print(f"[ICD9] ❌ AI could not normalize input")
        return {
            "status": "not_found",
            "result": None,
            "suggestions": [],
            "needs_selection": False,
            "message": "AI could not normalize input. Please rephrase."
        }
    
    # STEP 5: Validate AI suggestions
    valid_matches = validate_ai_suggestions(ai_suggestions)
    
    if len(valid_matches) == 0:
        print(f"[ICD9] ❌ No valid ICD-9 procedures found")
        return {
            "status": "not_found",
            "result": None,
            "suggestions": [],
            "needs_selection": False,
            "message": "No valid ICD-9 procedures found. Please check input."
        }
    elif len(valid_matches) == 1:
        # Auto-select jika hanya 1 match
        print(f"[ICD9] ✅ Single AI match (auto-selected): {valid_matches[0]['name']}")
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


# Helper function untuk backward compatibility (jika ada kode lain yang masih pakai)
def map_icd9_smart(procedure_name: str, **kwargs) -> Dict:
    """
    Backward compatibility wrapper.
    Redirects to lookup_icd9_procedure dan convert format.
    """
    result = lookup_icd9_procedure(procedure_name)
    
    if result["status"] == "success" and result["result"]:
        return {
            "kode": result["result"]["code"],
            "deskripsi": result["result"]["name"],
            "source": result["result"]["source"],
            "valid": result["result"]["valid"],
            "confidence": result["result"]["confidence"]
        }
    elif result["status"] == "suggestions" and result["suggestions"]:
        # Return first suggestion untuk backward compatibility
        first = result["suggestions"][0]
        return {
            "kode": first["code"],
            "deskripsi": first["name"],
            "source": first["source"],
            "valid": first["valid"],
            "confidence": first["confidence"]
        }
    else:
        return {
            "kode": "-",
            "deskripsi": procedure_name,
            "source": "Not Found",
            "valid": False,
            "confidence": 0
        }
