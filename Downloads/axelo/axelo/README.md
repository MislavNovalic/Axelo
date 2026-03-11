# Axelo 🗂️

> Open-source project management. Simple, fast, self-hostable.  
> Built with Vue 3 + FastAPI + PostgreSQL.

## Features (MVP)

- **Auth** — Register, login, JWT sessions
- **Projects** — Create projects with unique keys (e.g. `FLOW-1`), invite members by email
- **Kanban Board** — Drag-and-drop issues across Todo → In Progress → In Review → Done
- **Backlog** — Manage unplanned issues and organize sprints
- **Sprints** — Create, start, and complete sprints
- **Issues** — Types (bug/story/task/epic), priorities, story points, assignees, descriptions
- **Comments** — Threaded comments on issues
- **Roles** — Owner / Admin / Member / Viewer

## Quick Start (Docker)

```bash
git clone https://github.com/yourname/axelo
cd axelo

# Copy env
cp backend/.env.example backend/.env

# Run everything
docker compose up --build
```

- App: http://localhost:3000  
- API docs: http://localhost:8000/docs  

## Local Development

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Set DATABASE_URL in .env pointing to your local Postgres
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Proxies /api → http://localhost:8000
```

## Stack

| Layer    | Tech                  |
|----------|-----------------------|
| Frontend | Vue 3, Pinia, Tailwind CSS, Vite |
| Backend  | FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL            |
| Auth     | JWT (python-jose + bcrypt) |
| Deploy   | Docker + Nginx        |

## Project Structure

```
axelo/
├── backend/
│   └── app/
│       ├── models/       # SQLAlchemy ORM models
│       ├── schemas/      # Pydantic schemas
│       ├── routers/      # FastAPI route handlers
│       └── core/         # Auth utilities & deps
├── frontend/
│   └── src/
│       ├── views/        # Page components
│       ├── components/   # Reusable UI components
│       ├── store/        # Pinia stores
│       ├── api/          # Axios API client
│       └── router/       # Vue Router
└── docker-compose.yml
```

## Roadmap (post-MVP)

- [ ] File attachments
- [ ] Email notifications
- [ ] Activity feed / audit log
- [ ] Advanced filters & search
- [ ] Burndown charts
- [ ] Dark/light theme toggle
- [ ] GitHub integration

## License

MIT
