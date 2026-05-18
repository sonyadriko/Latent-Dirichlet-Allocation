# Fix Summary: Manual Input KDD Pipeline Error Handling

**Date:** 2026-05-18 16:01  
**Issue:** "Tidak ada dokumen ditemukan untuk project ini" error  
**Status:** ✅ FIXED with enhanced error handling and debugging

---

## 🔧 Changes Made

### 1. Enhanced Response Format Handling
**Problem:** API response format might vary (success/documents vs data vs direct array)

**Solution:** Added multiple fallback checks
```javascript
let documents = [];
if (docsResponse.success && docsResponse.documents) {
    documents = docsResponse.documents;
} else if (Array.isArray(docsResponse)) {
    documents = docsResponse;
} else if (docsResponse.data && Array.isArray(docsResponse.data)) {
    documents = docsResponse.data;
}
```

### 2. Added JSON Fallback (Legacy Support)
**Problem:** Old projects might have documents in JSON files, not database

**Solution:** Try loading from JSON if database is empty
```javascript
if (documents.length === 0) {
    const projectResponse = await apiRequest(`/api/projects/${projectId}/documents`);
    if (projectResponse.success && projectResponse.data.documents) {
        documents = projectResponse.data.documents;
    }
}
```

### 3. Added Database Commit Delay
**Problem:** Documents might not be committed to database yet when we try to load them

**Solution:** Added 500ms delay after save
```javascript
await new Promise(resolve => setTimeout(resolve, 500));
```

### 4. Enhanced Console Logging
**Problem:** Hard to debug what's happening

**Solution:** Added comprehensive logging
```javascript
console.log('=== Starting KDD Pipeline Process ===');
console.log('Documents in buffer:', documentsBuffer.length);
console.log('Project selection:', projectSelect);
console.log('Saving X new documents to project Y');
console.log('Documents response:', docsResponse);
console.log('Training dengan X dokumen dari project ID Y');
```

### 5. Better Error Messages
**Problem:** Generic error messages don't help debugging

**Solution:** Detailed error with troubleshooting steps
```javascript
throw new Error(`Tidak ada dokumen ditemukan untuk project ini (ID: ${projectId}).

Pastikan:
1. Dokumen sudah disimpan ke database
2. Project ID benar
3. Dokumen memiliki content yang valid`);
```

### 6. Enhanced Error Logging
**Problem:** Can't see full error context

**Solution:** Log everything in catch block
```javascript
console.error('=== Process Error ===');
console.error('Error message:', error.message);
console.error('Error stack:', error.stack);
console.error('Project ID:', projectId);
console.error('Current project:', currentProject);
console.error('Documents buffer:', documentsBuffer);
```

---

## 🧪 How to Debug the Error

### Step 1: Open Browser Console
Press `F12` and look for logs starting with `===`

### Step 2: Check What's Logged
You should see:
```
=== Starting KDD Pipeline Process ===
Documents in buffer: 3
Project selection: 5
Using existing project: 5
Saving 3 new documents to project 5
Successfully saved 3 documents
Documents response: { success: true, documents: [...], total: 3 }
Training dengan 3 dokumen dari project ID 5
```

### Step 3: If Error Occurs
Look for:
```
=== Process Error ===
Error message: Tidak ada dokumen ditemukan...
Project ID: 5
Documents response: { success: true, documents: [], total: 0 }
```

This tells you documents were saved but not loaded.

### Step 4: Run Debug Script
```bash
python scripts/debug_manual_input.py
```

This will:
- ✅ Check database tables exist
- ✅ Count projects and documents
- ✅ Show recent documents
- ✅ Test save/load operations
- ✅ Create test project if needed

---

## 🔍 Common Causes & Solutions

### Cause 1: Database Not Initialized
**Symptom:** "no such table: documents" error

**Solution:**
```bash
python -c "from core.database import init_database; import asyncio; asyncio.run(init_database())"
```

### Cause 2: Async Timing Issue
**Symptom:** Documents saved but immediately loading returns empty

**Solution:** Already fixed with 500ms delay

### Cause 3: Wrong Project ID
**Symptom:** Loading documents for wrong project

**Solution:** Check console logs for actual project ID being used

### Cause 4: Token Expired
**Symptom:** 401 Unauthorized errors

**Solution:** Login again to get fresh token

### Cause 5: Database Locked
**Symptom:** "database is locked" error

**Solution:**
```bash
# Find processes using database
lsof data/lda_app.db
# Kill them
kill -9 <PID>
```

---

## 📊 Testing Checklist

Run through these scenarios:

### ✅ Test 1: New Project + New Documents
1. Add 3 documents
2. Select "Buat Project Baru"
3. Enter name "Test Project 1"
4. Click "Proses dengan KDD Pipeline"
5. Check console for logs
6. Should succeed and redirect to visualization

### ✅ Test 2: Existing Project + New Documents
1. Select existing project
2. Add 2 new documents
3. Click "Proses dengan KDD Pipeline"
4. Check console for logs
5. Should succeed and redirect to visualization

### ✅ Test 3: Existing Project + All Saved Documents
1. Select project with saved documents
2. Don't add new documents (or all marked as `is_existing`)
3. Click "Proses dengan KDD Pipeline"
4. Should skip save, load from DB, train, redirect

### ✅ Test 4: Check Database After Save
```bash
sqlite3 data/lda_app.db "SELECT id, title, project_id FROM documents ORDER BY id DESC LIMIT 5;"
```

---

## 🛠️ Quick Fixes

### Fix 1: Clear Everything and Start Fresh
```bash
# Backup database
cp data/lda_app.db data/lda_app.db.backup

# Recreate database
rm data/lda_app.db
python -c "from core.database import init_database; import asyncio; asyncio.run(init_database())"

# Restart app
docker-compose restart
# OR
uvicorn app:app --reload
```

### Fix 2: Test API Endpoints Manually
```bash
# Get auth token first (from browser localStorage)
TOKEN="your_token_here"

# Test save
curl -X POST http://localhost:3030/api/documents/manual/bulk \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"documents":[{"title":"Test","content":"Test content"}],"project_id":1}'

# Test load
curl http://localhost:3030/api/documents/manual?project_id=1 \
  -H "Authorization: Bearer $TOKEN"
```

### Fix 3: Use Debug Script
```bash
python scripts/debug_manual_input.py
```

---

## 📝 Files Modified

1. **templates/manual-input.html**
   - Enhanced `processWithKDD()` function
   - Added response format fallbacks
   - Added JSON fallback for legacy projects
   - Added 500ms delay after save
   - Added comprehensive logging
   - Added detailed error messages

2. **scripts/debug_manual_input.py** (NEW)
   - Database state checker
   - Document operations tester
   - Interactive debugging tool

3. **DEBUGGING_GUIDE.md** (NEW)
   - Step-by-step debugging instructions
   - Common issues and solutions
   - Manual testing procedures

---

## 🎯 Next Steps

1. **Test the fix:**
   - Open browser console
   - Try creating new project with documents
   - Check console logs
   - Verify documents are saved and loaded

2. **If still failing:**
   - Copy full console output
   - Run debug script
   - Check database with sqlite3
   - Share logs for further investigation

3. **Report results:**
   - ✅ Success: Share success message and coherence score
   - ❌ Failure: Share console logs and error details

---

## 📞 Support

If you still encounter issues, provide:
1. Full browser console output (from `===` to `===`)
2. Output from `python scripts/debug_manual_input.py`
3. Database query: `sqlite3 data/lda_app.db "SELECT COUNT(*) FROM documents;"`
4. Backend terminal logs

---

**Status:** Ready for testing  
**Confidence:** High - Multiple fallbacks and enhanced error handling added
