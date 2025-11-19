# 📋 Penambahan Field "Jenis Pelayanan" ke Form Input

## 🎯 Ringkasan Perubahan

Menambahkan field input keempat **"Jenis Pelayanan"** ke form analisis klaim. Form sekarang memiliki 4 field:
1. **Diagnosis**
2. **Tindakan**
3. **Obat**
4. **Jenis Pelayanan** (NEW) - Dropdown selection

---

## 📊 Opsi Jenis Pelayanan

Field "Jenis Pelayanan" menggunakan dropdown dengan 4 opsi:

| Value | Label Display |
|-------|---------------|
| `rawat-inap` | Rawat Inap |
| `rawat-jalan` | Rawat Jalan |
| `igd` | IGD (Instalasi Gawat Darurat) |
| `one-day-care` | One Day Care |

---

## 🔧 File yang Dimodifikasi

### 1. **Frontend UI** 
📁 `web/src/components/SmartInputPanel.tsx`

**Perubahan:**
- ✅ Menambahkan props `serviceType` dan `onServiceTypeChange`
- ✅ Menambahkan field dropdown "Jenis Pelayanan" dengan icon `Building2`
- ✅ Update validasi: button disabled jika `serviceType` kosong
- ✅ Menggunakan `<select>` element dengan 4 opsi

**Kode:**
```tsx
interface SmartInputPanelProps {
  // ... existing props
  serviceType: string;
  onServiceTypeChange: (value: string) => void;
}

// Field JSX:
<div className="space-y-2 flex-shrink-0">
  <label className={`flex items-center gap-2 text-sm font-medium`}>
    <Building2 className="w-4 h-4" />
    Jenis Pelayanan
  </label>
  <select
    value={serviceType}
    onChange={(e) => onServiceTypeChange(e.target.value)}
    className={...}
  >
    <option value="" disabled>Pilih jenis pelayanan...</option>
    <option value="rawat-inap">Rawat Inap</option>
    <option value="rawat-jalan">Rawat Jalan</option>
    <option value="igd">IGD (Instalasi Gawat Darurat)</option>
    <option value="one-day-care">One Day Care</option>
  </select>
</div>

// Validasi button:
disabled={
  isLoading || 
  !diagnosis.trim() || 
  !procedure.trim() || 
  !medication.trim() || 
  !serviceType.trim() ||  // NEW validation
  isLimitReached
}
```

---

### 2. **Parent Component - State Management**
📁 `web/src/components/AdminRSDashboard.tsx`

**Perubahan:**
- ✅ Menambahkan state `serviceType`
- ✅ Pass `serviceType` ke API request
- ✅ Clear `serviceType` saat mode switch
- ✅ Pass props ke `SmartInputPanel`

**Kode:**
```tsx
// State management (Line 26):
const [serviceType, setServiceType] = useState('');

// API request payload (Line 175):
const response = await axios.post('/api/ai/analyze', {
  mode: inputMode,
  diagnosis,
  procedure,
  medication,
  service_type: serviceType,  // NEW field
  // ... other fields
});

// Clear on mode switch (Line 462):
const handleModeChange = (newMode: InputMode) => {
  setInputMode(newMode);
  setServiceType('');  // Reset service type
};

// Pass to SmartInputPanel (Line 484-489):
<SmartInputPanel
  serviceType={serviceType}
  onServiceTypeChange={setServiceType}
  // ... other props
/>
```

---

### 3. **Backend API Validation**
📁 `web/server/routes/aiRoutes.ts`

**Perubahan:**
- ✅ Extract `service_type` dari request body
- ✅ Update validasi form mode (require 4 fields)
- ✅ Pass `service_type` ke core engine payload

**Kode:**
```typescript
// Extract from request (Line 17):
const { mode, diagnosis, procedure, medication, service_type, input_text } = req.body;

// Validation (Line 56-62):
if (!diagnosis || !procedure || !medication || !service_type) {
  res.status(400).json({
    success: false,
    message: 'Diagnosis, procedure, medication, and service type are required for form mode',
  });
  return;
}

// Payload to core engine (Line 75):
const payload = mode === 'text' 
  ? { /* text mode payload */ }
  : {
      mode: 'form',
      diagnosis: diagnosis,
      tindakan: procedure,
      obat: medication,
      service_type: service_type,  // NEW field
      // ... other fields
    };
```

---

### 4. **Core Engine - Python Backend**
📁 `core_engine/lite_endpoints.py`

**Perubahan:**
- ✅ Update validasi form mode (require 4 fields)
- ✅ Update docstring contoh payload

**Kode:**
```python
# Validation (Line 545-560):
elif mode == "form":
    # Validasi 4 field form
    diagnosis = request_data.get("diagnosis", "")
    tindakan = request_data.get("tindakan", "")
    obat = request_data.get("obat", "")
    service_type = request_data.get("service_type", "")
    
    errors = []
    if not diagnosis:
        errors.append("diagnosis required untuk mode form")
    if not tindakan:
        errors.append("tindakan required untuk mode form")
    if not obat:
        errors.append("obat required untuk mode form")
    if not service_type:
        errors.append("service_type required untuk mode form")

# Example payload documentation (Line 503-512):
// Mode FORM (4 field terpisah)
"diagnosis": "Pneumonia berat (J18.9)",
"tindakan": "Nebulisasi (93.96), Rontgen Thorax",
"obat": "Ceftriaxone injeksi 1g, Paracetamol 500mg",
"service_type": "rawat-inap",  // NEW: rawat-inap | rawat-jalan | igd | one-day-care
```

---

## 🧪 Testing Checklist

### Manual Testing:

✅ **UI Rendering:**
- [ ] Field "Jenis Pelayanan" muncul di form
- [ ] Dropdown memiliki 4 opsi yang benar
- [ ] Placeholder text "Pilih jenis pelayanan..." muncul
- [ ] Icon `Building2` muncul di label

✅ **Validation:**
- [ ] Button "Generate AI Insight" disabled jika service type kosong
- [ ] Button enabled jika semua 4 field terisi
- [ ] Error validation muncul di backend jika service_type missing

✅ **API Integration:**
- [ ] Request payload mengandung `service_type`
- [ ] Backend menerima dan validasi `service_type`
- [ ] Core engine menerima parameter `service_type`

✅ **State Management:**
- [ ] Service type ter-reset saat switch mode (Form ↔ Text)
- [ ] Service type tersimpan saat input berubah
- [ ] Service type dikirim ke API saat submit

---

## 🚀 Deployment Steps

1. **Restart Docker Containers:**
```bash
docker compose restart
```

2. **Verify Services Running:**
```bash
docker compose ps
```

Expected output:
```
aiclaimlite-core-engine    Up (healthy)   0.0.0.0:8000->8000/tcp
aiclaimlite-web-backend    Up (healthy)   0.0.0.0:3001->3001/tcp
aiclaimlite-web-frontend   Up             0.0.0.0:5173->5173/tcp
```

3. **Check Logs:**
```bash
docker compose logs --tail=50 web_frontend
docker compose logs --tail=50 web_backend
docker compose logs --tail=50 core_engine
```

4. **Test UI:**
- Open: http://localhost:5173
- Navigate to "AI Analysis" panel
- Verify "Jenis Pelayanan" dropdown appears
- Fill all 4 fields and submit

---

## 📝 Next Steps (Future Enhancements)

Untuk implementasi lanjutan, pertimbangkan:

1. **Business Logic Based on Service Type:**
   - Filter obat berdasarkan jenis pelayanan
   - Different CP Ringkas rules untuk rawat inap vs rawat jalan
   - Dokumen wajib berbeda per service type

2. **Database Schema:**
   - Add `service_type` column ke `analysis_history` table
   - Create analytics/reporting by service type

3. **AI Insight Integration:**
   - Use service type sebagai context untuk AI insight generation
   - Tailor recommendations based on service type

4. **Validation Rules:**
   - Create service-type-specific validation rules
   - Example: IGD should require certain procedures
   - One Day Care should limit certain medications

---

## 🔍 References

- **UI Input Logic Flow:** `UI_INPUT_LOGIC_FLOW.md`
- **Original 3-field architecture:** Documented in UI_INPUT_LOGIC_FLOW.md Section 2
- **7-Step Guide for Adding Fields:** UI_INPUT_LOGIC_FLOW.md Section 5

---

## ✅ Status

**Implementation Status:** ✅ **COMPLETE**

**Tested:** ⚠️ **Pending Manual Testing**

**Deployed:** ✅ **Docker containers restarted**

---

**Last Updated:** 2025-01-XX  
**Author:** AI Development Team  
**Version:** 1.0
