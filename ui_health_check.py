import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))
import requests

BASE = "http://127.0.0.1:8000"
EMAIL = "bhaveshyelis2005@gmail.com"
PASSWORD = "bhavesh123"

OK = "OK "
FL = "FAIL"
results = []

def chk(label, ok, detail=""):
    tag = OK if ok else FL
    results.append((tag, label, detail))
    sym = "[OK]" if ok else "[FAIL]"
    print(f"  {sym}  {label}" + (f"  -> {detail}" if detail else ""))

print("\n=== Backend ===")
try:
    r = requests.get(f"{BASE}/health", timeout=5)
    chk("Backend running", r.status_code == 200)
except Exception as e:
    chk("Backend running", False, str(e))
    print("Cannot reach backend. Start it first.")
    sys.exit(1)

print("\n=== Auth ===")
token = None
try:
    r = requests.post(f"{BASE}/api/auth/login",
                      data={"username": EMAIL, "password": PASSWORD}, timeout=5)
    token = r.json().get("access_token")
    chk("POST /api/auth/login", r.status_code == 200 and bool(token), f"HTTP {r.status_code}")
except Exception as e:
    chk("POST /api/auth/login", False, str(e))

if not token:
    print("No token - all auth checks will fail")

H = {"Authorization": f"Bearer {token}"} if token else {}
AJ = {**H, "Content-Type": "application/json"}

def g(path, params=None, label=None):
    lbl = label or path
    try:
        r = requests.get(f"{BASE}{path}", headers=H, params=params, timeout=10)
        ok = r.status_code == 200
        try:
            b = r.json()
            d = f"HTTP {r.status_code}"
            if not ok:
                d += " " + str(b.get("detail",""))[:60]
            elif isinstance(b, list):
                d += f" [{len(b)} items]"
            elif isinstance(b, dict):
                d += " keys=" + str(list(b.keys())[:4])
        except Exception:
            d = f"HTTP {r.status_code}"
        chk(lbl, ok, d)
        return r.json() if ok else {}
    except Exception as e:
        chk(lbl, False, str(e)[:80])
        return {}

def p(path, payload, label=None):
    lbl = label or path
    try:
        r = requests.post(f"{BASE}{path}", headers=AJ, json=payload, timeout=10)
        ok = r.status_code in (200, 201)
        try:
            b = r.json()
            d = f"HTTP {r.status_code}"
            if not ok:
                d += " " + str(b.get("detail",""))[:60]
            elif isinstance(b, list):
                d += f" [{len(b)} items]"
            elif isinstance(b, dict):
                d += " keys=" + str(list(b.keys())[:4])
        except Exception:
            d = f"HTTP {r.status_code}"
        chk(lbl, ok, d)
        return r.json() if ok else {}
    except Exception as e:
        chk(lbl, False, str(e)[:80])
        return {}

print("\n=== Profile page ===")
g("/api/users/profile", label="GET /api/users/profile")
g("/api/users/summary", label="GET /api/users/summary")

print("\n=== Finance page ===")
g("/api/financial/records", label="GET /api/financial/records")
g("/api/financial/summary",  label="GET /api/financial/summary")
nr = p("/api/financial/records",
       {"record_type":"income","amount":100,"description":"healthcheck",
        "date":"2026-08-01T00:00:00","category":"test","recurring_frequency":"once"},
       label="POST /api/financial/records (add)")
if nr.get("id"):
    rid = nr["id"]
    r2 = requests.put(f"{BASE}/api/financial/records/{rid}",
                      headers=AJ, json={"amount":200}, timeout=5)
    chk("PUT  /api/financial/records/{id} (edit)", r2.status_code == 200, f"HTTP {r2.status_code}")
    r3 = requests.delete(f"{BASE}/api/financial/records/{rid}", headers=H, timeout=5)
    chk("DELETE /api/financial/records/{id}", r3.status_code == 204, f"HTTP {r3.status_code}")

print("\n=== Study page ===")
g("/api/study",                        label="GET /api/study")
g("/api/study/exam-readiness",         label="GET /api/study/exam-readiness")
g("/api/study/performance-prediction", label="GET /api/study/performance-prediction")
g("/api/study/trend",                  label="GET /api/study/trend")
p("/api/study/optimal-plan",
  {"target_score":80,"exam_date":"2026-10-01","subject":"Math"},
  label="POST /api/study/optimal-plan")

print("\n=== Habits & Fitness page ===")
g("/api/habits",                     label="GET /api/habits")
g("/api/habits/analysis",            label="GET /api/habits/analysis")
g("/api/habits/productivity-index",  label="GET /api/habits/productivity-index")
g("/api/habits/trend",               label="GET /api/habits/trend")
g("/api/habits/anomalies",           label="GET /api/habits/anomalies")
g("/api/fitness",                    label="GET /api/fitness")
g("/api/habits/fitness-goal-probability?days_to_goal=30",
  label="GET /api/habits/fitness-goal-probability")

print("\n=== Goals page ===")
g("/api/goals", label="GET /api/goals")
ng = p("/api/goals",
       {"name":"Health check goal","description":"test","target_value":100,
        "current_value":0,"target_date":"2027-01-01T00:00:00","status":"In Progress"},
       label="POST /api/goals (add)")
if ng.get("id"):
    r4 = requests.put(f"{BASE}/api/goals/{ng['id']}",
                      headers=AJ, json={"current_value":50}, timeout=5)
    chk("PUT /api/goals/{id} (update progress)", r4.status_code == 200, f"HTTP {r4.status_code}")
    r5 = requests.delete(f"{BASE}/api/goals/{ng['id']}", headers=H, timeout=5)
    chk("DELETE /api/goals/{id}", r5.status_code == 204, f"HTTP {r5.status_code}")

print("\n=== Analytics page ===")
g("/api/analytics/full",    label="GET /api/analytics/full")
g("/api/analytics/summary", label="GET /api/analytics/summary")
g("/api/analytics/logs",    label="GET /api/analytics/logs")

print("\n=== Forecasting page ===")
g("/api/forecasting/savings",  {"months":6},                       label="GET /api/forecasting/savings")
g("/api/forecasting/expenses", {"category":"Food","months":6},     label="GET /api/forecasting/expenses")
g("/api/forecasting/cashflow", {"months":6},                       label="GET /api/forecasting/cashflow")
p("/api/forecasting/scenario", {"savings_rate_change":0.1,"months":12},
  label="POST /api/forecasting/scenario")

print("\n=== Simulation page (Milestone 3) ===")
g("/api/digital-twin/summary",             label="GET /api/digital-twin/summary")
g("/api/digital-twin/risk",                label="GET /api/digital-twin/risk")
g("/api/digital-twin/snapshot",            label="GET /api/digital-twin/snapshot")
p("/api/digital-twin/recommendations", {}, label="POST /api/digital-twin/recommendations")
p("/api/digital-twin/create-snapshot", {"scenario_name":"healthcheck"},
  label="POST /api/digital-twin/create-snapshot")
p("/api/digital-twin/project", {"horizon_months":6},
  label="POST /api/digital-twin/project")
p("/api/simulation/financial",
  {"sim_type":"savings_increase","monthly_increase":200,"horizon_months":12},
  label="POST /api/simulation/financial  [savings_increase]")
p("/api/simulation/financial",
  {"sim_type":"investment_growth","initial_amount":10000,
   "monthly_contribution":200,"annual_return_pct":8,"horizon_months":24},
  label="POST /api/simulation/financial  [investment_growth]")
p("/api/simulation/financial",
  {"sim_type":"loan_impact","loan_amount":50000,
   "annual_interest_pct":10,"tenure_months":60},
  label="POST /api/simulation/financial  [loan_impact]")
p("/api/simulation/study",
  {"sim_type":"extra_hours","extra_hours_per_day":1,"horizon_weeks":8},
  label="POST /api/simulation/study     [extra_hours]")
p("/api/simulation/study",
  {"sim_type":"exam_prep","subject":"Math","days_until_exam":30,"target_score":85},
  label="POST /api/simulation/study     [exam_prep]")
p("/api/simulation/habits",
  {"sim_type":"new_habit","habit_name":"Morning Run","horizon_weeks":8},
  label="POST /api/simulation/habits    [new_habit]")
p("/api/simulation/habits",
  {"sim_type":"productivity","focus_improvement_pct":20,"horizon_weeks":8},
  label="POST /api/simulation/habits    [productivity]")
p("/api/simulation/fitness",
  {"sim_type":"workout_plan","sessions_per_week":3,
   "session_duration_minutes":45,"activity_type":"Running","horizon_weeks":8},
  label="POST /api/simulation/fitness   [workout_plan]")
p("/api/simulation/fitness",
  {"sim_type":"weight_loss","target_weekly_calories":1500,"horizon_weeks":12},
  label="POST /api/simulation/fitness   [weight_loss]")
p("/api/simulation/full",
  {"horizon_months":6,"financial_boost_pct":10,"study_hours_increase":1,
   "habit_compliance_target":80,"fitness_sessions_per_week":3},
  label="POST /api/simulation/full")
g("/api/simulation/history",  label="GET /api/simulation/history")
g("/api/scenarios/best-path", label="GET /api/scenarios/best-path")
p("/api/scenarios/compare",
  {"scenario_a":{"name":"Save More","sim_type":"financial.savings_increase",
                 "description":"","parameters":{"monthly_increase":200,"horizon_months":12}},
   "scenario_b":{"name":"Study More","sim_type":"study.extra_hours",
                 "description":"","parameters":{"extra_hours_per_day":1,"horizon_weeks":16}},
   "horizon_months":12,"domains":["financial","study","habits","fitness"]},
  label="POST /api/scenarios/compare")
p("/api/scenarios/risk-analysis",
  {"scenario":{"name":"Loan","sim_type":"financial.loan_impact","description":"",
               "parameters":{"loan_amount":50000,"annual_interest_pct":10,"tenure_months":60}},
   "horizon_months":12},
  label="POST /api/scenarios/risk-analysis")

# Summary
passed = sum(1 for r in results if r[0] == OK)
failed = sum(1 for r in results if r[0] == FL)
total  = len(results)

print(f"\n{'='*60}")
print(f"  TOTAL:  {passed}/{total} passed    {failed} FAILED")
print(f"{'='*60}")

if failed:
    print("\n  FAILED:")
    for tag, lbl, detail in results:
        if tag == FL:
            print(f"    [FAIL] {lbl}  ->  {detail}")
print()
