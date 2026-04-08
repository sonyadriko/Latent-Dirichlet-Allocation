# Project Management Page Design

## Overview
Create a dedicated page (`/projects`) for managing LDA projects with list and delete functionality.

## Architecture

### New Files
- `templates/projects.html` - Project management page template

### Modified Files
- `main.py` - Add route `/projects`

### Flow
```
User akses /projects → Cek authentication → Tampilkan halaman → Load data project → Tampilkan tabel → Hapus project (jika diklik)
```

## UI/UX Design

### Layout
```
┌─────────────────────────────────────────────────────────┐
│  Header: Manajemen Project                              │
│  [Logout]                                               │
├─────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────┐  │
│  │ Nama Project       | Topics | Docs | Actions       │  │
│  ├───────────────────────────────────────────────────┤  │
│  │ Project A          |   5    |  15  | [🗑️ Hapus]   │  │
│  │ Project B          |   3    |  20  | [🗑️ Hapus]   │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Features
- Responsive table with consistent styling (admin.html)
- Delete button with confirmation popup
- Loading state when fetching data
- Error handling for load/delete failures
- Auto refresh after delete

## Data Flow & API

### Existing APIs Used
- `GET /api/projects/list` - Fetch all projects
- `DELETE /api/projects/{project_id}/delete` - Delete project

### Flow
1. Page loads → `loadProjects()`
2. GET `/api/projects/list` → receive project data
3. Render table with data
4. User clicks "Hapus" → confirm → DELETE `/api/projects/{id}/delete`
5. Success → refresh table

### Authentication
- Use same JWT as admin page
- Check token in localStorage

## Error Handling & Validation

### Delete Confirmation
```
"Anda yakin ingin menghapus "{nama_project}"?
Aksi ini akan menghapus:
- Database records
- Model files
- Semua data terkait

Aksi tidak dapat dibatalkan."
```

### Error Cases
- Failed to load projects → Show error with retry button
- Failed to delete → Show error, stay on page
- No projects → Show "Belum ada project" message
- Unauthorized/Token expired → Redirect to login

### Styling
- Use existing CSS from `/static/css/style.css`
- Consistent with admin.html appearance
