from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.models.user import FinancialRecord, User
from app.schemas.financial import FinancialRecordCreate, FinancialRecordResponse, FinancialRecordUpdate, FinancialSummary

router = APIRouter()


@router.post("/records", response_model=FinancialRecordResponse, status_code=status.HTTP_201_CREATED)
def create_financial_record(
    payload: FinancialRecordCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> FinancialRecordResponse:
    record = FinancialRecord(
        user_id=current_user.id,
        record_type=payload.record_type,
        amount=payload.amount,
        description=payload.description,
        date=payload.date,
        category=payload.category,
        recurring_frequency=payload.recurring_frequency,
        goal_impact=payload.goal_impact,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return FinancialRecordResponse.model_validate(record)


@router.get("/records", response_model=list[FinancialRecordResponse])
def list_financial_records(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    category: str | None = None,
    record_type: str | None = None,
) -> list[FinancialRecordResponse]:
    query = db.query(FinancialRecord).filter(FinancialRecord.user_id == current_user.id)
    if category:
        query = query.filter(FinancialRecord.category == category)
    if record_type:
        query = query.filter(FinancialRecord.record_type == record_type)
    return [FinancialRecordResponse.model_validate(item) for item in query.order_by(FinancialRecord.date.desc()).all()]


@router.get("/records/{record_id}", response_model=FinancialRecordResponse)
def get_financial_record(
    record_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> FinancialRecordResponse:
    record = db.query(FinancialRecord).filter(FinancialRecord.id == record_id, FinancialRecord.user_id == current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Financial record not found")
    return FinancialRecordResponse.model_validate(record)


@router.put("/records/{record_id}", response_model=FinancialRecordResponse)
def update_financial_record(
    record_id: int,
    payload: FinancialRecordUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> FinancialRecordResponse:
    record = db.query(FinancialRecord).filter(FinancialRecord.id == record_id, FinancialRecord.user_id == current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Financial record not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return FinancialRecordResponse.model_validate(record)


@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_financial_record(
    record_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> None:
    record = db.query(FinancialRecord).filter(FinancialRecord.id == record_id, FinancialRecord.user_id == current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Financial record not found")
    db.delete(record)
    db.commit()


@router.get("/summary", response_model=FinancialSummary)
def get_financial_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> FinancialSummary:
    records = db.query(FinancialRecord).filter(FinancialRecord.user_id == current_user.id).all()
    total_income = sum(r.amount for r in records if r.record_type == "income")
    total_expenses = sum(r.amount for r in records if r.record_type == "expense")
    monthly_trend = total_income - total_expenses
    return FinancialSummary(
        total_income=total_income,
        total_expenses=total_expenses,
        net_savings=total_income - total_expenses,
        monthly_trend=monthly_trend,
    )
