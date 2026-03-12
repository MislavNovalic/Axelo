"""
OWASP hardening layer:
  - Rate limiter (slowapi)
  - Security headers middleware
  - Password validation
  - Input sanitisation helpers
  - Structured auth-failure logging
"""
import re
import logging
from datetime import datetime
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ── Logger ────────────────────────────────────────────────────────────────────
logger = logging.getLogger("axelo.security")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)

# ── Rate limiter (shared instance) ────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(f"Rate limit exceeded: {request.client.host} {request.url.path}")
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down."},
        headers={"Retry-After": "60"},
    )


# ── Security headers middleware ───────────────────────────────────────────────
def _build_api_csp() -> str:
    """
    Build the Content-Security-Policy for API responses.

    OWASP A03 — XSS mitigation strategy:
      • No 'unsafe-inline' in script-src — any injected inline script is blocked
      • No 'unsafe-eval' — blocks eval() / Function() code injection
      • object-src 'none' — blocks Flash, Java applets, and legacy plugins
      • base-uri 'self' — prevents <base> tag injection (dangling-markup attacks)
      • form-action 'self' — blocks forms from submitting data to external hosts
      • frame-ancestors 'none' — clickjacking defence (supersedes X-Frame-Options
        in all modern browsers but we keep both for legacy support)
      • upgrade-insecure-requests — forces HTTP sub-resources to HTTPS

    Import is deferred so settings are fully resolved before this is called.
    """
    from app.config import settings as _s

    # CAPTCHA CDN domains depend on which provider is configured
    captcha_script = ""
    captcha_connect = ""
    captcha_frame = ""
    if _s.CAPTCHA_ENABLED:
        if _s.CAPTCHA_PROVIDER == "hcaptcha":
            captcha_script  = " https://js.hcaptcha.com"
            captcha_connect = " https://hcaptcha.com https://newassets.hcaptcha.com"
            captcha_frame   = " https://newassets.hcaptcha.com"
        else:  # turnstile (default)
            captcha_script  = " https://challenges.cloudflare.com"
            captcha_connect = " https://challenges.cloudflare.com"
            captcha_frame   = " https://challenges.cloudflare.com"

    # Optional violation report endpoint (set CSP_REPORT_URI in .env)
    report = f" report-uri {_s.CSP_REPORT_URI};" if _s.CSP_REPORT_URI else ""

    directives = [
        "default-src 'self'",
        # No 'unsafe-inline' — the API never serves HTML with inline scripts
        f"script-src 'self'{captcha_script}",
        # 'unsafe-inline' in style-src is far less dangerous than in script-src
        # (CSS-based data exfiltration requires additional conditions to exploit)
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com data:",
        "img-src 'self' data: blob: https:",
        f"connect-src 'self' ws: wss:{captcha_connect}",
        "frame-src " + (captcha_frame if captcha_frame else "'none'"),
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "upgrade-insecure-requests",
    ]
    return "; ".join(directives) + ";" + report


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies security headers to every response.

    CSP is built once at first request and cached — avoids reconstructing
    the string on every single API call while still reading live settings.
    """
    _csp_cache: str | None = None

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Build CSP once and cache it for the lifetime of the process
        if self._csp_cache is None:
            SecurityHeadersMiddleware._csp_cache = _build_api_csp()

        response.headers["Content-Security-Policy"] = self._csp_cache
        response.headers["X-Content-Type-Options"]  = "nosniff"
        response.headers["X-Frame-Options"]         = "DENY"
        # X-XSS-Protection is deprecated in modern browsers and can cause issues;
        # kept for IE/legacy compatibility only
        response.headers["X-XSS-Protection"]        = "1; mode=block"
        response.headers["Referrer-Policy"]          = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]       = "geolocation=(), microphone=(), camera=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Strip server fingerprint — don't leak framework/version info
        if "server" in response.headers:
            del response.headers["server"]
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]

        return response


# ── Password validation ───────────────────────────────────────────────────────
MIN_PASSWORD_LENGTH = 8

def validate_password(password: str) -> list[str]:
    """Returns list of violation messages. Empty list = valid."""
    errors = []
    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if not re.search(r'[A-Za-z]', password):
        errors.append("Password must contain at least one letter.")
    if not re.search(r'[0-9]', password):
        errors.append("Password must contain at least one digit.")
    return errors


# ── Input length limits ───────────────────────────────────────────────────────
MAX_TITLE_LEN       = 512
MAX_DESC_LEN        = 50_000
MAX_COMMENT_LEN     = 20_000
MAX_PROJECT_NAME    = 128
MAX_KEY_LEN         = 10

def clamp_str(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    return value[:max_len]


# ── Auth failure logging ──────────────────────────────────────────────────────
def log_auth_failure(ip: str, email: str, reason: str):
    logger.warning(
        f"AUTH_FAILURE ip={ip} email={email!r} reason={reason} "
        f"time={datetime.utcnow().isoformat()}"
    )

def log_auth_success(ip: str, user_id: int, email: str):
    logger.info(
        f"AUTH_SUCCESS ip={ip} user_id={user_id} email={email!r} "
        f"time={datetime.utcnow().isoformat()}"
    )


# ── CAPTCHA verification ───────────────────────────────────────────────────────

import httpx as _httpx
from app.config import settings as _settings

_TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
_HCAPTCHA_VERIFY_URL  = "https://hcaptcha.com/siteverify"


async def verify_captcha(token: str | None, ip: str) -> None:
    """
    Verify a CAPTCHA token server-side.

    OWASP A07: verification is always server-side — a client-side-only check
    can be trivially bypassed by removing the widget from the DOM.
    OWASP A04: secret key is read from settings (env), never sent to frontend.
    OWASP A09: failures are logged with IP for abuse pattern detection.

    Raises HTTPException 400 if the token is invalid or verification fails.
    Raises HTTPException 503 if the CAPTCHA provider is unreachable.
    """
    if not _settings.CAPTCHA_ENABLED:
        return   # dev / test mode — skip silently

    if not token:
        logger.warning(f"CAPTCHA_MISSING ip={ip}")
        raise HTTPException(status_code=400, detail="CAPTCHA_REQUIRED")

    if not _settings.CAPTCHA_SECRET_KEY:
        # Misconfigured server — log and block registration to avoid silent bypass
        logger.error("CAPTCHA_SECRET_KEY not set but CAPTCHA_ENABLED=true")
        raise HTTPException(status_code=503, detail="CAPTCHA service not configured")

    verify_url = (
        _TURNSTILE_VERIFY_URL
        if _settings.CAPTCHA_PROVIDER == "turnstile"
        else _HCAPTCHA_VERIFY_URL
    )

    try:
        async with _httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(
                verify_url,
                data={
                    "secret":   _settings.CAPTCHA_SECRET_KEY,
                    "response": token,
                    "remoteip": ip,   # optional but helps provider detect abuse
                },
            )
        result = resp.json()
    except _httpx.TimeoutException:
        logger.error(f"CAPTCHA_TIMEOUT ip={ip} provider={_settings.CAPTCHA_PROVIDER}")
        raise HTTPException(status_code=503, detail="CAPTCHA verification timed out. Please try again.")
    except Exception as exc:
        logger.error(f"CAPTCHA_ERROR ip={ip} error={exc!r}")
        raise HTTPException(status_code=503, detail="CAPTCHA verification failed. Please try again.")

    if not result.get("success"):
        error_codes = result.get("error-codes", [])
        logger.warning(f"CAPTCHA_FAIL ip={ip} codes={error_codes}")
        raise HTTPException(status_code=400, detail="CAPTCHA_INVALID")
