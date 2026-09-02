import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT    = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("DATABASE_URL",                "sqlite:///./test_digital_twin_ai.db")
os.environ.setdefault("SECRET_KEY",                  "test-secret")
os.environ.setdefault("ALGORITHM",                   "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("OPENAI_API_KEY",              "")
os.environ.setdefault("RATE_LIMIT_MESSAGES_PER_HOUR","10000")
os.environ.setdefault("REDIS_URL",                   "")

# Import FastAPI app object (not the `app` package)
from main import app as fastapi_app          # noqa: E402
from app.core.database import Base, engine   # noqa: E402
import app.models.user                       # noqa: E402, F401 — registers all models inc. M4


@pytest.fixture(scope="function")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(fastapi_app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)
