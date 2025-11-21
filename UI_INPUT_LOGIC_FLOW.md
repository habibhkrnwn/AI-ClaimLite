# 🎯 UI Input 3 Field - Logic Flow & Cara Menambahkan Field Baru

## 📊 Current Architecture (3 Fields)

### **Field yang Ada Saat Ini:**
1. **Diagnosis** - Diagnosis penyakit
2. **Tindakan** (Procedure) - Tindakan medis yang dilakukan
3. **Obat** (Medication) - Obat yang diberikan

---

## 🔄 Logic Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                          │
│              AdminRSDashboard.tsx                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├── State Management (useState)
                            │   ├── diagnosis: string
                            │   ├── procedure: string
                            │   └── medication: string
                            │
                            ├── Props passed to SmartInputPanel
                            │   ├── diagnosis
                            │   ├── procedure
                            │   ├── medication
                            │   ├── onDiagnosisChange
                            │   ├── onProcedureChange
                            │   └── onMedicationChange
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               SmartInputPanel.tsx                            │
│          (Render 3 Input Fields + Button)                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ User clicks "Generate"
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│            handleGenerate() Function                         │
│  - Validate inputs (all 3 fields required)                  │
│  - Call API translation for diagnosis & procedure           │
│  - Show ICD-10 Explorer (diagnosis)                         │
│  - Show ICD-9 Explorer (procedure)                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ User selects ICD codes
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│        handleGenerateAnalysis() Function                     │
│  - Prepare requestData with 3 fields                        │
│  - Call apiService.analyzeClaimAI()                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               BACKEND (Express.js)                           │
│              web/server/routes/aiRoutes.ts                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├── Validate: diagnosis, procedure, medication
                            │
                            ├── Prepare payload:
                            │   {
                            │     mode: 'form',
                            │     diagnosis: string,
                            │     tindakan: string,  ← procedure renamed
                            │     obat: string,      ← medication renamed
                            │     icd10_code: string,
                            │     icd9_code: string
                            │   }
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           CORE ENGINE (FastAPI - Python)                     │
│        core_engine/lite_endpoints.py                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├── Parse payload:
                            │   - diagnosis → diagnosis_name
                            │   - tindakan → tindakan_list
                            │   - obat → obat_list
                            │
                            ├── Call analyze_lite_single()
                            │
                            ├── Return JSON result with 6 panels:
                            │   - klasifikasi
                            │   - validasi_klinis
                            │   - cp_ringkas
                            │   - checklist_dokumen
                            │   - konsistensi
                            │   - insight_ai
                            │
                            ▼
                        Display Results
```

---

## 📝 Code Structure

### 1. **Frontend State (AdminRSDashboard.tsx)**

**Lokasi:** `web/src/components/AdminRSDashboard.tsx` (Lines 22-24)

```tsx
const [diagnosis, setDiagnosis] = useState('');
const [procedure, setProcedure] = useState('');
const [medication, setMedication] = useState('');
```

---

### 2. **Form Input Component (SmartInputPanel.tsx)**

**Lokasi:** `web/src/components/SmartInputPanel.tsx` (Lines 85-147)

```tsx
// Props interface
interface SmartInputPanelProps {
  diagnosis: string;
  procedure: string;
  medication: string;
  onDiagnosisChange: (value: string) => void;
  onProcedureChange: (value: string) => void;
  onMedicationChange: (value: string) => void;
  // ... other props
}

// Render 3 input fields
<div className="space-y-2">
  <label>Diagnosis</label>
  <input
    value={diagnosis}
    onChange={(e) => onDiagnosisChange(e.target.value)}
    placeholder="Masukkan diagnosis..."
  />
</div>

<div className="space-y-2">
  <label>Tindakan</label>
  <input
    value={procedure}
    onChange={(e) => onProcedureChange(e.target.value)}
    placeholder="Masukkan tindakan medis..."
  />
</div>

<div className="space-y-2">
  <label>Obat</label>
  <input
    value={medication}
    onChange={(e) => onMedicationChange(e.target.value)}
    placeholder="Masukkan daftar obat..."
  />
</div>
```

---

### 3. **Validation Logic (SmartInputPanel.tsx)**

**Lokasi:** Line 151

```tsx
<button
  onClick={onGenerate}
  disabled={
    isLoading || 
    !diagnosis.trim() ||    // ← Field 1 required
    !procedure.trim() ||    // ← Field 2 required
    !medication.trim() ||   // ← Field 3 required
    isLimitReached
  }
>
  Generate AI Insight
</button>
```

---

### 4. **API Call Preparation (AdminRSDashboard.tsx)**

**Lokasi:** Lines 156-172

```tsx
const requestData = {
  mode: 'form',
  diagnosis,      // ← Field 1
  procedure,      // ← Field 2
  medication,     // ← Field 3
  icd10_code: selectedICD10Code.code,
  icd9_code: selectedICD9Code?.code || null,
  use_optimized: true,
  save_history: true
};
```

---

### 5. **Backend Validation (aiRoutes.ts)**

**Lokasi:** `web/server/routes/aiRoutes.ts` (Lines 60-68)

```typescript
if (!diagnosis || !procedure || !medication) {
  res.status(400).json({
    success: false,
    message: 'Diagnosis, procedure, and medication are required for form mode',
  });
  return;
}
```

---

### 6. **Backend Payload Mapping (aiRoutes.ts)**

**Lokasi:** Lines 79-88

```typescript
const payload = {
  mode: 'form',
  diagnosis: diagnosis,     // ← Frontend field
  tindakan: procedure,      // ← Renamed to 'tindakan'
  obat: medication,         // ← Renamed to 'obat'
  icd10_code: icd10_code || null,
  icd9_code: icd9_code || null,
  save_history: true,
  rs_id: userId,
};
```

---

### 7. **Core Engine Processing (lite_endpoints.py)**

**Lokasi:** `core_engine/lite_endpoints.py`

```python
# Parse request
diagnosis_raw = payload.get("diagnosis", "")
tindakan_raw = payload.get("tindakan", "")
obat_raw = payload.get("obat", "")

# Pass to analyzer
lite_result = analyze_lite_single({
    "mode": "form",
    "diagnosis": diagnosis_raw,
    "tindakan": tindakan_raw,
    "obat": obat_raw
})
```

---

## 🆕 Cara Menambahkan Field Baru (Contoh: "Alasan Rawat Inap")

### **Skenario:**
Menambahkan field baru **"Alasan Rawat Inap"** (admission_reason)

---

### **Step 1: Update Frontend State**

**File:** `web/src/components/AdminRSDashboard.tsx`

```tsx
// Line 22-24, tambahkan state baru:
const [diagnosis, setDiagnosis] = useState('');
const [procedure, setProcedure] = useState('');
const [medication, setMedication] = useState('');
const [admissionReason, setAdmissionReason] = useState(''); // ← NEW FIELD
```

---

### **Step 2: Update SmartInputPanel Props**

**File:** `web/src/components/SmartInputPanel.tsx`

**A. Update Interface (Lines 4-20):**

```tsx
interface SmartInputPanelProps {
  mode: InputMode;
  diagnosis: string;
  procedure: string;
  medication: string;
  admissionReason: string; // ← ADD THIS
  freeText: string;
  onDiagnosisChange: (value: string) => void;
  onProcedureChange: (value: string) => void;
  onMedicationChange: (value: string) => void;
  onAdmissionReasonChange: (value: string) => void; // ← ADD THIS
  onFreeTextChange: (value: string) => void;
  // ... other props
}
```

**B. Update Component Parameters (Lines 22-35):**

```tsx
export default function SmartInputPanel({
  mode,
  diagnosis,
  procedure,
  medication,
  admissionReason, // ← ADD THIS
  freeText,
  onDiagnosisChange,
  onProcedureChange,
  onMedicationChange,
  onAdmissionReasonChange, // ← ADD THIS
  onFreeTextChange,
  // ... other params
}: SmartInputPanelProps) {
```

**C. Add New Input Field (After medication field, ~Line 140):**

```tsx
<div className="space-y-2 flex-shrink-0">
  <label className={`flex items-center gap-2 text-sm font-medium ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
    <FileText className="w-4 h-4" />
    Alasan Rawat Inap
  </label>
  <input
    type="text"
    value={admissionReason}
    onChange={(e) => onAdmissionReasonChange(e.target.value)}
    placeholder="Masukkan alasan rawat inap..."
    className={`w-full px-4 py-2.5 rounded-lg border ${
      isDark
        ? 'bg-slate-800/50 border-cyan-500/30 text-white placeholder-slate-500'
        : 'bg-white/70 border-blue-200 text-gray-900 placeholder-gray-400'
    } backdrop-blur-sm focus:outline-none focus:ring-2 ${
      isDark ? 'focus:ring-cyan-500/50' : 'focus:ring-blue-500/50'
    } transition-all duration-300`}
  />
</div>
```

**D. Update Validation (Line 151):**

```tsx
<button
  onClick={onGenerate}
  disabled={
    isLoading || 
    !diagnosis.trim() || 
    !procedure.trim() || 
    !medication.trim() ||
    !admissionReason.trim() || // ← ADD VALIDATION
    isLimitReached
  }
>
```

---

### **Step 3: Pass Props from Parent Component**

**File:** `web/src/components/AdminRSDashboard.tsx` (Line 480)

```tsx
<SmartInputPanel
  mode={inputMode}
  diagnosis={diagnosis}
  procedure={procedure}
  medication={medication}
  admissionReason={admissionReason} // ← ADD THIS
  freeText={freeText}
  onDiagnosisChange={setDiagnosis}
  onProcedureChange={setProcedure}
  onMedicationChange={setMedication}
  onAdmissionReasonChange={setAdmissionReason} // ← ADD THIS
  onFreeTextChange={setFreeText}
  onGenerate={handleGenerate}
  isLoading={isLoading}
  isDark={isDark}
  aiUsage={aiUsage}
/>
```

---

### **Step 4: Update API Request Data**

**File:** `web/src/components/AdminRSDashboard.tsx` (Line 163)

```tsx
const requestData = {
  mode: 'form',
  diagnosis,
  procedure,
  medication,
  admission_reason: admissionReason, // ← ADD NEW FIELD
  icd10_code: selectedICD10Code.code,
  icd9_code: selectedICD9Code?.code || null,
  use_optimized: true,
  save_history: true
};
```

---

### **Step 5: Update Backend Validation**

**File:** `web/server/routes/aiRoutes.ts` (Line 16)

**A. Extract from request body:**

```typescript
const { mode, diagnosis, procedure, medication, input_text, admission_reason } = req.body;
```

**B. Update validation:**

```typescript
if (!diagnosis || !procedure || !medication || !admission_reason) {
  res.status(400).json({
    success: false,
    message: 'Diagnosis, procedure, medication, and admission reason are required for form mode',
  });
  return;
}
```

**C. Add to payload:**

```typescript
const payload = {
  mode: 'form',
  diagnosis: diagnosis,
  tindakan: procedure,
  obat: medication,
  alasan_rawat_inap: admission_reason, // ← NEW FIELD
  icd10_code: icd10_code || null,
  icd9_code: icd9_code || null,
  save_history: true,
  rs_id: userId,
};
```

---

### **Step 6: Update Core Engine**

**File:** `core_engine/lite_endpoints.py`

**A. Update payload model (if using Pydantic):**

```python
class AnalyzeLiteSingleRequest(BaseModel):
    mode: str
    diagnosis: Optional[str] = None
    tindakan: Optional[str] = None
    obat: Optional[str] = None
    alasan_rawat_inap: Optional[str] = None  # ← NEW FIELD
    input_text: Optional[str] = None
    icd10_code: Optional[str] = None
    icd9_code: Optional[str] = None
```

**B. Extract and use in analysis:**

```python
# Parse request
diagnosis_raw = payload.get("diagnosis", "")
tindakan_raw = payload.get("tindakan", "")
obat_raw = payload.get("obat", "")
alasan_rawat_inap = payload.get("alasan_rawat_inap", "")  # ← NEW

# Use in analysis logic
lite_result = analyze_lite_single({
    "mode": "form",
    "diagnosis": diagnosis_raw,
    "tindakan": tindakan_raw,
    "obat": obat_raw,
    "alasan_rawat_inap": alasan_rawat_inap  # ← PASS TO ANALYZER
})
```

---

### **Step 7: Update Clear Function (Optional)**

**File:** `web/src/components/AdminRSDashboard.tsx` (Line 457)

```tsx
setInputMode('text');
setDiagnosis('');
setProcedure('');
setMedication('');
setAdmissionReason(''); // ← CLEAR NEW FIELD
```

---

## 📋 Checklist: Menambahkan Field Baru

Untuk setiap field baru, pastikan update **7 file** berikut:

- [ ] **1. AdminRSDashboard.tsx** - Add `useState` for new field
- [ ] **2. SmartInputPanel.tsx (Interface)** - Add to `SmartInputPanelProps`
- [ ] **3. SmartInputPanel.tsx (Props)** - Add to function parameters
- [ ] **4. SmartInputPanel.tsx (JSX)** - Add new input field HTML
- [ ] **5. SmartInputPanel.tsx (Validation)** - Add to button `disabled` check
- [ ] **6. aiRoutes.ts (Backend)** - Add validation & payload mapping
- [ ] **7. lite_endpoints.py (Core Engine)** - Parse and use in analysis

---

## 🎨 UI Component Hierarchy

```
AdminRSDashboard
  └── SmartInputPanel
        ├── Input Field 1: Diagnosis
        ├── Input Field 2: Tindakan (Procedure)
        ├── Input Field 3: Obat (Medication)
        └── Button: Generate AI Insight
              └── onClick → handleGenerate()
                    └── API Call → /api/ai/analyze
```

---

## 🔄 Data Flow Summary

```
USER INPUT (Frontend)
  │
  ├── diagnosis: "Pneumonia"
  ├── procedure: "Rontgen Thorax"
  └── medication: "Ceftriaxone"
  │
  ▼
FRONTEND STATE (React useState)
  │
  ▼
API REQUEST (fetch/axios)
  {
    mode: "form",
    diagnosis: "Pneumonia",
    procedure: "Rontgen Thorax",
    medication: "Ceftriaxone"
  }
  │
  ▼
BACKEND MAPPING (Express.js)
  {
    mode: "form",
    diagnosis: "Pneumonia",
    tindakan: "Rontgen Thorax",  ← renamed
    obat: "Ceftriaxone"          ← renamed
  }
  │
  ▼
CORE ENGINE (Python)
  - Parse "tindakan" → tindakan_list
  - Parse "obat" → obat_list
  - Run analysis
  │
  ▼
RESPONSE (JSON)
  {
    klasifikasi: {...},
    konsistensi: {...},
    insight_ai: "...",
    ...
  }
  │
  ▼
DISPLAY RESULTS
```

---

## 💡 Tips & Best Practices

### 1. **Naming Convention Consistency**

| Layer | Field Name Pattern |
|-------|-------------------|
| Frontend | camelCase (`admissionReason`) |
| Backend API | snake_case (`admission_reason`) |
| Core Engine | snake_case (`alasan_rawat_inap`) |

### 2. **Validation Strategy**

- **Frontend:** Check `!fieldName.trim()` untuk memastikan tidak kosong
- **Backend:** Validate sebelum forward ke core engine
- **Core Engine:** Optional validation untuk edge cases

### 3. **State Management**

- Setiap field butuh:
  - State variable: `const [fieldName, setFieldName] = useState('')`
  - Change handler: `onFieldNameChange={setFieldName}`
  - Clear handler: `setFieldName('')` (saat switch mode)

### 4. **Testing Checklist**

Setelah menambahkan field baru:
- [ ] Test form validation (empty field)
- [ ] Test API call (field included in payload)
- [ ] Test backend processing (field parsed correctly)
- [ ] Test clear functionality (field cleared when switching modes)
- [ ] Test dengan data real (hasil analysis benar)

---

## 🚀 Quick Reference: Add Field in 7 Steps

1. **AdminRSDashboard.tsx** → `useState('');`
2. **SmartInputPanel (Props Interface)** → Add field + handler
3. **SmartInputPanel (JSX)** → Add `<input>` element
4. **SmartInputPanel (Validation)** → `!newField.trim() ||`
5. **AdminRSDashboard (API call)** → `new_field: newField,`
6. **aiRoutes.ts** → Validate + map to payload
7. **lite_endpoints.py** → Parse and use in analysis

---

**Generated:** November 17, 2025  
**Files Analyzed:** AdminRSDashboard.tsx, SmartInputPanel.tsx, aiRoutes.ts, lite_endpoints.py
