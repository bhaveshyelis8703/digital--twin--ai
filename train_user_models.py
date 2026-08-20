"""
train_user_models.py
====================
Trains per-user Prophet, XGBoost, and ARIMA forecasting models for every
user in the database who has sufficient financial data.

Usage
-----
    python train_user_models.py                 # all users
    python train_user_models.py --user-id 2     # single user
    python train_user_models.py --min-records 5 # custom data threshold

Models saved to: ml_models/trained/
  savings_prophet_user_{id}.pkl
  expense_xgb_user_{id}.pkl
  cashflow_arima_user_{id}.pkl
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# ── path bootstrap ────────────────────────────────────────────────────────────
_ROOT    = Path(__file__).resolve().parent
_BACKEND = _ROOT / "backend"
_ML      = _ROOT / "ml"
_MODELS  = _ROOT / "ml_models" / "trained"
_MODELS.mkdir(parents=True, exist_ok=True)

for _p in [str(_ROOT), str(_BACKEND), str(_ML)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _get_all_users(min_records: int) -> list[tuple[int, str, int]]:
    """Return [(user_id, email, record_count)] for users with enough data."""
    from app.core.database import SessionLocal
    from app.models.user import FinancialRecord, User

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        result = []
        for u in users:
            count = db.query(FinancialRecord).filter(
                FinancialRecord.user_id == u.id
            ).count()
            if count >= min_records:
                result.append((u.id, u.email, count))
        return result
    finally:
        db.close()


def train_prophet(user_id: int) -> dict:
    from ml.financial_forecasting import train_and_save_prophet_for_user
    try:
        return train_and_save_prophet_for_user(user_id)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def train_xgb(user_id: int) -> dict:
    from ml.financial_forecasting import train_expense_xgb
    try:
        return train_expense_xgb(user_id)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def train_arima(user_id: int) -> dict:
    from ml.financial_forecasting import train_cashflow_arima
    try:
        return train_cashflow_arima(user_id)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def train_for_user(user_id: int, email: str, record_count: int) -> None:
    print(f"\n{'─'*60}")
    print(f"  User  : {email} (id={user_id}, records={record_count})")
    print(f"{'─'*60}")

    # ── Prophet (savings) ─────────────────────────────────────────────────────
    print("  [1/3] Training Prophet savings model...", end=" ", flush=True)
    t0 = time.time()
    r = train_prophet(user_id)
    elapsed = time.time() - t0
    if r.get("status") == "ok":
        m = r.get("metrics", {})
        print(f"OK  ({elapsed:.1f}s)  MAE=${m.get('MAE',0):,.0f}  MAPE={m.get('MAPE',0):.1f}%")
    else:
        print(f"SKIP — {r.get('status','?')} {r.get('error','')}")

    # ── XGBoost (expenses) ────────────────────────────────────────────────────
    print("  [2/3] Training XGBoost expense model...", end=" ", flush=True)
    t0 = time.time()
    r = train_xgb(user_id)
    elapsed = time.time() - t0
    if r.get("status") == "ok":
        m = r.get("metrics", {})
        print(f"OK  ({elapsed:.1f}s)  MAPE={m.get('MAPE',0):.1f}%  RMSE={m.get('RMSE',0):.1f}")
    else:
        print(f"SKIP — {r.get('status','?')} {r.get('error','')}")

    # ── ARIMA (cashflow) ──────────────────────────────────────────────────────
    print("  [3/3] Training ARIMA cashflow model...", end=" ", flush=True)
    t0 = time.time()
    r = train_arima(user_id)
    elapsed = time.time() - t0
    if r.get("status") == "ok":
        m = r.get("metrics", {})
        print(f"OK  ({elapsed:.1f}s)  order={r.get('order')}  MAPE={m.get('MAPE',0):.1f}%")
    else:
        print(f"SKIP — {r.get('status','?')} {r.get('error','')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train per-user forecasting models")
    parser.add_argument("--user-id",     type=int, default=None,
                        help="Train for a single user ID only")
    parser.add_argument("--min-records", type=int, default=4,
                        help="Minimum financial records required (default: 4)")
    args = parser.parse_args()

    print("\n" + "═" * 60)
    print("  Digital Twin AI — User Model Training")
    print("  Models → ml_models/trained/")
    print("═" * 60)

    if args.user_id:
        # Single-user mode
        from app.core.database import SessionLocal
        from app.models.user import FinancialRecord, User
        db = SessionLocal()
        try:
            u = db.query(User).filter(User.id == args.user_id).first()
            if not u:
                print(f"\nERROR: user id={args.user_id} not found.")
                sys.exit(1)
            count = db.query(FinancialRecord).filter(
                FinancialRecord.user_id == u.id
            ).count()
        finally:
            db.close()
        train_for_user(u.id, u.email, count)
    else:
        # All eligible users
        users = _get_all_users(args.min_records)
        if not users:
            print(f"\nNo users found with ≥{args.min_records} financial records.")
            print("Add some financial data first, then re-run this script.")
            sys.exit(0)

        print(f"\nFound {len(users)} user(s) with ≥{args.min_records} records:\n")
        for uid, email, cnt in users:
            print(f"  id={uid:>4}  records={cnt:>4}  {email}")

        total_start = time.time()
        for uid, email, cnt in users:
            train_for_user(uid, email, cnt)

        elapsed = time.time() - total_start
        print(f"\n{'═'*60}")
        print(f"  Done — trained models for {len(users)} user(s) in {elapsed:.1f}s")
        print(f"  Models saved to: {_MODELS}")
        print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
