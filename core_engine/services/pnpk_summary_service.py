"""
PNPK Summary Service
Handles retrieval and intelligent matching of PNPK clinical pathway summaries
"""

import re
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
import asyncpg


class PNPKSummaryService:
    """Service for managing PNPK (Pedoman Nasional Praktik Klinik) summaries"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
    
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
    
    async def get_all_diagnoses(self) -> List[Dict]:
        """
        Get list of all available diagnoses in PNPK database
        
        Returns:
            List of dicts with diagnosis_name and stage_count
        """
        query = """
        SELECT 
            diagnosis_name,
            COUNT(*) as stage_count
        FROM pnpk_summary
        GROUP BY diagnosis_name
        ORDER BY diagnosis_name
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query)
            
        return [
            {
                "diagnosis_name": row["diagnosis_name"],
                "stage_count": row["stage_count"]
            }
            for row in rows
        ]
    
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
            return []
        
        normalized_keyword = self.normalize_diagnosis_name(keyword)
        base_keyword = self.extract_base_name(keyword)
        
        # Get all diagnoses
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
        
        return filtered_results[:limit]
    
    async def find_best_match(self, input_diagnosis: str) -> Optional[Dict]:
        """
        Find the best matching diagnosis from database
        
        Args:
            input_diagnosis: User input diagnosis name
            
        Returns:
            Best match dict with diagnosis_name and confidence score, or None
        """
        results = await self.search_diagnoses(input_diagnosis, limit=1)
        
        if results and results[0]["match_score"] >= 0.7:
            return {
                "diagnosis_name": results[0]["diagnosis_name"],
                "confidence": results[0]["match_score"],
                "matched_by": results[0]["matched_by"]
            }
        
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
            else:
                # No good match found
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
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, matched_name)
        
        if not rows:
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
        
        return result
    
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
        # First, find the best match for diagnosis
        match_result = await self.find_best_match(diagnosis_name)
        if not match_result:
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
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, matched_name, stage_order)
        
        if not row:
            return None
        
        return {
            "id": row["id"],
            "diagnosis": row["diagnosis_name"],
            "order": row["urutan"],
            "stage_name": row["tahap"],
            "description": row["deskripsi"]
        }
    
    async def validate_diagnosis_exists(self, diagnosis_name: str) -> bool:
        """
        Check if a diagnosis exists in the PNPK database
        
        Args:
            diagnosis_name: Diagnosis name to check
            
        Returns:
            True if exists, False otherwise
        """
        match_result = await self.find_best_match(diagnosis_name)
        return match_result is not None and match_result["confidence"] >= 0.8
