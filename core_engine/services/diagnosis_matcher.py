"""
Shared Diagnosis Matching Utilities
Digunakan oleh PNPK Summary Service dan Dokumen Wajib Service
untuk memastikan consistency dalam matching diagnosis name

Author: AI-CLAIM Team
Date: 2025-11-21
"""

import re
import logging
from typing import List, Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class DiagnosisMatcher:
    """Shared diagnosis matching utilities"""
    
    # Common medical modifiers yang bisa dihilangkan
    STOP_WORDS = {
        'unspecified', 'organism', 'not', 'elsewhere', 'classified',
        'with', 'without', 'due', 'to', 'other', 'nos', 'specified',
        'type', 'associated', 'related', 'induced', 'secondary',
        'acute', 'chronic', 'primary', 'recurrent'
    }
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text for matching
        - Lowercase
        - Remove extra spaces
        - Trim
        """
        if not text:
            return ""
        
        normalized = text.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    @staticmethod
    def extract_base_diagnosis(diagnosis: str) -> str:
        """
        Extract base diagnosis name (remove modifiers and specifics)
        
        Examples:
        - "Pneumonia, unspecified organism" → "pneumonia"
        - "Bacterial pneumonia, not elsewhere classified" → "bacterial pneumonia"
        - "Hospital-Acquired Pneumonia (HAP)" → "hospital-acquired pneumonia"
        - "Viral pneumonia, unspecified" → "viral pneumonia"
        
        Args:
            diagnosis: Full diagnosis name
            
        Returns:
            Base diagnosis name
        """
        # Remove content in parentheses (e.g., "(HAP)")
        base = re.sub(r'\([^)]*\)', '', diagnosis)
        
        # Remove comma and everything after it (common pattern in ICD-10)
        base = base.split(',')[0].strip()
        
        # Normalize
        return DiagnosisMatcher.normalize_text(base)
    
    @staticmethod
    def extract_keywords(diagnosis: str) -> List[str]:
        """
        Extract medical keywords from diagnosis
        
        Examples:
        - "Pneumonia, unspecified organism" → ["pneumonia"]
        - "Bacterial pneumonia, not elsewhere classified" → ["bacterial", "pneumonia"]
        - "Type 2 diabetes mellitus" → ["diabetes", "mellitus"]
        
        Args:
            diagnosis: Diagnosis name
            
        Returns:
            List of keywords (filtered, no stop words)
        """
        # Clean text
        cleaned = diagnosis.lower()
        
        # Remove punctuation
        cleaned = re.sub(r'[,;()\[\].:]', ' ', cleaned)
        
        # Split into words
        words = cleaned.split()
        
        # Filter stop words and short words
        keywords = [
            w for w in words 
            if w not in DiagnosisMatcher.STOP_WORDS and len(w) > 2
        ]
        
        return keywords
    
    @staticmethod
    def calculate_similarity(str1: str, str2: str) -> float:
        """
        Calculate similarity score between two strings
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score (0.0 - 1.0)
        """
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    @staticmethod
    def match_diagnosis(
        input_diagnosis: str,
        available_diagnoses: List[str],
        min_confidence: float = 0.6
    ) -> Optional[Tuple[str, float, str]]:
        """
        Match input diagnosis with available diagnoses
        Returns best match with confidence score and match method
        
        Matching Strategy (in order):
        1. Exact match (100%)
        2. Base diagnosis exact match (95%)
        3. Contains match (85%)
        4. Keyword match (70-80%)
        5. Fuzzy match (60-90%)
        
        Args:
            input_diagnosis: Input diagnosis name
            available_diagnoses: List of available diagnosis names in database
            min_confidence: Minimum confidence threshold
            
        Returns:
            Tuple of (matched_diagnosis, confidence, match_method) or None
        """
        if not input_diagnosis or not available_diagnoses:
            return None
        
        logger.info(f"[DIAGNOSIS_MATCHER] Matching '{input_diagnosis}' against {len(available_diagnoses)} diagnoses")
        
        input_normalized = DiagnosisMatcher.normalize_text(input_diagnosis)
        input_base = DiagnosisMatcher.extract_base_diagnosis(input_diagnosis)
        input_keywords = DiagnosisMatcher.extract_keywords(input_diagnosis)
        
        best_match = None
        best_score = 0.0
        best_method = ""
        
        for db_diagnosis in available_diagnoses:
            db_normalized = DiagnosisMatcher.normalize_text(db_diagnosis)
            db_base = DiagnosisMatcher.extract_base_diagnosis(db_diagnosis)
            db_keywords = DiagnosisMatcher.extract_keywords(db_diagnosis)
            
            # Strategy 1: Exact match
            if input_normalized == db_normalized:
                logger.info(f"[MATCH] Exact match: '{db_diagnosis}' (100%)")
                return (db_diagnosis, 1.0, "exact")
            
            # Strategy 2: Base diagnosis exact match
            if input_base == db_base and input_base:
                score = 0.95
                if score > best_score:
                    best_match = db_diagnosis
                    best_score = score
                    best_method = "base_exact"
            
            # Strategy 3: Contains match
            if input_normalized in db_normalized or db_normalized in input_normalized:
                score = 0.85
                if score > best_score:
                    best_match = db_diagnosis
                    best_score = score
                    best_method = "contains"
            
            # Strategy 4: Keyword match (IMPORTANT for ICD-10!)
            if input_keywords and db_keywords:
                matched_keywords = []
                for input_kw in input_keywords:
                    for db_kw in db_keywords:
                        # Check exact or substring match
                        if input_kw == db_kw:
                            matched_keywords.append((input_kw, db_kw, "exact"))
                        elif input_kw in db_kw or db_kw in input_kw:
                            matched_keywords.append((input_kw, db_kw, "partial"))
                
                if matched_keywords:
                    # Calculate keyword match score
                    # More matched keywords = higher score
                    match_ratio = len(matched_keywords) / max(len(input_keywords), len(db_keywords))
                    keyword_score = 0.65 + (match_ratio * 0.25)  # 65-90%
                    
                    if keyword_score > best_score:
                        best_match = db_diagnosis
                        best_score = keyword_score
                        best_method = f"keyword_match ({len(matched_keywords)} keywords)"
                        logger.debug(f"[MATCH] Keyword match: '{db_diagnosis}' - {matched_keywords} ({keyword_score:.2%})")
            
            # Strategy 5: Fuzzy match
            similarity = DiagnosisMatcher.calculate_similarity(input_normalized, db_normalized)
            if similarity >= 0.6:
                fuzzy_score = similarity * 0.9  # Scale down fuzzy scores
                if fuzzy_score > best_score:
                    best_match = db_diagnosis
                    best_score = fuzzy_score
                    best_method = "fuzzy"
        
        # Return best match if above threshold
        if best_match and best_score >= min_confidence:
            logger.info(f"[MATCH] Best match: '{best_match}' ({best_score:.2%}, method: {best_method})")
            return (best_match, best_score, best_method)
        
        logger.warning(f"[MATCH] No sufficient match found for '{input_diagnosis}' (best score: {best_score:.2%})")
        return None


# Convenience functions
def match_diagnosis(
    input_diagnosis: str,
    available_diagnoses: List[str],
    min_confidence: float = 0.6
) -> Optional[Tuple[str, float, str]]:
    """
    Quick access to diagnosis matching
    
    Returns:
        Tuple of (matched_diagnosis, confidence, match_method) or None
    """
    return DiagnosisMatcher.match_diagnosis(input_diagnosis, available_diagnoses, min_confidence)


def extract_base_diagnosis(diagnosis: str) -> str:
    """Quick access to extract base diagnosis"""
    return DiagnosisMatcher.extract_base_diagnosis(diagnosis)


def extract_keywords(diagnosis: str) -> List[str]:
    """Quick access to extract keywords"""
    return DiagnosisMatcher.extract_keywords(diagnosis)
