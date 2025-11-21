"""
Service untuk mengelola dan mengambil list dokumen wajib berdasarkan diagnosis
"""
from typing import List, Dict, Optional
from database_connection import get_db_session
from models import DokumenWajib
from sqlalchemy import func, or_
import logging
import re

# Import shared diagnosis matcher
from services.diagnosis_matcher import DiagnosisMatcher

logger = logging.getLogger(__name__)


class DokumenWajibService:
    """Service untuk mengelola dokumen wajib"""
    
    def __init__(self):
        pass
    
    def get_dokumen_wajib_by_diagnosis(
        self, 
        diagnosis_name: str
    ) -> Dict[str, any]:
        """
        Mengambil list dokumen wajib berdasarkan nama diagnosis
        Uses shared DiagnosisMatcher for consistency with PNPK
        
        Args:
            diagnosis_name: Nama diagnosis (misal: "Pneumonia", "Hospital-Acquired Pneumonia (HAP)")
            
        Returns:
            Dictionary dengan struktur:
            {
                "diagnosis": "Pneumonia",
                "total_dokumen": 7,
                "dokumen_list": [
                    {
                        "id": 1,
                        "nama_dokumen": "Rekam Medis",
                        "status": "wajib",
                        "keterangan": "Dokumen utama klinis dan administratif."
                    },
                    {
                        "id": 6,
                        "nama_dokumen": "Prokalsitonin (PCT)",
                        "status": "opsional",
                        "keterangan": "Tidak rutin untuk memulai antibiotik..."
                    },
                    ...
                ]
            }
        """
        try:
            logger.info(f"[DOKUMEN_WAJIB] Looking for diagnosis: '{diagnosis_name}'")
            
            # Use context manager for database session
            with get_db_session() as session:
                # Get all available diagnoses
                all_diagnoses_rows = session.query(DokumenWajib.diagnosis_name).distinct().all()
                available_diagnoses = [row.diagnosis_name for row in all_diagnoses_rows]
                
                logger.info(f"[DOKUMEN_WAJIB] Found {len(available_diagnoses)} unique diagnoses in database")
                
                # Use shared matcher (min confidence: 0.6)
                match_result = DiagnosisMatcher.match_diagnosis(
                    diagnosis_name,
                    available_diagnoses,
                    min_confidence=0.6
                )
                
                matched_diagnosis = None
                results = None
                
                if match_result:
                    matched_diagnosis, confidence, method = match_result
                    logger.info(f"[DOKUMEN_WAJIB] Match found: '{matched_diagnosis}' ({confidence:.2%}, method: {method})")
                    
                    # Fetch documents for matched diagnosis
                    results = session.query(DokumenWajib).filter(
                        DokumenWajib.diagnosis_name == matched_diagnosis
                    ).order_by(DokumenWajib.id).all()
                
                if not results:
                    logger.warning(f"[DOKUMEN_WAJIB] Tidak ada dokumen wajib ditemukan untuk diagnosis: {diagnosis_name}")
                    return {
                        "diagnosis": diagnosis_name,
                        "total_dokumen": 0,
                        "dokumen_list": [],
                        "message": f"Tidak ada dokumen wajib ditemukan untuk diagnosis: {diagnosis_name}",
                        "searched_diagnosis": diagnosis_name,
                        "matched_diagnosis": None
                    }
                
                # Konversi semua dokumen ke list
                dokumen_list = []
                
                for row in results:
                    dokumen_data = {
                        "id": row.id,
                        "diagnosis_name": row.diagnosis_name,
                        "nama_dokumen": row.nama_dokumen,
                        "status": row.status,  # status ditampilkan langsung: "wajib", "opsional", "sesuai indikasi"
                        "keterangan": row.keterangan
                    }
                    dokumen_list.append(dokumen_data)
                
                response = {
                    "diagnosis": results[0].diagnosis_name,  # Ambil diagnosis name dari hasil query
                    "total_dokumen": len(results),
                    "dokumen_list": dokumen_list,
                    "searched_diagnosis": diagnosis_name,
                    "matched_diagnosis": matched_diagnosis
                }
                
                logger.info(f"[DOKUMEN_WAJIB] Berhasil mengambil {len(results)} dokumen untuk diagnosis: {matched_diagnosis or diagnosis_name}")
                
                return response
            
        except Exception as e:
            logger.error(f"[DOKUMEN_WAJIB] Error mengambil dokumen wajib: {str(e)}")
            import traceback
            logger.error(f"[DOKUMEN_WAJIB] Traceback: {traceback.format_exc()}")
            raise Exception(f"Gagal mengambil dokumen wajib: {str(e)}")
    
    def get_all_diagnosis_list(self) -> List[str]:
        """
        Mengambil list semua diagnosis yang tersedia di tabel dokumen_wajib
        
        Returns:
            List nama diagnosis yang unik
        """
        try:
            with get_db_session() as session:
                # Query distinct diagnosis_name
                results = session.query(DokumenWajib.diagnosis_name).distinct().order_by(
                    DokumenWajib.diagnosis_name
                ).all()
                
                diagnosis_list = [row.diagnosis_name for row in results]
                
                logger.info(f"Berhasil mengambil {len(diagnosis_list)} diagnosis unik")
                
                return diagnosis_list
            
        except Exception as e:
            logger.error(f"Error mengambil list diagnosis: {str(e)}")
            raise Exception(f"Gagal mengambil list diagnosis: {str(e)}")
    
    def search_diagnosis(self, keyword: str) -> List[str]:
        """
        Search diagnosis berdasarkan keyword
        
        Args:
            keyword: Kata kunci untuk pencarian (case-insensitive)
            
        Returns:
            List nama diagnosis yang cocok
        """
        try:
            with get_db_session() as session:
                # Query dengan LIKE pattern (case-insensitive)
                search_pattern = f"%{keyword}%"
                results = session.query(DokumenWajib.diagnosis_name).distinct().filter(
                    func.lower(DokumenWajib.diagnosis_name).like(func.lower(search_pattern))
                ).order_by(DokumenWajib.diagnosis_name).all()
                
                diagnosis_list = [row.diagnosis_name for row in results]
                
                logger.info(f"Pencarian '{keyword}' menghasilkan {len(diagnosis_list)} diagnosis")
                
                return diagnosis_list
            
        except Exception as e:
            logger.error(f"Error search diagnosis: {str(e)}")
            raise Exception(f"Gagal search diagnosis: {str(e)}")


# Singleton instance
_dokumen_wajib_service = None


def get_dokumen_wajib_service() -> DokumenWajibService:
    """Get singleton instance of DokumenWajibService"""
    global _dokumen_wajib_service
    if _dokumen_wajib_service is None:
        _dokumen_wajib_service = DokumenWajibService()
    return _dokumen_wajib_service
