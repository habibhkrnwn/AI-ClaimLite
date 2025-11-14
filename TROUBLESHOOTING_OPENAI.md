# 🔧 Quick Troubleshooting Guide

## Error Fixed: `module 'openai' has no attribute 'error'`

### ✅ What was changed:
Updated error handling in `/core_engine/lite_endpoints.py` to be compatible with newer OpenAI library versions.

**Before (Broken):**
```python
except openai.error.AuthenticationError:
    # This doesn't work in OpenAI v1.x
```

**After (Fixed):**
```python
except Exception as e:
    error_msg = str(e)
    if "authentication" in error_msg.lower():
        # Works with any OpenAI version
```

---

## 🚀 How to Test

### Step 1: Restart Core Engine
```bash
cd /home/shunkazama/Documents/Kerja/AI-ClaimLite/core_engine
python main.py
```

**Expected output:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Test Translation Endpoint
```bash
# In another terminal
cd /home/shunkazama/Documents/Kerja/AI-ClaimLite/core_engine
python test_translation.py
```

**Expected output:**
```
📝 Test 1: radang paru paru bakteri
   Expected: bacterial pneumonia
   ✅ Result: bacterial pneumonia
   📊 Confidence: high
   ✓ PASS - Exact match!
```

### Step 3: Manual Test with curl
```bash
curl -X POST http://localhost:8000/api/lite/translate-medical \
  -H "Content-Type: application/json" \
  -d '{"term": "radang paru paru bakteri"}'
```

**Expected response:**
```json
{
  "status": "success",
  "result": {
    "medical_term": "bacterial pneumonia",
    "confidence": "high"
  }
}
```

---

## 🐛 Common Errors & Solutions

### Error 1: "Invalid OpenAI API key"
**Symptom:**
```json
{
  "status": "error",
  "message": "Invalid OpenAI API key"
}
```

**Solution:**
```bash
# Check if API key exists in .env
cat /home/shunkazama/Documents/Kerja/AI-ClaimLite/core_engine/.env | grep OPENAI_API_KEY

# Should show: OPENAI_API_KEY=sk-proj-...
# If empty, add your key to .env file
```

### Error 2: "Cannot connect to database"
**Symptom:**
```
psycopg2.OperationalError: could not connect to server
```

**Solution:**
```bash
# Test database connection
telnet 103.179.56.158 5434

# If fails, check:
# 1. Database server is running
# 2. Firewall allows port 5434
# 3. DATABASE_URL in .env is correct
```

### Error 3: "OpenAI API rate limit exceeded"
**Symptom:**
```json
{
  "status": "error",
  "message": "OpenAI API rate limit exceeded"
}
```

**Solution:**
- Wait a few minutes
- Check your OpenAI account quota
- Consider upgrading OpenAI plan

### Error 4: Port 8000 already in use
**Symptom:**
```
ERROR: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port in .env
APP_PORT=8001
```

---

## 📊 Full Test Flow

```bash
# Terminal 1: Start Core Engine
cd core_engine
python main.py

# Terminal 2: Start Web Backend + Frontend
cd web
npm run dev

# Terminal 3: Test Translation
cd core_engine
python test_translation.py
```

---

## ✅ Success Indicators

### Core Engine Running:
```
✓ INFO: Uvicorn running on http://0.0.0.0:8000
✓ INFO: Application startup complete
```

### Translation Working:
```bash
curl http://localhost:8000/health
# Response: {"status":"healthy","service":"AI-CLAIM Lite"}
```

### Full System Working:
1. Open http://localhost:5173
2. Login as Admin RS
3. Input "radang paru paru" in Diagnosis
4. Click "Generate AI Insight"
5. See ICD-10 Explorer with categories
6. Click a subcode
7. See full analysis

---

## 🔍 Debug Logs

### Check Core Engine Logs:
```bash
# Look for these lines in terminal
2025-11-14 XX:XX:XX - INFO - POST /api/lite/translate-medical
2025-11-14 XX:XX:XX - INFO - OpenAI translation success
```

### Enable Debug Mode:
```bash
# In core_engine/.env
DEBUG=true
```

---

## 📞 Next Steps If Still Failing

1. **Check OpenAI library version:**
   ```bash
   cd core_engine
   pip show openai
   # Should be 1.x.x
   ```

2. **Reinstall if needed:**
   ```bash
   pip install --upgrade openai
   ```

3. **Test OpenAI directly:**
   ```python
   import openai
   import os
   
   openai.api_key = os.getenv("OPENAI_API_KEY")
   
   response = openai.ChatCompletion.create(
       model="gpt-3.5-turbo",
       messages=[{"role": "user", "content": "Test"}]
   )
   print(response.choices[0].message.content)
   ```

---

**Last Updated:** November 14, 2025
**Status:** ✅ Fixed and Ready for Testing
