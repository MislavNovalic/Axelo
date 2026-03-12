import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    auth, projects, issues, sprints, calendar, stats, ws,
    search, reports, files, templates, custom_fields, github_integration,
)
# Phase 3
from app.routers import time_tracking, webhooks, roadmap
from app.core.security import limiter, rate_limit_exceeded_handler, SecurityHeadersMiddleware
from slowapi.errors import RateLimitExceeded

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

app = FastAPI(
    title="Axelo API",
    description="Open-source project management — Jira alternative",
    version="1.0.0",
    docs_url="/docs"   if ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if ENVIRONMENT != "production" else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SecurityHeadersMiddleware)

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Core
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(issues.router)
app.include_router(sprints.router)
app.include_router(calendar.router)
app.include_router(stats.router)
app.include_router(ws.router)
# P1
app.include_router(search.router)
app.include_router(templates.router)
# P2
app.include_router(reports.router)
app.include_router(files.router)
app.include_router(custom_fields.router)
app.include_router(github_integration.router)
# P3
app.include_router(time_tracking.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(roadmap.router, prefix="/api")
# P4
from app.routers import ai, orgs, importer
app.include_router(ai.router)
app.include_router(orgs.router)
app.include_router(importer.router)


@app.get("/health")
def health():
    return {"status": "ok"}
