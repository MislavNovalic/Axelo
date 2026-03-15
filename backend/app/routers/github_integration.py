"""
GitHub Integration — P2.
  POST /api/projects/{id}/github/connect          → save repo + secret
  GET  /api/projects/{id}/github/                 → get integration
  DELETE /api/projects/{id}/github/               → disconnect
  POST /api/integrations/github/webhook           → receive GitHub events
"""
import hmac
import hashlib
import re
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.issue import Issue, IssueStatus
from app.models.github_integration import GitHubIntegration, GitHubLink
from app.core.deps import get_current_user
from app.core.permissions import require_admin_or_owner

# Per-project router
router = APIRouter(tags=["github"])
proj_router = APIRouter(prefix="/api/projects/{project_id}/github")
webhook_router = APIRouter(prefix="/api/integrations/github")


class GitHubConnectBody(BaseModel):
    repo_owner: str
    repo_name: str
    webhook_secret: Optional[str] = None
    access_token: Optional[str] = None


def _get_project(pid: int, db: Session) -> Project:
    p = db.query(Project).filter(Project.id == pid).first()
    if not p:
        raise HTTPException(404, "Project not found")
    return p


@proj_router.post("/connect", status_code=201)
def connect_github(project_id: int, body: GitHubConnectBody,
                   db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = _get_project(project_id, db)
    require_admin_or_owner(project, current_user, db)
    existing = db.query(GitHubIntegration).filter_by(project_id=project_id).first()
    if existing:
        existing.repo_owner = body.repo_owner[:128]
        existing.repo_name  = body.repo_name[:128]
        if body.webhook_secret:
            existing.webhook_secret = body.webhook_secret
        if body.access_token:
            existing.access_token = body.access_token
    else:
        existing = GitHubIntegration(
            project_id=project_id, created_by=current_user.id,
            repo_owner=body.repo_owner[:128], repo_name=body.repo_name[:128],
            webhook_secret=body.webhook_secret, access_token=body.access_token,
        )
        db.add(existing)
    db.commit(); db.refresh(existing)
    return {"id": existing.id, "repo": f"{existing.repo_owner}/{existing.repo_name}",
            "webhook_url": f"/api/integrations/github/webhook?project_id={project_id}"}


@proj_router.get("/")
def get_github(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = _get_project(project_id, db)
    ids = {m.user_id for m in project.members} | {project.owner_id}
    if current_user.id not in ids:
        raise HTTPException(403, "Access denied")
    integration = db.query(GitHubIntegration).filter_by(project_id=project_id).first()
    if not integration:
        return None
    # Also return linked PRs
    links = db.query(GitHubLink).join(Issue).filter(Issue.project_id == project_id).order_by(GitHubLink.created_at.desc()).limit(20).all()
    return {
        "repo": f"{integration.repo_owner}/{integration.repo_name}",
        "connected": True,
        "recent_links": [_serialize_link(l) for l in links],
    }


@proj_router.delete("/", status_code=204)
def disconnect_github(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = _get_project(project_id, db)
    require_admin_or_owner(project, current_user, db)
    integration = db.query(GitHubIntegration).filter_by(project_id=project_id).first()
    if integration:
        db.delete(integration); db.commit()


@webhook_router.post("/webhook")
async def github_webhook(request: Request, project_id: int, db: Session = Depends(get_db)):
    """Receives GitHub webhook events and links them to issues."""
    body = await request.body()
    integration = db.query(GitHubIntegration).filter_by(project_id=project_id).first()

    # Verify HMAC signature if secret is configured
    if integration and integration.webhook_secret:
        sig_header = request.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(
            integration.webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig_header, expected):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    event_type = request.headers.get("X-GitHub-Event", "")
    payload = await request.json() if body else {}

    if event_type == "pull_request":
        _handle_pr_event(project_id, payload, db)
    elif event_type == "push":
        _handle_push_event(project_id, payload, db)

    return {"ok": True}


# ── Issue key pattern: AX-123, MOB-7, etc. ───────────────────────────────────
ISSUE_KEY_RE = re.compile(r'\b([A-Z]{1,10}-\d+)\b')


def _resolve_keys(text: str, project_id: int, db: Session) -> list[Issue]:
    keys = ISSUE_KEY_RE.findall(text or "")
    issues = []
    for key in set(keys):
        issue = db.query(Issue).filter(Issue.key == key, Issue.project_id == project_id).first()
        if issue:
            issues.append(issue)
    return issues


def _handle_pr_event(project_id: int, payload: dict, db: Session):
    pr   = payload.get("pull_request", {})
    title = pr.get("title", "")
    body  = pr.get("body", "")
    action = payload.get("action", "")
    issues = _resolve_keys(f"{title} {body}", project_id, db)

    for issue in issues:
        # Upsert link
        link = db.query(GitHubLink).filter_by(issue_id=issue.id, gh_number=pr.get("number"), link_type="pr").first()
        gh_state = pr.get("state", "open")
        merged   = pr.get("merged", False)
        if merged:
            gh_state = "merged"

        if link:
            link.gh_state = gh_state
            link.gh_title = title[:512]
        else:
            link = GitHubLink(
                issue_id=issue.id, link_type="pr",
                gh_number=pr.get("number"), gh_title=title[:512],
                gh_url=pr.get("html_url", "")[:512], gh_state=gh_state,
                payload={"action": action},
            )
            db.add(link)

        # Auto-transition: PR opened → in_review; merged → done
        if action == "opened" and issue.status.value in ("backlog", "todo", "in_progress"):
            issue.status = IssueStatus.in_review
        elif merged and issue.status != IssueStatus.done:
            issue.status = IssueStatus.done

    if issues:
        db.commit()


def _handle_push_event(project_id: int, payload: dict, db: Session):
    for commit in payload.get("commits", []):
        message = commit.get("message", "")
        issues = _resolve_keys(message, project_id, db)
        for issue in issues:
            sha = commit.get("id", "")[:40]
            existing = db.query(GitHubLink).filter_by(issue_id=issue.id, gh_sha=sha).first()
            if not existing:
                db.add(GitHubLink(
                    issue_id=issue.id, link_type="commit",
                    gh_sha=sha, gh_title=message[:512],
                    gh_url=commit.get("url", "")[:512], gh_state="committed",
                ))
    db.commit()


def _serialize_link(l: GitHubLink) -> dict:
    return {
        "id": l.id, "link_type": l.link_type, "issue_id": l.issue_id,
        "gh_number": l.gh_number, "gh_sha": l.gh_sha,
        "gh_title": l.gh_title, "gh_url": l.gh_url, "gh_state": l.gh_state,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    }


router.include_router(proj_router)
router.include_router(webhook_router)
