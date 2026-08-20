from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.models.user import FinancialRecord, Goal, Habit, User
from app.schemas.user import ProfileResponse, ProfileUpdate, SummaryResponse

router = APIRouter()


@router.get("/profile", response_model=ProfileResponse)
def get_profile(current_user: Annotated[User, Depends(get_current_user)]) -> ProfileResponse:
    return ProfileResponse.model_validate(current_user)


@router.put("/profile", response_model=ProfileResponse)
def update_profile(
    profile_update: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ProfileResponse:
    for field, value in profile_update.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return ProfileResponse.model_validate(current_user)


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> None:
    current_user.is_active = False
    db.commit()


@router.get("/summary", response_model=SummaryResponse)
def get_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> SummaryResponse:
    financial_record_count = db.query(FinancialRecord).filter(FinancialRecord.user_id == current_user.id).count()
    active_goals = db.query(Goal).filter(Goal.user_id == current_user.id, Goal.status != "Completed").count()
    habit_streak = sum(h.streak for h in db.query(Habit).filter(Habit.user_id == current_user.id).all())
    return SummaryResponse(
        profile=ProfileResponse.model_validate(current_user),
        financial_record_count=financial_record_count,
        active_goals=active_goals,
        habit_streak=habit_streak,
    )
