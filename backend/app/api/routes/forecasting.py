"""
backend/app/api/routes/forecasting.py
Financial forecasting endpoints.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.models.user import User

router = APIRouter()


class ScenarioRequest(BaseModel):
    savings_rate_change: float = Field(..., ge=0, le=1,
        description="Fraction of monthly income to save additionally (0.05 = 5% more)")
    months: int = Field(default=12, ge=1, le=36)


def _svc():
    """Lazy import so heavy ML libs only load when an endpoint is hit."""
    from app.services.forecasting_service import (
        generate_savings_projection,
        generate_expense_forecast,
        generate_cashflow_forecast,
        simulate_savings_rate_change,
    )
    return (generate_savings_projection, generate_expense_forecast,
            generate_cashflow_forecast, simulate_savings_rate_change)


@router.get("/savings", summary="Savings projection for next N months")
def savings_forecast(
    months: int = Query(default=12, ge=1, le=36,
                        description="Forecast horizon in months"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Prophet-based savings projection with confidence interval."""
    try:
        gen, *_ = _svc()
        result = gen(current_user.id, months)
        return {"user_id": current_user.id, "months": months, "forecast": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting error: {e}")


@router.get("/expenses", summary="Expense forecast by category")
def expense_forecast(
    category: str = Query(default="Food", description="Expense category to forecast"),
    months:   int = Query(default=6, ge=1, le=36),
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """XGBoost-based per-category expense forecast."""
    try:
        _, gen, *_ = _svc()
        result = gen(current_user.id, category, months)
        return {"user_id": current_user.id, "category": category,
                "months": months, "forecast": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting error: {e}")


@router.get("/cashflow", summary="Net cash-flow projection")
def cashflow_forecast(
    months: int = Query(default=6, ge=1, le=36),
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """ARIMA-based monthly net cash-flow forecast."""
    try:
        _, _, gen, _ = _svc()
        result = gen(current_user.id, months)
        return {"user_id": current_user.id, "months": months, "forecast": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting error: {e}")


@router.post("/scenario", summary="Simulate savings rate change impact")
def savings_scenario(
    body: ScenarioRequest,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Show how increasing savings rate by X% changes the 1-year projection."""
    try:
        _, _, _, sim = _svc()
        result = sim(current_user.id, body.savings_rate_change, body.months)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {e}")
