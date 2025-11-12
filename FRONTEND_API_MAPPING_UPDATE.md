# Frontend API Mapping Update

## 📅 Tanggal Update: 12 November 2025

## 🎯 Tujuan
Menyesuaikan tampilan hasil analisis di Frontend agar sesuai dengan struktur response terbaru dari API `core_engine`.

---

## 🔄 Perubahan yang Dilakukan

### 1. **Struktur Response API Terbaru (core_engine)**

Berdasarkan `lite_service.py` dan `lite_endpoints.py`, struktur response API adalah:

```json
{
  "status": "success",
  "result": {
    "klasifikasi": {
      "diagnosis": "Pneumonia berat (J18.9)",
      "tindakan": ["Nebulisasi (93.96)", "Rontgen Thorax (87.44)"],
      "obat": ["Ceftriaxone injeksi 1g", "Paracetamol 500mg"],
      "confidence": "85%"
    },
    "validasi_klinis": {
      "sesuai_cp": true,
      "sesuai_fornas": true,
      "catatan": "Tindakan dan obat sesuai Clinical Pathway..."
    },
    "fornas_validation": [
      {
        "no": 1,
        "nama_obat": "Ceftriaxone",
        "kelas_terapi": "Antibiotik – Sefalosporin",
        "status_fornas": "✅ Sesuai (Fornas)",
        "catatan_ai": "Lini pertama pneumonia berat...",
        "sumber_regulasi": "FORNAS 2023 • PNPK Pneumonia 2020"
      }
    ],
    "fornas_summary": {
      "total_obat": 3,
      "sesuai": 2,
      "perlu_justifikasi": 1,
      "non_fornas": 0
    },
    "cp_ringkas": [
      {
        "tahap": "Tahap 1",
        "keterangan": "Diagnosis & Stratifikasi"
      }
    ],
    "checklist_dokumen": [
      "Resume Medis",
      "Hasil Radiologi",
      "Hasil Lab"
    ],
    "insight_ai": "Diagnosis pneumonia berat sudah sesuai...",
    "konsistensi": {
      "tingkat": 85,
      "detail": "Konsistensi tinggi antara diagnosis, tindakan, dan obat"
    },
    "metadata": {
      "claim_id": "LITE-20251112001",
      "timestamp": "2025-11-12T21:00:00",
      "mode": "form",
      "parsing_confidence": 0.92
    }
  }
}
```

### 2. **Mapping di AdminRSDashboard.tsx**

File yang diupdate: `/web/src/components/AdminRSDashboard.tsx`

#### Perubahan Utama:

**A. Ekstraksi ICD-10 Code**
```typescript
// SEBELUM (salah - mengharapkan field icd10 langsung)
icd10: aiResult.klasifikasi?.icd10 ? [aiResult.klasifikasi.icd10] : []

// SESUDAH (benar - ekstrak dari diagnosis text)
const diagnosisText = aiResult.klasifikasi?.diagnosis || '';
const icd10Match = diagnosisText.match(/\(([A-Z]\d{2}(?:\.\d{1,2})?)\)/);
const icd10Code = icd10Match ? icd10Match[1] : '';
```

**B. Ekstraksi ICD-9 Codes**
```typescript
// SEBELUM (salah - mengharapkan array langsung)
icd9: aiResult.klasifikasi?.icd9 ? [...] : []

// SESUDAH (benar - ekstrak dari tindakan array)
const tindakanArray = aiResult.klasifikasi?.tindakan || [];
const icd9Codes = tindakanArray
  .map((t: any) => {
    if (typeof t === 'string') {
      const match = t.match(/\((\d{2}\.\d{2})\)/);
      return match ? match[1] : null;
    }
    return null;
  })
  .filter((code: any) => code !== null);
```

**C. Status Validasi**
```typescript
// SEBELUM (salah - field tidak ada)
const validStatus = aiResult.validasi_klinis?.status?.toLowerCase();

// SESUDAH (benar - gunakan sesuai_cp dan sesuai_fornas)
const sesuaiCP = aiResult.validasi_klinis?.sesuai_cp;
const sesuaiFornas = aiResult.validasi_klinis?.sesuai_fornas;

if (sesuaiCP === false || sesuaiFornas === false) {
  validationStatus = 'invalid';
} else if (sesuaiCP === 'parsial' || sesuaiFornas === 'parsial') {
  validationStatus = 'warning';
}
```

**D. Severity Level**
```typescript
// SEBELUM (salah - field severity.tingkat tidak ada)
const severityTingkat = aiResult.severity?.tingkat?.toLowerCase();

// SESUDAH (benar - gunakan konsistensi.tingkat)
const konsistensiTingkat = aiResult.konsistensi?.tingkat || 70;
if (konsistensiTingkat >= 80) {
  severityLevel = 'ringan';
} else if (konsistensiTingkat < 60) {
  severityLevel = 'berat';
}
```

**E. Fornas Status**
```typescript
// SEBELUM (salah - field tingkat_kepatuhan tidak ada)
const fornasKepatuhan = aiResult.fornas?.tingkat_kepatuhan || 100;

// SESUDAH (benar - gunakan fornas_summary)
const fornasSummary = aiResult.fornas_summary || {};
const sesuaiCount = fornasSummary.sesuai || 0;
const totalObat = fornasSummary.total_obat || 1;
const fornasPercentage = (sesuaiCount / totalObat) * 100;
```

**F. CP Ringkas Formatting**
```typescript
// SEBELUM (salah - struktur berbeda)
cpNasional: aiResult.cp_ringkas?.map((item: any) => 
  `${item.nama_tindakan}: ${item.tarif_ringkas}`
).join(', ') || '-'

// SESUDAH (benar - handle berbagai format)
const cpRingkasText = Array.isArray(aiResult.cp_ringkas) 
  ? aiResult.cp_ringkas.map((item: any) => {
      if (typeof item === 'string') return item;
      return `${item.tahap || item.stage_name || ''}: ${item.keterangan || item.description || ''}`;
    }).join(' • ')
  : (typeof aiResult.cp_ringkas === 'string' ? aiResult.cp_ringkas : '-');
```

**G. Required Documents**
```typescript
// SEBELUM (salah - field nama_dokumen tidak selalu ada)
requiredDocs: aiResult.checklist_dokumen?.map((doc: any) => doc.nama_dokumen) || []

// SESUDAH (benar - handle berbagai format)
const requiredDocs = Array.isArray(aiResult.checklist_dokumen)
  ? aiResult.checklist_dokumen.map((doc: any) => {
      if (typeof doc === 'string') return doc;
      return doc.nama_dokumen || doc.document || doc.name || '';
    }).filter((d: string) => d)
  : [];
```

---

## 🧪 Testing

### Test Case 1: Form Mode
**Input:**
- Diagnosis: `Pneumonia berat (J18.9)`
- Tindakan: `Nebulisasi (93.96), Rontgen Thorax (87.44)`
- Obat: `Ceftriaxone injeksi 1g, Paracetamol 500mg`

**Expected Result:**
- ICD-10: `["J18.9"]`
- ICD-9: `["93.96", "87.44"]`
- Validation status: Berdasarkan `sesuai_cp` dan `sesuai_fornas`
- Fornas percentage: Dihitung dari `fornas_summary`

### Test Case 2: Text Mode
**Input:**
```
Pasien Pneumonia berat (J18.9) dengan saturasi oksigen rendah. 
Diberikan Ceftriaxone 2x1g IV, Azithromycin 1x500mg PO, 
dan terapi oksigen nasal kanul 3 liter/menit.
```

**Expected Result:**
- AI akan parse otomatis ke diagnosis, tindakan, obat
- Response structure sama dengan Form Mode

---

## 📝 Debugging

### Console Logs yang Ditambahkan

```typescript
console.log('[AdminRS] Full AI Result:', JSON.stringify(aiResult, null, 2));
```

Untuk melihat struktur lengkap response dari API dan memudahkan debugging.

### Cara Melihat Logs:
1. Buka Developer Console di browser (F12)
2. Filter dengan keyword: `[AdminRS]`
3. Lihat struktur `Full AI Result` untuk memastikan mapping benar

---

## 🔧 Cara Menjalankan

### 1. Backend (core_engine)
```bash
cd core_engine
python main.py
# atau
uvicorn main:app --reload --port 8003
```

### 2. Web Backend (Express)
```bash
cd web
npm run dev
```

Frontend akan running di `http://localhost:5173`
Backend API akan running di `http://localhost:3001`

---

## ✅ Checklist Verifikasi

- [x] Response API structure documented
- [x] Frontend mapping updated di `AdminRSDashboard.tsx`
- [x] ICD-10 extraction fixed (regex dari diagnosis text)
- [x] ICD-9 extraction fixed (regex dari tindakan array)
- [x] Validation status mapping fixed (sesuai_cp, sesuai_fornas)
- [x] Severity calculation fixed (konsistensi.tingkat)
- [x] Fornas status calculation fixed (fornas_summary)
- [x] CP Ringkas formatting flexible
- [x] Required docs formatting flexible
- [x] Debug console logs added

---

## 📚 File yang Dimodifikasi

1. **`/web/src/components/AdminRSDashboard.tsx`**
   - Updated response mapping logic
   - Added console.log for debugging
   - Fixed all field extractions

2. **`/core_engine/main.py`** (sebelumnya)
   - Added `reload_excludes` untuk mencegah infinite reload

---

## 🚀 Next Steps

1. ✅ Test dengan real API call
2. ✅ Verify semua field ditampilkan dengan benar
3. ⬜ (Optional) Tambahkan table view untuk `fornas_validation` array
4. ⬜ (Optional) Tambahkan export to PDF/Excel feature

---

## 📞 Support

Jika ada masalah:
1. Check console logs di browser (F12)
2. Check core_engine logs di terminal
3. Verify API response structure dengan Postman/curl
4. Pastikan `CORE_ENGINE_URL` di `.env` sudah benar

---

**Last Updated:** 2025-11-12 21:15 WIB
