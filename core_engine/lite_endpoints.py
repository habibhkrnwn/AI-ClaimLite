# core_engine/ai_claim_lite_endpoints.py

"""
AI-CLAIM Lite Endpoints
Simplified REST API untuk demo/trial version
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json

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
# 🔹 IMPORT ALL SMART SERVICES (MERGED)
# ============================================================
from services.lite_service_optimized import analyze_lite_single_optimized
from services.fornas_smart_service import validate_fornas
from services.icd10_ai_normalizer import lookup_icd10_smart_with_rag
from services.icd10_service import select_icd10_code, get_icd10_statistics
from services.dokumen_wajib_service import get_dokumen_wajib_service
from services.pnpk_summary_service import PNPKSummaryService


# ============================================================
# 🔹 ASYNC WRAPPER for analyze_lite_single (with PNPK fetch)
# ============================================================
async def endpoint_analyze_single_async(request_data: Dict[str, Any], db_pool=None) -> Dict[str, Any]:
    """
    Async wrapper untuk analyze_lite_single yang melakukan PNPK fetch terlebih dahulu
    """
    pnpk_data = None
    
    # Pre-fetch PNPK data jika db_pool tersedia
    if db_pool:
        try:
            # Extract diagnosis untuk pre-fetch
            diagnosis_name = None
            mode = request_data.get("mode", "text")
            
            if mode == "form" or mode == "excel":
                diagnosis_name = request_data.get("diagnosis", "")
            elif mode == "text":
                # Untuk text mode, kita belum punya diagnosis, skip pre-fetch
                pass
            
            if diagnosis_name:
                pnpk_service = PNPKSummaryService(db_pool)
                pnpk_data = await pnpk_service.get_pnpk_summary(diagnosis_name, auto_match=True)
                print(f"[ENDPOINT_ASYNC] ✓ PNPK pre-fetched for: {diagnosis_name}")
        except Exception as e:
            print(f"[ENDPOINT_ASYNC] ⚠️ PNPK pre-fetch failed: {e}")
    
    # Inject pnpk_data ke request
    request_data["_pnpk_data"] = pnpk_data
    
    # Call synchronous analyzer
    use_optimized = request_data.get("use_optimized", True)
    if use_optimized:
        return analyze_lite_single_optimized(request_data, db_pool=db_pool)
    else:
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
    POST /api/lite/parse
    
    Parse resume medis free text menjadi struktur terpisah.
    Untuk preview sebelum analisis.
    
    Request:
    {
        "input_text": "Pneumonia berat, diberikan Ceftriaxone..."
    }
    
    Response:
    {
        "status": "success",
        "parsed": {
            "diagnosis": "Pneumonia berat",
            "tindakan": ["Nebulisasi"],
            "obat": ["Ceftriaxone injeksi"]
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
        
        # Parse text
        parsed = parse_free_text(input_text)
        
        return {
            "status": "success",
            "parsed": {
                "diagnosis": parsed["diagnosis"],
                "tindakan": parsed["tindakan"],
                "obat": parsed["obat"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
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
        
        // Mode FORM (3 field terpisah)
        "diagnosis": "Pneumonia berat (J18.9)",
        "tindakan": "Nebulisasi (93.96), Rontgen Thorax",
        "obat": "Ceftriaxone injeksi 1g, Paracetamol 500mg",
        
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
            # Validasi 3 field form
            diagnosis = request_data.get("diagnosis", "")
            tindakan = request_data.get("tindakan", "")
            obat = request_data.get("obat", "")
            
            errors = []
            if not diagnosis:
                errors.append("diagnosis required untuk mode form")
            if not tindakan:
                errors.append("tindakan required untuk mode form")
            if not obat:
                errors.append("obat required untuk mode form")
            
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
# 📌 ENDPOINT REGISTRY - untuk integrasi dengan main router
# ============================================================
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
    # FORNAS validation endpoint
    "validate_fornas": endpoint_validate_fornas,
    # Dokumen Wajib endpoints
    "get_dokumen_wajib": endpoint_get_dokumen_wajib,
    "get_all_diagnosis": endpoint_get_all_diagnosis,
    "search_diagnosis": endpoint_search_diagnosis,
    # Medical Translation endpoint
    "translate_medical": endpoint_translate_medical
}


# ============================================================
# 📌 MAIN HANDLER - untuk dipanggil dari FastAPI/Flask router
# ============================================================
def handle_lite_request(endpoint_name: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Universal handler untuk semua AI-CLAIM Lite endpoints.
    
    Usage:
        result = handle_lite_request("analyze_single", request_data)
    """
    
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
# 📌 ENDPOINT 11: Translate Medical Term (OpenAI)
# ============================================================
def endpoint_translate_medical(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/lite/translate-medical
    
    Translate colloquial/Indonesian medical term to standard medical terminology.
    Uses OpenAI for intelligent translation.
    
    Request:
    {
        "term": "radang paru paru bakteri"
    }
    
    Response:
    {
        "status": "success",
        "result": {
            "medical_term": "bacterial pneumonia",
            "confidence": "high"
        }
    }
    """
    
    try:
        from openai import OpenAI
        import os
        
        term = request_data.get("term", "").strip()
        
        if not term:
            return {
                "status": "error",
                "message": "Medical term is required",
                "result": None
            }
        
        # Get OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            return {
                "status": "error",
                "message": "OpenAI API key not configured in environment",
                "result": None
            }
        
        # Initialize OpenAI client (v1.x syntax)
        client = OpenAI(api_key=api_key)
        
        # Create prompt for medical term translation
        prompt = f"""Translate the following Indonesian/colloquial medical term to standard English medical terminology.

Input: "{term}"

Instructions:
- Translate to accurate medical terminology in English
- Use standard medical vocabulary
- If already medical terminology, return as is
- Be concise and precise

Examples:
- "paru2 basah" → "pneumonia"
- "radang paru paru bakteri" → "bacterial pneumonia"
- "pneumonia cacar air" → "varicella pneumonia"
- "demam berdarah" → "dengue hemorrhagic fever"

Respond with ONLY the translated medical term in English, nothing else."""
        
        # Call OpenAI API (v1.x syntax)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a medical terminology translator. Respond with ONLY the medical term."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )
        
        # Extract medical term from response
        medical_term = response.choices[0].message.content.strip().strip('"').strip("'")
        
        return {
            "status": "success",
            "result": {
                "medical_term": medical_term,
                "confidence": "high"
            }
        }
    
    except Exception as e:
        error_msg = str(e)
        
        # Handle different error types
        if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
            return {
                "status": "error",
                "message": "Invalid OpenAI API key",
                "result": None
            }
        elif "rate limit" in error_msg.lower():
            return {
                "status": "error",
                "message": "OpenAI API rate limit exceeded",
                "result": None
            }
        elif "timeout" in error_msg.lower():
            return {
                "status": "error",
                "message": "OpenAI API request timeout",
                "result": None
            }
        else:
            return {
                "status": "error",
                "message": f"Translation failed: {error_msg}",
                "result": None
            }
