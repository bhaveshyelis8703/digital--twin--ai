from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GoalCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    target_value: float = Field(..., gt=0)
    current_value: float = Field(default=0, ge=0)
    target_date: datetime
    status: str = Field(..., min_length=1)


class GoalUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = Field(default=None, min_length=1)
    target_value: float | None = Field(default=None, gt=0)
    current_value: float | None = Field(default=None, ge=0)
    target_date: datetime | None = None
    status: str | None = Field(default=None, min_length=1)


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    description: str
    target_value: float
    current_value: float
    target_date: datetime
    status: str
    created_at: datetime
    updated_at: datetime
