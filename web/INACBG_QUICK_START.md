# 🚀 INACBG UI - Quick Start Guide

## ⚡ TL;DR - Cara Cepat Test UI INACBG

### 1. Start Development Server
```bash
cd web
npm run dev
```

### 2. Login & Generate Analysis
1. Buka http://localhost:5173 (atau port yang ditampilkan)
2. Login dengan credentials Admin RS
3. Input data diagnosis & tindakan (atau gunakan free text)
4. Klik **"Generate AI Insight"**
5. Tunggu hingga hasil analisis muncul

### 3. Akses Panel INACBG
Setelah hasil analisis muncul, klik tab **💰 INACBG** di bagian atas panel hasil.

### 4. Toggle Theme
Klik icon Sun/Moon di header untuk test dark/light mode.

---

## 📋 Sample Input untuk Testing

### Option 1: Form Mode (Structured Input)
```
Diagnosis:  Infark Myokard Akut
Tindakan:   Chest X-ray, EKG
Obat:       Ceftriaxone, Aspirin
```

### Option 2: Free Text Mode
```
Pasien laki-laki 55 tahun dengan keluhan nyeri dada menjalar ke lengan kiri.
Diagnosis: Infark Myokard Akut (IMA).
Dilakukan pemeriksaan EKG dan Chest X-Ray.
Diberikan terapi Aspirin dan Clopidogrel.
```

---

## 🎯 What to Test

### ✅ Basic Functionality
- [ ] Panel INACBG muncul saat klik tab
- [ ] Data CBG code & description ditampilkan
- [ ] Tarif dalam format Rupiah yang benar
- [ ] Confidence badge menampilkan 80%
- [ ] Breakdown & Classification terisi lengkap
- [ ] Matching detail visible
- [ ] Warning section muncul dengan 1 item

### ✅ Visual Design
- [ ] Dark mode: Background slate, text cyan
- [ ] Light mode: Background white, text blue
- [ ] Cards memiliki shadow & rounded corners
- [ ] Hover effect: Scale up + shadow increase
- [ ] Typography hierarchy jelas (heading > body > small)
- [ ] Colors consistent dengan theme

### ✅ Layout & Spacing
- [ ] Grid 2-column untuk breakdown & classification
- [ ] Padding & margins konsisten
- [ ] Text alignment proper (left/center sesuai konteks)
- [ ] No overflow atau text cutting
- [ ] Responsive pada resize window

### ✅ Data Display
- [ ] CBG code: "I-4-10-I" dengan styling bold
- [ ] Description: "INFARK MYOKARD AKUT (RINGAN)"
- [ ] Tarif Kelas 1: Rp 5.770.100 (highlighted)
- [ ] Tarif Kelas 2: Rp 5.054.300
- [ ] Tarif Kelas 3: Rp 4.338.400
- [ ] CMG: "I - Cardiovascular system"
- [ ] Case Type: "4 - Rawat Inap Bukan Prosedur"
- [ ] Severity: "I" (large & bold)
- [ ] Strategy: "diagnosis_only_empirical"
- [ ] Confidence: 80%
- [ ] Warning: "Prosedur diabaikan..." visible

---

## 🔄 Toggle Between Panels

### Test Switching
1. Klik **📋 Analisis Klinis** → Should show ResultsPanel
2. Klik **💰 INACBG** → Should show INACBGPanel
3. Verify smooth transition (no flicker/delay)
4. Check active tab highlight (cyan/blue background)
5. Check inactive tab styling (gray background)

### Expected Behavior
- Tab switch instant (no loading)
- Active tab has solid background
- Inactive tab has transparent/gray background
- Panel content changes smoothly
- Scroll position resets to top (if needed)

---

## 🎨 Theme Testing Checklist

### Dark Mode Colors
```
✅ Background:     Slate 800 dengan opacity
✅ Border:         Cyan 500 dengan transparency
✅ Heading:        Cyan 300
✅ Body text:      Slate 300
✅ Secondary text: Slate 400
✅ Accent:         Cyan 400
✅ Card bg:        Slate 800/40
```

### Light Mode Colors
```
✅ Background:     White/Blue 50
✅ Border:         Blue 100-200
✅ Heading:        Blue 700
✅ Body text:      Gray 700
✅ Secondary text: Gray 600
✅ Accent:         Blue 500
✅ Card bg:        White/60
```

### Color Contrast Test
1. Toggle to dark mode
2. Check if all text readable
3. Toggle to light mode
4. Check if all text readable
5. No color should be too faint or too bright

---

## 🐛 Common Issues & Solutions

### Issue 1: Panel tidak muncul setelah klik tab INACBG
**Cause**: State `inacbgResult` masih null  
**Solution**: Check console log, pastikan mock data ter-set setelah analysis success

### Issue 2: Styling berantakan / tidak sesuai theme
**Cause**: Dark mode state tidak propagate ke INACBGPanel  
**Solution**: Verify `isDark` prop passed correctly dari AdminRSDashboard

### Issue 3: Tarif tidak diformat Rupiah
**Cause**: `formatRupiah` function issue  
**Solution**: Check browser console for errors, verify Intl.NumberFormat support

### Issue 4: Warning section tidak muncul
**Cause**: Mock data warnings array kosong/undefined  
**Solution**: Normal behavior jika tidak ada warnings

### Issue 5: Empty state terus menerus
**Cause**: Analysis belum dijalankan atau result null  
**Solution**: Generate analysis dulu, baru klik tab INACBG

---

## 📸 Expected Output Screenshots (Description)

### 1. Tab Header
```
[📋 Analisis Klinis]  [💰 INACBG]
     (gray bg)         (cyan bg - ACTIVE)
```

### 2. CBG Code Section
```
┌─────────────────────────────────────┐
│  I-4-10-I                    [80%] │
│  INFARK MYOKARD AKUT (RINGAN)      │
└─────────────────────────────────────┘
```

### 3. Tarif Display
```
Main: Rp 5.770.100 (large, gradient bg)
Grid: [Kelas 1: Rp 5.7M*] [Kelas 2: Rp 5.0M] [Kelas 3: Rp 4.3M]
      *highlighted
```

---

## 🔍 Debug Tips

### Check Console Logs
```javascript
// Should see these logs after analysis:
[Generate Analysis] Request data: {...}
[Generate Analysis] Completed in XXXms
[ICD-10] Selected: XXX - YYY
```

### Inspect React DevTools
```
AdminRSDashboard
├── resultViewMode: "inacbg" (when INACBG tab active)
├── inacbgResult: {success: true, cbg_code: "I-4-10-I", ...}
└── INACBGPanel
    └── result: {success: true, cbg_code: "I-4-10-I", ...}
```

### Network Tab (Future - when backend ready)
```
POST /api/inacbg/analyze
Status: 200 OK
Response: {success: true, ...}
```

---

## 🎓 For Developers

### Code Locations
```
Component:      web/src/components/INACBGPanel.tsx
Integration:    web/src/components/AdminRSDashboard.tsx (line ~310, ~660)
Types:          web/src/lib/supabase.ts
Demo:           web/src/components/INACBGDemo.tsx
```

### Mock Data Location
```typescript
// File: web/src/components/AdminRSDashboard.tsx
// Line: ~310 (after setResult)

const mockINACBG: INACBGResult = {
  success: true,
  cbg_code: "I-4-10-I",
  // ... rest of mock data
};
setInacbgResult(mockINACBG);
```

### Modify Mock Data
Edit `AdminRSDashboard.tsx` line ~310 untuk test dengan data berbeda:
```typescript
const mockINACBG: INACBGResult = {
  success: true,
  cbg_code: "A-1-05-II",  // Change this
  description: "TEST DIAGNOSIS",  // Change this
  tarif: 10000000.0,  // Change this
  // ... modify other fields as needed
};
```

---

## 📝 Next Steps After Testing

1. ✅ Verify all checklist items above
2. ✅ Take screenshots (optional)
3. ✅ Report any bugs/issues found
4. ⏳ Wait for backend service merge
5. ⏳ Replace mock data with real API call
6. ⏳ Test with production data
7. ⏳ Deploy to staging/production

---

## 💬 Feedback & Issues

Jika menemukan bug atau punya saran improvement:

1. Check console untuk error messages
2. Screenshot issue (jika visual bug)
3. Note steps to reproduce
4. Report ke team lead atau create issue

---

**Happy Testing!** 🚀

---

**Quick Links**:
- [Full Documentation](./INACBG_UI_README.md)
- [Implementation Summary](../INACBG_UI_IMPLEMENTATION.md)
- [Visual Guide](./INACBG_UI_VISUAL_GUIDE.md)
