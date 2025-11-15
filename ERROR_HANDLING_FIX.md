# Fix Error Handling - Analysis Failed Alert

## 🐛 Root Cause yang Ditemukan

Alert **"Error: Analysis failed - Pastikan core_engine API sedang berjalan di port 8000"** muncul karena **error handling yang terlalu general** dan tidak membedakan berbagai jenis error.

### Analisis Detail:

1. **Backend Timeout Terlalu Pendek**
   - Sebelumnya: 3 menit (180 detik)
   - Analisis OpenAI bisa memakan waktu 3-5 menit untuk kasus kompleks
   - Ketika timeout → axios throw error → backend catch → return 500 generic

2. **Frontend Error Handling Terlalu General**
   ```typescript
   // SEBELUM (❌ BURUK):
   if (error.response?.status === 429) {
     alert('Limit habis');
   } else {
     // SEMUA error lain → pesan "port 8000" ❌
     alert('Pastikan core_engine API sedang berjalan di port 8000');
   }
   ```

3. **Tidak Ada Distinction Error Type**
   - Timeout ≠ Connection Refused ≠ Internal Error
   - Semua ditampilkan dengan pesan sama → membingungkan user

## ✅ Solusi yang Diimplementasikan

### 1. **Increase Backend Timeout** (3 → 5 menit)

**File**: `web/server/routes/aiRoutes.ts`

```typescript
// SEBELUM:
const response = await axios.post(`${CORE_ENGINE_URL}/api/lite/analyze/single`, payload, {
  timeout: 180000, // 3 minutes ❌
});

// SESUDAH:
const response = await axios.post(`${CORE_ENGINE_URL}/api/lite/analyze/single`, payload, {
  timeout: 300000, // 5 minutes ✅
});
```

**Alasan**: Sinkronisasi dengan frontend timeout (juga 5 menit) dan beri waktu cukup untuk OpenAI processing.

---

### 2. **Improve Backend Error Handling**

**File**: `web/server/routes/aiRoutes.ts`

```typescript
// SESUDAH (✅ BAIK):
} catch (error: any) {
  let errorMessage = 'Failed to analyze claim';
  let errorType = 'internal_error';
  
  // Distinguish error types
  if (error.code === 'ECONNREFUSED') {
    errorMessage = 'Core engine tidak dapat dihubungi. Pastikan service berjalan di port 8000.';
    errorType = 'connection_refused';
  } else if (error.code === 'ETIMEDOUT' || error.message?.includes('timeout')) {
    errorMessage = 'Analisis timeout (>5 menit). Coba lagi atau hubungi admin.';
    errorType = 'timeout';
  } else if (error.response?.data?.message) {
    errorMessage = error.response.data.message;
    errorType = 'core_engine_error';
  }

  res.status(500).json({
    success: false,
    message: errorMessage,
    error_type: errorType, // 🔑 Key field untuk frontend
    detail: error.message,
  });
}
```

**Benefit**: Backend sekarang memberikan `error_type` yang spesifik.

---

### 3. **Improve Frontend Error Handling**

**File**: `web/src/components/AdminRSDashboard.tsx`

```typescript
// SESUDAH (✅ BAIK):
} catch (error: any) {
  const errorMessage = error.response?.data?.message || error.message || 'Gagal melakukan analisis';
  const errorType = error.response?.data?.error_type; // 🔑 Baca error_type dari backend
  
  if (error.response?.status === 429) {
    alert(`Limit penggunaan AI harian Anda sudah habis!\\n\\nSilakan coba lagi besok atau hubungi admin.`);
  } else if (errorType === 'timeout') {
    alert(`Timeout: Analisis memakan waktu terlalu lama (>5 menit).\\n\\nCoba lagi atau hubungi admin.`);
  } else if (errorType === 'connection_refused') {
    alert(`Error: ${errorMessage}\\n\\nCore engine tidak dapat dihubungi.`);
  } else {
    alert(`Error: ${errorMessage}\\n\\n${error.response?.data?.detail || 'Silakan coba lagi.'}`);
  }
}
```

**Benefit**: 
- User melihat pesan error yang **spesifik dan actionable**
- Tidak lagi "semua error = port 8000"
- Lebih mudah troubleshooting

---

## 📊 Comparison Sebelum vs Sesudah

| Skenario | Pesan Sebelum ❌ | Pesan Sesudah ✅ |
|----------|-----------------|-----------------|
| **Timeout (>5 menit)** | "Pastikan core_engine API sedang berjalan di port 8000" | "Timeout: Analisis memakan waktu terlalu lama (>5 menit). Coba lagi atau hubungi admin." |
| **Connection Refused** | "Pastikan core_engine API sedang berjalan di port 8000" | "Core engine tidak dapat dihubungi. Pastikan service berjalan di port 8000." |
| **Internal Error (DB fail, dll)** | "Pastikan core_engine API sedang berjalan di port 8000" | "Error: [specific error message]. Silakan coba lagi atau hubungi admin." |
| **Limit Exceeded** | "Limit penggunaan AI harian Anda sudah habis!" | "Limit penggunaan AI harian Anda sudah habis!" *(Tidak berubah)* |

---

## 🧪 Testing Scenarios

### Test 1: Timeout Simulation
**Cara**: Tambah `await new Promise(r => setTimeout(r, 360000))` di endpoint  
**Expected**: Alert "Timeout: Analisis memakan waktu terlalu lama"

### Test 2: Connection Refused
**Cara**: Stop container `aiclaimlite-core-engine`  
**Expected**: Alert "Core engine tidak dapat dihubungi. Pastikan service berjalan di port 8000."

### Test 3: Normal Error (DB connection fail)
**Cara**: Ubah DATABASE_URL di core_engine  
**Expected**: Alert dengan error message spesifik dari core_engine

### Test 4: Success Case
**Cara**: Analisis normal dengan input valid  
**Expected**: Hasil analisis muncul tanpa error

---

## 🚀 Deployment

Perubahan sudah di-apply dengan:
```bash
docker compose up -d
```

Karena menggunakan **volume mount** (`./web:/app`), perubahan code langsung terpakai tanpa rebuild.

---

## 📝 Key Takeaways

1. **Error handling harus spesifik** - jangan catch-all dengan pesan generic
2. **Timeout harus konsisten** - frontend dan backend sync (5 menit)
3. **Komunikasi error yang baik** - backend kirim `error_type`, frontend baca dan tampilkan pesan sesuai
4. **User experience** - pesan error harus actionable dan tidak membingungkan

---

## 🔮 Future Improvements (Optional)

1. **Retry mechanism** untuk timeout errors
2. **Loading progress bar** untuk analisis >1 menit
3. **WebSocket** untuk real-time progress updates
4. **Circuit breaker** pattern untuk repeated failures
5. **Sentry/logging** integration untuk monitoring errors di production

---

**Status**: ✅ **FIXED**  
**Date**: November 14, 2025  
**Impact**: Improved error UX, easier troubleshooting, better timeout handling
