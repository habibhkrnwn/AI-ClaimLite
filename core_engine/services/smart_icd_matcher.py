"""
Smart ICD Matcher - Keyword-based Database Search
Database-first approach untuk guarantee semua hasil dari database

Flow:
1. Extract keywords dari input
2. Search database dengan keywords (fuzzy/partial)
3. Rank results by relevance
4. Return top matches
"""

from sqlalchemy import text
from database_connection import get_db_session
from typing import List, Dict, Optional
import re


def extract_keywords(text: str) -> List[str]:
    """
    Extract meaningful keywords dari medical text
    
    Args:
        text: Medical term (e.g., "heart disease", "chest x-ray")
    
    Returns:
        List of keywords (e.g., ["heart", "disease"])
    """
    if not text:
        return []
    
    # Lowercase and split
    words = text.lower().strip().split()
    
    # Remove stopwords
    stopwords = {
        'the', 'a', 'an', 'of', 'and', 'or', 'in', 'on', 'at', 'to', 'for',
        'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be', 'been',
        'nos', 'not', 'otherwise', 'specified', 'unspecified', 'other'
    }
    
    # Filter keywords (length > 2, not stopword)
    keywords = [w for w in words if len(w) > 2 and w not in stopwords]
    
    return keywords


def smart_search_icd10(
    diagnosis_input: str,
    limit: int = 10,
    min_keyword_match: int = 1
) -> List[Dict]:
    """
    Smart keyword-based ICD-10 search
    
    Strategy:
    1. Extract keywords dari input
    2. Search database WHERE name contains ANY keyword
    3. Rank by number of matched keywords
    4. Return top results
    
    Args:
        diagnosis_input: User input (e.g., "heart disease", "jantung")
        limit: Max results
        min_keyword_match: Minimum keywords yang harus match
    
    Returns:
        List of {code, name, confidence} sorted by relevance
    """
    if not diagnosis_input or diagnosis_input.strip() == "":
        return []
    
    keywords = extract_keywords(diagnosis_input)
    
    if not keywords:
        return []
    
    print(f"[SMART_ICD10] Input: '{diagnosis_input}' → Keywords: {keywords}")
    
    try:
        with get_db_session() as session:
            # Build dynamic query for keyword matching
            # Each keyword gets an OR condition
            keyword_conditions = []
            params = {}
            
            for idx, keyword in enumerate(keywords):
                param_name = f"kw{idx}"
                keyword_conditions.append(f"LOWER(name) LIKE :{param_name}")
                params[param_name] = f"%{keyword}%"
            
            # Build WHERE clause
            where_clause = " OR ".join(keyword_conditions)
            
            # Query dengan ranking berdasarkan keyword matches
            query_str = f"""
                WITH keyword_matches AS (
                    SELECT 
                        code,
                        name,
                        ({' + '.join([f"CASE WHEN LOWER(name) LIKE :kw{i} THEN 1 ELSE 0 END" for i in range(len(keywords))])}) as match_count,
                        CASE 
                            WHEN LOWER(name) = LOWER(:exact_match) THEN 100
                            WHEN LOWER(name) LIKE LOWER(:starts_with) THEN 90
                            ELSE 70
                        END as position_score
                    FROM icd10_master
                    WHERE {where_clause}
                )
                SELECT code, name, 
                       (match_count * 30 + position_score) as confidence
                FROM keyword_matches
                WHERE match_count >= :min_match
                ORDER BY confidence DESC, LENGTH(name) ASC
                LIMIT :limit
            """
            
            params['exact_match'] = diagnosis_input.strip()
            params['starts_with'] = f"{diagnosis_input.strip()}%"
            params['min_match'] = min_keyword_match
            params['limit'] = limit
            
            query = text(query_str)
            results = session.execute(query, params).fetchall()
            
            if results:
                matches = [
                    {
                        "code": row[0],
                        "name": row[1],
                        "confidence": min(int(row[2]), 100),  # Cap at 100
                        "source": "database_smart",
                        "valid": True
                    }
                    for row in results
                ]
                print(f"[SMART_ICD10] ✅ Found {len(matches)} matches (top: {matches[0]['name']} - {matches[0]['confidence']}%)")
                return matches
            
            return []
            
    except Exception as e:
        print(f"[SMART_ICD10] ❌ Search error: {e}")
        import traceback
        print(f"[SMART_ICD10] Traceback: {traceback.format_exc()}")
        return []


def smart_search_icd9(
    procedure_input: str,
    limit: int = 10,
    min_keyword_match: int = 1
) -> List[Dict]:
    """
    Smart keyword-based ICD-9 search
    
    Same strategy as ICD-10 but for procedures
    
    Args:
        procedure_input: User input (e.g., "chest x-ray", "ultrason")
        limit: Max results
        min_keyword_match: Minimum keywords yang harus match
    
    Returns:
        List of {code, name, confidence} sorted by relevance
    """
    if not procedure_input or procedure_input.strip() == "":
        return []
    
    keywords = extract_keywords(procedure_input)
    
    if not keywords:
        return []
    
    print(f"[SMART_ICD9] Input: '{procedure_input}' → Keywords: {keywords}")
    
    try:
        with get_db_session() as session:
            # Build dynamic query for keyword matching
            keyword_conditions = []
            params = {}
            
            for idx, keyword in enumerate(keywords):
                param_name = f"kw{idx}"
                keyword_conditions.append(f"LOWER(name) LIKE :{param_name}")
                params[param_name] = f"%{keyword}%"
            
            # Build WHERE clause
            where_clause = " OR ".join(keyword_conditions)
            
            # Query dengan ranking
            query_str = f"""
                WITH keyword_matches AS (
                    SELECT 
                        code,
                        name,
                        ({' + '.join([f"CASE WHEN LOWER(name) LIKE :kw{i} THEN 1 ELSE 0 END" for i in range(len(keywords))])}) as match_count,
                        CASE 
                            WHEN LOWER(name) = LOWER(:exact_match) THEN 100
                            WHEN LOWER(name) LIKE LOWER(:starts_with) THEN 90
                            ELSE 70
                        END as position_score
                    FROM icd9cm_master
                    WHERE {where_clause}
                )
                SELECT code, name, 
                       (match_count * 30 + position_score) as confidence
                FROM keyword_matches
                WHERE match_count >= :min_match
                ORDER BY confidence DESC, LENGTH(name) ASC
                LIMIT :limit
            """
            
            params['exact_match'] = procedure_input.strip()
            params['starts_with'] = f"{procedure_input.strip()}%"
            params['min_match'] = min_keyword_match
            params['limit'] = limit
            
            query = text(query_str)
            results = session.execute(query, params).fetchall()
            
            if results:
                matches = [
                    {
                        "code": row[0],
                        "name": row[1],
                        "confidence": min(int(row[2]), 100),
                        "source": "database_smart",
                        "valid": True
                    }
                    for row in results
                ]
                print(f"[SMART_ICD9] ✅ Found {len(matches)} matches (top: {matches[0]['name']} - {matches[0]['confidence']}%)")
                return matches
            
            return []
            
    except Exception as e:
        print(f"[SMART_ICD9] ❌ Search error: {e}")
        import traceback
        print(f"[SMART_ICD9] Traceback: {traceback.format_exc()}")
        return []


def auto_select_best_match(matches: List[Dict]) -> Optional[Dict]:
    """
    Auto-select best match if confidence is high enough
    
    Args:
        matches: List of search results with confidence scores
    
    Returns:
        Best match if confidence >= 80, else None (needs user selection)
    """
    if not matches:
        return None
    
    best_match = matches[0]
    
    # Auto-select if confidence >= 80 or significantly better than 2nd
    if best_match['confidence'] >= 80:
        return best_match
    
    if len(matches) > 1:
        second_best = matches[1]
        # If gap between 1st and 2nd is > 20 points, auto-select
        if best_match['confidence'] - second_best['confidence'] > 20:
            return best_match
    
    return None  # Needs user selection


# Testing
if __name__ == "__main__":
    print("=" * 80)
    print("SMART ICD MATCHER TEST")
    print("=" * 80)
    
    # Test ICD-10 search
    test_diagnoses = [
        "heart disease",
        "heart",
        "pneumonia",
        "diabetes",
        "hypertension",
        "jantung",  # Should work if translation happens first
    ]
    
    for diagnosis in test_diagnoses:
        print(f"\n🔍 Searching ICD-10 for: '{diagnosis}'")
        results = smart_search_icd10(diagnosis, limit=5)
        
        if results:
            print(f"✅ Found {len(results)} results:")
            for r in results[:3]:
                print(f"   {r['code']} - {r['name']} ({r['confidence']}%)")
            
            best = auto_select_best_match(results)
            if best:
                print(f"🎯 Auto-selected: {best['code']} - {best['name']}")
            else:
                print("⚠️  Needs user selection (low confidence)")
        else:
            print("❌ No results found")
    
    # Test ICD-9 search
    print("\n" + "=" * 80)
    test_procedures = [
        "chest x-ray",
        "ultrasound",
        "ultrasonography",
        "ct scan",
        "blood test",
    ]
    
    for procedure in test_procedures:
        print(f"\n🔍 Searching ICD-9 for: '{procedure}'")
        results = smart_search_icd9(procedure, limit=5)
        
        if results:
            print(f"✅ Found {len(results)} results:")
            for r in results[:3]:
                print(f"   {r['code']} - {r['name']} ({r['confidence']}%)")
        else:
            print("❌ No results found")
    
    print("\n" + "=" * 80)
