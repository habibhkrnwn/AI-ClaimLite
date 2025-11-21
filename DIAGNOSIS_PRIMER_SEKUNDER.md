# 🏥 Fitur Diagnosis Primer & Sekunder - AI Translation

## 📋 Overview

Fitur baru yang memungkinkan sistem mendeteksi **diagnosis primer (utama)** dan **diagnosis sekunder (tambahan)** dari input teks dengan:

✅ **Multi-diagnosis detection** dengan berbagai separator  
✅ **AI translation** untuk bahasa colloquial dan typo  
✅ **Automatic priority ordering** (pertama = primer)  
✅ **ICD-10 code mapping** untuk setiap diagnosis  
✅ **Support untuk free text dan form mode**

---

## 🎯 Fitur Utama

### 1. **Multi-Diagnosis Detection**

Sistem dapat memisahkan multiple diagnosis dengan berbagai separator:

| Separator | Contoh Input | Hasil Detection |
|-----------|--------------|-----------------|
| Koma `,` | `Pneumonia, Diabetes` | Primer: Pneumonia<br>Sekunder: Diabetes |
| Titik `.` | `Pneumonia. Heart Disease` | Primer: Pneumonia<br>Sekunder: Heart Disease |
| Ampersand `&` | `Pneumonia & Diabetes` | Primer: Pneumonia<br>Sekunder: Diabetes |
| Slash `/` | `Pneumonia / Diabetes` | Primer: Pneumonia<br>Sekunder: Diabetes |
| Kata "dan" | `Pneumonia dan Diabetes` | Primer: Pneumonia<br>Sekunder: Diabetes |
| Kata "dengan" | `Pneumonia dengan Heart Disease` | Primer: Pneumonia<br>Sekunder: Heart Disease |
| Kata "disertai" | `Pneumonia disertai komplikasi` | Primer: Pneumonia<br>Sekunder: Komplikasi |

### 2. **AI Translation & Typo Correction**

AI akan otomatis menerjemahkan bahasa colloquial dan memperbaiki typo:

| Input (Bahasa Awam/Typo) | Output (Medical Term) |
|---------------------------|----------------------|
| `paru2 basah` | `Pneumonia` |
| `radang paru` | `Pneumonia` |
| `kencing manis` | `Diabetes Mellitus` |
| `jantung koroner` | `Coronary Heart Disease` |
| `demam berdarah` | `Dengue Hemorrhagic Fever` |
| `tipus` | `Typhoid Fever` |
| `asam urat` | `Gout` |
| `darah tinggi` | `Hypertension` |
| `jantung bengkak` | `Heart Failure` |

### 3. **Priority Ordering**

**Rule:** Diagnosis yang **PERTAMA** disebut = **DIAGNOSIS PRIMER**

**Contoh:**

```
Input: "Pneumonia, Diabetes, Hypertension"

Output:
✅ Diagnosis Primer: Pneumonia
✅ Diagnosis Sekunder:
   - Diabetes
   - Hypertension
```

### 4. **ICD-10 Code Detection**

Sistem dapat mendeteksi kode ICD-10 di dalam kurung untuk setiap diagnosis:

```
Input: "Pneumonia (J18.9), Diabetes (E11.9), Heart Disease"

Output:
✅ Diagnosis Primer: 
   - Name: Pneumonia
   - ICD-10: J18.9

✅ Diagnosis Sekunder:
   1. Name: Diabetes
      ICD-10: E11.9
   
   2. Name: Heart Disease
      ICD-10: null (akan di-lookup otomatis)
```

---

## 🔧 Cara Penggunaan

### Mode 1: **Free Text** (Narrative)

**Input bebas**, bisa berupa paragraf resume medis:

```json
POST /api/lite/analyze/single
{
  "mode": "text",
  "input_text": "Pasien didiagnosa paru2 basah dengan komplikasi kencing manis dan darah tinggi. Diberikan antibiotik dan nebulisasi."
}
```

**Output:**

```json
{
  "klasifikasi": {
    "diagnosis_primer": {
      "name": "Pneumonia",
      "icd10": null
    },
    "diagnosis_sekunder": [
      {
        "name": "Diabetes Mellitus",
        "icd10": null
      },
      {
        "name": "Hypertension",
        "icd10": null
      }
    ]
  }
}
```

### Mode 2: **Form Input** (Structured)

**Input terstruktur** dengan field diagnosis terpisah:

```json
POST /api/lite/analyze/single
{
  "mode": "form",
  "diagnosis": "paru2 basah, kencing manis & jantung koroner",
  "tindakan": "Nebulisasi, Rontgen Thorax",
  "obat": "Ceftriaxone, Paracetamol",
  "service_type": "rawat-inap"
}
```

**Output:**

```json
{
  "klasifikasi": {
    "diagnosis_primer": {
      "name": "Pneumonia",
      "icd10": "J18.9"  // Auto-matched
    },
    "diagnosis_sekunder": [
      {
        "name": "Diabetes Mellitus",
        "icd10": "E11.9"
      },
      {
        "name": "Coronary Heart Disease",
        "icd10": "I25.9"
      }
    ]
  }
}
```

---

## 📊 Response Format

### **New Fields** in `klasifikasi` object:

```typescript
{
  "klasifikasi": {
    // ✅ NEW: Primary diagnosis
    "diagnosis_primer": {
      "name": "Pneumonia",
      "icd10": "J18.9" | null
    },
    
    // ✅ NEW: Secondary diagnoses (array)
    "diagnosis_sekunder": [
      {
        "name": "Diabetes Mellitus",
        "icd10": "E11.9" | null
      },
      {
        "name": "Hypertension",
        "icd10": "I10" | null
      }
    ],
    
    // 🔄 DEPRECATED (untuk backward compatibility)
    "diagnosis": "Pneumonia, Diabetes Mellitus, Hypertension",
    "diagnosis_icd10": "J18.9",  // ICD-10 dari primer
    
    "tindakan": [...],
    "obat": [...]
  }
}
```

### **Backward Compatibility**

Field lama (`diagnosis`, `diagnosis_icd10`) **tetap ada** untuk kompatibilitas dengan kode existing:

- `diagnosis`: Gabungan primer + sekunder (separated by comma)
- `diagnosis_icd10`: Kode ICD-10 dari diagnosis **primer**

---

## 🎨 UI Display (Frontend)

### **Tampilan di ResultsPanel:**

```tsx
{/* DIAGNOSIS PRIMER */}
<div className="diagnosis-primer">
  <span className="badge">DIAGNOSIS PRIMER (Utama)</span>
  <div className="diagnosis-card">
    <span className="name">Pneumonia</span>
    <span className="icd10-badge">ICD-10: J18.9</span>
  </div>
</div>

{/* DIAGNOSIS SEKUNDER */}
<div className="diagnosis-sekunder">
  <span className="badge">DIAGNOSIS SEKUNDER (2)</span>
  
  <div className="diagnosis-card">
    <span className="number">#1</span>
    <span className="name">Diabetes Mellitus</span>
    <span className="icd10-badge">E11.9</span>
  </div>
  
  <div className="diagnosis-card">
    <span className="number">#2</span>
    <span className="name">Hypertension</span>
    <span className="icd10-badge">I10</span>
  </div>
</div>
```

---

## 🧪 Contoh Test Cases

### **Test Case 1: Bahasa Indonesia Colloquial**

```
Input: "paru2 basah, kencing manis & jantung"

Expected Output:
✅ Primer: Pneumonia
✅ Sekunder: [Diabetes Mellitus, Heart Disease]
```

### **Test Case 2: Mixed Separator**

```
Input: "Pneumonia (J18.9) / Diabetes. Hypertension"

Expected Output:
✅ Primer: Pneumonia (J18.9)
✅ Sekunder: [Diabetes, Hypertension]
```

### **Test Case 3: Free Text Narrative**

```
Input: "Pasien dengan radang paru disertai komplikasi kencing manis dan darah tinggi"

Expected Output:
✅ Primer: Pneumonia
✅ Sekunder: [Diabetes Mellitus, Hypertension]
```

### **Test Case 4: Form Input dengan Kata "dengan"**

```
Input: "Pneumonia dengan komplikasi heart failure"

Expected Output:
✅ Primer: Pneumonia
✅ Sekunder: [Heart Failure]
```

### **Test Case 5: Single Diagnosis**

```
Input: "Pneumonia (J18.9)"

Expected Output:
✅ Primer: Pneumonia (J18.9)
✅ Sekunder: []  // Empty array
```

---

## ⚙️ AI Prompt Engineering

### **System Prompt Key Rules:**

```
1. DETEKSI MULTIPLE DIAGNOSIS:
   - Separator: , . & / "dan" "dengan" "disertai"
   - PERTAMA = PRIMER, sisanya = SEKUNDER

2. AI TRANSLATION WAJIB:
   - "paru2 basah" → "Pneumonia"
   - "kencing manis" → "Diabetes Mellitus"
   - Handle typo dan abbreviation

3. DETEKSI KODE ICD-10:
   - Extract dari kurung: "Pneumonia (J18.9)" → J18.9
   - Bisa ada di setiap diagnosis (primer/sekunder)
```

### **Prompt Example (Mode: Text):**

```
INPUT: "paru2 basah, kencing manis & jantung koroner"

INSTRUKSI:
- Pisahkan diagnosis dengan separator: , & /
- Yang PERTAMA = DIAGNOSIS PRIMER
- Sisanya = DIAGNOSIS SEKUNDER
- AI Translation:
  * "paru2 basah" → "Pneumonia"
  * "kencing manis" → "Diabetes Mellitus"
  * "jantung koroner" → "Coronary Heart Disease"

OUTPUT JSON:
{
  "diagnosis_primer": {"name": "Pneumonia", "icd10": null},
  "diagnosis_sekunder": [
    {"name": "Diabetes Mellitus", "icd10": null},
    {"name": "Coronary Heart Disease", "icd10": null}
  ]
}
```

---

## 📝 Code Changes Summary

### **Backend (Python):**

1. **`core_engine/services/lite_service.py`:**
   - ✅ Updated `_get_system_prompt()` dengan multi-diagnosis rules
   - ✅ Updated `_build_prompt()` untuk mode text & form
   - ✅ Updated `_validate_and_normalize()` untuk support `diagnosis_primer` & `diagnosis_sekunder`
   - ✅ Added AI translation dictionary (paru2 basah → Pneumonia, dll)

2. **`core_engine/services/lite_service.py` - analyze_lite_single():**
   - ✅ Added `diagnosis_primer` & `diagnosis_sekunder` to `klasifikasi` object
   - ✅ Backward compatible with existing `diagnosis` field

### **Frontend (TypeScript/React):**

1. **`web/src/lib/supabase.ts`:**
   - ✅ Added `DiagnosisItem` interface
   - ✅ Updated `AnalysisResult.classification` dengan `diagnosis_primer?` & `diagnosis_sekunder?`

2. **`web/src/components/ResultsPanel.tsx`:**
   - ✅ Added diagnosis primer/sekunder display section
   - ✅ Styled with gradient background & badges
   - ✅ Shows ICD-10 codes for each diagnosis

---

## 🚀 Deployment Checklist

- [x] Update backend system prompt dengan multi-diagnosis detection
- [x] Update backend validation untuk diagnosis_primer & diagnosis_sekunder
- [x] Update backend response mapping (`klasifikasi` object)
- [x] Update frontend TypeScript interfaces
- [x] Update frontend UI component (ResultsPanel)
- [x] Create documentation (this file)
- [ ] Test with real data (various separator combinations)
- [ ] Test AI translation (bahasa colloquial → medical terms)
- [ ] Test backward compatibility (existing code still works)
- [ ] Update test cases in `test_*.py` files

---

## 🔍 Testing Commands

### **Test Free Text Mode:**

```bash
curl -X POST http://localhost:8000/api/lite/analyze/single \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "text",
    "input_text": "paru2 basah, kencing manis & jantung koroner"
  }'
```

### **Test Form Mode:**

```bash
curl -X POST http://localhost:8000/api/lite/analyze/single \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "form",
    "diagnosis": "Pneumonia (J18.9), Diabetes & Hypertension",
    "tindakan": "Nebulisasi",
    "obat": "Ceftriaxone",
    "service_type": "rawat-inap"
  }'
```

---

## 📊 Expected AI Cost Impact

- **Before:** ~$0.0002 per analysis (single diagnosis)
- **After:** ~$0.0003 per analysis (multi-diagnosis + translation)
- **Increase:** ~50% cost increase for multi-diagnosis cases
- **Benefit:** More accurate clinical analysis with multiple diagnoses

---

## 🎓 Best Practices

1. **Always use AI translation** - Jangan hardcode mapping Indonesia → English
2. **Support all common separators** - , . & / dan dengan disertai
3. **First diagnosis = Primary** - Rule sederhana untuk priority
4. **ICD-10 detection per diagnosis** - Bukan hanya untuk primer
5. **Backward compatible** - Field lama tetap ada untuk existing code

---

## 📞 Support

Untuk pertanyaan atau issue:
- Check dokumentasi di `QUICKSTART.md`
- Review test cases di `test_*.py` files
- Check logs di `core_engine/logs/`

---

**Last Updated:** 2024-11-21  
**Version:** 1.0  
**Author:** AI-ClaimLite Development Team
