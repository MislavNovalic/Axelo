# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

**Axelo** — a self-hostable project management platform (open-source Jira alternative). Vue 3 + FastAPI + PostgreSQL, deployed via Docker Compose.

---

## Commands

### Full stack (Docker)
```bash
docker compose up --build          # First run or after Dockerfile changes
docker compose up                  # Subsequent runs
docker compose down -v             # Tear down including volumes
```
Frontend: http://localhost:4173 · API docs: http://localhost:9876/docs

### Backend (standalone dev)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend (standalone dev)
```bash
cd frontend
npm install
npm run dev       # Vite dev server with /api proxy to localhost:8000
npm run build
npm run preview
```

### Database migrations
```bash
# Run all pending migrations
cd backend && alembic upgrade head

# Create a new migration (after editing models)
alembic revision --autogenerate -m "description"
```
Migrations run automatically in `start.sh` on container start.

---

## Architecture

### Stack
- **Frontend**: Vue 3 (Composition API), Pinia stores, Vue Router, Axios, Vite → served by Nginx in Docker
- **Backend**: FastAPI, SQLAlchemy (sync ORM), Alembic migrations, slowapi rate limiting, arq Redis task queue
- **Database**: PostgreSQL 16
- **Real-time**: WebSocket via `app/core/ws_manager.py` — broadcasts project-scoped events to connected clients

### Backend layout
```
backend/app/
  main.py          — FastAPI app, middleware registration, router mounting
  config.py        — Pydantic Settings (reads from env / .env file)
  database.py      — SessionLocal, Base, get_db dependency
  models/          — SQLAlchemy ORM models (one file per domain)
  schemas/         — Pydantic request/response schemas
  routers/         — One file per feature group (see below)
  core/
    auth.py        — JWT creation/decoding, password hashing
    deps.py        — get_current_user FastAPI dependency
    permissions.py — RBAC helpers: require_project_write, require_admin_or_owner
    security.py    — Rate limiter, SecurityHeadersMiddleware, CSP, CAPTCHA verification
    email.py       — Async SMTP email templates (verification + notifications)
    notify.py      — In-process notification creation + optional email dispatch
    ws_manager.py  — WebSocket connection registry and broadcast
    audit.py       — Audit log helpers
    webhook_delivery.py — Outbound webhook signing (HMAC-SHA256) + retry logic
    queue.py       — arq Redis worker settings for async email tasks
```

### Router prefixes (all under `/api/`)
| Router file | Prefix |
|---|---|
| auth | `/api/auth` |
| projects | `/api/projects` |
| issues | `/api/projects/{id}/issues` |
| sprints | `/api/projects/{id}/sprints` |
| reports | `/api/projects/{id}/reports` |
| files | `/api/projects/{id}/issues/{id}/attachments` |
| time_tracking | `/api/projects/{id}/issues/{id}/time-logs` *(no prefix in router def — `prefix="/api"` added in main.py)* |
| webhooks | *(same — prefix added in main.py)* |
| roadmap | *(same — prefix added in main.py)* |
| orgs | `/api/orgs` |
| importer | `/api/projects/{id}/import` |
| ai | `/api/projects/{id}` |
| search | `/api/search` |
| calendar | `/api/calendar` |
| stats | `/api/stats` |

### Frontend layout
```
frontend/src/
  main.js          — App init, global error handler, Pinia + Router setup
  router/index.js  — Vue Router; auth guard redirects unauthenticated users to /login
  store/
    auth.js        — Login, register, OAuth callbacks, 2FA flow, token storage
    projects.js    — Project CRUD + member management
    issues.js      — Issue CRUD, filtering, ordering
    notifications.js — In-app notification polling/websocket
    ws.js          — WebSocket connection lifecycle
  api/             — Axios instance with JWT interceptor; 401 → redirect /login
  views/           — One Vue component per page/route
  components/      — Shared UI components
```

---

## Key Patterns and Conventions

### Permission checks (backend)
Every mutation endpoint must check access. Pattern:
```python
project = get_project_or_404(project_id, db)
require_project_write(project, current_user, db)   # raises 403 for viewers
# OR
require_admin_or_owner(project, current_user, db)  # raises 403 for non-admins
```
`require_project_write` allows Owner/Admin/Member roles; blocks Viewer. The project owner is always expected to have a `ProjectMember` row with `MemberRole.owner`.

### Auth flow
- Standard login returns `{ access_token }` or `{ requires_2fa: true, temp_token }`.
- 2FA: frontend sends `temp_token + code` to `/api/auth/2fa/verify`.
- OAuth: backend redirects browser to provider; on callback, redirects to `frontend/#token=xxx` (URL **fragment**, not query param, to avoid server logs capturing the token).
- WebSocket auth: token passed as query param `?token=xxx` (not Bearer header).

### Email verification tokens
Tokens are stored as `SHA-256(raw_token)` in the database, never the raw value. Always validate with `_hash_token(supplied_token)` and compare hashes.

### Real-time broadcasts
After any mutation that changes project state, call `_broadcast(project_id, event, data)`. The helper handles the async/sync loop boundary safely.

### Migrations
After adding/changing a SQLAlchemy model, generate a migration:
```bash
alembic revision --autogenerate -m "add X column to Y table"
```
Review the generated file in `alembic/versions/` before committing — autogenerate misses some things (e.g. enum changes, index naming).

### Environment variables for local dev
Set in `.env` (copy from `.env.example`). Critical for dev:
```
CAPTCHA_ENABLED=false          # No Turnstile/hCaptcha keys needed
EMAIL_VERIFICATION_ENABLED=false  # No SMTP needed
```
Both default to `true`, which blocks registration and login in a clean environment with no keys configured.

### docker-compose `prefix="/api"` routers
Three routers (`time_tracking`, `webhooks`, `roadmap`) have no prefix in their `APIRouter()` definition and receive it only from `app.include_router(..., prefix="/api")` in `main.py`. Don't add `/api` to those router files.

---

## Data Model Highlights

- **Issue key**: `{PROJECT_KEY}-{n}` (e.g. `FLOW-42`), unique per project, auto-generated on create.
- **Issue hierarchy**: `parent_id` self-reference for epics. `type` enum: bug/story/task/epic.
- **Sprint status**: planning → active → completed (only one active sprint per project).
- **Notifications**: stored in DB (`Notification` model), optionally queued to Redis for email dispatch via arq worker.
- **Webhook deliveries**: tracked with attempts, response code/body, `next_retry_at`. Retries: 1 min, 5 min, 30 min.
- **Audit log**: every issue mutation records `{ field: [old, new] }` diffs in `AuditLog`.

## AI Features
`ANTHROPIC_API_KEY` must be set and `AI_ENABLED=true`. Model defaults to `claude-opus-4-6` (configurable via `AI_MODEL`). Rate limited to 10 req/min per IP and 10k tokens/day per user. Two endpoints: issue summarisation and sprint planner.
