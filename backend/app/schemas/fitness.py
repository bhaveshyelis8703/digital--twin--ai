from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FitnessActivityCreate(BaseModel):
    activity_type: str = Field(..., min_length=1)
    duration: float = Field(..., gt=0)
    calories_burned: float = Field(..., gt=0)
    activity_date: datetime


class FitnessActivityUpdate(BaseModel):
    activity_type: str | None = Field(default=None, min_length=1)
    duration: float | None = Field(default=None, gt=0)
    calories_burned: float | None = Field(default=None, gt=0)
    activity_date: datetime | None = None


class FitnessActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    activity_type: str
    duration: float
    calories_burned: float
    activity_date: datetime
    created_at: datetime
    updated_at: datetime
