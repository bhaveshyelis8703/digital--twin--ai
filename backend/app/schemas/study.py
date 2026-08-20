from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StudyActivityCreate(BaseModel):
    subject: str = Field(..., min_length=1)
    study_date: datetime
    study_hours: float = Field(..., ge=0.5, le=16)
    focus_score: float = Field(..., ge=0, le=100)
    task_completion: float = Field(..., ge=0, le=100)
    performance_score: float = Field(..., ge=0, le=100)


class StudyActivityUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=1)
    study_date: datetime | None = None
    study_hours: float | None = Field(default=None, ge=0.5, le=16)
    focus_score: float | None = Field(default=None, ge=0, le=100)
    task_completion: float | None = Field(default=None, ge=0, le=100)
    performance_score: float | None = Field(default=None, ge=0, le=100)


class StudyActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    subject: str
    study_date: datetime
    study_hours: float
    focus_score: float
    task_completion: float
    performance_score: float
    created_at: datetime
    updated_at: datetime
