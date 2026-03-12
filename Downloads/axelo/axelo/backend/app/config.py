import logging
from pydantic_settings import BaseSettings

logger = logging.getLogger("axelo.security")

_INSECURE_DEFAULT = "dev-secret-key-change-in-production"


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://axelo:axelo@db:5432/axelo"
    SECRET_KEY: str = _INSECURE_DEFAULT
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours — A02 fix (was 7 days)

    # CORS — comma-separated allowed origins — A05 fix
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Account lockout — A07 fix
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 15

    class Config:
        env_file = ".env"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    def check_security(self) -> None:
        if self.SECRET_KEY == _INSECURE_DEFAULT:
            logger.warning(
                "SECURITY WARNING: SECRET_KEY is the insecure default. "
                "Set SECRET_KEY env var before deploying to production."
            )


settings = Settings()
settings.check_security()
