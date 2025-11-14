# 🚀 Quick Start: Test ICD-10 Smart Correction

## Prerequisites
✅ PostgreSQL running (port 5432)
✅ `icd10_master` table populated (18543 rows)
✅ Node.js 18+ installed

---

## Step 1: Start Backend Server

```bash
cd web
npm install
npm run dev
```

Expected output:
```
Server running on port 3001
✅ Connected to PostgreSQL database
```

---

## Step 2: Verify ICD-10 Data

Test endpoint manually:
```bash
curl "http://localhost:3001/api/ai/icd10-hierarchy?search=pneumonia" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected response:
```json
{
  "success": true,
  "data": {
    "search_term": "pneumonia",
    "categories": [
      {
        "headCode": "J12",
        "headName": "Viral pneumonia, not elsewhere classified",
        "count": 6,
        "details": [...]
      }
    ]
  }
}
```

---

## Step 3: Login & Test UI

1. **Open browser:** http://localhost:5173
2. **Login** sebagai Admin RS
3. **Navigate** ke dashboard utama

### Test Scenario A: Form Mode
```
1. Select "Form Input" mode
2. Diagnosis: paru2 basah
3. Tindakan: rawat inap 5 hari
4. Obat: ceftriaxone, azithromycin
5. Click "✨ Generate AI Insight"

✅ Expected:
   - Header shows: "paru2 basah" → ✨ "pneumonia"
   - 3 columns appear:
     • Left: Input summary
     • Center: J12, J13, J14, J15, J18 (categories)
     • Right: Empty (click J12 to populate)
   - Click "J12" → Right panel shows J12.0 to J12.9
   - Bottom panel shows analysis result
```

### Test Scenario B: Text Mode
```
1. Select "Free Text" mode
2. Input: Pasien paru-paru basah (pneumonia viral) dengan demam tinggi
3. Click "✨ Generate AI Insight"

✅ Expected:
   - Correction: "paru-paru basah" → "pneumonia"
   - Categories shown with J12 auto-selected
   - Details panel shows viral pneumonia subcodes
   - Analysis extracts diagnosis, tindakan, obat from text
```

---

## Step 4: Verify Features

### ✅ Checklist
- [ ] AI Correction header visible
- [ ] 3-column layout appears
- [ ] Categories clickable
- [ ] Detail panel updates on click
- [ ] "← Kembali ke Input" button works
- [ ] Analysis result displayed below
- [ ] Badge indicators (🟢 Primary, 🟡 Unspecified) shown
- [ ] Legend explained in detail panel

---

## Troubleshooting

### Problem: "No categories found"
**Check:**
```bash
# Verify database connection
docker compose exec postgres psql -U postgres -d aiclaimlite

# Test query
SELECT code, name FROM icd10_master 
WHERE LOWER(name) LIKE '%pneumonia%' 
LIMIT 5;
```

### Problem: Endpoint returns 401
**Fix:** Get fresh access token
```bash
# Login first
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@rs.com","password":"password123"}'

# Use returned accessToken in subsequent requests
```

### Problem: Categories load but no details
**Check:** Regex pattern matching
```sql
-- Verify code format
SELECT code FROM icd10_master WHERE code LIKE 'J12%' ORDER BY code;

-- Should return:
-- J12
-- J12.0
-- J12.1
-- J12.2
-- J12.3
-- J12.8
-- J12.9
```

---

## Next Steps

After successful testing:
1. ✅ Test with different diagnosis terms (demam, batuk, diabetes, dll)
2. ✅ Verify AI usage counter decrements
3. ✅ Test limit reached scenario (set low limit)
4. ✅ Check analysis saved to database history
5. ✅ Test responsive layout on different screen sizes

---

## Demo Video Script

1. **Open dashboard** → Show input panel
2. **Type "paru2 basah"** → Show informal Indonesian
3. **Click Generate** → Show loading state
4. **Correction appears** → "paru2 basah" → ✨ "pneumonia"
5. **3 columns load** → Input | Categories | Details
6. **Click J12** → Details expand with 6 subcodes
7. **Scroll down** → Full analysis result visible
8. **Click "← Kembali"** → Return to input mode

**Duration:** 2-3 minutes
**Goal:** Demonstrate smart correction workflow end-to-end

---

## API Testing with Postman

Import collection:
```json
{
  "name": "ICD-10 Smart Correction",
  "requests": [
    {
      "name": "Get Hierarchy",
      "method": "GET",
      "url": "http://localhost:3001/api/ai/icd10-hierarchy?search=pneumonia",
      "headers": {
        "Authorization": "Bearer {{accessToken}}"
      }
    },
    {
      "name": "Get Details",
      "method": "GET",
      "url": "http://localhost:3001/api/ai/icd10-details/J12",
      "headers": {
        "Authorization": "Bearer {{accessToken}}"
      }
    },
    {
      "name": "Search Codes",
      "method": "GET",
      "url": "http://localhost:3001/api/ai/icd10-search?q=viral&limit=20",
      "headers": {
        "Authorization": "Bearer {{accessToken}}"
      }
    }
  ]
}
```

---

**Ready to test!** 🎉

If any issues, refer to `ICD10_SMART_CORRECTION_FEATURE.md` for detailed troubleshooting.
