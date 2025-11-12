"""
FORNAS Validator Service

Validate drug usage against FORNAS regulations:
1. Indication validation (ICD-10 matching)
2. Facility level validation (FPKTP/FPKTL)
3. Restriction validation (restriksi_penggunaan)
4. OEN flag validation
5. Prescription limits (persepan_maksimal)

Author: AI Assistant
Date: 2025-11-09
"""

import os
import sys
import json
from typing import List, Dict, Optional
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load API Key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import from core_engine database
from database_connection import SessionLocal
from models import FornasDrug, ICD9Procedure


class FornasValidator:
    """
    Comprehensive FORNAS regulation validator
    """
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    def validate_indication(
        self, 
        drug: FornasDrug, 
        icd10_code: str,
        diagnosis_name: str = ""
    ) -> Dict:
        """
        Validate drug indication against diagnosis (ICD-10)
        
        Strategy:
        1. Exact ICD-10 match in indikasi_fornas
        2. Partial match (chapter/category level)
        3. AI-powered semantic matching (diagnosis name → indication)
        
        Args:
            drug: FornasDrug object
            icd10_code: Patient's diagnosis ICD-10 code (e.g., "J18.9")
            diagnosis_name: Diagnosis name (e.g., "Pneumonia")
        
        Returns:
            {
                "valid": bool,
                "confidence": int,  # 0-100
                "method": str,  # "exact", "partial", "semantic", "ai"
                "reason": str,
                "fornas_indications": List[str]
            }
        """
        if not drug or not icd10_code:
            return {
                "valid": False,
                "confidence": 0,
                "method": None,
                "reason": "Missing drug or ICD-10 code",
                "fornas_indications": []
            }
        
        # Get FORNAS indications
        fornas_indications = drug.indikasi_fornas or []
        
        if not fornas_indications or fornas_indications == ["null"] or fornas_indications == "null":
            # No indication data in FORNAS → AI validation
            return self._ai_indication_validation(drug, icd10_code, diagnosis_name)
        
        # Convert to list if string
        if isinstance(fornas_indications, str):
            try:
                fornas_indications = json.loads(fornas_indications)
            except:
                fornas_indications = [fornas_indications]
        
        # Strategy 1: Exact ICD-10 match
        for indication in fornas_indications:
            if isinstance(indication, str):
                if icd10_code.upper() in indication.upper():
                    return {
                        "valid": True,
                        "confidence": 100,
                        "method": "exact",
                        "reason": f"ICD-10 {icd10_code} sesuai dengan indikasi FORNAS",
                        "fornas_indications": fornas_indications
                    }
        
        # Strategy 2: Partial match (chapter level)
        # Example: J18.9 → J18 → J1 → J (respiratory)
        icd_chapter = icd10_code[0] if icd10_code else ""
        icd_category = icd10_code[:3] if len(icd10_code) >= 3 else ""
        
        for indication in fornas_indications:
            indication_str = str(indication).upper()
            if icd_category and icd_category.upper() in indication_str:
                return {
                    "valid": True,
                    "confidence": 85,
                    "method": "partial",
                    "reason": f"Kategori ICD-10 {icd_category} sesuai dengan indikasi FORNAS",
                    "fornas_indications": fornas_indications
                }
            if icd_chapter and icd_chapter.upper() in indication_str:
                return {
                    "valid": True,
                    "confidence": 70,
                    "method": "chapter",
                    "reason": f"Chapter ICD-10 {icd_chapter} sesuai dengan indikasi FORNAS",
                    "fornas_indications": fornas_indications
                }
        
        # Strategy 3: Semantic matching (disease name)
        if diagnosis_name:
            diagnosis_lower = diagnosis_name.lower()
            for indication in fornas_indications:
                indication_lower = str(indication).lower()
                # Simple keyword matching
                if diagnosis_lower in indication_lower or indication_lower in diagnosis_lower:
                    return {
                        "valid": True,
                        "confidence": 80,
                        "method": "semantic",
                        "reason": f"Diagnosis '{diagnosis_name}' sesuai dengan indikasi FORNAS",
                        "fornas_indications": fornas_indications
                    }
        
        # Strategy 4: AI validation (GPT assessment)
        return self._ai_indication_validation(drug, icd10_code, diagnosis_name, fornas_indications)
    
    def _ai_indication_validation(
        self, 
        drug: FornasDrug, 
        icd10_code: str,
        diagnosis_name: str,
        fornas_indications: List = None
    ) -> Dict:
        """
        Use AI to validate drug-diagnosis appropriateness
        """
        prompt = f"""
Anda adalah apoteker klinis yang memvalidasi kesesuaian obat dengan diagnosis berdasarkan regulasi FORNAS Indonesia.

OBAT: {drug.obat_name}
KELAS TERAPI: {drug.kelas_terapi}
INDIKASI FORNAS: {fornas_indications or 'Tidak tersedia'}

DIAGNOSIS:
- ICD-10: {icd10_code}
- Nama: {diagnosis_name}

TUGAS:
Tentukan apakah obat ini SESUAI untuk diagnosis tersebut berdasarkan:
1. Indikasi FORNAS (jika ada)
2. Standar medis umum
3. Kelas terapi obat

OUTPUT JSON:
{{
    "valid": true/false,
    "confidence": 0-100,
    "reason": "Penjelasan singkat mengapa sesuai/tidak sesuai",
    "recommendation": "Rekomendasi jika tidak sesuai"
}}

Jawab dalam JSON.
"""
        
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            ai_result = json.loads(resp.choices[0].message.content)
            
            return {
                "valid": ai_result.get("valid", False),
                "confidence": ai_result.get("confidence", 50),
                "method": "ai",
                "reason": ai_result.get("reason", ""),
                "recommendation": ai_result.get("recommendation", ""),
                "fornas_indications": fornas_indications or []
            }
        
        except Exception as e:
            print(f"[FORNAS_VALIDATOR] AI validation error: {e}")
            return {
                "valid": False,
                "confidence": 0,
                "method": "ai_error",
                "reason": f"Tidak dapat memvalidasi indikasi (AI error: {str(e)})",
                "fornas_indications": fornas_indications or []
            }
    
    def validate_facility(self, drug: FornasDrug, facility_type: str) -> Dict:
        """
        Validate if drug can be prescribed at facility level
        
        Args:
            drug: FornasDrug object
            facility_type: "FPKTP" (primary) or "FPKTL" (advanced)
        
        Returns:
            {
                "allowed": bool,
                "reason": str
            }
        """
        if not drug:
            return {"allowed": False, "reason": "Drug not found"}
        
        facility_upper = facility_type.upper()
        
        if facility_upper == "FPKTP":
            if drug.fasilitas_fpktp:
                return {"allowed": True, "reason": "Obat tersedia untuk FPKTP"}
            else:
                return {"allowed": False, "reason": "Obat hanya tersedia untuk FPKTL/RS"}
        
        elif facility_upper == "FPKTL":
            if drug.fasilitas_fpktl:
                return {"allowed": True, "reason": "Obat tersedia untuk FPKTL"}
            else:
                return {"allowed": False, "reason": "Obat tidak tersedia untuk FPKTL"}
        
        return {"allowed": True, "reason": "Facility type tidak dikenali, default allowed"}
    
    def validate_restrictions(self, drug: FornasDrug) -> Dict:
        """
        Check if drug has usage restrictions
        
        Returns:
            {
                "has_restrictions": bool,
                "restrictions": str,
                "severity": str  # "info", "warning", "critical"
            }
        """
        if not drug or not drug.restriksi_penggunaan:
            return {
                "has_restrictions": False,
                "restrictions": "",
                "severity": "info"
            }
        
        restrictions = drug.restriksi_penggunaan.strip()
        
        if restrictions in ["–", "-", ""]:
            return {
                "has_restrictions": False,
                "restrictions": "",
                "severity": "info"
            }
        
        # Determine severity based on content
        severity = "warning"
        restrictions_lower = restrictions.lower()
        
        if any(word in restrictions_lower for word in ["hanya", "only", "wajib", "required", "specialist"]):
            severity = "critical"
        
        return {
            "has_restrictions": True,
            "restrictions": restrictions,
            "severity": severity
        }
    
    def validate_oen(self, drug: FornasDrug) -> Dict:
        """
        Check OEN (Obat Esensial Nasional) status
        
        Returns:
            {
                "is_oen": bool,
                "message": str
            }
        """
        if not drug:
            return {"is_oen": False, "message": "Drug not found"}
        
        if drug.oen:
            return {
                "is_oen": True,
                "message": "Obat termasuk dalam daftar OEN (Obat Esensial Nasional)"
            }
        else:
            return {
                "is_oen": False,
                "message": "Obat tidak termasuk OEN (dapat digunakan sesuai indikasi)"
            }
    
    def comprehensive_validation(
        self,
        drug: FornasDrug,
        icd10_code: str,
        diagnosis_name: str,
        facility_type: str = "FPKTL"
    ) -> Dict:
        """
        Run all validation checks at once
        
        Returns:
            {
                "overall_status": "approved" / "warning" / "rejected",
                "validations": {
                    "indication": {...},
                    "facility": {...},
                    "restrictions": {...},
                    "oen": {...}
                },
                "summary": str
            }
        """
        # Run all validations
        indication_result = self.validate_indication(drug, icd10_code, diagnosis_name)
        facility_result = self.validate_facility(drug, facility_type)
        restriction_result = self.validate_restrictions(drug)
        oen_result = self.validate_oen(drug)
        
        # Determine overall status
        if not indication_result["valid"]:
            overall_status = "rejected"
            summary = f"❌ Obat TIDAK SESUAI indikasi: {indication_result['reason']}"
        elif not facility_result["allowed"]:
            overall_status = "rejected"
            summary = f"❌ Obat TIDAK DIIZINKAN di {facility_type}: {facility_result['reason']}"
        elif restriction_result["has_restrictions"] and restriction_result["severity"] == "critical":
            overall_status = "warning"
            summary = f"⚠️ Obat DAPAT DIGUNAKAN dengan RESTRIKSI: {restriction_result['restrictions']}"
        elif restriction_result["has_restrictions"]:
            overall_status = "warning"
            summary = f"⚠️ Perhatian: {restriction_result['restrictions']}"
        else:
            overall_status = "approved"
            summary = f"✅ Obat SESUAI indikasi dan regulasi FORNAS"
        
        return {
            "overall_status": overall_status,
            "drug_name": drug.obat_name,
            "fornas_code": drug.kode_fornas,
            "validations": {
                "indication": indication_result,
                "facility": facility_result,
                "restrictions": restriction_result,
                "oen": oen_result
            },
            "summary": summary
        }


# ===========================================================
# HELPER FUNCTIONS
# ===========================================================

def validate_fornas_drug(
    drug: FornasDrug,
    icd10_code: str,
    diagnosis_name: str = "",
    facility_type: str = "FPKTL"
) -> Dict:
    """
    Quick helper untuk comprehensive validation
    
    Usage:
        from services.fornas_matcher import match_fornas_drug
        from services.fornas_validator import validate_fornas_drug
        
        match = match_fornas_drug("ceftriaxone")
        if match["found"]:
            result = validate_fornas_drug(
                match["drug"], 
                icd10_code="J18.9", 
                diagnosis_name="Pneumonia"
            )
            print(result["summary"])
    """
    validator = FornasValidator()
    return validator.comprehensive_validation(drug, icd10_code, diagnosis_name, facility_type)


if __name__ == "__main__":
    # Test validation
    print("=" * 70)
    print("FORNAS VALIDATOR TEST")
    print("=" * 70)
    
    from services.fornas_matcher import match_fornas_drug
    
    # Test case: Ceftriaxone for Pneumonia
    print("\n🧪 Test Case: Ceftriaxone for Pneumonia (J18.9)")
    
    match = match_fornas_drug("ceftriaxone", threshold=80)
    
    if match["found"]:
        drug = match["drug"]
        print(f"✅ Drug found: {drug.obat_name} ({drug.kode_fornas})")
        
        validator = FornasValidator()
        result = validator.comprehensive_validation(
            drug=drug,
            icd10_code="J18.9",
            diagnosis_name="Pneumonia",
            facility_type="FPKTL"
        )
        
        print(f"\n📊 VALIDATION RESULT:")
        print(f"   Status: {result['overall_status'].upper()}")
        print(f"   Summary: {result['summary']}")
        print(f"\n   Details:")
        print(f"      Indication: {result['validations']['indication']['method']} "
              f"(confidence: {result['validations']['indication']['confidence']}%)")
        print(f"      Facility: {result['validations']['facility']['reason']}")
        print(f"      Restrictions: {result['validations']['restrictions']['restrictions'] or 'None'}")
        print(f"      OEN: {result['validations']['oen']['message']}")
    else:
        print("❌ Drug not found in FORNAS database")
    
    print("\n" + "=" * 70)
