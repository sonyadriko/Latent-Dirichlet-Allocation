# Flow Diagram: Manual Input KDD Pipeline

## Old Flow (Before Fix)

```
┌─────────────────────────────────────────────────────────────┐
│                    Manual Input Page                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ User clicks "Proses dengan KDD Pipeline"
                            ▼
                    ┌───────────────┐
                    │ Save Documents│
                    └───────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Redirect to   │
                    │  /admin page  │
                    └───────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  USER MUST MANUALLY:                  │
        │  1. Select project                    │
        │  2. Click "Load Project"              │
        │  3. Click "Train LDA Model"           │
        │  4. Navigate to visualization         │
        └───────────────────────────────────────┘
```

## New Flow (After Fix)

```
┌─────────────────────────────────────────────────────────────┐
│                    Manual Input Page                         │
│  - User adds documents                                       │
│  - User selects/creates project                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ User clicks "Proses dengan KDD Pipeline"
                            ▼
                ┌───────────────────────┐
                │ Validate Project      │
                │ Selection             │
                └───────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
        Project = "new"          Project = existing ID
                │                       │
                ▼                       ▼
    ┌─────────────────────┐   ┌─────────────────────┐
    │ POST /api/projects/ │   │ Load project info   │
    │ Create new project  │   │ (if not loaded)     │
    └─────────────────────┘   └─────────────────────┘
                │                       │
                └───────────┬───────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │ POST /api/documents/manual/   │
            │        bulk                   │
            │ Save new documents to DB      │
            └───────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │ GET /api/documents/manual?    │
            │     project_id={id}           │
            │ Load ALL documents from DB    │
            └───────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │ POST /api/search/train        │
            │ Train LDA Model               │
            │ - num_topics from project     │
            │ - documents from DB           │
            └───────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │ Show Success Message          │
            │ - Document count              │
            │ - Topic count                 │
            │ - Coherence score             │
            └───────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │ Redirect to /visualization    │
            │ (after 3 seconds)             │
            └───────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  USER SEES:                           │
        │  - Interactive topic visualization    │
        │  - Document-topic distribution        │
        │  - Topic keywords                     │
        │  - Ready to explore results           │
        └───────────────────────────────────────┘
```

## State Transitions

```
┌──────────────┐
│   INITIAL    │  User adds documents to buffer
│   STATE      │
└──────┬───────┘
       │
       │ Click "Proses dengan KDD Pipeline"
       ▼
┌──────────────┐
│  VALIDATING  │  Check project selection
│   PROJECT    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   CREATING/  │  Create new or load existing project
│   LOADING    │
│   PROJECT    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    SAVING    │  Save new documents to database
│  DOCUMENTS   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   LOADING    │  Load all documents from database
│  DOCUMENTS   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   TRAINING   │  Train LDA model
│   LDA MODEL  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   SUCCESS    │  Show results and redirect
│   COMPLETE   │
└──────────────┘
```

## Error Handling Flow

```
                    ┌─────────────────┐
                    │  Any Step       │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Error Occurs?  │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                   YES               NO
                    │                 │
                    ▼                 ▼
        ┌───────────────────┐   ┌──────────┐
        │ Catch Exception   │   │ Continue │
        │ Show Error Alert  │   │ to Next  │
        │ Re-enable Button  │   │ Step     │
        │ Keep User on Page │   └──────────┘
        └───────────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │ User can:                 │
        │ - Fix the issue           │
        │ - Try again               │
        │ - Modify documents        │
        └───────────────────────────┘
```

## Button State Transitions

```
┌─────────────────────────────────────────────────────────────┐
│                    Button States                             │
└─────────────────────────────────────────────────────────────┘

IDLE STATE:
┌──────────────────────────────────┐
│ 🧠 Proses dengan KDD Pipeline    │  ← Enabled when documents exist
└──────────────────────────────────┘

CREATING PROJECT:
┌──────────────────────────────────┐
│ 🔄 Membuat Project...            │  ← Disabled, spinner visible
└──────────────────────────────────┘

SAVING DOCUMENTS:
┌──────────────────────────────────┐
│ 🔄 Menyimpan Dokumen...          │  ← Disabled, spinner visible
└──────────────────────────────────┘

LOADING DOCUMENTS:
┌──────────────────────────────────┐
│ 🔄 Memuat Dokumen untuk          │  ← Disabled, spinner visible
│    Training...                   │
└──────────────────────────────────┘

TRAINING MODEL:
┌──────────────────────────────────┐
│ 🔄 Training LDA Model...         │  ← Disabled, spinner visible
└──────────────────────────────────┘

SUCCESS STATE:
┌──────────────────────────────────┐
│ 🧠 Proses dengan KDD Pipeline    │  ← Re-enabled, original text
└──────────────────────────────────┘
(Success alert shown, redirect in progress)

ERROR STATE:
┌──────────────────────────────────┐
│ 🧠 Proses dengan KDD Pipeline    │  ← Re-enabled, original text
└──────────────────────────────────┘
(Error alert shown, user can retry)
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Browser)                        │
│                                                              │
│  documentsBuffer = [                                         │
│    { id, title, content, is_existing: false },  ← New docs  │
│    { id, title, content, is_existing: true }   ← Existing   │
│  ]                                                           │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ Filter new documents
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              POST /api/documents/manual/bulk                 │
│                                                              │
│  Request Body:                                               │
│  {                                                           │
│    documents: [                                              │
│      { title: "...", content: "..." }                       │
│    ],                                                        │
│    project_id: 123                                           │
│  }                                                           │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database (SQLite)                         │
│                                                              │
│  INSERT INTO documents (title, content, project_id, ...)    │
│  VALUES (?, ?, ?, ...)                                       │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ Load all documents
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           GET /api/documents/manual?project_id=123           │
│                                                              │
│  Response:                                                   │
│  {                                                           │
│    documents: [                                              │
│      { id, title, content, url, ... }                       │
│    ]                                                         │
│  }                                                           │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ Send to training
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 POST /api/search/train                       │
│                                                              │
│  Request Body:                                               │
│  {                                                           │
│    num_topics: 5,                                            │
│    documents: [                                              │
│      { id, title, content, url }                            │
│    ],                                                        │
│    project_name: null                                        │
│  }                                                           │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   LDA Service (Gensim)                       │
│                                                              │
│  1. Preprocess documents (tokenize, stem, remove stopwords) │
│  2. Create dictionary and corpus                            │
│  3. Train LDA model                                          │
│  4. Calculate coherence score                                │
│  5. Save model to disk                                       │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ Return results
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Response to Frontend                      │
│                                                              │
│  {                                                           │
│    success: true,                                            │
│    data: {                                                   │
│      num_documents: 10,                                      │
│      num_topics: 5,                                          │
│      coherence_score: 0.4534,                                │
│      topics: [...]                                           │
│    }                                                         │
│  }                                                           │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ Redirect
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Visualization Page (/visualization)             │
│                                                              │
│  - Load trained model                                        │
│  - Display pyLDAvis interactive visualization                │
│  - Show topic keywords                                       │
│  - Show document-topic distribution                          │
└─────────────────────────────────────────────────────────────┘
```
