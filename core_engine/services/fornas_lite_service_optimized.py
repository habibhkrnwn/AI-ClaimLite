# services/fornas_lite_service_optimized.py

"""
OPTIMIZED Fornas Lite Validator
Validates ALL drugs in single AI call instead of sequential calls per drug

UPDATED: Now uses fornas_smart_service.py for better English → Indonesian matching
"""

import json
import os
import re
import logging
from typing import Dict, List, Any
from openai import OpenAI

# Use new smart service instead of old fornas_service
from services.fornas_smart_service import validate_fornas

logger = logging.getLogger(__name__)


class FornasLiteValidatorOptimized:
    """
    OPTIMIZED: Validate multiple drugs in single AI batch call
    """
    
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
    
    
    def validate_drugs_lite(
        self,
        drug_list: List[str],
        diagnosis_icd10: str,
        diagnosis_name: str,
        include_summary: bool = True
    ) -> Dict[str, Any]:
        """
        Main validation - OPTIMIZED with batch AI call
        
        NEW: Uses fornas_smart_service for better matching:
        - Auto normalize English → Indonesian
        - AI-powered RAG matching
        - Guaranteed DB validation
        """
        if not drug_list:
            return {
                "fornas_validation": [],
                "summary": {
                    "total_obat": 0,
                    "sesuai": 0,
                    "perlu_justifikasi": 0,
                    "non_fornas": 0,
                    "error": "Tidak ada obat untuk divalidasi"
                }
            }
        
        logger.info(f"[FORNAS_OPTIMIZED] Starting batch validation for {len(drug_list)} drugs")
        
        # Use new smart service (handles matching + validation + AI normalization)
        result = validate_fornas(
            drug_list=drug_list,
            diagnosis_icd10=diagnosis_icd10,
            diagnosis_name=diagnosis_name
        )
        
        logger.info(f"[FORNAS_OPTIMIZED] ✓ Completed smart validation")
        
        return {
            "fornas_validation": result.get("fornas_validation", []),
            "fornas_summary": result.get("fornas_summary", {})
        }


# Public interface
def validate_fornas_lite_optimized(
    drug_list: List[str],
    diagnosis_icd10: str,
    diagnosis_name: str
) -> Dict:
    """
    OPTIMIZED validation - uses fornas_smart_service
    
    Usage:
        result = validate_fornas_lite_optimized(
            drug_list=["Ceftriaxone 1g IV", "Paracetamol 500mg"],
            diagnosis_icd10="J18.9",
            diagnosis_name="Pneumonia berat"
        )
    """
    validator = FornasLiteValidatorOptimized()
    return validator.validate_drugs_lite(
        drug_list=drug_list,
        diagnosis_icd10=diagnosis_icd10,
        diagnosis_name=diagnosis_name,
        include_summary=True
    )

