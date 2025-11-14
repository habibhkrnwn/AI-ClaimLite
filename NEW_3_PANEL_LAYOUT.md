# 🎨 New 3-Panel Layout Design

## 📋 Overview

Redesign ICD-10 Explorer dengan 3 panel yang lebih efisien:
1. **Panel Kiri**: ICD-10 Categories (HEAD codes)
2. **Panel Tengah**: ICD-10 Details (Subcodes)
3. **Panel Kanan**: Mapping Preview (Medical terminology)

---

## 🏗️ Layout Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Header: AI Translation                                                  │
│ "radang paru paru bakteri" → "bacterial pneumonia"                     │
│ Selected: ✓ J15.2                                                       │
├─────────────────┬─────────────────┬─────────────────────────────────────┤
│ PANEL 1 (Kiri)  │ PANEL 2 (Tengah)│ PANEL 3 (Kanan)                    │
│ Categories      │ Details         │ Mapping Preview                     │
├─────────────────┼─────────────────┼─────────────────────────────────────┤
│ Kategori ICD-10 │ Detail Sub-Kode:│ Preview Mapping                     │
│ 5 kategori      │ J15             │                                     │
│                 │ 10 sub-kode     │ ┌─────────────────────────────────┐│
│ J12   6   ➤     │                 │ │ Diagnosis (Original)            ││
│ J13   1   ➤     │ 1  J15.0       │ │ radang paru paru bakteri        ││
│ J15   10  ✓ ➤   │    Klebsiella   │ │                                 ││
│ J18   3   ➤     │                 │ │ Diagnosis (Medical Term)        ││
│                 │ 2  ✓ J15.2      │ │ ┌─────────────────────────────┐││
│                 │    Staphylococcus│ │ │ J15.2                       │││
│                 │    ✓ Dipilih    │ │ │ Pneumonia due to            │││
│                 │                 │ │ │ staphylococcus              │││
│                 │ 3  J15.9        │ │ └─────────────────────────────┘││
│                 │    Unspecified  │ │                                 ││
│                 │                 │ │ Tindakan:                       ││
│                 │ ─────────────── │ │ ultrasound                      ││
│                 │                 │ │                                 ││
│                 │ [Generate AI   ]│ │ Obat:                           ││
│                 │  Analysis       │ │ panadol                         ││
│                 │  (J15.2)        │ │                                 ││
│                 │                 │ │ ┌─────────────────────────────┐││
│                 │ Legend:         │ │ │ 💡 Preview Mapping          │││
│                 │ ⚫ Primary (.0) │ │ │ Diagnosis akan menggunakan  │││
│                 │ ⚫ Unspecified  │ │ │ kode J15.2 untuk analisis   │││
└─────────────────┴─────────────────┴─────────────────────────────────────┘
```

---

## 🎯 Panel Breakdown

### **Panel 1: ICD-10 Categories (Kiri)**

**Purpose:** Show HEAD codes hasil filtering dari OpenAI translation

**Content:**
- Title: "Kategori ICD-10"
- Count: "X kategori ditemukan"
- List of HEAD codes dengan format compact

**Item Format:**
```
┌──────────────────────────┐
│ J15   10   ➤            │ ← HEAD code, count, arrow
│ Bacterial pneumonia...  │ ← Name (1 line, truncated)
└──────────────────────────┘
```

**States:**
- **Unselected**: Gray background, thin border
- **Selected**: Cyan/Blue background, highlighted border, arrow rotated

**Features:**
- Compact view (lebih banyak items visible)
- Auto-scroll to selected
- Click to load details

---

### **Panel 2: ICD-10 Details (Tengah)**

**Purpose:** Show subcodes untuk selected HEAD code

**Content:**
- Title: "Detail Sub-Kode: J15"
- Count: "X sub-kode tersedia"
- List of subcodes dengan numbering

**Item Format:**
```
┌────────────────────────────┐
│ 1  J15.0                  │
│    Pneumonia due to       │
│    Klebsiella pneumoniae  │
└────────────────────────────┘

┌────────────────────────────┐
│ 2  ✓ J15.2                │ ← Selected
│    Pneumonia due to       │
│    staphylococcus         │
│    ✓ Dipilih              │ ← Badge
└────────────────────────────┘
```

**Badges:**
- `✓ Dipilih` - User selected this code
- `Primary` - Code ending with .0
- `Unspecified` - Code ending with .9

**Bottom Section:**
- **Generate AI Analysis Button** (Prominent, gradient)
  - Active if code selected
  - Shows selected code in button text
  - Disabled if no selection
- **Legend** (Information about badges)

**States:**
- **Unselected**: White/Gray background
- **Selected**: Cyan/Blue background with border
- **Hover**: Lighter background

---

### **Panel 3: Mapping Preview (Kanan)**

**Purpose:** Show preview of how input will be mapped with medical terminology

**Content:**

#### **Diagnosis Section (Highlighted)**
```
┌─────────────────────────────────┐
│ Diagnosis (Original)            │
│ radang paru paru bakteri        │ ← Strikethrough
│                                 │
│ Diagnosis (Medical Term)        │
│ ┌─────────────────────────────┐│
│ │ J15.2                       ││ ← Blue/Cyan box
│ │ Pneumonia due to            ││
│ │ staphylococcus              ││
│ └─────────────────────────────┘│
└─────────────────────────────────┘
```

#### **Tindakan Section** (If form mode)
```
┌─────────────────────────────────┐
│ Tindakan                        │
│ ultrasound                      │
└─────────────────────────────────┘
```

#### **Obat Section** (If form mode)
```
┌─────────────────────────────────┐
│ Obat                            │
│ panadol                         │
└─────────────────────────────────┘
```

#### **Info Box** (Always shown)
```
┌─────────────────────────────────┐
│ 💡 Preview Mapping              │
│ Diagnosis akan menggunakan kode │
│ J15.2 untuk analisis AI.        │
└─────────────────────────────────┘
```

**Empty State:**
```
┌─────────────────────────────────┐
│        📋 Icon                  │
│                                 │
│ Pilih sub-kode ICD-10 untuk    │
│ melihat preview mapping         │
└─────────────────────────────────┘
```

**Features:**
- Original input shown with strikethrough
- Medical term highlighted with colored box
- Real-time preview as user selects code
- Visual distinction between original and medical

---

## 🔄 User Flow

```
1. User fills form:
   - Diagnosis: "radang paru paru bakteri"
   - Tindakan: "ultrasound"
   - Obat: "panadol"
   
2. Click "Generate AI Insight"
   ↓
3. OpenAI Translation:
   "radang paru paru bakteri" → "bacterial pneumonia"
   ↓
4. Smart Filtering:
   Search "bacterial pneumonia" → J15 (10 subcodes)
   ↓
5. 3-Panel Explorer Shows:
   
   Panel 1 (Kiri):          Panel 2 (Tengah):        Panel 3 (Kanan):
   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
   │ J15 ✓        │ ←auto→  │ J15.0        │         │ (Empty)      │
   │ J13          │  select │ J15.2        │         │ Select code  │
   │ J18          │         │ J15.9        │         │ to preview   │
   └──────────────┘         └──────────────┘         └──────────────┘
   
6. User clicks J15.2:
   
   Panel 1 (Kiri):          Panel 2 (Tengah):        Panel 3 (Kanan):
   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
   │ J15 ✓        │         │ J15.0        │         │ ✓ Preview    │
   │ J13          │         │ ✓ J15.2      │ ←──┐    │ J15.2        │
   │ J18          │         │   Dipilih    │    └──► │ Staph...     │
   └──────────────┘         │              │         │              │
                            │ [Generate AI]│         │ Tindakan:    │
                            └──────────────┘         │ ultrasound   │
                                                     └──────────────┘
   
7. Click "Generate AI Analysis (J15.2)":
   ↓
8. Full AI Analysis with selected code J15.2
```

---

## 💡 Key Improvements

### **1. Removed Input Summary Panel**
**Sebelum:**
- Panel kiri menampilkan input data yang sudah user tahu
- Memakan space tanpa value tambahan
- Cuma repeat informasi

**Sesudah:**
- Panel kiri langsung show categories (actionable)
- Space lebih efisien
- Input data tetap visible di panel kanan (mapping preview)

### **2. Mapping Preview Panel**
**Value:**
- **Visual confirmation**: User lihat bagaimana input akan di-transform
- **Before/After comparison**: Original vs Medical term side-by-side
- **Confidence boost**: User yakin pilihan code sudah benar
- **Education**: User belajar medical terminology

**Before (No preview):**
```
User input → Select code → Generate → Hope for the best
```

**After (With preview):**
```
User input → Select code → SEE MAPPING PREVIEW ✓ → Generate with confidence
```

### **3. Better Space Utilization**

| Panel | Sebelum | Sesudah | Space Saved |
|-------|---------|---------|-------------|
| Input Summary | 33% | 0% | +33% |
| Categories | 33% | 33% | 0% |
| Details | 33% | 33% | 0% |
| Mapping Preview | 0% | 33% | NEW |

**Result:**
- Categories: Same space, more efficient (compact view)
- Details: Same space, added Generate button
- Preview: New feature using reclaimed space

---

## 🎨 Visual Design

### **Color Scheme:**

**Dark Mode:**
- Background: `bg-slate-800/50`
- Border: `border-slate-700/50`
- Selected: `bg-cyan-500/20 border-cyan-500/50`
- Text: `text-slate-300`
- Highlight: `text-cyan-300`

**Light Mode:**
- Background: `bg-white/50`
- Border: `border-gray-200`
- Selected: `bg-blue-50 border-blue-400`
- Text: `text-gray-700`
- Highlight: `text-blue-700`

### **Typography:**

| Element | Size | Weight |
|---------|------|--------|
| Panel Title | `text-sm` | `font-semibold` |
| Code | `text-sm` | `font-bold` |
| Name | `text-xs` | `font-normal` |
| Badge | `text-xs` | `font-medium` |
| Info | `text-xs` | `font-normal` |

### **Spacing:**

| Element | Padding | Gap |
|---------|---------|-----|
| Panel | `p-4` | - |
| Item | `p-2.5` | - |
| Grid | - | `gap-4` |
| List | - | `space-y-1.5` |

---

## 🧪 Testing Scenarios

### **Test 1: General Input**
```
Input: "pneumonia"
Expected Panel 1: J12, J13, J14, J15, J18 (5 categories)
Expected Panel 2: Auto-select J12 → 6 subcodes
Expected Panel 3: Empty (no code selected yet)
Action: Click J12.3
Expected Panel 3: Show "J12.3 - Human metapneumovirus pneumonia"
```

### **Test 2: Specific Input**
```
Input: "pneumonia cacar air"
Translation: "varicella pneumonia"
Expected Panel 1: B01 (1 category only)
Expected Panel 2: B01.0, B01.1, B01.2, B01.9
Expected Panel 3: Empty
Action: Click B01.2
Expected Panel 3: 
  - Original: pneumonia cacar air (strikethrough)
  - Medical: B01.2 - Varicella pneumonia (highlighted)
```

### **Test 3: Form Mode**
```
Input Form:
  - Diagnosis: "radang paru paru"
  - Tindakan: "nebulisasi"
  - Obat: "ceftriaxone"
  
Expected Panel 3 after selecting J18.9:
  ┌─────────────────────────┐
  │ Diagnosis (Original)    │
  │ radang paru paru        │ (strikethrough)
  │                         │
  │ Diagnosis (Medical)     │
  │ J18.9 - Pneumonia,      │
  │ unspecified organism    │
  ├─────────────────────────┤
  │ Tindakan:               │
  │ nebulisasi              │
  ├─────────────────────────┤
  │ Obat:                   │
  │ ceftriaxone             │
  └─────────────────────────┘
```

---

## 📊 Comparison: Old vs New

### **Old Layout (4 panels):**
```
┌─────────┬─────────┬─────────┬─────────┐
│ Header  │         │         │         │
├─────────┼─────────┼─────────┼─────────┤
│ Input   │ Category│ Details │ (Empty) │
│ Summary │         │         │         │
│         │         │         │         │
│ [Back]  │         │[Generate│         │
│         │         │   AI]   │         │
└─────────┴─────────┴─────────┴─────────┘

Problems:
✗ Input summary panel = wasted space
✗ Back button = extra click
✗ No preview of mapping
✗ 4th panel empty
```

### **New Layout (3 panels):**
```
┌─────────────────────────────────────────┐
│ Header: Translation + Selected Code     │
├─────────┬─────────┬───────────────────┐│
│ Category│ Details │ Mapping Preview   ││
│         │         │                   ││
│         │         │ Before: Original  ││
│         │         │ After: Medical    ││
│         │[Generate│                   ││
│         │   AI]   │ Info: Will use... ││
└─────────┴─────────┴───────────────────┴┘

Benefits:
✓ No wasted space
✓ Direct workflow (no back button)
✓ Visual preview of transformation
✓ All panels have purpose
```

---

## 🚀 Implementation Status

**Completed:**
- ✅ Removed Input Summary Panel (Panel 1)
- ✅ Moved Categories to Panel 1 (Left)
- ✅ Moved Details to Panel 2 (Middle)
- ✅ Created Mapping Preview Panel 3 (Right)
- ✅ Preview shows original input (strikethrough)
- ✅ Preview shows medical terminology (highlighted)
- ✅ Preview shows Tindakan & Obat (if form mode)
- ✅ Preview shows Info box with selected code
- ✅ Empty state for Panel 3 (when no code selected)

**Next Steps:**
- [ ] Test with real data
- [ ] Adjust responsive layout for smaller screens
- [ ] Add animation when switching codes
- [ ] Cache preview data for performance

---

## 📝 Developer Notes

### **Component Structure:**

```typescript
// ICD10Explorer.tsx
<div className="grid grid-cols-3 gap-4">
  {/* Panel 1: Categories */}
  <div>
    <ICD10CategoryPanel />
  </div>
  
  {/* Panel 2: Details */}
  <div>
    <ICD10DetailPanel />
  </div>
  
  {/* Panel 3: Mapping Preview */}
  <div>
    {selectedSubCode ? (
      <MappingPreview />
    ) : (
      <EmptyState />
    )}
  </div>
</div>
```

### **Data Flow:**

```
User selects J15.2
  ↓
handleSelectSubCode("J15.2", "Pneumonia due to staphylococcus")
  ↓
setSelectedSubCode("J15.2")
  ↓
Panel 3 re-renders with:
  - originalInput.diagnosis (from props)
  - selectedSubCode ("J15.2")
  - selectedDetails.find(d => d.code === "J15.2").name
```

---

**Version:** 3.0  
**Last Updated:** November 14, 2025  
**Status:** ✅ Implemented & Ready for Testing
