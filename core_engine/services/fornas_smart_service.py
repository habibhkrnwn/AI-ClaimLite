# services/fornas_smart_service.py

"""
FORNAS Smart Service - Unified & Optimized

Menggabungkan semua fungsi FORNAS dalam 1 file:
- Drug name matching (exact, fuzzy, alias)
- AI normalization (English → Indonesian)
- Database validation
- Batch validation untuk multiple drugs

Alur seperti ICD-10:
1. Input obat
2. Match ke database
3. Jika tidak match → AI normalize ke Indonesian
4. Validate AI result dengan DB
5. Return hasil yang pasti ada di DB

Author: AI-CLAIM Team
Date: 2025-11-14
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai import OpenAI
from fuzzywuzzy import fuzz

# Import database
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from database_connection import SessionLocal
from models import FornasDrug

logger = logging.getLogger(__name__)


# ============================================================
# 1️⃣ DATABASE HELPER FUNCTIONS
# ============================================================

def db_get_all_drug_names() -> List[Dict[str, str]]:
    """Get semua nama obat dari database untuk RAG context"""
    db = SessionLocal()
    try:
        drugs = db.query(FornasDrug).all()
        return [
            {
                "obat_name": drug.obat_name,
                "kode_fornas": drug.kode_fornas,
                "kelas_terapi": drug.kelas_terapi or ""
            }
            for drug in drugs
        ]
    finally:
        db.close()


def db_exact_match(drug_name: str) -> Optional[FornasDrug]:
    """Exact match dengan obat_name atau kode_fornas"""
    db = SessionLocal()
    try:
        # Try obat_name first
        result = db.query(FornasDrug).filter(
            FornasDrug.obat_name.ilike(drug_name)
        ).first()
        
        if result:
            return result
        
        # Try kode_fornas
        result = db.query(FornasDrug).filter(
            FornasDrug.kode_fornas.ilike(drug_name)
        ).first()
        
        return result
    finally:
        db.close()


def db_fuzzy_match(drug_name: str, threshold: int = 85) -> Optional[Dict]:
    """Fuzzy match dengan semua obat di database"""
    db = SessionLocal()
    try:
        all_drugs = db.query(FornasDrug).all()
        
        best_match = None
        best_score = 0
        
        normalized_input = drug_name.lower().strip()
        
        for drug in all_drugs:
            # Compare with obat_name
            score = fuzz.ratio(normalized_input, drug.obat_name.lower())
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = drug
            
            # Compare with aliases if exists
            if drug.nama_obat_alias:
                try:
                    aliases = json.loads(drug.nama_obat_alias) if isinstance(drug.nama_obat_alias, str) else drug.nama_obat_alias
                    for alias in aliases:
                        alias_score = fuzz.ratio(normalized_input, alias.lower())
                        if alias_score > best_score and alias_score >= threshold:
                            best_score = alias_score
                            best_match = drug
                except:
                    pass
        
        if best_match:
            return {
                "drug": best_match,
                "confidence": best_score,
                "strategy": "fuzzy"
            }
        
        return None
    finally:
        db.close()


def db_search_by_keywords(keywords: str, limit: int = 20) -> List[FornasDrug]:
    """Search obat berdasarkan keywords (untuk RAG context)"""
    db = SessionLocal()
    try:
        results = db.query(FornasDrug).filter(
            FornasDrug.obat_name.ilike(f"%{keywords}%")
        ).limit(limit).all()
        
        return results
    finally:
        db.close()


# ============================================================
# 2️⃣ AI NORMALIZATION (English → Indonesian)
# ============================================================

class FornasAINormalizer:
    """AI-powered drug name normalization (English → Indonesian)"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        self._cache = {}  # Cache untuk hasil normalization
    
    def normalize_to_indonesian(self, drug_name: str, db_context: List[str] = None) -> Dict[str, Any]:
        """
        Normalize drug name ke Indonesian menggunakan AI + RAG
        
        Alur:
        1. Check cache
        2. Get database context (similar drugs)
        3. Call AI dengan RAG prompt
        4. Validate AI result dengan DB
        5. Return normalized name yang pasti ada di DB
        
        Args:
            drug_name: Input drug name (bisa English/typo/etc)
            db_context: List of similar drug names from DB (optional)
        
        Returns:
            {
                "original_input": "ceftriaxone",
                "normalized_name": "Seftriakson",
                "found_in_db": True,
                "db_match": FornasDrug object,
                "confidence": 95,
                "method": "ai_rag"
            }
        """
        # Check cache
        cache_key = drug_name.lower().strip()
        if cache_key in self._cache:
            logger.info(f"[FORNAS_AI] Cache hit for: {drug_name}")
            return self._cache[cache_key]
        
        # Get database context if not provided
        if not db_context:
            similar_drugs = db_search_by_keywords(drug_name, limit=20)
            db_context = [drug.obat_name for drug in similar_drugs]
        
        # Build RAG prompt
        prompt = self._build_rag_prompt(drug_name, db_context)
        
        # Call AI
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Anda adalah expert farmasi Indonesia. Tugas Anda: normalisasi nama obat ke terminologi Indonesia yang PASTI ADA di database FORNAS."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=150,
                response_format={"type": "json_object"}
            )
            
            ai_result = json.loads(response.choices[0].message.content)
            normalized_name = ai_result.get("normalized_name", "").strip()
            
            logger.info(f"[FORNAS_AI] AI normalized '{drug_name}' → '{normalized_name}'")
            
            # Validate dengan database
            db_match = db_exact_match(normalized_name)
            
            if not db_match:
                # Try fuzzy match dengan AI result
                fuzzy_result = db_fuzzy_match(normalized_name, threshold=80)
                if fuzzy_result:
                    db_match = fuzzy_result["drug"]
                    confidence = fuzzy_result["confidence"]
                else:
                    confidence = 0
            else:
                confidence = 100
            
            result = {
                "original_input": drug_name,
                "normalized_name": normalized_name,
                "found_in_db": db_match is not None,
                "db_match": db_match,
                "confidence": confidence,
                "method": "ai_rag"
            }
            
            # Cache result
            self._cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"[FORNAS_AI] Normalization failed for '{drug_name}': {e}")
            return {
                "original_input": drug_name,
                "normalized_name": drug_name,
                "found_in_db": False,
                "db_match": None,
                "confidence": 0,
                "method": "failed",
                "error": str(e)
            }
    
    def _build_rag_prompt(self, drug_name: str, db_context: List[str]) -> str:
        """Build RAG prompt dengan database context"""
        
        context_str = "\n".join([f"- {name}" for name in db_context[:15]])  # Limit 15 untuk token
        
        prompt = f"""Normalisasi nama obat ke bahasa Indonesia sesuai database FORNAS.

INPUT OBAT: {drug_name}

DATABASE CONTEXT (Obat yang mirip):
{context_str if context_str else "- (tidak ada context)"}

TUGAS:
1. Identifikasi nama obat generik dari input
2. Normalisasi ke terminologi farmasi Indonesia
3. PILIH nama yang PALING MIRIP dengan database context
4. Pastikan nama yang dipilih ADA di database context

ATURAN TRANSLITERASI:
- "c" sebelum e/i → "s" (ceftriaxone → seftriakson)
- "x" → "ks" (levofloxacin → levofloksasin)
- "ph" → "f" (phenytoin → fenitoin)
- Pertahankan huruf kapital dari database

CONTOH:
Input: "ceftriaxone" → Output: "Seftriakson"
Input: "paracetamol" → Output: "Parasetamol"
Input: "metformin" → Output: "Metformin"

OUTPUT FORMAT (JSON):
{{
  "normalized_name": "Nama Obat Indonesia yang PASTI ADA di database",
  "confidence": 95,
  "reasoning": "Alasan singkat"
}}

PENTING: normalized_name HARUS persis salah satu dari database context!"""

        return prompt


# ============================================================
# 3️⃣ SMART MATCHER (Multi-Strategy)
# ============================================================

class FornasSmartMatcher:
    """
    Smart matcher dengan cascade strategy:
    1. Exact match
    2. Fuzzy match
    3. AI normalization → DB match
    """
    
    def __init__(self):
        self.ai_normalizer = FornasAINormalizer()
    
    def match(self, drug_name: str, threshold: int = 85, use_ai: bool = True) -> Dict[str, Any]:
        """
        Match drug name dengan database
        
        Strategy cascade:
        1. Exact match (fastest)
        2. Fuzzy match (fast)
        3. AI normalization + DB validation (accurate)
        
        Args:
            drug_name: Input drug name
            threshold: Fuzzy match threshold (default: 85)
            use_ai: Enable AI normalization jika fuzzy gagal (default: True)
        
        Returns:
            {
                "found": True/False,
                "drug": FornasDrug object,
                "confidence": 0-100,
                "strategy": "exact" | "fuzzy" | "ai_rag",
                "original_input": "ceftriaxone",
                "matched_name": "Seftriakson"
            }
        """
        if not drug_name or drug_name.strip() == "":
            return self._not_found_result(drug_name)
        
        # Clean input
        cleaned_name = self._clean_drug_name(drug_name)
        
        logger.info(f"[FORNAS_MATCH] Matching: {drug_name} → {cleaned_name}")
        
        # Strategy 1: Exact match
        exact_result = db_exact_match(cleaned_name)
        if exact_result:
            logger.info(f"[FORNAS_MATCH] ✓ Exact match found")
            return {
                "found": True,
                "drug": exact_result,
                "confidence": 100,
                "strategy": "exact",
                "original_input": drug_name,
                "matched_name": exact_result.obat_name
            }
        
        # Strategy 2: Fuzzy match
        fuzzy_result = db_fuzzy_match(cleaned_name, threshold=threshold)
        if fuzzy_result:
            logger.info(f"[FORNAS_MATCH] ✓ Fuzzy match found (score: {fuzzy_result['confidence']})")
            return {
                "found": True,
                "drug": fuzzy_result["drug"],
                "confidence": fuzzy_result["confidence"],
                "strategy": "fuzzy",
                "original_input": drug_name,
                "matched_name": fuzzy_result["drug"].obat_name
            }
        
        # Strategy 3: AI normalization (jika enabled)
        if use_ai:
            logger.info(f"[FORNAS_MATCH] Trying AI normalization...")
            ai_result = self.ai_normalizer.normalize_to_indonesian(cleaned_name)
            
            if ai_result["found_in_db"]:
                logger.info(f"[FORNAS_MATCH] ✓ AI normalization successful")
                return {
                    "found": True,
                    "drug": ai_result["db_match"],
                    "confidence": ai_result["confidence"],
                    "strategy": "ai_rag",
                    "original_input": drug_name,
                    "matched_name": ai_result["normalized_name"]
                }
        
        # Not found
        logger.warning(f"[FORNAS_MATCH] ✗ No match found for: {drug_name}")
        return self._not_found_result(drug_name)
    
    def _clean_drug_name(self, name: str) -> str:
        """Clean drug name dari dosage, route, dll"""
        cleaned = name.strip()
        
        # Remove dosage (1g, 500mg, dll)
        cleaned = re.sub(r'\d+\s*(mg|g|ml|mcg|iu|cc)\b', '', cleaned, flags=re.IGNORECASE)
        
        # Remove route (IV, oral, dll)
        cleaned = re.sub(r'\b(iv|im|sc|po|oral|injeksi|infus|tablet|kapsul)\b', '', cleaned, flags=re.IGNORECASE)
        
        # Clean whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _not_found_result(self, drug_name: str) -> Dict[str, Any]:
        """Standard not found result"""
        return {
            "found": False,
            "drug": None,
            "confidence": 0,
            "strategy": None,
            "original_input": drug_name,
            "matched_name": None
        }


# ============================================================
# 4️⃣ BATCH VALIDATOR (Multiple Drugs)
# ============================================================

class FornasBatchValidator:
    """Validate multiple drugs sekaligus dengan AI batch call"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        self.matcher = FornasSmartMatcher()
    
    def validate_drugs(
        self,
        drug_list: List[str],
        diagnosis_icd10: str,
        diagnosis_name: str
    ) -> Dict[str, Any]:
        """
        Validate multiple drugs dengan diagnosis
        
        Alur:
        1. Match semua drugs ke database (dengan AI normalization)
        2. Batch validate dengan AI (single call)
        3. Return hasil validasi
        
        Args:
            drug_list: List of drug names
            diagnosis_icd10: ICD-10 code
            diagnosis_name: Diagnosis name
        
        Returns:
            {
                "fornas_validation": [...],
                "summary": {...}
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
        
        logger.info(f"[FORNAS_BATCH] Validating {len(drug_list)} drugs")
        
        # Step 1: Match all drugs ke database
        matched_drugs = []
        for drug_name in drug_list:
            if not drug_name or drug_name.strip() == "":
                continue
            
            match_result = self.matcher.match(drug_name, use_ai=True)
            matched_drugs.append(match_result)
        
        logger.info(f"[FORNAS_BATCH] Matched {sum(1 for m in matched_drugs if m['found'])} / {len(matched_drugs)} drugs")
        
        # Step 2: Separate found vs not found
        fornas_drugs = []
        non_fornas_drugs = []
        
        for idx, match in enumerate(matched_drugs, 1):
            if match["found"]:
                drug = match["drug"]
                fornas_drugs.append({
                    "index": idx,
                    "nama_obat": drug.obat_name,
                    "kelas_terapi": drug.kelas_terapi or "Tidak tersedia",
                    "sumber_regulasi": drug.sumber_regulasi or "-",
                    "original_input": match["original_input"]
                })
            else:
                non_fornas_drugs.append({
                    "no": idx,
                    "nama_obat": match["original_input"],
                    "kelas_terapi": "Tidak ditemukan di FORNAS",
                    "status_fornas": "❌ Non-Fornas",
                    "catatan_ai": "Obat tidak terdaftar dalam Formularium Nasional",
                    "sumber_regulasi": "-"
                })
        
        # Step 3: Batch AI validation (hanya untuk yang found)
        if fornas_drugs:
            ai_validated = self._batch_ai_validate(fornas_drugs, diagnosis_icd10, diagnosis_name)
        else:
            ai_validated = []
        
        # Step 4: Combine results
        all_results = non_fornas_drugs + ai_validated
        all_results.sort(key=lambda x: x["no"])
        
        # Step 5: Generate summary
        summary = self._generate_summary(all_results)
        
        return {
            "fornas_validation": all_results,
            "summary": summary
        }
    
    def _batch_ai_validate(
        self,
        drugs: List[Dict],
        diagnosis_icd10: str,
        diagnosis_name: str
    ) -> List[Dict]:
        """Validate semua drugs dengan single AI call"""
        
        # Build prompt
        drugs_list = "\n".join([
            f"{d['index']}. {d['nama_obat']} - {d['kelas_terapi']}"
            for d in drugs
        ])
        
        prompt = f"""Validasi kesesuaian SEMUA obat berikut dengan diagnosis berdasarkan FORNAS & PNPK Indonesia.

DIAGNOSIS:
- Nama: {diagnosis_name}
- ICD-10: {diagnosis_icd10}

DAFTAR OBAT:
{drugs_list}

TUGAS:
Untuk SETIAP obat, tentukan:
1. status_fornas: "✅ Sesuai (Fornas)" | "⚠️ Perlu Justifikasi" | "❌ Non-Fornas"
2. catatan_ai: Penjelasan singkat (max 120 karakter)

KRITERIA:
- ✅ Sesuai: Obat lini pertama untuk diagnosis ini
- ⚠️ Perlu Justifikasi: Obat bisa digunakan tapi butuh justifikasi
- ❌ Non-Fornas: Tidak relevan atau kontraindikasi

OUTPUT FORMAT (JSON):
{{
  "validations": [
    {{
      "index": 1,
      "status_fornas": "✅ Sesuai (Fornas)",
      "catatan_ai": "Lini pertama untuk pneumonia"
    }}
  ]
}}

PENTING: Berikan hasil untuk SEMUA {len(drugs)} obat!"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Anda adalah AI validator FORNAS untuk BPJS Indonesia. Objektif dan akurat."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            ai_result = json.loads(response.choices[0].message.content)
            validations = ai_result.get("validations", [])
            
            logger.info(f"[FORNAS_BATCH] AI validated {len(validations)} drugs")
            
            # Map results
            results = []
            for drug_info in drugs:
                idx = drug_info["index"]
                ai_val = next((v for v in validations if v.get("index") == idx), None)
                
                if ai_val:
                    results.append({
                        "no": idx,
                        "nama_obat": drug_info["nama_obat"],
                        "kelas_terapi": drug_info["kelas_terapi"],
                        "status_fornas": ai_val.get("status_fornas", "⚠️ Perlu Justifikasi"),
                        "catatan_ai": ai_val.get("catatan_ai", "Perlu review manual")[:120],
                        "sumber_regulasi": drug_info["sumber_regulasi"]
                    })
                else:
                    # Fallback
                    results.append({
                        "no": idx,
                        "nama_obat": drug_info["nama_obat"],
                        "kelas_terapi": drug_info["kelas_terapi"],
                        "status_fornas": "⚠️ Perlu Justifikasi",
                        "catatan_ai": "Obat terdaftar di FORNAS. Perlu review manual.",
                        "sumber_regulasi": drug_info["sumber_regulasi"]
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"[FORNAS_BATCH] AI validation failed: {e}")
            
            # Fallback: semua jadi "Perlu Justifikasi"
            return [
                {
                    "no": d["index"],
                    "nama_obat": d["nama_obat"],
                    "kelas_terapi": d["kelas_terapi"],
                    "status_fornas": "⚠️ Perlu Justifikasi",
                    "catatan_ai": "Obat terdaftar di FORNAS. Perlu review manual.",
                    "sumber_regulasi": d["sumber_regulasi"]
                }
                for d in drugs
            ]
    
    def _generate_summary(self, validations: List[Dict]) -> Dict:
        """Generate validation summary"""
        total = len(validations)
        sesuai = sum(1 for v in validations if "✅" in v.get("status_fornas", ""))
        perlu_justifikasi = sum(1 for v in validations if "⚠️" in v.get("status_fornas", ""))
        non_fornas = sum(1 for v in validations if "❌" in v.get("status_fornas", ""))
        
        return {
            "total_obat": total,
            "sesuai": sesuai,
            "perlu_justifikasi": perlu_justifikasi,
            "non_fornas": non_fornas,
            "update_date": datetime.now().strftime("%Y-%m-%d"),
            "status_database": "Official Verified"
        }


# ============================================================
# 5️⃣ PUBLIC API
# ============================================================

def match_drug(drug_name: str, use_ai: bool = True) -> Dict[str, Any]:
    """
    Match single drug dengan database
    
    Args:
        drug_name: Drug name to match
        use_ai: Enable AI normalization (default: True)
    
    Returns:
        Match result dengan drug info
    
    Example:
        >>> result = match_drug("ceftriaxone")
        >>> print(result["found"])  # True
        >>> print(result["drug"].obat_name)  # "Seftriakson"
    """
    matcher = FornasSmartMatcher()
    return matcher.match(drug_name, use_ai=use_ai)


def validate_fornas(
    drug_list: List[str],
    diagnosis_icd10: str,
    diagnosis_name: str
) -> Dict[str, Any]:
    """
    Validate multiple drugs dengan diagnosis
    
    Args:
        drug_list: List of drug names
        diagnosis_icd10: ICD-10 code
        diagnosis_name: Diagnosis name
    
    Returns:
        Validation results dengan summary
    
    Example:
        >>> result = validate_fornas(
        ...     drug_list=["Ceftriaxone 1g IV", "Paracetamol 500mg"],
        ...     diagnosis_icd10="J18.9",
        ...     diagnosis_name="Pneumonia"
        ... )
        >>> print(result["summary"]["total_obat"])  # 2
    """
    validator = FornasBatchValidator()
    return validator.validate_drugs(drug_list, diagnosis_icd10, diagnosis_name)


# Backward compatibility
def match_multiple_obat(obat_list: List[str], threshold: int = 85) -> List[Dict]:
    """
    DEPRECATED: Use validate_fornas() instead
    
    Legacy function untuk backward compatibility
    """
    matcher = FornasSmartMatcher()
    results = []
    
    for obat_name in obat_list:
        if not obat_name or obat_name.strip() == "":
            continue
        
        match_result = matcher.match(obat_name, threshold=threshold, use_ai=True)
        
        if match_result["found"]:
            drug = match_result["drug"]
            results.append({
                "input_name": obat_name,
                "nama_generik": drug.obat_name,
                "kode_fornas": drug.kode_fornas,
                "kelas_terapi": drug.kelas_terapi or "Tidak tersedia",
                "sumber_regulasi": drug.sumber_regulasi or "-",
                "found": True,
                "confidence": match_result["confidence"],
                "strategy": match_result["strategy"]
            })
        else:
            results.append({
                "input_name": obat_name,
                "nama_generik": obat_name,
                "kode_fornas": None,
                "kelas_terapi": "Tidak ditemukan",
                "sumber_regulasi": None,
                "found": False,
                "confidence": 0,
                "strategy": None
            })
    
    return results
