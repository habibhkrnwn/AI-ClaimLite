"""
Fast Diagnosis Translation Service

Provides instant Indonesian → Medical term translation without slow fuzzy matching.
Optimized for common diagnosis terms in Indonesian language.

Author: AI Assistant
Date: 2025-11-13
"""

import json
import os
import re
from typing import Optional, Dict
from pathlib import Path


class FastDiagnosisTranslator:
    """
    Fast lookup for common Indonesian diagnosis terms
    
    Hybrid approach:
    1. Try dictionary lookup (instant - 0.02ms)
    2. If not found, use AI translation (2-3s but more flexible)
    
    Usage:
        translator = FastDiagnosisTranslator()
        result = translator.translate("paru paru basah")
        # Returns: "pneumonia" (instant, no AI/DB call)
        
        result = translator.translate("radang paru paru kanan")
        # Returns: "pneumonia" (AI translates uncommon variation)
    """
    
    def __init__(self, use_ai_fallback: bool = True):
        self.mapping: Dict[str, str] = {}
        self.use_ai_fallback = use_ai_fallback
        self._ai_cache: Dict[str, str] = {}  # Cache AI translations
        self._load_mapping()
        
        # Initialize OpenAI client for AI fallback
        if self.use_ai_fallback:
            try:
                from openai import OpenAI
                import os
                api_key = os.getenv("OPENAI_API_KEY")
                self.ai_client = OpenAI(api_key=api_key) if api_key else None
            except:
                self.ai_client = None
                self.use_ai_fallback = False
    
    def _load_mapping(self):
        """Load diagnosis mapping from JSON file"""
        try:
            mapping_file = Path(__file__).parent.parent / "rules" / "diagnosis_indonesian_mapping.json"
            
            if mapping_file.exists():
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    self.mapping = json.load(f)
                print(f"[FAST_TRANSLATOR] Loaded {len(self.mapping)} diagnosis mappings")
            else:
                print(f"[FAST_TRANSLATOR] Warning: Mapping file not found at {mapping_file}")
                self.mapping = {}
        
        except Exception as e:
            print(f"[FAST_TRANSLATOR] Error loading mapping: {e}")
            self.mapping = {}
    
    def normalize(self, text: str) -> str:
        """
        Normalize diagnosis text for lookup
        
        Args:
            text: Raw diagnosis text
        
        Returns:
            Normalized text (lowercase, clean)
        """
        if not text:
            return ""
        
        # Lowercase
        normalized = text.lower().strip()
        
        # Replace common abbreviations/patterns
        replacements = {
            '2': ' ',           # paru2 → paru paru (digit 2 becomes space)
            '-': ' ',           # paru-paru → paru paru
            '_': ' ',           # paru_paru → paru paru
            '/': ' ',           # paru/paru → paru paru
            'yg': 'yang',       # yg → yang
            'dgn': 'dengan',    # dgn → dengan
            'utk': 'untuk',     # utk → untuk
            'pd': 'pada',       # pd → pada
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove common medical suffixes
        suffixes = [
            ' akut', ' kronik', ' kronis',
            ' berat', ' ringan', ' sedang',
            ' dengan komplikasi', ' tanpa komplikasi',
            ' primer', ' sekunder', ' tersier',
            ' tipe 1', ' tipe 2', ' tipe i', ' tipe ii',
            ' grade 1', ' grade 2', ' grade 3', ' grade 4',
            ' stage 1', ' stage 2', ' stage 3', ' stage 4',
            ' derajat 1', ' derajat 2', ' derajat 3', ' derajat 4'
        ]
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        
        return normalized
    
    def translate(self, diagnosis_text: str, use_ai_if_not_found: bool = True) -> Optional[str]:
        """
        Translate Indonesian diagnosis to medical term
        
        Hybrid approach:
        1. Try dictionary lookup (instant)
        2. If not found and AI enabled, use AI translation (2-3s)
        
        Args:
            diagnosis_text: Indonesian diagnosis (e.g., "paru paru basah", "radang paru paru")
            use_ai_if_not_found: Use AI if dictionary lookup fails (default: True)
        
        Returns:
            Medical term (e.g., "pneumonia") or None if not found
        
        Example:
            >>> translator.translate("paru paru basah")
            "pneumonia"  # Dictionary hit (0.02ms)
            
            >>> translator.translate("radang paru paru kanan")
            "pneumonia"  # AI translation (2-3s, then cached)
            
            >>> translator.translate("radang paru paru kanan")  # 2nd call
            "pneumonia"  # Cache hit (0.02ms)
        """
        if not diagnosis_text:
            return None
        
        # Normalize input
        normalized = self.normalize(diagnosis_text)
        
        # Step 1: Try direct dictionary lookup (O(1) - instant!)
        if normalized in self.mapping:
            print(f"[FAST_TRANSLATE] Dictionary hit: '{diagnosis_text}' → '{self.mapping[normalized]}'")
            return self.mapping[normalized]
        
        # Try without normalization (in case it's already medical term)
        original_lower = diagnosis_text.lower().strip()
        if original_lower in self.mapping:
            print(f"[FAST_TRANSLATE] Dictionary hit: '{diagnosis_text}' → '{self.mapping[original_lower]}'")
            return self.mapping[original_lower]
        
        # Step 2: AI fallback for uncommon variations
        if use_ai_if_not_found and self.use_ai_fallback and self.ai_client:
            # Check AI cache first
            cache_key = normalized or original_lower
            if cache_key in self._ai_cache:
                print(f"[FAST_TRANSLATE] AI cache hit: '{diagnosis_text}' → '{self._ai_cache[cache_key]}'")
                return self._ai_cache[cache_key]
            
            # Call AI for translation
            try:
                ai_result = self._ai_translate(diagnosis_text)
                if ai_result and ai_result.lower() != diagnosis_text.lower():
                    # Cache the AI result
                    self._ai_cache[cache_key] = ai_result
                    print(f"[FAST_TRANSLATE] AI translation: '{diagnosis_text}' → '{ai_result}'")
                    return ai_result
            except Exception as e:
                print(f"[FAST_TRANSLATE] AI translation failed: {e}")
        
        # Not found
        return None
    
    def _ai_translate(self, diagnosis_text: str) -> Optional[str]:
        """
        Use AI to translate uncommon Indonesian diagnosis variations
        
        Args:
            diagnosis_text: Indonesian diagnosis text
        
        Returns:
            English medical term or None
        """
        if not self.ai_client:
            return None
        
        try:
            response = self.ai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a medical translator. Translate Indonesian diagnosis terms "
                            "to standard English medical terms. Return ONLY the medical term, "
                            "nothing else. If unsure, return the closest standard term."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Translate this Indonesian diagnosis to English medical term:\n\n"
                            f"Indonesian: {diagnosis_text}\n\n"
                            f"Examples:\n"
                            f"- 'radang paru paru' → 'pneumonia'\n"
                            f"- 'kencing manis yang berat' → 'diabetes mellitus'\n"
                            f"- 'darah tinggi kronik' → 'hypertension'\n"
                            f"- 'sakit jantung' → 'heart disease'\n\n"
                            f"Return ONLY the English medical term:"
                        )
                    }
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            result = response.choices[0].message.content.strip().lower()
            
            # Clean up result (remove quotes, periods, etc.)
            result = result.strip('"\'.,;: ')
            
            return result if result else None
            
        except Exception as e:
            print(f"[FAST_TRANSLATE] AI error: {e}")
            return None
    
    def translate_with_fallback(self, diagnosis_text: str, fallback: str = None, use_ai: bool = True) -> str:
        """
        Translate with fallback to original text
        
        Args:
            diagnosis_text: Indonesian diagnosis
            fallback: Custom fallback (default: original text)
            use_ai: Use AI if dictionary lookup fails (default: True)
        
        Returns:
            Translated term or fallback
        """
        result = self.translate(diagnosis_text, use_ai_if_not_found=use_ai)
        
        if result:
            return result
        
        return fallback if fallback is not None else diagnosis_text
    
    def get_all_mappings(self) -> Dict[str, str]:
        """Get all available mappings"""
        return self.mapping.copy()
    
    def add_mapping(self, indonesian: str, medical: str):
        """
        Add new mapping at runtime
        
        Args:
            indonesian: Indonesian term
            medical: Medical term
        """
        normalized = self.normalize(indonesian)
        self.mapping[normalized] = medical.lower()
    
    def search(self, query: str, max_results: int = 5) -> list:
        """
        Search for similar terms (for autocomplete/suggestions)
        
        Args:
            query: Search query
            max_results: Maximum results to return
        
        Returns:
            List of (indonesian_term, medical_term) tuples
        """
        if not query:
            return []
        
        query_lower = query.lower()
        results = []
        
        for indo_term, medical_term in self.mapping.items():
            if query_lower in indo_term or query_lower in medical_term:
                results.append((indo_term, medical_term))
                
                if len(results) >= max_results:
                    break
        
        return results


# Global singleton instance
_translator_instance = None

def get_fast_translator() -> FastDiagnosisTranslator:
    """Get or create singleton translator instance"""
    global _translator_instance
    
    if _translator_instance is None:
        _translator_instance = FastDiagnosisTranslator()
    
    return _translator_instance


# Convenience functions
def fast_translate_diagnosis(text: str, use_ai: bool = True) -> Optional[str]:
    """
    Quick translation function
    
    Args:
        text: Diagnosis text (any Indonesian variation)
        use_ai: Use AI for uncommon variations (default: True)
    """
    return get_fast_translator().translate(text, use_ai_if_not_found=use_ai)


def fast_translate_with_fallback(text: str, use_ai: bool = True) -> str:
    """
    Quick translation with fallback to original
    
    Args:
        text: Diagnosis text
        use_ai: Use AI if dictionary miss (default: True)
    """
    return get_fast_translator().translate_with_fallback(text, use_ai=use_ai)


# Testing
if __name__ == "__main__":
    print("=" * 80)
    print("FAST DIAGNOSIS TRANSLATOR TEST - HYBRID MODE")
    print("=" * 80)
    
    translator = FastDiagnosisTranslator(use_ai_fallback=True)
    
    test_cases = [
        # Dictionary hits (instant)
        ("paru paru basah", "Dictionary"),
        ("paru2 basah", "Dictionary + normalization"),
        ("kencing manis", "Dictionary"),
        ("darah tinggi", "Dictionary"),
        
        # AI fallback (uncommon variations)
        ("radang paru paru", "AI fallback"),
        ("radang paru paru kanan", "AI fallback"),
        ("paru basah sebelah kiri", "AI fallback"),
        ("kencing manis yang berat", "AI fallback"),
        ("sakit gula", "Dictionary"),
        
        # Unknown
        ("unknown rare disease xyz", "Not found"),
    ]
    
    print(f"\n📋 Testing {len(test_cases)} cases:\n")
    
    import time
    total_time = 0
    
    for diagnosis, expected_method in test_cases:
        start = time.time()
        result = translator.translate(diagnosis, use_ai_if_not_found=True)
        elapsed = (time.time() - start) * 1000
        total_time += elapsed
        
        status = "✅" if result else "❌"
        print(f"{status} {diagnosis:35} → {result or 'NOT FOUND':30} ({elapsed:6.1f}ms)")
    
    print(f"\n⚡ Total time: {total_time:.0f}ms ({total_time/len(test_cases):.1f}ms average)")
    print(f"📊 Loaded mappings: {len(translator.get_all_mappings())}")
    print(f"🤖 AI fallback: {'Enabled' if translator.use_ai_fallback else 'Disabled'}")
    print("\n" + "=" * 80)
    print("� STRATEGY:")
    print("   1. Dictionary lookup first (0.02ms - instant)")
    print("   2. AI translation for uncommon variations (2-3s)")
    print("   3. AI results cached for future lookups (0.02ms)")
    print("=" * 80)
