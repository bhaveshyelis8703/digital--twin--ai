import ast, os, sys

files = [
    # backend core
    'backend/main.py',
    'backend/app/models/user.py',
    'backend/app/schemas/digital_twin.py',
    'backend/app/schemas/simulation.py',
    'backend/app/schemas/scenario.py',
    # ML
    'backend/app/ml/digital_twin.py',
    'backend/app/ml/simulation_engine.py',
    # services
    'backend/app/services/digital_twin_service.py',
    'backend/app/services/recommendation_service.py',
    'backend/app/services/scenario_service.py',
    # routes
    'backend/app/api/routes/digital_twin.py',
    'backend/app/api/routes/simulation.py',
    'backend/app/api/routes/scenarios.py',
    # frontend
    'frontend/pages/2_Financial.py',
    'frontend/pages/8_Simulation.py',
    'frontend/components/ui.py',
    # tests
    'tests/test_digital_twin.py',
    'tests/test_simulation.py',
    'tests/test_scenarios.py',
]

results = []
errors  = []

for f in files:
    try:
        src = open(f, encoding='utf-8').read()
        ast.parse(src)
        lc = src.count('\n')
        results.append(f'OK   {lc:>4}L  {f}')
    except FileNotFoundError:
        errors.append(f'MISSING       {f}')
    except SyntaxError as e:
        errors.append(f'SYNTAX ERR    {f}  line {e.lineno}: {e.msg}')

for r in results:
    print(r)
if errors:
    print()
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print(f'\nAll {len(results)} files OK')
