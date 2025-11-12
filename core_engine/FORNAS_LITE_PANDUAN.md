# 📘 PANDUAN FORNAS LITE - AI-CLAIM

## 🎯 Ringkasan

FORNAS Lite Validator adalah modul untuk validasi obat terhadap diagnosis menggunakan database FORNAS dan AI reasoning (GPT-4o-mini).

---

## 📁 File yang Dibuat

### 1. `services/fornas_service.py`
**Fungsi**: Bridge service untuk compatibility dengan `lite_service.py`

**Fungsi utama**:
- `match_multiple_obat(obat_list)` → Match obat dengan database FORNAS
- `get_fornas_compliance_status(fornas_matched)` → Status compliance summary

### 2. `services/fornas_lite_service.py`
**Fungsi**: Main validator dengan AI reasoning

**Class**: `FornasLiteValidator`
**Method utama**: `validate_drugs_lite(drug_list, diagnosis_icd10, diagnosis_name)`

**Proses**:
1. Parse input obat (hapus dosis, rute)
2. Match dengan DB FORNAS (dapat `kelas_terapi`, `sumber_regulasi`)
3. AI validation (dapat `status_fornas`, `catatan_ai`)
4. Format output table

### 3. `test_fornas_lite.py`
**Fungsi**: Comprehensive test suite

**Test yang dilakukan**:
- Direct service test
- Endpoint test
- Integrated analysis test
- Edge cases test

---

## 📊 Output Format

```json
{
  "fornas_validation": [
    {
      "no": 1,
      "nama_obat": "Ceftriaxone",
      "kelas_terapi": "Antibiotik – Sefalosporin",  // DARI DB
      "status_fornas": "✅ Sesuai (Fornas)",         // DARI AI
      "catatan_ai": "Lini pertama pneumonia berat rawat inap.",  // DARI AI
      "sumber_regulasi": "FORNAS 2023 • PNPK Pneumonia 2020"    // DB + AI
    }
  ],
  "summary": {
    "total_obat": 2,
    "sesuai": 1,
    "perlu_justifikasi": 1,
    "non_fornas": 0
  }
}
```

---

## 🔧 Setup

### 1. Environment Variables (.env)

```bash
# Database FORNAS
DATABASE_URL=postgresql://user:password@localhost:5432/database_name

# OpenAI API Key
OPENAI_API_KEY=sk-...
```

### 2. Database Table Required

**Table**: `fornas_drugs`

**Kolom penting**:
- `obat_name` → Nama generik obat
- `kelas_terapi` → Kelas terapi (e.g., "Antibiotik – Sefalosporin")
- `sumber_regulasi` → Sumber (e.g., "FORNAS 2023")
- `kode_fornas` → Kode FORNAS
- `nama_obat_alias` → Alias names (JSON array)

---

## 🚀 Cara Penggunaan

### Option 1: Direct Service Call

```python
from services.fornas_lite_service import validate_fornas_lite

result = validate_fornas_lite(
    drug_list=["Ceftriaxone 1g IV", "Paracetamol 500mg"],
    diagnosis_icd10="J18.9",
    diagnosis_name="Pneumonia berat"
)

# Print hasil
for v in result["fornas_validation"]:
    print(f"{v['nama_obat']}: {v['status_fornas']}")
    print(f"  Catatan: {v['catatan_ai']}")
```

### Option 2: Standalone Endpoint

```python
from lite_endpoints import endpoint_validate_fornas

response = endpoint_validate_fornas({
    "diagnosis_icd10": "J18.9",
    "diagnosis_name": "Pneumonia berat",
    "obat": ["Ceftriaxone 1g IV", "Paracetamol 500mg"]
})

print(response)
```

### Option 3: Integrated Analysis

```python
from lite_endpoints import endpoint_analyze_single

response = endpoint_analyze_single({
    "mode": "form",
    "diagnosis": "Pneumonia berat (J18.9)",
    "tindakan": "Nebulisasi, Rontgen",
    "obat": "Ceftriaxone 1g IV, Paracetamol 500mg"
})

# FORNAS validation sudah included di response
fornas_result = response["result"]["fornas_validation"]
```

---

## 🧪 Testing

### Manual Test (setelah DB setup)

```bash
# Test 1: FORNAS service
cd core_engine
python -c "from services.fornas_service import match_multiple_obat; print(match_multiple_obat(['Ceftriaxone']))"

# Test 2: FORNAS Lite validator
python -c "from services.fornas_lite_service import validate_fornas_lite; print(validate_fornas_lite(['Ceftriaxone'], 'J18.9', 'Pneumonia'))"

# Test 3: Full test suite
python test_fornas_lite.py
```

---

## 💡 Konsep Penting

### Status FORNAS (dari AI)

| Status | Arti | Contoh |
|--------|------|--------|
| ✅ Sesuai (Fornas) | Obat di FORNAS DAN sesuai indikasi diagnosis (lini pertama) | Ceftriaxone untuk Pneumonia |
| ⚠️ Perlu Justifikasi | Obat di FORNAS tapi bukan lini pertama ATAU butuh kondisi khusus | Levofloxacin untuk Pneumonia (lini kedua) |
| ❌ Non-Fornas | Obat tidak terdaftar di FORNAS | Vitamin C untuk Pneumonia |

### Data Source

| Field | Source | Notes |
|-------|--------|-------|
| `nama_obat` | User input (parsed) | Dosis/rute dihapus |
| `kelas_terapi` | **Database FORNAS** | Langsung dari kolom DB |
| `sumber_regulasi` | **Database FORNAS + AI** | DB sebagai base, AI tambahkan PNPK/CP |
| `status_fornas` | **AI (GPT-4o-mini)** | AI reasoning |
| `catatan_ai` | **AI (GPT-4o-mini)** | AI reasoning |

---

## 💰 Biaya (Cost)

Menggunakan GPT-4o-mini:
- **~$0.00003 per obat**
- 3 obat = ~$0.0001
- 1000 obat = ~$0.03

Sangat murah untuk production use! ✅

---

## 📈 Integrasi dengan Lite Service

FORNAS Lite sudah **otomatis terintegrasi** dengan `analyze_lite_single()`:

```python
# Output dari analyze_lite_single() sekarang include:
{
  "klasifikasi": {...},
  "validasi_klinis": {...},
  "fornas_validation": [...],      // ← NEW
  "fornas_summary": {...},          // ← NEW
  "cp_ringkas": [...],
  "checklist_dokumen": [...],
  "insight_ai": "...",
  "konsistensi": {...}
}
```

---

## 🔮 Future Enhancement

1. **indikasi_fornas** → Tambahkan ke DB untuk validasi lebih akurat
2. **Restriction validation** → restriksi_penggunaan, FPKTP/FPKTL
3. **Batch validation** → Validate banyak claim sekaligus
4. **Caching** → Cache AI results untuk hemat biaya
5. **Multi-version FORNAS** → Support FORNAS 2022, 2023, dll

---

## ✅ Checklist Implementation

- [x] Create `fornas_service.py`
- [x] Create `fornas_lite_service.py`
- [x] Update `lite_service.py` (integration)
- [x] Update `lite_endpoints.py` (new endpoint)
- [x] Create test suite
- [x] Documentation
- [ ] Setup database (manual - butuh koneksi DB)
- [ ] Setup .env file (manual - butuh API key)
- [ ] Run end-to-end test (manual - setelah DB setup)

---

## 📞 Support

Jika ada error atau pertanyaan:

1. **Import Error** → Check DATABASE_URL dan OPENAI_API_KEY di .env
2. **Database Error** → Check table `fornas_drugs` ada dan populated
3. **AI Error** → Check OPENAI_API_KEY valid dan ada balance
4. **Empty Result** → Check obat name matching (gunakan nama generik)

---

**Author**: AI Assistant  
**Date**: 2025-11-11  
**Version**: 1.0.0  
**Project**: AI-Claim Lite - FORNAS Validation Module
