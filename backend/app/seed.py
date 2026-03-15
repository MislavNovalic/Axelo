from sqlalchemy.orm import Session
from datetime import date
from app.database import SessionLocal
from app.models.user import User
from app.models.project import Project, ProjectMember, MemberRole
from app.models.issue import Issue, IssueType, IssueStatus, IssuePriority, Comment as CommentModel
from app.models.sprint import Sprint, SprintStatus
from app.core.auth import hash_password
import app.models

# ── Users ─────────────────────────────────────────────────────────────────────
USERS = [
    # Original 5
    {"email": "alex@axelo.dev",    "full_name": "Alex Chen",          "password": "password123"},
    {"email": "blake@axelo.dev",   "full_name": "Blake Rivera",        "password": "password123"},
    {"email": "casey@axelo.dev",   "full_name": "Casey Morgan",        "password": "password123"},
    {"email": "dana@axelo.dev",    "full_name": "Dana Park",           "password": "password123"},
    {"email": "eli@axelo.dev",     "full_name": "Eli Thornton",        "password": "password123"},
    # 20 new users
    {"email": "fiona@axelo.dev",   "full_name": "Fiona Walsh",         "password": "password123"},
    {"email": "george@axelo.dev",  "full_name": "George Okafor",       "password": "password123"},
    {"email": "hana@axelo.dev",    "full_name": "Hana Suzuki",         "password": "password123"},
    {"email": "ivan@axelo.dev",    "full_name": "Ivan Petrov",         "password": "password123"},
    {"email": "julia@axelo.dev",   "full_name": "Julia Santos",        "password": "password123"},
    {"email": "kai@axelo.dev",     "full_name": "Kai Nakamura",        "password": "password123"},
    {"email": "lena@axelo.dev",    "full_name": "Lena Müller",         "password": "password123"},
    {"email": "marco@axelo.dev",   "full_name": "Marco Rossi",         "password": "password123"},
    {"email": "nina@axelo.dev",    "full_name": "Nina Johansson",      "password": "password123"},
    {"email": "omar@axelo.dev",    "full_name": "Omar Al-Farsi",       "password": "password123"},
    {"email": "priya@axelo.dev",   "full_name": "Priya Sharma",        "password": "password123"},
    {"email": "quinn@axelo.dev",   "full_name": "Quinn Bradley",       "password": "password123"},
    {"email": "rosa@axelo.dev",    "full_name": "Rosa Martinez",       "password": "password123"},
    {"email": "sam@axelo.dev",     "full_name": "Sam Osei",            "password": "password123"},
    {"email": "tara@axelo.dev",    "full_name": "Tara Nguyen",         "password": "password123"},
    {"email": "umar@axelo.dev",    "full_name": "Umar Hassan",         "password": "password123"},
    {"email": "vera@axelo.dev",    "full_name": "Vera Kozlov",         "password": "password123"},
    {"email": "will@axelo.dev",    "full_name": "Will Thompson",       "password": "password123"},
    {"email": "xin@axelo.dev",     "full_name": "Xin Li",              "password": "password123"},
    {"email": "yuki@axelo.dev",    "full_name": "Yuki Tanaka",         "password": "password123"},
    {"email": "zara@axelo.dev",    "full_name": "Zara Ahmed",          "password": "password123"},
]

# ── Project 1: Axelo Core ─────────────────────────────────────────────────────
ISSUES_AX = [
    dict(title="Set up FastAPI project structure",     type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=3,  si=0, ai=0,  due=date(2026, 3, 3),  desc="Scaffold the FastAPI app with proper folder layout, CORS, and lifespan hooks."),
    dict(title="Configure PostgreSQL + SQLAlchemy",    type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=2,  si=0, ai=0,  due=date(2026, 3, 4),  desc="Create the database engine, SessionLocal, and base model. Add alembic config."),
    dict(title="Implement JWT authentication",         type=IssueType.story, status=IssueStatus.done,        priority=IssuePriority.high,     sp=5,  si=0, ai=1,  due=date(2026, 3, 5),  desc="Issue short-lived access tokens on login, store user claims in payload."),
    dict(title="User registration & login endpoints",  type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=3,  si=0, ai=0,  due=date(2026, 3, 6),  desc="POST /auth/register and POST /auth/login. Return token on success."),
    dict(title="Password hashing with bcrypt",         type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.medium,   sp=1,  si=0, ai=2,  due=date(2026, 3, 6),  desc="Use passlib[bcrypt] to hash passwords at rest. Pin bcrypt==3.2.2."),
    dict(title="Project CRUD endpoints",               type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=3,  si=0, ai=1,  due=date(2026, 3, 7),  desc="Create, read, update, delete projects. Enforce owner-only mutations."),
    dict(title="Issue model + migrations",             type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=2,  si=0, ai=3,  due=date(2026, 3, 8),  desc="Define Issue table with type, status, priority, story_points, due_date columns."),
    dict(title="Build Kanban board drag-and-drop",     type=IssueType.story, status=IssueStatus.in_progress, priority=IssuePriority.high,     sp=8,  si=1, ai=1,  due=date(2026, 3, 12), desc="Vue 3 drag-and-drop across status columns. Persist new status on drop."),
    dict(title="Auth token refresh logic",             type=IssueType.bug,   status=IssueStatus.in_progress, priority=IssuePriority.critical, sp=3,  si=1, ai=0,  due=date(2026, 3, 13), desc="Access tokens expire silently. Add refresh endpoint and auto-retry on 401."),
    dict(title="Fix Postgres migration on fresh DB",   type=IssueType.bug,   status=IssueStatus.todo,        priority=IssuePriority.high,     sp=2,  si=1, ai=0,  due=date(2026, 3, 14), desc="Running docker compose up on a clean volume throws a relation does not exist error."),
    dict(title="Project invite via email",             type=IssueType.story, status=IssueStatus.in_review,   priority=IssuePriority.medium,   sp=5,  si=1, ai=2,  due=date(2026, 3, 17), desc="Send invite email when a member is added to a project. Include magic link."),
    dict(title="Sprint burndown chart component",      type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=5,  si=1, ai=1,  due=date(2026, 3, 18), desc="Render a simple line chart showing ideal vs actual burndown per sprint."),
    dict(title="Mobile responsive board layout",       type=IssueType.task,  status=IssueStatus.in_review,   priority=IssuePriority.low,      sp=3,  si=1, ai=2,  due=date(2026, 3, 19), desc="Board columns should stack on mobile. Cards should be touch-draggable."),
    dict(title="API rate limiting middleware",         type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=3,  si=1, ai=0,  due=date(2026, 3, 20), desc="Add slowapi middleware. Limit /auth endpoints to 10 req/min per IP."),
    dict(title="Write unit tests for auth module",     type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.high,     sp=5,  si=1, ai=3,  due=date(2026, 3, 21), desc="Cover register, login, invalid credentials, and token expiry scenarios."),
    dict(title="Refactor project membership logic",    type=IssueType.task,  status=IssueStatus.in_progress, priority=IssuePriority.medium,   sp=3,  si=1, ai=2,  due=date(2026, 3, 24), desc="Extract role checks into a shared dependency. Remove duplicated guard code."),
    dict(title="Optimise SQL queries on board view",   type=IssueType.bug,   status=IssueStatus.todo,        priority=IssuePriority.high,     sp=2,  si=1, ai=0,  due=date(2026, 3, 25), desc="N+1 query detected when loading issues with assignee and reporter. Add eager loading."),
    dict(title="Add pagination to issues endpoint",    type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.low,      sp=2,  si=1, ai=4,  due=date(2026, 3, 26), desc="Support ?page=1&per_page=50 query params. Return total count in response headers."),
    dict(title="Integrate Sentry error tracking",      type=IssueType.task,  status=IssueStatus.in_review,   priority=IssuePriority.low,      sp=2,  si=1, ai=3,  due=date(2026, 3, 27), desc="Add sentry-sdk to requirements. Capture unhandled exceptions with user context."),
    dict(title="Webhook system for integrations",      type=IssueType.epic,  status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=13, si=2, ai=None, due=date(2026, 4, 3),  desc="Allow external services to subscribe to issue state changes via webhooks."),
    dict(title="Two-factor authentication (TOTP)",     type=IssueType.story, status=IssueStatus.todo,        priority=IssuePriority.high,     sp=8,  si=2, ai=0,   due=date(2026, 4, 7),  desc="Add optional 2FA using pyotp. Show QR code in settings. Require on login if enabled."),
    dict(title="Audit log for issue changes",          type=IssueType.story, status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=5,  si=2, ai=1,   due=date(2026, 4, 10), desc="Record every field change on an issue with timestamp and actor."),
    dict(title="Custom issue fields",                  type=IssueType.epic,  status=IssueStatus.todo,        priority=IssuePriority.low,      sp=13, si=2, ai=None, due=date(2026, 4, 14), desc="Allow project admins to define custom fields (text, number, select) on issues."),
    dict(title="File attachment support",              type=IssueType.story, status=IssueStatus.backlog,     priority=IssuePriority.medium,   sp=8,  si=None, ai=None, due=None, desc="Upload images and files to issues. Store in S3-compatible storage."),
    dict(title="GitHub PR integration",                type=IssueType.epic,  status=IssueStatus.backlog,     priority=IssuePriority.medium,   sp=13, si=None, ai=None, due=None, desc="Link GitHub PRs to issues. Auto-transition to In Review when PR opened."),
    dict(title="Email notification system",            type=IssueType.story, status=IssueStatus.backlog,     priority=IssuePriority.low,      sp=5,  si=None, ai=None, due=None, desc="Send email when assigned, mentioned, or commented on an issue."),
    dict(title="Full-text issue search",               type=IssueType.task,  status=IssueStatus.backlog,     priority=IssuePriority.medium,   sp=5,  si=None, ai=None, due=None, desc="Global search across issue titles and descriptions. Support filters."),
]

# ── Project 2: Axelo Mobile ───────────────────────────────────────────────────
ISSUES_MOB = [
    dict(title="Bootstrap React Native project",          type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,    sp=2,  si=0, ai=3,  due=date(2026, 3, 4),  desc="Initialise Expo project with TypeScript template. Set up ESLint and Prettier."),
    dict(title="Configure navigation stack",              type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,    sp=3,  si=0, ai=4,  due=date(2026, 3, 5),  desc="Add React Navigation 6. Set up auth stack and main tab navigator."),
    dict(title="Login screen",                            type=IssueType.story, status=IssueStatus.done,        priority=IssuePriority.high,    sp=3,  si=0, ai=2,  due=date(2026, 3, 6),  desc="Email + password login. Persist token in SecureStore."),
    dict(title="Splash screen and app icon",              type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.medium,  sp=1,  si=0, ai=3,  due=date(2026, 3, 7),  desc="Design and export app icon at all required resolutions."),
    dict(title="Integrate Axelo REST API client",         type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,    sp=3,  si=0, ai=4,  due=date(2026, 3, 8),  desc="Axios client with auth interceptor. Auto-refresh token on 401."),
    dict(title="Issues list screen",                      type=IssueType.story, status=IssueStatus.in_progress, priority=IssuePriority.high,    sp=5,  si=1, ai=2,  due=date(2026, 3, 13), desc="Flat list of issues for the selected project. Swipe to change status."),
    dict(title="Issue detail screen",                     type=IssueType.story, status=IssueStatus.in_review,   priority=IssuePriority.high,    sp=5,  si=1, ai=3,  due=date(2026, 3, 15), desc="Show full issue detail. Allow status and priority changes."),
    dict(title="Push notifications (FCM)",                type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.medium,  sp=5,  si=1, ai=4,  due=date(2026, 3, 18), desc="Send push when assigned or commented on an issue. Use Expo Notifications."),
    dict(title="Offline mode with local cache",           type=IssueType.story, status=IssueStatus.todo,        priority=IssuePriority.medium,  sp=8,  si=1, ai=2,  due=date(2026, 3, 20), desc="Cache issues in AsyncStorage. Show stale data with 'Offline' banner."),
    dict(title="Create issue from mobile",                type=IssueType.story, status=IssueStatus.in_progress, priority=IssuePriority.high,    sp=3,  si=1, ai=3,  due=date(2026, 3, 21), desc="FAB button opens creation sheet. Support title, type, priority."),
    dict(title="Dark mode support",                       type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.low,     sp=2,  si=1, ai=4,  due=date(2026, 3, 24), desc="Respect system colour scheme. Use themed StyleSheet."),
    dict(title="Crash reporter integration",              type=IssueType.bug,   status=IssueStatus.in_review,   priority=IssuePriority.high,    sp=2,  si=1, ai=3,  due=date(2026, 3, 25), desc="App crashes on Android 12 when opening notification. Needs investigation."),
    dict(title="Biometric login (FaceID / fingerprint)",  type=IssueType.story, status=IssueStatus.todo,        priority=IssuePriority.medium,  sp=5,  si=2, ai=2,  due=date(2026, 4, 4),  desc="Use expo-local-authentication for biometric sign-in after first login."),
    dict(title="Kanban board view on mobile",             type=IssueType.epic,  status=IssueStatus.todo,        priority=IssuePriority.high,    sp=13, si=2, ai=4,  due=date(2026, 4, 8),  desc="Horizontal scroll board view. Swipe cards between columns."),
    dict(title="Widget for home screen",                  type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.low,     sp=5,  si=2, ai=3,  due=date(2026, 4, 11), desc="iOS 14+ widget showing issue count and overdue items."),
    dict(title="Apple Watch companion app",               type=IssueType.epic,  status=IssueStatus.backlog,     priority=IssuePriority.low,     sp=20, si=None, ai=None, due=None, desc="Glanceable sprint progress on the wrist."),
    dict(title="Voice-to-issue creation",                 type=IssueType.story, status=IssueStatus.backlog,     priority=IssuePriority.low,     sp=8,  si=None, ai=None, due=None, desc="Use device microphone to transcribe and create issues hands-free."),
]

# ── Project 3: DevOps & Infrastructure ───────────────────────────────────────
ISSUES_DEV = [
    dict(title="Set up GitHub Actions CI pipeline",        type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=3,  si=0, ai=5,  due=date(2026, 3, 2),  desc="Run pytest and eslint on every PR. Block merges on failure."),
    dict(title="Dockerise backend service",                type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=2,  si=0, ai=6,  due=date(2026, 3, 3),  desc="Multi-stage Dockerfile. Non-root user. Health check endpoint."),
    dict(title="Dockerise frontend (Nginx)",               type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=2,  si=0, ai=5,  due=date(2026, 3, 4),  desc="Build Vue app and serve with Nginx. Inject API base URL at runtime."),
    dict(title="Docker Compose local dev stack",           type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=2,  si=0, ai=6,  due=date(2026, 3, 5),  desc="One-command local setup: postgres, backend, frontend, redis."),
    dict(title="Kubernetes cluster setup (EKS)",           type=IssueType.epic,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=8,  si=0, ai=5,  due=date(2026, 3, 8),  desc="Provision EKS cluster with Terraform. Configure node groups and RBAC."),
    dict(title="Helm chart for Axelo services",            type=IssueType.task,  status=IssueStatus.in_progress, priority=IssuePriority.high,     sp=5,  si=1, ai=6,  due=date(2026, 3, 14), desc="Write Helm chart covering backend, frontend, ingress, and secrets."),
    dict(title="Set up Prometheus + Grafana monitoring",   type=IssueType.story, status=IssueStatus.in_progress, priority=IssuePriority.medium,   sp=5,  si=1, ai=5,  due=date(2026, 3, 17), desc="Scrape FastAPI /metrics endpoint. Build dashboard for request rate and latency."),
    dict(title="Centralised log aggregation (Loki)",       type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=3,  si=1, ai=6,  due=date(2026, 3, 19), desc="Ship container logs to Grafana Loki. Create log-based alerting rules."),
    dict(title="Automated DB backups to S3",               type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.high,     sp=3,  si=1, ai=5,  due=date(2026, 3, 20), desc="Nightly pg_dump, encrypt, upload to S3. Alert on failure."),
    dict(title="Zero-downtime rolling deployments",        type=IssueType.story, status=IssueStatus.in_review,   priority=IssuePriority.high,     sp=5,  si=1, ai=6,  due=date(2026, 3, 21), desc="Configure readiness/liveness probes. Use RollingUpdate strategy in Kubernetes."),
    dict(title="SSL certificate automation (cert-manager)",type=IssueType.task,  status=IssueStatus.in_review,   priority=IssuePriority.medium,   sp=2,  si=1, ai=5,  due=date(2026, 3, 22), desc="Let's Encrypt via cert-manager. Auto-renew before expiry."),
    dict(title="Autoscaling policy for backend pods",      type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=3,  si=2, ai=6,  due=date(2026, 4, 2),  desc="HPA based on CPU > 70%. Min 2 replicas, max 10."),
    dict(title="Disaster recovery runbook",                type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.high,     sp=3,  si=2, ai=5,  due=date(2026, 4, 5),  desc="Document RTO/RPO targets. Test restore from S3 backup in staging."),
    dict(title="Secret management with Vault",             type=IssueType.epic,  status=IssueStatus.todo,        priority=IssuePriority.high,     sp=8,  si=2, ai=6,  due=date(2026, 4, 9),  desc="Migrate hardcoded secrets to HashiCorp Vault. Integrate with K8s service accounts."),
    dict(title="Multi-region failover setup",              type=IssueType.epic,  status=IssueStatus.backlog,     priority=IssuePriority.medium,   sp=13, si=None, ai=None, due=None, desc="Active-passive setup across us-east-1 and eu-west-1."),
    dict(title="Load testing with k6",                     type=IssueType.task,  status=IssueStatus.backlog,     priority=IssuePriority.medium,   sp=5,  si=None, ai=None, due=None, desc="Simulate 500 concurrent users. Identify bottlenecks before production launch."),
    dict(title="CDN integration for static assets",        type=IssueType.task,  status=IssueStatus.backlog,     priority=IssuePriority.low,      sp=3,  si=None, ai=None, due=None, desc="Put CloudFront in front of frontend S3 bucket. Enable compression and caching."),
]

# ── Project 4: Marketing Website ─────────────────────────────────────────────
ISSUES_WEB = [
    dict(title="Design system and brand tokens",           type=IssueType.epic,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=8,  si=0, ai=7,  due=date(2026, 3, 5),  desc="Define color palette, typography scale, spacing tokens. Export to Figma and CSS."),
    dict(title="Hero section with animated demo",          type=IssueType.story, status=IssueStatus.done,        priority=IssuePriority.high,     sp=5,  si=0, ai=8,  due=date(2026, 3, 7),  desc="Animated product screenshot. CTA buttons to signup and demo booking."),
    dict(title="Features comparison table",                type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.medium,   sp=3,  si=0, ai=7,  due=date(2026, 3, 9),  desc="Free vs Pro vs Enterprise tier comparison. Highlight recommended plan."),
    dict(title="Pricing page",                             type=IssueType.story, status=IssueStatus.done,        priority=IssuePriority.high,     sp=5,  si=0, ai=8,  due=date(2026, 3, 10), desc="Monthly/annual toggle. FAQ accordion. Stripe checkout button."),
    dict(title="Blog with MDX support",                    type=IssueType.story, status=IssueStatus.in_progress, priority=IssuePriority.medium,   sp=5,  si=1, ai=7,  due=date(2026, 3, 16), desc="Next.js MDX blog. Syntax highlighting. Author bio. RSS feed."),
    dict(title="SEO meta tags and Open Graph",             type=IssueType.task,  status=IssueStatus.in_progress, priority=IssuePriority.high,     sp=2,  si=1, ai=8,  due=date(2026, 3, 17), desc="Per-page meta title, description, og:image. Sitemap.xml generation."),
    dict(title="Customer testimonials section",            type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=3,  si=1, ai=7,  due=date(2026, 3, 19), desc="Rotating testimonials with avatar, name, company. Source from CMS."),
    dict(title="Integration logos marquee",                type=IssueType.task,  status=IssueStatus.in_review,   priority=IssuePriority.low,      sp=2,  si=1, ai=8,  due=date(2026, 3, 20), desc="Scrolling strip of integration partner logos. Pause on hover."),
    dict(title="Cookie consent banner (GDPR)",             type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.high,     sp=3,  si=1, ai=7,  due=date(2026, 3, 22), desc="Opt-in banner for analytics. Persist choice in localStorage. Block GA until accepted."),
    dict(title="Contact and demo-request form",            type=IssueType.story, status=IssueStatus.in_review,   priority=IssuePriority.medium,   sp=3,  si=1, ai=8,  due=date(2026, 3, 24), desc="Zod-validated form. Send to HubSpot CRM. Confirmation email via SendGrid."),
    dict(title="Performance optimisation (Core Web Vitals)",type=IssueType.task, status=IssueStatus.todo,        priority=IssuePriority.high,     sp=5,  si=2, ai=7,  due=date(2026, 4, 3),  desc="Target LCP < 2.5s, CLS < 0.1. Optimise images with next/image. Lazy-load components."),
    dict(title="Changelog page",                           type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.low,      sp=2,  si=2, ai=8,  due=date(2026, 4, 7),  desc="Auto-generated from GitHub releases. Group by date. Show diff link."),
    dict(title="Internationalisation (i18n)",              type=IssueType.epic,  status=IssueStatus.backlog,     priority=IssuePriority.medium,   sp=13, si=None, ai=None, due=None, desc="Support EN, DE, FR, ES. next-intl library. Language switcher in navbar."),
    dict(title="A/B test hero CTA copy",                   type=IssueType.task,  status=IssueStatus.backlog,     priority=IssuePriority.low,      sp=3,  si=None, ai=None, due=None, desc="Test 'Start free trial' vs 'Get started'. Track conversions via Posthog."),
    dict(title="Affiliate / referral landing pages",       type=IssueType.story, status=IssueStatus.backlog,     priority=IssuePriority.low,      sp=5,  si=None, ai=None, due=None, desc="Parameterised landing pages for affiliate partners. Track UTM source."),
]

# ── Project 5: Data Analytics Platform ───────────────────────────────────────
ISSUES_DATA = [
    dict(title="Data warehouse setup (Redshift)",          type=IssueType.epic,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=8,  si=0, ai=9,  due=date(2026, 3, 6),  desc="Provision Redshift cluster. Define schema for events, users, projects tables."),
    dict(title="ETL pipeline: app events → warehouse",     type=IssueType.story, status=IssueStatus.done,        priority=IssuePriority.high,     sp=8,  si=0, ai=10, due=date(2026, 3, 9),  desc="Kafka consumer writes events to S3. Airflow DAG loads into Redshift nightly."),
    dict(title="User activity event schema",               type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=3,  si=0, ai=9,  due=date(2026, 3, 10), desc="Define event taxonomy: page_view, issue_created, sprint_started, etc."),
    dict(title="Retention cohort analysis",                type=IssueType.story, status=IssueStatus.done,        priority=IssuePriority.medium,   sp=5,  si=0, ai=10, due=date(2026, 3, 12), desc="Weekly cohort retention table. Visualise in Metabase."),
    dict(title="Real-time dashboard with Kafka Streams",   type=IssueType.epic,  status=IssueStatus.in_progress, priority=IssuePriority.high,     sp=13, si=1, ai=9,  due=date(2026, 3, 18), desc="Live metrics: active users, issues created today, sprint velocity."),
    dict(title="Predictive sprint velocity model",         type=IssueType.story, status=IssueStatus.in_progress, priority=IssuePriority.medium,   sp=8,  si=1, ai=10, due=date(2026, 3, 20), desc="Linear regression on past sprint data. Expose as /ai/sprint-velocity endpoint."),
    dict(title="Data quality checks (Great Expectations)", type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=5,  si=1, ai=9,  due=date(2026, 3, 22), desc="Validate null rates, schema drift, and referential integrity after each ETL run."),
    dict(title="Usage anomaly detection",                  type=IssueType.story, status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=8,  si=1, ai=10, due=date(2026, 3, 25), desc="Flag sudden drops in DAU or issue creation. Alert the ops team via Slack."),
    dict(title="Self-serve analytics portal",              type=IssueType.epic,  status=IssueStatus.in_review,   priority=IssuePriority.high,     sp=13, si=1, ai=9,  due=date(2026, 3, 27), desc="Drag-and-drop chart builder. Export to CSV/PDF. Role-based access."),
    dict(title="Feature flag analytics integration",       type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.low,      sp=3,  si=2, ai=10, due=date(2026, 4, 4),  desc="Track metrics split by feature flag variant. Measure impact of experiments."),
    dict(title="ML model for issue priority suggestion",   type=IssueType.epic,  status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=13, si=2, ai=9,  due=date(2026, 4, 10), desc="Train classifier on historical issues. Surface priority suggestion in the UI."),
    dict(title="Cross-project benchmark reports",          type=IssueType.story, status=IssueStatus.backlog,     priority=IssuePriority.low,      sp=5,  si=None, ai=None, due=None, desc="Compare cycle time and velocity across projects in the same org."),
    dict(title="GDPR data deletion pipeline",              type=IssueType.task,  status=IssueStatus.backlog,     priority=IssuePriority.high,     sp=5,  si=None, ai=None, due=None, desc="On account deletion, purge user data from warehouse within 30 days."),
    dict(title="Automated weekly digest emails",           type=IssueType.story, status=IssueStatus.backlog,     priority=IssuePriority.medium,   sp=5,  si=None, ai=None, due=None, desc="Send personalised sprint summary every Monday. Include velocity chart."),
]

# ── Project 6: Customer Support Portal ───────────────────────────────────────
ISSUES_SUP = [
    dict(title="Helpdesk ticket model and API",            type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=3,  si=0, ai=11, due=date(2026, 3, 4),  desc="Ticket schema: subject, body, status, priority, assignee, requester."),
    dict(title="Email-to-ticket ingest (Postmark)",        type=IssueType.story, status=IssueStatus.done,        priority=IssuePriority.high,     sp=5,  si=0, ai=12, due=date(2026, 3, 7),  desc="Postmark inbound webhook. Parse sender, subject, body. Create ticket automatically."),
    dict(title="Agent inbox view",                         type=IssueType.story, status=IssueStatus.done,        priority=IssuePriority.high,     sp=5,  si=0, ai=11, due=date(2026, 3, 9),  desc="Filterable list of open tickets. Quick reply editor. Assign to team member."),
    dict(title="Knowledge base article editor",            type=IssueType.story, status=IssueStatus.done,        priority=IssuePriority.medium,   sp=5,  si=0, ai=12, due=date(2026, 3, 11), desc="Rich text editor. Category tags. Publish / draft state. Full-text search."),
    dict(title="Customer-facing help centre",              type=IssueType.story, status=IssueStatus.in_progress, priority=IssuePriority.high,     sp=8,  si=1, ai=11, due=date(2026, 3, 16), desc="Public portal. Search articles. Submit new ticket. View ticket history."),
    dict(title="SLA tracking and breach alerts",           type=IssueType.story, status=IssueStatus.in_progress, priority=IssuePriority.high,     sp=5,  si=1, ai=12, due=date(2026, 3, 18), desc="Define SLA tiers per plan. Alert agent 1 hour before breach."),
    dict(title="Canned responses library",                 type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=3,  si=1, ai=11, due=date(2026, 3, 20), desc="Pre-saved reply templates. Insert with / shortcut in reply editor."),
    dict(title="CSAT survey after ticket close",           type=IssueType.task,  status=IssueStatus.in_review,   priority=IssuePriority.medium,   sp=3,  si=1, ai=12, due=date(2026, 3, 21), desc="Auto-send 1–5 star survey 2 hours after resolution. Log to analytics."),
    dict(title="Ticket auto-routing rules",                type=IssueType.story, status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=5,  si=1, ai=11, due=date(2026, 3, 24), desc="Route tickets by keyword or tag to the right team. Configurable in admin panel."),
    dict(title="Live chat widget",                         type=IssueType.epic,  status=IssueStatus.todo,        priority=IssuePriority.high,     sp=13, si=2, ai=12, due=date(2026, 4, 5),  desc="WebSocket-based live chat. Agent presence indicator. Handoff to ticket if offline."),
    dict(title="AI-powered reply suggestions",             type=IssueType.epic,  status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=13, si=2, ai=11, due=date(2026, 4, 10), desc="GPT-4o suggests reply based on ticket context and KB articles."),
    dict(title="Multi-brand support",                      type=IssueType.epic,  status=IssueStatus.backlog,     priority=IssuePriority.medium,   sp=13, si=None, ai=None, due=None, desc="Different inbox/portal per brand under one account. Separate SLAs."),
    dict(title="Zapier / Make integration",                type=IssueType.story, status=IssueStatus.backlog,     priority=IssuePriority.low,      sp=5,  si=None, ai=None, due=None, desc="Trigger automations when ticket created or resolved."),
    dict(title="Voice call integration (Twilio)",          type=IssueType.epic,  status=IssueStatus.backlog,     priority=IssuePriority.low,      sp=13, si=None, ai=None, due=None, desc="Click-to-call from ticket. Auto-create transcript as ticket note."),
]

# ── Project 7: E-Commerce Integration ────────────────────────────────────────
ISSUES_ECOM = [
    dict(title="Stripe payment intent API",                type=IssueType.story, status=IssueStatus.done,        priority=IssuePriority.high,     sp=5,  si=0, ai=13, due=date(2026, 3, 5),  desc="Create payment intent on checkout start. Handle 3DS confirmation flow."),
    dict(title="Product catalogue API",                    type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=3,  si=0, ai=14, due=date(2026, 3, 6),  desc="CRUD for products, variants, and inventory. Slug-based URLs."),
    dict(title="Shopping cart (Redis session)",            type=IssueType.story, status=IssueStatus.done,        priority=IssuePriority.high,     sp=5,  si=0, ai=13, due=date(2026, 3, 8),  desc="Persist cart in Redis with TTL. Merge guest cart on login."),
    dict(title="Order management system",                  type=IssueType.story, status=IssueStatus.done,        priority=IssuePriority.high,     sp=8,  si=0, ai=14, due=date(2026, 3, 11), desc="Order lifecycle: pending → paid → fulfilled → shipped → delivered."),
    dict(title="Webhook handling for Stripe events",       type=IssueType.task,  status=IssueStatus.done,        priority=IssuePriority.high,     sp=3,  si=0, ai=13, due=date(2026, 3, 12), desc="Handle payment_intent.succeeded and charge.refunded. Verify signature."),
    dict(title="Inventory reservation on checkout",        type=IssueType.story, status=IssueStatus.in_progress, priority=IssuePriority.high,     sp=5,  si=1, ai=14, due=date(2026, 3, 17), desc="Reserve stock on cart add. Release if session expires. Race-condition safe."),
    dict(title="Discount codes and promotions",            type=IssueType.story, status=IssueStatus.in_progress, priority=IssuePriority.medium,   sp=5,  si=1, ai=13, due=date(2026, 3, 19), desc="Percentage and fixed discounts. Single-use and multi-use codes. Expiry dates."),
    dict(title="Tax calculation (TaxJar)",                 type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.high,     sp=3,  si=1, ai=14, due=date(2026, 3, 21), desc="Calculate sales tax based on shipping address. Handle EU VAT."),
    dict(title="Shipping rate API integration",            type=IssueType.story, status=IssueStatus.in_review,   priority=IssuePriority.medium,   sp=5,  si=1, ai=13, due=date(2026, 3, 23), desc="EasyPost multi-carrier rate shopping. Show estimated delivery dates."),
    dict(title="Order confirmation emails",                type=IssueType.task,  status=IssueStatus.in_review,   priority=IssuePriority.medium,   sp=2,  si=1, ai=14, due=date(2026, 3, 24), desc="Transactional email via Resend. HTML template with order summary."),
    dict(title="Refund and return workflow",               type=IssueType.story, status=IssueStatus.todo,        priority=IssuePriority.high,     sp=5,  si=2, ai=13, due=date(2026, 4, 3),  desc="Agent initiates refund. Stripe refund created. Inventory restocked automatically."),
    dict(title="Product search with Algolia",              type=IssueType.task,  status=IssueStatus.todo,        priority=IssuePriority.medium,   sp=3,  si=2, ai=14, due=date(2026, 4, 7),  desc="Index products in Algolia. Instant search with typo tolerance."),
    dict(title="Subscription billing (Stripe Billing)",    type=IssueType.epic,  status=IssueStatus.backlog,     priority=IssuePriority.medium,   sp=13, si=None, ai=None, due=None, desc="Recurring billing for SaaS plan upgrades within the platform."),
    dict(title="Multi-currency support",                   type=IssueType.story, status=IssueStatus.backlog,     priority=IssuePriority.medium,   sp=8,  si=None, ai=None, due=None, desc="Display prices in local currency. Settle in account base currency via Stripe."),
    dict(title="Fraud detection rules",                    type=IssueType.story, status=IssueStatus.backlog,     priority=IssuePriority.high,     sp=8,  si=None, ai=None, due=None, desc="Block orders flagged by Stripe Radar. Manual review queue for high-risk orders."),
]

# ── Comments ───────────────────────────────────────────────────────────────────
COMMENTS_AX = [
    (7,  1, "Working on the column detection — HTML5 drag events are finicky on Safari. Will add a polyfill."),
    (7,  0, "Noted. Make sure to test Firefox too, they handle dragover differently."),
    (7,  2, "Can we also support touch-drag on iPad? That's a blocker for our mobile users."),
    (8,  0, "Root cause found: the axios interceptor is catching 401s from the login endpoint itself, causing an infinite loop."),
    (8,  1, "Good catch. We should whitelist /auth/* routes from the refresh logic."),
    (10, 2, "Design is ready in Figma. Waiting for backend invite endpoint before I can wire it up."),
    (10, 1, "Backend is done — POST /api/projects/{id}/members. Let me know if the response schema needs changes."),
    (14, 3, "I can pick this up. Should we use pytest-asyncio or just sync tests with TestClient?"),
    (14, 1, "Go with TestClient for now, it's simpler. We can migrate later."),
    (16, 4, "Found the N+1 — SQLAlchemy lazy-loads assignee and reporter on every issue. Adding joinedload."),
]

COMMENTS_MOB = [
    (5,  2, "List is rendering but performance is poor on 100+ items. Switching to FlatList with keyExtractor."),
    (5,  3, "Also add pull-to-refresh — users expect that on mobile."),
    (6,  3, "Status picker needs haptic feedback on iOS. Using Haptics.impactAsync(LIGHT)."),
    (11, 3, "Reproduced the crash. It's a null deref in the notification payload parser when data key is missing."),
    (11, 4, "PR up with the fix. Added a null check and a test case."),
    (9,  2, "We should use react-query for the cache layer — it handles stale-while-revalidate out of the box."),
]

COMMENTS_DEV = [
    (5,  5, "Terraform plan looks good. Going to apply to staging first before prod."),
    (5,  6, "Make sure to set prevent_destroy on the RDS instance — we wiped staging last sprint by accident."),
    (6,  6, "Helm chart is almost done. Values file needs review — there are some hardcoded staging hostnames."),
    (6,  5, "I'll review. Can you also add a NetworkPolicy to restrict pod-to-pod traffic?"),
    (8,  5, "Backup script tested in staging. Restore took 4 minutes for 2 GB. Well within our RTO."),
    (9,  6, "Rolling update works. Zero dropped requests confirmed with k6 during the rollout."),
    (13, 5, "Vault setup is complex. Might be worth evaluating AWS Secrets Manager instead — less ops overhead."),
]

COMMENTS_WEB = [
    (4,  7, "Blog is live on staging. Found an issue with code block overflow on mobile — will fix before go-live."),
    (4,  8, "Also make sure the RSS feed validates at w3c feed validator before we publish."),
    (7,  7, "GDPR banner needs a 'Reject All' option to be compliant in Germany and France."),
    (8,  8, "Form is connected to HubSpot. Demo request emails going to sales@ now."),
    (8,  7, "Great. Can we also add Slack notification for demo requests? Sales team prefers that."),
    (10, 7, "Lighthouse score: Performance 94, Accessibility 98, SEO 100. LCP is 1.8s."),
]

COMMENTS_DATA = [
    (4,  9,  "Dashboard is pulling live Kafka data. Latency is under 2 seconds end-to-end."),
    (4,  10, "Nice! Can we add a 7-day trend sparkline next to each metric?"),
    (5,  9,  "Model R² is 0.78 on the test set. Good enough for an MVP. Will retrain monthly."),
    (7,  10, "Anomaly detection triggered a false positive over the weekend — low traffic on Saturday looks like a drop."),
    (7,  9,  "Need to add day-of-week seasonality to the model. Will adjust the threshold logic."),
    (8,  10, "Self-serve portal is getting great feedback from the leadership team in the demo."),
]

COMMENTS_SUP = [
    (4,  11, "Help centre is indexed by Google. Seeing organic traffic from search already."),
    (4,  12, "Let's add structured data (FAQ schema) to the article pages to improve rich results."),
    (5,  11, "SLA breach alert fired correctly in staging. Agent got Slack DM 58 minutes before breach."),
    (7,  12, "CSAT scores are coming in — average 4.3/5 in the first week. Positive signal."),
    (8,  11, "Routing rules are live. Billing tickets now go straight to the finance team."),
    (10, 12, "Live chat spike caused WebSocket connection limit to be hit. Need to tune Nginx upstream config."),
]

COMMENTS_ECOM = [
    (5,  13, "Inventory reservation works in unit tests. Need to stress test with concurrent requests."),
    (5,  14, "I'll write a k6 script to simulate 50 simultaneous checkouts of the same SKU."),
    (6,  13, "Discount codes tested with 15 edge cases. The only failure is stacking codes — that's by design."),
    (7,  14, "TaxJar sandbox is returning rates correctly for all US states. EU VAT needs a VAT ID lookup."),
    (8,  13, "EasyPost integration returns rates from FedEx, UPS, and USPS. UX needs a better loading state."),
    (9,  14, "Order confirmation email looks great on Gmail and Outlook. Apple Mail has a rendering glitch."),
]


def _make_project(db, name, key, description, owner_idx, users, member_roles, sprint_defs, issues_data, comments_data, issue_prefix):
    project = Project(name=name, key=key, description=description, owner_id=users[owner_idx].id)
    db.add(project)
    db.flush()

    for i, (user_idx, role) in enumerate(member_roles):
        db.add(ProjectMember(project_id=project.id, user_id=users[user_idx].id, role=role))

    sprints = []
    for sdef in sprint_defs:
        s = Sprint(name=sdef["name"], goal=sdef["goal"], status=sdef["status"], project_id=project.id)
        db.add(s)
        sprints.append(s)
    db.flush()

    issue_objs = []
    for idx, data in enumerate(issues_data):
        sprint_id   = sprints[data["si"]].id if data["si"] is not None else None
        assignee_id = users[data["ai"]].id   if data["ai"] is not None else None
        issue = Issue(
            key=f"{issue_prefix}-{idx + 1}",
            title=data["title"],
            description=data.get("desc"),
            type=data["type"],
            status=data["status"],
            priority=data["priority"],
            story_points=data["sp"],
            due_date=data.get("due"),
            sprint_id=sprint_id,
            assignee_id=assignee_id,
            reporter_id=users[(idx + owner_idx) % len(users)].id,
            project_id=project.id,
            order=idx,
        )
        db.add(issue)
        issue_objs.append(issue)
    db.flush()

    for (issue_idx, author_idx, body) in comments_data:
        if issue_idx < len(issue_objs):
            db.add(CommentModel(body=body, issue_id=issue_objs[issue_idx].id, author_id=users[author_idx].id))

    return project


def run(db: Session):
    if db.query(User).first():
        print("⏭  Seed: data already present, skipping.")
        return

    print("🌱 Seeding demo data...")

    # ── Users ─────────────────────────────────────────────────────────────────
    users = []
    for u in USERS:
        print(f"   Creating user {u['email']} ...")
        user = User(
            email=u["email"],
            full_name=u["full_name"],
            hashed_password=hash_password(u["password"]),
            email_verified=True,
        )
        db.add(user)
        users.append(user)
    db.flush()

    # ── Project 1: Axelo Core ─────────────────────────────────────────────────
    print("   Creating project: Axelo Core ...")
    _make_project(
        db, "Axelo Core", "AX",
        "Backend API, authentication, and core infrastructure.",
        owner_idx=0, users=users,
        member_roles=[(0, MemberRole.owner), (1, MemberRole.admin), (2, MemberRole.member), (3, MemberRole.member), (4, MemberRole.viewer), (5, MemberRole.member), (6, MemberRole.viewer)],
        sprint_defs=[
            {"name": "Sprint 1", "goal": "Foundation & auth",        "status": SprintStatus.completed},
            {"name": "Sprint 2", "goal": "Kanban board & UX polish", "status": SprintStatus.active},
            {"name": "Sprint 3", "goal": "Integrations & security",  "status": SprintStatus.planned},
        ],
        issues_data=ISSUES_AX,
        comments_data=COMMENTS_AX,
        issue_prefix="AX",
    )

    # ── Project 2: Axelo Mobile ───────────────────────────────────────────────
    print("   Creating project: Axelo Mobile ...")
    _make_project(
        db, "Axelo Mobile", "MOB",
        "React Native mobile app for iOS and Android.",
        owner_idx=2, users=users,
        member_roles=[(0, MemberRole.member), (1, MemberRole.viewer), (2, MemberRole.owner), (3, MemberRole.admin), (4, MemberRole.member), (7, MemberRole.member), (8, MemberRole.member)],
        sprint_defs=[
            {"name": "Sprint 1", "goal": "App bootstrapping & auth",    "status": SprintStatus.completed},
            {"name": "Sprint 2", "goal": "Core screens & notifications", "status": SprintStatus.active},
            {"name": "Sprint 3", "goal": "Advanced features",            "status": SprintStatus.planned},
        ],
        issues_data=ISSUES_MOB,
        comments_data=COMMENTS_MOB,
        issue_prefix="MOB",
    )

    # ── Project 3: DevOps & Infrastructure ───────────────────────────────────
    print("   Creating project: DevOps & Infrastructure ...")
    _make_project(
        db, "DevOps & Infrastructure", "OPS",
        "CI/CD pipelines, Kubernetes, monitoring, and cloud infrastructure.",
        owner_idx=5, users=users,
        member_roles=[(5, MemberRole.owner), (6, MemberRole.admin), (0, MemberRole.member), (1, MemberRole.viewer), (8, MemberRole.member), (9, MemberRole.viewer)],
        sprint_defs=[
            {"name": "Sprint 1", "goal": "Containerisation & CI",         "status": SprintStatus.completed},
            {"name": "Sprint 2", "goal": "Kubernetes & observability",     "status": SprintStatus.active},
            {"name": "Sprint 3", "goal": "Security & disaster recovery",   "status": SprintStatus.planned},
        ],
        issues_data=ISSUES_DEV,
        comments_data=COMMENTS_DEV,
        issue_prefix="OPS",
    )

    # ── Project 4: Marketing Website ─────────────────────────────────────────
    print("   Creating project: Marketing Website ...")
    _make_project(
        db, "Marketing Website", "WEB",
        "Public-facing marketing site, blog, and SEO.",
        owner_idx=7, users=users,
        member_roles=[(7, MemberRole.owner), (8, MemberRole.admin), (2, MemberRole.member), (9, MemberRole.member), (10, MemberRole.viewer), (11, MemberRole.member)],
        sprint_defs=[
            {"name": "Sprint 1", "goal": "Design system & hero",       "status": SprintStatus.completed},
            {"name": "Sprint 2", "goal": "Content & SEO",              "status": SprintStatus.active},
            {"name": "Sprint 3", "goal": "Performance & i18n",         "status": SprintStatus.planned},
        ],
        issues_data=ISSUES_WEB,
        comments_data=COMMENTS_WEB,
        issue_prefix="WEB",
    )

    # ── Project 5: Data Analytics Platform ───────────────────────────────────
    print("   Creating project: Data Analytics Platform ...")
    _make_project(
        db, "Data Analytics Platform", "DATA",
        "Event pipeline, data warehouse, ML models, and analytics dashboards.",
        owner_idx=9, users=users,
        member_roles=[(9, MemberRole.owner), (10, MemberRole.admin), (0, MemberRole.member), (5, MemberRole.member), (11, MemberRole.viewer), (12, MemberRole.member)],
        sprint_defs=[
            {"name": "Sprint 1", "goal": "Data warehouse & ETL",       "status": SprintStatus.completed},
            {"name": "Sprint 2", "goal": "Real-time & ML",             "status": SprintStatus.active},
            {"name": "Sprint 3", "goal": "Self-serve & feature flags",  "status": SprintStatus.planned},
        ],
        issues_data=ISSUES_DATA,
        comments_data=COMMENTS_DATA,
        issue_prefix="DATA",
    )

    # ── Project 6: Customer Support Portal ───────────────────────────────────
    print("   Creating project: Customer Support Portal ...")
    _make_project(
        db, "Customer Support Portal", "SUP",
        "Helpdesk ticketing, knowledge base, SLA tracking, and live chat.",
        owner_idx=11, users=users,
        member_roles=[(11, MemberRole.owner), (12, MemberRole.admin), (3, MemberRole.member), (7, MemberRole.member), (13, MemberRole.member), (14, MemberRole.viewer)],
        sprint_defs=[
            {"name": "Sprint 1", "goal": "Ticketing & knowledge base",  "status": SprintStatus.completed},
            {"name": "Sprint 2", "goal": "Customer portal & SLA",       "status": SprintStatus.active},
            {"name": "Sprint 3", "goal": "Live chat & AI replies",      "status": SprintStatus.planned},
        ],
        issues_data=ISSUES_SUP,
        comments_data=COMMENTS_SUP,
        issue_prefix="SUP",
    )

    # ── Project 7: E-Commerce Integration ────────────────────────────────────
    print("   Creating project: E-Commerce Integration ...")
    _make_project(
        db, "E-Commerce Integration", "ECOM",
        "Stripe payments, product catalogue, orders, and inventory management.",
        owner_idx=13, users=users,
        member_roles=[(13, MemberRole.owner), (14, MemberRole.admin), (1, MemberRole.member), (4, MemberRole.member), (10, MemberRole.member), (15, MemberRole.viewer)],
        sprint_defs=[
            {"name": "Sprint 1", "goal": "Payments & catalogue",       "status": SprintStatus.completed},
            {"name": "Sprint 2", "goal": "Inventory & promotions",     "status": SprintStatus.active},
            {"name": "Sprint 3", "goal": "Refunds & subscriptions",    "status": SprintStatus.planned},
        ],
        issues_data=ISSUES_ECOM,
        comments_data=COMMENTS_ECOM,
        issue_prefix="ECOM",
    )

    db.commit()
    print("\n✅ Seed complete!")
    print(f"   {len(USERS)} users created. All passwords: password123")
    print("\n   Quick login accounts:")
    for u in USERS[:5]:
        print(f"   {u['email']}")
    print("   ... and 20 more (see USERS list in seed.py)")


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
