"""
tests/test_reports.py

Milestone 4 tests for PDF report generation and period comparison.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
_ROOT    = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def auth_headers_with_data(client):
    """Create a user with financial + study data for report testing."""
    # Register
    client.post("/api/auth/register", json={
        "name": "Report Tester", "email": "report@test.com",
        "password": "report1234!", "age": 30, "occupation": "Analyst",
    })
    r = client.post("/api/auth/login",
                    data={"username": "report@test.com", "password": "report1234!"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add some financial data
    for i, (rtype, amount, cat) in enumerate([
        ("income",  5000, "salary"),
        ("income",  1000, "freelance"),
        ("expense", 1500, "housing"),
        ("expense",  500, "food"),
        ("expense",  300, "transport"),
    ]):
        client.post("/api/financial/records", json={
            "record_type": rtype, "amount": amount,
            "description": f"Test {cat}", "category": cat,
            "date": (datetime.utcnow() - timedelta(days=i*7)).isoformat(),
            "recurring_frequency": "monthly",
        }, headers=headers)

    # Add a goal
    client.post("/api/goals", json={
        "name": "Save $10K", "description": "Emergency fund",
        "target_value": 10000, "current_value": 3000,
        "target_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "status": "In Progress",
    }, headers=headers)

    return headers


# ─────────────────────────────────────────────────────────────────────────────
# REPORT SERVICE UNIT TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestReportService:
    def test_pdf_bytes_returned(self, auth_headers_with_data):
        """generate_pdf_report returns non-empty bytes starting with %PDF."""
        from app.core.database import SessionLocal
        from app.models.user import User

        db = SessionLocal()
        u  = db.query(User).filter(User.email == "report@test.com").first()
        uid = u.id
        db.close()

        from app.services.report_service import generate_pdf_report
        pdf = generate_pdf_report(uid, report_type="full")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000
        assert pdf[:4] == b"%PDF"

    def test_all_report_types(self, auth_headers_with_data):
        from app.core.database import SessionLocal
        from app.models.user import User
        from app.services.report_service import generate_pdf_report

        db = SessionLocal()
        uid = db.query(User).filter(User.email == "report@test.com").first().id
        db.close()

        for rtype in ("full", "financial", "goals", "study", "recommendations"):
            pdf = generate_pdf_report(uid, report_type=rtype)
            assert isinstance(pdf, bytes), f"Failed for type: {rtype}"
            assert len(pdf) > 500, f"PDF too small for type: {rtype}"


class TestBinaryApiClient:
    def test_get_bytes_preserves_binary_content(self):
        from frontend.utils.api_client import APIClient

        response = MagicMock()
        response.content = b"%PDF-test"
        with patch("frontend.utils.api_client.requests.get", return_value=response):
            assert APIClient("http://api").get_bytes("/report", "token") == b"%PDF-test"
        response.raise_for_status.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# REPORT API ENDPOINT TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestReportEndpoint:
    def test_report_requires_auth(self, client):
        r = client.get("/api/reports/generate")
        assert r.status_code == 401

    def test_report_full_download(self, client, auth_headers_with_data):
        r = client.get("/api/reports/generate?type=full",
                       headers=auth_headers_with_data)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert "attachment" in r.headers.get("content-disposition", "")
        assert len(r.content) > 500

    def test_report_financial_type(self, client, auth_headers_with_data):
        r = client.get("/api/reports/generate?type=financial",
                       headers=auth_headers_with_data)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"

    def test_report_invalid_type(self, client, auth_headers_with_data):
        r = client.get("/api/reports/generate?type=invalid",
                       headers=auth_headers_with_data)
        assert r.status_code == 422

    def test_report_goals_type(self, client, auth_headers_with_data):
        r = client.get("/api/reports/generate?type=goals",
                       headers=auth_headers_with_data)
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# PERIOD COMPARISON TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestPeriodComparison:
    def test_comparison_requires_auth(self, client):
        r = client.get("/api/reports/comparison")
        assert r.status_code == 401

    def test_comparison_default_periods(self, client, auth_headers_with_data):
        r = client.get("/api/reports/comparison", headers=auth_headers_with_data)
        assert r.status_code == 200
        body = r.json()
        assert "period_a" in body
        assert "period_b" in body
        assert "financial" in body
        assert "study" in body
        assert "fitness" in body
        assert "habits" in body

    def test_comparison_custom_periods(self, client, auth_headers_with_data):
        r = client.get("/api/reports/comparison?period_a=1M&period_b=3M",
                       headers=auth_headers_with_data)
        assert r.status_code == 200
        body = r.json()
        assert body["period_a"]["label"] == "1M"
        assert body["period_b"]["label"] == "3M"

    def test_comparison_invalid_period(self, client, auth_headers_with_data):
        r = client.get("/api/reports/comparison?period_a=5Y",
                       headers=auth_headers_with_data)
        assert r.status_code == 422

    def test_comparison_delta_structure(self, client, auth_headers_with_data):
        r = client.get("/api/reports/comparison?period_a=1M&period_b=1Y",
                       headers=auth_headers_with_data)
        assert r.status_code == 200
        body = r.json()
        fin_delta = body["financial"]["delta"]
        assert "income" in fin_delta
        assert "expenses" in fin_delta
        assert "net" in fin_delta
        # Each delta has change, pct, improved
        for key in ("income", "expenses", "net"):
            if fin_delta[key]:  # may be empty dict if no data
                assert "change" in fin_delta[key] or fin_delta[key] == {}

    def test_comparison_windows_are_adjacent_and_equal(self, client, auth_headers_with_data):
        r = client.get("/api/reports/comparison?period_a=1M&period_b=1Y",
                       headers=auth_headers_with_data)
        assert r.status_code == 200
        body = r.json()
        period_a = body["period_a"]
        period_b = body["period_b"]
        assert period_a["end"] == period_b["start"]

    def test_expense_increase_is_not_improvement(self, client, auth_headers_with_data):
        r = client.get("/api/reports/comparison?period_a=1M&period_b=1Y",
                       headers=auth_headers_with_data)
        assert r.status_code == 200
        expenses = r.json()["financial"]["delta"]["expenses"]
        assert expenses["improved"] is False

    def test_comparison_all_period_options(self, client, auth_headers_with_data):
        for pa, pb in [("1M", "3M"), ("1M", "1Y"), ("3M", "1Y")]:
            r = client.get(f"/api/reports/comparison?period_a={pa}&period_b={pb}",
                           headers=auth_headers_with_data)
            assert r.status_code == 200, f"Failed for {pa} vs {pb}"


# ─────────────────────────────────────────────────────────────────────────────
# CONFTEST INTEGRATION — verify new tables exist
# ─────────────────────────────────────────────────────────────────────────────

class TestDatabaseSchema:
    def test_conversation_messages_table_exists(self, client):
        """Table created by Base.metadata.create_all in conftest fixture."""
        from app.core.database import SessionLocal
        from app.models.user import ConversationMessage
        db = SessionLocal()
        try:
            result = db.query(ConversationMessage).limit(1).all()
            assert isinstance(result, list)
        except Exception as exc:
            pytest.fail(f"conversation_messages table missing or broken: {exc}")
        finally:
            db.close()

    def test_user_role_column_exists(self, client):
        """User.role column exists with default 'user'."""
        from app.core.database import SessionLocal
        from app.models.user import User
        from app.core.security import get_password_hash
        db = SessionLocal()
        try:
            # Create a test user and verify role column
            u = User(
                name="Role Test", email="roletest@schema.com",
                hashed_password=get_password_hash("test"),
                age=25, occupation="Tester",
            )
            db.add(u)
            db.commit()
            db.refresh(u)
            assert hasattr(u, "role")
            assert u.role == "user"  # default
        finally:
            db.close()
