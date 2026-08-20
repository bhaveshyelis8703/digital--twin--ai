from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.models.user import FitnessActivity, User
from app.schemas.fitness import FitnessActivityCreate, FitnessActivityResponse, FitnessActivityUpdate

router = APIRouter()


@router.post("", response_model=FitnessActivityResponse, status_code=status.HTTP_201_CREATED)
def create_fitness_activity(
    payload: FitnessActivityCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> FitnessActivityResponse:
    activity = FitnessActivity(user_id=current_user.id, **payload.model_dump())
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return FitnessActivityResponse.model_validate(activity)


@router.get("", response_model=list[FitnessActivityResponse])
def list_fitness_activities(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> list[FitnessActivityResponse]:
    activities = db.query(FitnessActivity).filter(FitnessActivity.user_id == current_user.id).order_by(FitnessActivity.activity_date.desc()).all()
    return [FitnessActivityResponse.model_validate(item) for item in activities]


@router.get("/{activity_id}", response_model=FitnessActivityResponse)
def get_fitness_activity(
    activity_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> FitnessActivityResponse:
    activity = db.query(FitnessActivity).filter(FitnessActivity.id == activity_id, FitnessActivity.user_id == current_user.id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Fitness activity not found")
    return FitnessActivityResponse.model_validate(activity)


@router.put("/{activity_id}", response_model=FitnessActivityResponse)
def update_fitness_activity(
    activity_id: int,
    payload: FitnessActivityUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> FitnessActivityResponse:
    activity = db.query(FitnessActivity).filter(FitnessActivity.id == activity_id, FitnessActivity.user_id == current_user.id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Fitness activity not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(activity, field, value)
    db.commit()
    db.refresh(activity)
    return FitnessActivityResponse.model_validate(activity)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fitness_activity(
    activity_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> None:
    activity = db.query(FitnessActivity).filter(FitnessActivity.id == activity_id, FitnessActivity.user_id == current_user.id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Fitness activity not found")
    db.delete(activity)
    db.commit()
