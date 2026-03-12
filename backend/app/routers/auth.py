"""
Auth router — complete implementation including email verification.

OWASP notes:
  A02: verification token = secrets.token_urlsafe(32), stored as SHA-256 hash, 24h expiry
  A06: token invalidated on first use (one-time only)
  A07: resend rate-limited 3/hour; 2fa/verify rate-limited 5/min
  A09: resend always returns 200 (enumeration-safe)
  A01: login blocked for unverified users; OAuth users auto-verified
  A03: user content HTML-escaped before embedding in email templates
"""
import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta, timezone

import pyotp
import httpx

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, Token
from app.core.auth import (
    hash_password, verify_password, create_access_token, decode_token,
)
from app.core.deps import get_current_user
from app.core.security import (
    limiter, validate_password, log_auth_failure, log_auth_success,
    MAX_PROJECT_NAME, clamp_str, verify_captcha,
)
from app.core.email import send_verification_email
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GITHUB_CLIENT_ID     = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
FRONTEND_URL         = os.getenv("FRONTEND_URL", "http://localhost:3000")


# ── Pydantic bodies ───────────────────────────────────────────────────────────

class LoginBody(BaseModel):
    email: EmailStr
    password: str

class TFAEnableBody(BaseModel):
    secret: str
    code: str

class TFACodeBody(BaseModel):
    code: str

class TFAVerifyBody(BaseModel):
    temp_token: str
    code: str

class ResendBody(BaseModel):
    email: EmailStr


# ── Internal helpers ──────────────────────────────────────────────────────────

def _make_temp_token(user_id: int) -> str:
    return create_access_token(
        {"sub": str(user_id), "scope": "2fa_pending"},
        expires_delta=timedelta(minutes=5),
    )


def _verify_temp_token(token: str) -> int:
    payload = decode_token(token)
    if not payload or payload.get("scope") != "2fa_pending":
        raise HTTPException(status_code=401, detail="Invalid or expired 2FA challenge token")
    return int(payload["sub"])


def _make_oauth_state(provider: str) -> str:
    return create_access_token(
        {"nonce": secrets.token_hex(16), "provider": provider, "scope": "oauth_state"},
        expires_delta=timedelta(minutes=10),
    )


def _verify_oauth_state(state: str, expected_provider: str) -> None:
    payload = decode_token(state)
    if not payload or payload.get("scope") != "oauth_state":
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    if payload.get("provider") != expected_provider:
        raise HTTPException(status_code=400, detail="OAuth provider mismatch")


def _check_recovery_code(code: str, hashed_codes: list) -> int | None:
    for i, hashed in enumerate(hashed_codes):
        if verify_password(code, hashed):
            return i
    return None


def _hash_token(raw: str) -> str:
    """SHA-256 hash of a raw token. Compare stored hash against this."""
    return hashlib.sha256(raw.encode()).hexdigest()


def _issue_verification_token(user: User, db: Session) -> str:
    """Generate + store a fresh verification token. Returns raw token to email to user."""
    raw = secrets.token_urlsafe(32)   # 192-bit entropy, OWASP A02
    user.email_verification_token_hash = _hash_token(raw)
    user.email_verification_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    db.commit()
    return raw


def _get_or_create_oauth_user(db: Session, provider: str, oauth_id: str,
                               email: str, full_name: str) -> User:
    user = db.query(User).filter(
        User.oauth_provider == provider, User.oauth_id == oauth_id,
    ).first()
    if user:
        return user
    user = db.query(User).filter(User.email == email.lower()).first()
    if user:
        user.oauth_provider = provider
        user.oauth_id = oauth_id
        user.email_verified = True           # provider already verified it
        user.email_verification_token_hash = None
        db.commit()
        return user
    user = User(
        email=email.lower(),
        full_name=clamp_str(full_name, MAX_PROJECT_NAME) or email.split("@")[0],
        hashed_password=None,
        oauth_provider=provider,
        oauth_id=oauth_id,
        email_verified=True,                 # OAuth providers guarantee email ownership
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _do_login(request: Request, email_raw: str, password: str, db: Session):
    ip = request.client.host if request.client else "unknown"
    email = email_raw.lower().strip()
    user = db.query(User).filter(User.email == email).first()

    if not user:
        log_auth_failure(ip, email, "user_not_found")
        raise HTTPException(status_code=401, detail="Invalid credentials",
                            headers={"WWW-Authenticate": "Bearer"})
    if user.hashed_password is None:
        log_auth_failure(ip, email, "oauth_only_account")
        raise HTTPException(status_code=400, detail="Please sign in with your OAuth provider")
    if not verify_password(password, user.hashed_password):
        log_auth_failure(ip, email, "bad_password")
        raise HTTPException(status_code=401, detail="Invalid credentials",
                            headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        log_auth_failure(ip, email, "inactive")
        raise HTTPException(status_code=403, detail="Account is inactive")

    # OWASP A01 — block login until email verified
    if settings.EMAIL_VERIFICATION_ENABLED and not user.email_verified:
        raise HTTPException(status_code=403, detail="EMAIL_NOT_VERIFIED")

    if user.totp_enabled:
        return {"requires_2fa": True, "temp_token": _make_temp_token(user.id)}

    log_auth_success(ip, user.id, email)
    return {"access_token": create_access_token({"sub": str(user.id)}), "token_type": "bearer"}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"

    # OWASP A07: verify CAPTCHA server-side before any DB work
    # A bot that strips the widget from the DOM still hits this check
    await verify_captcha(user_in.captcha_token, ip)

    errors = validate_password(user_in.password)
    if errors:
        raise HTTPException(status_code=422, detail=" ".join(errors))

    email = user_in.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=email,
        full_name=clamp_str(user_in.full_name.strip(), MAX_PROJECT_NAME),
        hashed_password=hash_password(user_in.password),
        email_verified=not settings.EMAIL_VERIFICATION_ENABLED,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if settings.EMAIL_VERIFICATION_ENABLED:
        raw_token = _issue_verification_token(user, db)
        try:
            await send_verification_email(user.email, user.full_name, raw_token)
        except Exception:
            pass   # don't block registration on email failure

    return user


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """
    One-time email verification endpoint.
    OWASP A02: compare SHA-256(supplied_token) against stored hash — never the raw token.
    OWASP A06: token cleared on first successful use.
    """
    if not token or len(token) > 128:
        raise HTTPException(status_code=400, detail="Invalid token")

    token_hash = _hash_token(token)
    user = db.query(User).filter(
        User.email_verification_token_hash == token_hash
    ).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or already used verification link")

    now = datetime.now(timezone.utc)
    expires = user.email_verification_expires_at
    if expires:
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if now > expires:
            raise HTTPException(
                status_code=400,
                detail="Verification link has expired. Request a new one from the login page."
            )

    user.email_verified = True
    user.email_verification_token_hash = None
    user.email_verification_expires_at = None
    db.commit()

    return {"message": "Email verified successfully. You can now log in."}


@router.post("/resend-verification")
@limiter.limit("3/hour")
async def resend_verification(
    request: Request,
    body: ResendBody,
    db: Session = Depends(get_db),
):
    """
    Resend verification email.
    OWASP A09: always returns 200 regardless of whether email exists (enumeration-safe).
    OWASP A07: rate-limited 3 requests/hour per IP.
    """
    email = body.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()

    if user and not user.email_verified and user.hashed_password:
        raw_token = _issue_verification_token(user, db)
        try:
            await send_verification_email(user.email, user.full_name, raw_token)
        except Exception:
            pass

    return {"message": "If that email is registered and unverified, a new link has been sent."}


@router.post("/login", response_model=None)
@limiter.limit("20/minute")
def login_json(request: Request, body: LoginBody, db: Session = Depends(get_db)):
    return _do_login(request, body.email, body.password, db)


@router.post("/login/form", response_model=None, include_in_schema=False)
@limiter.limit("20/minute")
def login_form(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    return _do_login(request, form_data.username, form_data.password, db)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


# ── Two-Factor Authentication ─────────────────────────────────────────────────

@router.post("/2fa/setup")
def tfa_setup(current_user: User = Depends(get_current_user)):
    if current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA is already enabled")
    secret = pyotp.random_base32()
    uri = pyotp.TOTP(secret).provisioning_uri(name=current_user.email, issuer_name="Axelo")
    return {"secret": secret, "uri": uri}


@router.post("/2fa/enable")
@limiter.limit("10/minute")
def tfa_enable(
    request: Request,
    body: TFAEnableBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA is already enabled")
    if not pyotp.TOTP(body.secret).verify(body.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")
    raw_codes = [secrets.token_hex(8).upper() for _ in range(10)]
    hashed_codes = [hash_password(c) for c in raw_codes]
    current_user.totp_secret = body.secret
    current_user.totp_enabled = True
    current_user.totp_recovery_codes = json.dumps(hashed_codes)
    db.commit()
    return {"recovery_codes": raw_codes, "message": "2FA enabled. Save these recovery codes."}


@router.post("/2fa/verify", response_model=None)
@limiter.limit("5/minute")
def tfa_verify(request: Request, body: TFAVerifyBody, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    user_id = _verify_temp_token(body.temp_token)
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA not enabled for this account")

    if pyotp.TOTP(user.totp_secret).verify(body.code, valid_window=1):
        log_auth_success(ip, user.id, user.email)
        return {"access_token": create_access_token({"sub": str(user.id)}), "token_type": "bearer"}

    stored = json.loads(user.totp_recovery_codes or "[]")
    idx = _check_recovery_code(body.code.upper(), stored)
    if idx is not None:
        stored.pop(idx)
        user.totp_recovery_codes = json.dumps(stored)
        db.commit()
        log_auth_success(ip, user.id, user.email)
        return {"access_token": create_access_token({"sub": str(user.id)}), "token_type": "bearer"}

    log_auth_failure(ip, user.email, "invalid_totp")
    raise HTTPException(status_code=401, detail="Invalid 2FA code")


@router.post("/2fa/disable")
@limiter.limit("5/minute")
def tfa_disable(
    request: Request,
    body: TFACodeBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA is not enabled")
    if not pyotp.TOTP(current_user.totp_secret).verify(body.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")
    current_user.totp_enabled = False
    current_user.totp_secret = None
    current_user.totp_recovery_codes = None
    db.commit()
    return {"message": "2FA disabled"}


@router.get("/2fa/status")
def tfa_status(current_user: User = Depends(get_current_user)):
    return {"enabled": current_user.totp_enabled}


# ── OAuth / SSO ───────────────────────────────────────────────────────────────

@router.get("/oauth/google")
def oauth_google_start():
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")
    state = _make_oauth_state("google")
    redirect_uri = f"{FRONTEND_URL}/oauth/google/callback"
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        f"&state={state}"
        "&access_type=offline&prompt=select_account"
    )
    return RedirectResponse(url)


@router.get("/oauth/google/callback")
async def oauth_google_callback(code: str, state: str, db: Session = Depends(get_db)):
    _verify_oauth_state(state, "google")
    redirect_uri = f"{FRONTEND_URL}/oauth/google/callback"
    async with httpx.AsyncClient(timeout=10) as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={"code": code, "client_id": GOOGLE_CLIENT_ID,
                  "client_secret": GOOGLE_CLIENT_SECRET,
                  "redirect_uri": redirect_uri, "grant_type": "authorization_code"},
        )
    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Google token exchange failed")
    from jose import jwt as _jwt
    claims = _jwt.get_unverified_claims(token_resp.json().get("id_token", ""))
    email = claims.get("email", "")
    if not email:
        raise HTTPException(status_code=400, detail="Google did not return an email")
    user = _get_or_create_oauth_user(db, "google", claims.get("sub", ""), email, claims.get("name", ""))
    return RedirectResponse(f"{FRONTEND_URL}/#token={create_access_token({'sub': str(user.id)})}")


@router.get("/oauth/github")
def oauth_github_start():
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=501, detail="GitHub OAuth not configured")
    state = _make_oauth_state("github")
    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}&scope=user:email&state={state}"
    )
    return RedirectResponse(url)


@router.get("/oauth/github/callback")
async def oauth_github_callback(code: str, state: str, db: Session = Depends(get_db)):
    _verify_oauth_state(state, "github")
    async with httpx.AsyncClient(timeout=10) as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={"client_id": GITHUB_CLIENT_ID, "client_secret": GITHUB_CLIENT_SECRET, "code": code},
        )
        gh_token = token_resp.json().get("access_token", "")
        user_resp = await client.get("https://api.github.com/user",
            headers={"Authorization": f"Bearer {gh_token}", "Accept": "application/json"})
        email_resp = await client.get("https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {gh_token}", "Accept": "application/json"})
    gh_user = user_resp.json()
    emails = email_resp.json() if email_resp.status_code == 200 else []
    email = gh_user.get("email", "")
    if not email:
        for e in emails:
            if e.get("primary") and e.get("verified"):
                email = e["email"]
                break
    if not email:
        raise HTTPException(status_code=400, detail="GitHub did not provide a verified email")
    user = _get_or_create_oauth_user(
        db, "github", str(gh_user["id"]), email,
        gh_user.get("name") or gh_user.get("login", ""),
    )
    return RedirectResponse(f"{FRONTEND_URL}/#token={create_access_token({'sub': str(user.id)})}")


@router.get("/captcha-config")
def captcha_config():
    """
    Return CAPTCHA site key + provider to the frontend.
    OWASP A04: only the PUBLIC site key is returned — secret key never leaves the server.
    """
    return {
        "enabled":  settings.CAPTCHA_ENABLED,
        "provider": settings.CAPTCHA_PROVIDER,
        "site_key": settings.CAPTCHA_SITE_KEY,
    }
