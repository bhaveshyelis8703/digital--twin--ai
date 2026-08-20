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
    # If DATABASE_URL is set in .env, use that. Otherwise use the absolute
    # path to the single DB file in the project root.
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{_DEFAULT_DB_PATH}"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


settings = Settings()
