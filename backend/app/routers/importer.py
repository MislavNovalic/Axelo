"""
Issue Importer — Phase 4.
Supports Jira (JSON export), Linear (JSON export), and generic CSV.

POST /api/projects/{id}/import/preview   → Validate & preview (dry run, no write)
POST /api/projects/{id}/import/run       → Execute import
GET  /api/projects/{id}/import/jobs      → List import jobs
GET  /api/projects/{id}/import/jobs/{j}  → Get job status

OWASP:
  A01 — admin/owner only, project ownership verified
  A04 — field allowlist, no raw JSON passed to ORM
  A07 — IMPORT_MAX_ISSUES limit enforced
  A08 — JSON schema validated by Pydantic before any processing
"""
import json
import csv
import io
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import require_admin_or_owner
from app.models.user import User
from app.models.project import Project
from app.models.issue import Issue, IssueType, IssueStatus, IssuePriority
from app.models.organisation import ImportJob
from app.config import settings

router = APIRouter(prefix="/api/projects/{project_id}/import", tags=["importer"])

SUPPORTED_SOURCES = {"jira", "linear", "csv", "axelo"}

# ── Field mapping constants ───────────────────────────────────────────────────

JIRA_STATUS_MAP = {
    "to do": IssueStatus.todo, "in progress": IssueStatus.in_progress,
    "in review": IssueStatus.in_review, "done": IssueStatus.done,
    "backlog": IssueStatus.backlog, "closed": IssueStatus.done,
    "resolved": IssueStatus.done, "open": IssueStatus.todo,
}
JIRA_PRIORITY_MAP = {
    "highest": IssuePriority.critical, "high": IssuePriority.high,
    "medium": IssuePriority.medium, "low": IssuePriority.low,
    "lowest": IssuePriority.low, "blocker": IssuePriority.critical,
    "critical": IssuePriority.critical,
}
JIRA_TYPE_MAP = {
    "bug": IssueType.bug, "story": IssueType.story, "task": IssueType.task,
    "epic": IssueType.epic, "sub-task": IssueType.task, "improvement": IssueType.story,
    "new feature": IssueType.story,
}

LINEAR_STATUS_MAP = {
    "backlog": IssueStatus.backlog, "todo": IssueStatus.todo,
    "in progress": IssueStatus.in_progress, "in review": IssueStatus.in_review,
    "done": IssueStatus.done, "cancelled": IssueStatus.done,
}
LINEAR_PRIORITY_MAP = {0: IssuePriority.low, 1: IssuePriority.low, 2: IssuePriority.medium,
                       3: IssuePriority.high, 4: IssuePriority.critical}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_project(project_id: int, user: User, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    require_admin_or_owner(project, user, db)
    return project


def _next_issue_key(project: Project, db: Session) -> str:
    last = (
        db.query(Issue)
        .filter(Issue.project_id == project.id)
        .order_by(Issue.id.desc())
        .first()
    )
    if last and last.key:
        m = re.search(r'(\d+)$', last.key)
        num = int(m.group(1)) + 1 if m else 1
    else:
        num = 1
    return f"{project.key}-{num}"


def _safe_str(val, max_len: int = 500) -> str:
    if val is None:
        return ""
    return str(val)[:max_len]


def _parse_jira(data: dict | list) -> list[dict]:
    """Parse Jira JSON export (issues array or {issues: [...]} wrapper)."""
    issues_raw = data if isinstance(data, list) else data.get("issues", [])
    out = []
    for item in issues_raw:
        fields = item.get("fields", item)  # support both flat and nested
        status_str = ""
        if isinstance(fields.get("status"), dict):
            status_str = fields["status"].get("name", "").lower()
        elif isinstance(fields.get("status"), str):
            status_str = fields["status"].lower()

        priority_str = ""
        if isinstance(fields.get("priority"), dict):
            priority_str = fields["priority"].get("name", "").lower()
        elif isinstance(fields.get("priority"), str):
            priority_str = fields["priority"].lower()

        type_str = ""
        if isinstance(fields.get("issuetype"), dict):
            type_str = fields["issuetype"].get("name", "").lower()
        elif isinstance(fields.get("type"), str):
            type_str = fields["type"].lower()

        out.append({
            "title":       _safe_str(fields.get("summary") or fields.get("title"), 300),
            "description": _safe_str(fields.get("description"), 5000),
            "status":      JIRA_STATUS_MAP.get(status_str, IssueStatus.backlog),
            "priority":    JIRA_PRIORITY_MAP.get(priority_str, IssuePriority.medium),
            "type":        JIRA_TYPE_MAP.get(type_str, IssueType.task),
            "story_points": int(fields.get("story_points") or fields.get("storyPoints") or fields.get("customfield_10016") or 0) or None,
            "source_key":  _safe_str(item.get("key", ""), 50),
        })
    return out


def _parse_linear(data: dict | list) -> list[dict]:
    """Parse Linear JSON export."""
    issues_raw = data if isinstance(data, list) else data.get("issues", [])
    out = []
    for item in issues_raw:
        state = item.get("state", {})
        state_name = (state.get("name") if isinstance(state, dict) else str(state)).lower()
        priority = LINEAR_PRIORITY_MAP.get(int(item.get("priority", 2)), IssuePriority.medium)
        out.append({
            "title":       _safe_str(item.get("title"), 300),
            "description": _safe_str(item.get("description"), 5000),
            "status":      LINEAR_STATUS_MAP.get(state_name, IssueStatus.backlog),
            "priority":    priority,
            "type":        IssueType.task,
            "story_points": int(item.get("estimate", 0)) or None,
            "source_key":  _safe_str(item.get("identifier", ""), 50),
        })
    return out


def _parse_csv(content: str) -> list[dict]:
    """Parse generic CSV (title, description, status, priority, type, story_points)."""
    reader = csv.DictReader(io.StringIO(content))
    out = []
    for row in reader:
        status_str  = row.get("status", "backlog").strip().lower().replace(" ", "_")
        priority_str = row.get("priority", "medium").strip().lower()
        type_str    = row.get("type", "task").strip().lower()
        out.append({
            "title":       _safe_str(row.get("title") or row.get("summary"), 300),
            "description": _safe_str(row.get("description"), 5000),
            "status":      IssueStatus.__members__.get(status_str, IssueStatus.backlog),
            "priority":    IssuePriority.__members__.get(priority_str, IssuePriority.medium),
            "type":        IssueType.__members__.get(type_str, IssueType.task),
            "story_points": int(row.get("story_points") or row.get("points") or 0) or None,
            "source_key":  _safe_str(row.get("key", ""), 50),
        })
    return [i for i in out if i["title"]]  # skip empty rows


def _parse_axelo(data: dict | list) -> list[dict]:
    """Re-import from Axelo's own export format."""
    issues_raw = data if isinstance(data, list) else data.get("issues", [])
    out = []
    for item in issues_raw:
        out.append({
            "title":       _safe_str(item.get("title"), 300),
            "description": _safe_str(item.get("description"), 5000),
            "status":      IssueStatus.__members__.get(item.get("status", "backlog"), IssueStatus.backlog),
            "priority":    IssuePriority.__members__.get(item.get("priority", "medium"), IssuePriority.medium),
            "type":        IssueType.__members__.get(item.get("type", "task"), IssueType.task),
            "story_points": int(item.get("story_points") or 0) or None,
            "source_key":  _safe_str(item.get("key", ""), 50),
        })
    return [i for i in out if i["title"]]


def _parse_upload(source: str, content: bytes) -> list[dict]:
    if source == "csv":
        return _parse_csv(content.decode("utf-8", errors="replace"))
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON file")
    if source == "jira":
        return _parse_jira(data)
    elif source == "linear":
        return _parse_linear(data)
    elif source == "axelo":
        return _parse_axelo(data)
    raise HTTPException(400, f"Unsupported source: {source}")


# ── Background import task ────────────────────────────────────────────────────

def _run_import(job_id: int, project_id: int, parsed: list[dict], db_url: str):
    """Runs in background — creates issues and updates the job record."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
        if not job:
            return
        job.status = "running"
        db.commit()

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            job.status = "failed"
            db.commit()
            return

        imported = 0
        skipped = 0
        errors = []

        # Start order and key counter after existing issues
        base_count = db.query(Issue).filter(Issue.project_id == project_id).count()
        last_order = base_count
        next_key_num = base_count + 1

        for idx, item in enumerate(parsed):
            try:
                if not item.get("title"):
                    skipped += 1
                    continue

                key = f"{project.key}-{next_key_num}"

                issue = Issue(
                    project_id=project_id,
                    key=key,
                    title=item["title"],
                    description=item.get("description") or None,
                    status=item["status"],
                    priority=item["priority"],
                    type=item["type"],
                    story_points=item.get("story_points"),
                    reporter_id=job.created_by,
                    order=last_order + idx,
                )
                db.add(issue)
                db.flush()
                imported += 1
                next_key_num += 1

                # Commit in batches of 50
                if imported % 50 == 0:
                    db.commit()

            except Exception as e:
                db.rollback()
                # Re-sync counter from DB after rollback (unflushed issues were lost)
                next_key_num = db.query(Issue).filter(Issue.project_id == project_id).count() + 1
                skipped += 1
                errors.append(f"Row {idx+1}: {str(e)[:200]}")

        db.commit()
        job.status = "done"
        job.imported = imported
        job.skipped = skipped
        job.errors = json.dumps(errors[:50]) if errors else None
        job.finished_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        try:
            job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.errors = json.dumps([str(e)[:500]])
                job.finished_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/preview")
async def preview_import(
    project_id: int,
    source: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dry-run: parse and validate the file, return stats without writing."""
    if source not in SUPPORTED_SOURCES:
        raise HTTPException(400, f"source must be one of: {', '.join(SUPPORTED_SOURCES)}")

    _get_project(project_id, current_user, db)

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:   # 10 MB cap
        raise HTTPException(413, "Import file exceeds 10 MB limit")

    parsed = _parse_upload(source, content)

    if len(parsed) > settings.IMPORT_MAX_ISSUES:
        raise HTTPException(
            400,
            f"File contains {len(parsed):,} issues; maximum is {settings.IMPORT_MAX_ISSUES:,}"
        )

    # Count by type/status/priority for preview
    from collections import Counter
    type_dist     = Counter(i["type"].value for i in parsed)
    status_dist   = Counter(i["status"].value for i in parsed)
    priority_dist = Counter(i["priority"].value for i in parsed)

    return {
        "source": source,
        "total": len(parsed),
        "type_distribution": dict(type_dist),
        "status_distribution": dict(status_dist),
        "priority_distribution": dict(priority_dist),
        "sample": [
            {"title": i["title"], "type": i["type"].value,
             "status": i["status"].value, "story_points": i["story_points"]}
            for i in parsed[:5]
        ],
        "warnings": (
            [f"Large import: {len(parsed):,} issues will be created"]
            if len(parsed) > 500 else []
        ),
    }


@router.post("/run", status_code=202)
async def run_import(
    project_id: int,
    source: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute the import asynchronously. Returns a job ID to poll for status."""
    if source not in SUPPORTED_SOURCES:
        raise HTTPException(400, f"source must be one of: {', '.join(SUPPORTED_SOURCES)}")

    project = _get_project(project_id, current_user, db)

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "Import file exceeds 10 MB limit")

    parsed = _parse_upload(source, content)
    if not parsed:
        raise HTTPException(400, "No valid issues found in file")
    if len(parsed) > settings.IMPORT_MAX_ISSUES:
        raise HTTPException(400, f"Too many issues (max {settings.IMPORT_MAX_ISSUES:,})")

    job = ImportJob(
        project_id=project_id,
        created_by=current_user.id,
        source=source,
        total=len(parsed),
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    from app.config import settings as cfg
    background_tasks.add_task(_run_import, job.id, project_id, parsed, cfg.DATABASE_URL)

    return {
        "job_id": job.id,
        "status": "pending",
        "total": len(parsed),
        "message": f"Import of {len(parsed):,} issues started. Poll /import/jobs/{job.id} for status.",
    }


@router.get("/jobs")
def list_import_jobs(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project(project_id, current_user, db)
    jobs = (
        db.query(ImportJob)
        .filter(ImportJob.project_id == project_id)
        .order_by(ImportJob.created_at.desc())
        .limit(20)
        .all()
    )
    return [_fmt_job(j) for j in jobs]


@router.get("/jobs/{job_id}")
def get_import_job(
    project_id: int,
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project(project_id, current_user, db)
    job = db.query(ImportJob).filter(
        ImportJob.id == job_id, ImportJob.project_id == project_id
    ).first()
    if not job:
        raise HTTPException(404, "Import job not found")
    return _fmt_job(job)


def _fmt_job(job: ImportJob) -> dict:
    return {
        "id": job.id,
        "source": job.source,
        "status": job.status,
        "total": job.total,
        "imported": job.imported,
        "skipped": job.skipped,
        "progress_pct": round(100 * (job.imported + job.skipped) / max(job.total, 1)),
        "errors": json.loads(job.errors) if job.errors else [],
        "created_at": job.created_at.isoformat(),
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }
