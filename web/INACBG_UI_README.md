# 💰 INACBG Panel - Frontend UI Documentation

## 📋 Overview

Panel UI untuk menampilkan hasil analisis INACBG (INA-CBG - Indonesia Case Base Groups) yang merupakan sistem pembayaran berdasarkan diagnosis dan prosedur medis.

## 🎯 Fitur Utama

### 1. **Kode CBG & Deskripsi**
- Menampilkan kode CBG lengkap (format: `I-4-10-I`)
- Deskripsi diagnosis dalam bahasa Indonesia
- Badge confidence level dengan warna dinamis:
  - 🟢 Hijau: Confidence ≥ 80%
  - 🟡 Kuning: Confidence 60-79%
  - 🔴 Merah: Confidence < 60%

### 2. **Informasi Tarif**
- **Tarif Utama**: Tarif sesuai kelas BPJS yang digunakan
- **Tarif Detail per Kelas**:
  - Kelas 1 (tertinggi)
  - Kelas 2 (menengah)
  - Kelas 3 (terendah)
- Kelas aktif ditandai dengan highlight khusus
- Format Rupiah otomatis (Rp 5.770.100)

### 3. **Breakdown CBG**
Menampilkan komponen pembentuk kode CBG:
- **CMG (Case Mix Group)**: Kategori sistem organ (e.g., "I" = Cardiovascular)
- **Case Type**: Jenis perawatan (e.g., "4" = Rawat Inap Bukan Prosedur)
- **Specific Code**: Kode spesifik diagnosis
- **Severity**: Tingkat keparahan (I, II, III)

### 4. **Klasifikasi**
Informasi administratif rumah sakit:
- Regional (zona geografis)
- Kelas RS (A, B, C, D)
- Tipe RS (Pemerintah/Swasta)
- Layanan (RI/RJ - Rawat Inap/Jalan)

### 5. **Detail Matching**
Informasi akurasi pencocokan:
- **Strategy**: Metode yang digunakan untuk matching (e.g., `diagnosis_only_empirical`)
- **Case Count**: Jumlah kasus referensi
- **Note**: Catatan detail persentase matching

### 6. **Peringatan (Warnings)**
Alert box kuning jika ada kondisi khusus:
- Prosedur diabaikan
- Data tidak lengkap
- Pencocokan tidak sempurna

## 🎨 Desain UI

### Color Scheme

**Dark Mode:**
- Background: Slate 800/900 dengan opacity
- Border: Cyan 500 dengan transparency
- Accent: Cyan 300-400
- Text: Slate 200-400

**Light Mode:**
- Background: White/Blue 50
- Border: Blue 100-200
- Accent: Blue 600-700
- Text: Gray 600-800

### Layout
- Grid responsif 2 kolom untuk breakdown & klasifikasi
- Card-based design dengan rounded corners
- Hover effects dengan shadow & scale transition
- Smooth color transitions (300ms)

## 📂 File Structure

```
web/src/components/
├── INACBGPanel.tsx          # Komponen utama panel INACBG
├── INACBGDemo.tsx            # Demo standalone dengan mock data
└── AdminRSDashboard.tsx      # Integrasi dengan dashboard utama

web/src/lib/
└── supabase.ts               # Interface TypeScript untuk INACBGResult
```

## 🔧 Integration

### 1. Import Component
```tsx
import INACBGPanel from './INACBGPanel';
import { INACBGResult } from '../lib/supabase';
```

### 2. State Management
```tsx
const [inacbgResult, setInacbgResult] = useState<INACBGResult | null>(null);
```

### 3. Render Panel
```tsx
<INACBGPanel result={inacbgResult} isDark={isDark} />
```

### 4. Toggle dengan Panel Lain
```tsx
const [resultViewMode, setResultViewMode] = useState<'analysis' | 'inacbg'>('analysis');

// Toggle buttons
<button onClick={() => setResultViewMode('analysis')}>Analisis Klinis</button>
<button onClick={() => setResultViewMode('inacbg')}>INACBG</button>

// Conditional rendering
{resultViewMode === 'analysis' ? (
  <ResultsPanel result={result} isDark={isDark} />
) : (
  <INACBGPanel result={inacbgResult} isDark={isDark} />
)}
```

## 📡 Backend Integration (Coming Soon)

### Expected API Endpoint
```
POST /api/inacbg/analyze
```

### Request Format
```json
{
  "icd10_code": "I21.0",
  "icd9_codes": ["87.44", "99.29"],
  "regional": "1",
  "kelas_rs": "B",
  "tipe_rs": "Pemerintah",
  "layanan": "RI"
}
```

### Response Format
```json
{
  "success": true,
  "cbg_code": "I-4-10-I",
  "description": "INFARK MYOKARD AKUT (RINGAN)",
  "tarif": 5770100.0,
  "tarif_detail": {
    "tarif_kelas_1": 5770100.0,
    "tarif_kelas_2": 5054300.0,
    "tarif_kelas_3": 4338400.0,
    "kelas_bpjs_used": 1
  },
  "breakdown": {
    "cmg": "I",
    "cmg_description": "Cardiovascular system",
    "case_type": "4",
    "case_type_description": "Rawat Inap Bukan Prosedur",
    "specific_code": "10",
    "severity": "I"
  },
  "matching_detail": {
    "strategy": "diagnosis_only_empirical",
    "confidence": 80,
    "case_count": 4,
    "note": "40.0% kasus I21.0 masuk CBG ini"
  },
  "classification": {
    "regional": "1",
    "kelas_rs": "B",
    "tipe_rs": "Pemerintah",
    "layanan": "RI"
  },
  "warnings": [
    "Prosedur diabaikan, menggunakan CBG yang paling umum untuk diagnosis ini"
  ]
}
```

### Integration Code (TODO - when backend ready)
```tsx
const handleGenerateAnalysis = async () => {
  // ... existing analysis code ...
  
  // Fetch INACBG data
  try {
    const inacbgResponse = await apiService.analyzeINACBG({
      icd10_code: selectedICD10Code.code,
      icd9_codes: result.classification.icd9,
      regional: "1",
      kelas_rs: "B",
      tipe_rs: "Pemerintah",
      layanan: "RI"
    });
    
    if (inacbgResponse.success) {
      setInacbgResult(inacbgResponse);
    }
  } catch (error) {
    console.error('INACBG analysis failed:', error);
    // Fallback to null or show error state
    setInacbgResult(null);
  }
};
```

## 🧪 Testing

### Demo Mode
Akses standalone demo dengan mock data:
```tsx
import INACBGDemo from './components/INACBGDemo';

// Render di router atau sebagai modal
<INACBGDemo />
```

### Mock Data
Current mock data dalam `AdminRSDashboard.tsx`:
- Diagnosis: Infark Myokard Akut (Ringan)
- CBG Code: I-4-10-I
- Tarif: Rp 5.770.100 (Kelas 1)
- Confidence: 80%

## 🎯 Next Steps

1. ✅ UI Design & Implementation - **DONE**
2. ✅ TypeScript Interface Definition - **DONE**
3. ✅ Integration with AdminRSDashboard - **DONE**
4. ⏳ Backend Service Development - **PENDING** (by teammate)
5. ⏳ API Integration - **PENDING** (after backend merge)
6. ⏳ Real Data Testing - **PENDING**
7. ⏳ Error Handling Enhancement - **PENDING**

## 📝 Notes

- UI sudah siap 100% dengan mock data
- Backend service sedang dikembangkan oleh tim backend
- Setelah backend di-merge, tinggal replace mock data dengan real API call
- Interface TypeScript sudah match dengan struktur JSON backend
- Responsive design sudah diimplementasikan
- Dark/Light mode support sudah lengkap

## 🤝 Contributors

- Frontend UI: [Your Name]
- Backend Service: [Teammate Name] - Coming Soon

---

**Status**: ✅ UI Ready | ⏳ Backend Pending | 🔄 Integration Scheduled
