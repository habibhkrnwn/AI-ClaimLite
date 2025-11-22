# services/icd9_ai_normalizer.py

"""
ICD-9 AI Normalizer dengan RAG (Retrieval-Augmented Generation)

EXACT COPY of ICD-10 flow, adapted for ICD-9 procedures.

Menjamin akurasi dengan:
1. Database context injection ke AI prompt
2. Feedback loop untuk regenerate jika tidak match
3. Fallback ke closest suggestions

Author: AI-CLAIM Team  
Date: 2025-11-21
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Add parent directory untuk import
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

# ============================================
# LAZY CLIENT CREATION
# ============================================
_openai_client_cache = None

def _get_openai_client():
    """Lazy creation of OpenAI client"""
    global _openai_client_cache
    
    if _openai_client_cache is not None:
        return _openai_client_cache
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment")
    
    try:
        _openai_client_cache = OpenAI(api_key=api_key)
        print("[ICD9_AI] ✅ OpenAI client initialized")
        return _openai_client_cache
    except Exception as e:
        print(f"[ICD9_AI] ❌ Client initialization failed: {e}")
        raise

# Import ICD-9 service functions
from database_connection import get_db_session
from sqlalchemy import text

# =====================================================
# DATABASE HELPER FUNCTIONS
# =====================================================

def get_similar_procedures(procedure_input: str, limit: int = 30) -> List[Dict]:
    """
    Get similar procedures dari database untuk RAG context
    
    Args:
        procedure_input: User input
        limit: Max results
    
    Returns:
        List of {code, name}
    """
    if not procedure_input or procedure_input.strip() == "":
        return []
    
    with get_db_session() as session:
        try:
            search_term = procedure_input.strip().lower()
            
            # Extract keywords
            keywords = search_term.split()
            
            if not keywords:
                # Fallback: random samples
                query = text("SELECT code, name FROM icd9cm_master ORDER BY RANDOM() LIMIT :limit")
                results = session.execute(query, {"limit": limit}).fetchall()
            else:
                # Build OR conditions untuk setiap keyword
                search_conditions = []
                params = {}
                
                for idx, keyword in enumerate(keywords[:5]):
                    if len(keyword) > 2:
                        param_name = f"kw{idx}"
                        search_conditions.append(f"LOWER(name) LIKE :{param_name}")
                        params[param_name] = f"%{keyword}%"
                
                if search_conditions:
                    where_clause = " OR ".join(search_conditions)
                    query = text(f"""
                        SELECT code, name 
                        FROM icd9cm_master 
                        WHERE {where_clause}
                        LIMIT :limit
                    """)
                    params["limit"] = limit
                    results = session.execute(query, params).fetchall()
                else:
                    # Fallback
                    query = text("SELECT code, name FROM icd9cm_master ORDER BY RANDOM() LIMIT :limit")
                    results = session.execute(query, {"limit": limit}).fetchall()
            
            procedures = [{"code": row[0], "name": row[1]} for row in results]
            print(f"[ICD9_AI] 📚 Found {len(procedures)} similar procedures for context")
            return procedures
            
        except Exception as e:
            print(f"[ICD9_AI] ⚠️ DB search error: {e}")
            return []


def format_db_context_for_rag(procedures: List[Dict]) -> str:
    """Format database procedures untuk RAG prompt"""
    if not procedures:
        return "No procedures found in database."
    
    lines = []
    for i, proc in enumerate(procedures, 1):
        lines.append(f"{i}. {proc['code']} - {proc['name']}")
    
    return "\n".join(lines)


def db_search_exact(procedure_input: str) -> Optional[Dict]:
    """
    Exact match search di icd9cm_master
    
    Args:
        procedure_input: User input
    
    Returns:
        Dict dengan code, name, source atau None
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
                print(f"[ICD9_AI] ✅ Exact match: {result[1]} ({result[0]})")
                return {
                    "code": result[0],
                    "name": result[1],
                    "source": "database_exact",
                    "match_type": "exact"
                }
            return None
        except Exception as e:
            print(f"[ICD9_AI] ❌ DB search error: {e}")
            return None


def db_search_partial(procedure_input: str, limit: int = 10) -> List[Dict]:
    """
    Partial match search dengan ranking
    
    Args:
        procedure_input: Search term
        limit: Max results
    
    Returns:
        List of matching procedures dengan ranking
    """
    if not procedure_input or procedure_input.strip() == "":
        return []
    
    with get_db_session() as session:
        try:
            search_term = procedure_input.strip().lower()
            
            query = text("""
                SELECT code, name,
                       CASE 
                           WHEN LOWER(name) = :exact THEN 100
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
                "exact": search_term,
                "starts_with": f"{search_term}%",
                "contains": f"%{search_term}%",
                "limit": limit
            }).fetchall()
            
            if results:
                matches = [
                    {
                        "code": row[0],
                        "name": row[1],
                        "confidence": row[2],
                        "source": "database_partial",
                        "valid": True
                    }
                    for row in results
                ]
                print(f"[ICD9_AI] 🔍 Found {len(matches)} partial matches")
                return matches
            
            return []
            
        except Exception as e:
            print(f"[ICD9_AI] ❌ Partial search error: {e}")
            return []


# =====================================================
# AI PROMPTS (EXACT COPY dari ICD-10)
# =====================================================

PROMPT_NORMALIZE_TO_TERM = """
You are a medical terminology expert specializing in ICD-9-CM procedure classification.

Your task: Normalize user input to standard medical procedure terminology (English term ONLY).

USER INPUT: "{user_input}"

DATABASE CONTEXT (untuk referensi terminologi):
{database_context}

CRITICAL RULES:
1. Return ONLY the core medical procedure term (e.g., "x-ray", "scan", "injection") 
2. DO NOT include specific procedure details (e.g., NOT "Routine chest x-ray" - just "chest x-ray")
3. DO NOT include ICD-9 codes
4. If input is Indonesian/informal/typo, translate to English medical term
5. Return the GENERAL procedure term that would be used in database search
6. Use lowercase for the medical term

EXAMPLES OF CORRECT BEHAVIOR:
Input: "rontgen dada" / "rontgen thorax" → Output: "chest x-ray"
Input: "ct scan kepala" → Output: "ct scan head"
Input: "nebulizr" (typo) → Output: "nebulizer"
Input: "suntik antibiotik" → Output: "injection antibiotic"
Input: "usg" → Output: "ultrasonography"
Input: "ekg" → Output: "electrocardiogram"

OUTPUT FORMAT (JSON):
{{
  "medical_term": "general procedure term in English (lowercase)",
  "confidence": 95,
  "reasoning": "Brief explanation of terminology normalization (1 sentence)"
}}

IMPORTANT:
- Return ONLY the general medical term, NOT specific procedure
- Use lowercase
- Keep it simple (2-4 words max)
- This term will be used to search database for ALL matching procedures
"""

# =====================================================
# CORE AI FUNCTION
# =====================================================

def ai_normalize_to_medical_term(user_input: str, max_context: int = 30) -> Dict:
    """
    Normalize user input ke medical procedure terminology
    
    EXACT COPY of ICD-10 flow
    
    Args:
        user_input: User input (bisa Indonesia/informal/typo)
        max_context: Max database samples (default 30)
    
    Returns:
        Dict: {
            "medical_term": str (e.g., "chest x-ray", "nebulizer"),
            "confidence": int,
            "reasoning": str
        }
    """
    print(f"[ICD9_AI_NORMALIZER] Input: {user_input}")
    
    # Step 1: Get similar procedures untuk RAG context
    db_samples = get_similar_procedures(user_input, limit=max_context)
    
    if not db_samples:
        print(f"[ICD9_AI_NORMALIZER] ⚠️ No database context for '{user_input}'")
        print(f"[ICD9_AI_NORMALIZER] AI will normalize based on medical knowledge only")
        db_samples = []
    
    # Step 2: Format context
    if db_samples:
        db_context = format_db_context_for_rag(db_samples)
        print(f"[ICD9_AI_NORMALIZER] Using {len(db_samples)} DB samples as context")
    else:
        db_context = (
            "No specific database matches found. "
            "Please suggest standard ICD-9-CM procedure terminology based on the input. "
            "Focus on common medical procedures."
        )
        print("[ICD9_AI_NORMALIZER] Using AI medical knowledge (no DB context)")
    
    # Step 3: Call AI
    prompt = PROMPT_NORMALIZE_TO_TERM.format(
        user_input=user_input,
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
        medical_term = result.get("medical_term", "")
        
        print(f"[ICD9_AI_NORMALIZER] ✅ AI normalized: '{user_input}' → '{medical_term}'")
        
        return result
    
    except Exception as e:
        print(f"[ICD9_AI_NORMALIZER] ❌ Error: {e}")
        return {
            "medical_term": "",
            "confidence": 0,
            "reasoning": f"AI error: {str(e)}",
            "error": "ai_call_failed"
        }


# =====================================================
# SMART LOOKUP DENGAN RAG (EXACT COPY dari ICD-10)
# =====================================================

def lookup_icd9_smart_with_rag(user_input: str) -> Dict:
    """
    Smart ICD-9 lookup dengan AI normalization - EXACT COPY of ICD-10 flow
    
    Flow:
    1. Exact match di database → Return langsung
    2. Partial match (≤5 hasil) → Return suggestions
    3. AI normalize ke medical term (e.g., "rontgen dada" → "chest x-ray")
    4. Search DB dengan normalized term → Return SEMUA procedures yang match
    5. User pilih dari recommendations
    
    Args:
        user_input: User input
    
    Returns:
        Dict dengan guaranteed result (flow + data)
    """
    print(f"\n[ICD9_SMART_RAG] Processing: {user_input}")
    
    # Step 1: Exact match
    exact = db_search_exact(user_input)
    if exact:
        print("[ICD9_SMART_RAG] ✅ Exact match found")
        return {
            "flow": "exact",
            "requires_modal": False,
            "status": "success",
            "matched_code": exact["code"],
            "matched_name": exact["name"],
            "source": exact["source"],
            "confidence": 100,
            "ai_used": False
        }
    
    # Step 2: Partial match (jika sedikit, langsung suggest tanpa AI)
    partial = db_search_partial(user_input, limit=10)
    
    if partial and len(partial) <= 5:
        print(f"[ICD9_SMART_RAG] ✅ Found {len(partial)} partial matches (skip AI)")
        return {
            "flow": "partial",
            "requires_modal": True,
            "status": "suggestions",
            "suggestions": partial,
            "total_suggestions": len(partial),
            "ai_used": False,
            "message": "Silakan pilih prosedur yang sesuai:"
        }
    
    # Step 3: AI Normalize ke medical term
    print("[ICD9_SMART_RAG] 🤖 Using AI to normalize to medical term...")
    ai_result = ai_normalize_to_medical_term(user_input)
    
    medical_term = ai_result.get("medical_term", "")
    
    if not medical_term or ai_result.get("error"):
        print("[ICD9_SMART_RAG] ⚠️ AI normalization failed, using partial results")
        return {
            "flow": "partial",
            "requires_modal": True,
            "status": "suggestions",
            "suggestions": partial[:10] if partial else [],
            "total_suggestions": len(partial[:10]) if partial else 0,
            "ai_used": True,
            "normalized_term": user_input,
            "message": "AI normalization failed. Berikut suggestions berdasarkan input:"
        }
    
    print(f"[ICD9_SMART_RAG] ✅ AI normalized: '{user_input}' → '{medical_term}'")
    
    # Step 4: Search DB dengan normalized medical term
    print(f"[ICD9_SMART_RAG] 🔍 Searching DB for all procedures containing '{medical_term}'...")
    recommendations = db_search_partial(medical_term, limit=50)
    
    if not recommendations:
        print("[ICD9_SMART_RAG] ⚠️ No matches for normalized term, fallback to original")
        recommendations = partial[:10] if partial else []
    
    if len(recommendations) == 0:
        return {
            "flow": "not_found",
            "requires_modal": True,
            "status": "not_found",
            "suggestions": [],
            "total_suggestions": 0,
            "ai_used": True,
            "message": f"Tidak ditemukan prosedur untuk '{user_input}' (normalized: '{medical_term}')"
        }
    
    # Step 5: Return SEMUA recommendations
    print(f"[ICD9_SMART_RAG] ✅ Found {len(recommendations)} recommendations")
    
    return {
        "flow": "ai_normalized",
        "requires_modal": True,
        "status": "suggestions",
        "suggestions": recommendations,
        "total_suggestions": len(recommendations),
        "ai_used": True,
        "normalized_term": medical_term,
        "original_input": user_input,
        "ai_confidence": ai_result.get("confidence", 0),
        "ai_reasoning": ai_result.get("reasoning", ""),
        "message": f"Rekomendasi prosedur untuk '{user_input}' (medical term: '{medical_term}'):"
    }
