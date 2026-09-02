# Digital Twin AI — 10-Minute Demo Script

## Setup (before demo)
- Start the app: `Start App.bat` or `docker compose up`
- Log in with: `synthetic_259_ce036a08@example.com` / `demo123` (363 records of data)
- Open browser to `http://localhost:8501`

---

## Minute 1 — Register + Profile (if demo account not pre-loaded)

*Skip if using demo account. Otherwise:*

1. Navigate to Login page → "Create Account" tab
2. Fill: Name: "Alex Demo", Age: 28, Email: demo@example.com, Password: Demo1234!, Occupation: "Engineer"
3. Register → auto-redirected to Dashboard
4. **Talk point**: "The system creates a Digital Twin immediately — it's ready to learn."

---

## Minutes 2–3 — Financial Data + Analytics

1. Click **💰 Finance** in sidebar
2. Show: 5 KPI cards (Income, Expenses, Net Savings, Monthly Trend, Record count)
3. Show: 4 charts — Income vs Expenses, Spending by Category, Monthly Breakdown, Recurring Frequency
4. Show: Filter bar — filter by "expense" → CSV export
5. Click **📊 Analytics** → show the full API activity dashboard
6. **Talk point**: "Every interaction is logged — we can see API response times and usage patterns."

---

## Minutes 4–6 — Simulation + Scenario Comparison

1. Click **🧬 Simulation**
2. **Tab: Financial → Investment Growth**:
   - Initial: $10,000 | Monthly: $500 | Return: 8% | Horizon: 36 months
   - Click "Run" → show projected value ~$47,000
   - **Talk point**: "This uses compound interest formula with the user's real monthly capacity."
3. **Tab: Compare**:
   - Scenario A: "Save $200/mo extra"
   - Scenario B: "Study 2h extra/day"
   - Click "Compare Scenarios" → show radar chart + winner
   - **Talk point**: "The AI evaluates impact across all 5 life domains simultaneously."
4. **Tab: Recommendations** → show 8 prioritised actions
5. **Tab: Risk** → show risk heatmap

---

## Minutes 7–8 — Conversational AI (3 queries)

1. Click **🤖 AI Chat** in sidebar
2. **Query 1**: "Will I be able to save $50K in 3 years?"
   - Wait for response
   - Show: response references actual monthly savings figure
   - **Talk point**: "The AI uses real data — not generic advice."
3. **Query 2**: "What if I increase my savings rate to 30%?"
   - Show: AI calls `run_simulation` tool (tool chip visible)
   - **Talk point**: "The AI automatically decides when to call backend services."
4. **Query 3**: "What is my biggest financial risk?"
   - Show: AI calls `get_recommendations` tool
   - **Talk point**: "Safety filters prevent harmful advice — try asking about gambling."
5. Show: conversation history panel on the right

---

## Minutes 9–10 — Dashboard + PDF Export

1. Click **📈 Full Dashboard**
2. Change period selector: 1M → 1Y → 3Y → watch all 4 charts update simultaneously
3. Show: 5 KPI cards, savings projection with confidence band, radar chart
4. Click **📄 Reports** in sidebar
5. Select "Full Report" → click "Generate & Download"
6. Open the PDF → show: user name, financial summary, savings forecast table, goals, recommendations
7. **Comparison tab**: Period A: 1M, Period B: 1Y → "Compare Periods"
8. **Talk point**: "Every number in this PDF came directly from the database — no hardcoding."

---

## Key Demo Lines

- *"The Digital Twin scores you across 5 life domains and weighs them into a single alignment score."*
- *"Ask it anything — it knows your actual numbers."*
- *"All simulations run in under 100 milliseconds because we use deterministic formulas, not slow ML models at query time."*
- *"The PDF generates in under 1 second using your real data."*

---

## Contingency Notes

- If OpenAI key not set: AI falls back to rule-based responses using real data — still demonstrates the data-grounded approach
- If backend slow: use cached Streamlit state (data already loaded)
- If PDF fails: show the comparison view instead
