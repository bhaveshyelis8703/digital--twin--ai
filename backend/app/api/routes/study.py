"""
backend/app/api/routes/study.py
Milestone 1 CRUD + Milestone 2 prediction endpoints.

IMPORTANT: Named routes (e.g. /exam-readiness) must be declared BEFORE
/{activity_id} so FastAPI does not swallow them as path params.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.models.user import StudyActivity, User
from app.schemas.study import StudyActivityCreate, StudyActivityResponse, StudyActivityUpdate

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
#  MILESTONE 2 — PREDICTION ENDPOINTS  (must come before /{activity_id})
# ═══════════════════════════════════════════════════════════════════════════════

class OptimalPlanRequest(BaseModel):
    target_score: float = Field(..., ge=0, le=100)
    exam_date:    str   = Field(..., description="ISO date string e.g. 2026-09-01")
    subject:      str   = Field(default="General")


@router.get("/performance-prediction",
            summary="Predicted performance score for next session")
def performance_prediction(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    try:
        from app.services.study_service import get_performance_prediction
        from ml.data_preparation import load_study_data

        df = load_study_data(current_user.id)
        if df.empty:
            return {"predicted_score": None, "message": "No study data yet"}

        last = df.sort_values("study_date").iloc[-1]
        features = {
            "study_hours":       float(last.get("study_hours", 2)),
            "focus_score":       float(last.get("focus_score", 70)),
            "task_completion":   float(last.get("task_completion", 70)),
            "subject_encoded":   0,
            "month":             int(last["study_date"].month),
            "day_of_week":       int(last["study_date"].dayofweek),
            "study_streak_days": 3,
            "peak_study_hour":   int(last["study_date"].hour),
        }
        return get_performance_prediction(current_user.id, features)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exam-readiness", summary="Exam readiness score with explanation")
def exam_readiness(
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        from app.services.study_service import get_exam_readiness
        return get_exam_readiness(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimal-plan", summary="Recommended daily study schedule")
def optimal_plan(
    body: OptimalPlanRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        from app.services.study_service import get_optimal_plan
        return get_optimal_plan(
            body.target_score, body.exam_date,
            body.subject, current_user.id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend", summary="Study hours trend: improving / stable / declining")
def study_trend(
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        from app.services.study_service import get_study_trend
        return get_study_trend(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
#  MILESTONE 1 — CRUD  (/{activity_id} must come AFTER named routes)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("", response_model=StudyActivityResponse, status_code=status.HTTP_201_CREATED)
def create_study_activity(
    payload: StudyActivityCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> StudyActivityResponse:
    activity = StudyActivity(user_id=current_user.id, **payload.model_dump())
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return StudyActivityResponse.model_validate(activity)


@router.get("", response_model=list[StudyActivityResponse])
def list_study_activities(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> list[StudyActivityResponse]:
    activities = (
        db.query(StudyActivity)
        .filter(StudyActivity.user_id == current_user.id)
        .order_by(StudyActivity.study_date.desc())
        .all()
    )
    return [StudyActivityResponse.model_validate(a) for a in activities]


@router.get("/{activity_id}", response_model=StudyActivityResponse)
def get_study_activity(
    activity_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> StudyActivityResponse:
    activity = db.query(StudyActivity).filter(
        StudyActivity.id == activity_id,
        StudyActivity.user_id == current_user.id,
    ).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Study activity not found")
    return StudyActivityResponse.model_validate(activity)


@router.put("/{activity_id}", response_model=StudyActivityResponse)
def update_study_activity(
    activity_id: int,
    payload: StudyActivityUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> StudyActivityResponse:
    activity = db.query(StudyActivity).filter(
        StudyActivity.id == activity_id,
        StudyActivity.user_id == current_user.id,
    ).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Study activity not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(activity, field, value)
    db.commit()
    db.refresh(activity)
    return StudyActivityResponse.model_validate(activity)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_study_activity(
    activity_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> None:
    activity = db.query(StudyActivity).filter(
        StudyActivity.id == activity_id,
        StudyActivity.user_id == current_user.id,
    ).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Study activity not found")
    db.delete(activity)
    db.commit()
