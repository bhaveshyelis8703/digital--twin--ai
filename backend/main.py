import sys
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.routes import analytics, auth, financial, fitness, goals, habits, study, users
from app.api.routes import forecasting as forecasting_routes
from app.api.routes import digital_twin as digital_twin_routes
from app.api.routes import simulation as simulation_routes
from app.api.routes import scenarios as scenarios_routes
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import decode_access_token
from app.models.user import AnalyticsLog

app = FastAPI(
    title="Digital Twin AI",
    version="3.0.0",
    description="Milestone 1 data collection + Milestone 2 ML forecasting + Milestone 3 Simulation Engine",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.middleware("http")
async def analytics_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    if request.url.path.startswith("/api"):
        user_id = None
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                payload = decode_access_token(auth_header.split(" ", 1)[1])
                user_id = int(payload.get("sub"))
            except Exception:
                user_id = None

        db = SessionLocal()
        try:
            db.add(
                AnalyticsLog(
                    user_id=user_id,
                    endpoint=request.url.path,
                    method=request.method,
                    response_time_ms=duration_ms,
                )
            )
            db.commit()
        finally:
            db.close()
    return response


app.include_router(auth.router,              prefix="/api/auth",        tags=["auth"])
app.include_router(users.router,             prefix="/api/users",       tags=["users"])
app.include_router(financial.router,         prefix="/api/financial",   tags=["financial"])
app.include_router(study.router,             prefix="/api/study",       tags=["study"])
app.include_router(habits.router,            prefix="/api/habits",      tags=["habits"])
app.include_router(fitness.router,           prefix="/api/fitness",     tags=["fitness"])
app.include_router(goals.router,             prefix="/api/goals",       tags=["goals"])
app.include_router(analytics.router,              prefix="/api/analytics",      tags=["analytics"])
app.include_router(forecasting_routes.router,     prefix="/api/forecasting",    tags=["forecasting"])
app.include_router(digital_twin_routes.router,    prefix="/api/digital-twin",   tags=["digital-twin"])
app.include_router(simulation_routes.router,      prefix="/api/simulation",     tags=["simulation"])
app.include_router(scenarios_routes.router,       prefix="/api/scenarios",      tags=["scenarios"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
