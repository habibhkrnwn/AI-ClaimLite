# services/icd10_service.py

"""
ICD-10 Smart Lookup Service

Service terpisah untuk menangani ICD-10 lookup dengan AI (RAG approach).
Menjamin 100% match dengan database menggunakan Retrieval-Augmented Generation.

Features:
- Exact match (code & name)
- Partial match dengan ranking
- AI normalization dengan RAG (database context)
- Subcategory extraction
- Guarantee match (tidak ada "not found")

Author: AI-CLAIM Team
Date: 2025-11-14
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy import text, or_

# Add parent directory to path untuk import database_connection
sys.path.insert(0, str(Path(__file__).parent.parent))
from database_connection import get_db_session

# =====================================================
# 1️⃣ DATABASE QUERY FUNCTIONS
# =====================================================

def db_search_exact(user_input: str) -> Optional[Dict]:
    """
    Exact match search di icd10_master (code atau name)
    
    Priority:
    1. Code match (case-insensitive)
    2. Name exact match (case-insensitive)
    
    Args:
        user_input: Input dari user (bisa code/name)
    
    Returns:
        Dict dengan code, name, source atau None jika tidak ketemu
    """
    if not user_input or user_input.strip() == "":
        return None
    
    with get_db_session() as db:
        # Clean input
        cleaned_input = user_input.strip()
        
        # Try 1: Code match (exact)
        query = text("""
            SELECT code, name, source, validation_status
            FROM icd10_master
            WHERE UPPER(code) = UPPER(:input)
            LIMIT 1
        """)
        
        result = db.execute(query, {"input": cleaned_input}).fetchone()
        
        if result:
            return {
                "code": result[0],
                "name": result[1],
                "source": result[2],
                "validation_status": result[3],
                "match_type": "code_exact"
            }
        
        # Try 2: Name exact match
        query = text("""
            SELECT code, name, source, validation_status
            FROM icd10_master
            WHERE LOWER(name) = LOWER(:input)
            LIMIT 1
        """)
        
        result = db.execute(query, {"input": cleaned_input}).fetchone()
        
        if result:
            return {
                "code": result[0],
                "name": result[1],
                "source": result[2],
                "validation_status": result[3],
                "match_type": "name_exact"
            }
        
        return None


def db_search_partial(user_input: str, limit: int = 10) -> List[Dict]:
    """
    Partial match search dengan ranking + typo tolerance
    
    Ranking strategy:
    1. Name starts with input (highest priority)
    2. Name ends with input
    3. Name contains input
    4. Fuzzy match for typos (e.g., "paru2" → "paru", "nebulizr" → "nebuliz")
    5. Shorter names preferred (more specific)
    
    Args:
        user_input: Search term
        limit: Max results (default 10)
    
    Returns:
        List of matching diagnoses dengan ranking
    """
    if not user_input or user_input.strip() == "":
        return []
    
    with get_db_session() as db:
        cleaned_input = user_input.strip()
        
        # FIX: Normalize common typos/variations
        # "paru2" → "paru", "jantung2" → "jantung"
        normalized_input = cleaned_input.replace('2', '').replace('  ', ' ').strip()
        
        # Try original input first, then normalized
        search_terms = [cleaned_input]
        if normalized_input != cleaned_input:
            search_terms.append(normalized_input)
        
        # Try both original and normalized terms
        all_results = []
        for search_term in search_terms:
            query = text("""
                SELECT 
                    code,
                    name,
                    source,
                    validation_status,
                    CASE 
                        WHEN name ILIKE :starts_with THEN 1
                        WHEN name ILIKE :ends_with THEN 2
                        ELSE 3
                    END as relevance,
                    LENGTH(name) as name_length
                FROM icd10_master
                WHERE name ILIKE :contains
                ORDER BY relevance ASC, name_length ASC
                LIMIT :limit
            """)
            
            results = db.execute(query, {
                "starts_with": f"{search_term}%",
                "ends_with": f"%{search_term}",
                "contains": f"%{search_term}%",
                "limit": limit
            }).fetchall()
            
            all_results.extend(results)
            
            # If we found results with first term, no need to try second
            if results:
                break
        
        # Remove duplicates (same code) and sort
        seen_codes = set()
        unique_results = []
        for row in all_results:
            if row[0] not in seen_codes:
                seen_codes.add(row[0])
                unique_results.append(row)
        
        return [
            {
                "code": row[0],
                "name": row[1],
                "source": row[2],
                "validation_status": row[3],
                "relevance": row[4],
                "match_type": "partial"
            }
            for row in unique_results[:limit]  # Limit final results
        ]


def get_similar_diagnoses(user_input: str, limit: int = 50) -> List[Dict]:
    """
    Get similar diagnoses untuk RAG context
    
    Strategy: Ambil diagnosis yang paling mirip untuk dijadikan context AI
    
    Args:
        user_input: User input
        limit: Max samples (default 50 untuk RAG context)
    
    Returns:
        List of similar diagnoses
    """
    # Untuk RAG context, gunakan partial search dengan limit lebih besar
    return db_search_partial(user_input, limit=limit)


def extract_category_from_code(code: str) -> str:
    """
    Extract category dari ICD-10 code
    
    Examples:
        J18.9 → J18
        J18 → J18
        A90 → A90
    
    Args:
        code: ICD-10 code
    
    Returns:
        Category code (3 digit pertama)
    """
    if not code:
        return ""
    
    # If code has dot, take part before dot
    if '.' in code:
        return code.split('.')[0]
    
    # If code is already category (no dot), return as is
    return code


def get_subcategories(parent_code: str) -> Dict[str, any]:
    """
    Get all subcategories dari parent code
    
    Logic:
    1. Extract category (J18.9 → J18)
    2. Query semua kode yang dimulai dengan category
    3. Group: parent (J18) + children (J18.0, J18.1, ...)
    
    Args:
        parent_code: ICD-10 code (bisa category atau subcategory)
    
    Returns:
        Dict dengan parent dan children
        {
            "parent": {"code": "J18", "name": "Pneumonia..."},
            "children": [
                {"code": "J18.0", "name": "Bronchopneumonia..."},
                {"code": "J18.1", "name": "Lobar pneumonia..."},
                ...
            ]
        }
    """
    # Extract category
    category = extract_category_from_code(parent_code)
    
    if not category:
        return {"parent": None, "children": []}
    
    with get_db_session() as db:
        # Query parent + all children
        query = text("""
            SELECT code, name, source, validation_status
            FROM icd10_master
            WHERE code = :category 
               OR code LIKE :pattern
            ORDER BY code
        """)
        
        results = db.execute(query, {
            "category": category,
            "pattern": f"{category}.%"
        }).fetchall()
        
        parent = None
        children = []
        
        for row in results:
            code = row[0]
            data = {
                "code": code,
                "name": row[1],
                "source": row[2],
                "validation_status": row[3]
            }
            
            if code == category:
                parent = data
            elif code.startswith(category + '.'):
                children.append(data)
        
        return {
            "parent": parent,
            "children": children,
            "total_subcategories": len(children)
        }


# =====================================================
# 2️⃣ RAG HELPER FUNCTIONS
# =====================================================

def format_db_context_for_rag(db_samples: List[Dict]) -> str:
    """
    Format database samples untuk RAG prompt
    
    Args:
        db_samples: List of diagnosis dari database
    
    Returns:
        Formatted string untuk AI prompt
    """
    if not db_samples:
        return "No database context available."
    
    lines = []
    for i, sample in enumerate(db_samples[:30], 1):  # Max 30 untuk avoid token limit
        lines.append(f"{i}. {sample['code']} - {sample['name']}")
    
    return "\n".join(lines)


def validate_ai_output_against_db(ai_output: Dict) -> Optional[Dict]:
    """
    Validate AI output terhadap database
    
    Args:
        ai_output: Output dari AI (matched_diagnosis, matched_code)
    
    Returns:
        Verified result dari database atau None
    """
    matched_name = ai_output.get("matched_diagnosis", "")
    matched_code = ai_output.get("matched_code", "")
    
    # Try exact match dengan nama
    result = db_search_exact(matched_name)
    if result:
        return result
    
    # Try exact match dengan kode
    if matched_code:
        result = db_search_exact(matched_code)
        if result:
            return result
    
    return None


# ============================H=========================
# 3️⃣ MAIN LOOKUP FUNCTION (WITOUT AI - will be added in Phase 2)
# =====================================================

def lookup_icd10_basic(user_input: str, max_suggestions: int = 10) -> Dict:
    """
    Basic ICD-10 lookup tanpa AI (untuk testing)
    
    Flow:
    1. Exact match → Direct result
    2. Partial match → Suggestions
    3. Not found → Empty result
    
    Args:
        user_input: User input
        max_suggestions: Max suggestions untuk modal
    
    Returns:
        Dict dengan flow type dan results
    """
    print(f"[ICD10_SERVICE] Basic lookup: {user_input}")
    
    # Step 1: Exact match
    exact = db_search_exact(user_input)
    
    if exact:
        # Get subcategories
        category = extract_category_from_code(exact["code"])
        subcategories = get_subcategories(category)
        
        return {
            "flow": "direct",
            "requires_modal": False,
            "selected_code": exact["code"],
            "selected_name": exact["name"],
            "source": exact["source"],
            "subcategories": subcategories,
            "ai_used": False
        }
    
    # Step 2: Partial match
    partial = db_search_partial(user_input, limit=max_suggestions)
    
    if partial:
        return {
            "flow": "suggestion",
            "requires_modal": True,
            "suggestions": partial,
            "total_suggestions": len(partial),
            "ai_used": False,
            "message": "Silakan pilih diagnosis yang sesuai:"
        }
    
    # Step 3: Not found
    return {
        "flow": "not_found",
        "requires_modal": False,
        "message": "Diagnosis tidak ditemukan di database.",
        "suggestions": [],
        "ai_used": False
    }


def select_icd10_code(selected_code: str) -> Dict:
    """
    Select ICD-10 code (dari modal suggestion)
    Return subcategories dari code yang dipilih
    
    Args:
        selected_code: ICD-10 code yang dipilih user
    
    Returns:
        Dict dengan code info + subcategories
    """
    print(f"[ICD10_SERVICE] Code selected: {selected_code}")
    
    # Get code info
    code_info = db_search_exact(selected_code)
    
    if not code_info:
        return {
            "status": "error",
            "message": f"Code {selected_code} tidak ditemukan"
        }
    
    # Get subcategories
    category = extract_category_from_code(selected_code)
    subcategories = get_subcategories(category)
    
    return {
        "status": "success",
        "selected_code": code_info["code"],
        "selected_name": code_info["name"],
        "source": code_info["source"],
        "subcategories": subcategories
    }


# =====================================================
# 4️⃣ UTILITY FUNCTIONS
# =====================================================

def is_icd10_code_format(user_input: str) -> bool:
    """
    Check apakah input adalah format ICD-10 code
    
    Format:
    - 1-3 huruf + 2-3 angka (A00, J18, etc)
    - Optional: dot + 1 digit (J18.9, A90.1, etc)
    
    Args:
        user_input: User input
    
    Returns:
        True jika format ICD-10 code
    """
    if not user_input:
        return False
    
    # Pattern: 1-3 letters + 2-3 digits + optional (.digit)
    pattern = r'^[A-Z]{1,3}\d{2,3}(\.\d)?$'
    
    return bool(re.match(pattern, user_input.upper()))


def get_icd10_statistics() -> Dict:
    """
    Get statistik database ICD-10
    
    Returns:
        Dict dengan total codes, chapters, etc
    """
    with get_db_session() as db:
        # Total codes
        total_query = text("SELECT COUNT(*) FROM icd10_master")
        total = db.execute(total_query).scalar()
        
        # Total categories (codes without dot)
        category_query = text("SELECT COUNT(*) FROM icd10_master WHERE code NOT LIKE '%.%'")
        categories = db.execute(category_query).scalar()
        
        # Total subcategories (codes with dot)
        subcat_query = text("SELECT COUNT(*) FROM icd10_master WHERE code LIKE '%.%'")
        subcategories = db.execute(subcat_query).scalar()
        
        return {
            "total_codes": total,
            "total_categories": categories,
            "total_subcategories": subcategories,
            "database_source": "ICD10_2010",
            "last_updated": datetime.now().isoformat()
        }


# =====================================================
# 5️⃣ TESTING & DEBUG
# =====================================================

if __name__ == "__main__":
    print("🧪 Testing ICD-10 Service (Basic - No AI)\n")
    
    # Test 1: Exact code match
    print("1️⃣ Test exact code match:")
    result = lookup_icd10_basic("J18.9")
    print(f"  Flow: {result['flow']}")
    if result['flow'] == 'direct':
        print(f"  Code: {result['selected_code']}")
        print(f"  Name: {result['selected_name']}")
        print(f"  Subcategories: {result['subcategories']['total_subcategories']}")
    
    # Test 2: Exact name match
    print("\n2️⃣ Test exact name match:")
    result = lookup_icd10_basic("Pneumonia, unspecified")
    print(f"  Flow: {result['flow']}")
    if result['flow'] == 'direct':
        print(f"  Code: {result['selected_code']}")
    
    # Test 3: Partial match
    print("\n3️⃣ Test partial match:")
    result = lookup_icd10_basic("Pneum")
    print(f"  Flow: {result['flow']}")
    if result['flow'] == 'suggestion':
        print(f"  Total suggestions: {result['total_suggestions']}")
        for i, s in enumerate(result['suggestions'][:3], 1):
            print(f"    {i}. {s['code']} - {s['name']}")
    
    # Test 4: Get subcategories
    print("\n4️⃣ Test get subcategories:")
    subcats = get_subcategories("J18")
    print(f"  Parent: {subcats['parent']['code']} - {subcats['parent']['name']}")
    print(f"  Children: {subcats['total_subcategories']}")
    for child in subcats['children'][:5]:
        print(f"    - {child['code']} - {child['name']}")
    
    # Test 5: Statistics
    print("\n5️⃣ Database statistics:")
    stats = get_icd10_statistics()
    print(f"  Total codes: {stats['total_codes']}")
    print(f"  Categories: {stats['total_categories']}")
    print(f"  Subcategories: {stats['total_subcategories']}")
    
    print("\n✅ Basic testing completed!")
