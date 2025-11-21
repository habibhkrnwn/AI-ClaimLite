-- ============================================================================
-- TABEL DATABASE UNTUK INA-CBG GROUPER SERVICE
-- AI-ClaimLite - Core Engine
-- ============================================================================

-- ============================================================================
-- TABEL 1: MASTER TARIF INA-CBG (dari Permenkes)
-- ============================================================================
DROP TABLE IF EXISTS inacbg_tarif CASCADE;

CREATE TABLE inacbg_tarif (
    id SERIAL PRIMARY KEY,
    kode_ina_cbg VARCHAR(20) NOT NULL,        -- K-1-14-III (BUKAN UNIQUE!)
    deskripsi TEXT,                           -- PROSEDUR HERNIA...
    
    -- Tarif per kelas BPJS
    tarif_kelas_3 DECIMAL(15,2),             -- Kelas 3 BPJS
    tarif_kelas_2 DECIMAL(15,2),             -- Kelas 2 BPJS
    tarif_kelas_1 DECIMAL(15,2),             -- Kelas 1 BPJS
    tarif DECIMAL(15,2),                      -- Base tarif (backup)
    
    -- Klasifikasi RS
    regional VARCHAR(5),                      -- 1, 2, 3, 4, 5
    kelas_rs VARCHAR(10),                     -- A, B, C, D, B Pendidikan, dll
    tipe_rs VARCHAR(50),                      -- Pemerintah, Swasta
    
    -- Metadata
    layanan VARCHAR(10),                      -- Inap, Jalan
    no INTEGER,                               -- Nomor urut
    page_number_pdf INTEGER,                  -- Referensi halaman PDF
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- CONSTRAINT: Kombinasi kode + regional + kelas_rs + tipe_rs harus unik
    CONSTRAINT unique_cbg_regional_kelas_tipe UNIQUE (kode_ina_cbg, regional, kelas_rs, tipe_rs)
);

-- Index untuk performa query
CREATE INDEX idx_tarif_kode ON inacbg_tarif(kode_ina_cbg);
CREATE INDEX idx_tarif_regional_kelas ON inacbg_tarif(regional, kelas_rs);
CREATE INDEX idx_tarif_layanan ON inacbg_tarif(layanan);
CREATE INDEX idx_tarif_active ON inacbg_tarif(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE inacbg_tarif IS 'Master tarif INA-CBG dari Permenkes per regional, kelas RS, dan tipe RS';
COMMENT ON COLUMN inacbg_tarif.kode_ina_cbg IS 'Kode INA-CBG (bisa duplicate karena beda regional/kelas/tipe)';
COMMENT ON COLUMN inacbg_tarif.regional IS 'Regional 1-5 berdasarkan IHK';
COMMENT ON COLUMN inacbg_tarif.kelas_rs IS 'Kelas RS: A, B, B Pendidikan, C, D, Rujukan Nasional';
COMMENT ON COLUMN inacbg_tarif.tipe_rs IS 'Tipe RS: Pemerintah atau Swasta';


-- ============================================================================
-- TABEL 2: DATA EMPIRIS DARI RUMAH SAKIT (Cleaned Mapping)
-- ============================================================================
DROP TABLE IF EXISTS cleaned_mapping_cbg CASCADE;

CREATE TABLE cleaned_mapping_cbg (
    id SERIAL PRIMARY KEY,
    
    -- Input data
    layanan VARCHAR(10),                      -- RI, RJ
    icd10_primary VARCHAR(10),                -- E87.1
    icd10_secondary TEXT,                     -- K30 atau K30;R11 (multiple separated by ;)
    icd10_all TEXT,                           -- E87.1;K30 (gabungan primary + secondary)
    
    -- Procedure codes
    icd9_list TEXT,                           -- 57 atau 93.90;99.04 (multiple separated by ;)
    icd9_signature TEXT,                      -- 57 atau 93.90;99.04 (untuk exact matching)
    
    -- Output: Kode INA-CBG yang benar dari data RS
    inacbg_code VARCHAR(20) NOT NULL,         -- E-4-11-I (TARGET OUTPUT)
    
    -- Metadata dari RS
    kelas_raw VARCHAR(5),                     -- 1, 2, 3 (severity dari data asli RS)
    diagnosis_raw TEXT,                       -- Raw diagnosis dari RS
    proclist_raw TEXT,                        -- Raw procedure list dari RS
    
    -- Frequency tracking
    frequency INTEGER DEFAULT 1,              -- Berapa kali pattern ini muncul
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index untuk matching algorithm
CREATE INDEX idx_cbg_icd10_primary ON cleaned_mapping_cbg(icd10_primary);
CREATE INDEX idx_cbg_layanan ON cleaned_mapping_cbg(layanan);
CREATE INDEX idx_cbg_icd9_sig ON cleaned_mapping_cbg(icd9_signature);
CREATE INDEX idx_cbg_full_match ON cleaned_mapping_cbg(icd10_primary, icd9_signature, layanan);
CREATE INDEX idx_cbg_inacbg_code ON cleaned_mapping_cbg(inacbg_code);

COMMENT ON TABLE cleaned_mapping_cbg IS 'Data empiris ICD10+ICD9 → INA-CBG dari rumah sakit (3000+ patterns)';
COMMENT ON COLUMN cleaned_mapping_cbg.icd9_signature IS 'Signature untuk exact matching (sorted ICD9 codes)';
COMMENT ON COLUMN cleaned_mapping_cbg.frequency IS 'Jumlah kasus dengan pattern yang sama';


-- ============================================================================
-- TABEL 3: ICD10 → CMG MAPPING
-- ============================================================================
DROP TABLE IF EXISTS icd10_cmg_mapping CASCADE;

CREATE TABLE icd10_cmg_mapping (
    id SERIAL PRIMARY KEY,
    icd10_code VARCHAR(10),                   -- I21 atau I21.0
    icd10_chapter_start VARCHAR(10),          -- I00 (untuk range mapping)
    icd10_chapter_end VARCHAR(10),            -- I99 (untuk range mapping)
    cmg CHAR(1) NOT NULL,                     -- I (Cardiovascular)
    cmg_description TEXT,                     -- Cardiovascular system
    priority INTEGER DEFAULT 1,               -- Untuk multiple mapping (1 = highest)
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_icd10_cmg_code ON icd10_cmg_mapping(icd10_code);
CREATE INDEX idx_icd10_cmg_chapter ON icd10_cmg_mapping(icd10_chapter_start, icd10_chapter_end);
CREATE INDEX idx_cmg ON icd10_cmg_mapping(cmg);

COMMENT ON TABLE icd10_cmg_mapping IS 'Mapping ICD10 code/range ke CMG (Case Mix Group)';
COMMENT ON COLUMN icd10_cmg_mapping.priority IS 'Priority untuk overlapping ranges (1 = highest)';


-- ============================================================================
-- TABEL 4: ICD9 PROCEDURE INFO
-- ============================================================================
DROP TABLE IF EXISTS icd9_procedure_info CASCADE;

CREATE TABLE icd9_procedure_info (
    id SERIAL PRIMARY KEY,
    icd9_code VARCHAR(10) UNIQUE NOT NULL,    -- 57 atau 99.04
    description TEXT,                          -- Deskripsi prosedur
    
    -- Categorization
    chapter_range VARCHAR(10),                -- 55-59 (Urinary procedures)
    category VARCHAR(100),                    -- Urinary system procedures
    body_system VARCHAR(50),                  -- Nephro-urinary
    
    -- Classification
    is_major_procedure BOOLEAN DEFAULT FALSE, -- TRUE = prosedur besar, FALSE = minor
    procedure_type VARCHAR(20),               -- surgical, diagnostic, therapeutic
    
    -- Similarity
    similar_codes TEXT,                       -- JSON array: ["57.0", "57.1", "57.94"]
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_icd9_code ON icd9_procedure_info(icd9_code);
CREATE INDEX idx_icd9_chapter ON icd9_procedure_info(chapter_range);
CREATE INDEX idx_icd9_body_system ON icd9_procedure_info(body_system);
CREATE INDEX idx_icd9_major ON icd9_procedure_info(is_major_procedure);

COMMENT ON TABLE icd9_procedure_info IS 'Informasi ICD9 procedure untuk similarity matching';
COMMENT ON COLUMN icd9_procedure_info.is_major_procedure IS 'Untuk case_type determination (major=2, minor=3)';


-- ============================================================================
-- TABEL 5: ICD10 SEVERITY INFO (Optional - untuk future enhancement)
-- ============================================================================
DROP TABLE IF EXISTS icd10_severity_info CASCADE;

CREATE TABLE icd10_severity_info (
    id SERIAL PRIMARY KEY,
    icd10_code VARCHAR(10) UNIQUE NOT NULL,   -- E11.9
    description TEXT,                          -- Type 2 diabetes with complications
    
    -- Severity classification
    is_cc BOOLEAN DEFAULT FALSE,              -- Complication/Comorbidity
    is_mcc BOOLEAN DEFAULT FALSE,             -- Major CC
    severity_weight INTEGER DEFAULT 0,        -- 0=no impact, 1=minor, 2=moderate, 3=major
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_icd10_severity_code ON icd10_severity_info(icd10_code);
CREATE INDEX idx_icd10_cc ON icd10_severity_info(is_cc);
CREATE INDEX idx_icd10_mcc ON icd10_severity_info(is_mcc);

COMMENT ON TABLE icd10_severity_info IS 'ICD10 secondary diagnosis severity untuk menentukan level I/II/III';
COMMENT ON COLUMN icd10_severity_info.is_mcc IS 'Major complication/comorbidity (severity III)';


-- ============================================================================
-- VIEWS UNTUK KEMUDAHAN QUERY
-- ============================================================================

-- View: Tarif lengkap dengan breakdown kode
CREATE OR REPLACE VIEW v_inacbg_tarif_detail AS
SELECT 
    id,
    kode_ina_cbg,
    deskripsi,
    
    -- Breakdown kode
    SUBSTRING(kode_ina_cbg, 1, 1) as cmg,
    SUBSTRING(kode_ina_cbg, 3, 1) as case_type,
    SUBSTRING(kode_ina_cbg, 5, 2) as specific_code,
    SUBSTRING(kode_ina_cbg FROM 8) as severity,
    
    -- Tarif
    tarif_kelas_1,
    tarif_kelas_2,
    tarif_kelas_3,
    tarif as base_tarif,
    
    -- Klasifikasi
    regional,
    kelas_rs,
    tipe_rs,
    layanan,
    
    is_active
FROM inacbg_tarif
WHERE is_active = TRUE;

COMMENT ON VIEW v_inacbg_tarif_detail IS 'View tarif INA-CBG dengan breakdown komponen kode';


-- View: Statistik mapping empiris
CREATE OR REPLACE VIEW v_cbg_mapping_stats AS
SELECT 
    layanan,
    COUNT(DISTINCT icd10_primary) as total_unique_diagnosis,
    COUNT(DISTINCT icd9_signature) as total_unique_procedures,
    COUNT(DISTINCT inacbg_code) as total_unique_cbg,
    COUNT(*) as total_patterns,
    SUM(frequency) as total_cases
FROM cleaned_mapping_cbg
GROUP BY layanan;

COMMENT ON VIEW v_cbg_mapping_stats IS 'Statistik data empiris per layanan';


-- ============================================================================
-- TRIGGER: Auto update timestamp
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_inacbg_tarif_updated_at 
    BEFORE UPDATE ON inacbg_tarif 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cleaned_mapping_updated_at 
    BEFORE UPDATE ON cleaned_mapping_cbg 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- SAMPLE DATA CHECK QUERIES
-- ============================================================================

-- Check berapa regional dan kelas RS
-- SELECT DISTINCT regional, kelas_rs FROM inacbg_tarif ORDER BY regional, kelas_rs;

-- Check distribusi kode CBG
-- SELECT LEFT(kode_ina_cbg, 1) as cmg, COUNT(*) FROM inacbg_tarif GROUP BY cmg ORDER BY cmg;

-- Check tarif untuk 1 kode CBG
-- SELECT kode_ina_cbg, regional, kelas_rs, tarif_kelas_1, tarif_kelas_2, tarif_kelas_3 
-- FROM inacbg_tarif WHERE kode_ina_cbg = 'K-1-14-III' ORDER BY regional, kelas_rs;
