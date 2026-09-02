import os
from pathlib import Path

from dotenv import load_dotenv

# config.py lives at backend/app/core/config.py
# BASE_DIR resolves to backend/ (two levels up from this file)
BASE_DIR = Path(__file__).resolve().parents[2]

# Try backend/.env first; fall back to the project root .env
_env_in_backend     = BASE_DIR / ".env"
_env_in_project_root = BASE_DIR.parent / ".env"

if _env_in_backend.exists():
    load_dotenv(_env_in_backend)
elif _env_in_project_root.exists():
    load_dotenv(_env_in_project_root)

# Resolve DB path to an absolute path so it is the same regardless of
# which directory uvicorn / the seed script is launched from.
_DEFAULT_DB_PATH = str(BASE_DIR.parent / "digital_twin_ai.db")


class Settings:
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{_DEFAULT_DB_PATH}"
    )
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    ALLOWED_ORIGINS: str = os.getenv(
        "ALLOWED_ORIGINS", "http://127.0.0.1:8501,http://localhost:8501"
    )

    # ── Milestone 4: AI ───────────────────────────────────────────────────────
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "800"))
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))

    # ── Milestone 4: Rate limiting ────────────────────────────────────────────
    RATE_LIMIT_MESSAGES_PER_HOUR: int = int(os.getenv("RATE_LIMIT_MESSAGES_PER_HOUR", "30"))
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    # ── Milestone 4: Reports ──────────────────────────────────────────────────
    REPORTS_DIR: str = os.getenv("REPORTS_DIR", "./reports")


settings = Settings()
