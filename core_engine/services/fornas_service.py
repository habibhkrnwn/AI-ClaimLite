"""
FORNAS Service (Bridge for Lite Service)

Provide simple interface untuk FORNAS drug matching
Used by lite_service.py untuk backward compatibility

Author: AI Assistant
Date: 2025-11-11
"""

import sys
import os
from typing import List, Dict, Optional
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import existing matcher
from services.fornas_matcher import FornasDrugMatcher
from database_connection import SessionLocal
from models import FornasDrug


def match_multiple_obat(obat_list: List[str], threshold: int = 85) -> List[Dict]:
    """
    Match multiple drugs dengan FORNAS database
    
    Args:
        obat_list: List of drug names (e.g., ["Ceftriaxone 1g IV", "Paracetamol 500mg"])
        threshold: Fuzzy match threshold (default: 85)
    
    Returns:
        [
            {
                "input_name": "Ceftriaxone 1g IV",
                "nama_generik": "Ceftriaxone",
                "kode_fornas": "FORN-2023-001",
                "kelas_terapi": "Antibiotik – Sefalosporin",
                "sumber_regulasi": "FORNAS 2023",
                "level": "Level II",
                "found": True,
                "confidence": 100,
                "strategy": "exact"
            },
            ...
        ]
    """
    if not obat_list:
        return []
    
    matcher = FornasDrugMatcher()
    results = []
    
    for obat_name in obat_list:
        if not obat_name or obat_name.strip() == "":
            continue
        
        # Match dengan FORNAS DB (disable AI transliteration for speed)
        match_result = matcher.match(obat_name.strip(), threshold=threshold, use_ai_transliteration=False)
        
        if match_result["found"]:
            drug = match_result["drug"]
            
            # Format result - prefer the DB value for sumber_regulasi.
            # If DB value is missing or empty, return '-' to make it explicit that
            # no regulation source is available instead of inventing a concept string.
            sumber_db = drug.sumber_regulasi if getattr(drug, 'sumber_regulasi', None) else "-"

            results.append({
                "input_name": obat_name,
                "nama_generik": drug.obat_name,
                "kode_fornas": drug.kode_fornas,
                "kelas_terapi": drug.kelas_terapi or "Tidak tersedia",
                "sumber_regulasi": sumber_db,
                "level": _determine_fornas_level(drug),
                "found": True,
                "confidence": match_result["confidence"],
                "strategy": match_result["strategy"],
                "fornas_drug": drug  # Full object for advanced usage
            })
        else:
            # Drug not found in FORNAS
            results.append({
                "input_name": obat_name,
                "nama_generik": obat_name,
                "kode_fornas": None,
                "kelas_terapi": "Tidak ditemukan",
                "sumber_regulasi": None,
                "level": "Unknown",
                "found": False,
                "confidence": 0,
                "strategy": None,
                "fornas_drug": None
            })
    
    return results


def get_fornas_compliance_status(fornas_matched: List[Dict]) -> str:
    """
    Get compliance status summary dari hasil matching
    
    Args:
        fornas_matched: Result dari match_multiple_obat()
    
    Returns:
        "✅ Sesuai Fornas" | "⚠️ Perlu Justifikasi" | "❌ Non-Fornas" | "-"
    """
    if not fornas_matched:
        return "-"
    
    # Count status
    total = len(fornas_matched)
    found_count = sum(1 for m in fornas_matched if m.get("found", False))
    not_found_count = total - found_count
    
    # Determine overall status
    if not_found_count == 0:
        # Semua obat ditemukan di FORNAS
        return "✅ Sesuai Fornas"
    elif found_count > 0:
        # Sebagian ditemukan
        return "⚠️ Perlu Justifikasi"
    else:
        # Tidak ada yang ditemukan
        return "❌ Non-Fornas"


def _determine_fornas_level(drug: FornasDrug) -> str:
    """
    Determine FORNAS level based on facility flags
    
    Priority:
    - FPKTP (primary care) → Level I
    - FPKTL (advanced primary) → Level II
    - TP (hospital) → Level III
    - OEN → Special category
    """
    if not drug:
        return "Unknown"
    
    # Check OEN first (special category)
    if drug.oen:
        return "OEN"
    
    # Check facility levels
    if drug.fasilitas_fpktp:
        return "Level I (FPKTP)"
    elif drug.fasilitas_fpktl:
        return "Level II (FPKTL)"
    elif drug.fasilitas_tp:
        return "Level III (RS)"
    
    # Default
    return "Level III"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_fornas_drug_by_code(kode_fornas: str) -> Optional[FornasDrug]:
    """
    Get FORNAS drug by kode_fornas
    
    Args:
        kode_fornas: FORNAS code (e.g., "FORN-2023-001")
    
    Returns:
        FornasDrug object or None
    """
    db = SessionLocal()
    try:
        drug = db.query(FornasDrug).filter(
            FornasDrug.kode_fornas == kode_fornas
        ).first()
        return drug
    finally:
        db.close()


def search_fornas_by_class(kelas_terapi: str, limit: int = 10) -> List[FornasDrug]:
    """
    Search FORNAS drugs by therapeutic class
    
    Args:
        kelas_terapi: Therapeutic class (e.g., "Antibiotik")
        limit: Max results
    
    Returns:
        List of FornasDrug objects
    """
    db = SessionLocal()
    try:
        drugs = db.query(FornasDrug).filter(
            FornasDrug.kelas_terapi.ilike(f"%{kelas_terapi}%")
        ).limit(limit).all()
        return drugs
    finally:
        db.close()


# ============================================================
# TESTING
# ============================================================
if __name__ == "__main__":
    print("=" * 70)
    print("FORNAS SERVICE TEST")
    print("=" * 70)
    
    # Test drug list
    test_drugs = [
        "Ceftriaxone 1g IV",
        "Paracetamol 500mg",
        "Amoxicillin 500mg",
        "Vitamin C 1000mg",  # Might not be in FORNAS
        "Unknown Drug XYZ"   # Should not match
    ]
    
    print(f"\n📋 Testing {len(test_drugs)} drugs:")
    for drug in test_drugs:
        print(f"   - {drug}")
    
    # Match drugs
    print("\n🔍 Matching with FORNAS database...")
    results = match_multiple_obat(test_drugs, threshold=80)
    
    print(f"\n📊 Results:")
    print(f"   Total drugs: {len(results)}")
    print(f"   Found in FORNAS: {sum(1 for r in results if r['found'])}")
    print(f"   Not found: {sum(1 for r in results if not r['found'])}")
    
    print("\n📋 Details:")
    for i, result in enumerate(results, 1):
        status = "✅" if result['found'] else "❌"
        print(f"\n   {i}. {status} {result['input_name']}")
        print(f"      Nama Generik: {result['nama_generik']}")
        print(f"      Kode FORNAS: {result['kode_fornas'] or 'N/A'}")
        print(f"      Kelas Terapi: {result['kelas_terapi']}")
        print(f"      Level: {result['level']}")
        print(f"      Confidence: {result['confidence']}%")
        if result['found']:
            print(f"      Strategy: {result['strategy']}")
    
    # Test compliance status
    compliance = get_fornas_compliance_status(results)
    print(f"\n🏥 Overall Compliance: {compliance}")
    
    print("\n" + "=" * 70)
