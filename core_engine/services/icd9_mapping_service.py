# services/icd9_mapping_service.py

import json
from pathlib import Path
from typing import Dict, Optional

# Lazy load untuk performance
_icd9_mapping_cache = None
_indonesian_aliases_cache = None

def load_icd9_mapping() -> dict:
    """
    Load ICD-9 mapping file dengan caching untuk performance.
    File hanya di-load sekali saat pertama kali dibutuhkan.
    """
    global _icd9_mapping_cache
    
    if _icd9_mapping_cache is None:
        mapping_path = Path(__file__).parent.parent / "rules" / "icd9_mapping.json"
        
        try:
            with open(mapping_path, encoding="utf-8") as f:
                _icd9_mapping_cache = json.load(f)
            print(f"[ICD9_MAPPING] ✅ Loaded {len(_icd9_mapping_cache)} ICD-9 codes from mapping file")
        except FileNotFoundError:
            print(f"[ICD9_MAPPING] ❌ File not found: {mapping_path}")
            _icd9_mapping_cache = {}
        except Exception as e:
            print(f"[ICD9_MAPPING] ❌ Error loading file: {e}")
            _icd9_mapping_cache = {}
    
    return _icd9_mapping_cache


def load_indonesian_aliases() -> dict:
    """
    Load Indonesian aliases untuk mapping bahasa Indonesia ke WHO terminology.
    File hanya di-load sekali saat pertama kali dibutuhkan.
    """
    global _indonesian_aliases_cache
    
    if _indonesian_aliases_cache is None:
        aliases_path = Path(__file__).parent.parent / "rules" / "icd9_indonesian_aliases.json"
        
        try:
            with open(aliases_path, encoding="utf-8") as f:
                data = json.load(f)
                # Remove comment keys
                _indonesian_aliases_cache = {k: v for k, v in data.items() if not k.startswith("_")}
            print(f"[ICD9_MAPPING] ✅ Loaded {len(_indonesian_aliases_cache)} Indonesian aliases")
        except FileNotFoundError:
            print(f"[ICD9_MAPPING] ⚠️ Indonesian aliases file not found: {aliases_path}")
            _indonesian_aliases_cache = {}
        except Exception as e:
            print(f"[ICD9_MAPPING] ⚠️ Error loading aliases: {e}")
            _indonesian_aliases_cache = {}
    
    return _indonesian_aliases_cache


def normalize_procedure_name(name: str) -> str:
    """
    Normalize nama prosedur untuk matching yang lebih baik.
    - Lowercase
    - Strip whitespace
    - Remove extra spaces
    """
    if not name:
        return ""
    
    normalized = name.lower().strip()
    # Remove extra spaces
    normalized = " ".join(normalized.split())
    return normalized


def map_icd9_by_name(procedure_name: str, use_fuzzy: bool = True, threshold: int = 85) -> Dict:
    """
    Mapping nama prosedur ke kode ICD-9-CM dengan exact atau fuzzy matching.
    
    Args:
        procedure_name: Nama prosedur (bisa bahasa Indonesia atau English WHO standard)
        use_fuzzy: Gunakan fuzzy matching jika exact match gagal
        threshold: Minimum similarity score untuk fuzzy match (0-100)
    
    Returns:
        dict: {
            "kode": "87.44",
            "deskripsi": "Radiography of chest",
            "source": "WHO Official (Exact/Fuzzy)",
            "valid": True/False,
            "confidence": 100 (untuk exact) atau 85-99 (untuk fuzzy)
        }
    
    Flow:
    1. Normalize input
    2. Check Indonesian aliases (translate to WHO term)
    3. Try exact match
    4. Try fuzzy match (jika use_fuzzy=True)
    5. Return fallback jika tidak ada match
    """
    if not procedure_name or procedure_name.strip() in ["", "-"]:
        return {
            "kode": "-",
            "deskripsi": "No procedure name provided",
            "source": "N/A",
            "valid": False,
            "confidence": 0
        }
    
    # Load mapping data
    mapping_data = load_icd9_mapping()
    
    if not mapping_data:
        return {
            "kode": "-",
            "deskripsi": "Mapping file not available",
            "source": "Error",
            "valid": False,
            "confidence": 0
        }
    
    # Normalize input
    normalized_input = normalize_procedure_name(procedure_name)
    
    # 🔹 CHECK INDONESIAN ALIASES FIRST
    aliases = load_indonesian_aliases()
    translated_name = None
    
    if normalized_input in aliases:
        translated_name = aliases[normalized_input]
        print(f"[ICD9_MAPPING] 🇮🇩 Indonesian alias found: '{procedure_name}' → '{translated_name}'")
        # Use translated name for matching
        normalized_input = normalize_procedure_name(translated_name)
    
    # 1️⃣ EXACT MATCH (case-insensitive)
    for official_name, code in mapping_data.items():
        if normalize_procedure_name(official_name) == normalized_input:
            return {
                "kode": code,
                "deskripsi": official_name,
                "source": "WHO Official (Exact Match)",
                "valid": True,
                "confidence": 100
            }
    
    # 2️⃣ FUZZY MATCH (jika diizinkan)
    if use_fuzzy:
        try:
            from rapidfuzz import fuzz, process
            
            # 2a. Try fuzzy match on Indonesian aliases first (lebih relevan untuk input Indonesia)
            if aliases and not translated_name:  # Only if no exact alias match
                alias_result = process.extractOne(
                    normalize_procedure_name(procedure_name),  # Use original input
                    list(aliases.keys()),
                    scorer=fuzz.token_sort_ratio,
                    score_cutoff=threshold
                )
                
                if alias_result:
                    matched_alias, alias_score, _ = alias_result
                    who_term = aliases[matched_alias]
                    print(f"[ICD9_MAPPING] 🇮🇩 Fuzzy Indonesian alias: '{procedure_name}' → '{matched_alias}' → '{who_term}' (confidence: {alias_score}%)")
                    
                    # Now find the ICD-9 code for this WHO term
                    who_normalized = normalize_procedure_name(who_term)
                    for official_name, code in mapping_data.items():
                        if normalize_procedure_name(official_name) == who_normalized:
                            return {
                                "kode": code,
                                "deskripsi": official_name,
                                "source": "WHO Official (via Indonesian Alias)",
                                "valid": True,
                                "confidence": int(alias_score)
                            }
            
            # 2b. Fuzzy match directly on WHO terms (fallback)
            result = process.extractOne(
                normalized_input,
                [normalize_procedure_name(name) for name in mapping_data.keys()],
                scorer=fuzz.token_sort_ratio,
                score_cutoff=threshold
            )
            
            if result:
                matched_normalized, score, idx = result
                
                # Get original name dari index
                original_names = list(mapping_data.keys())
                matched_original = original_names[idx]
                matched_code = mapping_data[matched_original]
                
                print(f"[ICD9_MAPPING] 🔍 Fuzzy match: '{procedure_name}' → '{matched_original}' (confidence: {score}%)")
                
                return {
                    "kode": matched_code,
                    "deskripsi": matched_original,
                    "source": f"WHO Official (Fuzzy Match)",
                    "valid": True,
                    "confidence": int(score)
                }
        
        except ImportError:
            print("[ICD9_MAPPING] ⚠️ rapidfuzz not installed, skipping fuzzy match")
        except Exception as e:
            print(f"[ICD9_MAPPING] ⚠️ Fuzzy match error: {e}")
    
    # 3️⃣ FALLBACK - Tidak ditemukan
    print(f"[ICD9_MAPPING] ❌ No match found for: '{procedure_name}'")
    return {
        "kode": "-",
        "deskripsi": procedure_name,
        "source": "Not Found in WHO ICD-9-CM",
        "valid": False,
        "confidence": 0
    }


def validate_icd9_code(code: str) -> Dict:
    """
    Validasi kode ICD-9 (reverse lookup: cari kode di values).
    
    Gunakan ini ketika AI sudah memberikan kode ICD-9,
    dan kita ingin validasi apakah kode tersebut ada di mapping resmi.
    
    Args:
        code: Kode ICD-9 dari AI (contoh: "87.44")
    
    Returns:
        dict: Same structure as map_icd9_by_name
    """
    if not code or code.strip() in ["", "-"]:
        return {
            "kode": "-",
            "deskripsi": "No code provided",
            "source": "N/A",
            "valid": False,
            "confidence": 0
        }
    
    # Load mapping data
    mapping_data = load_icd9_mapping()
    
    if not mapping_data:
        return {
            "kode": code,
            "deskripsi": "Mapping file not available",
            "source": "Error",
            "valid": False,
            "confidence": 0
        }
    
    # Reverse search: cari kode di values
    code_normalized = code.strip()
    
    for procedure_name, official_code in mapping_data.items():
        if official_code == code_normalized:
            return {
                "kode": official_code,
                "deskripsi": procedure_name,
                "source": "WHO Official (Code Validated)",
                "valid": True,
                "confidence": 100
            }
    
    # Kode tidak ditemukan
    print(f"[ICD9_MAPPING] ⚠️ Code '{code}' not found in official WHO mapping")
    return {
        "kode": code,
        "deskripsi": "Code not verified in WHO ICD-9-CM",
        "source": "AI Generated (Unverified)",
        "valid": False,
        "confidence": 0
    }


def map_icd9_smart(
    procedure_name: str, 
    ai_code: Optional[str] = None,
    use_fuzzy: bool = True,
    threshold: int = 85
) -> Dict:
    """
    Smart ICD-9 mapping dengan multiple fallback strategies.
    
    Priority:
    1. Exact match by procedure name
    2. Fuzzy match by procedure name (jika use_fuzzy=True)
    3. Validate AI code (jika ai_code provided)
    4. Return AI code with unverified flag
    5. Return empty fallback
    
    Args:
        procedure_name: Nama prosedur dari input/AI
        ai_code: Kode ICD-9 dari AI (optional)
        use_fuzzy: Enable fuzzy matching
        threshold: Minimum fuzzy match score (85-100)
    
    Returns:
        dict: Complete ICD-9 mapping info
    
    Example:
        >>> map_icd9_smart("X-ray Thorax")
        {
            "kode": "87.44",
            "deskripsi": "Radiography of chest",
            "source": "WHO Official (Exact Match)",
            "valid": True,
            "confidence": 100
        }
    """
    # Strategy 1 & 2: Search by name (exact + fuzzy)
    result = map_icd9_by_name(procedure_name, use_fuzzy=use_fuzzy, threshold=threshold)
    
    if result["valid"]:
        return result
    
    # Strategy 3: Validate AI code (jika ada)
    if ai_code and ai_code.strip() and ai_code.strip() != "-":
        validated = validate_icd9_code(ai_code)
        
        if validated["valid"]:
            print(f"[ICD9_MAPPING] ✅ AI code '{ai_code}' validated successfully")
            return validated
        else:
            # AI code tidak valid, tapi kita tetap return
            print(f"[ICD9_MAPPING] ⚠️ AI code '{ai_code}' not found in official mapping")
            return {
                "kode": ai_code,
                "deskripsi": procedure_name,
                "source": "AI Generated (Unverified)",
                "valid": False,
                "confidence": 50  # Partial confidence (ada kode dari AI)
            }
    
    # Strategy 4: Pure fallback
    return {
        "kode": "-",
        "deskripsi": procedure_name,
        "source": "No Match Found",
        "valid": False,
        "confidence": 0
    }
