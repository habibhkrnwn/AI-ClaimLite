"""
PNPK Summary Service
Handles retrieval and intelligent matching of PNPK clinical pathway summaries
"""

import re
import time
import logging
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
import asyncpg

# Import shared diagnosis matcher
from services.diagnosis_matcher import DiagnosisMatcher

# Setup logging
logger = logging.getLogger(__name__)


class PNPKSummaryService:
    """Service for managing PNPK (Pedoman Nasional Praktik Klinik) summaries"""
    
    def __init__(self, db_pool, cache_ttl: int = 3600):
        """
        Initialize PNPK Summary Service
        
        Args:
            db_pool: AsyncPG database connection pool
            cache_ttl: Cache time-to-live in seconds (default: 3600 = 1 hour)
        """
        self.db_pool = db_pool
        self.cache_ttl = cache_ttl
        
        # Cache storage: {cache_key: (timestamp, data)}
        self._cache = {}
        
        logger.info(f"PNPKSummaryService initialized with cache_ttl={cache_ttl}s")
    
    def _get_cache(self, cache_key: str) -> Optional[any]:
        """
        Get data from cache if exists and not expired
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached data or None if expired/not found
        """
        if cache_key in self._cache:
            timestamp, data = self._cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Cache HIT: {cache_key}")
                return data
            else:
                # Cache expired, remove it
                logger.debug(f"Cache EXPIRED: {cache_key}")
                del self._cache[cache_key]
        
        logger.debug(f"Cache MISS: {cache_key}")
        return None
    
    def _set_cache(self, cache_key: str, data: any) -> None:
        """
        Store data in cache with current timestamp
        
        Args:
            cache_key: Cache key
            data: Data to cache
        """
        self._cache[cache_key] = (time.time(), data)
        logger.debug(f"Cache SET: {cache_key}")
    
    def clear_cache(self) -> int:
        """
        Clear all cached data
        
        Returns:
            Number of cache entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared: {count} entries removed")
        return count
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns:
            Dict with cache stats
        """
        total_entries = len(self._cache)
        expired_entries = 0
        current_time = time.time()
        
        for timestamp, _ in self._cache.values():
            if current_time - timestamp >= self.cache_ttl:
                expired_entries += 1
        
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "cache_ttl": self.cache_ttl
        }
    
    @staticmethod
    def normalize_diagnosis_name(name: str) -> str:
        """
        Normalize diagnosis name for matching
        - Convert to lowercase
        - Remove extra spaces
        - Remove punctuation (except hyphen)
        """
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower().strip()
        
        # Remove multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    @staticmethod
    def extract_base_name(name: str) -> str:
        """
        Extract base diagnosis name without abbreviations or aliases in parentheses
        Example: 
        - "Pneumonia" -> "pneumonia"
        - "Hospital-Acquired Pneumonia (HAP)" -> "hospital-acquired pneumonia"
        - "Penyakit Ginjal Kronik (PGK)" -> "penyakit ginjal kronik"
        """
        # Remove content in parentheses
        base_name = re.sub(r'\([^)]*\)', '', name)
        
        # Normalize
        return PNPKSummaryService.normalize_diagnosis_name(base_name)
    
    @staticmethod
    def extract_abbreviation(name: str) -> Optional[str]:
        """
        Extract abbreviation from parentheses
        Example: "Hospital-Acquired Pneumonia (HAP)" -> "hap"
        """
        match = re.search(r'\(([^)]+)\)', name)
        if match:
            return PNPKSummaryService.normalize_diagnosis_name(match.group(1))
        return None
    
    @staticmethod
    def calculate_similarity(str1: str, str2: str) -> float:
        """
        Calculate similarity score between two strings using SequenceMatcher
        Returns: float between 0 and 1 (1 = identical)
        """
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    @staticmethod
    def extract_medical_keywords(diagnosis: str) -> List[str]:
        """
        Extract key medical terms from diagnosis name
        Example: "Pneumonia, unspecified organism" -> ["pneumonia"]
        Example: "Bacterial pneumonia, not elsewhere classified" -> ["bacterial", "pneumonia"]
        """
        # Remove common medical modifiers
        stop_words = {
            'unspecified', 'organism', 'not', 'elsewhere', 'classified',
            'with', 'without', 'due', 'to', 'other', 'nos', 'specified',
            'type', 'associated', 'related', 'induced', 'secondary'
        }
        
        # Clean and tokenize
        cleaned = diagnosis.lower()
        # Remove punctuation
        cleaned = re.sub(r'[,;()\[\]]', ' ', cleaned)
        # Split into words
        words = cleaned.split()
        # Filter out stop words and short words
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords
    
    async def get_all_diagnoses(self) -> List[Dict]:
        """
        Get list of all available diagnoses in PNPK database
        
        Returns:
            List of dicts with diagnosis_name and stage_count
        """
        # Check cache first
        cache_key = "all_diagnoses"
        cached_data = self._get_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        logger.info("Fetching all diagnoses from database")
        
        query = """
        SELECT 
            diagnosis_name,
            COUNT(*) as stage_count
        FROM pnpk_summary
        GROUP BY diagnosis_name
        ORDER BY diagnosis_name
        """
        
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query)
            
            result = [
                {
                    "diagnosis_name": row["diagnosis_name"],
                    "stage_count": row["stage_count"]
                }
                for row in rows
            ]
            
            # Cache the result
            self._set_cache(cache_key, result)
            
            logger.info(f"Found {len(result)} diagnoses in database")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching all diagnoses: {e}")
            raise
    
    async def search_diagnoses(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        Search diagnoses by keyword with intelligent matching
        
        Args:
            keyword: Search keyword
            limit: Maximum number of results
            
        Returns:
            List of matched diagnoses with similarity scores
        """
        if not keyword or len(keyword.strip()) < 2:
            logger.warning(f"Search keyword too short: '{keyword}'")
            return []
        
        logger.info(f"Searching diagnoses for keyword: '{keyword}' (limit={limit})")
        
        normalized_keyword = self.normalize_diagnosis_name(keyword)
        base_keyword = self.extract_base_name(keyword)
        
        # Get all diagnoses (from cache if possible)
        all_diagnoses = await self.get_all_diagnoses()
        
        # Score each diagnosis
        scored_results = []
        for diag in all_diagnoses:
            name = diag["diagnosis_name"]
            normalized_name = self.normalize_diagnosis_name(name)
            base_name = self.extract_base_name(name)
            abbreviation = self.extract_abbreviation(name)
            
            # Calculate scores for different matching strategies
            scores = []
            
            # 1. Exact match (highest priority)
            if normalized_keyword == normalized_name:
                scores.append(1.0)
            
            # 2. Base name exact match
            if base_keyword == base_name:
                scores.append(0.95)
            
            # 3. Abbreviation match
            if abbreviation and normalized_keyword == abbreviation:
                scores.append(0.9)
            
            # 4. Contains match
            if normalized_keyword in normalized_name or normalized_name in normalized_keyword:
                scores.append(0.85)
            
            # 5. Base name contains match
            if base_keyword in base_name or base_name in base_keyword:
                scores.append(0.8)
            
            # 6. Fuzzy similarity (word-level)
            similarity = self.calculate_similarity(normalized_keyword, normalized_name)
            if similarity >= 0.6:
                scores.append(similarity * 0.7)
            
            # 7. Base name fuzzy similarity
            base_similarity = self.calculate_similarity(base_keyword, base_name)
            if base_similarity >= 0.6:
                scores.append(base_similarity * 0.65)
            
            # Take the highest score
            if scores:
                max_score = max(scores)
                scored_results.append({
                    "diagnosis_name": name,
                    "stage_count": diag["stage_count"],
                    "match_score": round(max_score, 3),
                    "matched_by": "exact" if max_score >= 0.95 else "partial" if max_score >= 0.8 else "fuzzy"
                })
        
        # Sort by score (descending) and take top results
        scored_results.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Filter by minimum score threshold (0.6)
        filtered_results = [r for r in scored_results if r["match_score"] >= 0.6]
        
        logger.info(f"Search completed: {len(filtered_results)} matches found for '{keyword}'")
        if filtered_results:
            logger.debug(f"Top match: {filtered_results[0]['diagnosis_name']} (score: {filtered_results[0]['match_score']})")
        
        return filtered_results[:limit]
    
    async def find_best_match(self, input_diagnosis: str) -> Optional[Dict]:
        """
        Find the best matching diagnosis from database
        Uses shared DiagnosisMatcher for consistency with Dokumen Wajib
        
        Args:
            input_diagnosis: User input diagnosis name (can be ICD-10 name)
            
        Returns:
            Best match dict with diagnosis_name and confidence score, or None
        """
        logger.info(f"[PNPK] Finding best match for: '{input_diagnosis}'")
        
        # Get all available diagnoses
        all_diagnoses_data = await self.get_all_diagnoses()
        available_diagnoses = [d["diagnosis_name"] for d in all_diagnoses_data]
        
        # Use shared matcher (min confidence: 0.6)
        match_result = DiagnosisMatcher.match_diagnosis(
            input_diagnosis,
            available_diagnoses,
            min_confidence=0.6
        )
        
        if match_result:
            matched_name, confidence, method = match_result
            return {
                "diagnosis_name": matched_name,
                "confidence": confidence,
                "matched_by": method
            }
        
        logger.warning(f"[PNPK] No match found for: '{input_diagnosis}'")
        return None
    
    async def get_pnpk_summary(
        self, 
        diagnosis_name: str, 
        auto_match: bool = True
    ) -> Optional[Dict]:
        """
        Get PNPK summary for a specific diagnosis
        
        Args:
            diagnosis_name: Diagnosis name (can be partial or with variations)
            auto_match: If True, attempt intelligent matching
            
        Returns:
            Dict containing diagnosis info and ordered stages, or None if not found
        """
        logger.info(f"Getting PNPK summary for: '{diagnosis_name}' (auto_match={auto_match})")
        
        # Check cache first
        cache_key = f"pnpk_summary_{diagnosis_name}_{auto_match}"
        cached_data = self._get_cache(cache_key)
        if cached_data is not None:
            logger.info(f"Returning cached PNPK summary for: '{diagnosis_name}'")
            return cached_data
        
        matched_name = diagnosis_name
        match_info = None
        
        # Try intelligent matching if auto_match is enabled
        if auto_match:
            match_result = await self.find_best_match(diagnosis_name)
            if match_result:
                matched_name = match_result["diagnosis_name"]
                match_info = {
                    "original_input": diagnosis_name,
                    "matched_name": matched_name,
                    "confidence": match_result["confidence"],
                    "matched_by": match_result["matched_by"]
                }
                logger.info(f"Matched '{diagnosis_name}' to '{matched_name}' (confidence: {match_result['confidence']})")
            else:
                # No good match found
                logger.warning(f"No PNPK match found for: '{diagnosis_name}'")
                return None
        
        # Fetch stages for the matched diagnosis
        query = """
        SELECT 
            id,
            diagnosis_name,
            urutan,
            tahap,
            deskripsi
        FROM pnpk_summary
        WHERE diagnosis_name = $1
        ORDER BY urutan ASC
        """
        
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, matched_name)
            
            if not rows:
                logger.warning(f"No PNPK stages found for: '{matched_name}'")
                return None
            
            # Format response
            stages = [
                {
                    "id": row["id"],
                    "order": row["urutan"],
                    "stage_name": row["tahap"],
                    "description": row["deskripsi"]
                }
                for row in rows
            ]
            
            result = {
                "diagnosis": matched_name,
                "total_stages": len(stages),
                "stages": stages
            }
            
            # Include match info if intelligent matching was used
            if match_info:
                result["match_info"] = match_info
            
            # Cache the result
            self._set_cache(cache_key, result)
            
            logger.info(f"PNPK summary retrieved: '{matched_name}' with {len(stages)} stages")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching PNPK summary for '{matched_name}': {e}")
            raise
    
    async def get_stage_by_order(
        self, 
        diagnosis_name: str, 
        stage_order: int
    ) -> Optional[Dict]:
        """
        Get a specific stage by its order number
        
        Args:
            diagnosis_name: Diagnosis name
            stage_order: Stage order number (urutan)
            
        Returns:
            Stage details or None
        """
        logger.info(f"Getting stage {stage_order} for diagnosis: '{diagnosis_name}'")
        
        # First, find the best match for diagnosis
        match_result = await self.find_best_match(diagnosis_name)
        if not match_result:
            logger.warning(f"No diagnosis match found for: '{diagnosis_name}'")
            return None
        
        matched_name = match_result["diagnosis_name"]
        
        query = """
        SELECT 
            id,
            diagnosis_name,
            urutan,
            tahap,
            deskripsi
        FROM pnpk_summary
        WHERE diagnosis_name = $1 AND urutan = $2
        """
        
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(query, matched_name, stage_order)
            
            if not row:
                logger.warning(f"Stage {stage_order} not found for '{matched_name}'")
                return None
            
            result = {
                "id": row["id"],
                "diagnosis": row["diagnosis_name"],
                "order": row["urutan"],
                "stage_name": row["tahap"],
                "description": row["deskripsi"]
            }
            
            logger.info(f"Stage retrieved: '{matched_name}' - Stage {stage_order}: {row['tahap']}")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching stage {stage_order} for '{matched_name}': {e}")
            raise
    
    async def validate_diagnosis_exists(self, diagnosis_name: str) -> bool:
        """
        Check if a diagnosis exists in the PNPK database
        
        Args:
            diagnosis_name: Diagnosis name to check
            
        Returns:
            True if exists, False otherwise
        """
        logger.debug(f"Validating diagnosis exists: '{diagnosis_name}'")
        
        match_result = await self.find_best_match(diagnosis_name)
        exists = match_result is not None and match_result["confidence"] >= 0.8
        
        if exists:
            logger.info(f"Diagnosis validation PASSED: '{diagnosis_name}' -> '{match_result['diagnosis_name']}'")
        else:
            logger.info(f"Diagnosis validation FAILED: '{diagnosis_name}'")
        
        return exists
