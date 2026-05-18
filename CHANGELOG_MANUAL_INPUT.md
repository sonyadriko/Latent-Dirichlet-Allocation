# Changelog: Manual Input KDD Pipeline Integration

**Date:** 2026-05-18  
**File Modified:** `templates/manual-input.html`  
**Function:** `processWithKDD()`

## Problem Statement

Sebelumnya, tombol "Proses dengan KDD Pipeline" di halaman manual input **TIDAK** melakukan training otomatis. Flow yang lama:

1. ✅ Simpan dokumen ke database
2. ❌ Redirect ke `/admin` (user harus manual training)
3. ❌ User harus:
   - Pilih project yang sama
   - Klik "Load Project"
   - Klik "Train LDA Model"

## Solution Implemented

Sekarang tombol "Proses dengan KDD Pipeline" melakukan **full automated pipeline**:

### New Flow

```
1. Validasi project selection
   ├─ Jika "new" → Buat project baru via POST /api/projects/
   └─ Jika existing → Load project info

2. Simpan dokumen baru
   └─ POST /api/documents/manual/bulk (hanya dokumen yang belum tersimpan)

3. Load semua dokumen dari database
   └─ GET /api/documents/manual?project_id={id}

4. Training LDA Model
   └─ POST /api/search/train dengan semua dokumen

5. Redirect ke /visualization
   └─ User langsung melihat hasil analisis
```

### Key Changes

#### Before:
```javascript
async function processWithKDD() {
    // Hanya save dan redirect
    await saveAllDocuments();
    window.location.href = '/admin';
}
```

#### After:
```javascript
async function processWithKDD() {
    // 1. Validate & create/load project
    // 2. Save new documents
    // 3. Load all documents from DB
    // 4. Train LDA model automatically
    // 5. Redirect to visualization
}
```

## Technical Details

### API Endpoints Used

1. **`POST /api/projects/`** (routers/project.py)
   - Create new project if user selects "new"
   - Returns project ID for document association

2. **`POST /api/documents/manual/bulk`** (routers/documents.py)
   - Bulk save documents to database
   - Associates documents with project_id

3. **`GET /api/documents/manual?project_id={id}`** (routers/documents.py)
   - Load all documents for a project from database
   - Returns documents with full content for training

4. **`POST /api/search/train`** (routers/search.py)
   - Train LDA model on provided documents
   - Parameters:
     - `num_topics`: Number of topics (from project settings)
     - `documents`: Array of document objects with id, title, content
     - `project_name`: null (don't create new project)

### Progress Indicators

The button shows real-time progress:
- 🔄 "Membuat Project..." (if creating new project)
- 🔄 "Menyimpan Dokumen..." (saving to database)
- 🔄 "Memuat Dokumen untuk Training..." (loading from DB)
- 🔄 "Training LDA Model..." (LDA training)
- ✅ Success message with stats
- 🔄 "Mengalihkan ke halaman visualisasi..." (redirecting)

### Error Handling

Comprehensive error handling for:
- ❌ No documents in buffer
- ❌ No project selected
- ❌ Empty project name (for new projects)
- ❌ Document save failures
- ❌ No documents found in database
- ❌ Training failures

### User Experience Improvements

1. **Clear validation messages** - User knows exactly what's missing
2. **Step-by-step progress** - User sees what's happening at each stage
3. **Automatic redirect** - No manual navigation needed
4. **Success metrics** - Shows document count, topics, coherence score
5. **Buffer cleanup** - Clears form after successful processing

## Testing Checklist

- [ ] Test with new project creation
- [ ] Test with existing project selection
- [ ] Test with no project selected (should show error)
- [ ] Test with only new documents
- [ ] Test with mix of new and existing documents
- [ ] Test with all documents already saved
- [ ] Test error handling (network failures, invalid data)
- [ ] Verify redirect to visualization page
- [ ] Verify LDA model is actually trained
- [ ] Verify visualization page shows correct results

## Benefits

1. **Seamless UX** - One-click from input to visualization
2. **No manual steps** - Fully automated pipeline
3. **Clear feedback** - User knows what's happening at each step
4. **Error recovery** - Proper error messages guide user
5. **Consistent flow** - Matches the URL crawling workflow

## Related Files

- `templates/manual-input.html` - Modified file
- `routers/documents.py` - Document management endpoints
- `routers/search.py` - LDA training endpoint
- `routers/project.py` - Project management endpoints
- `services/lda_service.py` - LDA training logic

## Notes

- Training uses documents from database, not from buffer
- This ensures consistency with saved data
- Project must be selected before processing
- Coherence score is displayed in success message
- Redirect happens after 3 seconds (2s + 1s)
