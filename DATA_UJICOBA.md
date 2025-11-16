# Data Ujicoba Sistem AI-ClaimLite

## 📋 Panduan Penggunaan

### Langkah-langkah Testing:
1. Login ke sistem sebagai Admin RS
2. Pilih mode input (Form Input atau Free Text)
3. Masukkan data diagnosis, tindakan, dan obat
4. Klik "Generate AI Insight" untuk mendapatkan saran kode ICD
5. Pilih kode ICD-10 dan ICD-9 yang sesuai
6. Klik "Generate AI Analysis" untuk mendapatkan analisis lengkap

---

## 🏥 Skenario 1: Pneumonia Varicella (Rawat Inap)

### Form Input Mode:
```
Diagnosis: Pneumonia varicella
Tindakan: Injeksi antibiotik, Rontgen thorax
Obat: Ceftriaxone 1g, Paracetamol 500mg, Acyclovir 800mg
```

### Kode ICD yang Sesuai:
- **ICD-10**: B01.2 - Varicella pneumonia
- **ICD-9**: 99.21 - Injection of antibiotic

### Expected Results:
- Validasi Klinis: ✅ Sesuai
- Fornas Status: ✅ Sesuai
- CP Nasional: Tersedia panduan rawat inap pneumonia
- Dokumen Wajib: Resume medis, Hasil lab, Foto thorax

---

## 🩺 Skenario 2: Diabetes Mellitus Type 2 dengan Hipertensi

### Form Input Mode:
```
Diagnosis: Diabetes melitus tipe 2 dengan hipertensi
Tindakan: Pemeriksaan gula darah, EKG
Obat: Metformin 500mg, Glimepiride 2mg, Amlodipine 10mg
```

### Kode ICD yang Sesuai:
- **ICD-10**: E11.9 - Type 2 diabetes mellitus without complications
- **ICD-10 Sekunder**: I10 - Essential (primary) hypertension
- **ICD-9**: 89.65 - Measurement of systemic arterial blood gases

### Expected Results:
- Validasi Klinis: ✅ Sesuai
- Fornas Status: ✅ Sesuai (semua obat ada di Fornas)
- CP Nasional: Panduan pengelolaan DM tipe 2
- Tingkat Konsistensi: Tinggi

---

## 🤢 Skenario 3: Gastritis Akut (Rawat Jalan)

### Form Input Mode:
```
Diagnosis: Gastritis akut
Tindakan: Endoskopi lambung
Obat: Omeprazole 20mg, Sucralfate syrup, Domperidone 10mg
```

### Kode ICD yang Sesuai:
- **ICD-10**: K29.0 - Acute gastritis
- **ICD-9**: 45.13 - Other endoscopy of small intestine

### Expected Results:
- Validasi Klinis: ✅ Sesuai
- Fornas Status: ✅ Sesuai
- CP Nasional: Panduan tata laksana gastritis
- Dokumen Wajib: Hasil endoskopi, Resume medis

---

## 🔪 Skenario 4: Appendisitis Akut dengan Operasi

### Form Input Mode:
```
Diagnosis: Appendisitis akut
Tindakan: Appendektomi laparoskopi, Pemasangan infus
Obat: Ceftriaxone 1g IV, Metronidazole 500mg IV, Ketorolac 30mg
```

### Kode ICD yang Sesuai:
- **ICD-10**: K35.80 - Unspecified acute appendicitis
- **ICD-9**: 47.01 - Laparoscopic appendectomy

### Expected Results:
- Validasi Klinis: ✅ Sesuai
- Fornas Status: ✅ Sesuai
- CP Nasional: Panduan tindakan bedah appendisitis
- Dokumen Wajib: Informed consent, Laporan operasi, Resume medis

---

## 🫁 Skenario 5: Pneumonia Bakterial (Rawat Inap ICU)

### Form Input Mode:
```
Diagnosis: Pneumonia bakterial berat
Tindakan: Pemasangan ventilator, Foto thorax serial, Pemeriksaan lab lengkap
Obat: Meropenem 1g IV, Levofloxacin 750mg IV, Dexamethasone 4mg
```

### Kode ICD yang Sesuai:
- **ICD-10**: J15.9 - Unspecified bacterial pneumonia
- **ICD-9**: 96.04 - Insertion of endotracheal tube

### Expected Results:
- Validasi Klinis: ✅ Sesuai
- Fornas Status: ⚠️ Perlu Justifikasi (Meropenem butuh justifikasi penggunaan)
- CP Nasional: Panduan rawat ICU pneumonia berat
- Tingkat Konsistensi: Tinggi
- Severity: Berat

---

## 💊 Skenario 6: Hipertensi Esensial (Rawat Jalan)

### Form Input Mode:
```
Diagnosis: Hipertensi esensial
Tindakan: Pengukuran tekanan darah, EKG
Obat: Amlodipine 5mg, Captopril 25mg, Hydrochlorothiazide 12.5mg
```

### Kode ICD yang Sesuai:
- **ICD-10**: I10 - Essential (primary) hypertension
- **ICD-9**: 89.52 - Electrocardiogram

### Expected Results:
- Validasi Klinis: ✅ Sesuai
- Fornas Status: ✅ Sesuai
- CP Nasional: Panduan tata laksana hipertensi
- Tingkat Konsistensi: Tinggi

---

## 🧠 Skenario 7: Stroke Iskemik Akut

### Form Input Mode:
```
Diagnosis: Stroke iskemik akut hemisfer kiri
Tindakan: CT scan kepala, Pemasangan NGT, Fisioterapi
Obat: Citicoline 500mg IV, Aspirin 80mg, Simvastatin 20mg
```

### Kode ICD yang Sesuai:
- **ICD-10**: I63.9 - Cerebral infarction, unspecified
- **ICD-9**: 87.03 - Computerized axial tomography of head

### Expected Results:
- Validasi Klinis: ✅ Sesuai
- Fornas Status: ✅ Sesuai
- CP Nasional: Panduan tata laksana stroke akut
- Dokumen Wajib: Hasil CT scan, Resume medis, Laporan fisioterapi

---

## 🦴 Skenario 8: Fraktur Femur dengan ORIF

### Form Input Mode:
```
Diagnosis: Fraktur tertutup femur kanan
Tindakan: ORIF femur dengan plate and screw, Foto rontgen femur
Obat: Cefazolin 1g IV, Ketorolac 30mg, Tramadol 50mg
```

### Kode ICD yang Sesuai:
- **ICD-10**: S72.90 - Unspecified fracture of unspecified femur
- **ICD-9**: 79.35 - Open reduction of fracture with internal fixation, femur

### Expected Results:
- Validasi Klinis: ✅ Sesuai
- Fornas Status: ✅ Sesuai
- CP Nasional: Panduan tindakan bedah ortopedi
- Dokumen Wajib: Informed consent, Laporan operasi, Foto rontgen pre/post op

---

## 🤰 Skenario 9: Sectio Caesarea

### Form Input Mode:
```
Diagnosis: Hamil aterm dengan indikasi sectio caesarea
Tindakan: Sectio caesarea transperitoneal, Pemasangan kateter urine
Obat: Cefazolin 1g IV, Oxytocin 10 IU, Asam Mefenamat 500mg
```

### Kode ICD yang Sesuai:
- **ICD-10**: O82.9 - Delivery by caesarean section, unspecified
- **ICD-9**: 74.1 - Low cervical cesarean section

### Expected Results:
- Validasi Klinis: ✅ Sesuai
- Fornas Status: ✅ Sesuai
- CP Nasional: Panduan sectio caesarea
- Dokumen Wajib: Informed consent, Partograf, Laporan operasi

---

## 🫀 Skenario 10: Infark Miokard Akut (IMA)

### Form Input Mode:
```
Diagnosis: Infark miokard akut STEMI inferior
Tindakan: Perekaman EKG serial, Pemeriksaan enzim jantung, Pemasangan IVFD
Obat: Aspirin 160mg, Clopidogrel 300mg, Atorvastatin 40mg, Bisoprolol 2.5mg
```

### Kode ICD yang Sesuai:
- **ICD-10**: I21.9 - Acute myocardial infarction, unspecified
- **ICD-9**: 89.52 - Electrocardiogram

### Expected Results:
- Validasi Klinis: ✅ Sesuai
- Fornas Status: ✅ Sesuai
- CP Nasional: Panduan tata laksana IMA STEMI
- Tingkat Konsistensi: Tinggi
- Severity: Berat

---

## 📝 Free Text Mode Examples

### Contoh 1:
```
Pasien datang dengan keluhan demam tinggi 3 hari, batuk berdahak, sesak napas. 
Dilakukan pemeriksaan fisik dan foto thorax. Hasil menunjukkan infiltrat pada 
paru kanan. Diberikan antibiotik ceftriaxone 2g IV per hari, paracetamol 3x500mg, 
dan mukolitik ambroxol 3x30mg. Diagnosis: Pneumonia bakterial komunitas.
```

**Expected ICD Suggestions:**
- ICD-10: J15.9 (Bacterial pneumonia)
- ICD-9: 87.44 (Routine chest x-ray), 99.21 (Injection of antibiotic)

### Contoh 2:
```
Pasien usia 55 tahun dengan riwayat DM tidak terkontrol, datang dengan luka 
di kaki kanan yang tidak sembuh-sembuh sejak 1 bulan. Dilakukan debridement 
luka dan kultur bakteri. Diberikan insulin rapid 3x8 unit, metformin 2x500mg, 
ceftriaxone 2g IV, dan perawatan luka harian.
```

**Expected ICD Suggestions:**
- ICD-10: E11.621 (Type 2 DM with foot ulcer)
- ICD-9: 86.22 (Excisional debridement of wound)

---

## ⚠️ Catatan Penting

### Data yang Harus Lengkap:
1. **Diagnosis**: Minimal 1 diagnosis utama
2. **Tindakan**: Minimal 1 tindakan medis
3. **Obat**: Minimal 1 obat yang diberikan

### Tips untuk Hasil Optimal:
1. Gunakan istilah medis yang jelas dan spesifik
2. Sertakan dosis obat untuk validasi yang lebih akurat
3. Pilih kode ICD yang paling spesifik sesuai kondisi pasien
4. Untuk kasus kompleks, gunakan mode Free Text untuk detail lebih lengkap

### Troubleshooting:
1. Jika error "Failed to analyze claim":
   - Pastikan core_engine berjalan di port 8000
   - Pastikan backend berjalan di port 3001
   - Cek log console untuk detail error
   - Pastikan data input lengkap dan valid

2. Jika limit AI habis:
   - Hubungi Admin Meta untuk reset limit
   - Atau tunggu hingga hari berikutnya (reset otomatis)

3. Jika hasil tidak sesuai:
   - Periksa kembali kode ICD yang dipilih
   - Gunakan istilah medis yang lebih spesifik
   - Coba mode input yang berbeda (Form vs Free Text)

---

## 🚀 Quick Start

1. Pilih **Skenario 1** (paling simple) untuk ujicoba awal
2. Copy-paste data ke form input
3. Klik "Generate AI Insight"
4. Pilih kode ICD-10: **B01.2**
5. Pilih kode ICD-9: **99.21**
6. Klik "Generate AI Analysis"
7. Review hasil analisis lengkap

---

**Update**: November 15, 2025
**Version**: 1.0
**Author**: AI-ClaimLite Team
