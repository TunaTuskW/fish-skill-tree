---
name: finance
description: Master sector router for Finance, Accounting, Quant Math, Data Science (Polars/DuckDB), Corporate Valuation (DCF/LBO/Comps/3-Statement), and Prediction Market Analytics. When invoked, the agent automatically selects and loads the exact sub-playbooks needed.
metadata:
  origin: fish-coding-agent
---

# Finance, Quant & Prediction Market Sector Router (`/finance`)

You have activated the **Finance, Accounting, Quant & Prediction Market** sector.

## Autonomous Sub-Skill Selection Protocol (Agent-Driven Routing)

Do **NOT** load every sub-playbook at once. Analyze the user's request, decide which specific sub-modules below are required, and read **only** the matching `SKILL.md` and reference files inside `references/`:

| Sub-Domain | When to Select & Load | Path to Read |
| :--- | :--- | :--- |
| **1. Excel & Accounting Modeling** | Building/editing `.xlsx` workbooks, `XIRR`/`NPV`/`PMT` formulas, amortization, or multi-sheet consolidation | [`references/accounting-tools/SKILL.md`](references/accounting-tools/SKILL.md) |
| **2. 3-Statement Financial Model** | Linking integrated Income Statement, Balance Sheet, and Cash Flow Statement templates | [`references/3-statement-model/SKILL.md`](references/3-statement-model/SKILL.md) |
| **3. DCF Valuation** | Intrinsic equity valuation, WACC calculation, free cash flow projections, sensitivity matrices | [`references/dcf-model/SKILL.md`](references/dcf-model/SKILL.md) & [`scripts/validate_dcf.py`](scripts/validate_dcf.py) |
| **4. LBO Modeling** | Private equity leveraged buyouts, debt tranches, cash sweeps, IRR/MoIC returns | [`references/lbo-model/SKILL.md`](references/lbo-model/SKILL.md) |
| **5. Comparable Companies (Comps)** | Public peer benchmarking, EV/EBITDA, P/E multiples, valuation percentiles | [`references/comps-analysis/SKILL.md`](references/comps-analysis/SKILL.md) |
| **6. Spreadsheet Formula Audit** | Debugging `#REF!`/`#DIV/0!`, checking BS balance (`Assets = L + E`), and cash tie-outs | [`references/audit-xls/SKILL.md`](references/audit-xls/SKILL.md) |
| **7. Financial & SEC Analysis** | Analyzing 10-K/10-Q filings, GAAP vs. Non-GAAP reconciliation, Sharpe/beta/drawdown | [`references/financial-analysis/SKILL.md`](references/financial-analysis/SKILL.md) |
| **8. Billing & Revenue Ops** | Pricing, refunds, billing-model truth, and revenue operations | [`references/finance-billing-ops/SKILL.md`](references/finance-billing-ops/SKILL.md) |
| **9. Data Science & Analytics** | Querying datasets with Polars/DuckDB, OLS regression (Statsmodels), ML pipelines (Scikit-learn) | [`references/data-analytics/SKILL.md`](references/data-analytics/SKILL.md) |
| **10. Quantitative Math & Optimization** | Symbolic calculus/algebra (SymPy), numerical linear algebra (SciPy), convex optimization (CVXPY) | [`references/math-toolkit/SKILL.md`](references/math-toolkit/SKILL.md) |
| **11. Prediction Market Tickets** | Analyzing Polymarket/Jupiter/sports/esports lines and generating `[ticket#][sector][matchup][pick].md` | [`references/prediction-market-analytics/SKILL.md`](references/prediction-market-analytics/SKILL.md) & [`scripts/fetch_market_odds.py`](scripts/fetch_market_odds.py) |
| **12. Prediction Oracle & Risk Review** | Auditing oracle resolution signals, market-implied probabilities, and trading-agent risk | [`references/prediction-market-oracle-research/SKILL.md`](references/prediction-market-oracle-research/SKILL.md) & [`references/prediction-market-risk-review/SKILL.md`](references/prediction-market-risk-review/SKILL.md) |

## Execution Workflow
1. Identify the 1–3 relevant rows from the routing table above based on the user's goal.
2. State briefly which sub-modules you are activating (e.g., *"Activating `dcf-model` + `audit-xls`"*).
3. Read the corresponding `references/<sub-module>/SKILL.md` and execute its workflow end-to-end.
