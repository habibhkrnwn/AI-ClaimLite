"""
Module: models

Model RulesMaster untuk core_engine agar bisa akses rules dari database.
"""

from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime, Boolean, Enum, JSON, Float, text, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID
from datetime import datetime
from database_connection import Base

class RulesMaster(Base):
    __tablename__ = "rules_master"

    id = Column(Integer, primary_key=True, index=True)
    diagnosis = Column(Text, nullable=False)       # Nama diagnosis: "Pneumonia", "DM Tipe 2", dll
    field = Column(Text, nullable=False)           # Field aturan: "rawat_inap.lama_rawat", dll
    layer = Column(Text, nullable=False)           # Layer: "permenkes", "nasional", "ppk", "regional", "rs", "bridging", "fraud", "temporary"
    isi = Column(Text, nullable=False)             # Isi aturan: "LOS ≥ 2 hari", dll
    sumber = Column(Text, nullable=True)           # Sumber: "PNPK Pneumonia 2023", "PPK RS Notopuro 2024", dll
    pdf_file = Column(Text, nullable=True)         # Nama file PDF: "ppk_hipertensi_2024.pdf", null jika tidak ada
    rs_id = Column(Text, nullable=True)            # ID RS: "rs_notopuro", null untuk rules global
    region_id = Column(Text, nullable=True)        # ID wilayah: "jatim", null untuk rules global
    status = Column(Text, nullable=False, default="unverified")  # Status: "unverified", "official", "active", "rejected"
    created_by = Column(Text, nullable=True)       # Pembuat: "admin_rs_notopuro", "ai_meta_admin", dll
    approved_by = Column(Text, nullable=True)      # Yang approve: "ai_meta_reviewer_1", dll
    approved_date = Column(DateTime, nullable=True) # Tanggal approval
    review_notes = Column(Text, nullable=True)     # Catatan reviewer AI META
    feedback = Column(Text, nullable=True)         # Feedback dari RS tentang aturan ini
    feedback_by = Column(Text, nullable=True)      # Yang beri feedback: "admin_rs_notopuro", dll
    feedback_date = Column(DateTime, nullable=True) # Tanggal feedback
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("now()"), onupdate=text("now()"))
    scope = Column(String(50), nullable=True)       # diagnosis / tindakan / idrg / kombinasi / umum
    procedure = Column(Text, nullable=True)         # nama tindakan, misal 'X-Ray Thorax', 'Antibiotik IV'

    def __repr__(self):
        return f"<RulesMaster(id={self.id}, diagnosis={self.diagnosis}, layer={self.layer}, status={self.status})>"
    
class FornasDrug(Base):
    """
    FORNAS Drug Reference (Master Data)
    """
    __tablename__ = "fornas_drugs"
    
    id = Column(Integer, primary_key=True)
    tindakan_name = Column(String(200))
    kelas_terapi = Column(Text())
    subkelas_terapi = Column(String(200))
    obat_name = Column(String(200), nullable=False, index=True)
    sediaan_kekuatan = Column(JSON, nullable=True)
    restriksi_penggunaan = Column(Text, nullable=True)
    fasilitas_fpktp = Column(Boolean, default=False)
    fasilitas_fpktl = Column(Boolean, default=False)
    fasilitas_tp = Column(Boolean, default=False)
    oen = Column(Boolean, default=False)
    persepan_maksimal = Column(String(100))
    status_excel = Column(String(50))
    kode_fornas = Column(String(50), nullable=False, index=True)
    nama_obat_alias = Column(JSON, nullable=True)
    indikasi_fornas = Column(JSON, nullable=True)
    sumber_regulasi = Column(Text, nullable=True)
    status = Column(String(50), default='active')
    fornas_version = Column(String(20), default='2023')
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("now()"), onupdate=text("now()"))
    
    def __repr__(self):
        return f"<FornasDrug {self.kode_fornas}: {self.obat_name}>"


class ICD10Master(Base):
    """
    ICD-10 Master Reference (Master Data Diagnosis)
    """
    __tablename__ = "icd10_master"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), nullable=False, unique=True, index=True)  # Kode ICD-10: "J18.9", "I10", dll
    name = Column(Text, nullable=False, index=True)  # Nama diagnosis: "Pneumonia, unspecified", dll
    source = Column(String(100), nullable=True)  # Sumber: "ICD10_2010", "WHO_2023", dll
    validation_status = Column(String(50), nullable=True)  # Status: "official", "draft", dll
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    
    def __repr__(self):
        return f"<ICD10Master {self.code}: {self.name}>"


class PNPKSummary(Base):
    """
    PNPK Summary (Panduan Nasional Pelayanan Kedokteran)
    Berisi summary/tahapan dari PNPK untuk setiap diagnosis
    """
    __tablename__ = "pnpk_summary"
    
    id = Column(Integer, primary_key=True, index=True)
    diagnosis_name = Column(Text, nullable=False, index=True)  # Nama diagnosis: "Pneumonia", "Hospital-Acquired Pneumonia", dll
    urutan = Column(Integer, nullable=False)  # Urutan tahapan: 1, 2, 3, 4, 5
    tahap = Column(Text, nullable=False)  # Nama tahap: "Tahap Diagnosis (Bundel)", "Tahap Terapi Empiris", dll
    deskripsi = Column(Text, nullable=True)  # Deskripsi detail tahapan
    
    # Metadata columns (optional, for future improvements)
    source = Column(String(200), nullable=True, default='Unknown')  # Sumber: "PNPK Pneumonia Kemenkes 2024"
    version = Column(String(20), nullable=True, default='1.0')  # Versi: "2024.1", "2023.2"
    status = Column(String(20), nullable=True, default='active')  # Status: "active", "inactive", "draft"
    created_at = Column(DateTime, nullable=True, server_default=text("now()"))  # Kapan data di-input
    updated_at = Column(DateTime, nullable=True, server_default=text("now()"), onupdate=text("now()"))  # Kapan terakhir update
    
    def __repr__(self):
        return f"<PNPKSummary {self.diagnosis_name} - Tahap {self.urutan}: {self.tahap}>"


class ICD9CMMaster(Base):
    """
    ICD-9-CM Master Reference (Master Data Tindakan/Prosedur)
    """
    __tablename__ = "icd9cm_master"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), nullable=False, unique=True, index=True)  # Kode ICD-9-CM: "93.96", "87.44", dll
    name = Column(Text, nullable=False, index=True)  # Nama prosedur: "Nebulisasi", "Rontgen Thorax", dll
    source = Column(String(100), nullable=True)  # Sumber: "ICD9CM_2010", "WHO_2023", dll
    validation_status = Column(String(50), nullable=True)  # Status: "official", "draft", dll
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    
    def __repr__(self):
        return f"<ICD9CMMaster {self.code}: {self.name}>"


# ============================================================
# INA-CBG MODELS (SQLAlchemy)
# ============================================================

class InacbgTarif(Base):
    """
    INA-CBG Tarif Master - Master tarif INA-CBG dari Permenkes
    """
    __tablename__ = "inacbg_tarif"
    
    id = Column(Integer, primary_key=True, index=True)
    kode_ina_cbg = Column(String(20), nullable=False, index=True)  # I-4-10-II
    deskripsi = Column(Text, nullable=True)
    layanan = Column(String(10), nullable=False, index=True)  # "inap" atau "jalan"
    regional = Column(String(5), nullable=False, index=True)  # "1" sampai "5"
    kelas_rs = Column(String(5), nullable=False, index=True)  # "A", "B", "C", "D"
    tipe_rs = Column(String(20), nullable=False, index=True)  # "Pemerintah" atau "Swasta"
    tarif_kelas_1 = Column(Numeric(15, 2), nullable=True)
    tarif_kelas_2 = Column(Numeric(15, 2), nullable=True)
    tarif_kelas_3 = Column(Numeric(15, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("now()"), onupdate=text("now()"))
    
    def __repr__(self):
        return f"<InacbgTarif {self.kode_ina_cbg} - {self.layanan} - Regional {self.regional}>"


class CleanedMappingInacbg(Base):
    """
    Cleaned Mapping INA-CBG - Empirical mapping dari data RS
    Pattern: ICD10 + ICD9 + Layanan → INA-CBG Code
    """
    __tablename__ = "cleaned_mapping_inacbg"
    
    id = Column(Integer, primary_key=True, index=True)
    icd10_primary = Column(String(10), nullable=False, index=True)
    icd9_signature = Column(Text, nullable=True, index=True)  # "36.06;36.07" (sorted)
    layanan = Column(String(10), nullable=False, index=True)  # "RI" atau "RJ"
    inacbg_code = Column(String(20), nullable=False, index=True)
    frequency = Column(Integer, default=1)
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    
    def __repr__(self):
        return f"<CleanedMappingInacbg {self.icd10_primary} → {self.inacbg_code} ({self.frequency}x)>"


class Icd10CmgMapping(Base):
    """
    ICD10 to CMG Mapping - Mapping ICD10 chapter ke CMG code
    """
    __tablename__ = "icd10_cmg_mapping"
    
    id = Column(Integer, primary_key=True, index=True)
    icd10_chapter = Column(String(50), nullable=False)
    icd10_chapter_start = Column(String(10), nullable=False, index=True)
    icd10_chapter_end = Column(String(10), nullable=False, index=True)
    cmg = Column(String(5), nullable=False, index=True)  # "I", "J", "K", dll
    cmg_description = Column(Text, nullable=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    
    def __repr__(self):
        return f"<Icd10CmgMapping {self.icd10_chapter} → CMG {self.cmg}>"


class Icd9ProcedureInfo(Base):
    """
    ICD9 Procedure Information - Info prosedur ICD9 dengan similar codes
    """
    __tablename__ = "icd9_procedure_info"
    
    id = Column(Integer, primary_key=True, index=True)
    icd9_code = Column(String(10), nullable=False, unique=True, index=True)
    procedure_name = Column(Text, nullable=True)
    is_major_procedure = Column(Boolean, default=False)
    chapter = Column(String(10), nullable=True, index=True)
    similar_codes = Column(JSON, nullable=True)  # ["36.07", "36.09"]
    similarity_score = Column(Float, nullable=True)
    usage_frequency = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
    
    def __repr__(self):
        return f"<Icd9ProcedureInfo {self.icd9_code}: {self.procedure_name}>"


class DokumenWajib(Base):
    """
    Dokumen Wajib untuk setiap Diagnosis
    Menyimpan list dokumen yang wajib, opsional, atau sesuai indikasi untuk diagnosis tertentu
    """
    __tablename__ = "dokumen_wajib"
    
    id = Column(Integer, primary_key=True, index=True)
    diagnosis_name = Column(Text, nullable=False, index=True)  # Nama diagnosis: "Pneumonia", "Hospital-Acquired Pneumonia (HAP)", dll
    nama_dokumen = Column(Text, nullable=False)  # Nama dokumen: "Rekam Medis", "Radiografi Toraks (PA)", dll
    status = Column(Text, nullable=False)  # Status: "wajib", "opsional", "sesuai indikasi"
    keterangan = Column(Text, nullable=True)  # Keterangan/deskripsi dokumen
    
    def __repr__(self):
        return f"<DokumenWajib {self.diagnosis_name} - {self.nama_dokumen} ({self.status})>"


# ============================================================================
# PYDANTIC MODELS FOR INA-CBG API
# ============================================================================

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any


class InacbgPredictRequest(BaseModel):
    """Request model untuk INA-CBG prediction"""
    
    icd10_primary: str = Field(..., description="Kode ICD10 diagnosis utama", example="I21.0")
    icd10_secondary: Optional[List[str]] = Field(None, description="List kode ICD10 diagnosis sekunder", example=["E11.9", "I25.1"])
    icd9_list: Optional[List[str]] = Field(None, description="List kode ICD9 prosedur", example=["36.06", "36.07"])
    layanan: str = Field("RI", description="Jenis layanan: RI (Rawat Inap) atau RJ (Rawat Jalan)", example="RI")
    regional: str = Field("1", description="Regional 1-5 berdasarkan IHK", example="1")
    kelas_rs: str = Field("B", description="Kelas RS: A, B, C, D, dll", example="B")
    tipe_rs: str = Field("Pemerintah", description="Tipe RS: Pemerintah atau Swasta", example="Pemerintah")
    kelas_bpjs: int = Field(1, description="Kelas BPJS pasien: 1, 2, atau 3", example=1)
    
    @validator('layanan')
    def validate_layanan(cls, v):
        v = v.upper()
        if v not in ['RI', 'RJ']:
            raise ValueError('Layanan harus RI atau RJ')
        return v
    
    @validator('regional')
    def validate_regional(cls, v):
        if v not in ['1', '2', '3', '4', '5']:
            raise ValueError('Regional harus 1-5')
        return v
    
    @validator('kelas_bpjs')
    def validate_kelas_bpjs(cls, v):
        if v not in [1, 2, 3]:
            raise ValueError('Kelas BPJS harus 1, 2, atau 3')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "icd10_primary": "I21.0",
                "icd10_secondary": ["E11.9", "I25.1"],
                "icd9_list": ["36.06", "36.07"],
                "layanan": "RI",
                "regional": "1",
                "kelas_rs": "B",
                "tipe_rs": "Pemerintah",
                "kelas_bpjs": 1
            }
        }


class CBGBreakdown(BaseModel):
    """Breakdown komponen kode INA-CBG"""
    
    cmg: str = Field(..., description="Case Mix Group (digit 1)", example="I")
    cmg_description: str = Field(..., description="Deskripsi CMG", example="Cardiovascular system")
    case_type: str = Field(..., description="Tipe kasus (digit 2)", example="4")
    case_type_description: str = Field(..., description="Deskripsi tipe kasus", example="Rawat Inap Bukan Prosedur")
    specific_code: str = Field(..., description="Kode spesifik (digit 3)", example="10")
    severity: str = Field(..., description="Tingkat keparahan (digit 4)", example="II")


class MatchingDetail(BaseModel):
    """Detail matching strategy yang digunakan"""
    
    strategy: str = Field(..., description="Strategy yang digunakan", example="exact_empirical_match")
    confidence: int = Field(..., description="Confidence score (0-100)", example=98)
    case_count: int = Field(0, description="Jumlah kasus yang match di data RS", example=150)
    note: str = Field("", description="Catatan tambahan", example="Exact match dari data RS")


class TarifDetail(BaseModel):
    """Detail tarif per kelas BPJS"""
    
    tarif_kelas_1: float = Field(..., description="Tarif untuk BPJS kelas 1")
    tarif_kelas_2: float = Field(..., description="Tarif untuk BPJS kelas 2")
    tarif_kelas_3: float = Field(..., description="Tarif untuk BPJS kelas 3")
    kelas_bpjs_used: int = Field(..., description="Kelas BPJS yang digunakan")


class Classification(BaseModel):
    """Klasifikasi RS dan layanan"""
    
    regional: str = Field(..., description="Regional")
    kelas_rs: str = Field(..., description="Kelas RS")
    tipe_rs: str = Field(..., description="Tipe RS")
    layanan: str = Field(..., description="Jenis layanan")


class InacbgPredictResponse(BaseModel):
    """Response model untuk INA-CBG prediction"""
    
    success: bool = Field(..., description="Status keberhasilan", example=True)
    cbg_code: Optional[str] = Field(None, description="Kode INA-CBG", example="I-4-10-II")
    description: Optional[str] = Field(None, description="Deskripsi INA-CBG", example="Infark Miocard Akut Sedang")
    tarif: Optional[float] = Field(None, description="Tarif sesuai kelas BPJS", example=12500000.0)
    tarif_detail: Optional[TarifDetail] = Field(None, description="Detail tarif per kelas")
    breakdown: Optional[CBGBreakdown] = Field(None, description="Breakdown komponen kode INA-CBG")
    matching_detail: Optional[MatchingDetail] = Field(None, description="Detail matching strategy")
    classification: Optional[Classification] = Field(None, description="Klasifikasi RS dan layanan")
    warnings: Optional[List[str]] = Field(None, description="Warning messages", example=[])
    error: Optional[str] = Field(None, description="Error message jika gagal")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "cbg_code": "I-4-10-II",
                "description": "Infark Miocard Akut Sedang",
                "tarif": 12500000.0,
                "tarif_detail": {
                    "tarif_kelas_1": 15000000.0,
                    "tarif_kelas_2": 12500000.0,
                    "tarif_kelas_3": 10000000.0,
                    "kelas_bpjs_used": 2
                },
                "breakdown": {
                    "cmg": "I",
                    "cmg_description": "Cardiovascular system",
                    "case_type": "4",
                    "case_type_description": "Rawat Inap Bukan Prosedur",
                    "specific_code": "10",
                    "severity": "II"
                },
                "matching_detail": {
                    "strategy": "exact_empirical_match",
                    "confidence": 98,
                    "case_count": 150,
                    "note": "Exact match dari data RS - PALING AKURAT"
                },
                "classification": {
                    "regional": "1",
                    "kelas_rs": "B",
                    "tipe_rs": "Pemerintah",
                    "layanan": "RI"
                },
                "warnings": []
            }
        }