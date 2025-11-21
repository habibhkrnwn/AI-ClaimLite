"""
INA-CBG Grouper Service

Service untuk memprediksi kode INA-CBG beserta tarifnya berdasarkan:
- ICD10 Primary & Secondary
- ICD9 Procedures
- Episode/Layanan (RI/RJ)
- Regional, Kelas RS, Tipe RS, Kelas BPJS

Menggunakan 5-level fallback strategy untuk akurasi maksimal.

Author: AI-ClaimLite
Date: 2025-11-18
"""

import json
from typing import List, Optional, Dict, Any
from sqlalchemy import text
from database_connection import get_db_session
import logging

# Setup logging
logger = logging.getLogger(__name__)


class InacbgGrouperService:
    """Service untuk INA-CBG grouping dan tarif"""
    
    def __init__(self, session=None):
        """
        Initialize service
        
        Args:
            session: Database session object (optional)
                    If not provided, will create from get_db_session()
        """
        if session is not None:
            self.session = session
            self._own_session = False  # Session dari luar, jangan di-close
        else:
            # Create new session (hanya untuk backward compatibility)
            from database_connection import SessionLocal
            self.session = SessionLocal()
            self._own_session = True  # Session dibuat sendiri, harus di-close
    
    def __del__(self):
        """Close session when object is destroyed (only if we created it)"""
        if hasattr(self, '_own_session') and self._own_session and hasattr(self, 'session'):
            self.session.close()
    
    # ========================================================================
    # MAIN PREDICTION FUNCTION
    # ========================================================================
    
    def predict_inacbg_with_tarif(
        self,
        icd10_primary: str,
        icd10_secondary: Optional[List[str]] = None,
        icd9_list: Optional[List[str]] = None,
        layanan: str = "RI",
        regional: str = "1",
        kelas_rs: str = "B",
        tipe_rs: str = "Pemerintah",
        kelas_bpjs: int = 1
    ) -> Dict[str, Any]:
        """
        Main function: Predict INA-CBG dan ambil tarif
        
        Args:
            icd10_primary: Kode ICD10 diagnosis utama (required)
            icd10_secondary: List kode ICD10 diagnosis sekunder (optional)
            icd9_list: List kode ICD9 prosedur (optional)
            layanan: RI atau RJ (default: RI)
            regional: Regional 1-5 (default: 1)
            kelas_rs: Kelas RS A/B/C/D (default: B)
            tipe_rs: Pemerintah/Swasta (default: Pemerintah)
            kelas_bpjs: Kelas BPJS 1/2/3 (default: 1)
        
        Returns:
            Dict dengan structure:
            {
                "success": True,
                "cbg_code": "I-4-10-II",
                "description": "Infark Miocard Akut Sedang",
                "tarif": 12500000,
                "breakdown": {...},
                "matching_detail": {...},
                "warnings": [...]
            }
        """
        try:
            # Normalize inputs
            icd10_secondary = icd10_secondary or []
            icd9_list = icd9_list or []
            layanan = layanan.upper()
            
            # Step 1: Predict CBG Code (5-level fallback)
            prediction = self._predict_cbg_code(
                icd10_primary=icd10_primary,
                icd10_secondary=icd10_secondary,
                icd9_list=icd9_list,
                layanan=layanan
            )
            
            if not prediction or "error" in prediction:
                return {
                    "success": False,
                    "error": prediction.get("reason", "Cannot predict INA-CBG"),
                    "inputs": {
                        "icd10_primary": icd10_primary,
                        "icd10_secondary": icd10_secondary,
                        "icd9_list": icd9_list,
                        "layanan": layanan
                    }
                }
            
            cbg_code = prediction["cbg_code"]
            
            # Step 2: Get Tarif dari master table
            tarif_result = self._get_tarif(
                cbg_code=cbg_code,
                regional=regional,
                kelas_rs=kelas_rs,
                tipe_rs=tipe_rs,
                kelas_bpjs=kelas_bpjs,
                layanan=layanan  # Pass layanan untuk conversion
            )
            
            if not tarif_result:
                return {
                    "success": False,
                    "error": "CBG code found but tarif not available",
                    "cbg_code": cbg_code,
                    "prediction": prediction,
                    "warning": f"Tarif untuk {cbg_code} dengan regional={regional}, kelas={kelas_rs}, tipe={tipe_rs} tidak ditemukan"
                }
            
            # Step 3: Build response
            return {
                "success": True,
                "cbg_code": cbg_code,
                "description": tarif_result["description"],
                "tarif": tarif_result["tarif"],
                "tarif_detail": {
                    "tarif_kelas_1": tarif_result["tarif_kelas_1"],
                    "tarif_kelas_2": tarif_result["tarif_kelas_2"],
                    "tarif_kelas_3": tarif_result["tarif_kelas_3"],
                    "kelas_bpjs_used": kelas_bpjs
                },
                "breakdown": self._breakdown_cbg_code(cbg_code),
                "matching_detail": {
                    "strategy": prediction["strategy"],
                    "confidence": prediction["confidence"],
                    "case_count": prediction.get("case_count", 0),
                    "note": prediction.get("note", "")
                },
                "classification": {
                    "regional": regional,
                    "kelas_rs": kelas_rs,
                    "tipe_rs": tipe_rs,
                    "layanan": layanan
                },
                "warnings": prediction.get("warnings", [])
            }
            
        except Exception as e:
            logger.error(f"Error in predict_inacbg_with_tarif: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ========================================================================
    # LEVEL 1: EXACT EMPIRICAL MATCH
    # ========================================================================
    
    def _exact_empirical_match(
        self, 
        icd10_primary: str, 
        icd9_list: List[str], 
        layanan: str
    ) -> Optional[Dict[str, Any]]:
        """
        Level 1: Exact match ICD10 + ALL ICD9 + Layanan
        Confidence: 95-100%
        """
        # Create ICD9 signature (sorted untuk konsistensi)
        if icd9_list:
            icd9_signature = ";".join(sorted(icd9_list))
        else:
            icd9_signature = None
        
        query = text("""
            SELECT 
                inacbg_code, 
                COUNT(*) as case_count,
                icd9_signature
            FROM cleaned_mapping_inacbg
            WHERE icd10_primary = :icd10
              AND (
                  (:icd9_sig IS NULL AND icd9_signature IS NULL) OR
                  (icd9_signature = :icd9_sig)
              )
              AND layanan = :layanan
            GROUP BY inacbg_code, icd9_signature
            ORDER BY case_count DESC
            LIMIT 1
        """)
        
        result = self.session.execute(query, {
            "icd10": icd10_primary,
            "icd9_sig": icd9_signature,
            "layanan": layanan
        }).fetchone()
        
        if result:
            return {
                "cbg_code": result[0],
                "strategy": "exact_empirical_match",
                "confidence": 98,
                "case_count": result[1],
                "matched_pattern": f"{icd10_primary} + {result[2] or 'no procedure'} + {layanan}",
                "note": "Exact match dari data RS - PALING AKURAT"
            }
        
        return None
    
    # ========================================================================
    # LEVEL 2: PARTIAL EMPIRICAL MATCH
    # ========================================================================
    
    def _partial_empirical_match(
        self, 
        icd10_primary: str, 
        icd9_list: List[str], 
        layanan: str
    ) -> Optional[Dict[str, Any]]:
        """
        Level 2: Match dengan ICD9 utama (yang pertama)
        Confidence: 85-95%
        """
        if not icd9_list:
            return None
        
        # ICD9 pertama = prosedur utama
        main_icd9 = icd9_list[0]
        
        query = text("""
            SELECT 
                inacbg_code, 
                COUNT(*) as case_count,
                icd9_signature
            FROM cleaned_mapping_inacbg
            WHERE icd10_primary = :icd10
              AND (
                  icd9_signature LIKE :icd9_pattern1 OR
                  icd9_signature = :main_icd9
              )
              AND layanan = :layanan
            GROUP BY inacbg_code, icd9_signature
            ORDER BY case_count DESC
            LIMIT 1
        """)
        
        result = self.session.execute(query, {
            "icd10": icd10_primary,
            "icd9_pattern1": f"{main_icd9};%",
            "main_icd9": main_icd9,
            "layanan": layanan
        }).fetchone()
        
        if result:
            warnings = []
            if len(icd9_list) > 1:
                ignored_icd9 = ", ".join(icd9_list[1:])
                warnings.append(f"Prosedur tambahan diabaikan: {ignored_icd9}")
            
            return {
                "cbg_code": result[0],
                "strategy": "partial_empirical_match",
                "confidence": 90,
                "case_count": result[1],
                "matched_pattern": f"{icd10_primary} + {result[2]} + {layanan}",
                "note": f"Match dengan ICD9 utama ({main_icd9})",
                "warnings": warnings
            }
        
        return None
    
    # ========================================================================
    # LEVEL 3: DIAGNOSIS-ONLY EMPIRICAL
    # ========================================================================
    
    def _diagnosis_only_empirical(
        self, 
        icd10_primary: str, 
        layanan: str
    ) -> Optional[Dict[str, Any]]:
        """
        Level 3: Match hanya ICD10 + Layanan, ambil yang paling sering
        Confidence: 75-85%
        """
        query = text("""
            SELECT 
                inacbg_code,
                COUNT(*) as total_cases,
                COUNT(DISTINCT icd9_signature) as pattern_count,
                ROUND(100.0 * COUNT(*) / 
                      SUM(COUNT(*)) OVER(), 2) as percentage
            FROM cleaned_mapping_inacbg
            WHERE icd10_primary = :icd10
              AND layanan = :layanan
            GROUP BY inacbg_code
            ORDER BY total_cases DESC
            LIMIT 3
        """)
        
        results = self.session.execute(query, {
            "icd10": icd10_primary,
            "layanan": layanan
        }).fetchall()
        
        if results:
            top_result = results[0]
            
            # Hitung confidence based on dominance
            percentage = float(top_result[3])
            if percentage >= 50:
                confidence = 85
            elif percentage >= 30:
                confidence = 80
            else:
                confidence = 75
            
            # Build alternatives
            alternatives = [
                {
                    "code": row[0],
                    "percentage": float(row[3]),
                    "case_count": row[1]
                }
                for row in results[1:]
            ]
            
            return {
                "cbg_code": top_result[0],
                "strategy": "diagnosis_only_empirical",
                "confidence": confidence,
                "case_count": top_result[1],
                "percentage": percentage,
                "alternatives": alternatives,
                "note": f"{percentage}% kasus {icd10_primary} masuk CBG ini",
                "warnings": ["Prosedur diabaikan, menggunakan CBG yang paling umum untuk diagnosis ini"]
            }
        
        return None
    
    # ========================================================================
    # LEVEL 4: SIMILAR PROCEDURE EMPIRICAL
    # ========================================================================
    
    def _similar_procedure_empirical(
        self, 
        icd10_primary: str, 
        icd9_list: List[str], 
        layanan: str
    ) -> Optional[Dict[str, Any]]:
        """
        Level 4: Cari prosedur mirip di data RS
        Confidence: 65-75%
        """
        if not icd9_list:
            return None
        
        main_icd9 = icd9_list[0]
        
        # Cari similar codes
        similar_query = text("""
            SELECT similar_codes
            FROM icd9_procedure_info
            WHERE icd9_code = :icd9
        """)
        
        similar_result = self.session.execute(similar_query, {
            "icd9": main_icd9
        }).fetchone()
        
        if not similar_result or not similar_result[0]:
            return None
        
        similar_codes = json.loads(similar_result[0])
        
        # Coba match dengan tiap similar code
        for similar_icd9 in similar_codes:
            query = text("""
                SELECT 
                    inacbg_code, 
                    COUNT(*) as case_count,
                    icd9_signature
                FROM cleaned_mapping_inacbg
                WHERE icd10_primary = :icd10
                  AND icd9_signature LIKE :icd9_pattern
                  AND layanan = :layanan
                GROUP BY inacbg_code, icd9_signature
                ORDER BY case_count DESC
                LIMIT 1
            """)
            
            result = self.session.execute(query, {
                "icd10": icd10_primary,
                "icd9_pattern": f"%{similar_icd9}%",
                "layanan": layanan
            }).fetchone()
            
            if result:
                return {
                    "cbg_code": result[0],
                    "strategy": "similar_procedure_empirical",
                    "confidence": 70,
                    "case_count": result[1],
                    "original_icd9": main_icd9,
                    "matched_icd9": similar_icd9,
                    "matched_pattern": result[2],
                    "note": f"ICD9 {main_icd9} tidak ada di data RS",
                    "warnings": [f"Menggunakan prosedur mirip: {similar_icd9}"]
                }
        
        return None
    
    # ========================================================================
    # LEVEL 5: RULE-BASED CONSTRUCTION
    # ========================================================================
    
    def _rule_based_construction(
        self, 
        icd10_primary: str, 
        icd10_secondary: List[str], 
        icd9_list: List[str], 
        layanan: str
    ) -> Optional[Dict[str, Any]]:
        """
        Level 5: Bangun kode dari aturan
        Confidence: 50-65%
        """
        # 1. Determine CMG
        cmg = self._get_cmg_from_icd10(icd10_primary)
        if not cmg:
            return None
        
        # 2. Determine Case Type
        case_type = self._determine_case_type(layanan, icd9_list)
        
        # 3. Get most common specific code for this CMG + Case Type
        specific_query = text("""
            SELECT 
                SUBSTRING(inacbg_code FROM 5 FOR 2) as specific_code,
                COUNT(*) as usage_count
            FROM cleaned_mapping_inacbg
            WHERE inacbg_code LIKE :pattern
            GROUP BY specific_code
            ORDER BY usage_count DESC
            LIMIT 1
        """)
        
        result = self.session.execute(specific_query, {
            "pattern": f"{cmg}-{case_type}-%"
        }).fetchone()
        
        if not result:
            return None
        
        specific_code = result[0]
        
        # 4. Determine Severity
        if layanan == 'RJ':
            severity = '0'
        else:
            severity = self._calculate_severity(icd10_secondary)
        
        # 5. Build code
        constructed_code = f"{cmg}-{case_type}-{specific_code}-{severity}"
        
        # 6. Validate: Cek apakah kode ini ada di master tarif
        validation = self._validate_cbg_code(constructed_code)
        
        if validation:
            return {
                "cbg_code": constructed_code,
                "strategy": "rule_based_construction",
                "confidence": 60,
                "construction_details": {
                    "cmg": cmg,
                    "case_type": case_type,
                    "specific_code": specific_code,
                    "severity": severity,
                    "based_on": f"Most common specific code for {cmg}-{case_type}"
                },
                "note": "Diagnosis belum ada di data RS, kode dibangun dari aturan",
                "warnings": ["Akurasi mungkin lebih rendah - tidak ada data empiris untuk kombinasi ini"]
            }
        else:
            # Try fallback severities
            for fallback_severity in ['I', 'II', 'III', '0']:
                fallback_code = f"{cmg}-{case_type}-{specific_code}-{fallback_severity}"
                if self._validate_cbg_code(fallback_code):
                    return {
                        "cbg_code": fallback_code,
                        "strategy": "rule_based_construction",
                        "confidence": 55,
                        "note": "Kode disesuaikan karena kode asli tidak ada di master",
                        "warnings": [f"Severity disesuaikan ke {fallback_severity}"]
                    }
        
        return None
    
    # ========================================================================
    # HELPER: GET TARIF FROM MASTER
    # ========================================================================
    
    def _get_tarif(
        self,
        cbg_code: str,
        regional: str,
        kelas_rs: str,
        tipe_rs: str,
        kelas_bpjs: int,
        layanan: str = "RI"
    ) -> Optional[Dict[str, Any]]:
        """
        Get tarif dari tabel inacbg_tarif
        
        Note: layanan di tabel inacbg_tarif menggunakan format "inap"/"jalan"
        sedangkan input menggunakan format "RI"/"RJ"
        
        Returns tarif berdasarkan kelas BPJS (1/2/3)
        """
        # Convert layanan dari RI/RJ ke inap/jalan
        layanan_db = self._convert_layanan_for_tarif(layanan)
        
        query = text("""
            SELECT 
                kode_ina_cbg,
                deskripsi,
                tarif_kelas_1,
                tarif_kelas_2,
                tarif_kelas_3,
                CASE 
                    WHEN :kelas_bpjs = 1 THEN tarif_kelas_1
                    WHEN :kelas_bpjs = 2 THEN tarif_kelas_2
                    WHEN :kelas_bpjs = 3 THEN tarif_kelas_3
                    ELSE tarif_kelas_1
                END as tarif
            FROM inacbg_tarif
            WHERE kode_ina_cbg = :cbg_code
              AND layanan = :layanan
              AND regional = :regional
              AND kelas_rs = :kelas_rs
              AND tipe_rs = :tipe_rs
              AND is_active = TRUE
            LIMIT 1
        """)
        
        result = self.session.execute(query, {
            "cbg_code": cbg_code,
            "layanan": layanan_db,
            "regional": regional,
            "kelas_rs": kelas_rs,
            "tipe_rs": tipe_rs,
            "kelas_bpjs": kelas_bpjs
        }).fetchone()
        
        if result:
            return {
                "cbg_code": result[0],
                "description": result[1],
                "tarif_kelas_1": float(result[2]) if result[2] else 0,
                "tarif_kelas_2": float(result[3]) if result[3] else 0,
                "tarif_kelas_3": float(result[4]) if result[4] else 0,
                "tarif": float(result[5]) if result[5] else 0
            }
        
        return None
    
    # ========================================================================
    # HELPER FUNCTIONS
    # ========================================================================
    
    def _convert_layanan_for_tarif(self, layanan: str) -> str:
        """
        Convert layanan dari format input (RI/RJ) ke format database (Inap/Jalan)
        
        Args:
            layanan: "RI" atau "RJ"
        
        Returns:
            "Inap" atau "Jalan" (huruf besar di awal)
        """
        mapping = {
            "RI": "Inap",
            "RJ": "Jalan"
        }
        return mapping.get(layanan.upper(), "Inap")
    
    def _predict_cbg_code(
        self,
        icd10_primary: str,
        icd10_secondary: List[str],
        icd9_list: List[str],
        layanan: str
    ) -> Optional[Dict[str, Any]]:
        """Execute 5-level fallback untuk predict CBG code"""
        
        # Level 1: Exact empirical
        result = self._exact_empirical_match(icd10_primary, icd9_list, layanan)
        if result:
            return result
        
        # Level 2: Partial empirical
        result = self._partial_empirical_match(icd10_primary, icd9_list, layanan)
        if result:
            return result
        
        # Level 3: Diagnosis-only
        result = self._diagnosis_only_empirical(icd10_primary, layanan)
        if result:
            return result
        
        # Level 4: Similar procedure
        result = self._similar_procedure_empirical(icd10_primary, icd9_list, layanan)
        if result:
            return result
        
        # Level 5: Rule-based
        result = self._rule_based_construction(icd10_primary, icd10_secondary, icd9_list, layanan)
        if result:
            return result
        
        # No match found
        return {
            "error": "Cannot predict INA-CBG",
            "reason": f"Diagnosis {icd10_primary} tidak ditemukan di data RS dan tidak bisa construct dari rules"
        }
    
    def _get_cmg_from_icd10(self, icd10_code: str) -> Optional[str]:
        """Get CMG dari ICD10 code"""
        query = text("""
            SELECT cmg
            FROM icd10_cmg_mapping
            WHERE :icd10 >= icd10_chapter_start
              AND :icd10 <= icd10_chapter_end
            ORDER BY priority DESC
            LIMIT 1
        """)
        
        result = self.session.execute(query, {"icd10": icd10_code}).fetchone()
        return result[0] if result else None
    
    def _determine_case_type(self, layanan: str, icd9_list: List[str]) -> str:
        """Determine case type dari layanan dan prosedur"""
        
        # Special cases: Obstetric (O) dan Neonatal (P) - need ICD10 for this
        # For now, simple logic:
        
        if layanan == 'RI':
            if icd9_list:
                return '1'  # Prosedur Rawat Inap
            else:
                return '4'  # Rawat Inap Bukan Prosedur
        elif layanan == 'RJ':
            if not icd9_list:
                return '5'  # Rawat Jalan Bukan Prosedur
            
            # Check if major procedure
            main_icd9 = icd9_list[0]
            is_major = self._is_major_procedure(main_icd9)
            
            if is_major:
                return '2'  # Prosedur Besar RJ
            else:
                return '3'  # Prosedur Signifikan RJ
        
        return '4'  # Default
    
    def _is_major_procedure(self, icd9_code: str) -> bool:
        """Check apakah ICD9 termasuk major procedure"""
        query = text("""
            SELECT is_major_procedure
            FROM icd9_procedure_info
            WHERE icd9_code = :icd9
        """)
        
        result = self.session.execute(query, {"icd9": icd9_code}).fetchone()
        return result[0] if result else False
    
    def _calculate_severity(self, icd10_secondary: List[str]) -> str:
        """Calculate severity dari ICD10 sekunder"""
        # Simplified: berdasarkan jumlah diagnosis sekunder
        if not icd10_secondary:
            return 'I'
        elif len(icd10_secondary) <= 2:
            return 'II'
        else:
            return 'III'
    
    def _validate_cbg_code(self, cbg_code: str) -> bool:
        """Validate apakah CBG code exist di master"""
        query = text("""
            SELECT 1
            FROM inacbg_tarif
            WHERE kode_ina_cbg = :cbg_code
            LIMIT 1
        """)
        
        result = self.session.execute(query, {"cbg_code": cbg_code}).fetchone()
        return result is not None
    
    def _breakdown_cbg_code(self, cbg_code: str) -> Dict[str, str]:
        """Breakdown CBG code ke komponennya"""
        parts = cbg_code.split('-')
        
        if len(parts) != 4:
            return {}
        
        # Get descriptions
        cmg_desc = self._get_cmg_description(parts[0])
        case_type_desc = self._get_case_type_description(parts[1])
        
        return {
            "cmg": parts[0],
            "cmg_description": cmg_desc,
            "case_type": parts[1],
            "case_type_description": case_type_desc,
            "specific_code": parts[2],
            "severity": parts[3]
        }
    
    def _get_cmg_description(self, cmg: str) -> str:
        """Get CMG description"""
        query = text("""
            SELECT cmg_description
            FROM icd10_cmg_mapping
            WHERE cmg = :cmg
            LIMIT 1
        """)
        
        result = self.session.execute(query, {"cmg": cmg}).fetchone()
        return result[0] if result else ""
    
    def _get_case_type_description(self, case_type: str) -> str:
        """Get case type description"""
        case_types = {
            '1': 'Prosedur Rawat Inap',
            '2': 'Prosedur Besar Rawat Jalan',
            '3': 'Prosedur Signifikan Rawat Jalan',
            '4': 'Rawat Inap Bukan Prosedur',
            '5': 'Rawat Jalan Bukan Prosedur',
            '6': 'Rawat Inap Kebidanan',
            '7': 'Rawat Jalan Kebidanan',
            '8': 'Rawat Inap Neonatal',
            '9': 'Rawat Jalan Neonatal',
            '0': 'Error Group'
        }
        return case_types.get(case_type, "Unknown")


# ========================================================================
# CONVENIENCE FUNCTION
# ========================================================================

def predict_inacbg(
    icd10_primary: str,
    icd10_secondary: Optional[List[str]] = None,
    icd9_list: Optional[List[str]] = None,
    layanan: str = "RI",
    regional: str = "1",
    kelas_rs: str = "B",
    tipe_rs: str = "Pemerintah",
    kelas_bpjs: int = 1
) -> Dict[str, Any]:
    """
    Convenience function untuk predict INA-CBG tanpa perlu instantiate class
    
    Fungsi ini akan handle database session secara otomatis
    """
    from database_connection import get_db_session
    
    # Use context manager untuk auto-close session
    with get_db_session() as session:
        service = InacbgGrouperService(session=session)
        return service.predict_inacbg_with_tarif(
            icd10_primary=icd10_primary,
            icd10_secondary=icd10_secondary,
            icd9_list=icd9_list,
            layanan=layanan,
            regional=regional,
            kelas_rs=kelas_rs,
            tipe_rs=tipe_rs,
            kelas_bpjs=kelas_bpjs
        )
