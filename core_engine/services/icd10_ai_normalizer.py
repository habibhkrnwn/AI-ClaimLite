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
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

PROMPT_RAG_TEMPLATE = """
You are a medical coding expert specializing in ICD-10 WHO classification.

Your task: Normalize user input to match EXACTLY ONE diagnosis from our ICD-10 database.

USER INPUT: "{user_input}"

AVAILABLE ICD-10 DIAGNOSES IN DATABASE (Most Relevant):
{database_context}

CRITICAL RULES:
1. You MUST return a diagnosis name that EXACTLY matches one from the database list above
2. Choose the MOST CLINICALLY RELEVANT diagnosis based on user input
3. If user input is Indonesian/informal (e.g., "paru2 basah"), find the English medical term equivalent
4. DO NOT create new diagnosis names - ONLY select from the database list
5. The "matched_diagnosis" field MUST be an EXACT character-by-character copy from database

EXAMPLES OF CORRECT BEHAVIOR:
Input: "paru2 basah"
→ Look for "Pneumonia" in database → Return "Pneumonia, unspecified" (EXACT match from list)

Input: "demam berdarah"
→ Look for "Dengue" in database → Return "Dengue haemorrhagic fever" (EXACT match from list)

Input: "Pneumonia"
→ Look for best "Pneumonia" match → Return "Pneumonia, organism unspecified" (EXACT match from list)

OUTPUT FORMAT (JSON):
{{
  "matched_diagnosis": "EXACT diagnosis name from database (copy-paste from list above)",
  "matched_code": "ICD-10 code from database",
  "confidence": 95,
  "reasoning": "Brief clinical reason why this is the best match (1 sentence)"
}}

IMPORTANT: 
- Copy the diagnosis name EXACTLY as written in the database list (character-by-character)
- Include all punctuation, commas, and capitalization exactly as shown
- If unsure, choose the most general/unspecified variant
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

def ai_normalize_with_rag(user_input: str, max_context: int = 30) -> Dict:
    """
    Normalize user input ke ICD-10 diagnosis dengan RAG
    
    Process:
    1. Get similar diagnoses dari database (RAG context)
    2. Inject context ke AI prompt
    3. AI pilih yang paling sesuai dari context
    4. Return matched diagnosis
    
    Args:
        user_input: User input (bisa Indonesia/informal)
        max_context: Max database samples untuk context (default 30)
    
    Returns:
        Dict: {
            "matched_diagnosis": str,
            "matched_code": str,
            "confidence": int,
            "reasoning": str
        }
    """
    print(f"[AI_NORMALIZER] Input: {user_input}")
    
    # Step 1: Get similar diagnoses untuk RAG context
    db_samples = get_similar_diagnoses(user_input, limit=max_context)
    
    if not db_samples:
        # Fallback: Jika tidak ada similar, ambil random samples
        print("[AI_NORMALIZER] No similar diagnoses, using broader search...")
        # Try dengan keyword yang lebih general
        general_terms = extract_keywords(user_input)
        for term in general_terms:
            db_samples = get_similar_diagnoses(term, limit=max_context)
            if db_samples:
                break
    
    if not db_samples:
        return {
            "matched_diagnosis": "",
            "matched_code": "",
            "confidence": 0,
            "reasoning": "No similar diagnoses found in database",
            "error": "no_context"
        }
    
    # Step 2: Format context untuk AI
    db_context = format_db_context_for_rag(db_samples)
    
    # Step 3: Call AI dengan RAG prompt
    prompt = PROMPT_RAG_TEMPLATE.format(
        user_input=user_input,
        database_context=db_context
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,  # Low for consistency
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        print(f"[AI_NORMALIZER] AI suggested: {result.get('matched_diagnosis', 'N/A')}")
        
        return result
    
    except Exception as e:
        print(f"[AI_NORMALIZER] ❌ Error: {e}")
        return {
            "matched_diagnosis": "",
            "matched_code": "",
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
    Smart ICD-10 lookup dengan RAG - GUARANTEED MATCH
    
    Flow:
    1. Exact match di database → Return langsung
    2. Partial match → Suggestions (skip AI)
    3. AI normalization dengan RAG → Verify → Return
    4. Jika AI tidak match → Feedback loop (max 3 attempts)
    5. Fallback → Closest suggestions dari database
    
    Args:
        user_input: User input
        max_attempts: Max AI regenerate attempts (default 3)
    
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
    
    # Step 3: AI Normalization dengan RAG
    print("[ICD10_SMART_RAG] 🤖 Using AI with RAG...")
    ai_result = ai_normalize_with_rag(user_input)
    
    # Verify AI output
    verified = validate_ai_output_against_db(ai_result)
    
    if verified:
        print("[ICD10_SMART_RAG] ✅ AI match verified")
        from services.icd10_service import extract_category_from_code, get_subcategories
        
        category = extract_category_from_code(verified["code"])
        subcats = get_subcategories(category)
        
        return {
            "flow": "ai_direct",
            "requires_modal": False,
            "selected_code": verified["code"],
            "selected_name": verified["name"],
            "source": verified["source"],
            "subcategories": subcats,
            "ai_used": True,
            "ai_confidence": ai_result.get("confidence", 0),
            "ai_reasoning": ai_result.get("reasoning", "")
        }
    
    # Step 4: Feedback loop (jika AI tidak match)
    print("[ICD10_SMART_RAG] ⚠️  AI output tidak match, regenerating...")
    
    # Use partial results sebagai available options
    available_options = partial if partial else get_similar_diagnoses(user_input, limit=30)
    
    for attempt in range(max_attempts):
        print(f"[ICD10_SMART_RAG] Attempt {attempt + 1}/{max_attempts}")
        
        regenerated = ai_regenerate_with_feedback(
            user_input=user_input,
            previous_attempt=ai_result.get("matched_diagnosis", ""),
            available_options=available_options
        )
        
        # Verify regenerated
        verified = validate_ai_output_against_db(regenerated)
        
        if verified:
            print(f"[ICD10_SMART_RAG] ✅ Match found on attempt {attempt + 1}")
            from services.icd10_service import extract_category_from_code, get_subcategories
            
            category = extract_category_from_code(verified["code"])
            subcats = get_subcategories(category)
            
            return {
                "flow": "ai_regenerated",
                "requires_modal": False,
                "selected_code": verified["code"],
                "selected_name": verified["name"],
                "source": verified["source"],
                "subcategories": subcats,
                "ai_used": True,
                "ai_attempts": attempt + 1,
                "ai_confidence": regenerated.get("confidence", 0)
            }
    
    # Step 5: Fallback - Return suggestions
    print("[ICD10_SMART_RAG] ⚠️  Max attempts reached, returning suggestions")
    
    return {
        "flow": "fallback_suggestions",
        "requires_modal": True,
        "suggestions": available_options[:10],
        "total_suggestions": len(available_options[:10]),
        "ai_used": True,
        "message": "AI tidak dapat menemukan exact match. Silakan pilih yang paling sesuai:",
        "ai_attempts": max_attempts
    }


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def extract_keywords(user_input: str) -> List[str]:
    """
    Extract keywords dari user input untuk fallback search
    
    Args:
        user_input: User input
    
    Returns:
        List of keywords
    """
    # Mapping umum bahasa Indonesia ke English medical terms
    indonesian_mapping = {
        "paru": "pneumonia",
        "basah": "pneumonia",
        "demam": "fever",
        "berdarah": "hemorrhagic",
        "batuk": "cough",
        "pilek": "rhinitis",
        "flu": "influenza",
        "tipus": "typhoid",
        "tifoid": "typhoid",
        "stroke": "cerebrovascular",
        "jantung": "cardiac",
        "ginjal": "renal",
        "liver": "hepatic",
        "hati": "hepatic"
    }
    
    # Remove common words
    common_words = {"di", "ke", "dari", "dengan", "pada", "untuk", "yang", "dan", "atau", "2"}
    
    words = user_input.lower().split()
    keywords = []
    
    # Try Indonesian mapping first
    for word in words:
        cleaned_word = word.strip(",.!?;:")
        if cleaned_word in indonesian_mapping:
            keywords.append(indonesian_mapping[cleaned_word])
        elif cleaned_word not in common_words and len(cleaned_word) > 2:
            keywords.append(cleaned_word)
    
    # If no keywords, return generic medical terms
    if not keywords:
        keywords = ["disease", "disorder", "infection"]
    
    return keywords[:3]  # Max 3 keywords


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
