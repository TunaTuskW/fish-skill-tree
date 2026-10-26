# Finance, Accounting, Quant, Data Science & Prediction Market Rules

## 1. Excel & Financial Modeling Integrity
- **Formula Integrity**: Always write native spreadsheet formulas (`=SUM(...)`, `=INDEX/MATCH`, etc.) for computed outputs so users can inspect calculation trails in Excel. Never paste hardcoded figures into calculated cells.
- **Explicit Assumptions Block**: Clearly isolate macroeconomic and financial assumptions (WACC, discount rates, tax rates, terminal growth rates, margins) into a dedicated "Assumptions" sheet or header block.
- **Format Consistency**: Enforce standard accounting formatting (two decimal places, currency symbols, negative numbers in parentheses) and distinguish GAAP metrics from Non-GAAP adjustments.
- **Regulatory Disclaimer**: Note that financial and valuation analyses are quantitative evaluations, not personalized investment, legal, or tax advice.

## 2. Quantitative Rigor & Data Science Standards
- **Zero Data Leakage**: Encapsulate all scaling, encoding, and imputation inside `Pipeline` or cross-validation folds—never fit transformers on the full dataset before splitting.
- **Statistical Significance**: Always report sample size ($N$), degrees of freedom, 95% confidence intervals, and explicit $p$-values alongside regression or hypothesis test results.
- **Performance-First Processing**: Default to Polars LazyFrames (`pl.scan_parquet` / `pl.scan_csv`) or DuckDB SQL for datasets exceeding 100,000 rows or 50MB.
- **Mathematical Exactness**: State domains of validity and convergence conditions; verify analytical derivations with `SymPy`/`SciPy` and typeset formulas in clean KaTeX/LaTeX (`$...$` / `$$...$$`).

## 3. Prediction Market Analytics & Ticket Standard
- **Strictly Unbiased Two-Sided Analysis**: Articulate realistic tactical win conditions for BOTH sides, include a dedicated `Pick Risk` section detailing failure states, and evaluate expected value relative to market price (pts/cents).
- **Standard Ticket Format & Naming**: Follow the exact `BLUF` / `Two-Sided Breakdown` / `Pick Risk` / `Key Player Matchups` ticket structure and save tickets as `[ticket#{number}][sector][matchup][pick].md`.

## 4. Mandatory Exports Mirror
- Whenever any Excel workbook (`.xlsx`), financial model, dataset, mathematical simulation, or prediction ticket is generated or updated, ALWAYS save or copy a duplicate into `~/vibe/` following the project subdirectory taxonomy.
