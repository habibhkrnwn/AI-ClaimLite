# Fix: Reset Flow untuk Free Text Parsing

## Problem
Ketika user mengisi free text → parsing → form terisi, lalu user ingin mengisi free text lagi:
- ❌ Data form lama masih terkirim
- ❌ ICD results lama masih tampil
- ❌ Tidak ada reset otomatis

## Solution Implemented

### 1. **Deteksi Input Mode saat Generate**
```typescript
// Old Logic (BROKEN)
if (freeText.trim() && !diagnosis && !procedure && !medication) {
  // Hanya parse jika form kosong
}

// New Logic (FIXED)
if (inputMode === 'text' && freeText.trim()) {
  // SELALU reset form dulu sebelum parsing
  setDiagnosis('');
  setProcedure('');
  setMedication('');
  
  // Parse free text
  const dummyParsedData = parseDummyText(freeText);
  // ... auto-fill
}
```

**Key Change**: Menggunakan `inputMode === 'text'` sebagai penanda, bukan cek form kosong.

---

### 2. **Auto-Clear ketika Edit Free Text**
```typescript
const handleFreeTextChange = (value: string) => {
  setFreeText(value);
  if (isParsed) {
    setIsParsed(false);
    
    // Clear form fields when editing free text after parsing
    if (inputMode === 'text') {
      setDiagnosis('');
      setProcedure('');
      setMedication('');
      
      // Clear ICD results
      setShowICD10Explorer(false);
      setShowICD9Explorer(false);
      setResult(null);
      setSelectedICD10Code(null);
      setSelectedICD9Code(null);
    }
  }
};
```

**Trigger**: Ketika user mulai mengetik di free text SETELAH pernah parsing.

---

### 3. **Handler untuk Mode Toggle**
```typescript
const handleInputModeChange = (mode: InputMode) => {
  // If switching to Free Text mode after parsing, clear everything
  if (mode === 'text' && isParsed) {
    setDiagnosis('');
    setProcedure('');
    setMedication('');
    setIsParsed(false);
    
    // Clear ICD results
    setShowICD10Explorer(false);
    setShowICD9Explorer(false);
    setResult(null);
    setSelectedICD10Code(null);
    setSelectedICD9Code(null);
  }
  setInputMode(mode);
};
```

**Trigger**: Ketika user klik toggle "Free Text" setelah pernah parsing.

---

## User Flow (Corrected)

### Scenario 1: First Time Parsing
```
1. User pilih mode "Free Text"
2. User ketik: "Pasien pneumonia dengan foto rontgen..."
3. Klik "Generate AI Insight"
4. ✅ Parsing runs
5. ✅ Auto-switch ke Form Input
6. ✅ Form terisi: Diagnosis=Pneumonia, Tindakan=Rontgen, dst
7. ✅ ICD codes muncul
```

### Scenario 2: Parsing Ulang (FIXED)
```
1. User klik toggle "Free Text" lagi
2. ✅ Form di-clear otomatis
3. ✅ ICD results hilang
4. User ketik resume baru: "Pasien diabetes dengan cek gula darah..."
5. Klik "Generate AI Insight"
6. ✅ Form di-reset dulu (clear diagnosis/tindakan lama)
7. ✅ Parsing resume baru
8. ✅ Form terisi dengan data baru: Diagnosis=Diabetes, Tindakan=Lab, dst
9. ✅ ICD codes baru muncul
```

### Scenario 3: Edit Free Text saat Parsed
```
1. User sudah parsing (form terisi, ICD muncul)
2. User klik toggle "Free Text"
3. ✅ Form & ICD results di-clear
4. User edit free text (tambah/ubah teks)
5. ✅ Form & ICD results langsung clear
6. User klik "Generate AI Insight"
7. ✅ Parsing ulang dengan teks baru
```

---

## Code Changes Summary

### File: `AdminRSDashboard.tsx`

**1. handleGenerate() - Line ~180**
```diff
- if (freeText.trim() && !diagnosis && !procedure && !medication) {
+ if (inputMode === 'text' && freeText.trim()) {
+   // Reset form first
+   setDiagnosis('');
+   setProcedure('');
+   setMedication('');
```

**2. handleFreeTextChange() - Line ~115**
```diff
  if (isParsed) {
    setIsParsed(false);
+   if (inputMode === 'text') {
+     setDiagnosis('');
+     setProcedure('');
+     setMedication('');
+     // Clear ICD results
+     setShowICD10Explorer(false);
+     setShowICD9Explorer(false);
+     // ... etc
+   }
  }
```

**3. New Handler: handleInputModeChange() - Line ~159**
```typescript
const handleInputModeChange = (mode: InputMode) => {
  if (mode === 'text' && isParsed) {
    // Clear everything for fresh start
    setDiagnosis('');
    setProcedure('');
    setMedication('');
    setIsParsed(false);
    setShowICD10Explorer(false);
    setShowICD9Explorer(false);
    setResult(null);
    setSelectedICD10Code(null);
    setSelectedICD9Code(null);
  }
  setInputMode(mode);
};
```

**4. Toggle Buttons - Line ~620**
```diff
- onClick={() => setInputMode('text')}
+ onClick={() => handleInputModeChange('text')}

- onClick={() => setInputMode('form')}
+ onClick={() => handleInputModeChange('form')}
```

---

## Testing Checklist

### Test 1: First Parsing
- [ ] Mode "Free Text" aktif
- [ ] Isi free text dengan example
- [ ] Klik Generate
- [ ] Verify: Form terisi otomatis
- [ ] Verify: Switch ke Form Input mode
- [ ] Verify: ICD codes muncul

### Test 2: Re-parsing (Main Fix)
- [ ] Setelah parsing pertama selesai
- [ ] Klik toggle "Free Text" lagi
- [ ] Verify: Form cleared (diagnosis/tindakan/obat kosong)
- [ ] Verify: ICD results hilang
- [ ] Isi free text BARU
- [ ] Klik Generate
- [ ] Verify: Form di-reset sebelum parsing
- [ ] Verify: Form terisi dengan data BARU (bukan data lama)
- [ ] Verify: ICD codes BARU muncul (bukan ICD lama)

### Test 3: Edit Free Text saat Parsed
- [ ] Setelah parsing selesai
- [ ] Toggle ke "Free Text"
- [ ] Mulai edit/ketik di textarea
- [ ] Verify: Form cleared immediately
- [ ] Verify: ICD results cleared

### Test 4: Form Mode (Unchanged)
- [ ] Mode "Form Input"
- [ ] Isi ketiga field manual
- [ ] Klik Generate
- [ ] Verify: Menggunakan input form langsung
- [ ] Verify: No parsing, direct translation

---

## Key Improvements

### Before:
```
User 1st parse → form filled ✓
User 2nd parse → USES OLD FORM DATA ✗
```

### After:
```
User 1st parse → form filled ✓
User click Free Text → CLEAR FORM ✓
User 2nd parse → RESET → PARSE NEW → form filled with NEW data ✓
```

---

## Edge Cases Handled

1. **User toggles Free Text → Form → Free Text**
   - ✅ Form cleared on return to Free Text if isParsed

2. **User edits free text mid-parsing**
   - ✅ Form cleared immediately on edit

3. **User switches to Form mode manually**
   - ✅ No clearing (user may want to edit parsed data)

4. **Multiple rapid toggles**
   - ✅ Handled by checking isParsed flag

---

## Notes

- `isParsed` flag tracks whether current form data came from parsing
- `inputMode` tracks active input method ('text' vs 'form')
- Clearing only happens when switching TO 'text' mode FROM parsed state
- Form mode behavior unchanged (direct input, no auto-clear)
