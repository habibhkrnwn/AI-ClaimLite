# core_engine/ai_claim_lite_config.py

"""
AI-CLAIM Lite Configuration
Settings untuk customization dan feature flags
"""

from typing import Dict, List, Any
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ============================================================
# 🔐 ENVIRONMENT CONFIGURATION
# ============================================================
class Config:
    """Configuration loaded from environment variables"""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
    APP_ENV = os.getenv("APP_ENV", "development")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", "8000"))


# ============================================================
# 🎯 FEATURE FLAGS - Enable/Disable fitur tertentu
# ============================================================
FEATURE_FLAGS = {
    # Core Features
    "text_parser": True,           # Enable parsing free text
    "form_input": True,            # Enable 3-field form input
    "batch_analyzer": True,        # Enable batch/Excel import
    
    # Advanced Features
    "history_save": True,          # Enable save to history
    "history_search": True,        # Enable search dalam history
    "export_excel": True,          # Enable export ke Excel
    "export_pdf": True,            # Enable export ke PDF
    
    # AI Features
    "ai_insights": True,           # Enable AI-generated insights
    "ai_consistency": True,        # Enable AI consistency check
    
    # Integration Features
    "multilayer_rules": True,      # Enable multilayer rules dari DB
    "icd9_mapping": True,          # Enable ICD-9 smart mapping
    "icd10_mapping": True,         # Enable ICD-10 WHO→BPJS mapping
    "inacbg_lookup": False,        # Enable INA-CBG tarif lookup (future)
}


# ============================================================
# 📊 PANEL CONFIGURATION - Kustomisasi 7 Panel Utama
# ============================================================
PANEL_CONFIG = {
    "klasifikasi": {
        "enabled": True,
        "title": "Klasifikasi & Coding",
        "icon": "📋",
        "fields": ["diagnosis", "tindakan", "obat", "confidence"],
        "color": "#3b82f6"
    },
    
    "validasi_klinis": {
        "enabled": True,
        "title": "Validasi Klinis (CP/PNPK/FORNAS)",
        "icon": "🩺",
        "fields": ["sesuai_cp", "sesuai_fornas", "catatan"],
        "color": "#10b981"
    },
    
    "cp_ringkas": {
        "enabled": True,
        "title": "Ringkasan CP Nasional",
        "icon": "📘",
        "fields": ["step_by_step"],
        "color": "#8b5cf6"
    },
    
    "checklist_dokumen": {
        "enabled": True,
        "title": "Checklist Dokumen Wajib",
        "icon": "📎",
        "fields": ["required_docs"],
        "color": "#06b6d4"
    },
    
    "insight_ai": {
        "enabled": True,
        "title": "Insight AI",
        "icon": "💡",
        "fields": ["actionable_insights"],
        "color": "#ec4899"
    },
    
    "konsistensi": {
        "enabled": True,
        "title": "Konsistensi Klinis",
        "icon": "📈",
        "fields": ["tingkat", "detail"],
        "color": "#14b8a6"
    }
}


# ============================================================
# 🔍 TEXT PARSER CONFIGURATION
# ============================================================
PARSER_CONFIG = {
    # Keywords untuk identifikasi diagnosis
    "diagnosis_keywords": [
        "diagnosis", "dx", "penyakit", "keluhan", "dengan diagnosis",
        "didiagnosa", "menderita", "sakit"
    ],
    
    # Keywords untuk identifikasi tindakan
    "tindakan_keywords": [
        "tindakan", "prosedur", "terapi", "tx", "dilakukan",
        "nebulisasi", "nebulizer", "rontgen", "radiologi", "x-ray",
        "ct scan", "mri", "kultur", "culture", "lab", "pemeriksaan",
        "ventilator", "ventilasi", "infus", "iv line", "kateter",
        "operasi", "bedah", "endoskopi", "kolonoskopi"
    ],
    
    # Keywords untuk identifikasi obat
    "obat_keywords": [
        "obat", "diberikan", "mendapat", "terapi",
        "injeksi", "inj", "infus", "iv", "tablet", "tab",
        "sirup", "kapsul", "salep", "antibiotik"
    ],
    
    # Common antibiotics pattern
    "antibiotic_patterns": [
        r'\b\w*(cillin|mycin|xone|zole|floxacin)\b',  # -cillin, -mycin, etc.
        r'\b(Ceftriaxone|Cefotaxime|Amoxicillin|Azithromycin|Levofloxacin|Ciprofloxacin)\b'
    ],
    
    # Common procedures pattern
    "procedure_patterns": [
        r'(nebulisasi|nebulizer)',
        r'(rontgen|radiologi|x-?ray)\s*(thorax|paru|chest|abdomen)?',
        r'(ct\s*scan|mri)\s*(brain|head|thorax|abdomen)?',
        r'(kultur|culture)\s*(darah|sputum|urine|feses)?',
        r'(ventilator|ventilasi)\s*(mekanik)?',
        r'(pemeriksaan|cek)\s*(lab|darah|urine|feses)'
    ]
}


# ============================================================
# 📋 CHECKLIST TEMPLATES - per diagnosis type
# ============================================================
CHECKLIST_TEMPLATES = {
    "pneumonia": [
        {"item": "Resume Medis", "required": True, "category": "administratif"},
        {"item": "Hasil Lab Darah Lengkap", "required": True, "category": "laboratorium"},
        {"item": "Radiologi Thoraks (AP/PA)", "required": True, "category": "radiologi"},
        {"item": "Hasil Kultur Sputum", "required": False, "category": "laboratorium"},
        {"item": "AGD (Analisa Gas Darah)", "required": False, "category": "laboratorium"},
        {"item": "Resep Obat", "required": True, "category": "farmasi"}
    ],
    
    "tifoid": [
        {"item": "Resume Medis", "required": True, "category": "administratif"},
        {"item": "Widal Test", "required": True, "category": "laboratorium"},
        {"item": "Kultur Darah", "required": True, "category": "laboratorium"},
        {"item": "Lab Darah Lengkap", "required": True, "category": "laboratorium"},
        {"item": "Resep Obat", "required": True, "category": "farmasi"}
    ],
    
    "dbd": [
        {"item": "Resume Medis", "required": True, "category": "administratif"},
        {"item": "Trombosit Serial", "required": True, "category": "laboratorium"},
        {"item": "NS1 Antigen/IgM IgG", "required": True, "category": "laboratorium"},
        {"item": "Hematokrit Serial", "required": True, "category": "laboratorium"},
        {"item": "USG Abdomen", "required": False, "category": "radiologi"},
        {"item": "Resep Obat", "required": True, "category": "farmasi"}
    ],
    
    "default": [
        {"item": "Resume Medis", "required": True, "category": "administratif"},
        {"item": "Hasil Lab Penunjang", "required": True, "category": "laboratorium"},
        {"item": "Radiologi (jika ada)", "required": False, "category": "radiologi"},
        {"item": "Resep Obat", "required": True, "category": "farmasi"}
    ]
}


# ============================================================
# 🎨 UI CONFIGURATION - Colors & Icons
# ============================================================
UI_CONFIG = {
    "colors": {
        "primary": "#3b82f6",
        "success": "#10b981",
        "warning": "#f59e0b",
        "error": "#ef4444",
        "info": "#06b6d4"
    },
    
    "consistency_colors": {
        "Tinggi": "#10b981",
        "Sedang": "#f59e0b",
        "Rendah": "#ef4444"
    },
    
    "status_icons": {
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "info": "ℹ️"
    }
}


# ============================================================
# ⚙️ ANALYSIS CONFIGURATION - AI & Rules Settings
# ============================================================
ANALYSIS_CONFIG = {
    # AI Model Settings
    "ai_model": "gpt-4o-mini",
    "ai_temperature": 0.3,
    "ai_max_tokens": 1000,
    
    # Confidence Thresholds
    "confidence_thresholds": {
        "high": 0.85,      # ≥85% = Tinggi
        "medium": 0.70,    # 70-84% = Sedang
        "low": 0.50        # <70% = Rendah
    },
    
    # Multilayer Rules Priority
    "rule_priority": {
        "rs": 1,           # Highest priority
        "regional": 2,
        "nasional": 3,
        "permenkes": 4,
        "default": 5       # Lowest priority
    },
    
    # Batch Processing
    "batch_max_size": 100,  # Max 100 klaim per batch
    "batch_timeout": 300    # 5 minutes timeout
}


# ============================================================
# 💾 HISTORY CONFIGURATION
# ============================================================
HISTORY_CONFIG = {
    "enabled": True,
    "max_items": 10,           # Simpan max 10 history terakhir
    "auto_save": True,         # Auto-save setiap analisis
    "retention_days": 30,      # Hapus history >30 hari
    "storage_type": "database" # "database" atau "localStorage"
}


# ============================================================
# 📤 EXPORT CONFIGURATION
# ============================================================
EXPORT_CONFIG = {
    "excel": {
        "enabled": True,
        "format": "xlsx",
        "columns": [
            "No", "Nama Pasien", "ICD-10", "ICD-9", "Fornas",
            "Konsistensi", "Insight Singkat"
        ]
    },
    
    "pdf": {
        "enabled": True,
        "template": "standard",  # "standard" atau "detailed"
        "include_charts": False,
        "include_regulations": False
    }
}


# ============================================================
# 🔐 VALIDATION RULES
# ============================================================
VALIDATION_RULES = {
    # Input validation
    "min_text_length": 10,        # Min 10 karakter untuk free text
    "max_text_length": 5000,      # Max 5000 karakter
    
    # Diagnosis validation
    "diagnosis_required": True,
    "diagnosis_min_length": 3,
    
    # Batch validation
    "batch_required_columns": ["Diagnosis"],  # Column wajib di Excel
    "batch_optional_columns": ["Nama", "Tindakan", "Obat"]
}


# ============================================================
# 🌐 INTEGRATION CONFIG - untuk RS yang sudah pakai AI-CLAIM
# ============================================================
INTEGRATION_CONFIG = {
    "use_full_engine": False,      # False = Lite standalone, True = integrate dengan AI-CLAIM full
    "api_endpoint": None,           # Endpoint AI-CLAIM full jika integrasi
    "api_timeout": 30,              # Timeout untuk API calls
    "fallback_to_lite": True       # Fallback ke Lite jika full engine error
}


# ============================================================
# 📝 HELPER FUNCTIONS
# ============================================================
def get_feature_flag(feature_name: str) -> bool:
    """Check if a feature is enabled"""
    return FEATURE_FLAGS.get(feature_name, False)


def get_panel_config(panel_name: str) -> Dict[str, Any]:
    """Get configuration for a specific panel"""
    return PANEL_CONFIG.get(panel_name, {})


def get_checklist_template(diagnosis: str) -> List[Dict[str, Any]]:
    """Get checklist template berdasarkan diagnosis"""
    # Normalize diagnosis name
    diagnosis_lower = diagnosis.lower()
    
    # Match dengan template
    for key, template in CHECKLIST_TEMPLATES.items():
        if key in diagnosis_lower:
            return template
    
    # Default template
    return CHECKLIST_TEMPLATES["default"]


def get_consistency_color(consistency: str) -> str:
    """Get color code untuk consistency level"""
    return UI_CONFIG["consistency_colors"].get(consistency, "#6b7280")


def validate_input(payload: Dict[str, Any], mode: str) -> Dict[str, Any]:
    """
    Validate input payload berdasarkan mode.
    
    Returns:
        {"valid": True/False, "errors": [...]}
    """
    errors = []
    
    if mode == "text":
        text = payload.get("input_text", "")
        if len(text) < VALIDATION_RULES["min_text_length"]:
            errors.append(f"Teks terlalu pendek (min {VALIDATION_RULES['min_text_length']} karakter)")
        if len(text) > VALIDATION_RULES["max_text_length"]:
            errors.append(f"Teks terlalu panjang (max {VALIDATION_RULES['max_text_length']} karakter)")
    
    elif mode == "form":
        diagnosis = payload.get("diagnosis", "")
        if VALIDATION_RULES["diagnosis_required"] and not diagnosis:
            errors.append("Diagnosis wajib diisi")
        elif len(diagnosis) < VALIDATION_RULES["diagnosis_min_length"]:
            errors.append(f"Diagnosis terlalu pendek (min {VALIDATION_RULES['diagnosis_min_length']} karakter)")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def get_config_summary() -> Dict[str, Any]:
    """Get summary of current configuration"""
    return {
        "version": "AI-CLAIM Lite v1.0",
        "features_enabled": sum(1 for v in FEATURE_FLAGS.values() if v),
        "total_features": len(FEATURE_FLAGS),
        "panels_enabled": sum(1 for p in PANEL_CONFIG.values() if p.get("enabled", False)),
        "ai_model": ANALYSIS_CONFIG["ai_model"],
        "history_enabled": HISTORY_CONFIG["enabled"],
        "export_formats": ["excel" if EXPORT_CONFIG["excel"]["enabled"] else None,
                          "pdf" if EXPORT_CONFIG["pdf"]["enabled"] else None],
        "integration_mode": "standalone" if not INTEGRATION_CONFIG["use_full_engine"] else "integrated"
    }


# ============================================================
# 🧪 TESTING
# ============================================================
if __name__ == "__main__":
    print("🔧 AI-CLAIM Lite Configuration Summary\n")
    
    summary = get_config_summary()
    print("📊 Configuration:")
    for key, value in summary.items():
        print(f"  • {key}: {value}")
    
    print("\n✅ Features Enabled:")
    for feature, enabled in FEATURE_FLAGS.items():
        if enabled:
            print(f"  ✓ {feature}")
    
    print("\n📋 Panels:")
    for panel_name, config in PANEL_CONFIG.items():
        if config.get("enabled"):
            print(f"  {config['icon']} {config['title']}")
    
    print("\n🏥 Sample Checklist (Pneumonia):")
    checklist = get_checklist_template("pneumonia")
    for item in checklist:
        req = "WAJIB" if item["required"] else "OPSIONAL"
        print(f"  {'☑' if item['required'] else '☐'} {item['item']} [{req}]")
    
    print("\n✅ Configuration loaded successfully!")