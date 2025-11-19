# 🔍 Parse Resume Medis Flow

## Alur Baru: Parsing Terpisah dari Analisis

### 1. User Flow

```
User mengisi Resume Medis (Free Text)
         ↓
Klik tombol "🔍 Parse & Analyze"
         ↓
AI parsing ekstrak: Diagnosis, Tindakan, Obat
         ↓
Form auto-filled dengan hasil parsing
         ↓
Badge hijau muncul: "✓ Form auto-filled dari resume medis"
         ↓
User review & edit form jika perlu
         ↓
Klik "Generate AI Insight"
         ↓
AI analisis ICD codes berdasarkan form data
         ↓
Tampilkan ICD-10 & ICD-9 categories
```

### 2. Technical Flow

#### Frontend (AdminRSDashboard.tsx)

1. **Parse Button**
   ```typescript
   // Tombol muncul ketika freeText terisi dan belum parsed
   {freeText.trim() && !isParsed && (
     <button onClick={handleParseResume}>
       🔍 Parse & Analyze
     </button>
   )}
   ```

2. **handleParseResume Function**
   ```typescript
   const handleParseResume = async () => {
     // Call API untuk parsing
     const parseResponse = await apiService.parseResumeMedis(freeText);
     
     // Auto-fill form dari hasil parsing
     setDiagnosis(parsed.diagnosis);
     setProcedure(parsed.tindakan);
     setMedication(parsed.obat);
     
     // Set flag parsed
     setIsParsed(true);
   }
   ```

3. **handleGenerate Function**
   ```typescript
   const handleGenerate = async () => {
     // Langsung translate diagnosis/procedure dari form
     // TIDAK ada auto-parsing lagi di sini
     
     const inputTerm = diagnosis || freeText;
     const procedureTerm = procedure || '';
     
     // Translate & tampilkan ICD hierarchy
     // ...
   }
   ```

#### Backend (Express/Node - aiRoutes.ts)

1. **POST /api/ai/parse-resume**
   ```typescript
   router.post('/parse-resume', async (req, res) => {
     // Tidak increment AI usage count
     // Hanya parsing saja
     
     const response = await axios.post(
       `${CORE_ENGINE_URL}/api/lite/parse-text`,
       { input_text: resume_text }
     );
     
     res.json({
       success: true,
       data: {
         diagnosis: parsed.diagnosis,
         tindakan: parsed.tindakan,
         obat: parsed.obat
       }
     });
   });
   ```

2. **POST /api/ai/analyze**
   ```typescript
   router.post('/analyze', async (req, res) => {
     // Increment AI usage count
     // Analisis ICD codes
     
     const payload = {
       mode: 'form', // Selalu form setelah parsing
       diagnosis,
       tindakan: procedure,
       obat: medication,
       icd10_code,
       icd9_code
     };
     
     // Increment usage AFTER success
     await authService.incrementAIUsage(userId);
   });
   ```

#### Core Engine (Python - lite_endpoints.py)

1. **POST /api/lite/parse-text**
   ```python
   def endpoint_parse_text(request_data):
       input_text = request_data.get("input_text", "")
       
       # Parse menggunakan AI (OpenAI)
       parsed = parse_free_text(input_text)
       
       return {
           "status": "success",
           "result": {
               "diagnosis": parsed.get("diagnosis", ""),
               "tindakan": parsed.get("tindakan", ""),
               "obat": parsed.get("obat", "")
           }
       }
   ```

2. **parse_free_text (services/lite_service.py)**
   ```python
   def parse_free_text(text: str) -> Dict[str, Any]:
       parser = get_parser()
       return parser.parse(text, input_mode="text")
   ```

### 3. API Contract

#### Parse Resume API

**Request:**
```json
POST /api/ai/parse-resume
{
  "resume_text": "Pasien didiagnosa pneumonia berat dengan saturasi oksigen rendah. Dilakukan nebulisasi dan foto thorax. Diberikan ceftriaxone injeksi 1g dan paracetamol 500mg."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "diagnosis": "Pneumonia berat",
    "tindakan": "Nebulisasi, Foto thorax",
    "obat": "Ceftriaxone injeksi 1g, Paracetamol 500mg"
  }
}
```

#### Analyze Claim API

**Request:**
```json
POST /api/ai/analyze
{
  "mode": "form",
  "diagnosis": "Pneumonia berat",
  "procedure": "Nebulisasi, Foto thorax",
  "medication": "Ceftriaxone injeksi 1g, Paracetamol 500mg",
  "icd10_code": null,
  "icd9_code": null
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "klasifikasi": { ... },
    "metadata": { ... }
  },
  "usage": {
    "used": 5,
    "remaining": 95,
    "limit": 100
  }
}
```

### 4. Perbedaan dengan Flow Lama

| Aspek | Flow Lama | Flow Baru |
|-------|-----------|-----------|
| Parsing | Otomatis saat Generate | Manual via tombol terpisah |
| AI Usage | 1x untuk parsing + analisis | 1x hanya untuk analisis |
| User Control | Tidak bisa review hasil parsing | Bisa review & edit sebelum analisis |
| Button | 1 tombol "Generate AI Insight" | 2 tombol: "Parse & Analyze" + "Generate AI Insight" |
| Form Auto-fill | Tidak ada feedback | Ada badge hijau konfirmasi |

### 5. Benefits

✅ **User lebih punya kontrol**: Bisa review & edit hasil parsing sebelum analisis  
✅ **AI usage lebih hemat**: Parsing tidak dihitung ke limit  
✅ **Feedback lebih jelas**: Badge hijau menunjukkan form sudah auto-filled  
✅ **Separation of concerns**: Parsing terpisah dari analisis ICD  
✅ **Flexibility**: User bisa edit form setelah parsing jika AI salah ekstraksi  

### 6. Future Enhancements

- [ ] Tambahkan confidence score untuk hasil parsing
- [ ] Highlight field yang di-auto-fill dengan warna berbeda
- [ ] Allow user to re-parse jika hasil kurang memuaskan
- [ ] Save parsing history untuk learning
- [ ] Show diff antara freeText vs hasil parsing
