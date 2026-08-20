from fastapi.testclient import TestClient


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_registration_login_and_profile(client: TestClient):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "password123",
            "age": 30,
            "occupation": "Engineer",
        },
    )
    assert response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        data={"username": "alice@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    profile_response = client.get("/api/users/profile", headers={"Authorization": f"Bearer {token}"})
    assert profile_response.status_code == 200
    assert profile_response.json()["name"] == "Alice"


def test_financial_crud_and_summary(client: TestClient):
    register = client.post(
        "/api/auth/register",
        json={"name": "Bob", "email": "bob@example.com", "password": "password123", "age": 26, "occupation": "Designer"},
    )
    token = client.post(
        "/api/auth/login",
        data={"username": "bob@example.com", "password": "password123"},
    ).json()["access_token"]

    record_response = client.post(
        "/api/financial/records",
        json={
            "record_type": "income",
            "amount": 1200,
            "description": "Salary",
            "date": "2026-08-01T00:00:00",
            "category": "Salary",
            "recurring_frequency": "Monthly",
            "goal_impact": "Savings",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert record_response.status_code == 201

    summary = client.get("/api/financial/summary", headers={"Authorization": f"Bearer {token}"})
    assert summary.status_code == 200
    assert summary.json()["total_income"] == 1200


def test_registration_allows_blank_occupation(client: TestClient):
    response = client.post(
        "/api/auth/register",
        json={"name": "Dana", "email": "dana@example.com", "password": "password123", "age": 28, "occupation": ""},
    )
    assert response.status_code == 201
    assert response.json()["occupation"] == ""


def test_other_cruds(client: TestClient):
    register = client.post(
        "/api/auth/register",
        json={"name": "Cara", "email": "cara@example.com", "password": "password123", "age": 29, "occupation": "Teacher"},
    )
    token = client.post(
        "/api/auth/login",
        data={"username": "cara@example.com", "password": "password123"},
    ).json()["access_token"]

    study = client.post(
        "/api/study",
        json={"subject": "Math", "study_date": "2026-08-02T00:00:00", "study_hours": 2.5, "focus_score": 85, "task_completion": 90, "performance_score": 88},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert study.status_code == 201

    habit = client.post(
        "/api/habits",
        json={"name": "Meditate", "target_frequency": "Daily", "completed": True, "streak": 3},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert habit.status_code == 201

    fitness = client.post(
        "/api/fitness",
        json={"activity_type": "Running", "duration": 30, "calories_burned": 250, "activity_date": "2026-08-03T00:00:00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert fitness.status_code == 201

    goal = client.post(
        "/api/goals",
        json={"name": "Save", "description": "Build savings", "target_value": 5000, "current_value": 1000, "target_date": "2026-12-31T00:00:00", "status": "On Track"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert goal.status_code == 201

    logs = client.get("/api/analytics/activity-log", headers={"Authorization": f"Bearer {token}"})
    assert logs.status_code == 200
