from sqlalchemy.orm import Session
from datetime import date
from app.database import SessionLocal
from app.models.user import User
from app.models.project import Project, ProjectMember, MemberRole
from app.models.issue import Issue, IssueType, IssueStatus, IssuePriority
from app.models.sprint import Sprint, SprintStatus
from app.core.auth import hash_password
import app.models

# ── Users ─────────────────────────────────────────────────────────────────────
USERS = [
    {"email": "alex@axelo.dev",   "full_name": "Alex Chen",      "password": "password123"},
    {"email": "blake@axelo.dev",  "full_name": "Blake Rivera",    "password": "password123"},
    {"email": "casey@axelo.dev",  "full_name": "Casey Morgan",    "password": "password123"},
    {"email": "dana@axelo.dev",   "full_name": "Dana Park",       "password": "password123"},
    {"email": "eli@axelo.dev",    "full_name": "Eli Thornton",    "password": "password123"},
]

# ── Project 1: Axelo Core (backend / infra) ───────────────────────────────────
ISSUES_AX = [
    # Sprint 1 — completed
    dict(title="Set up FastAPI project structure",     type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=3,  si=0, ai=0, due=date(2026, 3, 3),  desc="Scaffold the FastAPI app with proper folder layout, CORS, and lifespan hooks."),
    dict(title="Configure PostgreSQL + SQLAlchemy",    type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=2,  si=0, ai=0, due=date(2026, 3, 4),  desc="Create the database engine, SessionLocal, and base model. Add alembic config."),
    dict(title="Implement JWT authentication",         type=IssueType.story, status=IssueStatus.done,        priority=IssuePriority.high,     sp=5,  si=0, ai=1, due=date(2026, 3, 5),  desc="Issue short-lived access tokens on login, store user claims in payload."),
    dict(title="User registration & login endpoints",  type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=3,  si=0, ai=0, due=date(2026, 3, 6),  desc="POST /auth/register and POST /auth/login. Return token on success."),
    dict(title="Password hashing with bcrypt",         type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.medium,   sp=1,  si=0, ai=2, due=date(2026, 3, 6),  desc="Use passlib[bcrypt] to hash passwords at rest. Pin bcrypt==3.2.2."),
    dict(title="Project CRUD endpoints",               type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=3,  si=0, ai=1, due=date(2026, 3, 7),  desc="Create, read, update, delete projects. Enforce owner-only mutations."),
    dict(title="Issue model + migrations",             type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=2,  si=0, ai=3, due=date(2026, 3, 8),  desc="Define Issue table with type, status, priority, story_points, due_date columns."),
    # Sprint 2 — active
    dict(title="Build Kanban board drag-and-drop",     type=IssueType.story, status=IssueStatus.in_progress, priority=IssuePriority.high,     sp=8,  si=1, ai=1, due=date(2026, 3, 12), desc="Vue 3 drag-and-drop across status columns. Persist new status on drop."),
    dict(title="Auth token refresh logic",             type=IssueType.bug,   status=IssueStatus.in_progress, priority=IssuePriority.critical, sp=3,  si=1, ai=0, due=date(2026, 3, 13), desc="Access tokens expire silently. Add refresh endpoint and auto-retry on 401."),
    dict(title="Fix Postgres migration on fresh DB",   type=IssueType.bug,   status=IssueStatus.todo,        priority=IssuePriority.high,     sp=2,  si=1, ai=0, due=date(2026, 3, 14), desc="Running docker compose up on a clean volume throws a relation does not exist error."),
    dict(title="Project invite via email",             type=IssueType.story, status=IssueStatus.in_review,   priority=IssuePriority.medium,   sp=5,  si=1, ai=2, due=date(2026, 3, 17), desc="Send invite email when a member is added to a project. Include magic link."),
    dict(title="Sprint burndown chart component",      type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=5,  si=1, ai=1, due=date(2026, 3, 18), desc="Render a simple line chart showing ideal vs actual burndown per sprint."),
    dict(title="Mobile responsive board layout",       type=IssueType.task,  status=IssueStatus.in_review,   priority=IssuePriority.low,      sp=3,  si=1, ai=2, due=date(2026, 3, 19), desc="Board columns should stack on mobile. Cards should be touch-draggable."),
    dict(title="API rate limiting middleware",         type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=3,  si=1, ai=0, due=date(2026, 3, 20), desc="Add slowapi middleware. Limit /auth endpoints to 10 req/min per IP."),
    dict(title="Write unit tests for auth module",     type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.high,     sp=5,  si=1, ai=3, due=date(2026, 3, 21), desc="Cover register, login, invalid credentials, and token expiry scenarios."),
    dict(title="Refactor project membership logic",    type=IssueType.task,  status=IssueStatus.in_progress, priority=IssuePriority.medium,   sp=3,  si=1, ai=2, due=date(2026, 3, 24), desc="Extract role checks into a shared dependency. Remove duplicated guard code."),
    dict(title="Optimise SQL queries on board view",   type=IssueType.bug,   status=IssueStatus.todo,        priority=IssuePriority.high,     sp=2,  si=1, ai=0, due=date(2026, 3, 25), desc="N+1 query detected when loading issues with assignee and reporter. Add eager loading."),
    dict(title="Add pagination to issues endpoint",    type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.low,      sp=2,  si=1, ai=4, due=date(2026, 3, 26), desc="Support ?page=1&per_page=50 query params. Return total count in response headers."),
    dict(title="Integrate Sentry error tracking",      type=IssueType.task,  status=IssueStatus.in_review,   priority=IssuePriority.low,      sp=2,  si=1, ai=3, due=date(2026, 3, 27), desc="Add sentry-sdk to requirements. Capture unhandled exceptions with user context."),
    # Sprint 3 — planned
    dict(title="Webhook system for integrations",      type=IssueType.epic,  status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=13, si=2, ai=None, due=date(2026, 4, 3),  desc="Allow external services to subscribe to issue state changes via webhooks."),
    dict(title="Two-factor authentication (TOTP)",     type=IssueType.story, status=IssueStatus.todo,        priority=IssuePriority.high,     sp=8,  si=2, ai=0,    due=date(2026, 4, 7),  desc="Add optional 2FA using pyotp. Show QR code in settings. Require on login if enabled."),
    dict(title="Audit log for issue changes",          type=IssueType.story, status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=5,  si=2, ai=1,    due=date(2026, 4, 10), desc="Record every field change on an issue with timestamp and actor."),
    dict(title="Custom issue fields",                  type=IssueType.epic,  status=IssueStatus.todo,        priority=IssuePriority.low,      sp=13, si=2, ai=None, due=date(2026, 4, 14), desc="Allow project admins to define custom fields (text, number, select) on issues."),
    # Backlog
    dict(title="File attachment support",              type=IssueType.story, status=IssueStatus.backlog,     priority=IssuePriority.medium,   sp=8,  si=None, ai=None, due=None, desc="Upload images and files to issues. Store in S3-compatible storage."),
    dict(title="GitHub PR integration",                type=IssueType.epic,  status=IssueStatus.backlog,     priority=IssuePriority.medium,   sp=13, si=None, ai=None, due=None, desc="Link GitHub PRs to issues. Auto-transition to In Review when PR opened."),
    dict(title="Email notification system",            type=IssueType.story, status=IssueStatus.backlog,     priority=IssuePriority.low,      sp=5,  si=None, ai=None, due=None, desc="Send email when assigned, mentioned, or commented on an issue."),
    dict(title="Full-text issue search",               type=IssueType.task,  status=IssueStatus.backlog,     priority=IssuePriority.medium,   sp=5,  si=None, ai=None, due=None, desc="Global search across issue titles and descriptions. Support filters."),
]

# ── Project 2: Axelo Mobile (mobile app) ─────────────────────────────────────
ISSUES_MOB = [
    # Sprint 1 — completed
    dict(title="Bootstrap React Native project",          type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,    sp=2,  si=0, ai=3, due=date(2026, 3, 4),  desc="Initialise Expo project with TypeScript template. Set up ESLint and Prettier."),
    dict(title="Configure navigation stack",              type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,    sp=3,  si=0, ai=4, due=date(2026, 3, 5),  desc="Add React Navigation 6. Set up auth stack and main tab navigator."),
    dict(title="Login screen",                            type=IssueType.story, status=IssueStatus.done,        priority=IssuePriority.high,    sp=3,  si=0, ai=2, due=date(2026, 3, 6),  desc="Email + password login. Persist token in SecureStore."),
    dict(title="Splash screen and app icon",              type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.medium,  sp=1,  si=0, ai=3, due=date(2026, 3, 7),  desc="Design and export app icon at all required resolutions."),
    dict(title="Integrate Axelo REST API client",         type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,    sp=3,  si=0, ai=4, due=date(2026, 3, 8),  desc="Axios client with auth interceptor. Auto-refresh token on 401."),
    # Sprint 2 — active
    dict(title="Issues list screen",                      type=IssueType.story, status=IssueStatus.in_progress, priority=IssuePriority.high,    sp=5,  si=1, ai=2, due=date(2026, 3, 13), desc="Flat list of issues for the selected project. Swipe to change status."),
    dict(title="Issue detail screen",                     type=IssueType.story, status=IssueStatus.in_review,   priority=IssuePriority.high,    sp=5,  si=1, ai=3, due=date(2026, 3, 15), desc="Show full issue detail. Allow status and priority changes."),
    dict(title="Push notifications (FCM)",                type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.medium,  sp=5,  si=1, ai=4, due=date(2026, 3, 18), desc="Send push when assigned or commented on an issue. Use Expo Notifications."),
    dict(title="Offline mode with local cache",           type=IssueType.story, status=IssueStatus.todo,        priority=IssuePriority.medium,  sp=8,  si=1, ai=2, due=date(2026, 3, 20), desc="Cache issues in AsyncStorage. Show stale data with 'Offline' banner."),
    dict(title="Create issue from mobile",                type=IssueType.story, status=IssueStatus.in_progress, priority=IssuePriority.high,    sp=3,  si=1, ai=3, due=date(2026, 3, 21), desc="FAB button opens creation sheet. Support title, type, priority."),
    dict(title="Dark mode support",                       type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.low,     sp=2,  si=1, ai=4, due=date(2026, 3, 24), desc="Respect system colour scheme. Use themed StyleSheet."),
    dict(title="Crash reporter integration",              type=IssueType.bug,   status=IssueStatus.in_review,   priority=IssuePriority.high,    sp=2,  si=1, ai=3, due=date(2026, 3, 25), desc="App crashes on Android 12 when opening notification. Needs investigation."),
    # Sprint 3 — planned
    dict(title="Biometric login (FaceID / fingerprint)",  type=IssueType.story, status=IssueStatus.todo,        priority=IssuePriority.medium,  sp=5,  si=2, ai=2, due=date(2026, 4, 4),  desc="Use expo-local-authentication for biometric sign-in after first login."),
    dict(title="Kanban board view on mobile",             type=IssueType.epic,  status=IssueStatus.todo,        priority=IssuePriority.high,    sp=13, si=2, ai=4, due=date(2026, 4, 8),  desc="Horizontal scroll board view. Swipe cards between columns."),
    dict(title="Widget for home screen",                  type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.low,     sp=5,  si=2, ai=3, due=date(2026, 4, 11), desc="iOS 14+ widget showing issue count and overdue items."),
    # Backlog
    dict(title="Apple Watch companion app",               type=IssueType.epic,  status=IssueStatus.backlog,     priority=IssuePriority.low,     sp=20, si=None, ai=None, due=None, desc="Glanceable sprint progress on the wrist."),
    dict(title="Voice-to-issue creation",                 type=IssueType.story, status=IssueStatus.backlog,     priority=IssuePriority.low,     sp=8,  si=None, ai=None, due=None, desc="Use device microphone to transcribe and create issues hands-free."),
]

# ── Comments ──────────────────────────────────────────────────────────────────
# (issue_key_idx, author_idx, body)
COMMENTS_AX = [
    (7,  1, "Working on the column detection — HTML5 drag events are finicky on Safari. Will add a polyfill."),
    (7,  0, "Noted. Make sure to test Firefox too, they handle dragover differently."),
    (7,  2, "Can we also support touch-drag on iPad? That's a blocker for our mobile users."),
    (8,  0, "Root cause found: the axios interceptor is catching 401s from the login endpoint itself, causing an infinite loop. Fix incoming."),
    (8,  1, "Good catch. We should whitelist /auth/* routes from the refresh logic."),
    (10, 2, "Design is ready in Figma. Waiting for backend invite endpoint before I can wire it up."),
    (10, 1, "Backend is done — POST /api/projects/{id}/members. Let me know if the response schema needs changes."),
    (12, 0, "We could use express-rate-limit pattern but in FastAPI with slowapi. Already have a branch."),
    (14, 3, "I can pick this up. Should we use pytest-asyncio or just sync tests with TestClient?"),
    (14, 1, "Go with TestClient for now, it's simpler. We can migrate later."),
    (0,  1, "Looks good. Folder structure matches our agreed convention. ✅"),
    (2,  2, "Reviewed the JWT implementation — tokens are signed with HS256. Should we consider RS256 for future microservices?"),
    (2,  0, "Good point, but HS256 is fine for now. Added a note in the ADR."),
    (16, 4, "Found the N+1 — SQLAlchemy lazy-loads `assignee` and `reporter` on every issue. Adding `joinedload` in the query."),
    (17, 0, "Page size should be configurable via env var too, not just query param."),
]

COMMENTS_MOB = [
    (5,  2, "List is rendering but performance is poor on 100+ items. Switching to FlatList with keyExtractor."),
    (5,  3, "Also add pull-to-refresh — users expect that on mobile."),
    (6,  3, "Status picker needs haptic feedback on iOS. Using Haptics.impactAsync(LIGHT)."),
    (11, 3, "Reproduced the crash. It's a null deref in the notification payload parser when `data` key is missing."),
    (11, 4, "PR up with the fix. Added a null check and a test case."),
    (9,  2, "We should use react-query for the cache layer — it handles stale-while-revalidate out of the box."),
    (9,  4, "Agree. And it integrates nicely with the existing axios client."),
]


def run(db: Session):
    if db.query(User).first():
        print("⏭  Seed: data already present, skipping.")
        return

    print("🌱 Seeding demo data...")

    # Users
    users = []
    for u in USERS:
        print(f"   Creating user {u['email']} ...")
        user = User(email=u["email"], full_name=u["full_name"], hashed_password=hash_password(u["password"]), email_verified=True)
        db.add(user)
        users.append(user)
    db.flush()

    # ── Project 1 ─────────────────────────────────────────────────────────────
    p1 = Project(name="Axelo Core", key="AX", description="Backend API, authentication, and core infrastructure.", owner_id=users[0].id)
    db.add(p1)
    db.flush()

    p1_roles = [MemberRole.owner, MemberRole.admin, MemberRole.member, MemberRole.member, MemberRole.viewer]
    for i, user in enumerate(users):
        db.add(ProjectMember(project_id=p1.id, user_id=user.id, role=p1_roles[i]))

    p1_sprints = [
        Sprint(name="Sprint 1", goal="Foundation & auth",           status=SprintStatus.completed, project_id=p1.id),
        Sprint(name="Sprint 2", goal="Kanban board & UX polish",    status=SprintStatus.active,    project_id=p1.id),
        Sprint(name="Sprint 3", goal="Integrations & security",     status=SprintStatus.planned,   project_id=p1.id),
    ]
    for s in p1_sprints:
        db.add(s)
    db.flush()

    ax_issues = []
    for idx, data in enumerate(ISSUES_AX):
        sprint_id   = p1_sprints[data["si"]].id  if data["si"]   is not None else None
        assignee_id = users[data["ai"]].id         if data["ai"]   is not None else None
        issue = Issue(
            key=f"AX-{idx + 1}",
            title=data["title"],
            description=data.get("desc"),
            type=data["type"],
            status=data["status"],
            priority=data["priority"],
            story_points=data["sp"],
            due_date=data["due"],
            sprint_id=sprint_id,
            assignee_id=assignee_id,
            reporter_id=users[idx % 3].id,
            project_id=p1.id,
            order=idx,
        )
        db.add(issue)
        ax_issues.append(issue)
    db.flush()

    # Comments for project 1
    from app.models.issue import Comment as CommentModel
    for (issue_idx, author_idx, body) in COMMENTS_AX:
        db.add(CommentModel(body=body, issue_id=ax_issues[issue_idx].id, author_id=users[author_idx].id))

    # ── Project 2 ─────────────────────────────────────────────────────────────
    p2 = Project(name="Axelo Mobile", key="MOB", description="React Native mobile app for iOS and Android.", owner_id=users[2].id)
    db.add(p2)
    db.flush()

    p2_roles = [MemberRole.member, MemberRole.viewer, MemberRole.owner, MemberRole.admin, MemberRole.member]
    for i, user in enumerate(users):
        db.add(ProjectMember(project_id=p2.id, user_id=user.id, role=p2_roles[i]))

    p2_sprints = [
        Sprint(name="Sprint 1", goal="App bootstrapping & auth",     status=SprintStatus.completed, project_id=p2.id),
        Sprint(name="Sprint 2", goal="Core screens & notifications",  status=SprintStatus.active,    project_id=p2.id),
        Sprint(name="Sprint 3", goal="Advanced features",             status=SprintStatus.planned,   project_id=p2.id),
    ]
    for s in p2_sprints:
        db.add(s)
    db.flush()

    mob_issues = []
    for idx, data in enumerate(ISSUES_MOB):
        sprint_id   = p2_sprints[data["si"]].id  if data["si"]   is not None else None
        assignee_id = users[data["ai"]].id         if data["ai"]   is not None else None
        issue = Issue(
            key=f"MOB-{idx + 1}",
            title=data["title"],
            description=data.get("desc"),
            type=data["type"],
            status=data["status"],
            priority=data["priority"],
            story_points=data["sp"],
            due_date=data["due"],
            sprint_id=sprint_id,
            assignee_id=assignee_id,
            reporter_id=users[(idx + 2) % 5].id,
            project_id=p2.id,
            order=idx,
        )
        db.add(issue)
        mob_issues.append(issue)
    db.flush()

    for (issue_idx, author_idx, body) in COMMENTS_MOB:
        db.add(CommentModel(body=body, issue_id=mob_issues[issue_idx].id, author_id=users[author_idx].id))

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
