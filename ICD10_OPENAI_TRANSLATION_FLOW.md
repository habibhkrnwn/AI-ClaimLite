# 🌐 ICD-10 OpenAI Translation & Selection Flow

## 📋 Overview

Fitur baru yang mengintegrasikan OpenAI untuk translate istilah medis umum ke terminology standar, kemudian mencari di database ICD-10, dan memungkinkan user memilih subcode spesifik sebelum generate analisis AI.

---

## 🔄 Complete Flow

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: User Input                                          │
│ ┌─────────────┐                                             │
│ │ Diagnosis   │ "radang paru paru bakteri"                 │
│ │ Tindakan    │ "ultrasound"                               │
│ │ Obat        │ "panadol"                                   │
│ └─────────────┘                                             │
│                                                              │
│ [✨ Generate AI Insight] ← User clicks                      │
└─────────────────────────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: OpenAI Translation                                  │
│                                                              │
│ Request:                                                     │
│   POST /api/ai/translate-medical-term                       │
│   Body: { "term": "radang paru paru bakteri" }             │
│                                                              │
│ Backend calls:                                               │
│   POST http://localhost:8000/api/lite/translate-medical    │
│                                                              │
│ OpenAI Prompt:                                               │
│   "Translate Indonesian/colloquial term to medical English" │
│   Examples:                                                  │
│   - "paru2 basah" → "pneumonia"                            │
│   - "radang paru paru bakteri" → "bacterial pneumonia"     │
│   - "pneumonia cacar air" → "varicella pneumonia"          │
│                                                              │
│ Response:                                                    │
│   {                                                          │
│     "medical_term": "bacterial pneumonia",                  │
│     "confidence": "high"                                     │
│   }                                                          │
└─────────────────────────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: ICD-10 Smart Filtering                             │
│                                                              │
│ Input: "bacterial pneumonia" (from OpenAI)                  │
│ Words: ["bacterial", "pneumonia"] (2 words)                 │
│                                                              │
│ SQL Query (Multi-word AND logic):                           │
│   SELECT ...                                                 │
│   WHERE LOWER(name) LIKE '%bacterial%'                      │
│     AND LOWER(name) LIKE '%pneumonia%'                      │
│   GROUP BY head_code                                         │
│                                                              │
│ Results:                                                     │
│   J15 - Bacterial pneumonia, not elsewhere classified       │
│       ├─ J15.0 Klebsiella pneumoniae                        │
│       ├─ J15.1 Pseudomonas                                  │
│       ├─ J15.2 Staphylococcus                               │
│       ├─ J15.3 Streptococcus, group B                       │
│       ├─ J15.4 Other streptococci                           │
│       ├─ J15.5 Escherichia coli                             │
│       ├─ J15.6 Other aerobic Gram-negative bacteria         │
│       ├─ J15.7 Mycoplasma pneumoniae                        │
│       ├─ J15.8 Other bacterial pneumonia                    │
│       └─ J15.9 Bacterial pneumonia, unspecified             │
└─────────────────────────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: ICD-10 Explorer Displayed                          │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Header: "radang paru paru bakteri"                   │   │
│ │         → ✨ "bacterial pneumonia"                   │   │
│ ├──────┬──────────┬──────────────────────────────────┐│   │
│ │Input │Categories│ Details                          ││   │
│ │      │          │                                   ││   │
│ │radang│● J15 (10)│ □ J15.0 Klebsiella pneumoniae   ││   │
│ │paru  │          │ □ J15.1 Pseudomonas              ││   │
│ │paru  │          │ □ J15.2 Staphylococcus           ││   │
│ │bakter│          │ □ J15.3 Streptococcus, group B   ││   │
│ │      │          │ □ J15.4 Other streptococci       ││   │
│ │      │          │ □ J15.5 Escherichia coli         ││   │
│ │      │          │ □ J15.6 Other Gram-negative      ││   │
│ │      │          │ □ J15.7 Mycoplasma pneumoniae    ││   │
│ │      │          │ □ J15.8 Other bacterial          ││   │
│ │      │          │ □ J15.9 Unspecified              ││   │
│ └──────┴──────────┴──────────────────────────────────┘│   │
│                                                              │
│ User clicks: J15.2 (Staphylococcus)                        │
└─────────────────────────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Code Selected - Visual Update                      │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Header: "radang paru paru bakteri"                   │   │
│ │         → ✨ "bacterial pneumonia"                   │   │
│ │         Kode Terpilih: ✓ J15.2                      │   │
│ ├──────┬──────────┬──────────────────────────────────┐│   │
│ │Input │Categories│ Details                          ││   │
│ │      │          │                                   ││   │
│ │      │● J15     │ □ J15.0 Klebsiella               ││   │
│ │      │          │ □ J15.1 Pseudomonas              ││   │
│ │      │          │ ✓ J15.2 Staphylococcus ◄─────────││   │
│ │      │          │   🔵 SELECTED (cyan border)      ││   │
│ │      │          │ □ J15.3 Streptococcus            ││   │
│ │      │          │ □ J15.4 Other streptococci       ││   │
│ └──────┴──────────┴──────────────────────────────────┘│   │
└─────────────────────────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Generate AI Analysis with Selected Code            │
│                                                              │
│ handleCodeSelection("J15.2", "Staphylococcus pneumonia")   │
│                                                              │
│ Request:                                                     │
│   POST /api/ai/analyze                                      │
│   Body: {                                                    │
│     "mode": "form",                                         │
│     "diagnosis": "radang paru paru bakteri",               │
│     "procedure": "ultrasound",                              │
│     "medication": "panadol"                                 │
│   }                                                          │
│                                                              │
│ Analysis Result uses selected ICD-10 code:                  │
│   classification: {                                          │
│     icd10: ["J15.2"] ← User-selected code                  │
│   }                                                          │
│                                                              │
│ Display:                                                     │
│   📋 Klasifikasi & Coding                                   │
│   ICD-10: J15.2 - Staphylococcus pneumonia (User selected) │
│   ICD-9: ...                                                 │
│                                                              │
│   ✅ Validasi Klinis Cepat                                  │
│   "Pneumonia bakteri stafilokokus terdeteksi..."           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture

### Backend Components

#### 1. Core Engine (Python FastAPI)
**File:** `/core_engine/lite_endpoints.py`

```python
def endpoint_translate_medical(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translate colloquial medical term using OpenAI GPT-3.5
    
    Prompt Engineering:
    - System: "You are a medical terminology expert"
    - User: Structured prompt with examples
    - Temperature: 0.3 (precise, less creative)
    - Max tokens: 200
    
    Response format: JSON
    {
        "medical_term": "bacterial pneumonia",
        "confidence": "high|medium|low",
        "alternatives": [...]
    }
    """
```

**Registered in:** `/core_engine/main.py`
```python
@app.post("/api/lite/translate-medical")
async def translate_medical_term(request: Request):
    ...
```

#### 2. Web Backend (Express/TypeScript)
**File:** `/web/server/routes/aiRoutes.ts`

```typescript
// Proxy endpoint to core_engine
router.post('/translate-medical-term', async (req, res) => {
  const { term } = req.body;
  
  // Call core_engine
  const response = await axios.post(
    'http://localhost:8000/api/lite/translate-medical',
    { term }
  );
  
  res.json({
    success: true,
    data: {
      original: term,
      translated: response.data.result.medical_term,
      confidence: response.data.result.confidence
    }
  });
});
```

#### 3. ICD-10 Service (Smart Filtering)
**File:** `/web/server/services/icd10Service.ts`

```typescript
export async function getICD10Categories(searchTerm: string) {
  const words = searchTerm.toLowerCase().split(/\s+/).filter(w => w.length > 2);
  
  if (words.length > 1) {
    // Multi-word: Specific search with AND logic
    const conditions = words.map((_, i) => `LOWER(name) LIKE $${i + 1}`).join(' AND ');
    // Returns only codes matching ALL words
  } else {
    // Single word: Broad search
    // Returns codes matching ANY occurrence
  }
}
```

### Frontend Components

#### 1. API Client
**File:** `/web/src/lib/api.ts`

```typescript
class ApiService {
  async translateMedicalTerm(term: string) {
    return this.request('/api/ai/translate-medical-term', {
      method: 'POST',
      body: JSON.stringify({ term }),
    });
  }
}
```

#### 2. Dashboard Component
**File:** `/web/src/components/AdminRSDashboard.tsx`

```typescript
const handleGenerate = async () => {
  // Step 1: Translate with OpenAI
  const translation = await apiService.translateMedicalTerm(inputTerm);
  setCorrectedTerm(translation.data.translated);
  setShowICD10Explorer(true);
  
  // Explorer will show automatically with corrected term
};

const handleCodeSelection = async (code: string, name: string) => {
  // Step 2: Generate analysis with selected code
  setSelectedICD10Code({ code, name });
  
  const response = await apiService.analyzeClaimAI({...});
  // Use selected code in results
};
```

#### 3. ICD-10 Explorer
**File:** `/web/src/components/ICD10Explorer.tsx`

```typescript
useEffect(() => {
  if (correctedTerm) {
    loadICD10Hierarchy(); // Fetch categories based on corrected term
  }
}, [correctedTerm]);

const handleSelectSubCode = (code, name) => {
  setSelectedSubCode(code);
  onCodeSelected?.(code, name); // Notify parent → trigger analysis
};
```

---

## 🎯 Key Features

### 1. **OpenAI Translation**
- **Input:** Colloquial/Indonesian terms
- **Output:** Standard medical terminology in English
- **Examples:**
  - "paru2 basah" → "pneumonia"
  - "radang paru paru bakteri" → "bacterial pneumonia"
  - "pneumonia cacar air" → "varicella pneumonia"
  - "demam berdarah" → "dengue hemorrhagic fever"

### 2. **Smart Filtering**
- **Single word:** Broad search (OR logic)
  - "pneumonia" → J12, J13, J14, J15, J18
- **Multi-word:** Specific search (AND logic)
  - "bacterial pneumonia" → J15 only
  - "varicella pneumonia" → B01.2 only

### 3. **User Selection**
- Clickable subcodes with visual feedback
- Selected code persists in state
- Used in final AI analysis instead of auto-detected code

### 4. **Two-Step Analysis**
1. **Translation + Exploration** → Show ICD-10 codes
2. **Selection + Analysis** → Generate full AI insights with selected code

---

## 🧪 Testing Examples

### Test Case 1: Bacterial Pneumonia
```
Input: "radang paru paru bakteri"

Step 1 - Translation:
  Request: POST /api/ai/translate-medical-term
  Body: { "term": "radang paru paru bakteri" }
  Response: { "medical_term": "bacterial pneumonia", "confidence": "high" }

Step 2 - ICD-10 Search:
  Query: "bacterial pneumonia" (2 words)
  SQL: WHERE name LIKE '%bacterial%' AND name LIKE '%pneumonia%'
  Results: J15 (10 subcodes)

Step 3 - User Selection:
  User clicks: J15.2 (Staphylococcus)
  
Step 4 - Analysis:
  ICD-10 in result: J15.2 (user-selected)
  Insight: "Pneumonia bakteri stafilokokus terdeteksi..."
```

### Test Case 2: Varicella Pneumonia
```
Input: "pneumonia cacar air"

Step 1 - Translation:
  Response: { "medical_term": "varicella pneumonia" }

Step 2 - ICD-10 Search:
  Query: "varicella pneumonia" (2 words)
  SQL: WHERE name LIKE '%varicella%' AND name LIKE '%pneumonia%'
  Results: B01 (1 category)
    ├─ B01.0 Varicella meningitis
    ├─ B01.1 Varicella encephalitis
    ├─ B01.2 Varicella pneumonia ← Correct!
    └─ B01.9 Varicella without complication

Step 3 - User Selection:
  User clicks: B01.2 (Varicella pneumonia)
  
Step 4 - Analysis:
  ICD-10: B01.2 (NOT B01.1 encephalitis!)
```

### Test Case 3: General Pneumonia
```
Input: "paru2 basah"

Step 1 - Translation:
  Response: { "medical_term": "pneumonia" }

Step 2 - ICD-10 Search:
  Query: "pneumonia" (1 word, general)
  SQL: WHERE name LIKE '%pneumonia%'
  Results: J12, J13, J14, J15, J18 (5 categories)

Step 3 - User Selection:
  User browses categories and picks specific type:
  - J12.3 (Human metapneumovirus)
  - OR J15.9 (Bacterial, unspecified)
  - OR J18.9 (Pneumonia, unspecified)
```

---

## 📊 Data Flow Diagram

```
┌──────────┐     OpenAI        ┌─────────────┐
│  User    │ ──Translation──►  │ Core Engine │
│  Input   │                   │ (Python)    │
└──────────┘                   └─────────────┘
     │                               │
     │                               ▼
     │                         "bacterial
     │                          pneumonia"
     │                               │
     ▼                               ▼
┌─────────────┐              ┌──────────────┐
│   Smart     │              │  PostgreSQL  │
│  Filtering  │ ◄─Query────  │ icd10_master │
│  (Service)  │              │   18,543     │
└─────────────┘              │    codes     │
     │                       └──────────────┘
     ▼
┌─────────────┐
│ ICD-10      │
│ Explorer    │  User clicks J15.2
│ (Frontend)  │ ──────────┐
└─────────────┘           │
     │                    ▼
     │             ┌──────────────┐
     │             │ Code         │
     │             │ Selection    │
     │             │ Handler      │
     │             └──────────────┘
     │                    │
     ▼                    ▼
┌─────────────┐     ┌──────────────┐
│  AI         │     │  Analysis    │
│  Analysis   │ ◄───│  API Call    │
│  (Core)     │     │  w/ Code     │
└─────────────┘     └──────────────┘
     │
     ▼
┌─────────────┐
│  Results    │
│  Panel      │  ICD-10: J15.2
│  (Frontend) │  Insight: "..."
└─────────────┘
```

---

## 🔧 Environment Setup

### Required Environment Variables

#### Core Engine (`.env`)
```bash
OPENAI_API_KEY=sk-proj-...
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aiclaimlite
```

#### Web Backend (`.env`)
```bash
CORE_ENGINE_URL=http://localhost:8000
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aiclaimlite
JWT_SECRET=your-secret-key
```

### Running the System

```bash
# Terminal 1: PostgreSQL
docker compose up -d postgres

# Terminal 2: Core Engine
cd core_engine
python main.py
# Running on http://localhost:8000

# Terminal 3: Web Backend + Frontend
cd web
npm run dev
# Backend: http://localhost:3001
# Frontend: http://localhost:5173
```

---

## 🐛 Troubleshooting

### Issue 1: Wrong ICD-10 Code Selected
**Problem:** Input "pneumonia cacar air" shows B01.1 (encephalitis) instead of B01.2 (pneumonia)

**Root Cause:** Old system auto-selected first subcode without filtering

**Solution:** Smart filtering with multi-word AND logic filters to correct HEAD, then user manually selects correct subcode

### Issue 2: Translation Not Working
**Problem:** Term not translating, shows original input

**Possible Causes:**
1. OpenAI API key not set → Check `.env` in `core_engine/`
2. Core engine not running → Start `python main.py` on port 8000
3. Network timeout → Check `axios` timeout settings (30s default)

**Debug:**
```bash
# Check core engine logs
curl -X POST http://localhost:8000/api/lite/translate-medical \
  -H "Content-Type: application/json" \
  -d '{"term": "radang paru paru"}'
```

### Issue 3: No Subcodes Appearing
**Problem:** Categories load but no details

**Possible Causes:**
1. HEAD code format wrong → Check regex `^[A-Z][0-9]{2}$`
2. Database missing subcodes → Verify `icd10_master` has `.0`, `.1`, etc.

**Debug:**
```sql
-- Check if B01 has subcodes
SELECT * FROM icd10_master 
WHERE code LIKE 'B01.%' 
ORDER BY code;
```

---

## 📝 API Endpoints

### 1. Translate Medical Term
```http
POST /api/ai/translate-medical-term
Content-Type: application/json
Authorization: Bearer {token}

{
  "term": "radang paru paru bakteri"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "original": "radang paru paru bakteri",
    "translated": "bacterial pneumonia",
    "confidence": "high"
  }
}
```

### 2. Get ICD-10 Hierarchy
```http
GET /api/ai/icd10-hierarchy?search=bacterial+pneumonia
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "search_term": "bacterial pneumonia",
    "categories": [
      {
        "headCode": "J15",
        "headName": "Bacterial pneumonia, not elsewhere classified",
        "count": 10,
        "details": [
          { "code": "J15.0", "name": "Pneumonia due to Klebsiella pneumoniae" },
          { "code": "J15.2", "name": "Pneumonia due to staphylococcus" }
        ]
      }
    ]
  }
}
```

### 3. Analyze with Selected Code
```http
POST /api/ai/analyze
Content-Type: application/json
Authorization: Bearer {token}

{
  "mode": "form",
  "diagnosis": "radang paru paru bakteri",
  "procedure": "ultrasound",
  "medication": "panadol"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "klasifikasi": {
      "diagnosis": "Bacterial pneumonia (J15.2)"
    },
    "insight_ai": "Pneumonia bakteri stafilokokus terdeteksi..."
  },
  "usage": { "used": 5, "remaining": 95, "limit": 100 }
}
```

---

## 🚀 Future Enhancements

### Phase 1 (Current)
- ✅ OpenAI translation
- ✅ Smart filtering (single vs multi-word)
- ✅ Clickable subcodes
- ✅ Visual selection feedback
- ✅ Analysis with selected code

### Phase 2 (Planned)
- [ ] Cache translations to reduce OpenAI costs
- [ ] Batch translation for multiple diagnoses
- [ ] Confidence-based filtering (only show high-confidence results)
- [ ] Alternative suggestions from OpenAI

### Phase 3 (Future)
- [ ] AI-recommended subcodes based on symptoms
- [ ] Learning from user selections
- [ ] Multi-language support (Indonesian, English, local dialects)
- [ ] Voice input for diagnosis

---

**Version:** 2.0  
**Last Updated:** November 14, 2025  
**Status:** ✅ Implemented & Ready for Testing
