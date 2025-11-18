# 📝 Kalimat Dummy untuk Testing Parse Resume Medis

## 🎯 Cara Menggunakan:
1. Copy salah satu contoh dibawah
2. Paste ke field **"Resume Medis (Free Text)"**
3. Klik tombol **"✨ Generate AI Insight"**
4. Form akan auto-fill dengan hasil parsing dummy
5. Lihat ICD-10 dan ICD-9 yang muncul

---

## 📋 Contoh Resume Medis:

### 1. Pneumonia (Paru-paru Basah)
```
Pasien mengeluh sesak napas dan batuk berdahak sejak 3 hari yang lalu. 
Pada pemeriksaan fisik didapatkan suhu 38.5°C, saturasi oksigen 92%. 
Dilakukan foto rontgen thorax menunjukkan infiltrat pada lapangan paru kanan. 
Pasien didiagnosis dengan pneumonia dan diberikan terapi nebulisasi serta 
antibiotik ceftriaxone injeksi 1g IV setiap 12 jam dan paracetamol 500mg 
untuk menurunkan demam.
```

**Expected Output:**
- Diagnosis: Pneumonia
- Tindakan: Foto Rontgen Thorax, Nebulisasi
- Obat: Ceftriaxone injeksi 1g, Paracetamol 500mg

---

### 2. Diabetes Mellitus
```
Pasien datang dengan keluhan sering haus dan sering buang air kecil. 
Hasil pemeriksaan laboratorium menunjukkan gula darah puasa 250 mg/dL. 
Pasien didiagnosis diabetes mellitus tipe 2 dan diberi edukasi tentang 
pola makan. Terapi yang diberikan adalah metformin 500mg 2x sehari dan 
omeprazole 20mg untuk proteksi lambung.
```

**Expected Output:**
- Diagnosis: Diabetes Mellitus
- Tindakan: Pemeriksaan Laboratorium
- Obat: Metformin 500mg, Omeprazole 20mg

---

### 3. Hipertensi (Darah Tinggi)
```
Pasien mengeluh pusing dan kepala terasa berat. Tekanan darah 160/100 mmHg. 
Dilakukan pemeriksaan EKG untuk evaluasi jantung. Pasien didiagnosis 
hipertensi esensial dan diberikan terapi amlodipine 5mg sekali sehari 
serta anjuran diet rendah garam.
```

**Expected Output:**
- Diagnosis: Hipertensi
- Tindakan: Pemeriksaan EKG
- Obat: Amlodipine 5mg

---

### 4. Diare Akut
```
Pasien anak 5 tahun datang dengan keluhan mencret 6 kali sejak pagi, 
muntah 2 kali. Turgor kulit menurun, mukosa bibir kering. Dilakukan 
pemasangan infus RL untuk rehidrasi. Diberikan terapi zinc dan oralit 
untuk diminum dirumah.
```

**Expected Output:**
- Diagnosis: Diare Akut
- Tindakan: Pemasangan Infus
- Obat: Simptomatik (zinc, oralit)

---

### 5. Tuberkulosis Paru
```
Pasien mengeluh batuk lama lebih dari 2 minggu, berat badan turun, 
keringat malam. Hasil foto thorax menunjukkan lesi pada apex paru kanan. 
Pemeriksaan dahak BTA positif. Pasien didiagnosis TB paru dan dirujuk 
untuk program DOTS. Diberikan terapi OAT kombinasi dan vitamin B6.
```

**Expected Output:**
- Diagnosis: Tuberkulosis Paru
- Tindakan: Foto Rontgen Thorax, Pemeriksaan Laboratorium
- Obat: Simptomatik

---

### 6. Kombinasi Lengkap (Testing All Features)
```
Pasien laki-laki 45 tahun datang ke IGD dengan keluhan sesak napas berat 
sejak 1 hari yang lalu. Riwayat DM dan hipertensi tidak terkontrol. 
Pemeriksaan fisik: TD 180/110 mmHg, RR 32x/menit, saturasi 88% room air.
Hasil foto rontgen thorax menunjukkan infiltrat bilateral dan kardiomegali.
Dilakukan pemasangan infus dan pemberian oksigen 5 lpm. Pemeriksaan EKG 
menunjukkan LVH. Pemeriksaan lab: GDS 350 mg/dL, ureum kreatinin meningkat.
Pasien didiagnosis pneumonia dengan komplikasi gagal jantung kongestif dan 
diabetes mellitus tidak terkontrol. Terapi yang diberikan: nebulisasi dengan 
combivent, ceftriaxone injeksi 2g IV/12 jam, furosemide 40mg IV, insulin 
drip, amlodipine 10mg, metformin 500mg, dan paracetamol 500mg.
```

**Expected Output:**
- Diagnosis: Pneumonia
- Tindakan: Foto Rontgen Thorax, Nebulisasi, Pemasangan Infus, Pemeriksaan EKG, Pemeriksaan Laboratorium
- Obat: Ceftriaxone injeksi 1g, Paracetamol 500mg, Metformin 500mg, Amlodipine 5mg, Omeprazole 20mg

---

## 🔍 Keyword Detection (Dummy Parser Logic):

### Diagnosis Keywords:
- **Pneumonia**: pneumonia, paru, paru basah
- **Diabetes Mellitus**: diabetes, gula, dm
- **Hipertensi**: hipertensi, darah tinggi, tensi
- **Demam**: demam, panas
- **Diare**: diare, mencret
- **Tuberkulosis**: tbc, tuberkulosis, tb

### Tindakan Keywords:
- **Foto Rontgen**: rontgen, xray, x-ray, foto thorax
- **Nebulisasi**: nebulisasi, nebul
- **Infus**: infus, iv
- **EKG**: ekg, jantung
- **Lab**: lab, darah lengkap, cek darah

### Obat Keywords:
- **Ceftriaxone**: ceftriaxone, antibiotik
- **Paracetamol**: paracetamol, panadol, penurun panas
- **Amoxicillin**: amoxicillin, amoxilin
- **Metformin**: metformin
- **Amlodipine**: amlodipine
- **Omeprazole**: omeprazole

---

## ✨ Next Steps:

Setelah dummy parser bekerja dengan baik, kita akan:
1. Replace dummy parser dengan **real AI parsing** (OpenAI API)
2. Tambahkan **confidence score** untuk setiap hasil parsing
3. Implementasi **edit suggestion** jika parsing kurang akurat
4. Simpan **parsing history** untuk improvement

Untuk saat ini, gunakan contoh-contoh di atas untuk testing UI flow! 🚀
