"""
FORNAS Drug Extractor Service

Extract drug names from:
1. AI generated procedure descriptions (GPT output)
2. Procedure names (ICD-9 descriptions)
3. Medical records text (rekam medis)
4. Claims data (tindakan names)

Author: AI Assistant
Date: 2025-11-09
"""

import re
import os
from typing import List, Dict, Set
from pathlib import Path

from services.fornas_matcher import FornasDrugMatcher


class FornasDrugExtractor:
    """
    Extract drug names from various text sources
    """
    
    def __init__(self):
        self.matcher = FornasDrugMatcher()
        
        # Common drug keywords (untuk detection)
        self.drug_keywords = [
            "antibiotik", "antibiotic", "infus", "infusion", "injeksi", "injection",
            "obat", "drug", "medication", "tablet", "kapsul", "capsule",
            "sirup", "syrup", "salep", "ointment", "drops", "tetes"
        ]
        
        # Pharmacologic ICD-9 patterns
        self.pharmacologic_patterns = [
            r"injection.*antibiotic",
            r"infusion.*",
            r"administration.*drug",
            r"therapy.*pharmacologic",
            r"nebulization",
            r"inhalation.*medication"
        ]
    
    def is_pharmacologic_procedure(self, procedure_name: str) -> bool:
        """
        Deteksi apakah procedure name mengindikasikan penggunaan obat
        
        Args:
            procedure_name: Nama prosedur (e.g., "Injection of antibiotic")
        
        Returns:
            True jika procedure likely melibatkan obat
        """
        if not procedure_name:
            return False
        
        text_lower = procedure_name.lower()
        
        # Check keywords
        for keyword in self.drug_keywords:
            if keyword in text_lower:
                return True
        
        # Check patterns
        for pattern in self.pharmacologic_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False
    
    def extract_from_procedure_name(self, procedure_name: str) -> List[str]:
        """
        Extract potential drug names from procedure description
        
        Example:
            "Injection of ceftriaxone 1g IV" → ["ceftriaxone"]
            "Nebulization with salbutamol" → ["salbutamol"]
        
        Returns:
            List of potential drug names (belum divalidasi dengan FORNAS)
        """
        if not procedure_name:
            return []
        
        candidates = []
        text_lower = procedure_name.lower()
        
        # ✅ ENHANCED: Pattern untuk format Indonesia ("Injeksi seftriakson 1g IV")
        # Format: [Injeksi|Infus|Tablet|Kapsul] [Nama Obat] [Dosis] [Rute]
        indo_patterns = [
            r'(?:injeksi|infus|suntikan)\s+([a-z]+(?:\s+[a-z]+)?)',  # "Injeksi seftriakson" (greedy)
            r'(?:tablet|kapsul|sirup)\s+([a-z]+(?:\s+[a-z]+)?)',  # "Tablet parasetamol"
            r'pemberian\s+([a-z]+(?:\s+[a-z]+)?)',  # "Pemberian seftriakson"
        ]
        
        for pattern in indo_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else ""
                match = match.strip()
                # Remove dosage info from extracted name
                match = re.sub(r'\s+\d+\s*(?:mg|g|ml|mcg|iu).*$', '', match).strip()
                # Remove route info
                match = re.sub(r'\s+(?:iv|im|sc|po|oral).*$', '', match).strip()
                if match and len(match) > 3:  # Min 3 characters
                    candidates.append(match)
        
        # Pattern 1: "injection of [drug]", "infusion of [drug]"
        match = re.search(r"(?:injection|infusion|administration|nebulization).*?(?:of|with)\s+([a-z]+)", text_lower)
        if match:
            candidates.append(match.group(1))
        
        # Pattern 2: Common drugs mentioned (English & Indonesian names)
        common_drugs = [
            # English names
            "ceftriaxone", "cefotaxime", "ampicillin", "gentamicin", "amoxicillin",
            "paracetamol", "ibuprofen", "omeprazole", "ranitidine", "metronidazole",
            "ciprofloxacin", "azithromycin", "dexamethasone", "methylprednisolone",
            "salbutamol", "adrenaline", "epinephrine", "furosemide", "dopamine",
            "levofloxacin", "moxifloxacin", "metformin", "glimepiride", "insulin",
            
            # Indonesian names (FORNAS database format)
            "seftriakson", "sefotaksim", "ampisilin", "amoksisilin", "parasetamol",
            "siprofloksasin", "azitromisin", "deksametason", "metilprednisolon",
            "levofloksasin", "moksifloksasin", "ranitidin", "omeprazol",
            "metronidazol", "furosemid", "metformin", "glimepirid",
            "sefiksim", "sefadroksil", "sefaleksin", "diklofenak", "ketorolak",
            "amlodipin", "kaptopril", "spironolakton", "glibenklamid",
            "prednisolon", "teofilin", "klopidogrel", "asam folat", "kalsium"
        ]
        
        for drug in common_drugs:
            if drug in text_lower:
                candidates.append(drug)
        
        # Remove duplicates
        return list(set(candidates))
    
    def extract_from_ai_tindakan(self, tindakan_list: List[Dict]) -> Dict[str, List[str]]:
        """
        Extract drugs from AI-generated tindakan list
        
        Args:
            tindakan_list: List of dicts from GPT output
                [{"nama": "Injection of antibiotic", "kategori": "terapi", ...}, ...]
        
        Returns:
            {
                "tindakan_id": ["drug1", "drug2", ...],
                ...
            }
        """
        results = {}
        
        for idx, tindakan in enumerate(tindakan_list):
            if not isinstance(tindakan, dict):
                continue
            
            tindakan_id = tindakan.get("id", f"tindakan_{idx}")
            nama = tindakan.get("nama", "") or tindakan.get("tindakan", "")
            
            # Extract dari nama prosedur
            extracted = self.extract_from_procedure_name(nama)
            
            if extracted:
                results[str(tindakan_id)] = extracted
        
        return results
    
    def extract_and_match(self, text: str, threshold: int = 85) -> List[Dict]:
        """
        Extract drug names from text AND match them with FORNAS database
        
        Args:
            text: Any medical text (procedure name, rekam medis, etc.)
            threshold: Fuzzy match threshold
        
        Returns:
            [
                {
                    "extracted_name": "ceftriaxone",
                    "matched": True/False,
                    "fornas_drug": FornasDrug object or None,
                    "confidence": 100,
                    "strategy": "exact"
                },
                ...
            ]
        """
        # Extract candidates
        candidates = self.extract_from_procedure_name(text)
        
        if not candidates:
            return []
        
        # Match each candidate
        results = []
        for drug_name in candidates:
            match_result = self.matcher.match(drug_name, threshold=threshold)
            
            results.append({
                "extracted_name": drug_name,
                "matched": match_result["found"],
                "fornas_drug": match_result["drug"],
                "confidence": match_result["confidence"],
                "strategy": match_result["strategy"],
                "alternatives": match_result.get("alternatives", [])
            })
        
        return results
    
    def validate_tindakan_drugs(self, tindakan_list: List[Dict], threshold: int = 85) -> Dict:
        """
        Validate all drugs in tindakan list against FORNAS
        
        Returns:
            {
                "total_procedures": 10,
                "pharmacologic_procedures": 5,
                "drugs_found": 7,
                "fornas_validated": 6,
                "fornas_missing": 1,
                "details": [
                    {
                        "tindakan_id": "...",
                        "tindakan_name": "...",
                        "is_pharmacologic": True,
                        "drugs": [
                            {
                                "name": "ceftriaxone",
                                "fornas_valid": True,
                                "fornas_code": "FORN-2023-...",
                                "confidence": 100
                            }
                        ]
                    },
                    ...
                ]
            }
        """
        total_procedures = len(tindakan_list)
        pharmacologic_count = 0
        total_drugs = 0
        fornas_validated = 0
        fornas_missing = 0
        details = []
        
        for idx, tindakan in enumerate(tindakan_list):
            if not isinstance(tindakan, dict):
                continue
            
            tindakan_id = tindakan.get("id", f"tindakan_{idx}")
            nama = tindakan.get("nama", "") or tindakan.get("tindakan", "")
            
            # Check if pharmacologic
            is_pharmaco = self.is_pharmacologic_procedure(nama)
            if is_pharmaco:
                pharmacologic_count += 1
            
            # Extract and match drugs
            drug_results = self.extract_and_match(nama, threshold=threshold)
            
            tindakan_detail = {
                "tindakan_id": tindakan_id,
                "tindakan_name": nama,
                "is_pharmacologic": is_pharmaco,
                "drugs": []
            }
            
            for drug_res in drug_results:
                total_drugs += 1
                
                if drug_res["matched"]:
                    fornas_validated += 1
                    drug_info = {
                        "name": drug_res["extracted_name"],
                        "fornas_valid": True,
                        "fornas_code": drug_res["fornas_drug"].kode_fornas if drug_res["fornas_drug"] else None,
                        "fornas_name": drug_res["fornas_drug"].obat_name if drug_res["fornas_drug"] else None,
                        "confidence": drug_res["confidence"],
                        "strategy": drug_res["strategy"]
                    }
                else:
                    fornas_missing += 1
                    drug_info = {
                        "name": drug_res["extracted_name"],
                        "fornas_valid": False,
                        "fornas_code": None,
                        "confidence": 0,
                        "reason": "Tidak ditemukan di FORNAS"
                    }
                
                tindakan_detail["drugs"].append(drug_info)
            
            if tindakan_detail["drugs"]:  # Only add if drugs were found
                details.append(tindakan_detail)
        
        return {
            "total_procedures": total_procedures,
            "pharmacologic_procedures": pharmacologic_count,
            "drugs_found": total_drugs,
            "fornas_validated": fornas_validated,
            "fornas_missing": fornas_missing,
            "validation_rate": f"{(fornas_validated/total_drugs*100) if total_drugs > 0 else 0:.1f}%",
            "details": details
        }


# ===========================================================
# HELPER FUNCTIONS
# ===========================================================

def extract_drugs_from_procedures(procedures: List[Dict], threshold: int = 85) -> Dict:
    """
    Quick helper to extract and validate drugs from procedure list
    
    Usage:
        tindakan = [
            {"nama": "Injection of ceftriaxone", "id": 1},
            {"nama": "Nebulization with salbutamol", "id": 2}
        ]
        result = extract_drugs_from_procedures(tindakan)
        print(result["validation_rate"])  # e.g., "85.5%"
    """
    extractor = FornasDrugExtractor()
    return extractor.validate_tindakan_drugs(procedures, threshold=threshold)


if __name__ == "__main__":
    # Test extraction
    print("=" * 70)
    print("FORNAS DRUG EXTRACTOR TEST")
    print("=" * 70)
    
    test_procedures = [
        {"id": 1, "nama": "Injection of antibiotic (ceftriaxone 1g IV)"},
        {"id": 2, "nama": "Nebulization with salbutamol"},
        {"id": 3, "nama": "Infusion of paracetamol 1g"},
        {"id": 4, "nama": "Routine chest x-ray"},  # Non-pharmacologic
        {"id": 5, "nama": "Administration of mysterious_drug_123"},  # Should not match
    ]
    
    extractor = FornasDrugExtractor()
    results = extractor.validate_tindakan_drugs(test_procedures, threshold=80)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total procedures: {results['total_procedures']}")
    print(f"   Pharmacologic: {results['pharmacologic_procedures']}")
    print(f"   Drugs found: {results['drugs_found']}")
    print(f"   FORNAS validated: {results['fornas_validated']}")
    print(f"   FORNAS missing: {results['fornas_missing']}")
    print(f"   Validation rate: {results['validation_rate']}")
    
    print(f"\n📋 DETAILS:")
    for detail in results['details']:
        print(f"\n   Tindakan: {detail['tindakan_name']}")
        print(f"   Pharmacologic: {detail['is_pharmacologic']}")
        for drug in detail['drugs']:
            status = "✅" if drug['fornas_valid'] else "❌"
            print(f"      {status} {drug['name']} → {drug.get('fornas_name', 'NOT IN FORNAS')}")
    
    print("\n" + "=" * 70)
