# 🧪 Test Plan - Revisi ICD-10 Explorer

## 📋 Revisi yang Diimplementasikan

### **1. Auto-Select HEAD Code untuk Kategori Tanpa Sub-Kode**
**Implementasi:**
- Jika kategori tidak memiliki sub-kode spesifik, HEAD code langsung dipilih sebagai mapping
- User tidak perlu klik lagi, langsung ready untuk Generate AI

**Logika:**
```typescript
// Di loadICD10Hierarchy()
if (!firstCategory.details || firstCategory.details.length === 0) {
  setSelectedSubCode(firstCategory.headCode);
  onCodeSelected?.(firstCategory.headCode, firstCategory.headName);
}

// Di handleSelectCategory()
if (category.details.length === 0) {
  setSelectedSubCode(headCode);
  onCodeSelected?.(headCode, category.headName);
}
```

### **2. Loading State pada Button Generate AI Analysis**
**Implementasi:**
- Button disabled saat `isAnalyzing = true`
- Tampil spinner + text "Analyzing..."
- Sama seperti button di input form

**UI States:**
```typescript
// Normal state
<Sparkles icon> Generate AI Analysis (J15.2)

// Loading state
<Spinner animation> Analyzing...

// Disabled state
Gray background, cursor-not-allowed
```

---

## 🧪 Test Scenarios

### **Test 1: Kategori dengan Sub-Kode**
**Input:** "pneumonia bakteri"
**Expected Translation:** "bacterial pneumonia"
**Expected Result:**
1. ✅ Panel Categories: J15 (10 sub-codes)
2. ✅ Panel Details: J15.0, J15.2, J15.9, etc.
3. ✅ Panel Mapping: Empty state (belum pilih)
4. ⚠️ Selected Code Indicator: **TIDAK MUNCUL** (belum pilih)
5. ⚠️ Generate Button: **TIDAK MUNCUL** (karena selectedSubCode = null)

**Action:** Click J15.2
**Expected After Click:**
1. ✅ Selected Code Indicator: "✓ J15.2"
2. ✅ Panel Mapping: Preview muncul dengan J15.2
3. ✅ Generate Button: **MUNCUL** dengan text "Generate AI Analysis (J15.2)"

**Action:** Click Generate Button
**Expected:**
1. ✅ Button disabled (gray)
2. ✅ Spinner muncul
3. ✅ Text berubah "Analyzing..."
4. ✅ Setelah selesai: Result panel muncul dengan ICD-10 = J15.2

---

### **Test 2: Kategori TANPA Sub-Kode (Auto-Select HEAD)**
**Input:** "alergi obat"
**Expected Translation:** "drug allergy"
**Expected Result:**
1. ✅ Panel Categories: T88 (0 sub-codes) atau Y57 atau Z88
2. ✅ Panel Details: "Tidak ada sub-kode ditemukan untuk T88"
3. ✅ Selected Code Indicator: **LANGSUNG MUNCUL "✓ T88"** ⭐
4. ✅ Panel Mapping: **LANGSUNG PREVIEW** dengan T88 sebagai code ⭐
5. ✅ Generate Button: **LANGSUNG MUNCUL** dengan text "Generate AI Analysis (T88)" ⭐

**Action:** Click Generate Button (tanpa perlu klik subcode)
**Expected:**
1. ✅ Button disabled (gray)
2. ✅ Spinner muncul
3. ✅ Text berubah "Analyzing..."
4. ✅ Setelah selesai: Result panel muncul dengan ICD-10 = T88

---

### **Test 3: Switch Category (dari Ada Sub-Kode → Tidak Ada Sub-Kode)**
**Input:** "pneumonia"
**Expected Categories:** J12, J13, J15, J18, dll

**Initial State:**
- J12 auto-selected (ada 6 sub-codes)
- Panel Details: J12.0, J12.1, J12.2, dll.
- Panel Mapping: Empty (belum pilih)

**Action:** Click category **J13** (category tanpa sub-code)
**Expected:**
1. ✅ Panel Details: "Tidak ada sub-kode ditemukan untuk J13"
2. ✅ Selected Code Indicator: **LANGSUNG "✓ J13"** ⭐
3. ✅ Panel Mapping: **LANGSUNG PREVIEW** dengan J13 ⭐
4. ✅ Generate Button: **LANGSUNG MUNCUL** ⭐

---

### **Test 4: Loading State - Full Journey**
**Setup:** Input "radang paru paru bakteri"

**Step 1: Initial Generate (Translation)**
- Click "Generate AI Insight" button di input form
- Expected: Button loading, text "Translating..."

**Step 2: Select Code**
- Translation success → J15 categories
- Click J15.2 subcode

**Step 3: Generate AI Analysis**
- Click "Generate AI Analysis (J15.2)" di panel mapping
- Expected:
  1. ✅ Button disabled immediately
  2. ✅ Background: `bg-slate-700` (dark) or `bg-gray-300` (light)
  3. ✅ Text color: `text-slate-400` (dark) or `text-gray-500` (light)
  4. ✅ Cursor: `cursor-not-allowed`
  5. ✅ Content: `<spinner> Analyzing...`

**Step 4: Analysis Complete**
- Expected:
  1. ✅ Button back to normal (gradient blue/cyan)
  2. ✅ Result panel shows analysis
  3. ✅ ICD-10 code in result = J15.2

---

### **Test 5: Empty State Validation**
**Scenario A: No Category Selected**
- Panel Details: Empty state icon "Pilih kategori..."
- Panel Mapping: Empty state icon "Pilih sub-kode..."
- Generate Button: **TIDAK MUNCUL**

**Scenario B: Category Selected, No Sub-Code, Has Details**
- Panel Details: List of subcodes (J15.0, J15.2, etc.)
- Panel Mapping: Empty state "Pilih sub-kode..."
- Generate Button: **TIDAK MUNCUL**

**Scenario C: Category Selected, No Details (Auto-Select)**
- Panel Details: "Tidak ada sub-kode ditemukan"
- Panel Mapping: **PREVIEW MUNCUL** dengan HEAD code
- Generate Button: **MUNCUL**

---

## 🎯 Validation Checklist

### **Auto-Select HEAD Code:**
- [ ] HEAD code dipilih otomatis saat category memiliki 0 details
- [ ] `onCodeSelected` dipanggil dengan HEAD code
- [ ] Selected Code Indicator langsung muncul
- [ ] Panel Mapping langsung show preview
- [ ] Generate Button langsung enabled

### **Loading State:**
- [ ] Button disabled saat `isAnalyzing = true`
- [ ] Spinner animation muncul
- [ ] Text berubah "Analyzing..."
- [ ] Background berubah ke gray/slate
- [ ] Cursor jadi `cursor-not-allowed`
- [ ] Button kembali normal setelah analysis selesai

### **User Experience:**
- [ ] Tidak ada klik berlebihan untuk category tanpa sub-code
- [ ] Loading feedback jelas (user tahu system sedang process)
- [ ] Konsisten dengan button di input form
- [ ] Transition smooth (disabled ↔ enabled)

---

## 🚀 How to Test

### **1. Start Services**
```bash
# Terminal 1: Core Engine
cd /home/shunkazama/Documents/Kerja/AI-ClaimLite/core_engine
python main.py

# Terminal 2: Web Dev Server
cd /home/shunkazama/Documents/Kerja/AI-ClaimLite/web
npm run dev
```

### **2. Open Browser**
```
http://localhost:5173
```

### **3. Login as Admin RS**
- Username: admin_rs
- Password: (your password)

### **4. Run Test Scenarios**

**Test Auto-Select (Category tanpa sub-code):**
1. Input Diagnosis: "alergi antibiotik"
2. Click "Generate AI Insight"
3. Wait for translation
4. ✅ Check: T88 or Z88 langsung selected?
5. ✅ Check: Mapping preview langsung muncul?
6. ✅ Check: Generate button langsung ready?

**Test Loading State:**
1. Input Diagnosis: "pneumonia staph"
2. Click "Generate AI Insight"
3. Wait → Select J15.2
4. Click "Generate AI Analysis (J15.2)"
5. ✅ Check: Button jadi gray + disabled?
6. ✅ Check: Spinner + "Analyzing..." muncul?
7. ✅ Check: Button kembali normal setelah selesai?

**Test Switch Category:**
1. Input Diagnosis: "pneumonia"
2. Click "Generate AI Insight"
3. J12 auto-selected (has subcodes)
4. Click category J13 (no subcodes)
5. ✅ Check: J13 langsung selected?
6. ✅ Check: Mapping preview langsung update?
7. ✅ Check: Generate button langsung ready?

---

## 📊 Expected vs Actual

| Test Case | Expected | Actual | Status |
|-----------|----------|--------|--------|
| Auto-select HEAD (load) | ✓ T88 selected | | ⏳ |
| Auto-select HEAD (switch) | ✓ J13 selected | | ⏳ |
| Loading - button disabled | ✓ Gray + disabled | | ⏳ |
| Loading - spinner visible | ✓ Spinner + text | | ⏳ |
| Loading - restore normal | ✓ Gradient + enabled | | ⏳ |
| Mapping preview (auto) | ✓ Shows HEAD code | | ⏳ |
| Generate button (auto) | ✓ Ready to click | | ⏳ |

---

## 🐛 Known Edge Cases

### **Edge Case 1: API Error During Translation**
- Translation fails → fallback to original term
- Categories load → auto-select first category
- ✅ Should still work (auto-select HEAD if no details)

### **Edge Case 2: Multiple Categories, All Without Sub-Codes**
- Example: "injury" → T00, T01, T02 (all HEAD only)
- First category (T00) auto-selected
- User can switch to T01 → auto-select T01
- User can switch to T02 → auto-select T02

### **Edge Case 3: Analysis Fails**
- Button in loading state
- API returns error
- ✅ Button should restore to normal (enabled)
- ✅ User can retry

---

## ✅ Success Criteria

**Revisi 1 (Auto-Select HEAD):**
- [x] Code implemented
- [ ] Manual test passed
- [ ] No console errors
- [ ] UX smooth (no extra clicks)

**Revisi 2 (Loading State):**
- [x] Code implemented
- [ ] Manual test passed
- [ ] Visual feedback clear
- [ ] Consistent with input button

**Overall:**
- [ ] All test scenarios passed
- [ ] Edge cases handled
- [ ] User feedback positive
- [ ] Ready for production

---

**Test Date:** _________  
**Tester:** _________  
**Result:** ⏳ Pending / ✅ Pass / ❌ Fail  
**Notes:** _________
