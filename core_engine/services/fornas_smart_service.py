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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Note: fuzzywuzzy removed per new flow (we rely on exact DB match + AI normalization)
import threading

# Import database
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from database_connection import SessionLocal
from models import FornasDrug

logger = logging.getLogger(__name__)

# Module-level, thread-safe cache for normalizer to be shared across instances/workers (in-process)
_NORMALIZER_CACHE: Dict[str, Dict[str, Any]] = {}
_NORMALIZER_LOCK = threading.Lock()


def _normalize_text_for_matching(s: str) -> str:
    """Normalize text for matching: lowercase, remove dosage/route tokens, punctuation, normalize whitespace."""
    if not s:
        return ""
    x = s.lower()
    # remove dosage tokens
    x = re.sub(r'\d+\s*(mg|g|ml|mcg|iu|cc)\b', '', x, flags=re.IGNORECASE)
    # remove route/administration words
    x = re.sub(r'\b(iv|im|sc|po|oral|injeksi|infus|tablet|kapsul)\b', '', x, flags=re.IGNORECASE)
    # remove punctuation
    x = re.sub(r'[^a-z0-9\s]', ' ', x)
    # collapse whitespace
    x = re.sub(r'\s+', ' ', x).strip()
    return x


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
        # Try obat_name first (case-insensitive exact-ish)
        result = db.query(FornasDrug).filter(
            FornasDrug.obat_name.ilike(f"%{drug_name}%")
        ).first()

        if result:
            return result

        # Try kode_fornas exact
        result = db.query(FornasDrug).filter(
            FornasDrug.kode_fornas.ilike(drug_name)
        ).first()

        if result:
            return result

        # Fallback: normalized matching against candidates from keyword search
        cleaned = _normalize_text_for_matching(drug_name)
        if not cleaned:
            return None

        candidates = db.query(FornasDrug).filter(
            FornasDrug.obat_name.ilike(f"%{cleaned}%")
        ).limit(50).all()

        for c in candidates:
            if _normalize_text_for_matching(c.obat_name) == cleaned:
                return c

        return None
    finally:
        db.close()


def db_fuzzy_match(drug_name: str, threshold: int = 85) -> Optional[Dict]:
    """Deprecated: fuzzy matching removed in new flow. Keep function for compatibility but it returns None."""
    return None


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


def db_search_by_subkelas(subkelas: str, limit: int = 50) -> List[FornasDrug]:
    """Search obat berdasarkan subkelas_terapi (preferensi untuk rekomendasi)"""
    if not subkelas:
        return []
    db = SessionLocal()
    try:
        results = db.query(FornasDrug).filter(
            FornasDrug.subkelas_terapi.ilike(f"%{subkelas}%")
        ).limit(limit).all()

        return results
    finally:
        db.close()


def db_search_by_kelas(kelas: str, limit: int = 50) -> List[FornasDrug]:
    """Search obat berdasarkan kelas_terapi (fallback jika subkelas tidak ada)"""
    if not kelas:
        return []
    db = SessionLocal()
    try:
        results = db.query(FornasDrug).filter(
            FornasDrug.kelas_terapi.ilike(f"%{kelas}%")
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
        # Check module-level cache (thread-safe)
        cache_key = _normalize_text_for_matching(drug_name)
        with _NORMALIZER_LOCK:
            cached = _NORMALIZER_CACHE.get(cache_key)
        if cached:
            logger.info(f"[FORNAS_AI] Cache hit for: {drug_name}")
            # reconstruct db_match object if possible
            db_match = None
            if cached.get("kode_fornas"):
                db_match = db_exact_match(cached.get("kode_fornas"))
            elif cached.get("normalized_name"):
                db_match = db_exact_match(cached.get("normalized_name"))

            return {
                "original_input": drug_name,
                "normalized_name": cached.get("normalized_name") or drug_name,
                "found_in_db": cached.get("found_in_db", False),
                "db_match": db_match,
                "confidence": cached.get("confidence", 0),
                "method": "ai_rag_cached"
            }
        
        # Get database context if not provided
        if not db_context:
            similar_drugs = db_search_by_keywords(drug_name, limit=20)
            db_context = [drug.obat_name for drug in similar_drugs] if similar_drugs else []
        
        if not db_context:
            print(f"[FORNAS_AI] ⚠️ No database context for '{drug_name}'")
            print(f"[FORNAS_AI] AI will normalize based on pharmaceutical knowledge only")
        
        # Build RAG prompt (handles empty context)
        prompt = self._build_rag_prompt(drug_name, db_context)
        
        # Call AI (robust parsing)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Anda adalah expert farmasi Indonesia. Tugas Anda: normalisasi nama obat ke terminologi Indonesia yang PASTI ADA di database FORNAS. Kembalikan hanya objek JSON sesuai format yang diminta."
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

            # SDK may already return a parsed object or a JSON string
            raw_content = None
            try:
                raw_content = response.choices[0].message.content
            except Exception:
                # Fallback if different shape
                raw_content = getattr(response.choices[0].message, 'content', None) or response.choices[0].get('text')

            if isinstance(raw_content, (dict, list)):
                ai_result = raw_content
            else:
                try:
                    ai_result = json.loads(raw_content or "{}")
                except Exception:
                    ai_result = {}

            normalized_name = (ai_result.get("normalized_name") or "").strip()

            logger.info(f"[FORNAS_AI] AI normalized '{drug_name}' → '{normalized_name}'")

            # Validate with exact DB match only (no fuzzy)
            db_match = db_exact_match(normalized_name)
            confidence = 100 if db_match else 0

            # If AI returned a normalized_name but no DB match, attempt one retry with stricter prompt
            if normalized_name and not db_match:
                try:
                    retry_prompt = (
                        "Pilih SATU nama obat PERSIS dari konteks database di bawah yang paling sesuai dengan input. "
                        "Kembalikan hanya JSON: {\"normalized_name\": \"...\", \"confidence\": 100}.\n\n"
                        f"INPUT: {drug_name}\nDATABASE CONTEXT:\n" + "\n".join([f"- {n}" for n in (db_context or [])[:15]])
                    )

                    retry_resp = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "Anda adalah expert farmasi Indonesia. RETURN ONLY JSON."},
                            {"role": "user", "content": retry_prompt}
                        ],
                        temperature=0.0,
                        max_tokens=80,
                        response_format={"type": "json_object"}
                    )

                    raw_retry = None
                    try:
                        raw_retry = retry_resp.choices[0].message.content
                    except Exception:
                        raw_retry = getattr(retry_resp.choices[0].message, 'content', None) or retry_resp.choices[0].get('text')

                    if isinstance(raw_retry, (dict, list)):
                        retry_ai = raw_retry
                    else:
                        try:
                            retry_ai = json.loads(raw_retry or "{}")
                        except Exception:
                            retry_ai = {}

                    retry_name = (retry_ai.get("normalized_name") or "").strip()
                    if retry_name:
                        db_match = db_exact_match(retry_name)
                        if db_match:
                            normalized_name = retry_name
                            confidence = 100
                except Exception:
                    # swallow retry errors but keep original result
                    pass

            result = {
                "original_input": drug_name,
                "normalized_name": normalized_name or drug_name,
                "found_in_db": db_match is not None,
                "db_match": db_match,
                "confidence": confidence,
                "method": "ai_rag"
            }

            # Cache minimal result (do not cache DB objects)
            cache_value = {
                "normalized_name": result["normalized_name"],
                "found_in_db": result["found_in_db"],
                "kode_fornas": result["db_match"].kode_fornas if result["db_match"] else None,
                "confidence": result["confidence"]
            }
            with _NORMALIZER_LOCK:
                _NORMALIZER_CACHE[cache_key] = cache_value

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

    def generate_recommendations(self, drug_name: str, max_recommend: int = 5) -> Dict[str, Any]:
        """
        Generate recommended alternative drugs based on input.

        Flow:
        1. Try DB exact match, if fails → normalize with AI first
        2. Collect DB context with FALLBACK HIERARCHY:
           - Priority 1: Same subkelas_terapi (most specific)
           - Priority 2: Same kelas_terapi (broader category)
           - Priority 3: Keyword-based search (least specific)
        3. Ask AI to rank up to `max_recommend` recommended drugs from context with short reasons
        4. Map recommendations to DB records and return structured list
        """
        # Prepare context from DB
        # First try to find a DB match for the input to get subkelas_terapi
        db_match_for_input = db_exact_match(drug_name)
        
        # If no match, try AI normalization first
        normalized_name = drug_name
        if not db_match_for_input:
            try:
                norm_result = self.normalize_to_indonesian(drug_name)
                if norm_result.get('normalized_name'):
                    normalized_name = norm_result['normalized_name']
                    db_match_for_input = db_exact_match(normalized_name)
                    logger.info(f"[FORNAS_AI] Normalized '{drug_name}' → '{normalized_name}' for recommendations")
            except Exception as e:
                logger.warning(f"[FORNAS_AI] Normalization failed for '{drug_name}': {e}")

        # IMPROVED: Fallback hierarchy untuk build kandidat pool
        similar = []
        context_strategy = "unknown"
        
        if db_match_for_input:
            # Priority 1: Subkelas terapi (paling spesifik)
            subkelas = getattr(db_match_for_input, 'subkelas_terapi', None)
            if subkelas and subkelas.strip():
                similar = db_search_by_subkelas(subkelas, limit=50)
                context_strategy = f"subkelas_terapi: {subkelas}"
                logger.info(f"[FORNAS_AI] Found {len(similar)} drugs with same subkelas_terapi")
            
            # Priority 2: Kelas terapi (jika subkelas kosong atau hasil < 5)
            if len(similar) < 5:
                kelas = getattr(db_match_for_input, 'kelas_terapi', None)
                if kelas and kelas.strip():
                    kelas_results = db_search_by_kelas(kelas, limit=50)
                    # Merge dengan hasil subkelas (jika ada) dan deduplicate
                    existing_ids = {d.id for d in similar if hasattr(d, 'id')}
                    for drug in kelas_results:
                        if not hasattr(drug, 'id') or drug.id not in existing_ids:
                            similar.append(drug)
                    context_strategy = f"kelas_terapi: {kelas}"
                    logger.info(f"[FORNAS_AI] Expanded to {len(similar)} drugs with same kelas_terapi")
        
        # Priority 3: Keyword search (jika masih < 10 atau tidak ada db_match)
        if len(similar) < 10:
            keyword_results = db_search_by_keywords(normalized_name, limit=30)
            existing_ids = {d.id for d in similar if hasattr(d, 'id')}
            for drug in keyword_results:
                if not hasattr(drug, 'id') or drug.id not in existing_ids:
                    similar.append(drug)
            context_strategy = f"keyword: {normalized_name}"
            logger.info(f"[FORNAS_AI] Expanded to {len(similar)} drugs with keyword search")

        context_names = [d.obat_name for d in similar]

        # Fallback: jika masih kosong, ambil sample dari DB
        if not context_names:
            all_names = db_get_all_drug_names()
            context_names = [d["obat_name"] for d in all_names[:30]]
            context_strategy = "random_sample"
            logger.warning(f"[FORNAS_AI] No specific context found, using random sample")

        # IMPROVED: Better prompt dengan instruksi lebih jelas
        prompt = f"""Berikan maksimal {max_recommend} rekomendasi obat yang paling relevan sebagai alternatif atau yang berada di kelas terapi serupa untuk input: \"{drug_name}\".

INSTRUKSI:
- Pilih obat yang memiliki indikasi/mekanisme aksi SERUPA
- Return HANYA nama generik obat (tanpa dosis, tanpa bentuk sediaan)
- Berikan alasan farmakologis singkat untuk setiap rekomendasi

DATABASE CONTEXT (obat yang tersedia):
"""
        prompt += "\n".join([f"- {n}" for n in context_names[:25]])
        prompt += "\n\nOUTPUT FORMAT (JSON): {\n  \"recommendations\": [ {\"name\": \"nama generik saja\", \"reason\": \"alasan farmakologis\"} ]\n}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Anda adalah expert farmasi Indonesia. Berikan rekomendasi obat berdasarkan context yang diberikan. Return HANYA nama generik tanpa dosis. Kembalikan hanya JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800,
                response_format={"type": "json_object"}
            )

            raw = None
            try:
                raw = response.choices[0].message.content
            except Exception:
                raw = getattr(response.choices[0].message, 'content', None) or response.choices[0].get('text')

            if isinstance(raw, (dict, list)):
                ai_res = raw
            else:
                try:
                    ai_res = json.loads(raw or "{}")
                except Exception:
                    ai_res = {}

            recs = ai_res.get("recommendations", []) if isinstance(ai_res, dict) else []

            structured = []
            for r in recs[:max_recommend]:
                name = (r.get("name") or r.get("nama") or "").strip()
                reason = (r.get("reason") or r.get("alasan") or "").strip()
                if not name:
                    continue

                # IMPROVED: Clean AI output (hapus dosis jika ada)
                name_cleaned = _normalize_text_for_matching(name)

                # Map to DB
                db_match = db_exact_match(name_cleaned)
                if not db_match:
                    # try partial search
                    candidates = db_search_by_keywords(name_cleaned, limit=1)
                    db_match = candidates[0] if candidates else None

                structured.append({
                    "recommended_name": name_cleaned,
                    "reason": reason or "Direkomendasikan AI berdasarkan nama/kelas terapi",
                    "db_match": db_match,
                    "context_strategy": context_strategy  # Debug info
                })

            # Fallback: if AI gave nothing, return top candidates from DB
            if not structured and similar:
                logger.warning(f"[FORNAS_AI] AI returned no recommendations, using DB fallback")
                for d in similar[:max_recommend]:
                    structured.append({
                        "recommended_name": d.obat_name,
                        "reason": "Obat sejenis dari database (fallback)",
                        "db_match": d,
                        "context_strategy": context_strategy
                    })

            return {
                "original_input": drug_name,
                "recommendations": structured
            }

        except Exception as e:
            logger.error(f"[FORNAS_AI] Recommendation generation failed for '{drug_name}': {e}")
            # Fallback to DB-only suggestions
            fallback = []
            for d in similar[:max_recommend]:
                fallback.append({
                    "recommended_name": d.obat_name,
                    "reason": "Similar name / keyword match",
                    "db_match": d
                })

            return {
                "original_input": drug_name,
                "recommendations": fallback,
                "error": str(e)
            }
    
    def _build_rag_prompt(self, drug_name: str, db_context: List[str]) -> str:
        """Build RAG prompt dengan database context (or fallback to AI knowledge)"""
        
        if db_context:
            context_str = "\n".join([f"- {name}" for name in db_context[:15]])  # Limit 15 untuk token
            context_section = f"""DATABASE CONTEXT (Obat yang mirip):
{context_str}

TUGAS:
1. Identifikasi nama obat generik dari input
2. Normalisasi ke terminologi farmasi Indonesia
3. PILIH nama yang PALING MIRIP dengan database context
4. Pastikan nama yang dipilih ADA di database context"""
        else:
            # No DB context - AI uses pharmaceutical knowledge
            context_section = """DATABASE CONTEXT: (tidak tersedia)

TUGAS:
1. Identifikasi nama obat generik dari input
2. Normalisasi ke terminologi farmasi Indonesia standar
3. Gunakan pengetahuan farmasi untuk transliterasi yang benar
4. Hasil akan divalidasi dengan database setelah normalisasi"""
        
        prompt = f"""Normalisasi nama obat ke bahasa Indonesia sesuai database FORNAS.

INPUT OBAT: {drug_name}

{context_section}

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
        
        # Note: fuzzy matching removed from flow. We rely on exact match first,
        # then AI normalization if enabled.
        
        # Strategy 2: AI normalization (jika enabled)
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
        cleaned = name.lower().strip()

        # Remove fornas markers
        cleaned = cleaned.replace("[p]", "").replace("(p)", "")

        # Remove underscores from frontend sediaan
        cleaned = cleaned.replace("_", " ")

        # Remove dosage
        cleaned = re.sub(r'\d+\s*(mg|g|ml|mcg|iu|cc)\b', '', cleaned, flags=re.IGNORECASE)

        # Remove route
        cleaned = re.sub(r'\b(iv|im|sc|po|oral|injeksi|infus|tablet|kapsul)\b', '', cleaned, flags=re.IGNORECASE)

        # Multiple spaces → single space
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
        
        # Step 1: For new flow, we assume input drug names are selected by user
        # (either canonical names or raw input). Validation only runs for names
        # that exist in the FORNAS DB. Do not call AI normalization here.
        fornas_drugs = []
        non_fornas_drugs = []

        for idx, drug_name in enumerate(drug_list, 1):
            if not drug_name or drug_name.strip() == "":
                continue

            cleaned = self.matcher._clean_drug_name(drug_name)
            db_match = db_exact_match(cleaned)

            # NEW FIX — Gunakan AI normalization kalau exact match gagal
            if not db_match:
                ai_res = self.matcher.ai_normalizer.normalize_to_indonesian(drug_name)
                if ai_res.get("found_in_db"):
                    db_match = ai_res.get("db_match")

            if db_match:
                fornas_drugs.append({
                    "index": idx,
                    "nama_obat": db_match.obat_name,
                    "kelas_terapi": db_match.kelas_terapi or "Tidak tersedia",
                    "sumber_regulasi": db_match.sumber_regulasi or "-",
                    "original_input": drug_name
                })
            else:
                non_fornas_drugs.append({
                    "no": idx,
                    "nama_obat": drug_name,
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
            "fornas_summary": summary    # <-- WAJIB MENGGUNAKAN FIELD INI
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


def recommend_drug(drug_input: str, max_recommend: int = 5) -> Dict[str, Any]:
    """
    Generate AI-backed recommendations for a drug input (used when user clicks 'Generate AI').

    Returns:
        {
            "original_input": str,
            "recommendations": [ {"recommended_name": str, "reason": str, "db_match": FornasDrug|None}, ... ]
        }
    """
    normalizer = FornasAINormalizer()
    return normalizer.generate_recommendations(drug_input, max_recommend=max_recommend)


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
    # === FIX AMAN (TAMBAHAN 4 BARIS) ===
    # Jika FE hanya kirim nama generik (mis: 'fentanil'), padahal data fornas hanya punya sediaan detail,
    # kita gunakan nama generik sebagai fallback match.
    normalized = []
    for drug in drug_list:
        generic = drug.lower().split()[0]  # ambil nama generik saja
        normalized.append(generic)

    drug_list = normalized
    # ==================================
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
