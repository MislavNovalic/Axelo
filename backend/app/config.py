from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://axelo:axelo@db:5432/axelo"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # OAuth (Phase 3)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    # Phase 4 — AI features
    ANTHROPIC_API_KEY: str = ""
    AI_ENABLED: bool = True
    AI_MAX_TOKENS: int = 1024
    AI_MODEL: str = "claude-opus-4-6"

    # Phase 4 — Import limits
    IMPORT_MAX_ISSUES: int = 5000
    IMPORT_MAX_MEMBERS: int = 500

    # Email verification
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@axelo.dev"
    SMTP_FROM_NAME: str = "Axelo"
    SMTP_TLS: bool = True
    EMAIL_VERIFICATION_ENABLED: bool = True   # set False in dev to skip verification

    # CAPTCHA (Cloudflare Turnstile by default; hCaptcha also supported)
    CAPTCHA_ENABLED: bool = True                   # set False in dev/test to skip
    CAPTCHA_PROVIDER: str = "turnstile"            # "turnstile" | "hcaptcha"
    CAPTCHA_SECRET_KEY: str = ""                   # Turnstile: secret key from dash.cloudflare.com
    CAPTCHA_SITE_KEY: str = ""                     # Turnstile: site key (safe to expose to frontend)

    # Phase 5 — Redis / async task queue
    REDIS_URL: str = "redis://localhost:6379/0"
    EMAIL_NOTIFICATIONS_ENABLED: bool = True   # master switch for queued email notifications

    # Content-Security-Policy violation reporting (optional)
    # Point to a collector such as https://report-uri.com or your own endpoint
    # Leave empty to omit the report-uri directive
    CSP_REPORT_URI: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
