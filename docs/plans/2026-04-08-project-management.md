# Project Management Page Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a dedicated page (`/projects`) for managing LDA projects with list and delete functionality.

**Architecture:** New FastAPI route serving a standalone HTML template that consumes existing project APIs (GET /api/projects/list, DELETE /api/projects/{id}/delete).

**Tech Stack:** FastAPI, Jinja2 templates, JavaScript (vanilla), existing JWT authentication

---

## Task 1: Create the Projects HTML Template

**Files:**
- Create: `templates/projects.html`

**Step 1: Create the HTML template**

```html
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manajemen Project - LDA News Trend</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="page-header">
            <div class="header-content">
                <h1>📁 Manajemen Project</h1>
                <div class="header-actions">
                    <a href="/admin" class="btn btn-secondary">← Kembali ke Admin</a>
                    <button class="btn-refresh" onclick="loadProjects()">🔄 Refresh</button>
                    <button class="btn btn-danger" onclick="logout()">Logout</button>
                </div>
            </div>
        </header>

        <!-- Projects Table -->
        <div class="projects-section">
            <div id="projects-table" class="projects-table">
                <div class="projects-loading">Memuat projects...</div>
            </div>
        </div>
    </div>

    <script>
        // Get token from localStorage
        function getToken() {
            return localStorage.getItem('token');
        }

        // API request helper
        async function apiRequest(url, options = {}) {
            const token = getToken();
            const headers = {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` })
            };

            const response = await fetch(url, {
                ...options,
                headers: { ...headers, ...options.headers }
            });

            if (response.status === 401) {
                localStorage.removeItem('token');
                window.location.href = '/login';
                throw new Error('Unauthorized');
            }

            return await response.json();
        }

        // Escape HTML to prevent XSS
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Load all projects
        async function loadProjects() {
            const container = document.getElementById('projects-table');

            try {
                container.innerHTML = '<div class="projects-loading">Memuat projects...</div>';
                const response = await apiRequest('/api/projects/list');

                if (response.success) {
                    renderProjectsTable(response.data);
                } else {
                    container.innerHTML = `
                        <div class="projects-error">
                            <p>Gagal memuat projects: ${response.message}</p>
                            <button class="btn btn-secondary" onclick="loadProjects()">Coba Lagi</button>
                        </div>
                    `;
                }
            } catch (error) {
                container.innerHTML = `
                    <div class="projects-error">
                        <p>Error: ${error.message}</p>
                        <button class="btn btn-secondary" onclick="loadProjects()">Coba Lagi</button>
                    </div>
                `;
            }
        }

        // Render projects table
        function renderProjectsTable(projects) {
            const container = document.getElementById('projects-table');

            if (!projects || projects.length === 0) {
                container.innerHTML = '<p class="projects-empty">Belum ada project. Buat project untuk memulai.</p>';
                return;
            }

            const headerHtml = `
                <div class="project-header">
                    <div>Nama Project</div>
                    <div class="project-stat-label">Topics</div>
                    <div class="project-stat-label">Documents</div>
                    <div class="project-stat-label">Coherence</div>
                    <div class="project-stat-label">Status</div>
                    <div>Aksi</div>
                </div>
            `;

            const rowsHtml = projects.map(project => `
                <div class="project-row" data-id="${project.id}">
                    <div>
                        <div class="project-name">${escapeHtml(project.name)}</div>
                        ${project.description ? `<div class="project-description">${escapeHtml(project.description)}</div>` : ''}
                    </div>
                    <div class="project-stat">
                        <div class="project-stat-value">${project.num_topics || 0}</div>
                        <div class="project-stat-label">Topics</div>
                    </div>
                    <div class="project-stat">
                        <div class="project-stat-value">${project.document_count || 0}</div>
                        <div class="project-stat-label">Docs</div>
                    </div>
                    <div class="project-stat">
                        <div class="project-stat-value">${(project.coherence_score || 0).toFixed(3)}</div>
                        <div class="project-stat-label">Cv Score</div>
                    </div>
                    <div>
                        <span class="project-status ${project.status || 'active'}">
                            ${project.status || 'active'}
                        </span>
                    </div>
                    <div>
                        <button class="btn-delete" onclick="deleteProject(${project.id}, '${escapeHtml(project.name)}')">
                            🗑️ Hapus
                        </button>
                    </div>
                </div>
            `).join('');

            container.innerHTML = headerHtml + rowsHtml;
        }

        // Delete project with confirmation
        async function deleteProject(projectId, projectName) {
            const confirmMsg = `Anda yakin ingin menghapus "${projectName}"?\n\nAksi ini akan menghapus:\n- Database records\n- Model files\n- Semua data terkait\n\nAksi tidak dapat dibatalkan.`;

            if (!confirm(confirmMsg)) {
                return;
            }

            const container = document.getElementById('projects-table');
            const row = container.querySelector(`.project-row[data-id="${projectId}"]`);
            const button = row?.querySelector('.btn-delete');

            if (button) {
                button.disabled = true;
                button.textContent = '⏳ Menghapus...';
            }

            try {
                const response = await apiRequest(`/api/projects/${projectId}/delete`, {
                    method: 'DELETE'
                });

                if (response.success) {
                    // Animate row removal
                    if (row) {
                        row.style.opacity = '0';
                        row.style.transform = 'translateX(-20px)';
                        setTimeout(() => {
                            row.remove();
                            // Check if table is empty
                            const remainingRows = container.querySelectorAll('.project-row');
                            if (remainingRows.length === 0) {
                                renderProjectsTable([]);
                            }
                        }, 300);
                    }
                } else {
                    if (button) {
                        button.disabled = false;
                        button.textContent = '🗑️ Hapus';
                    }
                    alert(`Gagal menghapus project: ${response.message}`);
                }
            } catch (error) {
                if (button) {
                    button.disabled = false;
                    button.textContent = '🗑️ Hapus';
                }
                alert(`Error: ${error.message}`);
            }
        }

        // Logout
        function logout() {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }

        // Check authentication on page load
        function checkAuth() {
            const token = getToken();
            if (!token) {
                window.location.href = '/login';
                return false;
            }
            return true;
        }

        // Initialize page
        document.addEventListener('DOMContentLoaded', () => {
            if (checkAuth()) {
                loadProjects();
            }
        });
    </script>

    <style>
        .page-header {
            background: var(--bg-card);
            border-radius: var(--radius-lg);
            padding: var(--space-6);
            margin-bottom: var(--space-6);
            box-shadow: var(--shadow-sm);
        }

        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: var(--space-4);
        }

        .header-content h1 {
            margin: 0;
            color: var(--primary);
            font-size: 1.75rem;
        }

        .header-actions {
            display: flex;
            gap: var(--space-3);
        }

        .projects-section {
            background: var(--bg-card);
            border-radius: var(--radius-lg);
            padding: var(--space-6);
            box-shadow: var(--shadow-sm);
        }

        .projects-table {
            min-height: 200px;
        }

        .projects-loading,
        .projects-empty,
        .projects-error {
            text-align: center;
            padding: var(--space-8);
            color: var(--text-muted);
        }

        .projects-error {
            color: var(--danger);
        }

        .project-header {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1fr 1fr 100px;
            gap: var(--space-4);
            padding: var(--space-4);
            background: var(--bg-tertiary);
            border-radius: var(--radius-md);
            font-weight: 600;
            color: var(--text-secondary);
        }

        .project-row {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1fr 1fr 100px;
            gap: var(--space-4);
            padding: var(--space-4);
            border-bottom: 1px solid var(--border-color);
            align-items: center;
            transition: all var(--transition-normal);
        }

        .project-row:last-child {
            border-bottom: none;
        }

        .project-row:hover {
            background: var(--bg-secondary);
        }

        .project-name {
            font-weight: 600;
            color: var(--text-primary);
        }

        .project-description {
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-top: var(--space-1);
        }

        .project-stat {
            text-align: center;
        }

        .project-stat-value {
            font-weight: 600;
            color: var(--text-primary);
        }

        .project-stat-label {
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        .project-status {
            display: inline-block;
            padding: var(--space-1) var(--space-3);
            border-radius: var(--radius-full);
            font-size: 0.75rem;
            font-weight: 600;
        }

        .project-status.active {
            background: rgba(34, 197, 94, 0.1);
            color: var(--success);
        }

        .project-status.deleted {
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
        }

        .btn-delete {
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
            border: 1px solid var(--danger);
            padding: var(--space-2) var(--space-4);
            border-radius: var(--radius-md);
            cursor: pointer;
            font-weight: 500;
            transition: all var(--transition-normal);
        }

        .btn-delete:hover:not(:disabled) {
            background: var(--danger);
            color: white;
        }

        .btn-delete:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .btn-refresh {
            background: var(--primary);
            color: white;
            border: none;
            padding: var(--space-3) var(--space-4);
            border-radius: var(--radius-md);
            cursor: pointer;
            font-weight: 500;
            transition: all var(--transition-normal);
        }

        .btn-refresh:hover {
            background: var(--primary-dark);
        }

        .btn-secondary {
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            padding: var(--space-3) var(--space-4);
            border-radius: var(--radius-md);
            cursor: pointer;
            font-weight: 500;
            text-decoration: none;
            transition: all var(--transition-normal);
        }

        .btn-secondary:hover {
            background: var(--bg-tertiary);
        }

        .btn-danger {
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
            border: 1px solid var(--danger);
            padding: var(--space-3) var(--space-4);
            border-radius: var(--radius-md);
            cursor: pointer;
            font-weight: 500;
            transition: all var(--transition-normal);
        }

        .btn-danger:hover {
            background: var(--danger);
            color: white;
        }

        @media (max-width: 768px) {
            .project-header,
            .project-row {
                grid-template-columns: 1fr;
                gap: var(--space-2);
            }

            .project-header {
                display: none;
            }

            .project-row {
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                padding: var(--space-4);
                margin-bottom: var(--space-3);
            }
        }
    </style>
</body>
</html>
```

**Step 2: Verify file was created**

Check: `ls -la templates/projects.html`
Expected: File exists

---

## Task 2: Add the Projects Route to FastAPI

**Files:**
- Modify: `main.py`

**Step 1: Read main.py to understand existing route structure**

Run: `head -100 main.py`
Look for: Existing `@app.get()` routes and template rendering patterns

**Step 2: Add the /projects route**

Find the section with other page routes (like `/admin`, `/login`, etc.) and add:

```python
@app.get("/projects")
async def projects_page(request: Request):
    """Project management page - requires authentication"""
    token = request.cookies.get('token')

    if not token:
        return RedirectResponse(url='/login', status_code=303)

    # You could add additional validation here if needed
    # For now, the template will handle auth via localStorage

    return templates.TemplateResponse("projects.html", {
        "request": request
    })
```

**Step 3: Verify the route was added correctly**

Run: `grep -n "projects" main.py`
Expected: Should show the new route line

**Step 4: Commit**

```bash
git add templates/projects.html main.py
git commit -m "feat: add project management page with list and delete functionality"
```

---

## Task 3: Add Link to Projects Page from Admin

**Files:**
- Modify: `templates/admin.html`

**Step 1: Find the header section in admin.html**

Run: `grep -n "page-header\|header-content\|Admin Dashboard" templates/admin.html`
Note: The line number for the header

**Step 2: Add a button/link to the projects page**

In the header actions section, add:

```html
<a href="/projects" class="btn btn-secondary">📁 Manajemen Project</a>
```

Place it near other header action buttons.

**Step 3: Commit**

```bash
git add templates/admin.html
git commit -m "feat: add link to project management page from admin"
```

---

## Verification & Testing

**Step 1: Start the application**

```bash
docker-compose up -d
# or locally: python main.py
```

**Step 2: Test the flow**

1. Login to the application
2. Navigate to `http://localhost:3030/projects`
3. Verify:
   - Page loads without errors
   - Projects table displays (if projects exist)
   - "Belum ada project" message shows (if no projects)
   - "Hapus" button works for each project
   - Delete confirmation dialog appears
   - After confirming, project is removed from table
   - "Refresh" button reloads the table
   - "Kembali ke Admin" button navigates back
   - "Logout" button redirects to login

**Step 3: Test authentication**

1. Open `http://localhost:3030/projects` without logging in
2. Verify: Redirected to `/login`

**Step 4: Test error handling**

1. Check browser console for errors
2. Verify API calls work correctly

---

## Notes

- The template uses the same CSS variables and styling patterns as admin.html
- JWT authentication is checked both server-side (in route) and client-side (in JavaScript)
- The delete functionality reuses the existing `DELETE /api/projects/{id}/delete` endpoint
- All text is in Indonesian as per the existing UI
