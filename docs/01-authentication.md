# Authentication

User registration and login with JWT-based session management.

## Endpoints

| Method | Path | Auth required |
|--------|------|:---:|
| POST | `/api/auth/register` | No |
| POST | `/api/auth/login` | No |
| GET | `/api/auth/verify` | Yes |
| POST | `/api/auth/logout` | No |

## Register

**POST /api/auth/register**

```json
{
  "name": "Soni",
  "email": "soni@example.com",
  "password": "secret123"
}
```

**Constraints:**
- `name`: required
- `email`: required, must be unique
- `password`: minimum 6 characters

**Success response:**
```json
{ "success": true, "message": "Registrasi berhasil", "user": { "id": 1, "name": "Soni", "email": "soni@example.com" } }
```

**Error responses:**
```json
{ "success": false, "message": "Semua field harus diisi" }
{ "success": false, "message": "Password minimal 6 karakter" }
{ "success": false, "message": "Email sudah terdaftar" }
```

## Login

**POST /api/auth/login**

```json
{ "email": "soni@example.com", "password": "secret123" }
```

**Success response:**
```json
{
  "success": true,
  "token": "<jwt>",
  "user": { "id": 1, "name": "Soni", "email": "soni@example.com" }
}
```

**Error responses:**
```json
{ "success": false, "message": "Email dan password harus diisi" }
{ "success": false, "message": "Email atau password salah" }
```

## Using the Token

All protected endpoints require the token in the `Authorization` header:

```
Authorization: Bearer <token>
```

The frontend stores the token in `localStorage` (`token` key) and attaches it automatically via `apiRequest()` in `static/js/auth.js`.

**Token expiry:** 24 hours. Expired tokens return HTTP 401, which triggers automatic logout and redirect to `/login`.

## Password Security

Passwords are hashed with **PBKDF2-SHA256** (29,000 rounds). Legacy **bcrypt** hashes from old JSON-based accounts are also validated for backward compatibility (migration path).

## Frontend Pages

| Path | Template | Purpose |
|------|----------|---------|
| `/login` | `templates/login.html` | Login form |
| `/register` | `templates/register.html` | Registration form |

## Logout

JWT tokens are stateless — logout is client-side only (removes `token` and `user` from `localStorage`). The `/api/auth/logout` endpoint exists for completeness but does not invalidate the token server-side.
