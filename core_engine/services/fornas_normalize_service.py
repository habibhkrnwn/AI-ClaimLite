# services/fornas_normalize_service.py

"""
FORNAS Service - UNIFIED (NEW FLOW)

This is the SINGLE source of truth for ALL FORNAS operations.

Features:
1. AI Normalization: English/typo → Indonesian drug name
2. Drug Lookup: Search database (Panel Kiri - drug list)
3. Drug Details: Get sediaan_kekuatan + restriksi (Panel Kanan - details)
4. Validation: Check if drugs exist in FORNAS (for Generate AI Analysis)

IMPORTANT: 
- Database uses Indonesian names (parasetamol, fentanil, morfin, etc.)
- AI normalizes English → Indonesian (ceftriaxone → seftriakson)
- Validation reuses normalization logic (no duplication!)

Functions:
- ai_normalize_to_indonesian(drug_input) → Normalize to Indonesian
- search_drugs_by_name(drug_name) → Search DB for Panel Kiri
- get_drug_details(drug_name) → Get details for Panel Kanan
- validate_drugs_in_fornas(drug_list) → Validate for analysis
- lookup_fornas_smart(drug_input) → Smart lookup with AI fallback

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

# Add parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

# Database imports
from database_connection import SessionLocal
from models import FornasDrug

# =====================================================
# LAZY CLIENT CREATION
# =====================================================
_openai_client_cache = None

def _get_openai_client():
    """Lazy OpenAI client creation"""
    global _openai_client_cache
    
    if _openai_client_cache is not None:
        return _openai_client_cache
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment")
    
    try:
        _openai_client_cache = OpenAI(api_key=api_key)
        print("[FORNAS_AI] ✅ OpenAI client initialized")
        return _openai_client_cache
    except Exception as e:
        print(f"[FORNAS_AI] ❌ Client initialization failed: {e}")
        raise


# =====================================================
# AI PROMPT FOR NORMALIZATION
# =====================================================

PROMPT_NORMALIZE_TO_INDONESIAN = """
You are a pharmaceutical terminology expert specializing in Indonesian drug names (FORNAS database).

Your task: Normalize user input to Indonesian drug name format.

USER INPUT: "{drug_input}"

DATABASE CONTEXT (untuk referensi drug names):
{database_context}

CRITICAL RULES:
1. Return ONLY the general drug name in Indonesian (e.g., "seftriakson", "parasetamol")
2. DO NOT include dosage, strength, or form (e.g., NOT "Seftriakson 1g")
3. DO NOT include brand names
4. If input is English/typo, normalize to proper Indonesian transliteration
5. Return the GENERAL drug name for database search
6. Use lowercase for simplicity

TRANSLITERATION RULES (English → Indonesian):
- "c" before e/i → "s" (ceftriaxone → seftriakson)
- "x" → "ks" (levofloxacin → levofloksasin)
- "ph" → "f" (phenytoin → fenitoin)
- "c" in other positions → "k" (paracetamol → parasetamol)
- Keep common names as-is (metformin → metformin, insulin → insulin)

EXAMPLES:
Input: "ceftriaxone" → Output: "seftriakson"
Input: "paracetamol" → Output: "parasetamol" 
Input: "levofloxacin" → Output: "levofloksasin"
Input: "fentanyl" → Output: "fentanil"
Input: "metformin" → Output: "metformin"
Input: "insulin" → Output: "insulin"
Input: "asetaminofen" → Output: "parasetamol" (common alias)

OUTPUT FORMAT (JSON):
{{
  "indonesian_name": "general drug name in Indonesian (lowercase)",
  "confidence": 95,
  "reasoning": "Brief explanation (1 sentence)"
}}

IMPORTANT:
- Return ONLY general drug name (without dosage/form)
- Lowercase
- Simple (1-2 words max)
- This name will search database for ALL matching drug variants
"""


# =====================================================
# CORE FUNCTIONS
# =====================================================

def get_similar_drugs_from_db(drug_input: str, limit: int = 20) -> List[Dict]:
    """
    Get similar drugs dari database untuk RAG context
    
    Args:
        drug_input: Input dari user
        limit: Max results
    
    Returns:
        List of {obat_name, kode_fornas}
    """
    if not drug_input or drug_input.strip() == "":
        return []
    
    db = SessionLocal()
    try:
        # Search using ILIKE untuk partial match
        results = db.query(FornasDrug).filter(
            FornasDrug.obat_name.ilike(f"%{drug_input}%")
        ).limit(limit).all()
        
        return [
            {
                "obat_name": drug.obat_name,
                "kode_fornas": drug.kode_fornas
            }
            for drug in results
        ]
    finally:
        db.close()


def format_db_context_for_rag(drugs: List[Dict]) -> str:
    """Format database drugs untuk RAG prompt"""
    if not drugs:
        return "No drugs found in database."
    
    lines = []
    for i, drug in enumerate(drugs[:15], 1):  # Limit 15
        lines.append(f"{i}. {drug['obat_name']}")
    
    return "\n".join(lines)


def ai_normalize_to_indonesian(drug_input: str) -> Dict:
    """
    Normalize drug input ke Indonesian name dengan AI
    
    Process:
    1. Get similar drugs dari DB (RAG context)
    2. AI normalize ke Indonesian (e.g., "ceftriaxone" → "seftriakson")
    3. Return Indonesian name untuk DB search
    
    Args:
        drug_input: User input (bisa English/typo)
    
    Returns:
        Dict: {
            "indonesian_name": str,
            "confidence": int,
            "reasoning": str
        }
    """
    if not drug_input or drug_input.strip() == "":
        return {"indonesian_name": "", "confidence": 0, "reasoning": "Empty input"}
    
    print(f"[FORNAS_NORMALIZER] Input: {drug_input}")
    
    # Step 1: Get similar drugs untuk RAG context
    db_samples = get_similar_drugs_from_db(drug_input, limit=20)
    
    if not db_samples:
        print(f"[FORNAS_NORMALIZER] ⚠️ No database context for '{drug_input}'")
        print(f"[FORNAS_NORMALIZER] AI will normalize based on pharmaceutical knowledge only")
        db_samples = []
    
    # Step 2: Format context
    if db_samples:
        db_context = format_db_context_for_rag(db_samples)
        print(f"[FORNAS_NORMALIZER] Using {len(db_samples)} DB samples as context")
    else:
        db_context = (
            "No specific database matches found. "
            "Please suggest standard Indonesian pharmaceutical name based on transliteration rules."
        )
        print("[FORNAS_NORMALIZER] Using AI pharmaceutical knowledge (no DB context)")
    
    # Step 3: Call AI
    prompt = PROMPT_NORMALIZE_TO_INDONESIAN.format(
        drug_input=drug_input,
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
        print(f"[FORNAS_NORMALIZER] AI normalized: '{drug_input}' → '{result.get('indonesian_name', 'N/A')}'")
        
        return result
    
    except Exception as e:
        print(f"[FORNAS_NORMALIZER] ❌ Error: {e}")
        return {
            "indonesian_name": "",
            "confidence": 0,
            "reasoning": f"AI error: {str(e)}",
            "error": "ai_call_failed"
        }


def search_drugs_by_name(drug_name: str, limit: int = 50) -> List[Dict]:
    """
    Search drugs by name (untuk PANEL KIRI)
    
    Returns list of unique drug names (bukan detail sediaan)
    
    Args:
        drug_name: Drug name to search
        limit: Max results
    
    Returns:
        List of Dict with unique drug names + count of variants
    """
    if not drug_name or drug_name.strip() == "":
        return []
    
    db = SessionLocal()
    try:
        # Search for all drugs containing the name
        all_drugs = db.query(FornasDrug).filter(
            FornasDrug.obat_name.ilike(f"%{drug_name}%")
        ).limit(limit).all()
        
        # Group by base drug name (simplified - actual logic may need refinement)
        drug_groups = {}
        for drug in all_drugs:
            base_name = drug.obat_name  # You might want to extract base name better
            
            if base_name not in drug_groups:
                drug_groups[base_name] = {
                    "obat_name": base_name,
                    "kode_fornas": drug.kode_fornas,
                    "kelas_terapi": drug.kelas_terapi,
                    "subkelas_terapi": drug.subkelas_terapi,
                    "variant_count": 0
                }
            
            drug_groups[base_name]["variant_count"] += 1
        
        return list(drug_groups.values())
    
    finally:
        db.close()


def get_drug_details(drug_name: str) -> List[Dict]:
    """
    Get ALL sediaan_kekuatan + restriksi untuk drug tertentu (untuk PANEL KANAN)
    
    Args:
        drug_name: Exact drug name yang dipilih user
    
    Returns:
        List of all variants with sediaan_kekuatan + restriksi_penggunaan
    """
    if not drug_name or drug_name.strip() == "":
        return []
    
    db = SessionLocal()
    try:
        # Get all variants of this drug
        variants = db.query(FornasDrug).filter(
            FornasDrug.obat_name.ilike(f"%{drug_name}%")
        ).all()
        
        return [
            {
                "kode_fornas": v.kode_fornas,
                "obat_name": v.obat_name,
                "sediaan_kekuatan": v.sediaan_kekuatan,
                "restriksi_penggunaan": v.restriksi_penggunaan,
                "kelas_terapi": v.kelas_terapi,
                "subkelas_terapi": v.subkelas_terapi,
                "kemasan_terkecil": v.kemasan_terkecil if hasattr(v, 'kemasan_terkecil') else None
            }
            for v in variants
        ]
    
    finally:
        db.close()


def lookup_fornas_smart(drug_input: str) -> Dict:
    """
    Smart FORNAS lookup - NEW FLOW
    
    Flow:
    1. Exact match → Return drug details directly
    2. Partial match (< 5 results) → Return suggestions
    3. AI normalize ke Indonesian → Search DB → Return recommendations (PANEL KIRI)
    
    Args:
        drug_input: User input
    
    Returns:
        Dict dengan flow type dan data
    """
    print(f"\n[FORNAS_SMART] Processing: {drug_input}")
    
    # Step 1: Exact match
    db = SessionLocal()
    exact = db.query(FornasDrug).filter(
        FornasDrug.obat_name.ilike(drug_input.strip())
    ).first()
    db.close()
    
    if exact:
        print("[FORNAS_SMART] ✅ Exact match found")
        details = get_drug_details(exact.obat_name)
        
        return {
            "flow": "direct",
            "requires_modal": False,
            "selected_drug": exact.obat_name,
            "details": details,
            "ai_used": False
        }
    
    # Step 2: Partial match (jika sedikit, langsung suggest)
    partial = search_drugs_by_name(drug_input, limit=10)
    
    if partial and len(partial) <= 5:
        print(f"[FORNAS_SMART] ✅ Found {len(partial)} partial matches (skip AI)")
        return {
            "flow": "suggestion",
            "requires_modal": True,
            "suggestions": partial,
            "total_suggestions": len(partial),
            "ai_used": False,
            "message": "Silakan pilih obat yang sesuai:"
        }
    
    # Step 3: AI Normalize ke Indonesian
    print("[FORNAS_SMART] 🤖 Using AI to normalize to Indonesian...")
    ai_result = ai_normalize_to_indonesian(drug_input)
    
    indonesian_name = ai_result.get("indonesian_name", "")
    
    if not indonesian_name or ai_result.get("error"):
        print("[FORNAS_SMART] ⚠️ AI normalization failed, using partial results")
        return {
            "flow": "fallback_suggestions",
            "requires_modal": True,
            "suggestions": partial[:10] if partial else [],
            "total_suggestions": len(partial[:10]) if partial else 0,
            "ai_used": True,
            "message": "AI normalization failed. Berikut suggestions:"
        }
    
    print(f"[FORNAS_SMART] ✅ AI normalized: '{drug_input}' → '{indonesian_name}'")
    
    # Step 4: Search DB dengan normalized name
    print(f"[FORNAS_SMART] 🔍 Searching DB for drugs containing '{indonesian_name}'...")
    recommendations = search_drugs_by_name(indonesian_name, limit=50)
    
    if not recommendations:
        print("[FORNAS_SMART] ⚠️ No matches for normalized name, fallback to original")
        recommendations = partial[:10] if partial else []
    
    if len(recommendations) == 0:
        return {
            "flow": "not_found",
            "requires_modal": True,
            "suggestions": [],
            "total_suggestions": 0,
            "ai_used": True,
            "message": f"Tidak ditemukan obat untuk '{drug_input}' (normalized: '{indonesian_name}')"
        }
    
    # Step 5: Return recommendations (PANEL KIRI)
    print(f"[FORNAS_SMART] ✅ Found {len(recommendations)} recommendations")
    
    return {
        "flow": "ai_recommendations",
        "requires_modal": True,
        "suggestions": recommendations,
        "total_suggestions": len(recommendations),
        "ai_used": True,
        "normalized_name": indonesian_name,
        "original_input": drug_input,
        "ai_confidence": ai_result.get("confidence", 0),
        "ai_reasoning": ai_result.get("reasoning", ""),
        "message": f"Rekomendasi obat untuk '{drug_input}' (normalized: '{indonesian_name}'):"
    }


# =====================================================
# VALIDATION FUNCTION (for Generate AI Analysis)
# =====================================================

def validate_drugs_in_fornas(drug_list: List[str]) -> Dict:
    """
    Validate multiple drugs against FORNAS database
    Used in Generate AI Analysis flow
    
    Args:
        drug_list: List of drug names (e.g., ["Ceftriaxone 1g IV", "Paracetamol 500mg"])
    
    Returns:
        {
            "total_obat": 2,
            "sesuai_fornas": 1,
            "tidak_sesuai": 1,
            "validations": [
                {
                    "no": 1,
                    "nama_obat": "Ceftriaxone 1g IV",
                    "status_fornas": "Sesuai",
                    "kode_fornas": "FOR123",
                    "nama_di_fornas": "Seftriakson",
                    "kelas_terapi": "Antibiotik",
                    "catatan_ai": "Obat ditemukan di FORNAS"
                }
            ]
        }
    """
    if not drug_list:
        return {
            "total_obat": 0,
            "sesuai_fornas": 0,
            "tidak_sesuai": 0,
            "validations": []
        }
    
    print(f"[FORNAS_VALIDATION] Validating {len(drug_list)} drugs")
    
    validations = []
    sesuai_count = 0
    tidak_sesuai_count = 0
    
    for idx, drug_input in enumerate(drug_list, start=1):
        # Normalize drug name using AI (reuse existing function)
        ai_result = ai_normalize_to_indonesian(drug_input)
        normalized = ai_result.get("indonesian_name", "").lower().strip()
        
        if not normalized:
            # Fallback: simple normalization
            import re
            normalized = drug_input.lower().strip()
            normalized = re.sub(r'\d+\s*(mg|g|ml|mcg|iu|cc|gr)\b', '', normalized, flags=re.IGNORECASE)
            normalized = re.sub(r'\b(iv|im|sc|po|oral|injeksi|infus|tablet|kapsul|sirup)\b', '', normalized, flags=re.IGNORECASE)
            normalized = re.sub(r'[^a-z0-9\s]', ' ', normalized)
            normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        print(f"[FORNAS_VALIDATION] Drug #{idx}: '{drug_input}' → '{normalized}'")
        
        # Check in database
        db = SessionLocal()
        try:
            # Try exact match
            drug = db.query(FornasDrug).filter(
                FornasDrug.obat_name.ilike(normalized)
            ).first()
            
            # Try partial match if exact not found
            if not drug:
                drug = db.query(FornasDrug).filter(
                    FornasDrug.obat_name.ilike(f"%{normalized}%")
                ).first()
            
            if drug:
                sesuai_count += 1
                validations.append({
                    "no": idx,
                    "nama_obat": drug_input,
                    "status_fornas": "Sesuai",
                    "kode_fornas": drug.kode_fornas,
                    "nama_di_fornas": drug.obat_name,
                    "kelas_terapi": drug.kelas_terapi,
                    "subkelas_terapi": drug.subkelas_terapi,
                    "sediaan_kekuatan": drug.sediaan_kekuatan,
                    "restriksi_penggunaan": drug.restriksi_penggunaan,
                    "sumber_regulasi": drug.sumber_regulasi or "-",
                    "updated_at": drug.updated_at.strftime("%Y-%m-%d %H:%M:%S") if drug.updated_at else "-",
                    "catatan_ai": f"Obat ditemukan di FORNAS (normalized: {normalized})"
                })
            else:
                tidak_sesuai_count += 1
                validations.append({
                    "no": idx,
                    "nama_obat": drug_input,
                    "status_fornas": "Tidak Sesuai",
                    "kode_fornas": None,
                    "nama_di_fornas": None,
                    "kelas_terapi": None,
                    "subkelas_terapi": None,
                    "sediaan_kekuatan": None,
                    "restriksi_penggunaan": None,
                    "sumber_regulasi": None,
                    "updated_at": None,
                    "catatan_ai": f"Obat tidak ditemukan di FORNAS (searched: {normalized})"
                })
        finally:
            db.close()
    
    print(f"[FORNAS_VALIDATION] ✅ Complete: {sesuai_count} sesuai, {tidak_sesuai_count} tidak sesuai")
    
    return {
        "total_obat": len(drug_list),
        "sesuai_fornas": sesuai_count,
        "tidak_sesuai": tidak_sesuai_count,
        "validations": validations
    }


# =====================================================
# TESTING
# =====================================================

if __name__ == "__main__":
    print("🧪 Testing FORNAS Normalization\n")
    
    test_cases = [
        "ceftriaxone",
        "paracetamol",
        "fentanyl",
        "metformin"
    ]
    
    for test_input in test_cases:
        print(f"\n{'='*80}")
        print(f"TEST: '{test_input}'")
        print("="*80)
        
        result = lookup_fornas_smart(test_input)
        
        print(f"\n📊 RESULT:")
        print(f"   Flow: {result.get('flow')}")
        print(f"   AI Used: {result.get('ai_used')}")
        
        if result.get('normalized_name'):
            print(f"   Normalized: '{result['normalized_name']}'")
        
        if result.get('suggestions'):
            print(f"   Found {len(result['suggestions'])} drugs")
            for i, sugg in enumerate(result['suggestions'][:5], 1):
                print(f"   {i}. {sugg['obat_name']} (variants: {sugg.get('variant_count', 1)})")
    
    print("\n✅ Testing completed!")
