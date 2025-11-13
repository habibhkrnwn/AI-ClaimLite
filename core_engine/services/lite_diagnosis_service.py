"""
LITE Diagnosis Service - Simplified & Fast

Optimized for speed: Minimal AI calls, focus on essential data only.
Replaces heavy analyze_diagnosis_service for Lite mode.

Author: AI Assistant  
Date: 2025-11-13
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
logger = logging.getLogger(__name__)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class LiteDiagnosisAnalyzer:
    """
    Fast diagnosis analyzer for Lite mode
    
    Single AI call to get essential diagnosis info:
    - ICD-10 code
    - Basic clinical justification
    - Severity level
    
    NO multiple AI calls for each field like original service!
    """
    
    def __init__(self):
        self.model = "gpt-4o-mini"
        self._icd10_cache = {}
    
    def analyze(
        self,
        diagnosis_name: str,
        tindakan_list: List[str] = None,
        obat_list: List[str] = None
    ) -> Dict[str, Any]:
        """
        Fast single-call diagnosis analysis
        
        Args:
            diagnosis_name: Medical diagnosis (already translated if Indonesian)
            tindakan_list: List of procedures (optional)
            obat_list: List of medications (optional)
        
        Returns:
            {
                "icd10": {"kode_icd": "J18.9", "nama": "Pneumonia"},
                "severity": "sedang",
                "justifikasi_klinis": "...",
                "tingkat_faskes": "RS Tipe B"
            }
        """
        logger.info(f"[LITE_DIAGNOSIS] Analyzing: {diagnosis_name}")
        
        # Check cache first
        cache_key = diagnosis_name.lower().strip()
        if cache_key in self._icd10_cache:
            logger.info(f"[LITE_DIAGNOSIS] Cache hit for '{diagnosis_name}'")
            return self._icd10_cache[cache_key]
        
        # Build context
        context_parts = [f"Diagnosis: {diagnosis_name}"]
        if tindakan_list:
            context_parts.append(f"Tindakan: {', '.join(tindakan_list)}")
        if obat_list:
            context_parts.append(f"Obat: {', '.join(obat_list)}")
        
        context = "\n".join(context_parts)
        
        # Single AI call for essential info
        try:
            result = self._call_ai_analysis(context)
            
            # Cache the result
            self._icd10_cache[cache_key] = result
            
            logger.info(f"[LITE_DIAGNOSIS] ✓ Analysis complete: ICD-10 {result['icd10']['kode_icd']}")
            return result
            
        except Exception as e:
            logger.error(f"[LITE_DIAGNOSIS] ❌ Analysis failed: {e}")
            # Fallback to minimal data
            return self._get_fallback_result(diagnosis_name)
    
    def _call_ai_analysis(self, context: str) -> Dict[str, Any]:
        """Single AI call to get essential diagnosis data"""
        
        prompt = f"""Analisis diagnosis berikut dan berikan informasi ESENSIAL dalam format JSON:

KONTEKS:
{context}

TUGAS:
Berikan HANYA informasi penting berikut:

1. ICD-10 code (kode diagnosis standar WHO/ICD-10-CM)
   - Pilih kode PALING SPESIFIK yang sesuai dengan diagnosis
   - Hindari kode "unspecified" (.9) jika ada kode yang lebih spesifik
   - Contoh: "human metapneumovirus pneumonia" → J12.3 (BUKAN J18.9)
   - Contoh: "viral pneumonia" → J12.9 (BUKAN J18.9)
   - Contoh: "bacterial pneumonia" → J15.9 (BUKAN J18.9)

2. Severity level (ringan/sedang/berat)
3. Justifikasi klinis singkat (1-2 kalimat)
4. Level faskes yang sesuai (Puskesmas/RS Tipe D/C/B/A)

OUTPUT FORMAT (JSON):
{{
  "icd10": {{
    "kode_icd": "J12.3",
    "nama": "Human metapneumovirus pneumonia"
  }},
  "severity": "sedang",
  "justifikasi_klinis": "Infeksi saluran napas bawah viral yang memerlukan antibiotik dan monitoring ketat.",
  "tingkat_faskes": "RS Tipe B",
  "lama_rawat_estimasi": "5-7 hari"
}}

PENTING TENTANG ICD-10:
- Gunakan ICD-10-CM 2024 terbaru
- Pilih kode MOST SPECIFIC (4-5 digit) bukan generic (.9)
- J12.x = Viral pneumonia (specific virus)
- J13 = Streptococcus pneumoniae
- J14 = Haemophilus influenzae
- J15.x = Bacterial pneumonia (specific bacteria)
- J18.9 = HANYA jika tidak ada informasi virus/bakteri sama sekali
- Severity: ringan/sedang/berat berdasarkan kondisi klinis
- Tingkat faskes: Puskesmas (ringan), RS Tipe D/C (sedang), RS Tipe B/A (berat/kompleks)
- Jawab SINGKAT, padat, dan informatif

Contoh spesifik diagnosis → ICD-10:
- "viral pneumonia" → J12.9
- "human metapneumovirus pneumonia" → J12.3
- "RSV pneumonia" / "respiratory syncytial virus pneumonia" → J12.1
- "adenoviral pneumonia" → J12.0
- "parainfluenza virus pneumonia" → J12.2
- "bacterial pneumonia" → J15.9
- "pneumococcal pneumonia" / "streptococcus pneumoniae" → J13
- "haemophilus influenzae" → J14
- "klebsiella pneumonia" → J15.0
- "pseudomonas pneumonia" → J15.1
- "staphylococcus pneumonia" → J15.2
- "mycoplasma pneumonia" → J15.7
- "chlamydial pneumonia" → J16.0
- "pneumonia" (tanpa detail virus/bakteri) → J18.9
- "human pneumonia" (ambiguous, assume unspecified) → J18.9"""

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Anda adalah AI medical coder yang ahli dalam ICD-10-CM coding. Prioritaskan kode SPESIFIK daripada kode 'unspecified'. Berikan jawaban akurat dan ringkas."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Very low for consistent ICD-10 coding
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Validate and normalize
        if "icd10" not in result or "kode_icd" not in result["icd10"]:
            raise ValueError("Invalid AI response: missing ICD-10 code")
        
        # Add default values if missing
        result.setdefault("severity", "sedang")
        result.setdefault("justifikasi_klinis", "Diagnosis memerlukan penanganan medis sesuai standar.")
        result.setdefault("tingkat_faskes", "RS Tipe C")
        result.setdefault("lama_rawat_estimasi", "3-5 hari")
        
        return result
    
    def _get_fallback_result(self, diagnosis_name: str) -> Dict[str, Any]:
        """Fallback when AI call fails"""
        return {
            "icd10": {
                "kode_icd": "-",
                "nama": diagnosis_name
            },
            "severity": "sedang",
            "justifikasi_klinis": "Memerlukan evaluasi medis lebih lanjut.",
            "tingkat_faskes": "RS Tipe C",
            "lama_rawat_estimasi": "3-5 hari"
        }


# Global singleton
_analyzer_instance = None

def get_lite_analyzer() -> LiteDiagnosisAnalyzer:
    """Get or create singleton analyzer"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = LiteDiagnosisAnalyzer()
    return _analyzer_instance


def analyze_diagnosis_lite(
    diagnosis_name: str,
    tindakan_list: List[str] = None,
    obat_list: List[str] = None
) -> Dict[str, Any]:
    """
    Fast diagnosis analysis for Lite mode
    
    Usage:
        result = analyze_diagnosis_lite(
            diagnosis_name="Pneumonia",
            tindakan_list=["Rontgen Thorax"],
            obat_list=["Ceftriaxone"]
        )
        
        # Returns ICD-10, severity, justification in SINGLE AI call
    """
    analyzer = get_lite_analyzer()
    return analyzer.analyze(diagnosis_name, tindakan_list, obat_list)


# Testing
if __name__ == "__main__":
    print("=" * 80)
    print("LITE DIAGNOSIS ANALYZER TEST")
    print("=" * 80)
    
    import time
    
    test_cases = [
        {
            "diagnosis": "Pneumonia",
            "tindakan": ["Rontgen Thorax", "Pemeriksaan Darah Lengkap"],
            "obat": ["Ceftriaxone", "Paracetamol"]
        },
        {
            "diagnosis": "Diabetes Mellitus Type 2",
            "tindakan": ["Cek Gula Darah"],
            "obat": ["Metformin", "Glimepiride"]
        },
        {
            "diagnosis": "Hipertensi",
            "tindakan": ["Pemeriksaan Tekanan Darah"],
            "obat": ["Amlodipine"]
        }
    ]
    
    total_time = 0
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {case['diagnosis']}")
        print("-" * 80)
        
        start = time.time()
        result = analyze_diagnosis_lite(
            diagnosis_name=case["diagnosis"],
            tindakan_list=case["tindakan"],
            obat_list=case["obat"]
        )
        elapsed = time.time() - start
        total_time += elapsed
        
        print(f"⏱️  Time: {elapsed:.2f}s")
        print(f"📊 ICD-10: {result['icd10']['kode_icd']} - {result['icd10']['nama']}")
        print(f"🔥 Severity: {result['severity']}")
        print(f"🏥 Faskes: {result['tingkat_faskes']}")
        print(f"💡 Justifikasi: {result['justifikasi_klinis']}")
    
    print("\n" + "=" * 80)
    print(f"✅ Total time: {total_time:.2f}s")
    print(f"⚡ Average: {total_time/len(test_cases):.2f}s per diagnosis")
    print(f"🎯 Expected: ~2-3s per diagnosis (vs 60-90s with original service)")
    print("=" * 80)
