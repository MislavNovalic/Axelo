from sqlalchemy.orm import Session
from datetime import date
from app.database import SessionLocal
from app.models.user import User
from app.models.project import Project, ProjectMember, MemberRole
from app.models.issue import Issue, IssueType, IssueStatus, IssuePriority
from app.models.sprint import Sprint, SprintStatus
from app.core.auth import hash_password
import app.models

USERS = [
    {"email": "alex@axelo.dev",  "full_name": "Alex Chen",    "password": "password123"},
    {"email": "blake@axelo.dev", "full_name": "Blake Rivera",  "password": "password123"},
    {"email": "casey@axelo.dev", "full_name": "Casey Morgan",  "password": "password123"},
]

# Spread due dates across current month (March 2026) for all 3 users
ISSUES = [
    # Sprint 1 — completed (alex 0, blake 1, casey 2)
    dict(title="Set up FastAPI project structure",    type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,    story_points=3,  sprint_idx=0, assignee_idx=0, due=date(2026, 3, 3)),
    dict(title="Configure PostgreSQL + SQLAlchemy",   type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,    story_points=2,  sprint_idx=0, assignee_idx=0, due=date(2026, 3, 4)),
    dict(title="Implement JWT authentication",        type=IssueType.story, status=IssueStatus.done,        priority=IssuePriority.high,    story_points=5,  sprint_idx=0, assignee_idx=1, due=date(2026, 3, 5)),
    dict(title="User registration & login endpoints", type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,    story_points=3,  sprint_idx=0, assignee_idx=0, due=date(2026, 3, 6)),
    dict(title="Password hashing with bcrypt",        type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.medium,  story_points=1,  sprint_idx=0, assignee_idx=2, due=date(2026, 3, 6)),
    # Sprint 2 — active
    dict(title="Build Kanban board drag-and-drop",    type=IssueType.story, status=IssueStatus.in_progress, priority=IssuePriority.high,    story_points=8,  sprint_idx=1, assignee_idx=1, due=date(2026, 3, 12)),
    dict(title="Auth token refresh logic",            type=IssueType.bug,   status=IssueStatus.in_progress, priority=IssuePriority.critical,story_points=3,  sprint_idx=1, assignee_idx=0, due=date(2026, 3, 13)),
    dict(title="Fix Postgres migration on fresh DB",  type=IssueType.bug,   status=IssueStatus.todo,        priority=IssuePriority.high,    story_points=2,  sprint_idx=1, assignee_idx=0, due=date(2026, 3, 14)),
    dict(title="Project invite via email",            type=IssueType.story, status=IssueStatus.in_review,   priority=IssuePriority.medium,  story_points=5,  sprint_idx=1, assignee_idx=2, due=date(2026, 3, 17)),
    dict(title="Sprint burndown chart component",     type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.medium,  story_points=5,  sprint_idx=1, assignee_idx=1, due=date(2026, 3, 18)),
    dict(title="Mobile responsive board layout",      type=IssueType.task,  status=IssueStatus.in_review,   priority=IssuePriority.low,     story_points=3,  sprint_idx=1, assignee_idx=2, due=date(2026, 3, 19)),
    dict(title="API rate limiting middleware",        type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.medium,  story_points=3,  sprint_idx=1, assignee_idx=0, due=date(2026, 3, 20)),
    dict(title="Write unit tests for auth module",    type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.high,    story_points=5,  sprint_idx=1, assignee_idx=1, due=date(2026, 3, 21)),
    dict(title="Refactor project membership logic",   type=IssueType.task,  status=IssueStatus.in_progress, priority=IssuePriority.medium,  story_points=3,  sprint_idx=1, assignee_idx=2, due=date(2026, 3, 24)),
    dict(title="Optimise SQL queries on board view",  type=IssueType.bug,   status=IssueStatus.todo,        priority=IssuePriority.high,    story_points=2,  sprint_idx=1, assignee_idx=0, due=date(2026, 3, 25)),
    dict(title="Add pagination to issues endpoint",   type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.low,     story_points=2,  sprint_idx=1, assignee_idx=1, due=date(2026, 3, 26)),
    dict(title="Integrate Sentry error tracking",     type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.low,     story_points=2,  sprint_idx=1, assignee_idx=2, due=date(2026, 3, 27)),
    # Backlog — no due date
    dict(title="Add file attachment support",         type=IssueType.story, status=IssueStatus.backlog,     priority=IssuePriority.medium,  story_points=8,  sprint_idx=None, assignee_idx=None, due=None),
    dict(title="GitHub PR integration",               type=IssueType.epic,  status=IssueStatus.backlog,     priority=IssuePriority.medium,  story_points=13, sprint_idx=None, assignee_idx=None, due=None),
    dict(title="Email notification system",           type=IssueType.story, status=IssueStatus.backlog,     priority=IssuePriority.low,     story_points=5,  sprint_idx=None, assignee_idx=None, due=None),
    dict(title="Dark / light theme toggle",           type=IssueType.task,  status=IssueStatus.backlog,     priority=IssuePriority.low,     story_points=2,  sprint_idx=None, assignee_idx=None, due=None),
]


def run(db: Session):
    if db.query(User).first():
        print("⏭  Seed: data already present, skipping.")
        return

    print("🌱 Seeding demo data...")

    users = []
    for u in USERS:
        print(f"   Creating user {u['email']} ...")
        user = User(email=u["email"], full_name=u["full_name"], hashed_password=hash_password(u["password"]))
        db.add(user)
        users.append(user)
    db.flush()

    project = Project(name="Axelo Core", key="AX", description="Backend API and core infrastructure.", owner_id=users[0].id)
    db.add(project)
    db.flush()

    roles = [MemberRole.owner, MemberRole.admin, MemberRole.member]
    for i, user in enumerate(users):
        db.add(ProjectMember(project_id=project.id, user_id=user.id, role=roles[i]))

    sprints = [
        Sprint(name="Sprint 1", goal="Foundation & auth",        status=SprintStatus.completed, project_id=project.id),
        Sprint(name="Sprint 2", goal="Kanban board & UX polish", status=SprintStatus.active,    project_id=project.id),
    ]
    for s in sprints:
        db.add(s)
    db.flush()

    for idx, data in enumerate(ISSUES):
        sprint_id   = sprints[data["sprint_idx"]].id  if data["sprint_idx"]   is not None else None
        assignee_id = users[data["assignee_idx"]].id  if data["assignee_idx"] is not None else None
        db.add(Issue(
            key=f"AX-{idx + 1}",
            title=data["title"],
            type=data["type"],
            status=data["status"],
            priority=data["priority"],
            story_points=data["story_points"],
            due_date=data["due"],
            sprint_id=sprint_id,
            assignee_id=assignee_id,
            reporter_id=users[0].id,
            project_id=project.id,
            order=idx,
        ))

    db.commit()
    print("✅ Seed complete! Login with:")
    for u in USERS:
        print(f"   {u['email']}  /  {u['password']}")


def seed():
    db = SessionLocal()
    try:
        run(db)
    except Exception as exc:
        db.rollback()
        print(f"❌ Seed failed: {exc}")
        raise
    finally:
        db.close()
