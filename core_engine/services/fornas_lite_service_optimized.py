# services/fornas_lite_service_optimized.py

"""
OPTIMIZED Fornas Lite Validator
Validates ALL drugs in single AI call instead of sequential calls per drug
"""

import json
import os
import re
import logging
from typing import Dict, List, Any
from openai import OpenAI

from services.fornas_service import match_multiple_obat

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
        
        # Step 1: Parse drug input
        parsed_drugs = self._parse_drug_input(drug_list)
        
        # Step 2: Match dengan FORNAS database
        fornas_matched = match_multiple_obat(parsed_drugs, threshold=85)
        logger.info(f"[FORNAS_OPTIMIZED] ✓ Matched {len(fornas_matched)} drugs with database")
        
        # Step 3: BATCH AI validation (1 call for all drugs)
        validation_results = self._validate_all_drugs_batch(
            fornas_matched=fornas_matched,
            diagnosis_icd10=diagnosis_icd10,
            diagnosis_name=diagnosis_name
        )
        logger.info(f"[FORNAS_OPTIMIZED] ✓ Completed batch AI validation")
        
        # Step 4: Build output
        output = {"fornas_validation": validation_results}
        
        if include_summary:
            output["summary"] = self._generate_summary(validation_results)
        
        return output
    
    
    def _parse_drug_input(self, drug_list: List[str]) -> List[str]:
        """Parse and clean drug names"""
        cleaned = []
        
        for drug in drug_list:
            if not drug or drug.strip() == "":
                continue
            
            # Remove dosage (e.g., "1g", "500mg")
            drug_clean = re.sub(r'\d+\s*(mg|g|ml|mcg|iu|cc)\b', '', drug, flags=re.IGNORECASE)
            
            # Remove route (e.g., "IV", "oral")
            drug_clean = re.sub(r'\b(iv|im|sc|po|oral|injeksi|infus|tablet|kapsul)\b', '', drug_clean, flags=re.IGNORECASE)
            
            # Clean whitespace
            drug_clean = drug_clean.strip()
            
            if drug_clean:
                cleaned.append(drug_clean)
        
        return cleaned
    
    
    def _validate_all_drugs_batch(
        self,
        fornas_matched: List[Dict],
        diagnosis_icd10: str,
        diagnosis_name: str
    ) -> List[Dict]:
        """
        OPTIMIZED: Validate ALL drugs in single AI call
        """
        # Prepare drug list for AI
        drugs_to_validate = []
        non_fornas_drugs = []
        
        for idx, matched in enumerate(fornas_matched, 1):
            if not matched.get("found", False):
                # Drug NOT in FORNAS - no AI needed
                non_fornas_drugs.append({
                    "no": idx,
                    "nama_obat": matched.get("nama_generik", "Unknown"),
                    "kelas_terapi": "Tidak ditemukan di FORNAS",
                    "status_fornas": "❌ Non-Fornas",
                    "catatan_ai": "Obat tidak terdaftar dalam Formularium Nasional.",
                    "sumber_regulasi": "-"
                })
            else:
                # Drug found - prepare for batch AI validation
                drugs_to_validate.append({
                    "index": idx,
                    "nama_obat": matched.get("nama_generik", "Unknown"),
                    "kelas_terapi": matched.get("kelas_terapi", "Tidak tersedia"),
                    "sumber_regulasi_db": matched.get("sumber_regulasi", "FORNAS 2023")
                })
        
        # If no drugs to validate with AI, return non-fornas only
        if not drugs_to_validate:
            return non_fornas_drugs
        
        # Call AI for batch validation
        try:
            ai_results = self._call_batch_ai_validation(
                drugs=drugs_to_validate,
                diagnosis_icd10=diagnosis_icd10,
                diagnosis_name=diagnosis_name
            )
            
            # Merge AI results with non-fornas drugs
            all_results = non_fornas_drugs + ai_results
            
            # Sort by index number
            all_results.sort(key=lambda x: x["no"])
            
            return all_results
            
        except Exception as e:
            logger.error(f"[FORNAS_OPTIMIZED] ❌ Batch AI validation failed: {e}")
            
            # Fallback: return all as "Perlu Justifikasi"
            fallback_results = []
            for drug in drugs_to_validate:
                fallback_results.append({
                    "no": drug["index"],
                    "nama_obat": drug["nama_obat"],
                    "kelas_terapi": drug["kelas_terapi"],
                    "status_fornas": "⚠️ Perlu Justifikasi",
                    "catatan_ai": "Obat terdaftar di FORNAS. Perlu review manual.",
                    "sumber_regulasi": drug["sumber_regulasi_db"]
                })
            
            all_results = non_fornas_drugs + fallback_results
            all_results.sort(key=lambda x: x["no"])
            return all_results
    
    
    def _call_batch_ai_validation(
        self,
        drugs: List[Dict],
        diagnosis_icd10: str,
        diagnosis_name: str
    ) -> List[Dict]:
        """
        Single AI call to validate multiple drugs
        
        Returns list of validation results
        """
        # Build batch prompt
        prompt = self._build_batch_prompt(drugs, diagnosis_icd10, diagnosis_name)
        
        # Call OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Anda adalah AI validator FORNAS untuk sistem BPJS Indonesia. Berikan penilaian objektif dan akurat untuk semua obat sekaligus."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=2000,  # Increased for multiple drugs
            response_format={"type": "json_object"}
        )
        
        # Parse response
        content = response.choices[0].message.content
        ai_result = json.loads(content)
        
        logger.info(f"[FORNAS_OPTIMIZED] ✓ AI processed {len(drugs)} drugs in single call")
        logger.info(f"[FORNAS_OPTIMIZED] Tokens: {response.usage.prompt_tokens} prompt + {response.usage.completion_tokens} completion")
        
        # Build validation results
        validations = ai_result.get("validations", [])
        results = []
        
        for drug_info in drugs:
            idx = drug_info["index"]
            
            # Find AI result for this drug
            ai_validation = next(
                (v for v in validations if v.get("index") == idx),
                None
            )
            
            if ai_validation:
                # Use sumber_regulasi from DB only
                sumber_regulasi = drug_info["sumber_regulasi_db"] if drug_info["sumber_regulasi_db"] and str(drug_info["sumber_regulasi_db"]).strip() else "-"
                
                results.append({
                    "no": idx,
                    "nama_obat": drug_info["nama_obat"],
                    "kelas_terapi": drug_info["kelas_terapi"],
                    "status_fornas": ai_validation.get("status_fornas", "⚠️ Perlu Justifikasi"),
                    "catatan_ai": ai_validation.get("catatan_ai", "Perlu review manual")[:150],
                    "sumber_regulasi": sumber_regulasi
                })
            else:
                # AI didn't return result for this drug - fallback
                results.append({
                    "no": idx,
                    "nama_obat": drug_info["nama_obat"],
                    "kelas_terapi": drug_info["kelas_terapi"],
                    "status_fornas": "⚠️ Perlu Justifikasi",
                    "catatan_ai": "Obat terdaftar di FORNAS. Perlu review manual.",
                    "sumber_regulasi": drug_info["sumber_regulasi_db"]
                })
        
        return results
    
    
    def _build_batch_prompt(
        self,
        drugs: List[Dict],
        diagnosis_icd10: str,
        diagnosis_name: str
    ) -> str:
        """Build prompt for batch validation"""
        
        drugs_list = "\n".join([
            f"{d['index']}. {d['nama_obat']} - {d['kelas_terapi']}"
            for d in drugs
        ])
        
        prompt = f"""Validasi kesesuaian SEMUA obat berikut dengan diagnosis berdasarkan regulasi FORNAS dan PNPK Indonesia.

DIAGNOSIS:
- Nama: {diagnosis_name}
- ICD-10: {diagnosis_icd10}

DAFTAR OBAT:
{drugs_list}

TUGAS:
Untuk SETIAP obat, tentukan:
1. status_fornas: "✅ Sesuai (Fornas)" | "⚠️ Perlu Justifikasi" | "❌ Non-Fornas"
2. catatan_ai: Penjelasan singkat (max 100 karakter) mengapa obat sesuai/tidak sesuai

KRITERIA:
- ✅ Sesuai: Obat adalah lini pertama/standard untuk diagnosis ini
- ⚠️ Perlu Justifikasi: Obat bisa digunakan tapi butuh justifikasi khusus
- ❌ Non-Fornas: Obat tidak relevan atau kontraindikasi

OUTPUT FORMAT (JSON):
{{
  "validations": [
    {{
      "index": 1,
      "status_fornas": "✅ Sesuai (Fornas)",
      "catatan_ai": "Lini pertama untuk pneumonia berat rawat inap"
    }},
    {{
      "index": 2,
      "status_fornas": "⚠️ Perlu Justifikasi",
      "catatan_ai": "Bukan lini pertama, perlu justifikasi alergi"
    }}
  ]
}}

PENTING: 
- Berikan hasil untuk SEMUA {len(drugs)} obat
- Catatan harus singkat, padat, dan informatif
- Fokus pada kesesuaian klinis berdasarkan PNPK Indonesia"""

        return prompt
    
    
    def _generate_summary(self, validations: List[Dict]) -> Dict:
        """Generate validation summary"""
        total = len(validations)
        sesuai = sum(1 for v in validations if "✅" in v.get("status_fornas", ""))
        perlu_justifikasi = sum(1 for v in validations if "⚠️" in v.get("status_fornas", ""))
        non_fornas = sum(1 for v in validations if "❌" in v.get("status_fornas", ""))
        
        from datetime import datetime
        
        return {
            "total_obat": total,
            "sesuai": sesuai,
            "perlu_justifikasi": perlu_justifikasi,
            "non_fornas": non_fornas,
            "update_date": datetime.now().strftime("%Y-%m-%d"),
            "status_database": "Official Verified",
            "optimization": "Batch AI validation (single call for all drugs)"
        }


# Public interface
def validate_fornas_lite_optimized(
    drug_list: List[str],
    diagnosis_icd10: str,
    diagnosis_name: str
) -> Dict:
    """
    OPTIMIZED validation - single AI call for all drugs
    
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
