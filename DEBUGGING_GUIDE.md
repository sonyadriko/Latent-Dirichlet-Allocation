# Debugging Guide: "Tidak ada dokumen ditemukan" Error

**Error Message:**
```
Process error: Error: Tidak ada dokumen ditemukan untuk project ini. Pastikan dokumen sudah tersimpan.
```

---

## 🔍 Langkah-langkah Debugging

### 1. Buka Browser Console
- Tekan `F12` atau `Ctrl+Shift+I` (Windows/Linux) atau `Cmd+Option+I` (Mac)
- Pilih tab "Console"
- Lihat log messages yang dimulai dengan `===`

### 2. Cek Log Messages

Anda harus melihat log seperti ini:
```
=== Starting KDD Pipeline Process ===
Documents in buffer: 5
Project selection: 123
Using existing project: 123
Saving 5 new documents to project 123
Successfully saved 5 documents
Documents response: { success: true, documents: [...], total: 5 }
Training dengan 5 dokumen dari project ID 123
```

### 3. Identifikasi Masalah

#### ❌ Problem 1: Documents response kosong
```
Documents response: { success: true, documents: [], total: 0 }
```

**Penyebab:**
- Dokumen tidak tersimpan ke database
- Project ID salah
- Database connection error

**Solusi:**
1. Cek apakah dokumen benar-benar disimpan:
   ```javascript
   // Di console browser, jalankan:
   fetch('/api/documents/manual?project_id=123', {
       headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
   }).then(r => r.json()).then(console.log)
   ```

2. Cek database langsung:
   ```bash
   # Di terminal
   sqlite3 data/lda_app.db "SELECT COUNT(*) FROM documents WHERE project_id = 123;"
   ```

#### ❌ Problem 2: Response format salah
```
Documents response: { data: [...] }  // Bukan { documents: [...] }
```

**Solusi:** Sudah diperbaiki dengan fallback handling di kode baru

#### ❌ Problem 3: Timing issue (dokumen belum commit)
```
Successfully saved 5 documents
Documents response: { success: true, documents: [], total: 0 }
```

**Penyebab:** Database belum commit saat query

**Solusi:** Sudah ditambahkan delay 500ms setelah save

---

## 🧪 Manual Testing Steps

### Test 1: Cek Endpoint Save
```bash
# Test save documents
curl -X POST http://localhost:3030/api/documents/manual/bulk \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "documents": [
      {"title": "Test Doc 1", "content": "Test content 1"},
      {"title": "Test Doc 2", "content": "Test content 2"}
    ],
    "project_id": 1
  }'
```

**Expected Response:**
```json
{
  "created_count": 2,
  "documents": [...],
  "message": "Successfully created 2 documents"
}
```

### Test 2: Cek Endpoint Load
```bash
# Test load documents
curl http://localhost:3030/api/documents/manual?project_id=1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response:**
```json
{
  "success": true,
  "documents": [
    {
      "id": 1,
      "title": "Test Doc 1",
      "content": "Test content 1",
      ...
    }
  ],
  "total": 2
}
```

### Test 3: Cek Database Langsung
```bash
# Connect to database
sqlite3 data/lda_app.db

# Check documents table
SELECT id, title, project_id, LENGTH(content) as content_length 
FROM documents 
WHERE project_id = 1;

# Check if table exists
.tables

# Check table schema
.schema documents
```

---

## 🔧 Quick Fixes

### Fix 1: Database Tidak Ada
```bash
# Recreate database
python -c "from core.database import init_database; import asyncio; asyncio.run(init_database())"
```

### Fix 2: Clear Cache dan Reload
```javascript
// Di browser console
localStorage.clear();
sessionStorage.clear();
location.reload();
```

### Fix 3: Restart Application
```bash
# Docker
docker-compose restart

# Local
# Ctrl+C to stop
uvicorn app:app --host 0.0.0.0 --port 3030 --reload
```

---

## 📊 Expected Console Output (Success Case)

```
=== Starting KDD Pipeline Process ===
Documents in buffer: 3
Project selection: new
Creating new project: My Test Project
Project created successfully: 5
Saving 3 new documents to project 5
Successfully saved 3 documents
Documents response: {
  success: true,
  documents: [
    { id: 10, title: "Doc 1", content: "...", ... },
    { id: 11, title: "Doc 2", content: "...", ... },
    { id: 12, title: "Doc 3", content: "...", ... }
  ],
  total: 3
}
Training dengan 3 dokumen dari project ID 5
=== KDD Pipeline Process Ended ===
```

---

## 🐛 Common Issues

### Issue 1: Token Expired
**Symptom:** 401 Unauthorized errors
**Solution:** 
```javascript
// Check token in console
console.log('Token:', localStorage.getItem('token'));
// If null or expired, login again
```

### Issue 2: CORS Error
**Symptom:** Network errors in console
**Solution:** Check if backend is running on correct port (3030)

### Issue 3: Database Locked
**Symptom:** "database is locked" error
**Solution:**
```bash
# Kill any processes using the database
lsof data/lda_app.db
kill -9 <PID>
```

### Issue 4: Async/Await Timing
**Symptom:** Documents saved but not loaded
**Solution:** Already fixed with 500ms delay after save

---

## 📝 What to Check Next

1. **Open browser console** - Look for the detailed logs
2. **Copy all console output** - Share it for further debugging
3. **Check network tab** - See actual API responses
4. **Check database** - Verify documents are actually saved
5. **Check backend logs** - Look for errors in terminal

---

## 🆘 If Still Not Working

Please provide:
1. ✅ Full console output (from `===` to `===`)
2. ✅ Network tab screenshot (API calls)
3. ✅ Database query result: `SELECT COUNT(*) FROM documents;`
4. ✅ Backend terminal logs
5. ✅ Steps you took before the error

---

## 💡 Temporary Workaround

If you need to test training immediately, use the **Admin page** instead:
1. Go to `/admin`
2. Select "Manual Mode"
3. Choose your project
4. Click "Load Project"
5. Click "Train LDA Model"

This bypasses the automated flow and lets you test training manually.
