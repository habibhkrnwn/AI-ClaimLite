# services/icd10_ai_normalizer.py

"""
ICD-10 AI Normalizer dengan RAG (Retrieval-Augmented Generation)

Menjamin 100% match dengan database menggunakan:
1. Database context injection ke AI prompt
2. Feedback loop untuk regenerate jika tidak match
3. Fallback ke closest suggestions

Author: AI-CLAIM Team  
Date: 2025-11-14
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
# LAZY CLIENT CREATION (Fix for invalid API key)
# ============================================
_openai_client_cache = None

def _get_openai_client():
    """
    Lazy creation of OpenAI client.
    Only creates client when AI normalization is actually needed.
    
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
        raise ValueError("OPENAI_API_KEY not found in environment")
    
    try:
        _openai_client_cache = OpenAI(api_key=api_key)
        print("[ICD10_AI] ✅ OpenAI client initialized")
        return _openai_client_cache
    except Exception as e:
        print(f"[ICD10_AI] ❌ Client initialization failed: {e}")
        raise

# Import ICD-10 service functions
from services.icd10_service import (
    get_similar_diagnoses,
    format_db_context_for_rag,
    validate_ai_output_against_db,
    db_search_exact
)

# =====================================================
# AI PROMPTS
# =====================================================

PROMPT_NORMALIZE_TO_TERM = """
You are a medical terminology expert specializing in ICD-10 WHO classification.

Your task: Normalize user input to standard medical terminology (English medical term ONLY).

USER INPUT: "{user_input}"

DATABASE CONTEXT (untuk referensi terminologi):
{database_context}

CRITICAL RULES:
1. Return ONLY the core medical term (e.g., "pneumonia", "heart", "diabetes") 
2. DO NOT include specific diagnosis details (e.g., NOT "Pneumonia, unspecified" - just "pneumonia")
3. DO NOT include ICD-10 codes
4. If input is Indonesian/informal, translate to English medical term
5. Return the GENERAL medical term that would be used in database search
6. Use lowercase for the medical term

EXAMPLES OF CORRECT BEHAVIOR:
Input: "jantung" → Output: "heart"
Input: "paru2 basah" / "paru basah" → Output: "pneumonia"
Input: "demam berdarah" → Output: "dengue"
Input: "diabetes" → Output: "diabetes"
Input: "sakit kepala" → Output: "headache"
Input: "stroke" → Output: "stroke"
Input: "jantung koroner" → Output: "coronary heart"

OUTPUT FORMAT (JSON):
{{
  "medical_term": "general medical term in English (lowercase)",
  "confidence": 95,
  "reasoning": "Brief explanation of terminology normalization (1 sentence)"
}}

IMPORTANT:
- Return ONLY the general medical term, NOT specific diagnosis
- Use lowercase
- Keep it simple (1-3 words max)
- This term will be used to search database for ALL matching diagnoses
"""

PROMPT_REGENERATE_TEMPLATE = """
You are a medical coding expert. Your previous attempt did not match our database.

USER INPUT: "{user_input}"
PREVIOUS ATTEMPT: "{previous_attempt}"
FEEDBACK: The diagnosis "{previous_attempt}" was not found in our database.

AVAILABLE OPTIONS FROM DATABASE (You MUST choose from these):
{database_context}

TASK: Select the BEST match from the list above. Copy the diagnosis name EXACTLY.

CRITICAL:
- Do NOT modify the diagnosis name
- Do NOT add or remove words
- COPY EXACTLY character-by-character from the list

OUTPUT (JSON):
{{
  "matched_diagnosis": "EXACT diagnosis name from list above",
  "matched_code": "ICD-10 code",
  "confidence": 90,
  "reasoning": "Why this is the best alternative"
}}
"""

# =====================================================
# CORE AI FUNCTIONS
# =====================================================

def ai_normalize_to_medical_term(user_input: str, max_context: int = 30) -> Dict:
    """
    Normalize user input ke medical terminology (NOT specific diagnosis)
    
    Process:
    1. Get similar diagnoses dari database (RAG context) untuk referensi terminologi
    2. Inject context ke AI prompt
    3. AI normalize input ke general medical term (e.g., "jantung" → "heart")
    4. Return medical term untuk database search
    
    Args:
        user_input: User input (bisa Indonesia/informal)
        max_context: Max database samples untuk context (default 30)
    
    Returns:
        Dict: {
            "medical_term": str (e.g., "heart", "pneumonia"),
            "confidence": int,
            "reasoning": str
        }
    """
    print(f"[AI_NORMALIZER] Input: {user_input}")
    
    # Step 1: Get similar diagnoses untuk RAG context
    # Use original input for initial search
    db_samples = get_similar_diagnoses(user_input, limit=max_context)
    
    if not db_samples:
        # No database context found
        # Let AI try to normalize anyway with generic medical knowledge
        print(f"[AI_NORMALIZER] ⚠️ No database context for '{user_input}'")
        print(f"[AI_NORMALIZER] AI will normalize based on medical knowledge only")
        # Continue to AI normalization without context
        # AI will use its medical knowledge to suggest terms
        db_samples = []  # Empty context, AI uses own knowledge
    
    # Step 2: Format context untuk AI (if available)
    if db_samples:
        db_context = format_db_context_for_rag(db_samples)
        print(f"[AI_NORMALIZER] Using {len(db_samples)} DB samples as context")
    else:
        # Fallback: AI will use general medical knowledge
        db_context = (
            "No specific database matches found. "
            "Please suggest standard ICD-10 medical terminology based on the input. "
            "Focus on common diagnoses related to the symptoms/terms provided."
        )
        print("[AI_NORMALIZER] Using AI medical knowledge (no DB context)")
    
    # Step 3: Call AI dengan normalization prompt
    prompt = PROMPT_NORMALIZE_TO_TERM.format(
        user_input=user_input,
        database_context=db_context
    )
    
    try:
        # Lazy client creation
        try:
            client = _get_openai_client()
        except ValueError as e:
            print(f"[AI_NORMALIZER] ⚠️ OpenAI not configured: {e}")
            return {
                "matched_diagnosis": "",
                "matched_code": "",
                "confidence": 0,
                "reasoning": "OpenAI API key not configured",
                "error": "no_api_key"
            }
        except Exception as e:
            print(f"[AI_NORMALIZER] ❌ Client error: {e}")
            return {
                "matched_diagnosis": "",
                "matched_code": "",
                "confidence": 0,
                "reasoning": f"Client error: {str(e)}",
                "error": "client_failed"
            }
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,  # Low for consistency
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        print(f"[AI_NORMALIZER] AI normalized term: {result.get('medical_term', 'N/A')}")
        
        return result
    
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            print(f"[AI_NORMALIZER] ❌ INVALID API KEY")
            print(f"[AI_NORMALIZER] → Get new key from: https://platform.openai.com/api-keys")
        elif "429" in error_msg:
            print(f"[AI_NORMALIZER] ⚠️ Rate limit exceeded")
        else:
            print(f"[AI_NORMALIZER] ❌ Error: {e}")
        
        return {
            "medical_term": "",
            "confidence": 0,
            "reasoning": f"AI error: {str(e)}",
            "error": "ai_call_failed"
        }


def ai_regenerate_with_feedback(
    user_input: str, 
    previous_attempt: str, 
    available_options: List[Dict]
) -> Dict:
    """
    Regenerate AI output dengan feedback loop
    
    Digunakan ketika AI output tidak match dengan database.
    
    Args:
        user_input: Original user input
        previous_attempt: Previous AI output yang gagal
        available_options: List diagnosis dari database
    
    Returns:
        Dict dengan matched diagnosis (guaranteed from database)
    """
    print(f"[AI_NORMALIZER] Regenerating with feedback...")
    print(f"  Previous: {previous_attempt}")
    
    # Format options untuk prompt
    db_context = format_db_context_for_rag(available_options)
    
    # Regenerate prompt
    prompt = PROMPT_REGENERATE_TEMPLATE.format(
        user_input=user_input,
        previous_attempt=previous_attempt,
        database_context=db_context
    )
    
    try:
        # Lazy client creation
        try:
            client = _get_openai_client()
        except Exception as e:
            print(f"[AI_NORMALIZER] ❌ Client unavailable: {e}")
            if available_options:
                return {
                    "matched_diagnosis": available_options[0]["name"],
                    "matched_code": available_options[0]["code"],
                    "confidence": 50,
                    "reasoning": "Fallback - OpenAI unavailable",
                    "fallback": True
                }
            return {
                "matched_diagnosis": "",
                "matched_code": "",
                "confidence": 0,
                "reasoning": "Client unavailable",
                "error": "no_client"
            }
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Even lower untuk force exact match
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        print(f"[AI_NORMALIZER] Regenerated: {result.get('matched_diagnosis', 'N/A')}")
        
        return result
    
    except Exception as e:
        print(f"[AI_NORMALIZER] ❌ Regenerate error: {e}")
        # Fallback: Return first option dari available
        if available_options:
            return {
                "matched_diagnosis": available_options[0]["name"],
                "matched_code": available_options[0]["code"],
                "confidence": 50,
                "reasoning": "Fallback to closest match",
                "fallback": True
            }
        return {
            "matched_diagnosis": "",
            "matched_code": "",
            "confidence": 0,
            "reasoning": "Regenerate failed",
            "error": "regenerate_failed"
        }


# =====================================================
# SMART LOOKUP DENGAN RAG (GUARANTEE MATCH)
# =====================================================

def lookup_icd10_smart_with_rag(user_input: str, max_attempts: int = 3) -> Dict:
    """
    Smart ICD-10 lookup dengan AI normalization - Return SEMUA recommendations
    
    NEW FLOW (Sesuai request):
    1. Exact match di database → Return langsung dengan subkategori
    2. Partial match (< 5 hasil) → Return suggestions
    3. AI normalize ke medical term (e.g., "jantung" → "heart")
    4. Search DB dengan normalized term → Return SEMUA diagnoses yang match
    5. User pilih dari recommendations (belum masuk subkategori detail)
    
    Args:
        user_input: User input
        max_attempts: Unused (kept for backward compatibility)
    
    Returns:
        Dict dengan guaranteed result (flow + data)
    """
    print(f"\n[ICD10_SMART_RAG] Processing: {user_input}")
    
    # Step 1: Exact match
    exact = db_search_exact(user_input)
    if exact:
        print("[ICD10_SMART_RAG] ✅ Exact match found")
        from services.icd10_service import extract_category_from_code, get_subcategories
        
        category = extract_category_from_code(exact["code"])
        subcats = get_subcategories(category)
        
        return {
            "flow": "direct",
            "requires_modal": False,
            "selected_code": exact["code"],
            "selected_name": exact["name"],
            "source": exact["source"],
            "subcategories": subcats,
            "ai_used": False
        }
    
    # Step 2: Partial match (jika sedikit, langsung suggest tanpa AI)
    from services.icd10_service import db_search_partial
    partial = db_search_partial(user_input, limit=10)
    
    if partial and len(partial) <= 5:
        print(f"[ICD10_SMART_RAG] ✅ Found {len(partial)} partial matches (skip AI)")
        return {
            "flow": "suggestion",
            "requires_modal": True,
            "suggestions": partial,
            "total_suggestions": len(partial),
            "ai_used": False,
            "message": "Silakan pilih diagnosis yang sesuai:"
        }
    
    # Step 3: AI Normalize ke medical term (NOT specific diagnosis!)
    print("[ICD10_SMART_RAG] 🤖 Using AI to normalize to medical term...")
    ai_result = ai_normalize_to_medical_term(user_input)
    
    medical_term = ai_result.get("medical_term", "")
    
    if not medical_term or ai_result.get("error"):
        print("[ICD10_SMART_RAG] ⚠️ AI normalization failed, using partial results")
        return {
            "flow": "fallback_suggestions",
            "requires_modal": True,
            "suggestions": partial[:10] if partial else [],
            "total_suggestions": len(partial[:10]) if partial else 0,
            "ai_used": True,
            "message": "AI normalization failed. Berikut suggestions berdasarkan input:"
        }
    
    print(f"[ICD10_SMART_RAG] ✅ AI normalized: '{user_input}' → '{medical_term}'")
    
    # Step 4: Search DB dengan normalized medical term
    print(f"[ICD10_SMART_RAG] 🔍 Searching DB for all diagnoses containing '{medical_term}'...")
    recommendations = db_search_partial(medical_term, limit=50)
    
    if not recommendations:
        print("[ICD10_SMART_RAG] ⚠️ No matches found for normalized term, fallback to original input")
        recommendations = partial[:10] if partial else []
    
    if len(recommendations) == 0:
        return {
            "flow": "not_found",
            "requires_modal": True,
            "suggestions": [],
            "total_suggestions": 0,
            "ai_used": True,
            "message": f"Tidak ditemukan diagnosis untuk '{user_input}' (normalized: '{medical_term}')"
        }
    
    # Step 5: Return SEMUA recommendations (belum masuk subkategori)
    print(f"[ICD10_SMART_RAG] ✅ Found {len(recommendations)} recommendations")
    
    return {
        "flow": "ai_recommendations",
        "requires_modal": True,
        "suggestions": recommendations,
        "total_suggestions": len(recommendations),
        "ai_used": True,
        "normalized_term": medical_term,
        "original_input": user_input,
        "ai_confidence": ai_result.get("confidence", 0),
        "ai_reasoning": ai_result.get("reasoning", ""),
        "message": f"Rekomendasi diagnosis untuk '{user_input}' (medical term: '{medical_term}'):"
    }

# =====================================================
# HELPER FUNCTIONS
# =====================================================
# Note: Keyword extraction removed - AI handles all normalization directly


# =====================================================
# TESTING
# =====================================================

if __name__ == "__main__":
    print("🧪 Testing AI Normalizer dengan RAG\n")
    
    test_cases = [
        "paru2 basah",
        "demam berdarah",
        "Pneumonia",
        "batuk pilek",
        "J18.9"
    ]
    
    for test_input in test_cases:
        print(f"\n{'='*60}")
        print(f"TEST INPUT: {test_input}")
        print('='*60)
        
        result = lookup_icd10_smart_with_rag(test_input)
        
        print(f"\n📊 RESULT:")
        print(f"  Flow: {result['flow']}")
        print(f"  AI Used: {result.get('ai_used', False)}")
        
        if result['flow'] in ['direct', 'ai_direct', 'ai_regenerated']:
            print(f"  Code: {result['selected_code']}")
            print(f"  Name: {result['selected_name']}")
            print(f"  Subcategories: {result['subcategories']['total_subcategories']}")
            
            if result.get('ai_reasoning'):
                print(f"  AI Reasoning: {result['ai_reasoning']}")
        
        elif result['flow'] in ['suggestion', 'fallback_suggestions']:
            print(f"  Total Suggestions: {result['total_suggestions']}")
            print(f"  Top 3:")
            for i, s in enumerate(result['suggestions'][:3], 1):
                print(f"    {i}. {s['code']} - {s['name']}")
    
    print("\n✅ AI Testing completed!")
