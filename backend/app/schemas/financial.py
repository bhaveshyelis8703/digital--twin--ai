from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FinancialRecordCreate(BaseModel):
    record_type: str = Field(..., pattern="^(income|expense)$")
    amount: float = Field(..., gt=0)
    description: str = Field(..., min_length=1)
    date: datetime
    category: str = Field(..., min_length=1)
    recurring_frequency: str = Field(..., min_length=1)
    goal_impact: str | None = None


class FinancialRecordUpdate(BaseModel):
    record_type: str | None = Field(default=None, pattern="^(income|expense)$")
    amount: float | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, min_length=1)
    date: datetime | None = None
    category: str | None = Field(default=None, min_length=1)
    recurring_frequency: str | None = Field(default=None, min_length=1)
    goal_impact: str | None = None


class FinancialRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    record_type: str
    amount: float
    description: str
    date: datetime
    category: str
    recurring_frequency: str
    goal_impact: str | None = None
    created_at: datetime
    updated_at: datetime


class FinancialSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_savings: float
    monthly_trend: float
