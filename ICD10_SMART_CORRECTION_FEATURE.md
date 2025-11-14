# 🏥 Smart ICD-10 Correction & Hierarchy Explorer

## 📋 Overview

Fitur **Smart ICD-10 Correction** memungkinkan Admin RS untuk:
1. ✍️ Input diagnosis dalam **bahasa Indonesia informal** (contoh: "paru2 basah")
2. 🤖 **AI auto-correction** menjadi istilah medis standar ("pneumonia")
3. 📊 Melihat **HEAD categories ICD-10** yang relevan (J12, J13, J14, J15, J18)
4. 🔍 Eksplorasi **detail subcodes** dengan klik kategori (J12.0, J12.1, J12.2, dll)
5. 📄 Analisis lengkap ditampilkan di panel bawah

---

## 🎯 User Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. USER INPUT: "paru2 basah"                               │
│     (Panel Kiri - Form/Text Input)                          │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼ Klik "Generate AI Insight"
┌─────────────────────────────────────────────────────────────┐
│  2. AI CORRECTION: "pneumonia"                              │
│     (Ditampilkan di header dengan ikon ✨)                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼ Auto-fetch dari database icd10_master
┌─────────────────────────────────────────────────────────────┐
│  3. ICD-10 EXPLORER (3-Column Layout)                       │
│                                                              │
│  ┌──────────┬──────────────┬──────────────┐                │
│  │ Input    │ HEAD         │ DETAIL       │                │
│  │ Summary  │ Categories   │ Subcodes     │                │
│  ├──────────┼──────────────┼──────────────┤                │
│  │ Diagnosis│ ● J12 (6)    │ J12.0        │                │
│  │ paru2    │   J13 (1)    │ J12.1        │                │
│  │ basah    │   J14 (1)    │ J12.2        │                │
│  │          │   J15 (10)   │ J12.3 ← Human│                │
│  │ Tindakan │   J18 (3)    │ J12.8        │                │
│  │ ...      │              │ J12.9        │                │
│  └──────────┴──────────────┴──────────────┘                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼ Otomatis setelah AI selesai
┌─────────────────────────────────────────────────────────────┐
│  4. HASIL ANALISIS (Panel Bawah)                            │
│     - Klasifikasi ICD-10 & ICD-9                            │
│     - Validasi CP Nasional & Fornas                         │
│     - Severity & Consistency Score                          │
│     - AI Insight                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture

### Backend Components

#### 1. **ICD-10 Service** (`web/server/services/icd10Service.ts`)

**Functions:**
- `getICD10Hierarchy(searchTerm)` → Returns HEAD categories + subcodes
- `getICD10Categories(searchTerm)` → Returns HEAD codes only
- `getICD10Details(headCode)` → Returns subcodes for specific HEAD
- `searchICD10Codes(query)` → Fuzzy search across all codes

**Database Query Logic:**
```sql
-- Get HEAD categories matching "pneumonia"
WITH matched_codes AS (
  SELECT 
    code,
    name,
    CASE 
      WHEN code ~ '^[A-Z][0-9]{2}\.[0-9]' THEN SUBSTRING(code FROM 1 FOR 3)
      ELSE code
    END as head_code
  FROM icd10_master
  WHERE 
    LOWER(name) LIKE '%pneumonia%'
    AND validation_status = 'official'
)
SELECT 
  head_code,
  MIN(name) as head_name,
  COUNT(*) as count
FROM matched_codes
WHERE head_code ~ '^[A-Z][0-9]{2}$'
GROUP BY head_code
-- Result: J12 (6), J13 (1), J14 (1), J15 (10), J18 (3)
```

#### 2. **API Endpoints** (`web/server/routes/aiRoutes.ts`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/icd10-hierarchy?search={term}` | GET | Get full hierarchy (categories + details) |
| `/api/ai/icd10-details/{headCode}` | GET | Get subcodes for specific HEAD (e.g., J12) |
| `/api/ai/icd10-search?q={query}` | GET | Fuzzy search all ICD-10 codes |

**Example Response:**
```json
{
  "success": true,
  "data": {
    "search_term": "pneumonia",
    "categories": [
      {
        "headCode": "J12",
        "headName": "Viral pneumonia, not elsewhere classified",
        "count": 6,
        "details": [
          { "code": "J12.0", "name": "Adenoviral pneumonia" },
          { "code": "J12.1", "name": "Respiratory syncytial virus pneumonia" },
          { "code": "J12.2", "name": "Parainfluenza virus pneumonia" },
          { "code": "J12.3", "name": "Human metapneumovirus pneumonia" },
          { "code": "J12.8", "name": "Other viral pneumonia" },
          { "code": "J12.9", "name": "Viral pneumonia, unspecified" }
        ]
      },
      { "headCode": "J13", ... },
      { "headCode": "J15", ... }
    ],
    "total_categories": 5
  }
}
```

### Frontend Components

#### 1. **SmartInputPanel** (`web/src/components/SmartInputPanel.tsx`)

**Props:**
- `mode`: 'form' | 'text'
- `diagnosis`, `procedure`, `medication`, `freeText`
- `onGenerate(correctedTerm?)` → Callback dengan medical term

**State Management:**
```typescript
const [correctedTerm, setCorrectedTerm] = useState<string>('');
const [icd10Categories, setIcd10Categories] = useState<ICD10Category[]>([]);
const [selectedHeadCode, setSelectedHeadCode] = useState<string | null>(null);
const [selectedDetails, setSelectedDetails] = useState<ICD10Detail[]>([]);
const [showICD10Explorer, setShowICD10Explorer] = useState(false);
```

**Key Functions:**
- `handleGenerateWithCorrection()`:
  1. Call `translateToMedical(inputTerm)` → "paru2 basah" → "pneumonia"
  2. Call `apiService.getICD10Hierarchy("pneumonia")`
  3. Show ICD-10 Explorer UI
  4. Call `onGenerate(medicalTerm)` untuk analisis

#### 2. **ICD10CategoryPanel** (`web/src/components/ICD10CategoryPanel.tsx`)

**Features:**
- Display HEAD codes (J12, J13, J14)
- Show subcode count badge
- Click handler → update parent state
- Active state highlighting

**UI States:**
- Loading: Spinner + "Memuat kategori..."
- Empty: "Masukkan diagnosis dan klik Generate..."
- Populated: List of clickable categories

#### 3. **ICD10DetailPanel** (`web/src/components/ICD10DetailPanel.tsx`)

**Features:**
- Display subcodes for selected HEAD
- Badge indicators:
  - 🟢 `.0` = Primary/Specific
  - 🟡 `.9` = Unspecified
- Numbered list (1, 2, 3...)
- Legend explaining badge meanings

---

## 🔄 Data Flow

```
User Input                    Backend                    Database
─────────────────────────────────────────────────────────────────
1. "paru2 basah"
   │
   ▼ translateToMedical()
2. "pneumonia" ──────────────► GET /icd10-hierarchy ──► SELECT code
                               ?search=pneumonia          WHERE name LIKE '%pneumonia%'
                                                          GROUP BY head_code
   ◄──────────────────────────── JSON Response  ◄────── J12, J13, J14, J15, J18
3. ICD10Category[]
   │
   ▼ User clicks "J12"
4. selectedHeadCode = "J12" ──► GET /icd10-details/J12 ─► SELECT code, name
                                                           WHERE code LIKE 'J12.%'
   ◄──────────────────────────── JSON Response  ◄────── J12.0 ... J12.9
5. ICD10Detail[]
   │
   ▼ Display in DetailPanel
6. User sees subcodes
```

---

## 🎨 UI Layout

### Desktop (1920x1080)
```
┌──────────────────────────────────────────────────────────────┐
│ ┌─────────┬────────────────────────────────────────────────┐ │
│ │ Input   │               Header: AI Correction             │ │
│ │ Panel   │  "paru2 basah" → ✨ "pneumonia"                │ │
│ │         ├─────────────┬──────────────┬───────────────────┤ │
│ │ Mode:   │ Input       │ HEAD         │ DETAIL            │ │
│ │ [Form]  │ Summary     │ Categories   │ Subcodes          │ │
│ │ [Text]  │             │              │                   │ │
│ │         │ Diagnosis:  │ ● J12 (6)    │ 1. J12.0          │ │
│ │ Usage:  │ paru2 basah │   J13 (1)    │ 2. J12.1          │ │
│ │ 5/100   │             │   J14 (1)    │ 3. J12.2          │ │
│ │ ███░░   │ Tindakan:   │   J15 (10)   │ 4. J12.3 🟢       │ │
│ │         │ ...         │   J18 (3)    │ 5. J12.8          │ │
│ │         │             │              │ 6. J12.9 🟡       │ │
│ │ [Diag]  │ Obat:       │ (Click to    │                   │ │
│ │ [Proc]  │ ...         │  see detail) │ Legend:           │ │
│ │ [Med]   │             │              │ 🟢 Primary        │ │
│ │         │ ← Back      │              │ 🟡 Unspecified    │ │
│ │ Generate│             │              │                   │ │
│ └─────────┴─────────────┴──────────────┴───────────────────┘ │
│                                                                │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │                     Hasil Analisis AI                       │ │
│ │ ┌──────────────┬───────────────┬────────────────────────┐  │ │
│ │ │ Klasifikasi  │ Validasi      │ Severity              │  │ │
│ │ │ ICD-10: J12.3│ ✓ Sesuai CP   │ Sedang                │  │ │
│ │ │ ICD-9: ...   │ ✓ Sesuai Fornas│ Consistency: 85%     │  │ │
│ │ └──────────────┴───────────────┴────────────────────────┘  │ │
│ │ AI Insight: ...                                            │ │
│ └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## 🚀 Deployment Checklist

### 1. Database Migration (if needed)
```bash
# Verify icd10_master table exists and populated
docker compose exec postgres psql -U postgres -d aiclaimlite -c "SELECT COUNT(*) FROM icd10_master;"

# Expected: 18543 rows (from screenshot)
```

### 2. Environment Variables
```env
# .env in web/ directory
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aiclaimlite
DB_USER=postgres
DB_PASSWORD=your_password
CORE_ENGINE_URL=http://localhost:8000
```

### 3. Install Dependencies
```bash
cd web
npm install
```

### 4. Build & Start
```bash
# Development
npm run dev

# Production
npm run build
npm run start
```

---

## 📊 Testing Scenarios

### Test Case 1: Form Mode dengan Indonesian Input
```
Input:
  Diagnosis: paru2 basah
  Tindakan: rawat inap 5 hari
  Obat: antibiotik

Expected:
  1. AI Correction: "paru2 basah" → "pneumonia"
  2. Categories shown: J12, J13, J14, J15, J18
  3. Click J12 → Shows J12.0 to J12.9
  4. Analysis result with ICD-10: J12.3 (if "human pneumonia")
```

### Test Case 2: Text Mode dengan Complex Input
```
Input:
  "Pasien demam tinggi dengan paru-paru basah akibat virus, 
   diberikan terapi oksigen dan antibiotik ceftriaxone"

Expected:
  1. AI extracts: diagnosis = "pneumonia", medication = "ceftriaxone"
  2. Correction: "paru-paru basah" → "viral pneumonia"
  3. Categories: J12 (Viral pneumonia) highlighted
  4. Click J12 → J12.0, J12.1, ... J12.9
```

### Test Case 3: Edge Cases
```
1. Empty input → Button disabled
2. AI limit reached → Gray button + warning message
3. Network error → Alert with error message
4. No ICD-10 match → Empty state message
5. Multiple diagnosis terms → Shows combined categories
```

---

## 🔧 Troubleshooting

### Issue 1: "No categories found"
**Cause:** Search term tidak match dengan database
**Solution:**
```typescript
// Check if translation is correct
console.log('Corrected term:', correctedTerm);

// Verify database has data
SELECT * FROM icd10_master WHERE LOWER(name) LIKE '%pneumonia%' LIMIT 5;
```

### Issue 2: Categories load but no details
**Cause:** HEAD code regex not matching
**Solution:**
```sql
-- Verify code format in database
SELECT DISTINCT code FROM icd10_master WHERE code LIKE 'J12%' LIMIT 10;

-- Should return: J12, J12.0, J12.1, etc.
```

### Issue 3: AI correction returns original term
**Cause:** Dictionary mapping incomplete
**Solution:**
```typescript
// Extend dictionary in SmartInputPanel.tsx
const dictionary: Record<string, string> = {
  'paru paru basah': 'pneumonia',
  'paru basah': 'pneumonia',
  'radang paru': 'pneumonia',
  'infeksi paru': 'lung infection',
  // Add more mappings...
};
```

---

## 🎓 Future Enhancements

### Phase 2: Advanced Translation
- [ ] Integrate dengan `core_engine` untuk AI translation
- [ ] Cache translation results di localStorage
- [ ] Support multiple languages (EN, ID, medical terms)

### Phase 3: Enhanced UX
- [ ] Search bar di Category Panel
- [ ] Favorite/Recent codes bookmarking
- [ ] ICD-10 code autocomplete di input field
- [ ] Copy code to clipboard dengan single click

### Phase 4: Analytics
- [ ] Track most used ICD-10 codes per RS
- [ ] Suggest codes based on historical data
- [ ] Highlight frequently misclassified codes

---

## 📞 Support

Untuk pertanyaan atau issue:
1. Check troubleshooting section terlebih dahulu
2. Verify database connection dan data
3. Check browser console untuk error logs
4. Contact development team dengan:
   - Screenshot error
   - Input data yang digunakan
   - Expected vs actual result

---

**Version:** 1.0.0  
**Last Updated:** November 14, 2025  
**Author:** AI-ClaimLite Development Team
