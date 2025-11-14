"""
ICD-9 Smart Service - Standalone
Database-first approach with AI normalization fallback

Flow:
1. Exact search di database icd9cm_master
2. Jika tidak ada → AI normalization (GPT-4o-mini)
3. Validate AI suggestions dengan database
4. Return results
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
    finally:
        session.close()


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
    
    session = get_db_session()
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
    finally:
        session.close()


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


def normalize_procedure_with_ai(procedure_input: str) -> List[str]:
    """
    AI normalization ke WHO ICD-9-CM terminology dengan RAG context.
    
    Enhanced with:
    - Database context injection (RAG)
    - Better Indonesian term mapping
    - Explicit matching rules
    - Guaranteed database alignment
    
    Args:
        procedure_input: Input dari user (bisa kurang lengkap/Indonesia)
    
    Returns:
        List of procedure names (3-5 items) yang guaranteed ada di database
        Example: ["Routine chest x-ray, so described", "Other chest x-ray"]
    """
    if not procedure_input or procedure_input.strip() == "":
        return []
    
    # Step 1: Get similar procedures dari DB untuk RAG context
    db_samples = get_similar_procedures_from_db(procedure_input, limit=30)
    
    if not db_samples:
        print("[ICD9] ⚠️ No DB samples for context, using generic prompt")
        db_context = "Database not available - suggest common medical procedures."
    else:
        db_context = format_db_context_for_rag(db_samples)
    
    # Step 2: Enhanced RAG prompt
    prompt = f"""You are a medical coding expert specializing in ICD-9-CM procedure classification.

Your task: Normalize user input to match EXACTLY procedures from our ICD-9-CM database.

USER INPUT: "{procedure_input}"

AVAILABLE ICD-9-CM PROCEDURES IN DATABASE (Most Relevant):
{db_context}

CRITICAL RULES:
1. You MUST return procedure names that EXACTLY match entries from the database list above
2. Return ALL CLINICALLY RELEVANT procedures based on user input (no limit on number of suggestions)
3. Handle Indonesian/informal terms correctly:
   - "rontgen" = "x-ray" or "radiography"
   - "rontgen thorax/dada" = "chest x-ray"
   - "suntik" = "injection"
   - "infus" = "infusion" or "venous catheterization"
   - "operasi" = surgical procedures
   - "ct scan" = "computerized axial tomography"
   - "mri" = "magnetic resonance imaging"
   - "nebulizer/nebul" = "nebulization" or "inhalation therapy"
   - "oksigen" = "oxygen therapy"
   - "ventilator" = "mechanical ventilation"
   - "ekg/ecg" = "electrocardiogram"
   - "usg" = "ultrasonography"
   - "endoskopi" = "endoscopy"
   - "cuci darah" = "hemodialysis"
   - "transfusi" = "transfusion"
4. If input is vague (e.g., "x-ray" only), suggest procedures for common body parts (chest, abdomen, extremity)
5. DO NOT create new procedure names - ONLY select from the database list
6. The procedure names in output MUST be EXACT character-by-character copies from database
7. Order by clinical likelihood (most common procedures first)

EXAMPLES OF CORRECT BEHAVIOR:
Input: "rontgen thorax" or "rontgen dada"
→ Look for chest x-ray procedures in database
→ Return: ["Routine chest x-ray, so described", "Other chest x-ray"]

Input: "ct scan kepala"
→ Look for CT procedures in database
→ Return: ["Computerized axial tomography of head", "Other computerized axial tomography"]

Input: "nebulizer"
→ Look for nebulization/inhalation in database
→ Return: ["Non-invasive mechanical ventilation", "Continuous positive airway pressure [CPAP]"]

Input: "suntik antibiotik"
→ Look for injection procedures in database
→ Return: ["Injection of antibiotic", "Injection or infusion of oxazolidinone class of antibiotics"]

INPUT PARSING GUIDELINES:
- Extract body part: thorax/dada → chest, kepala → head, perut → abdomen
- Extract modality: rontgen → x-ray, ct → computerized tomography, usg → ultrasound
- Extract procedure type: suntik → injection, operasi → surgical, pemeriksaan → examination
- Combine intelligently: "rontgen thorax" → "chest x-ray procedures"

OUTPUT FORMAT (JSON only):
{{
  "procedures": [
    "Exact procedure name 1 from database (name ONLY, no code)",
    "Exact procedure name 2 from database (name ONLY, no code)",
    "Exact procedure name 3 from database (name ONLY, no code)",
    "... (return ALL relevant procedures, tidak ada batasan jumlah)"
  ]
}}

WRONG FORMAT EXAMPLES (DO NOT DO THIS):
❌ "87.44 - Routine chest x-ray" (includes code - WRONG!)
❌ "99.21 - Injection of antibiotic" (includes code - WRONG!)

CORRECT FORMAT EXAMPLES:
✅ "Routine chest x-ray, so described" (name only - CORRECT!)
✅ "Injection of antibiotic" (name only - CORRECT!)

IMPORTANT: 
- Return ONLY procedure NAMES (no codes!)
- Copy the procedure names EXACTLY as written in the database list (character-by-character)
- Include all punctuation, commas, brackets, and capitalization exactly as shown
- Return ALL relevant procedures (NO MAXIMUM LIMIT - bisa 3, 5, 10, atau lebih)
- Order by clinical likelihood (most common procedures first)
- If user input is ambiguous, return ALL possible interpretations
- Return ONLY valid JSON, no explanation"""

    try:
        print(f"[ICD9] 🤖 Calling AI normalization with RAG context for: '{procedure_input}'")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fast & cost-effective
            messages=[
                {
                    "role": "system", 
                    "content": "You are a medical coding expert specializing in ICD-9-CM procedure classification. You MUST return procedure names that exactly match the provided database entries. Character-by-character accuracy is critical."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.2,  # Lower temp for better accuracy with RAG
            max_tokens=800  # Increased to allow returning many suggestions (no limit)
        )
        
        content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        data = json.loads(content)
        procedures = data.get("procedures", [])
        
        print(f"[ICD9] ✅ AI with RAG returned {len(procedures)} suggestions: {procedures}")
        return procedures
        
    except json.JSONDecodeError as e:
        print(f"[ICD9] ⚠️ JSON decode error: {e}")
        print(f"[ICD9] Response content: {content}")
        return []
    except Exception as e:
        print(f"[ICD9] ❌ AI normalization error: {e}")
        return []


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
    session = get_db_session()
    
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
    finally:
        session.close()
    
    return valid_matches


def lookup_icd9_procedure(procedure_input: str) -> Dict:
    """
    Main orchestrator - Simple 2-step flow.
    
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
    
    # STEP 2: AI normalization
    print(f"[ICD9] 🤖 No exact match, using AI normalization...")
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
    
    # STEP 3: Validate AI suggestions
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
