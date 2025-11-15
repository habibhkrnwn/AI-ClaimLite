"""
Clinical Consistency Service
Evaluasi konsistensi klinis antara Diagnosis, Tindakan, dan Obat
berdasarkan data PNPK, Clinical Pathway, dan FORNAS
"""

import json
import os
import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

# Path ke file mapping
RULES_DIR = os.path.join(os.path.dirname(__file__), "..", "rules")
ICD10_ICD9_MAP_FILE = os.path.join(RULES_DIR, "icd10_icd9_map.json")
DIAGNOSIS_OBAT_MAP_FILE = os.path.join(RULES_DIR, "diagnosis_obat_map.json")
TINDAKAN_OBAT_MAP_FILE = os.path.join(RULES_DIR, "tindakan_obat_map.json")

# Cache untuk mapping data
_icd10_icd9_map = None
_diagnosis_obat_map = None
_tindakan_obat_map = None


def load_icd10_icd9_map() -> Dict:
    """Load mapping Diagnosis (ICD-10) → Tindakan (ICD-9)"""
    global _icd10_icd9_map
    
    if _icd10_icd9_map is not None:
        return _icd10_icd9_map
    
    try:
        if os.path.exists(ICD10_ICD9_MAP_FILE):
            with open(ICD10_ICD9_MAP_FILE, 'r', encoding='utf-8') as f:
                _icd10_icd9_map = json.load(f)
                logger.info(f"✓ Loaded ICD-10→ICD-9 mapping: {len(_icd10_icd9_map)} diagnoses")
        else:
            logger.warning(f"⚠️ File not found: {ICD10_ICD9_MAP_FILE}")
            _icd10_icd9_map = {}
    except Exception as e:
        logger.error(f"❌ Error loading ICD-10→ICD-9 map: {e}")
        _icd10_icd9_map = {}
    
    return _icd10_icd9_map


def load_diagnosis_obat_map() -> Dict:
    """Load mapping Diagnosis → Obat generik"""
    global _diagnosis_obat_map
    
    if _diagnosis_obat_map is not None:
        return _diagnosis_obat_map
    
    try:
        if os.path.exists(DIAGNOSIS_OBAT_MAP_FILE):
            with open(DIAGNOSIS_OBAT_MAP_FILE, 'r', encoding='utf-8') as f:
                _diagnosis_obat_map = json.load(f)
                logger.info(f"✓ Loaded Diagnosis→Obat mapping: {len(_diagnosis_obat_map)} diagnoses")
        else:
            logger.warning(f"⚠️ File not found: {DIAGNOSIS_OBAT_MAP_FILE}")
            _diagnosis_obat_map = {}
    except Exception as e:
        logger.error(f"❌ Error loading Diagnosis→Obat map: {e}")
        _diagnosis_obat_map = {}
    
    return _diagnosis_obat_map


def load_tindakan_obat_map() -> Dict:
    """Load mapping Tindakan (ICD-9) → Obat terkait"""
    global _tindakan_obat_map
    
    if _tindakan_obat_map is not None:
        return _tindakan_obat_map
    
    try:
        if os.path.exists(TINDAKAN_OBAT_MAP_FILE):
            with open(TINDAKAN_OBAT_MAP_FILE, 'r', encoding='utf-8') as f:
                _tindakan_obat_map = json.load(f)
                logger.info(f"✓ Loaded Tindakan→Obat mapping: {len(_tindakan_obat_map)} procedures")
        else:
            logger.warning(f"⚠️ File not found: {TINDAKAN_OBAT_MAP_FILE}")
            _tindakan_obat_map = {}
    except Exception as e:
        logger.error(f"❌ Error loading Tindakan→Obat map: {e}")
        _tindakan_obat_map = {}
    
    return _tindakan_obat_map


def normalize_icd_code(code: str) -> str:
    """Normalisasi kode ICD untuk matching yang lebih baik"""
    if not code:
        return ""
    
    # Remove whitespace and convert to uppercase
    code = code.strip().upper()
    
    # Handle ICD-10 format (e.g., "J18.9" or "J189")
    if '.' in code:
        # Already has dot
        return code
    else:
        # Try to add dot if it's ICD-10 format
        if len(code) >= 3 and code[0].isalpha():
            return f"{code[:3]}.{code[3:]}" if len(code) > 3 else code
    
    return code


def normalize_drug_name(drug: str) -> str:
    """Normalisasi nama obat untuk matching"""
    if not drug:
        return ""
    
    # Lowercase and remove extra spaces
    drug = drug.lower().strip()
    
    # Remove common suffixes/dosage info
    drug = drug.split('(')[0].strip()  # Remove (1g), (500mg), etc.
    drug = drug.split('[')[0].strip()
    
    # Remove dosage patterns
    import re
    drug = re.sub(r'\d+\s*(mg|g|ml|mcg|iu|%)', '', drug).strip()
    
    return drug


def calculate_match_score(expected: List[str], actual: List[str]) -> Tuple[float, int, int]:
    """
    Hitung skor kesesuaian antara expected dan actual items
    
    Returns:
        (score, matched_actual, total_actual)
        - score: Percentage of ACTUAL items found in EXPECTED (correctness %)
        - matched_actual: Number of actual items matching expected
        - total_actual: Total number of actual items provided
    """
    if not expected:
        # Jika tidak ada expected, anggap sesuai
        return 1.0, 0, 0
    
    if not actual:
        # Ada expected tapi tidak ada actual
        return 0.0, 0, 0
    
    # Normalize both lists
    expected_norm = [item.lower().strip() for item in expected]
    actual_norm = [item.lower().strip() for item in actual]
    
    # Count how many ACTUAL items are found in EXPECTED (correctness check)
    matched = 0
    for act in actual_norm:
        for exp in expected_norm:
            if exp in act or act in exp:
                matched += 1
                break
    
    total_actual = len(actual_norm)
    score = matched / total_actual if total_actual > 0 else 0.0
    
    return score, matched, total_actual
    return score, matched, total_expected


def validate_dx_tx(dx: str, tx_list: List[str]) -> Dict[str, str]:
    """
    Validasi konsistensi Diagnosis (ICD-10) → Tindakan (ICD-9)
    
    Args:
        dx: Kode ICD-10 (e.g., "J18.9")
        tx_list: List kode ICD-9-CM (e.g., ["93.9", "87.44"])
    
    Returns:
        {
            "status": "✅ Sesuai" | "⚠️ Parsial" | "❌ Tidak Sesuai",
            "catatan": "Penjelasan klinis"
        }
    """
    logger.info(f"[DX→TX] Validating: {dx} → {tx_list}")
    
    # Load mapping
    dx_tx_map = load_icd10_icd9_map()
    
    # Normalize diagnosis code
    dx_norm = normalize_icd_code(dx)
    
    # Cari expected tindakan untuk diagnosis ini
    expected_tx = []
    
    # Try exact match first
    if dx_norm in dx_tx_map:
        # Handle both list and dict formats
        if isinstance(dx_tx_map[dx_norm], list):
            expected_tx = dx_tx_map[dx_norm]
        else:
            expected_tx = dx_tx_map[dx_norm].get("tindakan", [])
    else:
        # Try base code (without decimal)
        base_code = dx_norm.split('.')[0]
        if base_code in dx_tx_map:
            if isinstance(dx_tx_map[base_code], list):
                expected_tx = dx_tx_map[base_code]
            else:
                expected_tx = dx_tx_map[base_code].get("tindakan", [])
    
    # Jika tidak ada mapping, return status khusus
    if not expected_tx:
        logger.warning(f"[DX→TX] No mapping found for {dx_norm}")
        return {
            "status": "⚠️ Parsial",
            "catatan": f"Tidak ada aturan khusus tindakan untuk diagnosis {dx}"
        }
    
    # Jika tidak ada tindakan actual
    if not tx_list:
        return {
            "status": "❌ Tidak Sesuai",
            "catatan": f"Diagnosis {dx} memerlukan tindakan: {', '.join(expected_tx[:3])}"
        }
    
    # Calculate match score
    score, matched, total = calculate_match_score(expected_tx, tx_list)
    
    logger.info(f"[DX→TX] Match score: {score:.2f} ({matched}/{total})")
    
    # Determine status based on score
    if score >= 0.8:
        return {
            "status": "✅ Sesuai",
            "catatan": f"Tindakan sesuai dengan protokol diagnosis {dx}"
        }
    elif score >= 0.4:
        return {
            "status": "⚠️ Parsial",
            "catatan": f"Sebagian tindakan sesuai ({matched}/{total}), pertimbangkan: {', '.join([t for t in expected_tx if t not in tx_list][:2])}"
        }
    else:
        return {
            "status": "❌ Tidak Sesuai",
            "catatan": f"Tindakan tidak sesuai protokol. Direkomendasikan: {', '.join(expected_tx[:3])}"
        }


def validate_dx_drug(dx: str, drug_list: List[str]) -> Dict[str, str]:
    """
    Validasi konsistensi Diagnosis → Obat
    
    Args:
        dx: Kode ICD-10 atau nama diagnosis
        drug_list: List nama obat (generic names)
    
    Returns:
        {
            "status": "✅ Sesuai" | "⚠️ Parsial" | "❌ Tidak Sesuai",
            "catatan": "Penjelasan klinis"
        }
    """
    logger.info(f"[DX→DRUG] Validating: {dx} → {drug_list}")
    
    # Load mapping
    dx_drug_map = load_diagnosis_obat_map()
    
    # Normalize diagnosis
    dx_norm = normalize_icd_code(dx)
    
    # Cari expected drugs
    expected_drugs = []
    
    # Try exact match
    if dx_norm in dx_drug_map:
        # Handle both list and dict formats
        if isinstance(dx_drug_map[dx_norm], list):
            expected_drugs = dx_drug_map[dx_norm]
        else:
            expected_drugs = dx_drug_map[dx_norm].get("obat", [])
    else:
        # Try base code
        base_code = dx_norm.split('.')[0]
        if base_code in dx_drug_map:
            if isinstance(dx_drug_map[base_code], list):
                expected_drugs = dx_drug_map[base_code]
            else:
                expected_drugs = dx_drug_map[base_code].get("obat", [])
    
    # Jika tidak ada mapping
    if not expected_drugs:
        logger.warning(f"[DX→DRUG] No mapping found for {dx_norm}")
        return {
            "status": "⚠️ Parsial",
            "catatan": f"Tidak ada aturan khusus obat untuk diagnosis {dx}"
        }
    
    # Jika tidak ada obat actual
    if not drug_list:
        return {
            "status": "❌ Tidak Sesuai",
            "catatan": f"Diagnosis {dx} memerlukan terapi: {', '.join(expected_drugs[:3])}"
        }
    
    # Normalize drug names untuk matching
    expected_norm = [normalize_drug_name(d) for d in expected_drugs]
    actual_norm = [normalize_drug_name(d) for d in drug_list]
    
    # Calculate match score
    score, matched, total = calculate_match_score(expected_norm, actual_norm)
    
    logger.info(f"[DX→DRUG] Match score: {score:.2f} ({matched}/{total})")
    
    # Determine status
    if score >= 0.7:
        return {
            "status": "✅ Sesuai",
            "catatan": f"Terapi obat sesuai dengan protokol diagnosis {dx}"
        }
    elif score >= 0.3:
        missing_drugs = [d for d in expected_drugs if normalize_drug_name(d) not in actual_norm][:2]
        return {
            "status": "⚠️ Parsial",
            "catatan": f"Sebagian terapi sesuai ({matched}/{total}), pertimbangkan: {', '.join(missing_drugs)}"
        }
    else:
        return {
            "status": "❌ Tidak Sesuai",
            "catatan": f"Terapi tidak sesuai protokol. Direkomendasikan: {', '.join(expected_drugs[:3])}"
        }


def validate_tx_drug(tx_list: List[str], drug_list: List[str]) -> Dict[str, str]:
    """
    Validasi konsistensi Tindakan → Obat
    
    Args:
        tx_list: List kode ICD-9-CM
        drug_list: List nama obat
    
    Returns:
        {
            "status": "✅ Sesuai" | "⚠️ Parsial" | "❌ Tidak Sesuai",
            "catatan": "Penjelasan klinis"
        }
    """
    logger.info(f"[TX→DRUG] Validating: {tx_list} → {drug_list}")
    
    # Load mapping
    tx_drug_map = load_tindakan_obat_map()
    
    # Aggregate expected drugs dari semua tindakan
    expected_drugs = []
    
    for tx in tx_list:
        tx_norm = tx.strip().upper()
        if tx_norm in tx_drug_map:
            # Handle both list and dict formats
            if isinstance(tx_drug_map[tx_norm], list):
                expected_drugs.extend(tx_drug_map[tx_norm])
            else:
                tx_drugs = tx_drug_map[tx_norm].get("obat", [])
                expected_drugs.extend(tx_drugs)
    
    # Remove duplicates
    expected_drugs = list(set(expected_drugs))
    
    # Jika tidak ada mapping
    if not expected_drugs:
        logger.warning(f"[TX→DRUG] No mapping found for procedures: {tx_list}")
        return {
            "status": "⚠️ Parsial",
            "catatan": "Tidak ada aturan khusus obat untuk tindakan ini"
        }
    
    # Jika tidak ada obat actual
    if not drug_list:
        return {
            "status": "⚠️ Parsial",
            "catatan": f"Tindakan dapat memerlukan obat pendukung: {', '.join(expected_drugs[:3])}"
        }
    
    # Normalize
    expected_norm = [normalize_drug_name(d) for d in expected_drugs]
    actual_norm = [normalize_drug_name(d) for d in drug_list]
    
    # Calculate match score
    score, matched, total = calculate_match_score(expected_norm, actual_norm)
    
    logger.info(f"[TX→DRUG] Match score: {score:.2f} ({matched}/{total})")
    
    # Determine status (lebih lenient karena tx-drug bukan one-to-one)
    if score >= 0.5 or matched > 0:
        return {
            "status": "✅ Sesuai",
            "catatan": f"Obat pendukung sesuai dengan tindakan yang dilakukan"
        }
    elif score >= 0.2:
        return {
            "status": "⚠️ Parsial",
            "catatan": f"Sebagian obat sesuai tindakan ({matched}/{total})"
        }
    else:
        return {
            "status": "❌ Tidak Sesuai",
            "catatan": f"Obat tidak terkait dengan tindakan. Pertimbangkan: {', '.join(expected_drugs[:2])}"
        }


def analyze_clinical_consistency(
    dx: str,
    tx_list: List[str],
    drug_list: List[str]
) -> Dict[str, Any]:
    """
    Analisis komprehensif konsistensi klinis
    
    Args:
        dx: Kode ICD-10 diagnosis
        tx_list: List kode ICD-9 tindakan
        drug_list: List nama obat generik
    
    Returns:
        {
            "konsistensi": {
                "dx_tx": {"status": "...", "catatan": "..."},
                "dx_drug": {"status": "...", "catatan": "..."},
                "tx_drug": {"status": "...", "catatan": "..."},
                "tingkat_konsistensi": "Tinggi/Sedang/Rendah"
            }
        }
    """
    logger.info(f"[CONSISTENCY] Analyzing: DX={dx}, TX={tx_list}, DRUG={drug_list}")
    
    # Validate each dimension
    dx_tx_result = validate_dx_tx(dx, tx_list)
    dx_drug_result = validate_dx_drug(dx, drug_list)
    tx_drug_result = validate_tx_drug(tx_list, drug_list)
    
    # Calculate overall score
    status_scores = {
        "✅ Sesuai": 1.0,
        "⚠️ Parsial": 0.5,
        "❌ Tidak Sesuai": 0.0
    }
    
    dx_tx_score = status_scores.get(dx_tx_result["status"], 0.0)
    dx_drug_score = status_scores.get(dx_drug_result["status"], 0.0)
    tx_drug_score = status_scores.get(tx_drug_result["status"], 0.0)
    
    total_score = dx_tx_score + dx_drug_score + tx_drug_score
    
    logger.info(f"[CONSISTENCY] Scores: DX→TX={dx_tx_score}, DX→DRUG={dx_drug_score}, TX→DRUG={tx_drug_score}, Total={total_score}")
    
    # Determine overall consistency level
    if total_score >= 2.5:
        tingkat = "Tinggi"
    elif total_score >= 1.5:
        tingkat = "Sedang"
    else:
        tingkat = "Rendah"
    
    result = {
        "konsistensi": {
            "dx_tx": dx_tx_result,
            "dx_drug": dx_drug_result,
            "tx_drug": tx_drug_result,
            "tingkat_konsistensi": tingkat,
            "_score": total_score  # For debugging/monitoring
        }
    }
    
    logger.info(f"[CONSISTENCY] Result: {tingkat} (score={total_score:.2f})")
    
    return result


def clear_cache():
    """Clear cached mapping data (for testing/reload)"""
    global _icd10_icd9_map, _diagnosis_obat_map, _tindakan_obat_map
    _icd10_icd9_map = None
    _diagnosis_obat_map = None
    _tindakan_obat_map = None
    logger.info("✓ Mapping cache cleared")
