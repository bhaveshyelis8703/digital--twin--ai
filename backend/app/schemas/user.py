from pydantic import BaseModel, ConfigDict, Field


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    age: int | None = Field(default=None, ge=13, le=100)
    occupation: str | None = Field(default=None, min_length=1)


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    age: int
    occupation: str
    is_active: bool


class SummaryResponse(BaseModel):
    profile: ProfileResponse
    financial_record_count: int
    active_goals: int
    habit_streak: int
