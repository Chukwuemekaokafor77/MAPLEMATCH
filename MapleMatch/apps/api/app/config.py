import json

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MapleMatch API"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/maplematch"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Clerk
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""

    # CORS — accepts a JSON string (["https://a.com","https://b.com"]) or
    # a single URL, in addition to a native list[str] from pydantic-settings.
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # CMHC Open Data
    cmhc_api_url: str = "https://api-prd.cmhc-schl.gc.ca/cmba/api"
    cmhc_api_key: str = ""

    # Email / SMTP (optional — notifications still stored in DB if not configured)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notification_from_email: str = "noreply@maplematch.ca"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    def model_post_init(self, __context: object) -> None:
        # Support CORS_ORIGINS supplied as a JSON string from env vars
        # e.g.  CORS_ORIGINS='["https://foo.vercel.app"]'
        if isinstance(self.cors_origins, str):  # type: ignore[arg-type]
            try:
                parsed = json.loads(self.cors_origins)  # type: ignore[arg-type]
                object.__setattr__(self, "cors_origins", parsed)
            except (json.JSONDecodeError, TypeError):
                # Single URL passed as plain string
                object.__setattr__(self, "cors_origins", [self.cors_origins])  # type: ignore[arg-type]


settings = Settings()
