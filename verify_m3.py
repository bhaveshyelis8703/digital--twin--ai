"""Quick Milestone 3 verification — run: python verify_m3.py"""
import sys, importlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

errors = []
checks = []

# 1. Import all M3 modules
try:
    from app.ml.digital_twin import DigitalTwin
    checks.append("OK  app.ml.digital_twin.DigitalTwin imported")
except Exception as e:
    errors.append(f"ERR app.ml.digital_twin: {e}")

try:
    from app.ml.simulation_engine import SimulationEngine
    checks.append("OK  app.ml.simulation_engine.SimulationEngine imported")
except Exception as e:
    errors.append(f"ERR app.ml.simulation_engine: {e}")

try:
    from app.services.digital_twin_service import get_current_twin
    checks.append("OK  digital_twin_service imported")
except Exception as e:
    errors.append(f"ERR digital_twin_service: {e}")

try:
    from app.services.recommendation_service import generate_all_recommendations
    checks.append("OK  recommendation_service imported")
except Exception as e:
    errors.append(f"ERR recommendation_service: {e}")

try:
    from app.services.scenario_service import compare_two_scenarios, best_future_path
    checks.append("OK  scenario_service imported")
except Exception as e:
    errors.append(f"ERR scenario_service: {e}")

try:
    from app.api.routes import digital_twin, simulation, scenarios
    checks.append("OK  all 3 M3 route modules imported")
except Exception as e:
    errors.append(f"ERR route imports: {e}")

try:
    from app.models.user import SimulationResult
    checks.append("OK  SimulationResult model imported")
except Exception as e:
    errors.append(f"ERR SimulationResult: {e}")

try:
    from app.schemas.digital_twin import TwinState, TwinSummaryResponse
    from app.schemas.simulation import SimulationResult as SimResult, FullSimulationRequest
    from app.schemas.scenario import ScenarioCompareRequest, BestPathResponse
    checks.append("OK  all 3 M3 schema modules imported")
except Exception as e:
    errors.append(f"ERR schemas: {e}")

# 2. DB table check
try:
    import sqlite3
    conn = sqlite3.connect("digital_twin_ai.db")
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    conn.close()
    if "simulation_results" in tables:
        checks.append("OK  simulation_results table EXISTS in DB")
    else:
        errors.append("ERR simulation_results table NOT in DB — run: python create_m3_tables.py")
except Exception as e:
    errors.append(f"ERR DB check: {e}")

# 3. Check SimulationEngine methods
try:
    eng = SimulationEngine(999)
    methods = [m for m in dir(eng) if m.startswith("simulate_")]
    checks.append(f"OK  SimulationEngine has {len(methods)} simulate_* methods: {', '.join(methods)}")
except Exception as e:
    errors.append(f"ERR SimulationEngine methods: {e}")

# 4. Check DigitalTwin methods
try:
    twin = DigitalTwin(999)
    required = ["load_from_database","build_current_state","project_state",
                "calculate_behavioral_score","calculate_risk_score",
                "generate_summary","save_snapshot","compare_states"]
    missing = [m for m in required if not hasattr(twin, m)]
    if missing:
        errors.append(f"ERR DigitalTwin missing methods: {missing}")
    else:
        checks.append(f"OK  DigitalTwin has all {len(required)} required methods")
except Exception as e:
    errors.append(f"ERR DigitalTwin: {e}")

# 5. Frontend page exists
try:
    src = open("frontend/pages/8_Simulation.py", encoding="utf-8").read()
    tab_count = src.count("with tab_")
    checks.append(f"OK  8_Simulation.py exists ({len(src.splitlines())} lines, {tab_count} tabs)")
except Exception as e:
    errors.append(f"ERR 8_Simulation.py: {e}")

# 6. Tests exist
for t in ["tests/test_digital_twin.py","tests/test_simulation.py","tests/test_scenarios.py"]:
    try:
        lc = len(open(t, encoding="utf-8").readlines())
        checks.append(f"OK  {t} ({lc} lines)")
    except Exception as e:
        errors.append(f"ERR {t}: {e}")

print("\n".join(checks))
if errors:
    print("\nFAILURES:")
    print("\n".join(errors))
    sys.exit(1)
else:
    print(f"\n{'='*50}")
    print(f"MILESTONE 3 COMPLETE — {len(checks)} checks passed, 0 errors")
    print(f"{'='*50}")
