# Axelo 🗂️

> Open-source project management. Simple, fast, self-hostable.  
> Built with Vue 3 + FastAPI + PostgreSQL · Python 3.12 · Docker

---

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/axelo.git
cd axelo
cp .env.example .env        # then edit SECRET_KEY and POSTGRES_PASSWORD
docker compose up --build
```

- **App** → http://localhost:3000
- **API docs** → http://localhost:8000/docs

---

## Stack

| Layer    | Tech |
|----------|------|
| Frontend | Vue 3, Pinia, Tailwind CSS, Vite |
| Backend  | FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL 16 |
| Auth     | JWT · bcrypt · pyotp (TOTP) |
| Deploy   | Docker Compose · Nginx |

---

## Phase 1 — Foundation ✅

> Real-time collaboration, notifications, search, burndown charts.

| Feature | Description |
|---------|-------------|
| **Kanban Board** | Drag-and-drop across Todo → In Progress → In Review → Done |
| **Real-time Sync** | WebSocket broadcast — board updates instantly for all teammates |
| **Sprints** | Create, start, complete sprints with burndown chart |
| **Backlog** | Manage and prioritise unplanned issues |
| **Issues** | Types (bug / story / task / epic), priorities, story points, assignees |
| **Comments** | Threaded comments with `@mention` notifications |
| **Notifications Centre** | Bell icon, in-app notifications for assignments, mentions, status changes |
| **Global Search** | `Cmd+K` palette — search issues and projects instantly |
| **Issue Templates** | Pre-defined templates per project (bug report, feature request, incident) |
| **Keyboard Shortcuts** | `G→B` Board · `G→L` Backlog · `G→T` Team · `G→R` Reports · `?` Help |
| **Roles** | Owner / Admin / Member / Viewer |
| **Projects** | Unique keys (e.g. `FLOW-1`), invite members by email |

---

## Phase 2 — Integrations & Reporting ✅

> GitHub integration, file attachments, reporting dashboard, custom fields.

| Feature | Description |
|---------|-------------|
| **File Attachments** | Attach images, PDFs, and files to issues (50 MB max) |
| **GitHub Integration** | Link PRs and commits to issues · PR merged → issue moves to Done |
| **Reporting Dashboard** | Velocity, burndown, cycle time, issue flow charts |
| **Custom Fields** | Admins define text / number / select fields per project |
| **Audit Log** | Full history of every change — actor, timestamp, diff |
| **Rate Limiting** | slowapi — 10 req/min per IP on auth and write endpoints |
| **Calendar View** | Issues and sprint dates in a monthly calendar |

---

## Phase 3 — Security & Scale ⚠️

> 2FA, webhooks, time tracking, roadmap, OAuth login.

| Feature | Status | Description |
|---------|--------|-------------|
| **Two-Factor Authentication** | ✅ Complete | TOTP via pyotp · QR code setup · 10 single-use recovery codes (bcrypt-hashed) |
| **Webhook System** | ✅ Complete | Outbound webhooks · HMAC-SHA256 signatures · exponential backoff retry · Slack / Zapier / n8n compatible |
| **Time Tracking** | ✅ Complete | Log time on issues · weekly totals per member and per project |
| **Roadmap Timeline** | ✅ Complete | Gantt-style view · By Sprint / By Epic / All Issues modes |
| **SSO / OAuth Login** | ⚠️ Partial | Google ✅ · GitHub ✅ · Microsoft ❌ · SAML ❌ |
| **Mobile App** | ❌ Not built | React Native (Expo) planned — not yet implemented |

> **P3 completion note:** 5 of 6 features are fully shipped. Microsoft OAuth, SAML enterprise support, and the React Native mobile app remain as future work.

---

## Phase 4 — AI & Team Intelligence ✅

> AI-powered sprint planning, multi-org workspaces, Jira/Linear importer.

| Feature | Route | Description |
|---------|-------|-------------|
| **AI Issue Summary** | Issue view → ✦ AI Summary | Claude summarises the issue thread and suggests next actions |
| **AI Sprint Planner** | `/projects/:id/ai/sprint-planner` | Claude analyses velocity history and recommends optimal sprint composition |
| **Organisations** | `/orgs` | Multi-workspace grouping, member management, cross-project search |
| **Importer** | `/projects/:id/import` | Jira JSON · Linear JSON · CSV · Axelo re-import · async background jobs |

### AI Setup

```bash
# Add to .env
ANTHROPIC_API_KEY=sk-ant-api03-...   # get at console.anthropic.com
AI_ENABLED=true
AI_MODEL=claude-opus-4-6
```

Set `AI_ENABLED=false` to disable AI endpoints without removing them.  
AI requests are rate-limited (10/min per IP) with a 10,000 token daily budget per user.

---

## Registration Security ✅

> Email verification and bot protection on account creation.

| Feature | Description |
|---------|-------------|
| **Email Verification** | New accounts must verify their email before logging in · one-time SHA-256-hashed token · 24 h expiry · resend endpoint (rate-limited 3/hour, enumeration-safe) · OAuth users auto-verified |
| **CAPTCHA** | Cloudflare Turnstile (or hCaptcha) on the registration form · token verified server-side — stripping the widget from the DOM still fails the backend check · secret key never leaves the server |

---

## Content-Security-Policy ✅

> Strict CSP on every response — browser-enforced XSS mitigation.

The CSP is applied at **two layers**:

- **Nginx** — covers every HTML/JS/CSS response from the SPA (the correct place to stop XSS)
- **FastAPI `SecurityHeadersMiddleware`** — covers every API response

| Directive | Value | Why |
|-----------|-------|-----|
| `script-src` | `'self'` + CAPTCHA CDNs | No `'unsafe-inline'` — injected `<script>` tags are blocked |
| `object-src` | `'none'` | Blocks Flash, Java applets, and all legacy plugins |
| `base-uri` | `'self'` | Prevents `<base>` tag injection (dangling-markup attacks) |
| `form-action` | `'self'` | Forms cannot submit data to external hosts |
| `frame-ancestors` | `'none'` | Clickjacking defence (supersedes `X-Frame-Options`) |
| `frame-src` | CAPTCHA iframes only | Turnstile and hCaptcha widgets load; nothing else |
| `connect-src` | `'self'` + ws/wss + CAPTCHA | WebSocket and CAPTCHA API calls allowed |
| `upgrade-insecure-requests` | — | HTTP sub-resources are transparently upgraded to HTTPS |
| `style-src` | `'self' 'unsafe-inline'` | Retained for Vue scoped styles; CSS exfiltration is far harder to exploit than script injection |

> **Why `'unsafe-inline'` is gone from `script-src`:** The previous CSP included `script-src 'self' 'unsafe-inline'`, which made it completely ineffective — any injected inline `<script>` would execute. Vite bundles all JavaScript into external files, so inline scripts are never needed in production.

### Optional: CSP violation reporting

```bash
# .env — forward browser violation reports to a collector
CSP_REPORT_URI=https://your-id.report-uri.com/r/d/csp/enforce
```

Free collectors: [report-uri.com](https://report-uri.com), [Sentry](https://docs.sentry.io/product/security-policy-reporting/).

### Email Verification Setup

```bash
# Add to .env
EMAIL_VERIFICATION_ENABLED=true

SMTP_HOST=smtp.gmail.com          # or smtp.sendgrid.net, smtp.mailgun.org, etc.
SMTP_PORT=587
SMTP_USERNAME=you@gmail.com
SMTP_PASSWORD=your-app-password   # Gmail: Settings → Security → App Passwords
SMTP_FROM=noreply@yourdomain.com
SMTP_FROM_NAME=Axelo
SMTP_TLS=true
```

Set `EMAIL_VERIFICATION_ENABLED=false` to skip verification in local dev.

### CAPTCHA Setup

Get free Turnstile keys at **[dash.cloudflare.com](https://dash.cloudflare.com)** → Turnstile → Add site.

```bash
# Add to .env
CAPTCHA_ENABLED=true
CAPTCHA_PROVIDER=turnstile          # "turnstile" (default) or "hcaptcha"
CAPTCHA_SITE_KEY=0x...              # public key — safe to expose to the frontend
CAPTCHA_SECRET_KEY=0x...            # secret key — backend only, never sent to client
```

Set `CAPTCHA_ENABLED=false` to bypass CAPTCHA in local dev or automated tests.

> **Note:** If `CAPTCHA_ENABLED=true` but `CAPTCHA_SECRET_KEY` is empty, registration returns `503` — the server refuses to silently skip the check due to misconfiguration.

#### hCaptcha alternative

```bash
CAPTCHA_PROVIDER=hcaptcha
CAPTCHA_SITE_KEY=<hcaptcha site key>
CAPTCHA_SECRET_KEY=<hcaptcha secret key>
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `C` | Create issue |
| `G` → `B` | Board |
| `G` → `L` | Backlog |
| `G` → `T` | Team |
| `G` → `R` | Reports |
| `G` → `M` | Roadmap |
| `G` → `A` | AI Sprint Planner |
| `G` → `I` | Importer |
| `?` | Show all shortcuts |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | JWT signing key — generate with `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `POSTGRES_PASSWORD` | ✅ | Database password |
| `ANTHROPIC_API_KEY` | AI features | Get at console.anthropic.com |
| `GOOGLE_CLIENT_ID` | OAuth | Google OAuth app credentials |
| `GOOGLE_CLIENT_SECRET` | OAuth | |
| `GITHUB_CLIENT_ID` | OAuth | GitHub OAuth app credentials |
| `GITHUB_CLIENT_SECRET` | OAuth | |
| `FRONTEND_URL` | OAuth | e.g. `http://localhost:3000` |
| `AI_ENABLED` | | `true` / `false` (default `true`) |
| `EMAIL_VERIFICATION_ENABLED` | | `true` / `false` (default `true`) — set `false` in dev |
| `SMTP_HOST` | Email | SMTP server hostname |
| `SMTP_PORT` | Email | Usually `587` (STARTTLS) or `465` (TLS) |
| `SMTP_USERNAME` | Email | SMTP login username |
| `SMTP_PASSWORD` | Email | SMTP login password or app password |
| `SMTP_FROM` | Email | From address shown on outbound emails |
| `SMTP_TLS` | Email | `true` / `false` (default `true`) |
| `CAPTCHA_ENABLED` | | `true` / `false` (default `true`) — set `false` in dev |
| `CAPTCHA_PROVIDER` | CAPTCHA | `turnstile` (default) or `hcaptcha` |
| `CAPTCHA_SITE_KEY` | CAPTCHA | Public key from Cloudflare / hCaptcha dashboard |
| `CAPTCHA_SECRET_KEY` | CAPTCHA | Secret key — backend only, never expose |
| `CSP_REPORT_URI` | | Optional URL to receive CSP violation reports (e.g. report-uri.com) |

---

## Project Structure

```
axelo/
├── backend/
│   └── app/
│       ├── models/          # SQLAlchemy ORM models
│       ├── schemas/         # Pydantic schemas
│       ├── routers/         # FastAPI route handlers
│       └── core/            # Auth, security, email, permissions, webhooks
│   └── alembic/versions/    # DB migrations (0001 → 0004)
├── frontend/
│   └── src/
│       ├── views/           # Page components
│       ├── components/      # Reusable UI components
│       ├── store/           # Pinia stores
│       ├── api/             # Axios API client
│       └── router/          # Vue Router
├── docker-compose.yml
├── SECURITY_AUDIT.md        # Full OWASP audit report
└── .env.example
```

---

## Security

A full OWASP Top 10 audit was performed across all phases. See [`SECURITY_AUDIT.md`](./SECURITY_AUDIT.md) for the complete report. Key controls:

- RBAC enforced on every mutation endpoint
- Rate limiting on all auth and write endpoints
- TOTP 2FA with bcrypt-hashed recovery codes
- HMAC-SHA256 webhook signatures
- SSRF protection on outbound webhook delivery
- JWT never appears in server logs (OAuth uses URL fragment `#token=`)
- Prompt injection defence on all AI endpoints
- `X-Content-Type-Options: nosniff` on all file downloads
- Email verification — accounts blocked until email ownership is confirmed
- CAPTCHA verified server-side — client-side widget bypass does not work
- CAPTCHA secret key never sent to the frontend (`/captcha-config` returns only the public site key)
- Verification tokens stored as SHA-256 hashes, invalidated on first use
- Strict `Content-Security-Policy` on every response — `script-src` has no `'unsafe-inline'`, blocking injected scripts at the browser level
- `object-src 'none'`, `base-uri 'self'`, `form-action 'self'` — plugins, base-tag injection, and form exfiltration all blocked

---

## Local Development

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev     # proxies /api → http://localhost:8000
```

---

## What's Not Built Yet

| Item | Phase | Notes |
|------|-------|-------|
| Microsoft OAuth | P3 | Add to `auth.py` alongside Google/GitHub |
| SAML enterprise SSO | P3 | Requires `python3-saml` or `pysaml2` |
| React Native mobile app | P3 | Expo app using the existing REST API |
| Kubernetes Helm chart | P4 | Production self-hosted deployment |

---

## License

MIT


> Open-source project management. Simple, fast, self-hostable.  
> Built with Vue 3 + FastAPI + PostgreSQL · Python 3.12 · Docker

---

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/axelo.git
cd axelo
cp .env.example .env        # then edit SECRET_KEY and POSTGRES_PASSWORD
docker compose up --build
```

- **App** → http://localhost:3000
- **API docs** → http://localhost:8000/docs

---

## Stack

| Layer    | Tech |
|----------|------|
| Frontend | Vue 3, Pinia, Tailwind CSS, Vite |
| Backend  | FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL 16 |
| Auth     | JWT · bcrypt · pyotp (TOTP) |
| Deploy   | Docker Compose · Nginx |

---

## Phase 1 — Foundation ✅

> Real-time collaboration, notifications, search, burndown charts.

| Feature | Description |
|---------|-------------|
| **Kanban Board** | Drag-and-drop across Todo → In Progress → In Review → Done |
| **Real-time Sync** | WebSocket broadcast — board updates instantly for all teammates |
| **Sprints** | Create, start, complete sprints with burndown chart |
| **Backlog** | Manage and prioritise unplanned issues |
| **Issues** | Types (bug / story / task / epic), priorities, story points, assignees |
| **Comments** | Threaded comments with `@mention` notifications |
| **Notifications Centre** | Bell icon, in-app notifications for assignments, mentions, status changes |
| **Global Search** | `Cmd+K` palette — search issues and projects instantly |
| **Issue Templates** | Pre-defined templates per project (bug report, feature request, incident) |
| **Keyboard Shortcuts** | `G→B` Board · `G→L` Backlog · `G→T` Team · `G→R` Reports · `?` Help |
| **Roles** | Owner / Admin / Member / Viewer |
| **Projects** | Unique keys (e.g. `FLOW-1`), invite members by email |

---

## Phase 2 — Integrations & Reporting ✅

> GitHub integration, file attachments, reporting dashboard, custom fields.

| Feature | Description |
|---------|-------------|
| **File Attachments** | Attach images, PDFs, and files to issues (50 MB max) |
| **GitHub Integration** | Link PRs and commits to issues · PR merged → issue moves to Done |
| **Reporting Dashboard** | Velocity, burndown, cycle time, issue flow charts |
| **Custom Fields** | Admins define text / number / select fields per project |
| **Audit Log** | Full history of every change — actor, timestamp, diff |
| **Rate Limiting** | slowapi — 10 req/min per IP on auth and write endpoints |
| **Calendar View** | Issues and sprint dates in a monthly calendar |

---

## Phase 3 — Security & Scale ⚠️

> 2FA, webhooks, time tracking, roadmap, OAuth login.

| Feature | Status | Description |
|---------|--------|-------------|
| **Two-Factor Authentication** | ✅ Complete | TOTP via pyotp · QR code setup · 10 single-use recovery codes (bcrypt-hashed) |
| **Webhook System** | ✅ Complete | Outbound webhooks · HMAC-SHA256 signatures · exponential backoff retry · Slack / Zapier / n8n compatible |
| **Time Tracking** | ✅ Complete | Log time on issues · weekly totals per member and per project |
| **Roadmap Timeline** | ✅ Complete | Gantt-style view · By Sprint / By Epic / All Issues modes |
| **SSO / OAuth Login** | ⚠️ Partial | Google ✅ · GitHub ✅ · Microsoft ❌ · SAML ❌ |
| **Mobile App** | ❌ Not built | React Native (Expo) planned — not yet implemented |

> **P3 completion note:** 5 of 6 features are fully shipped. Microsoft OAuth, SAML enterprise support, and the React Native mobile app remain as future work.

---

## Phase 4 — AI & Team Intelligence ✅

> AI-powered sprint planning, multi-org workspaces, Jira/Linear importer.

| Feature | Route | Description |
|---------|-------|-------------|
| **AI Issue Summary** | Issue view → ✦ AI Summary | Claude summarises the issue thread and suggests next actions |
| **AI Sprint Planner** | `/projects/:id/ai/sprint-planner` | Claude analyses velocity history and recommends optimal sprint composition |
| **Organisations** | `/orgs` | Multi-workspace grouping, member management, cross-project search |
| **Importer** | `/projects/:id/import` | Jira JSON · Linear JSON · CSV · Axelo re-import · async background jobs |

### AI Setup

```bash
# Add to .env
ANTHROPIC_API_KEY=sk-ant-api03-...   # get at console.anthropic.com
AI_ENABLED=true
AI_MODEL=claude-opus-4-6
```

Set `AI_ENABLED=false` to disable AI endpoints without removing them.
AI requests are rate-limited (10/min per IP) with a 10,000 token daily budget per user.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `C` | Create issue |
| `G` → `B` | Board |
| `G` → `L` | Backlog |
| `G` → `T` | Team |
| `G` → `R` | Reports |
| `G` → `M` | Roadmap |
| `G` → `A` | AI Sprint Planner |
| `G` → `I` | Importer |
| `?` | Show all shortcuts |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | JWT signing key — generate with `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `POSTGRES_PASSWORD` | ✅ | Database password |
| `ANTHROPIC_API_KEY` | AI features | Get at console.anthropic.com |
| `GOOGLE_CLIENT_ID` | OAuth | Google OAuth app credentials |
| `GOOGLE_CLIENT_SECRET` | OAuth | |
| `GITHUB_CLIENT_ID` | OAuth | GitHub OAuth app credentials |
| `GITHUB_CLIENT_SECRET` | OAuth | |
| `FRONTEND_URL` | OAuth | e.g. `http://localhost:3000` |
| `AI_ENABLED` | | `true` / `false` (default `true`) |

---

## Project Structure

```
axelo/
├── backend/
│   └── app/
│       ├── models/          # SQLAlchemy ORM models
│       ├── schemas/         # Pydantic schemas
│       ├── routers/         # FastAPI route handlers
│       └── core/            # Auth, security, permissions, webhooks
│   └── alembic/versions/    # DB migrations (0001 → 0003)
├── frontend/
│   └── src/
│       ├── views/           # Page components
│       ├── components/      # Reusable UI components
│       ├── store/           # Pinia stores
│       ├── api/             # Axios API client
│       └── router/          # Vue Router
├── docker-compose.yml
├── SECURITY_AUDIT.md        # Full OWASP audit report
└── .env.example
```

---

## Security

A full OWASP Top 10 audit was performed across all phases. See [`SECURITY_AUDIT.md`](./SECURITY_AUDIT.md) for the complete report. Key controls:

- RBAC enforced on every mutation endpoint
- Rate limiting on all auth and write endpoints
- TOTP 2FA with bcrypt-hashed recovery codes
- HMAC-SHA256 webhook signatures
- SSRF protection on outbound webhook delivery
- JWT never appears in server logs (OAuth uses URL fragment `#token=`)
- Prompt injection defence on all AI endpoints
- `X-Content-Type-Options: nosniff` on all file downloads

---

## Local Development

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev     # proxies /api → http://localhost:8000
```

---

## What's Not Built Yet

| Item | Phase | Notes |
|------|-------|-------|
| Microsoft OAuth | P3 | Add to `auth.py` alongside Google/GitHub |
| SAML enterprise SSO | P3 | Requires `python3-saml` or `pysaml2` |
| React Native mobile app | P3 | Expo app using the existing REST API |
| Kubernetes Helm chart | P4 | Production self-hosted deployment |

---

## License

MIT
