"""
Service untuk mengelola dan mengambil list dokumen wajib berdasarkan diagnosis
"""
from typing import List, Dict, Optional
from database_connection import get_db_session
from models import DokumenWajib
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


class DokumenWajibService:
    """Service untuk mengelola dokumen wajib"""
    
    def __init__(self):
        self.session = None
        
    def _get_session(self):
        """Get database session"""
        if not self.session:
            self.session = get_db_session()
        return self.session
    
    def get_dokumen_wajib_by_diagnosis(
        self, 
        diagnosis_name: str
    ) -> Dict[str, any]:
        """
        Mengambil list dokumen wajib berdasarkan nama diagnosis
        
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
            session = self._get_session()
            
            # Query untuk mengambil semua dokumen berdasarkan diagnosis (case-insensitive)
            results = session.query(DokumenWajib).filter(
                func.lower(DokumenWajib.diagnosis_name) == func.lower(diagnosis_name)
            ).order_by(DokumenWajib.id).all()
            
            if not results:
                logger.warning(f"Tidak ada dokumen wajib ditemukan untuk diagnosis: {diagnosis_name}")
                return {
                    "diagnosis": diagnosis_name,
                    "total_dokumen": 0,
                    "dokumen_list": [],
                    "message": "Tidak ada dokumen wajib ditemukan untuk diagnosis ini"
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
                "dokumen_list": dokumen_list
            }
            
            logger.info(f"Berhasil mengambil {len(results)} dokumen untuk diagnosis: {diagnosis_name}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error mengambil dokumen wajib: {str(e)}")
            raise Exception(f"Gagal mengambil dokumen wajib: {str(e)}")
    
    def get_all_diagnosis_list(self) -> List[str]:
        """
        Mengambil list semua diagnosis yang tersedia di tabel dokumen_wajib
        
        Returns:
            List nama diagnosis yang unik
        """
        try:
            session = self._get_session()
            
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
            session = self._get_session()
            
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
    
    def close(self):
        """Close database session"""
        if self.session:
            self.session.close()
            self.session = None


# Singleton instance
_dokumen_wajib_service = None


def get_dokumen_wajib_service() -> DokumenWajibService:
    """Get singleton instance of DokumenWajibService"""
    global _dokumen_wajib_service
    if _dokumen_wajib_service is None:
        _dokumen_wajib_service = DokumenWajibService()
    return _dokumen_wajib_service
