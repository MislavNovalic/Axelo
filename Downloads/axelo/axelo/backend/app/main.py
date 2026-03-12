import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.core.security_headers import SecurityHeadersMiddleware
from app.routers import auth, projects, issues, sprints, calendar
from app.routers import notifications, search, templates, websocket

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Axelo API",
    description="Open-source project management — Jira alternative",
    version="0.2.0",
)

# Rate limiting (A04 fix)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers (A05 fix)
app.add_middleware(SecurityHeadersMiddleware)

# CORS — configurable via env (A05 fix)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(issues.router)
app.include_router(sprints.router)
app.include_router(calendar.router)
app.include_router(notifications.router)
app.include_router(search.router)
app.include_router(templates.router)
app.include_router(websocket.router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.2.0"}
