"""
Organisations / Multi-workspace — Phase 4.

POST   /api/orgs/                        → Create org
GET    /api/orgs/                        → List my orgs
GET    /api/orgs/{slug}                  → Get org details
PATCH  /api/orgs/{slug}                  → Update org (owner)
DELETE /api/orgs/{slug}                  → Delete org (owner)
POST   /api/orgs/{slug}/members          → Invite member by email
PATCH  /api/orgs/{slug}/members/{uid}    → Change member role
DELETE /api/orgs/{slug}/members/{uid}    → Remove member
GET    /api/orgs/{slug}/projects         → List org projects
POST   /api/orgs/{slug}/projects/{pid}   → Attach project to org
DELETE /api/orgs/{slug}/projects/{pid}   → Detach project from org
GET    /api/orgs/{slug}/search           → Cross-project search within org

OWASP A01: every mutation checks org ownership/role.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.organisation import Organisation, OrgMember
from app.models.project import Project, ProjectMember

router = APIRouter(prefix="/api/orgs", tags=["orgs"])

# ── Pydantic schemas ──────────────────────────────────────────────────────────

class OrgCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    slug: str = Field(..., min_length=2, max_length=64, pattern=r'^[a-z0-9\-]+$')
    logo_url: Optional[str] = Field(None, max_length=512)


class OrgUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=128)
    logo_url: Optional[str] = Field(None, max_length=512)


class InviteMember(BaseModel):
    email: str
    role: str = Field("member", pattern=r'^(admin|member)$')


class UpdateRole(BaseModel):
    role: str = Field(..., pattern=r'^(admin|member)$')


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_org(slug: str, db: Session) -> Organisation:
    org = db.query(Organisation).filter(Organisation.slug == slug).first()
    if not org:
        raise HTTPException(404, "Organisation not found")
    return org


def _get_membership(org: Organisation, user: User, db: Session) -> OrgMember:
    m = db.query(OrgMember).filter_by(org_id=org.id, user_id=user.id).first()
    if not m:
        raise HTTPException(403, "Not a member of this organisation")
    return m


def _require_admin(org: Organisation, user: User, db: Session):
    if org.owner_id == user.id:
        return
    m = db.query(OrgMember).filter_by(org_id=org.id, user_id=user.id).first()
    if not m or m.role not in ("admin", "owner"):
        raise HTTPException(403, "Admin or Owner role required")


def _require_owner(org: Organisation, user: User):
    if org.owner_id != user.id:
        raise HTTPException(403, "Only the organisation owner can perform this action")


def _fmt_org(org: Organisation, db: Session) -> dict:
    member_count = db.query(OrgMember).filter_by(org_id=org.id).count()
    project_count = db.query(Project).filter_by(org_id=org.id).count()
    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "logo_url": org.logo_url,
        "plan": org.plan,
        "owner_id": org.owner_id,
        "owner_name": org.owner.full_name if org.owner else None,
        "member_count": member_count,
        "project_count": project_count,
        "created_at": org.created_at.isoformat(),
    }


# ── Org CRUD ─────────────────────────────────────────────────────────────────

@router.post("/", status_code=201)
def create_org(
    body: OrgCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.query(Organisation).filter(Organisation.slug == body.slug).first():
        raise HTTPException(400, f"Slug '{body.slug}' is already taken")

    # Max 5 orgs per user (abuse prevention)
    owned = db.query(Organisation).filter(Organisation.owner_id == current_user.id).count()
    if owned >= 5:
        raise HTTPException(400, "Maximum 5 organisations per user")

    org = Organisation(
        name=body.name, slug=body.slug,
        logo_url=body.logo_url, owner_id=current_user.id,
    )
    db.add(org)
    db.flush()
    # Add owner as member
    db.add(OrgMember(org_id=org.id, user_id=current_user.id, role="owner"))
    db.commit()
    db.refresh(org)
    return _fmt_org(org, db)


@router.get("/")
def list_my_orgs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    memberships = db.query(OrgMember).filter_by(user_id=current_user.id).limit(50).all()
    org_ids = [m.org_id for m in memberships]
    orgs = db.query(Organisation).filter(Organisation.id.in_(org_ids)).all() if org_ids else []
    return [_fmt_org(o, db) for o in orgs]


@router.get("/{slug}")
def get_org(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = _get_org(slug, db)
    _get_membership(org, current_user, db)
    return _fmt_org(org, db)


@router.patch("/{slug}")
def update_org(
    slug: str,
    body: OrgUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = _get_org(slug, db)
    _require_admin(org, current_user, db)
    if body.name is not None:
        org.name = body.name
    if body.logo_url is not None:
        org.logo_url = body.logo_url
    db.commit()
    return _fmt_org(org, db)


@router.delete("/{slug}", status_code=204)
def delete_org(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = _get_org(slug, db)
    _require_owner(org, current_user)
    # Detach projects (don't cascade delete projects — they're independent)
    db.query(Project).filter_by(org_id=org.id).update({"org_id": None})
    db.delete(org)
    db.commit()


# ── Members ───────────────────────────────────────────────────────────────────

@router.get("/{slug}/members")
def list_members(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = _get_org(slug, db)
    _get_membership(org, current_user, db)
    members = (
        db.query(OrgMember, User)
        .join(User, OrgMember.user_id == User.id)
        .filter(OrgMember.org_id == org.id)
        .all()
    )
    return [
        {
            "user_id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": m.role,
            "joined_at": m.joined_at.isoformat(),
        }
        for m, u in members
    ]


@router.post("/{slug}/members", status_code=201)
def invite_member(
    slug: str,
    body: InviteMember,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = _get_org(slug, db)
    _require_admin(org, current_user, db)

    user = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if not user:
        raise HTTPException(404, "No user with that email address")

    existing = db.query(OrgMember).filter_by(org_id=org.id, user_id=user.id).first()
    if existing:
        raise HTTPException(400, "User is already a member")

    # Max 200 members per org
    count = db.query(OrgMember).filter_by(org_id=org.id).count()
    if count >= 200:
        raise HTTPException(400, "Organisation member limit (200) reached")

    db.add(OrgMember(org_id=org.id, user_id=user.id, role=body.role))
    db.commit()
    return {"message": f"{user.full_name} added to {org.name}", "role": body.role}


@router.patch("/{slug}/members/{user_id}")
def update_member_role(
    slug: str,
    user_id: int,
    body: UpdateRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = _get_org(slug, db)
    _require_admin(org, current_user, db)
    if user_id == org.owner_id:
        raise HTTPException(400, "Cannot change the owner's role")
    m = db.query(OrgMember).filter_by(org_id=org.id, user_id=user_id).first()
    if not m:
        raise HTTPException(404, "Member not found")
    m.role = body.role
    db.commit()
    return {"user_id": user_id, "role": m.role}


@router.delete("/{slug}/members/{user_id}", status_code=204)
def remove_member(
    slug: str,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = _get_org(slug, db)
    _require_admin(org, current_user, db)
    if user_id == org.owner_id:
        raise HTTPException(400, "Cannot remove the organisation owner")
    m = db.query(OrgMember).filter_by(org_id=org.id, user_id=user_id).first()
    if not m:
        raise HTTPException(404, "Member not found")
    db.delete(m)
    db.commit()


# ── Projects ──────────────────────────────────────────────────────────────────

@router.get("/{slug}/projects")
def list_org_projects(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = _get_org(slug, db)
    _get_membership(org, current_user, db)
    projects = db.query(Project).filter_by(org_id=org.id).limit(200).all()
    return [
        {"id": p.id, "name": p.name, "key": p.key, "description": p.description}
        for p in projects
    ]


@router.post("/{slug}/projects/{project_id}", status_code=200)
def attach_project(
    slug: str,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = _get_org(slug, db)
    _require_admin(org, current_user, db)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(403, "Only the project owner can attach it to an org")
    project.org_id = org.id
    db.commit()
    return {"message": f"Project '{project.name}' attached to '{org.name}'"}


@router.delete("/{slug}/projects/{project_id}", status_code=204)
def detach_project(
    slug: str,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = _get_org(slug, db)
    _require_admin(org, current_user, db)
    project = db.query(Project).filter(Project.id == project_id, Project.org_id == org.id).first()
    if not project:
        raise HTTPException(404, "Project not found in this organisation")
    project.org_id = None
    db.commit()


# ── Cross-project search ──────────────────────────────────────────────────────

@router.get("/{slug}/search")
def org_search(
    slug: str,
    q: str = Query(..., min_length=1, max_length=128),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search issues and projects across all projects within an org."""
    from app.models.issue import Issue
    org = _get_org(slug, db)
    _get_membership(org, current_user, db)

    term = f"%{q.strip()}%"
    org_project_ids = [
        p.id for p in db.query(Project).filter_by(org_id=org.id).limit(200).all()
    ]

    # Scope to projects the user can also access
    member_project_ids = {
        m.project_id for m in db.query(ProjectMember).filter_by(user_id=current_user.id).all()
    } | {p.id for p in db.query(Project).filter_by(owner_id=current_user.id).all()}

    accessible = [pid for pid in org_project_ids if pid in member_project_ids]

    issues = (
        db.query(Issue)
        .filter(
            Issue.project_id.in_(accessible),
            or_(Issue.title.ilike(term), Issue.key.ilike(term)),
        )
        .limit(30)
        .all()
    )

    projects = (
        db.query(Project)
        .filter(
            Project.id.in_(accessible),
            or_(Project.name.ilike(term), Project.key.ilike(term)),
        )
        .limit(10)
        .all()
    )

    return {
        "issues": [
            {"id": i.id, "key": i.key, "title": i.title, "project_id": i.project_id,
             "status": i.status.value, "type": i.type.value}
            for i in issues
        ],
        "projects": [
            {"id": p.id, "name": p.name, "key": p.key}
            for p in projects
        ],
    }
