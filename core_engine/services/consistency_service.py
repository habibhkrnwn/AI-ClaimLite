"""
Clinical Consistency Service
Evaluasi konsistensi klinis antara Diagnosis, Tindakan, dan Obat
berdasarkan data PNPK, Clinical Pathway, dan FORNAS
"""

import json
import os
import logging
from typing import Dict, List, Any, Tuple, Set, Optional
import openai
from dotenv import load_dotenv

# Load environment variables early so os.getenv works even if config.py not imported
load_dotenv()
try:
    from rapidfuzz import fuzz
except ImportError:  # Fail-safe if library not present
    fuzz = None

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
    """(Legacy) Simple proportion match used previously."""
    if not expected:
        return 1.0, 0, 0
    if not actual:
        return 0.0, 0, 0
    expected_norm = [item.lower().strip() for item in expected]
    actual_norm = [item.lower().strip() for item in actual]
    matched = 0
    for act in actual_norm:
        for exp in expected_norm:
            if exp in act or act in exp:
                matched += 1
                break
    total_actual = len(actual_norm)
    score = matched / total_actual if total_actual > 0 else 0.0
    return score, matched, total_actual


def _fuzzy_match(candidate: str, pool: Set[str], threshold: int = 85) -> Optional[str]:
    """Return matched item from pool using fuzzy ratio >= threshold, else None."""
    if not pool:
        return None
    if fuzz is None:
        # Fallback exact matching only
        return candidate if candidate in pool else None
    best_item = None
    best_score = 0
    for item in pool:
        score = fuzz.token_set_ratio(candidate, item)
        if score > best_score:
            best_score = score
            best_item = item
    if best_score >= threshold:
        return best_item
    return None


def compute_metrics(expected: List[str], actual: List[str], fuzzy: bool = False) -> Dict[str, Any]:
    """
    Compute precision, recall, F1 along with matched/missing/extra lists.
    If fuzzy=True, use fuzzy matching for actual items against expected.
    """
    expected_set = {e.lower().strip() for e in expected if e}
    actual_norm = [a.lower().strip() for a in actual if a]
    matched: Set[str] = set()
    mapping: Dict[str, str] = {}
    if fuzzy:
        for act in actual_norm:
            m = _fuzzy_match(act, expected_set)
            if m:
                matched.add(m)
                mapping[act] = m
    else:
        for act in actual_norm:
            if act in expected_set:
                matched.add(act)
                mapping[act] = act
    missing = list(expected_set - matched)
    extra = [act for act in actual_norm if act not in mapping]
    precision = (len(matched) / len(actual_norm)) if actual_norm else 0.0
    recall = (len(matched) / len(expected_set)) if expected_set else 1.0  # If no expected → perfect recall semantics
    if precision == 0 and recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "matched_items": sorted(list(matched)),
        "missing_expected": sorted(missing),
        "extra_actual": sorted(extra)
    }


def validate_dx_tx(dx: str, tx_list: List[str]) -> Dict[str, str]:
    """
    Validasi konsistensi Diagnosis (ICD-10) → Tindakan (ICD-9)
    
    Args:
        dx: Kode ICD-10 (e.g., "J18.9")
        tx_list: List kode ICD-9-CM (e.g., ["93.9", "87.44"])
    
    Returns:
        {
            "status": "✅ Sesuai" | "⚠️ Perlu Perhatian" | "❌ Tidak Sesuai",
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
    
    # Jika tidak ada mapping → Informasional, tidak dihitung skor
    if not expected_tx:
        logger.warning(f"[DX→TX] No mapping found for {dx_norm}")
        note = generate_clinical_note(dx, tx_list, [], {"status": "ℹ️ Tidak Ada Referensi"}, 'no_mapping_dx_tx')
        return {
            "status": "ℹ️ Tidak Ada Referensi",
            "score": None,
            "precision": None,
            "recall": None,
            "f1": None,
            "matched_items": [],
            "missing_expected": [],
            "extra_actual": tx_list,
            "source": "ai_only",
            "catatan": note
        }
    
    # Jika tidak ada tindakan actual
    if not tx_list:
        return {
            "status": "❌ Tidak Sesuai",
            "catatan": f"Diagnosis {dx} memerlukan tindakan: {', '.join(expected_tx[:3])}"
        }
    
    metrics = compute_metrics(expected_tx, tx_list, fuzzy=False)
    f1 = metrics["f1"]
    # Status threshold for Dx→Tx
    if f1 >= 0.80:
        status = "✅ Sesuai"
    elif f1 >= 0.60:
        status = "🟡 Cukup Sesuai"
    elif f1 >= 0.40:
        status = "⚠️ Perlu Perhatian"
    else:
        status = "❌ Tidak Sesuai"
    base_note = generate_clinical_note(dx, tx_list, [], {"status": status, "metrics": metrics}, 'dx_tx')
    return {
        "status": status,
        "score": f1,
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": f1,
        "matched_items": metrics["matched_items"],
        "missing_expected": metrics["missing_expected"],
        "extra_actual": metrics["extra_actual"],
        "source": "rule",
        "catatan": base_note
    }


def validate_dx_drug(dx: str, drug_list: List[str]) -> Dict[str, str]:
    """
    Validasi konsistensi Diagnosis → Obat
    
    Args:
        dx: Kode ICD-10 atau nama diagnosis
        drug_list: List nama obat (generic names)
    
    Returns:
        {
            "status": "✅ Sesuai" | "⚠️ Perlu Perhatian" | "❌ Tidak Sesuai",
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
    
    if not expected_drugs:
        logger.warning(f"[DX→DRUG] No mapping found for {dx_norm}")
        note = generate_clinical_note(dx, [], drug_list, {"status": "ℹ️ Tidak Ada Referensi"}, 'no_mapping_dx_drug')
        return {
            "status": "ℹ️ Tidak Ada Referensi",
            "score": None,
            "precision": None,
            "recall": None,
            "f1": None,
            "matched_items": [],
            "missing_expected": [],
            "extra_actual": [normalize_drug_name(d) for d in drug_list],
            "source": "ai_only",
            "catatan": note
        }
    
    # Jika tidak ada obat actual
    if not drug_list:
        return {
            "status": "❌ Tidak Sesuai",
            "catatan": f"Diagnosis {dx} memerlukan terapi: {', '.join(expected_drugs[:3])}"
        }
    
    expected_norm = [normalize_drug_name(d) for d in expected_drugs]
    actual_norm = [normalize_drug_name(d) for d in drug_list]
    metrics = compute_metrics(expected_norm, actual_norm, fuzzy=True)
    f1 = metrics["f1"]
    if f1 >= 0.80:
        status = "✅ Sesuai"
    elif f1 >= 0.60:
        status = "🟡 Cukup Sesuai"
    elif f1 >= 0.40:
        status = "⚠️ Perlu Perhatian"
    else:
        status = "❌ Tidak Sesuai"
    note = generate_clinical_note(dx, [], drug_list, {"status": status, "metrics": metrics}, 'dx_drug')
    return {
        "status": status,
        "score": f1,
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": f1,
        "matched_items": metrics["matched_items"],
        "missing_expected": metrics["missing_expected"],
        "extra_actual": metrics["extra_actual"],
        "source": "rule",
        "catatan": note
    }


def validate_tx_drug(tx_list: List[str], drug_list: List[str]) -> Dict[str, str]:
    """
    Validasi konsistensi Tindakan → Obat
    
    Args:
        tx_list: List kode ICD-9-CM
        drug_list: List nama obat
    
    Returns:
        {
            "status": "✅ Sesuai" | "⚠️ Perlu Perhatian" | "❌ Tidak Sesuai",
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
    
    if not expected_drugs:
        logger.warning(f"[TX→DRUG] No mapping found for procedures: {tx_list}")
        note = generate_clinical_note("", tx_list, drug_list, {"status": "ℹ️ Tidak Ada Referensi"}, 'no_mapping_tx_drug')
        return {
            "status": "ℹ️ Tidak Ada Referensi",
            "score": None,
            "precision": None,
            "recall": None,
            "f1": None,
            "matched_items": [],
            "missing_expected": [],
            "extra_actual": [normalize_drug_name(d) for d in drug_list],
            "source": "ai_only",
            "catatan": note
        }
    
    # Jika tidak ada obat actual
    if not drug_list:
        result = {
            "status": "⚠️ Perlu Perhatian",
            "catatan": f"Tindakan dapat memerlukan obat pendukung: {', '.join(expected_drugs[:3])}"
        }
        result["catatan"] = generate_clinical_note("", tx_list, drug_list, result, 'tx_drug')
        return result
    
    expected_norm = [normalize_drug_name(d) for d in expected_drugs]
    actual_norm = [normalize_drug_name(d) for d in drug_list]
    metrics = compute_metrics(expected_norm, actual_norm, fuzzy=True)
    f1 = metrics["f1"]
    if f1 >= 0.60:
        status = "✅ Sesuai"
    elif f1 >= 0.40:
        status = "🟡 Cukup Sesuai"
    elif f1 >= 0.25:
        status = "⚠️ Perlu Perhatian"
    else:
        status = "❌ Tidak Sesuai"
    note = generate_clinical_note("", tx_list, drug_list, {"status": status, "metrics": metrics}, 'tx_drug')
    return {
        "status": status,
        "score": f1,
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": f1,
        "matched_items": metrics["matched_items"],
        "missing_expected": metrics["missing_expected"],
        "extra_actual": metrics["extra_actual"],
        "source": "rule",
        "catatan": note
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
    
    dx_tx_result = validate_dx_tx(dx, tx_list)
    dx_drug_result = validate_dx_drug(dx, drug_list)
    tx_drug_result = validate_tx_drug(tx_list, drug_list)
    numeric_scores = [r["score"] for r in [dx_tx_result, dx_drug_result, tx_drug_result] if isinstance(r.get("score"), (int, float))]
    if numeric_scores:
        aggregate = round(sum(numeric_scores) / len(numeric_scores), 4)
        if aggregate >= 0.75:
            tingkat = "Tinggi"
        elif aggregate >= 0.50:
            tingkat = "Sedang"
        else:
            tingkat = "Rendah"
    else:
        aggregate = None
        tingkat = "Data Terbatas"
    result = {
        "konsistensi": {
            "dx_tx": dx_tx_result,
            "dx_drug": dx_drug_result,
            "tx_drug": tx_drug_result,
            "tingkat_konsistensi": tingkat,
            "_score": aggregate,
            "_dimensi_dihitung": len(numeric_scores)
        }
    }
    logger.info(f"[CONSISTENCY] Aggregate={aggregate} Level={tingkat}")
    return result


def clear_cache():
    """Clear cached mapping data (for testing/reload)"""
    global _icd10_icd9_map, _diagnosis_obat_map, _tindakan_obat_map
    _icd10_icd9_map = None
    _diagnosis_obat_map = None
    _tindakan_obat_map = None
    logger.info("✓ Mapping cache cleared")


def generate_clinical_note(dx: str, tx_list: List[str], drug_list: List[str], validation_result: Dict[str, Any], validation_type: str) -> str:
    """
    Generate clinical note using OpenAI based on diagnosis, procedures, drugs, and validation results.
    
    Args:
        dx: Diagnosis code
        tx_list: List of procedure codes
        drug_list: List of drug names
        validation_result: Result from validation (status, score, etc.)
        validation_type: Type of validation ('dx_tx', 'dx_drug', 'tx_drug')
    
    Returns:
        Generated clinical note
    """
    try:
        # Get OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.warning("OpenAI API key not found, using fallback note")
            fallback_note = validation_result.get('catatan', 'Catatan tidak tersedia')
            return f"[AI] {fallback_note}"
        
        # Create OpenAI client (for openai>=1.0)
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Prepare prompt based on validation type
        if validation_type == 'dx_tx':
            prompt = f"""
            Berdasarkan diagnosis ICD-10: {dx}
            Tindakan ICD-9 yang dilakukan: {', '.join(tx_list) if tx_list else 'Tidak ada'}
            Hasil validasi: {validation_result['status']}
            
            Berikan catatan klinis yang solutif dan inovatif tentang konsistensi antara diagnosis dan tindakan medis.
            Catatan harus membantu dokter dalam pengambilan keputusan klinis, saran perbaikan jika diperlukan, dan pertimbangan risiko.
            """
        elif validation_type == 'dx_drug':
            prompt = f"""
            Berdasarkan diagnosis ICD-10: {dx}
            Obat yang diberikan: {', '.join(drug_list) if drug_list else 'Tidak ada'}
            Hasil validasi: {validation_result['status']}
            
            Berikan catatan klinis yang solutif dan inovatif tentang konsistensi antara diagnosis dan terapi obat.
            Catatan harus membantu dokter dalam pengambilan keputusan klinis, saran perbaikan jika diperlukan, dan pertimbangan risiko.
            """
        elif validation_type == 'tx_drug':
            prompt = f"""
            Berdasarkan tindakan ICD-9: {', '.join(tx_list) if tx_list else 'Tidak ada'}
            Obat yang diberikan: {', '.join(drug_list) if drug_list else 'Tidak ada'}
            Hasil validasi: {validation_result['status']}
            
            Berikan catatan klinis yang solutif dan inovatif tentang konsistensi antara tindakan medis dan terapi obat.
            Catatan harus membantu dokter dalam pengambilan keputusan klinis, saran perbaikan jika diperlukan, dan pertimbangan risiko.
            """
        elif validation_type.startswith('no_mapping'):
            prompt = f"""
            Tidak tersedia rule mapping khusus.
            Data klinis:
            - Diagnosis: {dx or 'Tidak ada'}
            - Tindakan: {', '.join(tx_list) if tx_list else 'Tidak ada'}
            - Obat: {', '.join(drug_list) if drug_list else 'Tidak ada'}
            Berikan analisis kewajaran kombinasi ini, kemungkinan gap, dan saran verifikasi klinis lanjutan secara ringkas dan fokus.
            """
        else:
            prompt = f"Berikan catatan klinis berdasarkan data yang diberikan."
        
        # Call OpenAI API (new client-based format for openai>=1.0)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Anda adalah asisten medis AI yang memberikan catatan klinis yang akurat, solutif, dan inovatif dalam bahasa Indonesia."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        note = response.choices[0].message.content.strip()
        # Only prefix [AI] for rule-guided validations, not for no_mapping cases
        if validation_type.startswith('no_mapping'):
            final_note = note  # plain
        else:
            final_note = f"[AI] {note}"
        logger.info(f"Generated note for {validation_type}: {final_note[:100]}...")
        return final_note
    
    except Exception as e:
        logger.error(f"Error generating clinical note: {e}")
        return validation_result.get('catatan', 'Catatan tidak dapat dihasilkan')
