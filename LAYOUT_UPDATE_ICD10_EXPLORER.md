# 🎨 Layout Update: ICD-10 Explorer Positioning

## ✅ FIXED: Layout Structure

Sebelumnya 3-column ICD-10 explorer ada **di dalam** SmartInputPanel, sekarang sudah dipindahkan menjadi **card terpisah** menggantikan posisi ResultsPanel.

---

## 📐 New Layout Structure

```
┌──────────────────────────────────────────────────────────────┐
│                    TOP SECTION (66% height)                  │
│  ┌─────────────┬────────────────────────────────────────┐   │
│  │ Panel Kiri  │   Panel Kanan: ICD-10 Explorer         │   │
│  │ Input       │ ┌─────────────────────────────────────┐│   │
│  │ (w-72)      │ │ Header: AI Correction               ││   │
│  │             │ │ "paru2 basah" → ✨ "pneumonia"      ││   │
│  │ Mode:       │ ├──────┬──────────┬──────────────────┤│   │
│  │ [Form]      │ │Input │Categories│ Details          ││   │
│  │ [Text]      │ │Summ. │ (HEAD)   │(Subcodes)        ││   │
│  │             │ │      │          │                  ││   │
│  │ Usage:      │ │Diag: │● J12 (6) │1. J12.0         ││   │
│  │ 5/100       │ │paru2 │  J13 (1) │2. J12.1         ││   │
│  │ ███░░       │ │basah │  J14 (1) │3. J12.2         ││   │
│  │             │ │      │  J15 (10)│4. J12.3 🟢      ││   │
│  │ [Diag]      │ │Proc: │  J18 (3) │5. J12.8         ││   │
│  │ [Proc]      │ │...   │          │6. J12.9 🟡      ││   │
│  │ [Med]       │ │      │(Click to │                  ││   │
│  │             │ │Med:  │ expand)  │Legend:          ││   │
│  │ [Generate]  │ │...   │          │🟢 Primary       ││   │
│  │             │ │      │          │🟡 Unspecified   ││   │
│  │             │ │← Back│          │                  ││   │
│  └─────────────┴─┴──────┴──────────┴──────────────────┴┘   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                  BOTTOM SECTION (33% height)                 │
│  ┌──────────────────────────────────────────────────────────┐│
│  │              Hasil Analisis AI (Full Width)              ││
│  │ ┌──────────────┬───────────────┬───────────────────────┐││
│  │ │ Klasifikasi  │ Validasi      │ Severity             │││
│  │ │ ICD-10: J12.3│ ✓ Sesuai CP   │ Sedang               │││
│  │ │ ICD-9: ...   │ ✓ Sesuai Fornas│ Consistency: 85%    │││
│  │ └──────────────┴───────────────┴───────────────────────┘││
│  │ AI Insight: ...                                          ││
│  │ CP Nasional: ...                                         ││
│  │ Required Docs: ...                                       ││
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

---

## 🔄 Component Changes

### 1. **SmartInputPanel.tsx** (Simplified)
**BEFORE:**
- ❌ Berisi 3-column ICD-10 explorer
- ❌ State management untuk categories/details
- ❌ Toggle between input mode dan explorer mode

**AFTER:**
- ✅ Hanya input form (diagnosis, procedure, medication) atau free text
- ✅ Simple button "Generate AI Insight"
- ✅ No internal state untuk ICD-10 data

### 2. **ICD10Explorer.tsx** (New Component)
**Purpose:** Standalone component untuk menampilkan ICD-10 hierarchy

**Props:**
```typescript
interface ICD10ExplorerProps {
  searchTerm: string;          // Original input "paru2 basah"
  correctedTerm: string;       // AI correction "pneumonia"
  originalInput: {             // User's input data
    diagnosis?: string;
    procedure?: string;
    medication?: string;
    freeText?: string;
    mode: 'form' | 'text';
  };
  isDark: boolean;
  onBack?: () => void;         // Optional callback to hide explorer
}
```

**Features:**
- Auto-loads ICD-10 hierarchy on mount via `useEffect`
- 3-column grid layout (Input Summary | Categories | Details)
- Click category → Update details panel
- Back button to return to input mode

### 3. **AdminRSDashboard.tsx** (Layout Manager)
**State:**
```typescript
const [showICD10Explorer, setShowICD10Explorer] = useState(false);
const [correctedTerm, setCorrectedTerm] = useState('');
const [originalSearchTerm, setOriginalSearchTerm] = useState('');
```

**Layout:**
- Top section (66% height):
  - Left: Input panel (w-72, fixed width)
  - Right: ICD10Explorer (flex-1, full width)
- Bottom section (33% height):
  - ResultsPanel (full width)

**Flow:**
1. User inputs diagnosis → Click "Generate AI Insight"
2. `handleGenerate()` calls:
   - `translateToMedical(inputTerm)` → Get corrected term
   - `setShowICD10Explorer(true)` → Show explorer
   - API call for analysis
3. ICD10Explorer renders with corrected term
4. ResultsPanel shows analysis below

---

## 🎯 User Interaction Flow

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: User Input                                          │
│ ┌─────────────┐                                             │
│ │ Panel Kiri  │ User types "paru2 basah"                   │
│ │ [Diagnosis] │ Clicks "Generate AI Insight"                │
│ │ paru2 basah │                                             │
│ │ [Generate]  │                                             │
│ └─────────────┘                                             │
└─────────────────────────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: AI Processing                                       │
│ - translateToMedical("paru2 basah") → "pneumonia"          │
│ - setShowICD10Explorer(true)                                │
│ - API call to core_engine for analysis                      │
└─────────────────────────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: ICD-10 Explorer Appears (Right Panel)              │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ Header: "paru2 basah" → ✨ "pneumonia"               │  │
│ ├──────┬──────────┬──────────────────────────────────┐  │  │
│ │Input │Categories│ Details                          │  │  │
│ │      │ J12 ✓    │ J12.0, J12.1, J12.2, J12.3, ... │  │  │
│ │      │ J13      │                                  │  │  │
│ │      │ J15      │                                  │  │  │
│ └──────┴──────────┴──────────────────────────────────┘  │  │
└─────────────────────────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: User Clicks J12                                     │
│ - handleSelectCategory("J12")                               │
│ - setSelectedDetails([J12.0, J12.1, ..., J12.9])           │
│ - Right panel updates with subcodes                         │
└─────────────────────────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Results Shown Below                                 │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Hasil Analisis AI (Full Width)                          ││
│ │ - Classification: ICD-10 J12.3, ICD-9 ...               ││
│ │ - Validation: ✓ Sesuai CP, ✓ Sesuai Fornas             ││
│ │ - Severity: Sedang (85% consistency)                    ││
│ │ - AI Insight: "Patient dengan viral pneumonia..."       ││
│ └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 File Structure

```
web/src/components/
├── AdminRSDashboard.tsx       ← Main layout manager
├── SmartInputPanel.tsx        ← Simple input component
├── ICD10Explorer.tsx          ← NEW: Standalone 3-column explorer
├── ICD10CategoryPanel.tsx     ← Middle column (HEAD categories)
├── ICD10DetailPanel.tsx       ← Right column (subcodes)
└── ResultsPanel.tsx           ← Bottom section (analysis results)
```

---

## 🎨 Tailwind Classes Breakdown

### Height Distribution
```css
/* Top Section: 66% */
.h-2/3 

/* Bottom Section: 33% */
.h-1/3
```

### Grid Layout (Inside ICD10Explorer)
```css
/* 3 equal columns */
.grid.grid-cols-3.gap-4
```

### Width Distribution (Top Section)
```css
/* Left panel: Fixed 288px */
.w-72.flex-shrink-0

/* Right panel: Remaining space */
.flex-1
```

---

## 🧪 Testing Checklist

### Visual Layout
- [ ] Input panel tetap di kiri dengan width 72 (288px)
- [ ] ICD-10 Explorer menempati sisa space kanan
- [ ] Top section menggunakan 66% dari total height
- [ ] Bottom section (ResultsPanel) menggunakan 33% height
- [ ] Semua panel responsive dengan overflow handling

### Functional
- [ ] Input "paru2 basah" → Correction shows "pneumonia"
- [ ] Explorer muncul di panel kanan (bukan modal/overlay)
- [ ] Click kategori J12 → Details update di kolom kanan
- [ ] Back button hide explorer → Show empty state
- [ ] Hasil analisis muncul di bawah explorer
- [ ] Scroll works independently (explorer vs results)

### Edge Cases
- [ ] Empty state ketika belum generate
- [ ] Loading state saat fetch ICD-10 data
- [ ] Error handling jika API gagal
- [ ] Dark mode theming konsisten
- [ ] Small screen: vertical stack (optional)

---

## 🚀 Deployment Notes

**No Breaking Changes:**
- Existing API endpoints tetap sama
- Database schema tidak berubah
- Backend logic tidak terpengaruh
- Only frontend component restructuring

**Migration Steps:**
1. ✅ Create `ICD10Explorer.tsx`
2. ✅ Simplify `SmartInputPanel.tsx`
3. ✅ Update `AdminRSDashboard.tsx` layout
4. ✅ Test responsive behavior
5. 🔄 Deploy frontend build

---

## 📝 Developer Notes

**Why This Layout?**
1. **Separation of Concerns:** Input, ICD-10 selection, dan results adalah 3 concern berbeda
2. **Visual Hierarchy:** Top section untuk exploration, bottom untuk final results
3. **Screen Real Estate:** ICD-10 explorer butuh space horizontal untuk 3 columns
4. **User Focus:** Mata user fokus ke explorer dulu, baru scroll down untuk results

**Performance:**
- ICD-10 data fetched once per analysis (cached in component state)
- No re-rendering of ResultsPanel when selecting categories
- Lazy load details only when category clicked

**Future Enhancements:**
- [ ] Collapsible bottom section untuk maximize explorer space
- [ ] Breadcrumb navigation (J12 > J12.3 > Selected)
- [ ] Quick search bar dalam ICD10CategoryPanel
- [ ] Copy code to clipboard functionality

---

**Last Updated:** November 14, 2025  
**Layout Version:** 2.0  
**Component Count:** 6 (Dashboard, SmartInput, ICD10Explorer, CategoryPanel, DetailPanel, ResultsPanel)
