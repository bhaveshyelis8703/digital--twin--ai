"""
Quick test: login as ramprasad and call all forecasting endpoints.
Run: .venv\Scripts\python.exe test_forecasting.py
"""
import json
import sys
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8000"

def call(path, token=None, method="GET", body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"HTTP_ERROR": e.code, "detail": e.read().decode()}
    except Exception as e:
        return {"ERROR": str(e)}

# 1. Login
print("=" * 55)
print("Testing forecasting endpoints for ramprasad16007@gmail.com")
print("=" * 55)

form_data = urllib.parse.urlencode({
    "username": "ramprasad16007@gmail.com",
    "password": "12345678"
}).encode()
req = urllib.request.Request(
    BASE + "/api/auth/login",
    data=form_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
try:
    resp = urllib.request.urlopen(req, timeout=10)
    token = json.loads(resp.read())["access_token"]
    print("[OK] Login successful")
except Exception as e:
    print(f"[FAIL] Login failed: {e}")
    sys.exit(1)

# 2. Check user data counts
print("\n--- Data in DB ---")
profile = call("/api/users/profile", token)
print(f"User: {profile.get('name')} | id={profile.get('id')}")

fin = call("/api/financial/records", token)
print(f"Financial records : {len(fin) if isinstance(fin, list) else fin}")

study = call("/api/study", token)
print(f"Study sessions    : {len(study) if isinstance(study, list) else study}")

habits = call("/api/habits", token)
print(f"Habits            : {len(habits) if isinstance(habits, list) else habits}")

fitness = call("/api/fitness", token)
print(f"Fitness activities: {len(fitness) if isinstance(fitness, list) else fitness}")

# 3. Test forecasting endpoints
print("\n--- Forecasting Endpoints ---")

savings = call("/api/forecasting/savings?months=6", token)
fc = savings.get("forecast", [])
print(f"[savings]  {len(fc)} data points | first={fc[0] if fc else 'EMPTY'}")

expenses = call("/api/forecasting/expenses?category=Food&months=6", token)
exp_fc = expenses.get("forecast", [])
print(f"[expenses] {len(exp_fc)} data points | first={exp_fc[0] if exp_fc else 'EMPTY'}")

cashflow = call("/api/forecasting/cashflow?months=6", token)
cf_fc = cashflow.get("forecast", [])
print(f"[cashflow] {len(cf_fc)} data points | first={cf_fc[0] if cf_fc else 'EMPTY'}")

scenario = call("/api/forecasting/scenario", token, method="POST",
                body={"savings_rate_change": 0.1, "months": 12})
proj = scenario.get("monthly_projection", [])
print(f"[scenario] {len(proj)} data points | extra_1yr={scenario.get('total_extra_1yr')}")

# 4. Study endpoints
print("\n--- Study Endpoints ---")

readiness = call("/api/study/exam-readiness", token)
print(f"[exam-readiness] RAW: {readiness}")

perf = call("/api/study/performance-prediction", token)
print(f"[performance-pred] RAW: {perf}")

trend = call("/api/study/trend", token)
print(f"[trend] RAW: {trend}")

# 5. Habit endpoints
print("\n--- Habit Endpoints ---")

prod = call("/api/habits/productivity-index", token)
print(f"[productivity] RAW: {prod}")

analysis = call("/api/habits/analysis", token)
print(f"[analysis] RAW: {analysis}")

hab_trend = call("/api/habits/trend", token)
print(f"[habit-trend] RAW: {hab_trend}")

anomalies = call("/api/habits/anomalies", token)
anom = anomalies.get("anomalies", [])
print(f"[anomalies]     {len(anom)} detected")

print("\n" + "=" * 55)
print("DONE - if all show data, the UI should display correctly.")
print("=" * 55)
