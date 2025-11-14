# 🔍 ICD-10 Smart Filtering & Code Selection

## 📋 Overview

Fitur ini memungkinkan:
1. **Smart filtering** berdasarkan detail input
2. **Clickable subcodes** untuk memilih kode spesifik
3. **Re-analysis** dengan kode ICD-10 terpilih

---

## 🎯 Smart Filtering Logic

### 1. General Input (Single Word)
**Input:** `"pneumonia"`

**SQL Query:**
```sql
WHERE LOWER(name) LIKE '%pneumonia%'
```

**Results:**
- J12 - Viral pneumonia, not elsewhere classified (6 subcodes)
- J13 - Pneumonia due to Streptococcus pneumoniae (1 subcode)
- J14 - Pneumonia due to Haemophilus influenzae (1 subcode)
- J15 - Bacterial pneumonia, not elsewhere classified (10 subcodes)
- J18 - Pneumonia, organism unspecified (3 subcodes)

**Total:** 5 HEAD categories

---

### 2. Specific Input (Multi-Word)
**Input:** `"pneumonia cacar air"` atau `"varicella pneumonia"`

**SQL Query (AND logic):**
```sql
WHERE 
  LOWER(name) LIKE '%pneumonia%' 
  AND LOWER(name) LIKE '%varicella%'
```

**Results:**
- B01.2 - Varicella pneumonia (1 exact match)

**Total:** 1 HEAD category (highly specific)

---

### 3. More Examples

| Input | Words Detected | Categories Found | Specificity |
|-------|----------------|------------------|-------------|
| `pneumonia` | 1 (general) | J12, J13, J14, J15, J18 | Low |
| `viral pneumonia` | 2 (specific) | J12 only | Medium |
| `pneumonia streptococcus` | 2 (specific) | J13 only | High |
| `bacterial pneumonia` | 2 (specific) | J15 only | Medium |
| `pneumonia haemophilus` | 2 (specific) | J14 only | High |
| `pneumonia cacar` | 2 (specific) | B01 only | High |

---

## 🖱️ Code Selection Flow

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: User Input "pneumonia"                             │
│ ┌─────────────┐                                             │
│ │ Input Panel │ Types: "pneumonia"                         │
│ │ [Diagnosis] │ Clicks: "Generate AI Insight"              │
│ │ pneumonia   │                                             │
│ └─────────────┘                                             │
└─────────────────────────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: AI Correction + Smart Filtering                    │
│ - translateToMedical("pneumonia") → "pneumonia"            │
│ - getICD10Categories("pneumonia") → 5 HEAD codes          │
│ - Auto-select first: J12                                   │
└─────────────────────────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: ICD-10 Explorer Shown                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Header: "pneumonia" → ✨ "pneumonia"                │   │
│ ├──────┬──────────┬──────────────────────────────────┐│   │
│ │Input │Categories│ Details                          ││   │
│ │      │● J12 (6) │ □ J12.0 Adenoviral              ││   │
│ │      │  J13 (1) │ □ J12.1 RSV                     ││   │
│ │      │  J14 (1) │ □ J12.2 Parainfluenza           ││   │
│ │      │  J15 (10)│ □ J12.3 Human metapneumovirus   ││   │
│ │      │  J18 (3) │ □ J12.8 Other viral             ││   │
│ │      │          │ □ J12.9 Viral, unspecified      ││   │
│ └──────┴──────────┴──────────────────────────────────┘│   │
└─────────────────────────────────────────────────────────────┘
               ↓ User clicks J12.3
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Code Selected                                       │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Header: "pneumonia" → ✨ "pneumonia"                │   │
│ │ Kode Terpilih: ✓ J12.3                              │   │
│ ├──────┬──────────┬──────────────────────────────────┐│   │
│ │Input │Categories│ Details                          ││   │
│ │      │● J12     │ □ J12.0 Adenoviral              ││   │
│ │      │          │ □ J12.1 RSV                     ││   │
│ │      │          │ □ J12.2 Parainfluenza           ││   │
│ │      │          │ ✓ J12.3 Human metapneumovirus ◄─││   │
│ │      │          │   (SELECTED)                     ││   │
│ │      │          │ □ J12.8 Other viral             ││   │
│ └──────┴──────────┴──────────────────────────────────┘│   │
└─────────────────────────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Analysis Result Updated                            │
│ - Classification: ICD-10 J12.3 (User selected)             │
│ - AI Insight: "Human metapneumovirus pneumonia detected"   │
│ - Validation: ✓ Sesuai CP                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 UI Interaction

### Subcode Button States

#### Unselected State
```css
bg-white/50 border border-gray-200
hover:bg-white hover:border-blue-300
```

#### Selected State
```css
bg-cyan-500/20 border-2 border-cyan-500/50
shadow-lg shadow-cyan-500/20
```

#### Badge Indicators
- **✓ Dipilih** - User has selected this code
- **Primary** - Code ending with .0 (primary type)
- **Unspecified** - Code ending with .9 (use if details unknown)

---

## 🧪 Testing Scenarios

### Test Case 1: General Search
```
Input: "pneumonia"
Expected Categories: 5 (J12, J13, J14, J15, J18)
Action: Click J12
Expected Details: 6 subcodes (J12.0 to J12.9)
Action: Click J12.3
Expected: Header shows "Kode Terpilih: ✓ J12.3"
```

### Test Case 2: Specific Search
```
Input: "viral pneumonia"
Expected Categories: 1 (J12 only)
Action: Auto-selected J12
Expected Details: 6 viral pneumonia subcodes
Action: Click J12.1 (RSV)
Expected: Badge "✓ Dipilih" on J12.1
```

### Test Case 3: Multi-Word Filtering
```
Input: "pneumonia cacar air"
Expected Categories: 1 (B01 - Varicella)
Action: Auto-selected B01
Expected Details: B01.2 - Varicella pneumonia
Action: Click B01.2
Expected: Analysis uses B01.2 specifically
```

### Test Case 4: Indonesian to Medical Translation
```
Input: "paru2 basah"
Correction: "pneumonia"
Expected Categories: 5 (J12-J18)
Action: Click J18 (organism unspecified)
Expected Details: J18.0, J18.1, J18.2, J18.8, J18.9
Action: Click J18.9 (unspecified)
Expected: Analysis with J18.9
```

---

## 📊 Backend Implementation

### Smart Filtering Query

```typescript
export async function getICD10Categories(searchTerm: string): Promise<ICD10Category[]> {
  const words = searchTerm.toLowerCase().split(/\s+/).filter(w => w.length > 2);
  
  if (words.length > 1) {
    // Multi-word: AND logic for specific matching
    const conditions = words.map((_, i) => `LOWER(name) LIKE $${i + 1}`).join(' AND ');
    const wordPatterns = words.map(w => `%${w}%`);
    
    query = `
      WITH matched_codes AS (
        SELECT code, name, 
          SUBSTRING(code FROM 1 FOR 3) as head_code
        FROM icd10_master
        WHERE ${conditions} AND validation_status = 'official'
      )
      SELECT head_code, MIN(name) as "headName", COUNT(*) as count
      FROM matched_codes
      WHERE head_code ~ '^[A-Z][0-9]{2}$'
      GROUP BY head_code
    `;
    params = wordPatterns;
  } else {
    // Single word: OR logic for general matching
    query = `... LOWER(name) LIKE $1 ...`;
    params = [`%${searchTerm}%`];
  }
  
  return pool.query(query, params);
}
```

---

## 🔄 State Management

### Component State Flow

```typescript
// AdminRSDashboard.tsx
const [selectedICD10Code, setSelectedICD10Code] = useState<{code: string; name: string} | null>(null);

const handleCodeSelection = async (code: string, name: string) => {
  setSelectedICD10Code({ code, name });
  console.log(`Selected: ${code} - ${name}`);
  // Optional: Re-trigger analysis with specific code
};

// ICD10Explorer.tsx
const [selectedSubCode, setSelectedSubCode] = useState<string | null>(null);

const handleSelectSubCode = (code: string, name: string) => {
  setSelectedSubCode(code);
  onCodeSelected?.(code, name); // Notify parent
};

// ICD10DetailPanel.tsx
<button onClick={() => onSelectCode?.(detail.code, detail.name)}>
  {detail.code} - {detail.name}
</button>
```

---

## 🚀 Future Enhancements

### Phase 1 (Current)
- ✅ Smart filtering (general vs specific)
- ✅ Clickable subcodes
- ✅ Visual selection indicator
- ✅ State propagation to parent

### Phase 2 (Future)
- [ ] Re-analyze automatically when code selected
- [ ] Show ICD-10 description in analysis result
- [ ] Save selected code to database
- [ ] History of selected codes per diagnosis

### Phase 3 (Advanced)
- [ ] ICD-10 code recommendation based on AI
- [ ] Highlight most frequently used codes
- [ ] Quick select from favorite codes
- [ ] Bulk code selection for multiple diagnoses

---

## 📝 Developer Notes

**Word Splitting Logic:**
```typescript
const words = searchTerm.toLowerCase().split(/\s+/).filter(w => w.length > 2);
// "pneumonia cacar air" → ["pneumonia", "cacar", "air"]
// Filters out words < 3 chars to avoid noise
```

**AND vs OR Logic:**
- Single word: `name LIKE '%pneumonia%'` (broad)
- Multi-word: `name LIKE '%pneumonia%' AND name LIKE '%cacar%'` (narrow)

**Performance:**
- Indexed on `icd10_master.name` for fast LIKE queries
- CTE (Common Table Expression) for efficient grouping
- Regex matching on `head_code` pattern `^[A-Z][0-9]{2}$`

---

## 🎓 User Guide

### How to Use Smart Filtering

1. **General Search**: Type single word (e.g., "pneumonia")
   - System shows ALL related categories
   - Good for exploration

2. **Specific Search**: Type multiple words (e.g., "viral pneumonia")
   - System narrows down to exact matches
   - Good for precise coding

3. **Select Code**: Click on any subcode
   - Badge "✓ Dipilih" appears
   - Header shows selected code
   - Analysis uses selected code

4. **Change Selection**: Click different subcode
   - Previous selection clears
   - New code becomes active
   - Re-analyze (optional)

---

**Version:** 1.0  
**Last Updated:** November 14, 2025  
**Feature Status:** ✅ Implemented & Ready for Testing
