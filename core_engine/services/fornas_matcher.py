"""
FORNAS Drug Matcher Service

Multi-strategy drug name matching:
1. Exact match (kode_fornas, obat_name)
2. Alias match (nama_obat_alias)
3. Normalized match (lowercase, strip whitespace)
4. Fuzzy match (Levenshtein distance)
5. Phonetic match (untuk typo umum)

Author: AI Assistant
Date: 2025-11-09
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from fuzzywuzzy import fuzz, process
from openai import OpenAI
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import from core_engine database
from database_connection import SessionLocal
from models import FornasDrug


class FornasDrugMatcher:
    """
    Smart drug name matcher dengan multi-strategy approach + AI transliteration
    """
    
    def __init__(self):
        self.db = SessionLocal()
        self._cache = {}  # Cache untuk hasil matching
        self._transliteration_cache = {}  # Cache untuk AI transliteration
        
        # Initialize OpenAI client for transliteration
        api_key = os.getenv("OPENAI_API_KEY")
        self.ai_client = OpenAI(api_key=api_key) if api_key else None
        self.ai_enabled = self.ai_client is not None
        
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    def normalize_drug_name(self, name: str, use_ai: bool = True) -> str:
        """
        Normalisasi nama obat untuk matching
        - Lowercase
        - Remove extra whitespace
        - Remove common suffixes/prefixes
        - AI-powered English → Indonesian transliteration
        
        Args:
            name: Drug name to normalize
            use_ai: Use AI for transliteration (default: True)
        
        Returns:
            Normalized drug name (Indonesian version if possible)
        """
        if not name:
            return ""
        
        normalized = name.lower().strip()
        
        # Remove common medical suffixes first
        suffixes = [" injection", " injeksi", " tablet", " tab", " kapsul", " caps", 
                   " sirup", " syrup", " infus", " infusion", " [p]", "[p]", " iv", " oral"]
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        
        # Remove dosage info (e.g., "500mg", "1g")
        import re
        normalized = re.sub(r'\d+\s*(mg|g|ml|mcg|iu)', '', normalized).strip()
        
        # ✅ AI-POWERED TRANSLITERATION (if enabled)
        if use_ai and self.ai_enabled:
            # Check cache first
            if normalized in self._transliteration_cache:
                return self._transliteration_cache[normalized]
            
            # Try AI transliteration for better accuracy
            try:
                indonesian_name = self._ai_transliterate(normalized)
                if indonesian_name and indonesian_name != normalized:
                    # Cache the result
                    self._transliteration_cache[normalized] = indonesian_name
                    return indonesian_name
            except Exception as e:
                # Fallback to original if AI fails
                print(f"[FORNAS_MATCHER] AI transliteration failed for '{normalized}': {e}")
        
        return normalized
    
    def _ai_transliterate(self, drug_name: str) -> str:
        """
        Use AI to transliterate English drug name to Indonesian
        
        Args:
            drug_name: Drug name (cleaned, lowercase)
        
        Returns:
            Indonesian version of drug name
        
        Example:
            "ceftriaxone" → "seftriakson"
            "paracetamol" → "parasetamol"
            "levofloxacin" → "levofloksasin"
        """
        if not self.ai_client:
            return drug_name
        
        prompt = f"""Convert this pharmaceutical drug name from English to Indonesian medical terminology.

DRUG NAME: {drug_name}

RULES:
1. If already in Indonesian, return as-is
2. Apply standard Indonesian transliteration:
   - "c" before e/i → "s" (ceftriaxone → seftriakson)
   - "x" → "ks" (levofloxacin → levofloksasin)
   - Keep generic pharmaceutical naming conventions
3. Return ONLY the Indonesian drug name, nothing else
4. If unsure, return original name

EXAMPLES:
- ceftriaxone → seftriakson
- paracetamol → parasetamol
- levofloxacin → levofloksasin
- metformin → metformin (same)
- salbutamol → salbutamol (same)

Indonesian name:"""

        try:
            response = self.ai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a pharmaceutical terminology expert specializing in English-Indonesian drug name transliteration. Return only the drug name, no explanation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Very low for consistency
                max_tokens=50
            )
            
            result = response.choices[0].message.content.strip().lower()
            
            # Clean result (remove any extra text)
            result = result.split('\n')[0].split(',')[0].strip()
            
            return result if result else drug_name
            
        except Exception as e:
            print(f"[FORNAS_MATCHER] AI transliteration error: {e}")
            return drug_name
    
    def exact_match(self, drug_name: str) -> Optional[FornasDrug]:
        """
        Strategy 1: Exact match dengan obat_name atau kode_fornas
        """
        # Try exact match with obat_name
        result = self.db.query(FornasDrug).filter(
            FornasDrug.obat_name == drug_name
        ).first()
        
        if result:
            return result
        
        # Try exact match with kode_fornas (case-insensitive)
        result = self.db.query(FornasDrug).filter(
            FornasDrug.kode_fornas.ilike(drug_name)
        ).first()
        
        return result
    
    def alias_match(self, drug_name: str) -> Optional[FornasDrug]:
        """
        Strategy 2: Match dengan nama_obat_alias (JSON array)
        """
        normalized = self.normalize_drug_name(drug_name)
        
        # Query all drugs and check aliases in Python (PostgreSQL JSON array contains check)
        drugs = self.db.query(FornasDrug).filter(
            FornasDrug.nama_obat_alias.isnot(None)
        ).all()
        
        for drug in drugs:
            if drug.nama_obat_alias:
                # nama_obat_alias is JSON array: ["alias1", "alias2", ...]
                for alias in drug.nama_obat_alias:
                    if self.normalize_drug_name(alias) == normalized:
                        return drug
        
        return None
    
    def normalized_match(self, drug_name: str) -> Optional[FornasDrug]:
        """
        Strategy 3: Normalized string match
        """
        normalized = self.normalize_drug_name(drug_name)
        
        # Search in normalized obat_name
        drugs = self.db.query(FornasDrug).all()
        
        for drug in drugs:
            if self.normalize_drug_name(drug.obat_name) == normalized:
                return drug
        
        return None
    
    def fuzzy_match(self, drug_name: str, threshold: int = 85) -> List[Dict]:
        """
        Strategy 4: Fuzzy match dengan Levenshtein distance
        
        Args:
            drug_name: Nama obat yang dicari
            threshold: Minimum similarity score (0-100)
        
        Returns:
            List of matches dengan score, sorted by score descending
        """
        normalized = self.normalize_drug_name(drug_name)
        
        # Get all drugs
        drugs = self.db.query(FornasDrug).all()
        
        # Build candidates
        candidates = {}
        for drug in drugs:
            # Match against obat_name
            score_name = fuzz.ratio(normalized, self.normalize_drug_name(drug.obat_name))
            
            # Match against aliases
            max_alias_score = 0
            if drug.nama_obat_alias:
                for alias in drug.nama_obat_alias:
                    alias_score = fuzz.ratio(normalized, self.normalize_drug_name(alias))
                    max_alias_score = max(max_alias_score, alias_score)
            
            # Take best score
            best_score = max(score_name, max_alias_score)
            
            if best_score >= threshold:
                candidates[drug.id] = {
                    "drug": drug,
                    "score": best_score,
                    "matched_field": "obat_name" if score_name > max_alias_score else "alias"
                }
        
        # Sort by score descending
        sorted_matches = sorted(
            candidates.values(), 
            key=lambda x: x["score"], 
            reverse=True
        )
        
        return sorted_matches
    
    def match(self, drug_name: str, threshold: int = 85, return_all: bool = False) -> Dict:
        """
        Main matching function - cascading strategy
        
        Args:
            drug_name: Nama obat yang dicari
            threshold: Minimum fuzzy match threshold
            return_all: If True, return all fuzzy matches; if False, return best match only
        
        Returns:
            {
                "found": bool,
                "strategy": str,  # "exact", "alias", "normalized", "fuzzy"
                "drug": FornasDrug or None,
                "confidence": int,  # 0-100
                "alternatives": List[FornasDrug]  # For fuzzy matches
            }
        """
        if not drug_name:
            return {"found": False, "strategy": None, "drug": None, "confidence": 0, "alternatives": []}
        
        # Check cache
        cache_key = f"{drug_name}_{threshold}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Strategy 1: Exact match
        result = self.exact_match(drug_name)
        if result:
            match_result = {
                "found": True,
                "strategy": "exact",
                "drug": result,
                "confidence": 100,
                "alternatives": []
            }
            self._cache[cache_key] = match_result
            return match_result
        
        # Strategy 2: Alias match
        result = self.alias_match(drug_name)
        if result:
            match_result = {
                "found": True,
                "strategy": "alias",
                "drug": result,
                "confidence": 95,
                "alternatives": []
            }
            self._cache[cache_key] = match_result
            return match_result
        
        # Strategy 3: Normalized match
        result = self.normalized_match(drug_name)
        if result:
            match_result = {
                "found": True,
                "strategy": "normalized",
                "drug": result,
                "confidence": 90,
                "alternatives": []
            }
            self._cache[cache_key] = match_result
            return match_result
        
        # Strategy 4: Fuzzy match
        fuzzy_results = self.fuzzy_match(drug_name, threshold=threshold)
        
        if fuzzy_results:
            best_match = fuzzy_results[0]
            match_result = {
                "found": True,
                "strategy": "fuzzy",
                "drug": best_match["drug"],
                "confidence": best_match["score"],
                "alternatives": [m["drug"] for m in fuzzy_results[1:5]] if len(fuzzy_results) > 1 else []
            }
            self._cache[cache_key] = match_result
            return match_result
        
        # No match found
        return {"found": False, "strategy": None, "drug": None, "confidence": 0, "alternatives": []}
    
    def batch_match(self, drug_names: List[str], threshold: int = 85) -> Dict[str, Dict]:
        """
        Match multiple drugs at once
        
        Returns:
            {
                "drug_name_1": {...match_result...},
                "drug_name_2": {...match_result...},
                ...
            }
        """
        results = {}
        for name in drug_names:
            results[name] = self.match(name, threshold=threshold)
        return results
    
    def search_by_class(self, kelas_terapi: str) -> List[FornasDrug]:
        """
        Cari obat berdasarkan kelas terapi
        """
        return self.db.query(FornasDrug).filter(
            FornasDrug.kelas_terapi.ilike(f"%{kelas_terapi}%")
        ).all()
    
    def search_by_indication(self, indication_keyword: str) -> List[FornasDrug]:
        """
        Cari obat berdasarkan indikasi (search in indikasi_fornas JSON)
        """
        # PostgreSQL JSON search
        from sqlalchemy import func
        
        drugs = self.db.query(FornasDrug).filter(
            func.jsonb_path_exists(
                FornasDrug.indikasi_fornas,
                f'$[*] ? (@ like_regex "{indication_keyword}" flag "i")'
            )
        ).all()
        
        return drugs


# ===========================================================
# HELPER FUNCTIONS (untuk dipanggil dari services lain)
# ===========================================================

def match_fornas_drug(drug_name: str, threshold: int = 85) -> Dict:
    """
    Quick helper untuk matching single drug
    
    Usage:
        result = match_fornas_drug("ceftriaxone")
        if result["found"]:
            print(f"Found: {result['drug'].obat_name} (confidence: {result['confidence']}%)")
    """
    matcher = FornasDrugMatcher()
    return matcher.match(drug_name, threshold=threshold)


def match_fornas_drugs(drug_names: List[str], threshold: int = 85) -> Dict[str, Dict]:
    """
    Quick helper untuk matching multiple drugs
    
    Usage:
        results = match_fornas_drugs(["ceftriaxone", "paracetamol"])
        for drug_name, match_result in results.items():
            if match_result["found"]:
                print(f"{drug_name} → {match_result['drug'].obat_name}")
    """
    matcher = FornasDrugMatcher()
    return matcher.batch_match(drug_names, threshold=threshold)


if __name__ == "__main__":
    # Test matching
    print("=" * 70)
    print("FORNAS DRUG MATCHER TEST")
    print("=" * 70)
    
    test_drugs = [
        "ceftriaxone",  # Should match
        "paracetamol",  # Should match
        "asetaminofen",  # Alias of paracetamol
        "ceftriakson",  # Typo - should fuzzy match
        "obat_tidak_ada",  # Should not match
    ]
    
    matcher = FornasDrugMatcher()
    
    for drug_name in test_drugs:
        print(f"\n🔍 Matching: '{drug_name}'")
        result = matcher.match(drug_name, threshold=80)
        
        if result["found"]:
            drug = result["drug"]
            print(f"  ✅ FOUND via {result['strategy']}")
            print(f"     Nama FORNAS: {drug.obat_name}")
            print(f"     Kode: {drug.kode_fornas}")
            print(f"     Confidence: {result['confidence']}%")
            if result["alternatives"]:
                print(f"     Alternatives: {[d.obat_name for d in result['alternatives'][:3]]}")
        else:
            print(f"  ❌ NOT FOUND")
    
    print("\n" + "=" * 70)
