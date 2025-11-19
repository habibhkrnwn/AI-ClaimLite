# 🎨 INACBG UI Visual Guide

## 📸 UI Preview (Mockup Description)

### 1. **Header Section** (Top Card)
```
┌─────────────────────────────────────────────────────────────────┐
│  ✅ Kode CBG INACBG                              [80% Badge]    │
│                                                                  │
│     I-4-10-I                                                    │
│     INFARK MYOKARD AKUT (RINGAN)                                │
└─────────────────────────────────────────────────────────────────┘
```

**Features**:
- Large, bold CBG code dalam box berwarna
- Description clear & readable
- Confidence badge di pojok kanan atas (green/yellow/red)

---

### 2. **Tarif Section** (Main Card)
```
┌─────────────────────────────────────────────────────────────────┐
│  💰 Tarif INACBG                                                │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         Tarif Kelas 1                                    │   │
│  │      Rp 5.770.100                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │ Kelas 1  │  │ Kelas 2  │  │ Kelas 3  │                     │
│  │ Rp 5.7M  │  │ Rp 5.0M  │  │ Rp 4.3M  │                     │
│  └──────────┘  └──────────┘  └──────────┘                     │
│   [ACTIVE]       [Inactive]    [Inactive]                      │
└─────────────────────────────────────────────────────────────────┘
```

**Features**:
- Main tarif highlighted dengan gradient background
- 3-column grid untuk tarif per kelas
- Active class dengan border & background special
- Rupiah formatting otomatis

---

### 3. **Breakdown & Classification** (2-Column Grid)
```
┌───────────────────────────┐  ┌───────────────────────────┐
│  📈 Breakdown CBG         │  │  ℹ️ Klasifikasi           │
│                           │  │                           │
│  CMG: I                   │  │  Regional: 1              │
│  ↳ Cardiovascular system  │  │  Kelas RS: B              │
│                           │  │  Tipe RS: Pemerintah      │
│  Case Type: 4             │  │  Layanan: RI              │
│  ↳ Rawat Inap Bukan       │  │                           │
│    Prosedur               │  │                           │
│                           │  │                           │
│  Specific Code: 10        │  │                           │
│  Severity: I              │  │                           │
└───────────────────────────┘  └───────────────────────────┘
```

**Features**:
- Side-by-side layout untuk efisiensi space
- Indented sub-descriptions
- Clear label-value pairs
- Consistent spacing

---

### 4. **Matching Detail Section**
```
┌─────────────────────────────────────────────────────────────────┐
│  ℹ️ Detail Matching                                             │
│                                                                  │
│  Strategy:    [diagnosis_only_empirical]                        │
│  Case Count:  4 kasus                                           │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  40.0% kasus I21.0 masuk CBG ini                        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Features**:
- Strategy dalam monospace font box
- Note dalam bordered container
- Clear visual hierarchy

---

### 5. **Warnings Section** (Conditional)
```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️ Peringatan                                                  │
│                                                                  │
│  ⚠️ Prosedur diabaikan, menggunakan CBG yang paling umum       │
│     untuk diagnosis ini                                         │
└─────────────────────────────────────────────────────────────────┘
```

**Features**:
- Yellow/amber color scheme
- Warning icon untuk setiap item
- Only shows if warnings exist

---

## 🎨 Color Palette

### Dark Mode
```css
Background:      #1e293b (slate-800) dengan opacity 40%
Border:          #06b6d4 (cyan-500) dengan opacity 20%
Text Primary:    #67e8f9 (cyan-300)
Text Secondary:  #cbd5e1 (slate-300)
Accent:          #22d3ee (cyan-400)
Card Hover:      Scale 1.02 + shadow-xl
```

### Light Mode
```css
Background:      #ffffff (white) dengan opacity 60%
Border:          #dbeafe (blue-100)
Text Primary:    #1d4ed8 (blue-700)
Text Secondary:  #4b5563 (gray-600)
Accent:          #3b82f6 (blue-500)
Card Hover:      Scale 1.02 + shadow-xl
```

### Status Colors
```css
Confidence High (≥80%):   Green (#10b981 / #34d399)
Confidence Medium (60-79%): Yellow (#f59e0b / #fbbf24)
Confidence Low (<60%):    Red (#ef4444 / #f87171)
Warning:                  Amber (#f59e0b / #fbbf24)
```

---

## 📐 Layout Specifications

### Spacing
- Card padding: `1.25rem` (p-5)
- Section margin bottom: `1.5rem` (mb-6)
- Grid gap: `1rem` (gap-4)
- Element gap: `0.5rem` (gap-2)

### Typography
```css
Heading (h3):     18px, font-semibold
Subheading:       14px, font-medium
Body:             14px, regular
Small:            12px, regular
CBG Code:         24px, font-bold, monospace
Tarif Main:       30px (3xl), font-bold
```

### Border Radius
- Cards: `0.75rem` (rounded-xl)
- Buttons: `0.5rem` (rounded-lg)
- Badges: `0.5rem` (rounded-lg)

### Shadows
- Card default: `shadow-lg`
- Card hover: `shadow-xl`
- Emphasis: `shadow-2xl`

---

## 🔄 State Variations

### 1. Empty State (No Data)
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│                     💰                                           │
│            (Large icon, opacity 30%)                             │
│                                                                  │
│        Hasil analisis INACBG akan muncul di sini                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Loading State (Future Enhancement)
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│                     ⏳                                           │
│              (Spinning loader)                                   │
│                                                                  │
│             Sedang menganalisis INACBG...                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Error State (Future Enhancement)
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│                     ❌                                           │
│                                                                  │
│          Gagal menganalisis INACBG                              │
│          Silakan coba lagi atau hubungi admin                   │
│                                                                  │
│                  [Retry Button]                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎭 Interaction States

### Hover Effects
```css
Cards:
  - Scale: 1.02
  - Shadow: Increase to xl
  - Duration: 300ms
  - Cursor: default (not clickable cards)

Buttons (if added):
  - Background: Darken 10%
  - Scale: 1.05
  - Duration: 200ms
  - Cursor: pointer
```

### Active States
```css
Tarif Kelas Active:
  - Background: Cyan/Blue gradient
  - Border: Thicker + stronger color
  - Text: Brighter color
  - Font: Bolder
```

---

## 📱 Responsive Behavior

### Desktop (≥1024px)
- Full 2-column grid untuk breakdown & classification
- Spacious padding & margins
- Larger typography

### Tablet (768px - 1023px)
- Maintain 2-column grid
- Slightly reduced padding
- Same typography

### Mobile (<768px) - Future Enhancement
- Stack breakdown & classification vertically
- Reduce padding
- Smaller typography for long text
- Tarif grid remains 3-column (compact)

---

## 🎬 Animation Specifications

### Entry Animation (Future)
```css
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

Duration: 400ms
Easing: ease-out
Stagger: 50ms per card
```

### Transition
```css
All interactive elements:
  transition: all 300ms ease-in-out
```

---

## 🔍 Accessibility

### Color Contrast
- ✅ Text-background contrast ratio ≥ 4.5:1
- ✅ Interactive elements contrast ≥ 3:1
- ✅ Dark & light modes both WCAG AA compliant

### Font Sizes
- ✅ Minimum body text: 14px (readable)
- ✅ Minimum labels: 12px (acceptable for secondary)
- ✅ Large text (≥24px) for emphasis

### Focus States (Future Enhancement)
```css
Focusable elements:
  outline: 2px solid cyan-500
  outline-offset: 2px
```

---

**Last Updated**: November 19, 2025  
**Version**: 1.0.0  
**Status**: ✅ Implemented & Ready for Use
