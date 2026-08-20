from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HabitCreate(BaseModel):
    name: str = Field(..., min_length=1)
    target_frequency: str = Field(..., min_length=1)
    completed: bool = False
    completion_date: datetime | None = None
    streak: int = 0


class HabitUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    target_frequency: str | None = Field(default=None, min_length=1)
    completed: bool | None = None
    completion_date: datetime | None = None
    streak: int | None = None


class HabitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    target_frequency: str
    completed: bool
    completion_date: datetime | None = None
    streak: int
    created_at: datetime
    updated_at: datetime
