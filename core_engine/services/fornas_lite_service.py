"""
FORNAS Lite Validator Service

Simplified FORNAS validation untuk AI-Claim Lite version
Focus: Direct drug validation dengan AI reasoning

Key Features:
- Parse drug input dari field "obat"
- Match dengan FORNAS database (get kelas_terapi, sumber_regulasi)
- AI-powered validation (status + catatan)
- Table-ready output

Author: AI Assistant
Date: 2025-11-11
"""

import json
import re
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import services
from services.fornas_service import match_multiple_obat
from services.fornas_matcher import FornasDrugMatcher


class FornasLiteValidator:
    """
    Simplified FORNAS validator untuk AI-Claim Lite
    
    Input: drug_list, diagnosis_icd10, diagnosis_name
    Output: Table-ready validation results
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize validator
        
        Args:
            api_key: OpenAI API key (optional, dari env)
        """
        self.matcher = FornasDrugMatcher()
        
        # OpenAI client
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        
        # Statistics
        self._total_validations = 0
        self._ai_requests = 0
        self._total_cost = 0.0
    
    
    def validate_drugs_lite(
        self,
        drug_list: List[str],
        diagnosis_icd10: str,
        diagnosis_name: str,
        include_summary: bool = True
    ) -> Dict[str, Any]:
        """
        Main validation method untuk Lite version
        
        Args:
            drug_list: List of drug names (e.g., ["Ceftriaxone 1g IV", "Paracetamol"])
            diagnosis_icd10: ICD-10 code (e.g., "J18.9")
            diagnosis_name: Diagnosis name (e.g., "Pneumonia berat")
            include_summary: Include summary statistics
        
        Returns:
            {
                "fornas_validation": [
                    {
                        "no": 1,
                        "nama_obat": "Ceftriaxone",
                        "kelas_terapi": "Antibiotik – Sefalosporin",  # FROM DB
                        "status_fornas": "✅ Sesuai (Fornas)",         # FROM AI
                        "catatan_ai": "Lini pertama pneumonia...",    # FROM AI
                        "sumber_regulasi": "FORNAS 2023 • PNPK..."   # FROM DB + AI
                    },
                    ...
                ],
                "summary": {
                    "total_obat": 2,
                    "sesuai": 1,
                    "perlu_justifikasi": 1,
                    "non_fornas": 0,
                    "update_date": "2025-11-11",
                    "status_database": "Official Verified"
                }
            }
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
        
        # Step 1: Parse drug input
        parsed_drugs = self._parse_drug_input(drug_list)
        
        # Step 2: Match dengan FORNAS database
        fornas_matched = match_multiple_obat(parsed_drugs, threshold=85)
        
        # Step 3: AI validation untuk setiap obat
        validation_results = []
        
        for idx, matched in enumerate(fornas_matched, 1):
            validation = self._validate_single_drug_ai(
                matched=matched,
                diagnosis_icd10=diagnosis_icd10,
                diagnosis_name=diagnosis_name,
                index=idx
            )
            validation_results.append(validation)
        
        # Step 4: Build output
        output = {
            "fornas_validation": validation_results
        }
        
        # Add summary if requested
        if include_summary:
            output["summary"] = self._generate_summary(validation_results)
        
        return output
    
    
    def _parse_drug_input(self, drug_list: List[str]) -> List[str]:
        """
        Parse and clean drug names
        
        Args:
            drug_list: Raw drug list (may contain dosage, route, etc.)
        
        Returns:
            Cleaned drug names
        
        Example:
            ["Ceftriaxone 1g IV", "Paracetamol 500mg"] 
            → ["Ceftriaxone", "Paracetamol"]
        """
        cleaned = []
        
        for drug in drug_list:
            if not drug or drug.strip() == "":
                continue
            
            # Remove dosage (e.g., "1g", "500mg")
            drug_clean = re.sub(r'\d+\s*(mg|g|ml|mcg|iu|cc)\b', '', drug, flags=re.IGNORECASE)
            
            # Remove route (e.g., "IV", "oral", "injeksi")
            drug_clean = re.sub(r'\b(iv|im|sc|po|oral|injeksi|infus|tablet|kapsul)\b', '', drug_clean, flags=re.IGNORECASE)
            
            # Clean whitespace
            drug_clean = drug_clean.strip()
            
            if drug_clean:
                cleaned.append(drug_clean)
        
        return cleaned
    
    
    def _validate_single_drug_ai(
        self,
        matched: Dict,
        diagnosis_icd10: str,
        diagnosis_name: str,
        index: int
    ) -> Dict:
        """
        Validate single drug dengan AI reasoning
        
        Args:
            matched: Result dari match_multiple_obat()
            diagnosis_icd10: ICD-10 code
            diagnosis_name: Diagnosis name
            index: Row number
        
        Returns:
            {
                "no": 1,
                "nama_obat": "Ceftriaxone",
                "kelas_terapi": "Antibiotik – Sefalosporin",
                "status_fornas": "✅ Sesuai (Fornas)",
                "catatan_ai": "Lini pertama pneumonia berat rawat inap.",
                "sumber_regulasi": "FORNAS 2023 • PNPK Pneumonia 2020"
            }
        """
        # Base data dari DB
        nama_obat = matched.get("nama_generik", "Unknown")
        kelas_terapi = matched.get("kelas_terapi", "Tidak tersedia")
        sumber_regulasi_db = matched.get("sumber_regulasi", "FORNAS 2023")
        
        # Check if drug found in FORNAS
        if not matched.get("found", False):
            # Drug NOT in FORNAS
            return {
                "no": index,
                "nama_obat": nama_obat,
                "kelas_terapi": "Tidak ditemukan di FORNAS",
                "status_fornas": "❌ Non-Fornas",
                "catatan_ai": "Obat tidak terdaftar dalam Formularium Nasional.",
                "sumber_regulasi": "-"
            }
        
        # Drug found in FORNAS → AI validation
        try:
            ai_result = self._call_ai_validation(
                drug_name=nama_obat,
                kelas_terapi=kelas_terapi,
                diagnosis_icd10=diagnosis_icd10,
                diagnosis_name=diagnosis_name,
                sumber_regulasi_db=sumber_regulasi_db
            )
            
            return {
                "no": index,
                "nama_obat": nama_obat,
                "kelas_terapi": kelas_terapi,
                "status_fornas": ai_result["status_fornas"],
                "catatan_ai": ai_result["catatan_ai"],
                "sumber_regulasi": ai_result["sumber_regulasi"]
            }
        
        except Exception as e:
            # AI error → fallback
            print(f"[FORNAS_LITE] ❌ AI validation error for {nama_obat}: {e}")
            return {
                "no": index,
                "nama_obat": nama_obat,
                "kelas_terapi": kelas_terapi,
                "status_fornas": "⚠️ Perlu Justifikasi",
                "catatan_ai": f"Obat terdaftar di FORNAS. Perlu review manual.",
                "sumber_regulasi": sumber_regulasi_db
            }
    
    
    def _call_ai_validation(
        self,
        drug_name: str,
        kelas_terapi: str,
        diagnosis_icd10: str,
        diagnosis_name: str,
        sumber_regulasi_db: str
    ) -> Dict:
        """
        Call OpenAI untuk validation reasoning
        
        Returns:
            {
                "status_fornas": "✅ Sesuai (Fornas)" | "⚠️ Perlu Justifikasi" | "❌ Non-Fornas",
                "catatan_ai": "Reasoning singkat (max 100 char)",
                "sumber_regulasi": "FORNAS 2023 • PNPK Pneumonia 2020"
            }
        """
        prompt = self._build_ai_prompt(
            drug_name=drug_name,
            kelas_terapi=kelas_terapi,
            diagnosis_icd10=diagnosis_icd10,
            diagnosis_name=diagnosis_name,
            sumber_regulasi_db=sumber_regulasi_db
        )
        
        # Call OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Anda adalah AI validator FORNAS untuk sistem BPJS Indonesia. Berikan penilaian objektif dan akurat."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,  # Low for consistency
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        content = response.choices[0].message.content
        ai_result = json.loads(content)
        
        # Track statistics
        self._ai_requests += 1
        cost = (response.usage.prompt_tokens * 0.00000015 + 
                response.usage.completion_tokens * 0.00000060)
        self._total_cost += cost
        
        # Validate response format
        status = ai_result.get("status_fornas", "⚠️ Perlu Justifikasi")
        catatan = ai_result.get("catatan_ai", "Perlu review manual")[:150]  # Max 150 char
        
        # Build sumber_regulasi:
        # Per keputusan: prefer authoritative DB value only.
        # Do NOT append AI-suggested concept strings to the source. If DB value
        # is empty or None, fall back to '-' (explicit missing marker).
        sumber_regulasi = sumber_regulasi_db if sumber_regulasi_db and str(sumber_regulasi_db).strip() else "-"

        return {
            "status_fornas": status,
            "catatan_ai": catatan,
            "sumber_regulasi": sumber_regulasi
        }
    
    
    def _build_ai_prompt(
        self,
        drug_name: str,
        kelas_terapi: str,
        diagnosis_icd10: str,
        diagnosis_name: str,
        sumber_regulasi_db: str
    ) -> str:
        """
        Build AI validation prompt
        
        Returns:
            Formatted prompt string
        """
        prompt = f"""Validasi kesesuaian obat dengan diagnosis berdasarkan regulasi FORNAS dan PNPK Indonesia.

INPUT DATA:
- Diagnosis: {diagnosis_name} (ICD-10: {diagnosis_icd10})
- Obat: {drug_name}
- Kelas Terapi: {kelas_terapi}
- Sumber Regulasi (DB): {sumber_regulasi_db}

TUGAS:
Tentukan apakah obat ini sesuai untuk diagnosis tersebut.

OUTPUT (JSON format):
{{
    "status_fornas": "STATUS",
    "catatan_ai": "Alasan singkat (max 100 karakter)",
    "sumber_regulasi": ["PNPK yang relevan", "Clinical Pathway"]
}}

PILIHAN STATUS:
- "✅ Sesuai (Fornas)" → Obat terdaftar di FORNAS DAN sesuai indikasi diagnosis (lini pertama)
- "⚠️ Perlu Justifikasi" → Obat di FORNAS tapi bukan lini pertama ATAU butuh kondisi khusus
- "❌ Non-Fornas" → Tidak sesuai indikasi untuk diagnosis ini

CONTOH OUTPUT:
{{
    "status_fornas": "✅ Sesuai (Fornas)",
    "catatan_ai": "Lini pertama pneumonia berat rawat inap.",
    "sumber_regulasi": ["PNPK Pneumonia 2020", "CP BPJS 2022"]
}}

PENTING:
- Berikan catatan_ai yang spesifik dan actionable
- Sebutkan PNPK/guideline yang relevan di sumber_regulasi
- Respond HANYA dengan JSON, tidak ada teks tambahan
"""
        return prompt
    
    
    def _generate_summary(self, validation_results: List[Dict]) -> Dict:
        """
        Generate summary statistics
        
        Args:
            validation_results: List of validation results
        
        Returns:
            Summary dict
        """
        total = len(validation_results)
        
        # Count by status
        sesuai = sum(1 for v in validation_results if "✅" in v.get("status_fornas", ""))
        perlu_justifikasi = sum(1 for v in validation_results if "⚠️" in v.get("status_fornas", ""))
        non_fornas = sum(1 for v in validation_results if "❌" in v.get("status_fornas", ""))
        
        return {
            "total_obat": total,
            "sesuai": sesuai,
            "perlu_justifikasi": perlu_justifikasi,
            "non_fornas": non_fornas,
            "update_date": datetime.now().strftime("%Y-%m-%d"),
            "status_database": "Official Verified"
        }
    
    
    def get_statistics(self) -> Dict:
        """Get validator statistics"""
        return {
            "total_validations": self._total_validations,
            "ai_requests": self._ai_requests,
            "total_cost_usd": round(self._total_cost, 4),
            "avg_cost_per_validation": round(
                self._total_cost / self._ai_requests if self._ai_requests > 0 else 0,
                6
            )
        }


# ============================================================
# HELPER FUNCTION (Public Interface)
# ============================================================

def validate_fornas_lite(
    drug_list: List[str],
    diagnosis_icd10: str,
    diagnosis_name: str
) -> Dict:
    """
    Quick validation function (public interface)
    
    Args:
        drug_list: List of drug names
        diagnosis_icd10: ICD-10 code
        diagnosis_name: Diagnosis name
    
    Returns:
        Validation results with summary
    
    Example:
        >>> result = validate_fornas_lite(
        ...     drug_list=["Ceftriaxone 1g IV", "Paracetamol 500mg"],
        ...     diagnosis_icd10="J18.9",
        ...     diagnosis_name="Pneumonia berat"
        ... )
        >>> print(result["summary"]["sesuai"])
        1
    """
    validator = FornasLiteValidator()
    return validator.validate_drugs_lite(
        drug_list=drug_list,
        diagnosis_icd10=diagnosis_icd10,
        diagnosis_name=diagnosis_name,
        include_summary=True
    )


# ============================================================
# TESTING
# ============================================================
if __name__ == "__main__":
    print("=" * 80)
    print("FORNAS LITE VALIDATOR TEST")
    print("=" * 80)
    
    # Test data
    test_data = {
        "diagnosis_icd10": "J18.9",
        "diagnosis_name": "Pneumonia berat",
        "drug_list": [
            "Ceftriaxone 1g IV",
            "Paracetamol 500mg",
            "Levofloxacin 500mg",
            "Vitamin C 1000mg"  # Might need justification
        ]
    }
    
    print(f"\n📋 Test Case:")
    print(f"   Diagnosis: {test_data['diagnosis_name']} ({test_data['diagnosis_icd10']})")
    print(f"   Obat: {', '.join(test_data['drug_list'])}")
    
    print("\n🔍 Running validation...")
    
    try:
        result = validate_fornas_lite(
            drug_list=test_data["drug_list"],
            diagnosis_icd10=test_data["diagnosis_icd10"],
            diagnosis_name=test_data["diagnosis_name"]
        )
        
        print("\n" + "=" * 80)
        print("VALIDASI FORNAS (AI-CLAIM Lite)")
        print("=" * 80)
        
        # Print table
        validations = result["fornas_validation"]
        for v in validations:
            print(f"\n{v['no']}. {v['nama_obat']}")
            print(f"   Kelas Terapi: {v['kelas_terapi']}")
            print(f"   Status: {v['status_fornas']}")
            print(f"   Catatan: {v['catatan_ai']}")
            print(f"   Sumber: {v['sumber_regulasi']}")
        
        # Print summary
        summary = result["summary"]
        print("\n" + "-" * 80)
        print("📊 SUMMARY:")
        print(f"   Total obat: {summary['total_obat']}")
        print(f"   ✅ Sesuai: {summary['sesuai']}")
        print(f"   ⚠️ Perlu Justifikasi: {summary['perlu_justifikasi']}")
        print(f"   ❌ Non-Fornas: {summary['non_fornas']}")
        print(f"   Update: {summary['update_date']}")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
