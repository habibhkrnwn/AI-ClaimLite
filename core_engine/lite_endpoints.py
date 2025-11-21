# core_engine/ai_claim_lite_endpoints.py

"""
AI-CLAIM Lite Endpoints
Simplified REST API untuk demo/trial version
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os
from sqlalchemy import text
from collections import OrderedDict
import time

# OpenAI for generating explanations - LAZY INITIALIZATION
try:
    from openai import OpenAI
    import config
    OPENAI_AVAILABLE = bool(config.Config.OPENAI_API_KEY) if hasattr(config, 'Config') else False
    openai_client = None  # Will be created lazily when needed
    
    def _get_openai_client():
        """
        Lazy OpenAI client initialization.
        Only creates client when actually needed (not at import time).
        
        This prevents:
        - Crash if .env not loaded during import
        - False "Incorrect API key" errors from premature initialization
        - Wasted resources if AI features not used
        
        Returns:
            OpenAI client instance
        
        Raises:
            ValueError: If API key missing or invalid
        """
        global openai_client
        
        if openai_client is not None:
            return openai_client
        
        api_key = config.Config.OPENAI_API_KEY if hasattr(config, 'Config') else None
        
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not configured. Please set it in .env file. "
                "Get your key from: https://platform.openai.com/api-keys"
            )
        
        if not api_key.startswith("sk-"):
            raise ValueError(
                f"Invalid OpenAI API key format. Key should start with 'sk-' "
                f"(got: '{api_key[:15]}...')"
            )
        
        try:
            openai_client = OpenAI(api_key=api_key)
            print("[OpenAI] ✓ Client initialized successfully")
            return openai_client
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenAI client: {e}")
    
    print(f"[OpenAI] Lazy initialization ready (key present: {OPENAI_AVAILABLE})")
except ImportError as e:
    print(f"[OpenAI] Module not available: {e}")
    OPENAI_AVAILABLE = False
    openai_client = None
    
    def _get_openai_client():
        raise ImportError("OpenAI library not installed. Run: pip install openai")

# Load ICD-10 common terms mapping
ICD10_COMMON_TERMS = {}
try:
    common_terms_path = os.path.join(os.path.dirname(__file__), 'rules', 'icd10_common_terms.json')
    with open(common_terms_path, 'r', encoding='utf-8') as f:
        ICD10_COMMON_TERMS = json.load(f)
    print(f"[ICD10] Loaded {len(ICD10_COMMON_TERMS)} common terms")
except Exception as e:
    print(f"[ICD10] Warning: Could not load common terms: {e}")

# Load ICD-9 common terms mapping
ICD9_COMMON_TERMS = {}
try:
    icd9_terms_path = os.path.join(os.path.dirname(__file__), 'rules', 'icd9_common_terms.json')
    with open(icd9_terms_path, 'r', encoding='utf-8') as f:
        ICD9_COMMON_TERMS = json.load(f)
    print(f"[ICD9] Loaded {len(ICD9_COMMON_TERMS)} common terms")
except Exception as e:
    print(f"[ICD9] Warning: Could not load common terms: {e}")

# Load ICD-10 explanations mapping
ICD10_EXPLANATIONS = {}
try:
    icd10_exp_path = os.path.join(os.path.dirname(__file__), 'rules', 'icd10_explanations.json')
    with open(icd10_exp_path, 'r', encoding='utf-8') as f:
        ICD10_EXPLANATIONS = json.load(f)
    print(f"[ICD10] Loaded {len(ICD10_EXPLANATIONS)} explanations")
except Exception as e:
    print(f"[ICD10] Warning: Could not load explanations: {e}")

# Load ICD-9 explanations mapping
ICD9_EXPLANATIONS = {}
try:
    icd9_exp_path = os.path.join(os.path.dirname(__file__), 'rules', 'icd9_explanations.json')
    with open(icd9_exp_path, 'r', encoding='utf-8') as f:
        ICD9_EXPLANATIONS = json.load(f)
    print(f"[ICD9] Loaded {len(ICD9_EXPLANATIONS)} explanations")
except Exception as e:
    print(f"[ICD9] Warning: Could not load explanations: {e}")

# ============================================================
# 🤖 AI EXPLANATION GENERATOR
# ============================================================
def generate_medical_explanation(code: str, name: str, code_type: str = "ICD-10") -> str:
    """
    Generate penjelasan singkat berbahasa Indonesia untuk kode ICD
    
    Args:
        code: Kode ICD (e.g., "A92.0" atau "88.76")
        name: Nama diagnosis/prosedur
        code_type: "ICD-10" atau "ICD-9"
    
    Returns:
        Penjelasan singkat dalam bahasa Indonesia
    """
    # Validasi input minimal
    if not code or not name:
        return ""

    # Jika OpenAI tidak tersedia, langsung fallback
    if not OPENAI_AVAILABLE or not openai_client:
        return ""

    try:
        prompt = f"""Buatkan penjelasan singkat dalam bahasa Indonesia (maksimal 15 kata) untuk kode medis berikut:

Kode: {code}
Nama: {name}
Tipe: {code_type}

Penjelasan harus:
- Singkat dan jelas (maksimal 15 kata)
- Menjelaskan apa itu penyakit/prosedur tersebut
- Menyebutkan penyebab, gejala, atau cara prosedur dilakukan
- Menggunakan bahasa awam yang mudah dipahami
- Tanpa prefix seperti "Penjelasan:" atau "Keterangan:"

Contoh:
- Chikungunya virus disease → Penyakit virus menular dari gigitan nyamuk Aedes, menyebabkan demam dan nyeri sendi
- Appendectomy → Operasi pengangkatan usus buntu yang meradang atau terinfeksi

Penjelasan:"""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Anda adalah ahli medis yang menjelaskan istilah medis dalam bahasa Indonesia yang mudah dipahami.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.3,
        )

        explanation = response.choices[0].message.content.strip()
        # Bersihkan karakter pembuka/penutup yang tidak perlu
        explanation = explanation.strip().strip('"').strip("'")
        return explanation

    except Exception as e:
        print(f"[AI_EXPLANATION] Error generating explanation for {code}: {e}")
        return ""


# Cache untuk explanation agar tidak perlu generate ulang
_explanation_cache = {}

def get_cached_explanation(code: str, name: str, code_type: str = "ICD-10") -> str:
    """Get explanation from cache or generate new one"""
    cache_key = f"{code_type}:{code}"
    
    if cache_key not in _explanation_cache:
        _explanation_cache[cache_key] = generate_medical_explanation(code, name, code_type)
    
    return _explanation_cache[cache_key]

# Import AI-CLAIM Lite service
from services.lite_service import (
    analyze_lite_single,
    analyze_lite_batch,
    parse_free_text,
    save_to_history,
    load_from_history,
    get_history_list
)

# ============================================================
# 🚀 SIMPLE IN-MEMORY LRU CACHE FOR FAST HIERARCHY LOOKUPS
# ============================================================
class LRUCache:
    def __init__(self, capacity: int = 512, ttl_seconds: int = 6 * 60 * 60):
        self.capacity = capacity
        self.ttl = ttl_seconds
        self.store: "OrderedDict[str, tuple[float, Any]]" = OrderedDict()

    def _now(self) -> float:
        return time.time()

    def get(self, key: str):
        if key in self.store:
            ts, val = self.store[key]
            if self._now() - ts < self.ttl:
                # move to end (most recently used)
                self.store.move_to_end(key)
                return val
            # expired
            del self.store[key]
        return None

    def set(self, key: str, value: Any):
        self.store[key] = (self._now(), value)
        self.store.move_to_end(key)
        if len(self.store) > self.capacity:
            # pop least recently used
            self.store.popitem(last=False)


# Caches for hierarchy endpoints
ICD10_HIERARCHY_CACHE = LRUCache(capacity=512, ttl_seconds=12 * 60 * 60)
ICD9_HIERARCHY_CACHE = LRUCache(capacity=512, ttl_seconds=12 * 60 * 60)

# ============================================================
# 🔹 IMPORT ALL SMART SERVICES (MERGED)
# ============================================================
from services.lite_service_optimized import analyze_lite_single_optimized
from services.lite_service_ultra_fast import analyze_lite_single_ultra_fast, get_cache_stats, clear_analysis_cache
from services.fornas_smart_service import validate_fornas
from services.icd10_ai_normalizer import lookup_icd10_smart_with_rag
from services.icd10_service import select_icd10_code, get_icd10_statistics, lookup_icd10_basic, db_search_partial
from services.icd9_smart_service import lookup_icd9_procedure
from services.dokumen_wajib_service import get_dokumen_wajib_service

# ============================================================
# 📋 MEDICAL PROCEDURE SYNONYM MAPPING (OPTIMIZED - MODULE LEVEL)
# ============================================================
# Centralized synonym dictionary for medical procedures
# Maps variations/synonyms to standardized database terms
# Format: {synonym: [preferred_term, alternative1, alternative2]}

# Common medication terms that are NOT procedures (for validation)
MEDICATION_TERMS = {
    'antibiotic', 'antibiotik', 'amoxicillin', 'amoxilin', 'ceftriaxone', 
    'paracetamol', 'ibuprofen', 'aspirin', 'metformin', 'insulin',
    'antiviral', 'antifungal', 'analgesic', 'analgetik', 'obat',
    'tablet', 'capsule', 'kapsul', 'syrup', 'sirup', 'injection', 'injeksi'
}

PROCEDURE_SYNONYMS = {
    # Ultrasound family
    'usg': ['ultrasound', 'ultrasonography', 'ultrasonic', 'diagnostic ultrasound'],
    'ultrasound': ['ultrasound', 'ultrasonography', 'ultrasonic', 'diagnostic ultrasound'],
    'ultrasonography': ['ultrasound', 'ultrasonography', 'ultrasonic', 'diagnostic ultrasound'],
    'ultrasonic': ['ultrasound', 'ultrasonography', 'ultrasonic', 'diagnostic ultrasound'],
    'echo': ['ultrasound', 'ultrasonography', 'echocardiography'],
    'ekokardiografi': ['echocardiography', 'cardiac ultrasound', 'ultrasonography'],

    # X-ray family
    'rontgen': ['x-ray', 'radiography', 'radiograph', 'plain radiography'],
    'x-ray': ['x-ray', 'radiography', 'radiograph', 'plain radiography'],
    'xray': ['x-ray', 'radiography', 'radiograph', 'plain radiography'],
    'radiography': ['x-ray', 'radiography', 'radiograph'],
    'radiograph': ['x-ray', 'radiography', 'radiograph'],
    'rontgen thorax': ['chest x-ray', 'thorax radiography', 'x-ray chest'],

    # CT Scan family
    'ct scan': ['ct scan', 'computed tomography', 'cat scan'],
    'ct': ['ct scan', 'computed tomography', 'cat scan'],
    'cat scan': ['ct scan', 'computed tomography', 'cat scan'],
    'ct scan kepala': ['head ct scan', 'brain ct scan', 'computed tomography head'],

    # MRI family
    'mri': ['mri', 'magnetic resonance imaging'],

    # Endoscopy family
    'endoscopy': ['endoscopy', 'endoscopic examination'],
    'scope': ['endoscopy', 'endoscopic examination'],
    'endoskopi': ['endoscopy', 'endoscopic examination'],

    # Surgery family (generic)
    'operasi': ['surgery', 'operation', 'surgical procedure'],
    'surgery': ['surgery', 'operation', 'surgical procedure'],
    'operation': ['surgery', 'operation', 'surgical procedure'],

    # Common Indonesian colloquial to standard procedures
    'operasi usus buntu': ['appendectomy', 'appendicectomy', 'open appendectomy', 'laparoscopic appendectomy'],
    'apendektomi': ['appendectomy', 'appendicectomy', 'open appendectomy', 'laparoscopic appendectomy'],
    'operasi katarak': ['cataract extraction', 'phacoemulsification', 'lens extraction'],
    'operasi caesar': ['cesarean delivery', 'cesarean section', 'caesarean section'],
    'sectio caesarea': ['cesarean delivery', 'cesarean section', 'caesarean section'],
    'cuci darah': ['hemodialysis', 'renal dialysis', 'dialysis'],
    'hemodialisa': ['hemodialysis', 'renal dialysis', 'dialysis'],
    'hemodialisis': ['hemodialysis', 'renal dialysis', 'dialysis'],
    'dialisis': ['hemodialysis', 'renal dialysis', 'dialysis'],
    'pemasangan ring jantung': ['coronary stent placement', 'percutaneous coronary intervention', 'coronary angioplasty with stent', 'pci'],
    'ring jantung': ['coronary stent placement', 'percutaneous coronary intervention', 'coronary angioplasty with stent', 'pci'],
    'stent jantung': ['coronary stent placement', 'percutaneous coronary intervention', 'coronary angioplasty with stent', 'pci'],
    'operasi jantung': ['cardiac surgery', 'coronary artery bypass graft', 'cabg', 'heart surgery'],
    'kateter jantung': ['cardiac catheterization', 'coronary angiography', 'heart catheterization'],
    'kateterisasi jantung': ['cardiac catheterization', 'coronary angiography', 'heart catheterization'],
    'angiografi koroner': ['coronary angiography', 'cardiac catheterization'],
    'operasi tulang patah': ['open reduction internal fixation', 'orif', 'fracture fixation'],
    'operasi patah tulang': ['open reduction internal fixation', 'orif', 'fracture fixation'],

    # Biopsy family
    'biopsy': ['biopsy', 'tissue sampling', 'histopathology'],
    'biopsi': ['biopsy', 'tissue sampling', 'histopathology']
}
from services.pnpk_summary_service import PNPKSummaryService


# ============================================================
# 🔹 ASYNC WRAPPER for analyze_lite_single (with ULTRA FAST mode)
# ============================================================
async def endpoint_analyze_single_async(request_data: Dict[str, Any], db_pool=None, progress_callback=None) -> Dict[str, Any]:
    """
    Async wrapper untuk analyze_lite_single dengan mode selection
    
    Modes:
    - "ultra_fast": Parallel processing + caching (DEFAULT, 60-75% faster)
    - "optimized": Sequential optimized (40-50% faster)
    - "original": Original version (baseline)
    """
    
    # Determine analysis mode
    analysis_mode = request_data.get("analysis_mode", "ultra_fast")
    
    print(f"[ENDPOINT_ASYNC] Analysis mode: {analysis_mode}")
    
    if analysis_mode == "ultra_fast":
        # 🚀 ULTRA FAST MODE: Parallel processing + caching
        print("[ENDPOINT_ASYNC] Using ULTRA FAST mode (parallel + cache)")
        result = await analyze_lite_single_ultra_fast(
            request_data, 
            db_pool=db_pool,
            progress_callback=progress_callback
        )
        return result
    
    elif analysis_mode == "optimized":
        # ⚡ OPTIMIZED MODE: Sequential with combined prompts
        print("[ENDPOINT_ASYNC] Using OPTIMIZED mode (sequential combined)")
        
        # Pre-fetch PNPK data
        pnpk_data = None
        if db_pool:
            try:
                diagnosis_name = None
                mode = request_data.get("mode", "text")
                
                if mode == "form" or mode == "excel":
                    diagnosis_name = request_data.get("diagnosis", "")
                
                if diagnosis_name:
                    pnpk_service = PNPKSummaryService(db_pool)
                    pnpk_data = await pnpk_service.get_pnpk_summary(diagnosis_name, auto_match=True)
                    print(f"[ENDPOINT_ASYNC] ✓ PNPK pre-fetched for: {diagnosis_name}")
            except Exception as e:
                print(f"[ENDPOINT_ASYNC] ⚠️ PNPK pre-fetch failed: {e}")
        
        request_data["_pnpk_data"] = pnpk_data
        return analyze_lite_single_optimized(request_data, db_pool=db_pool)
    
    else:
        # 📝 ORIGINAL MODE: Baseline
        print("[ENDPOINT_ASYNC] Using ORIGINAL mode (baseline)")
        return analyze_lite_single(request_data, db_pool=db_pool)


# ============================================================
# 📌 ENDPOINT 1A: Validate Form Input
# ============================================================
def endpoint_validate_form(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/validate/form
    
    Validasi input form 3 field sebelum analisis.
    Untuk preview hasil parsing dan validasi format.
    
    Request:
    {
        "diagnosis": "Pneumonia berat (J18.9)",
        "tindakan": "Nebulisasi (93.96), Rontgen Thorax",
        "obat": "Ceftriaxone injeksi 1g, Paracetamol 500mg"
    }
    
    Response:
    {
        "status": "success",
        "validation": {
            "diagnosis_valid": true,
            "tindakan_valid": true,
            "obat_valid": true,
            "errors": []
        },
        "parsed": {
            "diagnosis": "Pneumonia berat",
            "diagnosis_icd": "J18.9",
            "tindakan": ["Nebulisasi", "Rontgen Thorax"],
            "tindakan_codes": {"Nebulisasi": "93.96"},
            "obat": ["Ceftriaxone injeksi 1g", "Paracetamol 500mg"]
        }
    }
    """
    
    try:
        from services.lite_service import parse_form_input
        
        diagnosis = request_data.get("diagnosis", "")
        tindakan = request_data.get("tindakan", "")
        obat = request_data.get("obat", "")
        
        # Validasi input kosong
        errors = []
        if not diagnosis or diagnosis.strip() == "":
            errors.append("Diagnosis tidak boleh kosong")
        
        if not tindakan or tindakan.strip() == "":
            errors.append("Tindakan tidak boleh kosong (minimal 1 tindakan)")
        
        if not obat or obat.strip() == "":
            errors.append("Obat tidak boleh kosong (minimal 1 obat)")
        
        if errors:
            return {
                "status": "error",
                "validation": {
                    "diagnosis_valid": bool(diagnosis),
                    "tindakan_valid": bool(tindakan),
                    "obat_valid": bool(obat),
                    "errors": errors
                }
            }
        
        # Parse input
        parsed = parse_form_input(diagnosis, tindakan, obat)
        
        # Additional validation
        if len(parsed["tindakan"]) == 0:
            errors.append("Format tindakan tidak valid")
        
        if len(parsed["obat"]) == 0:
            errors.append("Format obat tidak valid")
        
        return {
            "status": "success",
            "validation": {
                "diagnosis_valid": True,
                "tindakan_valid": len(parsed["tindakan"]) > 0,
                "obat_valid": len(parsed["obat"]) > 0,
                "errors": errors
            },
            "parsed": parsed,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# ============================================================
# 📌 ENDPOINT 1B: Parse Free Text Input (renamed from endpoint_parse_text)
# ============================================================
def endpoint_parse_text(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/parse-text
    
    Parse resume medis free text menjadi struktur terpisah menggunakan AI.
    Untuk ekstraksi diagnosis, tindakan, dan obat dari paragraf resume medis.
    
    Request:
    {
        "input_text": "Pasien didiagnosa pneumonia berat, diberikan nebulisasi dan ceftriaxone injeksi..."
    }
    
    Response:
    {
        "status": "success",
        "result": {
            "diagnosis": "Pneumonia berat",
            "tindakan": "Nebulisasi",
            "obat": "Ceftriaxone injeksi"
        }
    }
    """
    
    try:
        input_text = request_data.get("input_text", "")
        
        if not input_text or input_text.strip() == "":
            return {
                "status": "error",
                "message": "Input text tidak boleh kosong"
            }
        
        # Parse text using AI
        parsed = parse_free_text(input_text)
        
        # Extract structured data
        diagnosis = parsed.get("diagnosis", "")
        tindakan = parsed.get("tindakan", "")
        obat = parsed.get("obat", "")
        
        return {
            "status": "success",
            "result": {
                "diagnosis": diagnosis,
                "tindakan": tindakan,
                "obat": obat
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Parsing error: {str(e)}"
        }


# ============================================================
# 📌 ENDPOINT 2: Analyze Single Claim (ENHANCED untuk Form Mode)
# ============================================================
def endpoint_analyze_single(request_data: Dict[str, Any], db_pool=None) -> Dict[str, Any]:
    """
    POST /api/lite/analyze/single
    
    Analisis klaim tunggal dengan 3 mode input.
    
    OPTIMIZED VERSION: Uses combined AI prompts for faster processing
    - Original: 5 OpenAI calls, ~15-18 seconds
    - Optimized: 3 OpenAI calls, ~8-12 seconds (40-50% faster)
    
    Args:
        request_data: Request payload
        db_pool: Optional AsyncPG database pool for PNPK data
    
    Request:
    {
        "mode": "text" | "form" | "excel",
        
        // Mode TEXT (free text input)
        "input_text": "Pneumonia berat, diberikan Ceftriaxone...",
        
        // Mode FORM (4 field terpisah)
        "diagnosis": "Pneumonia berat (J18.9)",
        "tindakan": "Nebulisasi (93.96), Rontgen Thorax",
        "obat": "Ceftriaxone injeksi 1g, Paracetamol 500mg",
        "service_type": "rawat-inap",  // NEW: rawat-inap | rawat-jalan | igd | one-day-care
        
        // Optional context
        "rs_id": "RS001",
        "region_id": "REG01",
        "use_optimized": true  // NEW: use optimized version (default: true)
    }
    
    Response:
    {
        "status": "success",
        "result": {
            "klasifikasi": {...},
            "validasi_klinis": {...},
            "cp_ringkas": [...],
            "checklist_dokumen": [...],
            "insight_ai": "...",
            "konsistensi": {...},
            "metadata": {
                "ai_calls": 3,  // Optimized version
                "optimization": "combined_prompts"
            }
        }
    }
    """
    
    try:
        mode = request_data.get("mode", "text")
        use_optimized = request_data.get("use_optimized", True)  # Default to optimized version
        
        # Validasi input berdasarkan mode
        if mode == "text":
            if not request_data.get("input_text"):
                return {
                    "status": "error",
                    "message": "input_text required untuk mode text"
                }
        elif mode == "form":
            # Validasi 4 field form
            diagnosis = request_data.get("diagnosis", "")
            tindakan = request_data.get("tindakan", "")
            obat = request_data.get("obat", "")
            service_type = request_data.get("service_type", "")
            
            errors = []
            if not diagnosis:
                errors.append("diagnosis required untuk mode form")
            if not tindakan:
                errors.append("tindakan required untuk mode form")
            if not obat:
                errors.append("obat required untuk mode form")
            if not service_type:
                errors.append("service_type required untuk mode form")
            
            if errors:
                return {
                    "status": "error",
                    "message": "; ".join(errors),
                    "errors": errors
                }
        else:
            # Excel mode (legacy)
            if not request_data.get("diagnosis"):
                return {
                    "status": "error",
                    "message": "diagnosis required"
                }
        
        # Call analyzer (optimized or original)
        if use_optimized:
            print(f"[ENDPOINT] Using OPTIMIZED analyzer (3 AI calls)")
            result = analyze_lite_single_optimized(request_data, db_pool=db_pool)
        else:
            print(f"[ENDPOINT] Using ORIGINAL analyzer (5 AI calls)")
            result = analyze_lite_single(request_data, db_pool=db_pool)
        
        # Save to history (optional, based on config)
        if request_data.get("save_history", False):
            save_to_history(result)
        
        return {
            "status": "success",
            "result": result,
            "mode": mode,
            "optimized": use_optimized,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"[AI-CLAIM LITE] Error in analyze_single: {e}")
        return {
            "status": "error",
            "message": str(e),
            "detail": "Terjadi kesalahan saat analisis. Silakan coba lagi."
        }


# ============================================================
# 📌 ENDPOINT 3: Analyze Batch (Excel Import)
# ============================================================
def endpoint_analyze_batch(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/analyze/batch
    
    Analisis batch dari Excel data.
    
    Request:
    {
        "batch_data": [
            {"Nama": "Ahmad S.", "Diagnosis": "Pneumonia", ...},
            {"Nama": "Siti R.", "Diagnosis": "Tifoid", ...}
        ],
        "rs_id": "RS001",
        "region_id": "REG01"
    }
    
    Response:
    {
        "status": "success",
        "summary": {
            "total_klaim": 10,
            "success": 9,
            "failed": 1
        },
        "results": [
            {
                "no": 1,
                "nama_pasien": "Ahmad S.",
                "icd10": "J18.9",
                "insight": "Perlu radiologi...",
                ...
            }
        ]
    }
    """
    
    try:
        batch_data = request_data.get("batch_data", [])
        
        if not batch_data or len(batch_data) == 0:
            return {
                "status": "error",
                "message": "batch_data tidak boleh kosong"
            }
        
        # Add context dari request
        rs_id = request_data.get("rs_id")
        region_id = request_data.get("region_id")
        
        # Inject rs_id dan region_id ke setiap row
        for row in batch_data:
            if rs_id:
                row["rs_id"] = rs_id
            if region_id:
                row["region_id"] = region_id
        
        # Call batch analyzer
        batch_result = analyze_lite_batch(batch_data)
        
        return {
            "status": "success",
            "summary": {
                "total_klaim": batch_result["total_klaim"],
                "success": batch_result["success"],
                "failed": batch_result["failed"]
            },
            "results": batch_result["results"],
            "timestamp": batch_result["timestamp"]
        }
        
    except Exception as e:
        print(f"[AI-CLAIM LITE] Error in analyze_batch: {e}")
        return {
            "status": "error",
            "message": str(e),
            "detail": "Terjadi kesalahan saat analisis batch. Periksa format data Excel."
        }


# ============================================================
# 📌 ENDPOINT 4: Get History List
# ============================================================
def endpoint_get_history(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    GET /api/lite/history
    
    Ambil list history 10 terakhir.
    
    Request:
    {
        "limit": 10,  // optional, default 10
        "user_id": "..."  // optional, untuk filter per user
    }
    
    Response:
    {
        "status": "success",
        "history": [
            {
                "claim_id": "LITE-20251108001",
                "diagnosis": "Pneumonia berat",
                "timestamp": "2025-11-08T10:15:00",
                "mode": "text"
            }
        ]
    }
    """
    
    try:
        limit = request_data.get("limit", 10)
        
        # Get history dari database/storage
        history_list = get_history_list(limit=limit)
        
        return {
            "status": "success",
            "history": history_list,
            "total": len(history_list)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# ============================================================
# 📌 ENDPOINT 5: Load History Detail
# ============================================================
def endpoint_load_history_detail(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    GET /api/lite/history/{history_id}
    
    Load full detail dari history untuk ditampilkan ulang.
    
    Request:
    {
        "history_id": "LITE-20251108001"
    }
    
    Response:
    {
        "status": "success",
        "result": {
            "klasifikasi": {...},
            "validasi_klinis": {...},
            ...
        }
    }
    """
    
    try:
        history_id = request_data.get("history_id")
        
        if not history_id:
            return {
                "status": "error",
                "message": "history_id required"
            }
        
        # Load dari database
        result = load_from_history(history_id)
        
        if not result:
            return {
                "status": "error",
                "message": "History tidak ditemukan"
            }
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# ============================================================
# 📌 ENDPOINT 6: Delete History
# ============================================================
def endpoint_delete_history(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    DELETE /api/lite/history
    
    Hapus history (single atau semua).
    
    Request:
    {
        "history_id": "LITE-20251108001",  // optional, untuk delete single
        "delete_all": true  // optional, untuk delete all
    }
    
    Response:
    {
        "status": "success",
        "message": "History berhasil dihapus"
    }
    """
    
    try:
        history_id = request_data.get("history_id")
        delete_all = request_data.get("delete_all", False)
        
        # TODO: Implementasi delete dari database
        # if delete_all:
        #     delete_all_history()
        # elif history_id:
        #     delete_single_history(history_id)
        
        return {
            "status": "success",
            "message": "History berhasil dihapus"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# ============================================================
# 📌 ENDPOINT 7: Export Results
# ============================================================
def endpoint_export_results(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/export
    
    Export hasil analisis ke Excel/PDF.
    
    Request:
    {
        "format": "excel" | "pdf",
        "data": {...}  // result data untuk di-export
    }
    
    Response:
    {
        "status": "success",
        "file_url": "https://...",
        "filename": "ai-claim-lite-export.xlsx"
    }
    """
    
    try:
        export_format = request_data.get("format", "excel")
        data = request_data.get("data")
        
        if not data:
            return {
                "status": "error",
                "message": "Data untuk export tidak boleh kosong"
            }
        
        # TODO: Implementasi export
        # if export_format == "excel":
        #     file_bytes = export_to_excel(data)
        # else:
        #     file_bytes = export_to_pdf(data)
        
        # Sementara return placeholder
        return {
            "status": "success",
            "message": "Export berhasil",
            "filename": f"ai-claim-lite-export.{export_format}",
            "note": "Implementasi export akan diselesaikan pada tahap berikutnya"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# ============================================================
# 📌 ENDPOINT 7: ICD-10 Smart Lookup (NEW)
# ============================================================
def endpoint_icd10_lookup(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/icd10/lookup
    
    Smart ICD-10 lookup dengan AI (RAG approach).
    Guarantee 100% match dengan database.
    
    Request:
    {
        "diagnosis_input": "paru2 basah"
    }
    
    Response (Direct Flow):
    {
        "status": "success",
        "flow": "direct",
        "requires_modal": false,
        "selected_code": "J18.9",
        "selected_name": "Pneumonia, unspecified",
        "source": "ICD10_2010",
        "subcategories": {
            "parent": {"code": "J18", "name": "Pneumonia, organism unspecified"},
            "children": [
                {"code": "J18.0", "name": "Bronchopneumonia, unspecified"},
                {"code": "J18.1", "name": "Lobar pneumonia, unspecified"},
                ...
            ],
            "total_subcategories": 5
        },
        "ai_used": true,
        "ai_confidence": 95,
        "ai_reasoning": "..."
    }
    
    Response (Suggestion Flow):
    {
        "status": "success",
        "flow": "suggestion",
        "requires_modal": true,
        "suggestions": [
            {"code": "J18.9", "name": "Pneumonia, unspecified", "relevance": 1},
            {"code": "J18.0", "name": "Bronchopneumonia, unspecified", "relevance": 2},
            ...
        ],
        "total_suggestions": 5,
        "message": "Silakan pilih diagnosis yang sesuai:"
    }
    """
    try:
        diagnosis_input = request_data.get("diagnosis_input", "")
        
        if not diagnosis_input or diagnosis_input.strip() == "":
            return {
                "status": "error",
                "message": "diagnosis_input required"
            }
        
        print(f"[ENDPOINT_ICD10] Lookup: {diagnosis_input}")
        
        # Call smart lookup dengan RAG
        result = lookup_icd10_smart_with_rag(diagnosis_input)
        
        return {
            "status": "success",
            **result,  # Spread all result fields
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"[ENDPOINT_ICD10] ❌ Error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================
# 📌 ENDPOINT 8: ICD-10 Select Code (NEW)
# ============================================================
def endpoint_icd10_select(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/icd10/select
    
    Select ICD-10 code setelah user pilih dari modal suggestion.
    Return subcategories dari code yang dipilih.
    
    Request:
    {
        "selected_code": "J18.9"
    }
    
    Response:
    {
        "status": "success",
        "selected_code": "J18.9",
        "selected_name": "Pneumonia, unspecified",
        "source": "ICD10_2010",
        "subcategories": {
            "parent": {"code": "J18", "name": "Pneumonia, organism unspecified"},
            "children": [
                {"code": "J18.0", "name": "Bronchopneumonia, unspecified"},
                ...
            ],
            "total_subcategories": 5
        }
    }
    """
    try:
        selected_code = request_data.get("selected_code", "")
        
        if not selected_code:
            return {
                "status": "error",
                "message": "selected_code required"
            }
        
        print(f"[ENDPOINT_ICD10] Select: {selected_code}")
        
        # Call select function
        result = select_icd10_code(selected_code)
        
        return {
            **result,  # Already has "status" field
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"[ENDPOINT_ICD10] ❌ Error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================
# 📌 ENDPOINT 9: ICD-10 Statistics (NEW)
# ============================================================
def endpoint_icd10_statistics(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    GET /api/icd10/statistics
    
    Get statistik database ICD-10.
    
    Response:
    {
        "status": "success",
        "statistics": {
            "total_codes": 18543,
            "total_categories": 2048,
            "total_subcategories": 16495,
            "database_source": "ICD10_2010",
            "last_updated": "2025-11-14T..."
        }
    }
    """
    try:
        print("[ENDPOINT_ICD10] Getting statistics...")
        
        stats = get_icd10_statistics()
        
        return {
            "status": "success",
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"[ENDPOINT_ICD10] ❌ Error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================
# 📌 ENDPOINT 5: ICD-9 Smart Lookup (NEW - STANDALONE)
# ============================================================
def endpoint_icd9_lookup(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/icd9/lookup
    
    Get ICD-9 procedure code dengan AI normalization fallback.
    
    Request:
    {
        "procedure_input": "x-ray thorax" atau "rontgen dada"
    }
    
    Response:
    {
        "status": "success",
        "data": {
            "status": "success" | "suggestions" | "not_found",
            "result": {...} atau null,
            "suggestions": [...],
            "needs_selection": true/false
        },
        "timestamp": "2025-11-14T..."
    }
    """
    from services.icd9_smart_service import lookup_icd9_procedure
    
    try:
        procedure_input = request_data.get("procedure_input", "")
        
        if not procedure_input or procedure_input.strip() == "":
            return {
                "status": "error",
                "message": "procedure_input is required",
                "timestamp": datetime.now().isoformat()
            }
        
        print(f"[ENDPOINT_ICD9] Looking up: '{procedure_input}'")
        
        # Call ICD-9 smart service
        result = lookup_icd9_procedure(procedure_input)
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"[ENDPOINT_ICD9] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================
# 📌 FORNAS VALIDATION ENDPOINT
# ============================================================
    if endpoint_name not in LITE_ENDPOINTS:
        return {
            "status": "error",
            "message": f"Unknown endpoint: {endpoint_name}",
            "available_endpoints": list(LITE_ENDPOINTS.keys())
        }
    
    handler_func = LITE_ENDPOINTS[endpoint_name]
    
    try:
        return handler_func(request_data)
    except Exception as e:
        print(f"[AI-CLAIM LITE] Unhandled error in {endpoint_name}: {e}")
        return {
            "status": "error",
            "message": "Internal server error",
            "detail": str(e)
        }


# ============================================================
# 📌 ENDPOINT 6: Validate FORNAS (Standalone)
# ============================================================
def endpoint_validate_fornas(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/validate/fornas
    
    Standalone FORNAS validation dengan AI reasoning.
    Untuk validasi obat terhadap diagnosis tanpa full analisis.
    
    Request:
    {
        "diagnosis_icd10": "J18.9",
        "diagnosis_name": "Pneumonia berat",
        "obat": ["Ceftriaxone 1g IV", "Paracetamol 500mg", "Levofloxacin 500mg"]
    }
    
    Response:
    {
        "status": "success",
        "fornas_validation": [
            {
                "no": 1,
                "nama_obat": "Ceftriaxone",
                "kelas_terapi": "Antibiotik – Sefalosporin",
                "status_fornas": "✅ Sesuai (Fornas)",
                "catatan_ai": "Lini pertama pneumonia berat rawat inap.",
                "sumber_regulasi": "FORNAS 2023 • PNPK Pneumonia 2020"
            },
            ...
        ],
        "summary": {
            "total_obat": 3,
            "sesuai": 2,
            "perlu_justifikasi": 1,
            "non_fornas": 0,
            "update_date": "2025-11-11",
            "status_database": "Official Verified"
        }
    }
    """
    try:
        # Extract request data
        diagnosis_icd10 = request_data.get("diagnosis_icd10", "")
        diagnosis_name = request_data.get("diagnosis_name", "")
        obat_input = request_data.get("obat", [])
        
        # Validate required fields
        if not diagnosis_icd10 or not diagnosis_name:
            return {
                "status": "error",
                "message": "diagnosis_icd10 dan diagnosis_name required"
            }
        
        if not obat_input or len(obat_input) == 0:
            return {
                "status": "error",
                "message": "obat list required (minimal 1 obat)"
            }
        
        # Convert obat to list if string
        if isinstance(obat_input, str):
            # Parse comma-separated string
            obat_list = [o.strip() for o in obat_input.split(",") if o.strip()]
        else:
            obat_list = obat_input
        
        # Call FORNAS Smart validator (with English→Indonesian support)
        result = validate_fornas(
            drug_list=obat_list,
            diagnosis_icd10=diagnosis_icd10,
            diagnosis_name=diagnosis_name
        )
        
        return {
            "status": "success",
            "fornas_validation": result.get("fornas_validation", []),
            "summary": result.get("summary", {}),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================
# 📌 TESTING HELPERS
# ============================================================
if __name__ == "__main__":
    print("🧪 Testing AI-CLAIM Lite Endpoints\n")
    
    # Test 0: Validate Form Input
    print("0️⃣ Testing validate_form:")
    validate_result = endpoint_validate_form({
        "diagnosis": "Pneumonia berat (J18.9)",
        "tindakan": "Nebulisasi (93.96), Rontgen Thorax",
        "obat": "Ceftriaxone injeksi 1g, Paracetamol 500mg"
    })
    print(json.dumps(validate_result, indent=2, ensure_ascii=False))
    
    # Test 1: Parse Text
    print("\n1️⃣ Testing parse_text:")
    parse_result = endpoint_parse_text({
        "input_text": "Pneumonia berat, diberikan Ceftriaxone injeksi 1g/12 jam, Nebulisasi dengan Salbutamol"
    })
    print(json.dumps(parse_result, indent=2, ensure_ascii=False))
    
    # Test 2A: Analyze Single (Text Mode)
    print("\n2️⃣A Testing analyze_single (text mode):")
    analyze_text_result = endpoint_analyze_single({
        "mode": "text",
        "input_text": "Pneumonia berat dengan infiltrat bilateral, Nebulisasi 3x sehari, Ceftriaxone injeksi 1g/12jam",
        "save_history": False
    })
    print(f"Status: {analyze_text_result['status']}")
    if analyze_text_result['status'] == 'success':
        print(f"Diagnosis: {analyze_text_result['result']['klasifikasi']['diagnosis']}")
    
    # Test 2B: Analyze Single (Form Mode) - NEW
    print("\n2️⃣B Testing analyze_single (form mode):")
    analyze_form_result = endpoint_analyze_single({
        "mode": "form",
        "diagnosis": "Pneumonia berat (J18.9)",
        "tindakan": "Nebulisasi (93.96), Rontgen Thorax (87.44)",
        "obat": "Ceftriaxone injeksi 1g/12jam, Paracetamol tablet 500mg",
        "save_history": True
    })
    print(f"Status: {analyze_form_result['status']}")
    if analyze_form_result['status'] == 'success':
        result = analyze_form_result['result']
        print(f"Klasifikasi:")
        print(f"  - Diagnosis: {result['klasifikasi']['diagnosis']}")
        print(f"  - Tindakan: {result['klasifikasi']['tindakan']}")
        print(f"  - Obat: {result['klasifikasi']['obat']}")
        print(f"Insight: {result['insight_ai']}")
    
    # Test 3: Batch Analysis
    print("\n3️⃣ Testing analyze_batch:")
    batch_result = endpoint_analyze_batch({
        "batch_data": [
            {"Nama": "Ahmad S.", "Diagnosis": "Pneumonia", "Tindakan": "Nebulisasi", "Obat": "Ceftriaxone"},
            {"Nama": "Siti R.", "Diagnosis": "Tifoid", "Tindakan": "Infus", "Obat": "Ceftriaxone"}
        ]
    })
    print(f"Total: {batch_result.get('summary', {}).get('total_klaim', 0)}")
    print(f"Success: {batch_result.get('summary', {}).get('success', 0)}")
    
    print("\n✅ Testing completed!")


# ============================================================
# 📌 ENDPOINT 10: Dokumen Wajib (3 endpoints)
# ============================================================

def endpoint_get_dokumen_wajib(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    GET/POST /api/dokumen-wajib
    
    Mengambil list dokumen wajib berdasarkan diagnosis
    
    Request:
    {
        "diagnosis": "Pneumonia"
    }
    
    Response:
    {
        "status": "success",
        "diagnosis": "Pneumonia",
        "total_dokumen": 7,
        "dokumen_list": [
            {
                "id": 1,
                "diagnosis_name": "Pneumonia",
                "nama_dokumen": "Rekam Medis",
                "status": "wajib",
                "keterangan": "Dokumen utama klinis dan administratif."
            },
            {
                "id": 6,
                "diagnosis_name": "Pneumonia",
                "nama_dokumen": "Prokalsitonin (PCT)",
                "status": "opsional",
                "keterangan": "Tidak rutin untuk memulai antibiotik..."
            },
            ...
        ]
    }
    """
    try:
        # Validasi input
        diagnosis = request_data.get("diagnosis")
        if not diagnosis:
            return {
                "status": "error",
                "message": "Parameter 'diagnosis' wajib diisi",
                "error_code": "MISSING_DIAGNOSIS"
            }
        
        # Get service
        service = get_dokumen_wajib_service()
        
        # Get dokumen wajib
        result = service.get_dokumen_wajib_by_diagnosis(diagnosis)
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            **result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "error_code": "DOKUMEN_WAJIB_ERROR",
            "timestamp": datetime.now().isoformat()
        }


# ============================================================
# FORNAS ENDPOINTS (NEW FLOW - PANEL KIRI & KANAN)
# ============================================================

def endpoint_fornas_lookup(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/fornas/lookup
    
    Lookup FORNAS drug - Panel Kiri (drug list)
    Uses fornas_normalize_service.py
    
    Request:
    {
        "drug_input": "ceftriaxone"
    }
    
    Response:
    {
        "status": "success",
        "data": {
            "flow": "recommendations",
            "original_input": "ceftriaxone",
            "normalized_name": "seftriakson",
            "recommendations": [
                {
                    "obat_name": "Seftriakson",
                    "variant_count": 12,
                    "kelas_terapi": "Antibiotik"
                }
            ]
        }
    }
    """
    try:
        from services.fornas_normalize_service import lookup_fornas_smart
        
        drug_input = request_data.get("drug_input", "").strip()
        
        if not drug_input:
            return {
                "status": "error",
                "message": "drug_input is required"
            }
        
        result = lookup_fornas_smart(drug_input)
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        print(f"[FORNAS_LOOKUP] Error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def endpoint_fornas_details(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/fornas/details
    
    Get FORNAS drug details - Panel Kanan (sediaan variants)
    Uses fornas_normalize_service.py
    
    Request:
    {
        "drug_name": "Seftriakson"
    }
    
    Response:
    {
        "status": "success",
        "data": {
            "drug_name": "Seftriakson",
            "variants": [
                {
                    "kode_fornas": "FOR123",
                    "obat_name": "Seftriakson",
                    "sediaan_kekuatan": "Injeksi 1 g/vial",
                    "restriksi_penggunaan": "Infeksi berat...",
                    "kelas_terapi": "Antibiotik",
                    "subkelas_terapi": "Sefalosporin Generasi 3"
                }
            ],
            "total": 12
        }
    }
    """
    try:
        from services.fornas_normalize_service import get_drug_details
        
        drug_name = request_data.get("drug_name", "").strip()
        
        if not drug_name:
            return {
                "status": "error",
                "message": "drug_name is required"
            }
        
        variants = get_drug_details(drug_name)
        
        return {
            "status": "success",
            "data": {
                "drug_name": drug_name,
                "variants": variants,
                "total": len(variants)
            }
        }
        
    except Exception as e:
        print(f"[FORNAS_DETAILS] Error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def endpoint_get_all_diagnosis() -> Dict[str, Any]:
    """
    GET /api/dokumen-wajib/diagnosis-list
    
    Mengambil semua diagnosis yang tersedia di database
    
    Response:
    {
        "status": "success",
        "total": 15,
        "diagnosis_list": [
            "Pneumonia",
            "Hospital-Acquired Pneumonia (HAP)",
            "Ventilator-Associated Pneumonia (VAP)",
            ...
        ]
    }
    """
    try:
        service = get_dokumen_wajib_service()
        diagnosis_list = service.get_all_diagnosis_list()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total": len(diagnosis_list),
            "diagnosis_list": diagnosis_list
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "error_code": "GET_DIAGNOSIS_LIST_ERROR",
            "timestamp": datetime.now().isoformat()
        }


def endpoint_search_diagnosis(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/dokumen-wajib/search-diagnosis
    
    Search diagnosis berdasarkan keyword
    
    Request:
    {
        "keyword": "pneumo"
    }
    
    Response:
    {
        "status": "success",
        "keyword": "pneumo",
        "total": 3,
        "diagnosis_list": [
            "Pneumonia",
            "Hospital-Acquired Pneumonia (HAP)",
            "Ventilator-Associated Pneumonia (VAP)"
        ]
    }
    """
    try:
        keyword = request_data.get("keyword", "")
        
        if not keyword:
            return {
                "status": "error",
                "message": "Parameter 'keyword' wajib diisi",
                "error_code": "MISSING_KEYWORD"
            }
        
        service = get_dokumen_wajib_service()
        diagnosis_list = service.search_diagnosis(keyword)
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "keyword": keyword,
            "total": len(diagnosis_list),
            "diagnosis_list": diagnosis_list
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "error_code": "SEARCH_DIAGNOSIS_ERROR",
            "timestamp": datetime.now().isoformat()
        }


# ============================================================
# 📌 ENDPOINT 11: Translate Medical Term (OpenAI) - OPTIMIZED v2.0
# ============================================================
def endpoint_translate_medical(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/translate-medical
    
    Translate colloquial/Indonesian medical term to standard medical terminology.
    NOW USES AI NORMALIZER SERVICE (ICD-10, ICD-9, FORNAS).
    
    Request:
    {
        "term": "paru2 basah",
        "type": "diagnosis"  // Optional: "diagnosis" (default), "procedure", "drug"
    }
    
    Response (diagnosis):
    {
        "status": "success",
        "data": {
            "original": "paru2 basah",
            "translated": "pneumonia",
            "confidence": "high"
        }
    }
    
    Response (procedure):
    {
        "status": "success",
        "data": {
            "original": "rontgen dada",
            "translated": "chest x-ray",
            "confidence": "high"
        }
    }
    
    Response (drug):
    {
        "status": "success",
        "data": {
            "original": "ceftriaxone",
            "translated": "seftriakson",
            "confidence": "high"
        }
    }
    """
    
    try:
        term = request_data.get("term", "").strip()
        term_type = request_data.get("type", "diagnosis")  # diagnosis | procedure | drug
        
        if not term:
            return {
                "status": "error",
                "message": "Medical term is required",
                "data": None
            }
        
        print(f"[TRANSLATE_MEDICAL] Processing: '{term}' (type: {term_type})")
        
        # Route to appropriate AI normalizer
        if term_type == "procedure":
            # Use ICD-9 AI normalizer
            from services.icd9_smart_service import ai_normalize_procedure_to_term
            
            result = ai_normalize_procedure_to_term(term)
            
            if result.get("error"):
                return {
                    "status": "error",
                    "message": result.get("reasoning", "Normalization failed"),
                    "data": {
                        "original": term,
                        "translated": term,
                        "confidence": "low"
                    }
                }
            
            return {
                "status": "success",
                "data": {
                    "original": term,
                    "translated": result.get("medical_term", term),
                    "confidence": "high" if result.get("confidence", 0) >= 80 else "medium"
                }
            }
        
        elif term_type == "drug":
            # Use FORNAS AI normalizer
            from services.fornas_normalize_service import ai_normalize_to_indonesian
            
            result = ai_normalize_to_indonesian(term)
            
            if result.get("error"):
                return {
                    "status": "error",
                    "message": result.get("reasoning", "Normalization failed"),
                    "data": {
                        "original": term,
                        "translated": term,
                        "confidence": "low"
                    }
                }
            
            return {
                "status": "success",
                "data": {
                    "original": term,
                    "translated": result.get("indonesian_name", term),
                    "confidence": "high" if result.get("confidence", 0) >= 80 else "medium"
                }
            }
        
        else:
            # Default: Use ICD-10 AI normalizer (diagnosis)
            from services.icd10_ai_normalizer import ai_normalize_to_medical_term
            
            result = ai_normalize_to_medical_term(term)
            
            if result.get("error"):
                return {
                    "status": "error",
                    "message": result.get("reasoning", "Normalization failed"),
                    "data": {
                        "original": term,
                        "translated": term,
                        "confidence": "low"
                    }
                }
            
            return {
                "status": "success",
                "data": {
                    "original": term,
                    "translated": result.get("medical_term", term),
                    "confidence": "high" if result.get("confidence", 0) >= 80 else "medium"
                }
            }
    
    except Exception as e:
        error_msg = str(e)
        print(f"[TRANSLATE_MEDICAL] ❌ Error: {error_msg}")
        
        # Return original term on error (graceful degradation)
        return {
            "status": "error",
            "message": f"Translation failed: {error_msg}",
            "data": {
                "original": term,
                "translated": term,
                "confidence": "low"
            }
        }


# ============================================================
# 🔹 ENDPOINT: Translate Medical Procedure - OPTIMIZED v2.0
# ============================================================
def endpoint_translate_procedure(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/translate-procedure
    
    Translate colloquial/Indonesian procedure term to standard medical terminology.
    NOW USES ICD-9 AI NORMALIZER SERVICE.
    
    Request:
    {
        "term": "rontgen dada"
    }
    
    Response:
    {
        "status": "success",
        "data": {
            "original": "rontgen dada",
            "translated": "chest x-ray",
            "confidence": "high"
        }
    }
    """
    
    try:
        term = request_data.get("term", "").strip()
        
        if not term:
            return {
                "status": "error",
                "message": "Procedure term is required",
                "data": None
            }
        
        term_lower = term.lower().strip()
        
        # VALIDATION: Check if term is a medication (common mistake)
        if term_lower in MEDICATION_TERMS or any(med in term_lower for med in ['tablet', 'kapsul', 'injeksi', 'mg', 'ml']):
            print(f"[TRANSLATE_PROCEDURE] ⚠️  Detected medication term: {term}")
            return {
                "status": "error",
                "message": f"'{term}' adalah obat/medication, bukan tindakan medis. Silakan masukkan prosedur/tindakan seperti 'injeksi antibiotik', 'pemberian obat IV', dll.",
                "data": None,
                "suggestion": "Input tindakan medis seperti: injeksi, infus, nebulisasi, rontgen, USG, dll."
            }
        
        # Use ICD-9 AI normalizer
        print(f"[TRANSLATE_PROCEDURE] Processing: '{term}'")
        
        from services.icd9_smart_service import ai_normalize_procedure_to_term
        
        result = ai_normalize_procedure_to_term(term)
        
        if result.get("error"):
            return {
                "status": "error",
                "message": result.get("reasoning", "Normalization failed"),
                "data": {
                    "original": term,
                    "translated": term,
                    "confidence": "low"
                }
            }
        
        return {
            "status": "success",
            "data": {
                "original": term,
                "translated": result.get("medical_term", term),
                "confidence": "high" if result.get("confidence", 0) >= 80 else "medium"
            }
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"[TRANSLATE_PROCEDURE] ❌ Error: {error_msg}")
        
        # Return original term on error (graceful degradation)
        return {
            "status": "error",
            "message": f"Translation failed: {error_msg}",
            "data": {
                "original": term,
                "translated": term,
                "confidence": "low"
            }
        }


# ============================================================
# UNUSED CODE - Commented out for fallback mode
# ============================================================
"""
        # PRIORITY 2: Use optimized translation service (with caching)
"""


# ============================================================
# 🔹 ENDPOINT: Translate Medical Procedure (Legacy - for backward compatibility)
# ============================================================
def endpoint_translate_procedure_legacy(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/translate-procedure-legacy
    
    Legacy procedure translation endpoint using synonym dictionary + OpenAI.
    
    Request:
    {
        "term": "usg"
    }
    
    Response:
    {
        "status": "success",
        "result": {
            "medical_term": "ultrasound",
            "synonyms": ["ultrasound", "ultrasonography", "ultrasonic"],
            "confidence": "high"
        }
    }
    """
    
    try:
        term = request_data.get("term", "").strip()
        
        if not term:
            return {
                "status": "error",
                "message": "Procedure term is required",
                "result": None
            }
        
        term_lower = term.lower().strip()
        
        # FAST PATH: Check synonym dictionary first (no API call needed)
        if term_lower in PROCEDURE_SYNONYMS:
            synonyms = PROCEDURE_SYNONYMS[term_lower]
            return {
                "status": "success",
                "result": {
                    "medical_term": synonyms[0],  # Primary term
                    "synonyms": synonyms,  # All related terms for broader search
                    "confidence": "high",
                    "source": "synonym_dictionary"
                }
            }
        
        # SLOW PATH: Use OpenAI for unknown terms (typos, new terms, etc.)
        try:
            from openai import OpenAI
            import os
            
            api_key = os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                return {
                    "status": "error",
                    "message": "OpenAI API key not configured",
                    "result": None
                }
            
            client = OpenAI(api_key=api_key)
            
            # Optimized prompt - shorter and more direct
            prompt = f"""Translate to medical procedure term in English: "{term}"

Examples:
- "ultrason" -> "ultrasonography"
- "operasi usus buntu" -> "appendectomy"
- "rontgen dada" -> "chest x-ray"

Respond with ONLY the medical term, nothing else."""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Medical procedure translator. Output: medical term only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            medical_term = response.choices[0].message.content.strip().strip('"').strip("'")
            
            return {
                "status": "success",
                "result": {
                    "medical_term": medical_term,
                    "confidence": "high",
                    "source": "openai"
                }
            }
        
        except ImportError:
            return {
                "status": "error",
                "message": "OpenAI library not installed",
                "result": None
            }
    
    except Exception as e:
        error_msg = str(e)
        
        # Simplified error handling
        if "api key" in error_msg.lower():
            msg = "Invalid OpenAI API key"
        elif "rate limit" in error_msg.lower():
            msg = "API rate limit exceeded"
        elif "timeout" in error_msg.lower():
            msg = "API timeout"
        else:
            msg = f"Translation failed: {error_msg}"
        
        return {
            "status": "error",
            "message": msg,
            "result": None
        }


# ============================================================
# 🔹 ENDPOINT: Translate Medication with AI Normalization
# ============================================================
def endpoint_translate_medication(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/translate-medication
    
    Translate medication name to Indonesian using FORNAS AI normalization.
    Returns suggestions from FORNAS database.
    
    Request:
    {
        "term": "ceftriaxone"
    }
    
    Response:
    {
        "status": "success",
        "result": {
            "original_term": "ceftriaxone",
            "normalized_name": "Seftriakson",
            "suggestions": [
                {
                    "kode_fornas": "A001",
                    "obat_name": "Seftriakson 1 g Injeksi",
                    "kelas_terapi": "Antibiotik",
                    "confidence": 100
                },
                {
                    "kode_fornas": "A002",
                    "obat_name": "Seftriakson 500 mg Injeksi",
                    "kelas_terapi": "Antibiotik",
                    "confidence": 95
                }
            ],
            "confidence": 100,
            "found_in_db": true,
            "source": "ai_fornas"
        }
    }
    """
    
    try:
        from services.fornas_smart_service import (
            FornasAINormalizer, 
            db_search_by_keywords,
            db_exact_match
        )
        
        term = request_data.get("term", "").strip()
        
        if not term:
            return {
                "status": "error",
                "message": "Medication term is required",
                "result": None
            }
        
        print(f"[TRANSLATE_MEDICATION] Processing: {term}")
        
        # Step 1: Search by keywords to get context
        similar_drugs = db_search_by_keywords(term, limit=50)
        db_context = [drug.obat_name for drug in similar_drugs]
        
        # Step 2: Use AI normalization to get generic name
        normalizer = FornasAINormalizer()
        ai_result = normalizer.normalize_to_indonesian(term, db_context=db_context)
        
        print(f"[TRANSLATE_MEDICATION] AI result: {ai_result}")
        
        # Step 3: Extract generic name from normalized result
        normalized_name = ai_result.get("normalized_name", term)
        
        # Extract generic name (remove dosage/form info)
        # Example: "Fentanil 50 mcg/ml Injeksi" -> "Fentanil"
        import re
        generic_name = re.split(r'\s+\d+', normalized_name)[0].strip()
        
        print(f"[TRANSLATE_MEDICATION] Generic name extracted: {generic_name}")
        
        # Step 4: Search all drugs with this generic name (like ICD hierarchy)
        from models import FornasDrug
        from database_connection import SessionLocal
        
        db = SessionLocal()
        
        try:
            # Search for all dosage forms of this generic drug
            results = db.query(FornasDrug).filter(
                FornasDrug.obat_name.ilike(f"{generic_name}%")
            ).order_by(FornasDrug.obat_name).limit(30).all()
            
            print(f"[TRANSLATE_MEDICATION] Found {len(results)} dosage forms")
            
            # Step 5: Group by generic name (like ICD categories)
            categories = {}
            
            for drug in results:
                # Extract generic name from full name
                generic = re.split(r'\s+\d+', drug.obat_name)[0].strip()
                
                # Use sediaan_kekuatan from database (JSON or text)
                # If it's JSON, extract the value; if text, use directly
                sediaan_kekuatan = drug.sediaan_kekuatan
                if isinstance(sediaan_kekuatan, (dict, list)):
                    # If JSON, convert to string representation
                    import json
                    sediaan_kekuatan = json.dumps(sediaan_kekuatan, ensure_ascii=False)
                elif not sediaan_kekuatan:
                    # Fallback: extract from obat_name if sediaan_kekuatan is NULL
                    sediaan_match = re.search(r'(\d+.*)', drug.obat_name)
                    sediaan_kekuatan = sediaan_match.group(1) if sediaan_match else drug.obat_name
                
                # Generate unique ID: use kode_fornas if exists, else create from obat_name + sediaan
                unique_id = drug.kode_fornas if drug.kode_fornas else f"{drug.obat_name}_{sediaan_kekuatan}".replace(" ", "_")
                
                # DEBUG: Print unique_id untuk setiap drug
                print(f"[TRANSLATE_MEDICATION] Drug: {drug.obat_name} | UniqueID: {unique_id} | Sediaan: {sediaan_kekuatan}")
                
                if generic not in categories:
                    categories[generic] = {
                        "generic_name": generic,
                        "kelas_terapi": drug.kelas_terapi or "",
                        "subkelas_terapi": drug.subkelas_terapi or "",
                        "total_dosage_forms": 0,
                        "confidence": 100,
                        "details": []
                    }
                
                categories[generic]["details"].append({
                    "kode_fornas": unique_id,  # Use unique_id instead
                    "obat_name": drug.obat_name,
                    "sediaan_kekuatan": str(sediaan_kekuatan),
                    "restriksi_penggunaan": drug.restriksi_penggunaan or ""
                })
                categories[generic]["total_dosage_forms"] += 1
            
            # Convert to list and sort by relevance
            categories_list = list(categories.values())
            
            # Sort: exact match first, then by number of dosage forms
            def category_sort_key(cat):
                exact_match = cat["generic_name"].lower() == generic_name.lower()
                return (not exact_match, -cat["total_dosage_forms"])
            
            categories_list.sort(key=category_sort_key)
            
            return {
                "status": "success",
                "result": {
                    "original_term": term,
                    "normalized_generic": generic_name,
                    "categories": categories_list,
                    "confidence": ai_result.get("confidence", 100),
                    "found_in_db": len(categories_list) > 0
                }
            }
        finally:
            db.close()
    
    except Exception as e:
        error_msg = str(e)
        print(f"[TRANSLATE_MEDICATION] ❌ Error: {error_msg}")
        
        return {
            "status": "error",
            "message": f"Medication translation failed: {error_msg}",
            "result": None
        }


# ============================================================
# 🔹 ENDPOINT: ICD-9 Hierarchy (for Tindakan)
# ============================================================


# ============================================================
# 🔍 ICD-10 HIERARCHY ENDPOINT
# ============================================================
def endpoint_icd10_hierarchy(request_data: Dict[str, Any], db) -> Dict[str, Any]:
    """
    Get ICD-10 hierarchy for diagnosis using AI normalization + database search
    
    ENHANCED: Now uses lookup_icd10_smart_with_rag for:
    - AI normalization (Indonesian → English medical terms)
    - Database search with typo tolerance
    - Groups results by HEAD code (e.g., I25 for I25.0, I25.1, etc.)
    """
    try:
        search_term = request_data.get("search_term", "").strip()
        
        if not search_term:
            return {
                "status": "error",
                "message": "search_term is required",
                "data": None
            }
        
        print(f"[ICD10_HIERARCHY] Searching for: '{search_term}'")
        
        # STEP 1: Try smart lookup with AI normalization
        from services.icd10_ai_normalizer import lookup_icd10_smart_with_rag
        smart_result = lookup_icd10_smart_with_rag(search_term)
        
        # Extract matches based on flow type
        matches = []
        
        if smart_result["flow"] == "direct":
            # Single exact match - get subcategories for hierarchy display
            print(f"[ICD10_HIERARCHY] Direct match: {smart_result['selected_code']}")
            subcats = smart_result.get("subcategories", {})
            
            # Add parent
            if subcats.get("parent"):
                matches.append({
                    "code": subcats["parent"]["code"],
                    "name": subcats["parent"]["name"],
                    "source": subcats["parent"]["source"]
                })
            
            # Add all children
            for child in subcats.get("children", []):
                matches.append({
                    "code": child["code"],
                    "name": child["name"],
                    "source": child["source"]
                })
        
        elif smart_result["flow"] in ["suggestion", "fallback_suggestions"]:
            # Multiple suggestions
            print(f"[ICD10_HIERARCHY] Got {smart_result['total_suggestions']} suggestions")
            matches = smart_result.get("suggestions", [])
        
        elif smart_result["flow"] == "ai_direct":
            # AI found match - get subcategories
            print(f"[ICD10_HIERARCHY] AI match: {smart_result['selected_code']} (confidence: {smart_result.get('ai_confidence')})")
            subcats = smart_result.get("subcategories", {})
            
            # Add parent
            if subcats.get("parent"):
                matches.append({
                    "code": subcats["parent"]["code"],
                    "name": subcats["parent"]["name"],
                    "source": subcats["parent"]["source"]
                })
            
            # Add all children
            for child in subcats.get("children", []):
                matches.append({
                    "code": child["code"],
                    "name": child["name"],
                    "source": child["source"]
                })
        
        # STEP 2: If smart lookup failed, fallback to direct database search
        if not matches:
            print(f"[ICD10_HIERARCHY] Smart lookup empty, using fallback db_search_partial")
            matches = db_search_partial(search_term, limit=50)
        
        if not matches:
            print(f"[ICD10_HIERARCHY] No matches found")
            return {
                "status": "success",
                "data": {"categories": []},
                "message": "No matching diagnoses found"
            }
        
        print(f"[ICD10_HIERARCHY] Found {len(matches)} matches from service")
        
        # Group by HEAD code (e.g., "I25" from "I25.1")
        categories_dict = {}
        
        for match in matches:
            code = match["code"]
            name = match["name"]
            
            # Extract HEAD code
            if len(code) > 3 and '.' in code:
                head_code = code.split('.')[0]
            else:
                head_code = code[:3] if len(code) >= 3 else code
            
            # Initialize category if not exists
            if head_code not in categories_dict:
                # Get common term from mapping
                head_common_term = ICD10_COMMON_TERMS.get(head_code)
                
                categories_dict[head_code] = {
                    "headCode": head_code,
                    "headName": name if code == head_code else name.split(',')[0],
                    "commonTerm": head_common_term,
                    "count": 0,
                    "details": []
                }
            
            # Add to details if it's a sub-code
            if code != head_code:
                detail_common_term = ICD10_COMMON_TERMS.get(code) or ICD10_COMMON_TERMS.get(head_code)
                explanation = ICD10_EXPLANATIONS.get(code, "")
                if not explanation:
                    explanation = get_cached_explanation(code, name, "ICD-10")
                
                detail_obj = {
                    "code": code,
                    "name": name,
                    "commonTerm": detail_common_term
                }
                
                if explanation:
                    detail_obj["explanation"] = explanation
                
                categories_dict[head_code]["details"].append(detail_obj)
                categories_dict[head_code]["count"] += 1
            else:
                # This is the HEAD code itself, update headName
                categories_dict[head_code]["headName"] = name
        
        # Convert to list, sort by count (more subcategories = more comprehensive/relevant)
        categories = sorted(
            categories_dict.values(),
            key=lambda x: (-x["count"], x["headCode"])
        )[:15]  # Limit to top 15
        
        print(f"[ICD10_HIERARCHY] Grouped into {len(categories)} categories")
        if categories:
            print(f"[ICD10_HIERARCHY] Top: [{categories[0]['headCode']}] {categories[0]['headName']} ({categories[0]['count']} subcategories)")
        
        data_obj = {"categories": categories}
        return {"status": "success", "data": data_obj}
    
    except Exception as e:
        print(f"[ICD10_HIERARCHY] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "status": "error",
            "message": f"Failed to get ICD-10 hierarchy: {str(e)}",
            "data": None
        }


# ============================================================
# 🔹 ICD-9 HIERARCHY ENDPOINT (untuk Tindakan/Prosedur)
# ============================================================
def endpoint_icd9_hierarchy(request_data: dict, db):
    """
    Get ICD-9 CM procedure codes grouped by HEAD category (2-digit).
    
    ENHANCED: Now uses lookup_icd9_procedure() with AI normalization for:
    - Indonesian → English medical term translation
    - Typo tolerance and informal terms handling
    - Smart database search with confidence scoring
    
    Flow:
    1. Use lookup_icd9_procedure() from service (includes AI normalization)
    2. Group results by HEAD code (2-digit)
    3. Return hierarchical structure
    
    Returns hierarchical structure:
    - Categories: List of HEAD codes (e.g., "47" for Appendectomy)
    - Details: List of specific procedure codes under each category
    """
    try:
        from services.icd9_smart_service import lookup_icd9_procedure, partial_search_icd9
        
        search_term = request_data.get("search_term", "").strip()
        synonyms = request_data.get("synonyms", [])
        
        if not search_term:
            return {
                "status": "error",
                "message": "search_term is required",
                "data": None
            }
        
        print(f"[ICD9_HIERARCHY] Searching for: '{search_term}'")
        if synonyms:
            print(f"[ICD9_HIERARCHY] With synonyms: {synonyms}")
        
        # STEP 1: Try smart lookup with AI normalization
        smart_result = lookup_icd9_procedure(search_term)
        
        # Extract matches based on result type
        matches = []
        
        if smart_result["status"] == "success" and smart_result.get("result"):
            # Single match found - get related procedures for hierarchy
            print(f"[ICD9_HIERARCHY] Direct match: {smart_result['result']['code']}")
            single_match = smart_result["result"]
            
            # Add the direct match
            matches.append(single_match)
            
            # Get HEAD code to find related procedures
            code = single_match["code"]
            if '.' in code:
                head_code = code.split('.')[0]
            else:
                head_code = code[:2] if len(code) >= 2 else code
            
            # Search for related procedures with same HEAD code
            related_matches = partial_search_icd9(head_code, limit=20)
            for related in related_matches:
                if related["code"] != code:  # Don't duplicate
                    matches.append(related)
        
        elif smart_result["status"] == "suggestions" and smart_result.get("suggestions"):
            # Multiple suggestions from AI/database
            print(f"[ICD9_HIERARCHY] Got {len(smart_result['suggestions'])} suggestions")
            matches = smart_result["suggestions"]
        
        # STEP 2: If smart lookup failed or empty, try fallback with partial search
        if not matches:
            print(f"[ICD9_HIERARCHY] Smart lookup empty, using fallback partial_search_icd9")
            matches = partial_search_icd9(search_term, limit=50)
        
        # If synonyms provided, search for them too and merge results
        if synonyms and isinstance(synonyms, list):
            for synonym in synonyms[:2]:  # Max 2 synonyms to avoid overload
                if synonym and synonym.strip():
                    synonym_matches = partial_search_icd9(synonym.strip(), limit=20)
                    # Merge without duplicates (check by code)
                    existing_codes = {m['code'] for m in matches}
                    for syn_match in synonym_matches:
                        if syn_match['code'] not in existing_codes:
                            matches.append(syn_match)
                            existing_codes.add(syn_match['code'])
        
        if not matches:
            print(f"[ICD9_HIERARCHY] No matches found")
            return {
                "status": "success",
                "data": {"categories": []},
                "message": "No matching procedures found"
            }
        
        print(f"[ICD9_HIERARCHY] Found {len(matches)} matches from service")
        
        # Group by HEAD code (2-digit: e.g., "47" from "47.09")
        categories_dict = {}
        
        for match in matches:
            code = match["code"]
            name = match["name"]
            confidence = match.get("confidence", 70)
            
            # Extract HEAD code (first 2 digits: e.g., "47" from "47.09")
            # ICD-9 format: 00-99 (2 chars) or 00.0-99.99 (4-5 chars)
            if '.' in code:
                head_code = code.split('.')[0]  # e.g., "47"
            else:
                head_code = code[:2] if len(code) >= 2 else code
            
            # Initialize category if not exists
            if head_code not in categories_dict:
                # Get common term from mapping
                head_common_term = ICD9_COMMON_TERMS.get(head_code)
                
                categories_dict[head_code] = {
                    "headCode": head_code,
                    "headName": name if code == head_code else name.split(',')[0],
                    "commonTerm": head_common_term,
                    "count": 0,
                    "details": [],
                    "total_confidence": 0  # Aggregate confidence
                }
            
            # Add to details if it's a sub-code
            if code != head_code:
                # Get common term and explanation from mappings
                detail_common_term = ICD9_COMMON_TERMS.get(code) or ICD9_COMMON_TERMS.get(head_code)
                explanation = ICD9_EXPLANATIONS.get(code, "")
                if not explanation:
                    explanation = get_cached_explanation(code, name, "ICD-9")
                
                detail_obj = {
                    "code": code,
                    "name": name,
                    "commonTerm": detail_common_term,
                    "confidence": confidence
                }
                
                if explanation:
                    detail_obj["explanation"] = explanation
                
                categories_dict[head_code]["details"].append(detail_obj)
                categories_dict[head_code]["count"] += 1
                categories_dict[head_code]["total_confidence"] += confidence
            else:
                # This is the HEAD code itself, update headName
                categories_dict[head_code]["headName"] = name
                categories_dict[head_code]["total_confidence"] += confidence
        
        # Sort categories by total confidence (higher = better match)
        categories = sorted(
            categories_dict.values(),
            key=lambda x: (-x["total_confidence"], -x["count"], x["headCode"])
        )[:20]  # Limit to top 20 most relevant
        
        print(f"[ICD9_HIERARCHY] Grouped into {len(categories)} categories (top 20 by relevance)")
        if categories:
            top = categories[0]
            print(f"[ICD9_HIERARCHY] Top result: [{top['headCode']}] {top['headName']}")
            print(f"[ICD9_HIERARCHY] Confidence: {top['total_confidence']}, Count: {top['count']}")
        
        data_obj = {"categories": categories}
        return {"status": "success", "data": data_obj}
    
    except Exception as e:
        print(f"[ICD9_HIERARCHY] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "status": "error",
            "message": f"Failed to get ICD-9 hierarchy: {str(e)}",
            "data": None
        }


# ============================================================
# 📌 NEW OPTIMIZED TRANSLATION ENDPOINTS (Using Translation Service)
# ============================================================
def endpoint_translate_diagnosis_v2(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/translate-diagnosis-v2
    
    Optimized diagnosis translation using multi-layer dictionary + cached DB search.
    ~1500x faster than OpenAI for known terms.
    
    Request:
    {
        "term": "jntung",
        "use_openai": true,  // Optional, default true
        "with_icd10": true   // Optional, include ICD-10 search, default true
    }
    
    Response:
    {
        "status": "success",
        "result": {
            "original": "jntung",
            "english": "heart",
            "icd10_code": "I50.9",
            "icd10_name": "Heart failure, unspecified",
            "source": "id_en_autocorrect",
            "confidence": 85,
            "cache_hit": true,
            "speed": "instant"
        }
    }
    """
    try:
        term = request_data.get("term", "").strip()
        use_openai = request_data.get("use_openai", True)
        with_icd10 = request_data.get("with_icd10", True)
        
        if not term:
            return {
                "status": "error",
                "message": "Term is required",
                "result": None
            }
        
        # Use combined translation + optimized search
        if with_icd10:
            from services.db_search_optimizer import search_with_medical_translation
            
            result = search_with_medical_translation(term, use_openai=use_openai)
            
            if result.get("status") == "success":
                # Combine translation + ICD-10 data
                combined = {
                    "original": term,
                    "english": result["translation"]["english"],
                    "icd10_code": result["icd10"]["code"],
                    "icd10_name": result["icd10"]["name"],
                    "source": result["translation"]["source"],
                    "confidence": result["translation"]["confidence"],
                    "cache_hit": result["icd10"].get("cache_hit", False),
                    "speed": result["speed"]
                }
                
                return {
                    "status": "success",
                    "result": combined
                }
            else:
                # Return suggestions
                return {
                    "status": "suggestions",
                    "result": {
                        "original": term,
                        "english": result["translation"]["english"],
                        "suggestions": result.get("suggestions", []),
                        "total": result.get("total", 0),
                        "source": result["translation"]["source"],
                        "confidence": result["translation"]["confidence"]
                    }
                }
        else:
            # Translation only (no ICD-10 search)
            from services.medical_translation_service import translate_diagnosis
            
            result = translate_diagnosis(term, use_openai=use_openai)
            
            return {
                "status": "success",
                "result": result
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Translation failed: {str(e)}",
            "result": None
        }


def endpoint_translate_procedure_v2(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/translate-procedure-v2
    
    Optimized procedure translation using multi-layer dictionary.
    
    Request:
    {
        "term": "cuci darah",
        "use_openai": true
    }
    
    Response:
    {
        "status": "success",
        "result": {
            "original": "cuci darah",
            "english": "hemodialysis",
            "source": "procedure_dictionary",
            "confidence": 100
        }
    }
    """
    try:
        from services.medical_translation_service import translate_procedure
        
        term = request_data.get("term", "").strip()
        use_openai = request_data.get("use_openai", True)
        
        if not term:
            return {
                "status": "error",
                "message": "Term is required",
                "result": None
            }
        
        result = translate_procedure(term, use_openai=use_openai)
        
        return {
            "status": "success",
            "result": result
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Translation failed: {str(e)}",
            "result": None
        }


def endpoint_search_medical_terms(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/search-medical-terms
    
    Search medical terms by partial match.
    Useful for autocomplete/suggestions.
    
    Request:
    {
        "query": "heart",
        "limit": 10
    }
    
    Response:
    {
        "status": "success",
        "result": {
            "matches": [
                {"term": "heart failure", "icd10_code": "I50.9"},
                {"term": "heart disease", "icd10_code": "I51.9"},
                ...
            ],
            "total": 10
        }
    }
    """
    try:
        from services.medical_translation_service import search_medical_terms
        
        query = request_data.get("query", "").strip()
        limit = request_data.get("limit", 10)
        
        if not query:
            return {
                "status": "error",
                "message": "Query is required",
                "result": None
            }
        
        matches = search_medical_terms(query, limit=limit)
        
        return {
            "status": "success",
            "result": {
                "matches": matches,
                "total": len(matches)
            }
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Search failed: {str(e)}",
            "result": None
        }


def endpoint_translation_stats(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    GET /api/lite/translation-stats
    
    Get translation service statistics including cache performance.
    
    Response:
    {
        "status": "success",
        "result": {
            "translation": {
                "indonesian_english_terms": 198,
                "english_icd10_terms": 18480,
                "procedure_synonyms": 62,
                "total_coverage": 18740
            },
            "cache": {
                "cache_hits": 150,
                "cache_misses": 25,
                "hit_rate_percent": 85.71,
                "icd10_codes_cached": 18543,
                "icd10_names_cached": 18480,
                "search_results_cached": 45,
                "cache_memory_kb": 4500
            }
        }
    }
    """
    try:
        from services.medical_translation_service import get_statistics as get_trans_stats
        from services.db_search_optimizer import get_cache_statistics
        
        trans_stats = get_trans_stats()
        cache_stats = get_cache_statistics()
        
        return {
            "status": "success",
            "result": {
                "translation": trans_stats,
                "cache": cache_stats
            }
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get statistics: {str(e)}",
            "result": None
        }


# ============================================================
# 📌 ENDPOINT REGISTRY - untuk integrasi dengan main router
# ============================================================
# IMPORTANT: Dictionary ini HARUS di akhir file setelah semua fungsi didefinisikan
LITE_ENDPOINTS = {
    "validate_form": endpoint_validate_form,
    "parse_text": endpoint_parse_text,
    "analyze_single": endpoint_analyze_single,
    "analyze_batch": endpoint_analyze_batch,
    "get_history": endpoint_get_history,
    "load_history_detail": endpoint_load_history_detail,
    "delete_history": endpoint_delete_history,
    "export_results": endpoint_export_results,
    # ICD-10 endpoints
    "icd10_lookup": endpoint_icd10_lookup,
    "icd10_select": endpoint_icd10_select,
    "icd10_statistics": endpoint_icd10_statistics,
    # ICD-9 endpoints
    "icd9_lookup": endpoint_icd9_lookup,
    "icd9_hierarchy": endpoint_icd9_hierarchy,
    # FORNAS validation endpoint
    "validate_fornas": endpoint_validate_fornas,
    # Dokumen Wajib endpoints
    "get_dokumen_wajib": endpoint_get_dokumen_wajib,
    "get_all_diagnosis": endpoint_get_all_diagnosis,
    "search_diagnosis": endpoint_search_diagnosis,
    # Medical Translation endpoint (legacy - uses OpenAI)
    "translate_medical": endpoint_translate_medical,
    "translate_procedure": endpoint_translate_procedure,
    # Optimized Translation endpoints (v2 - uses dictionary + OpenAI fallback)
    "translate_diagnosis_v2": endpoint_translate_diagnosis_v2,
    "translate_procedure_v2": endpoint_translate_procedure_v2,
    "search_medical_terms": endpoint_search_medical_terms,
    "translation_stats": endpoint_translation_stats,
    "predict_inacbg": None  # Will be defined below
}


# ============================================================
# 🏥 INA-CBG PREDICTION ENDPOINT
# ============================================================

def endpoint_predict_inacbg(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Endpoint untuk memprediksi kode INA-CBG beserta tarifnya
    
    Request format:
    {
        "icd10_primary": "I21.0",
        "icd10_secondary": ["E11.9", "I25.1"],
        "icd9_list": ["36.06", "36.07"],
        "layanan": "RI",
        "regional": "1",
        "kelas_rs": "B",
        "tipe_rs": "Pemerintah",
        "kelas_bpjs": 1
    }
    
    Response:
    {
        "status": "success",
        "data": {
            "cbg_code": "I-4-10-II",
            "description": "Infark Miocard Akut Sedang",
            "tarif": 12500000,
            ...
        }
    }
    """
    from services.inacbg_grouper_service import predict_inacbg
    
    try:
        # Extract parameters
        icd10_primary = request_data.get("icd10_primary")
        icd10_secondary = request_data.get("icd10_secondary", [])
        icd9_list = request_data.get("icd9_list", [])
        layanan = request_data.get("layanan", "RI")
        regional = request_data.get("regional", "1")
        kelas_rs = request_data.get("kelas_rs", "B")
        tipe_rs = request_data.get("tipe_rs", "Pemerintah")
        kelas_bpjs = request_data.get("kelas_bpjs", 1)
        
        # Validate required fields
        if not icd10_primary:
            return {
                "status": "error",
                "message": "icd10_primary is required"
            }
        
        # Call prediction service
        result = predict_inacbg(
            icd10_primary=icd10_primary,
            icd10_secondary=icd10_secondary,
            icd9_list=icd9_list,
            layanan=layanan,
            regional=regional,
            kelas_rs=kelas_rs,
            tipe_rs=tipe_rs,
            kelas_bpjs=kelas_bpjs
        )
        
        # Format response
        if result.get("success"):
            return {
                "status": "success",
                "data": {
                    "cbg_code": result.get("cbg_code"),
                    "description": result.get("description"),
                    "tarif": result.get("tarif"),
                    "tarif_detail": result.get("tarif_detail"),
                    "breakdown": result.get("breakdown"),
                    "matching_detail": result.get("matching_detail"),
                    "classification": result.get("classification"),
                    "warnings": result.get("warnings", [])
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": result.get("error", "Failed to predict INA-CBG"),
                "details": result
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error in INA-CBG prediction: {str(e)}"
        }


# Register the endpoint
LITE_ENDPOINTS["predict_inacbg"] = endpoint_predict_inacbg


# ============================================================
# 📌 MAIN HANDLER - untuk dipanggil dari FastAPI/Flask router
# ============================================================
def handle_lite_request(endpoint_name: str, request_data: Dict[str, Any], db=None) -> Dict[str, Any]:
    """
    Universal handler untuk semua AI-CLAIM Lite endpoints.
    
    Usage:
        result = handle_lite_request("analyze_single", request_data)
    """
    if endpoint_name not in LITE_ENDPOINTS:
        return {
            "status": "error",
            "message": f"Unknown endpoint: {endpoint_name}"
        }
    
    handler = LITE_ENDPOINTS[endpoint_name]
    
    # Check if endpoint needs db parameter
    if endpoint_name in ["icd9_hierarchy"]:
        return handler(request_data, db)
    else:
        return handler(request_data)
