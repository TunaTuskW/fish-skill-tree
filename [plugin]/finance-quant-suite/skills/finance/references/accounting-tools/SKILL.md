---
name: accounting-tools
description: |
  Perform Excel spreadsheet data modeling, financial statement workbook creation, formula evaluation (XIRR, NPV, PMT), and multi-sheet consolidation.
  Trigger when:
  - User asks to create, modify, or inspect Excel files (.xlsx, .xls) for accounting or financial analysis.
  - User asks for financial formula modeling in spreadsheets (amortization schedules, DCF workbooks, cash flow forecasts, 3-statement models).
  - User needs to automate Excel data cleaning, pivot tables, or multi-workbook consolidation using Python (openpyxl, pandas, xlsxwriter).
  - User asks to evaluate or audit complex Excel formulas, named ranges, or circular references.
---

# Excel & Financial Data Modeling Skill

Runbooks and best practices for spreadsheet automation, financial formula modeling, and accounting data engineering.

## Core Workflows

### 1. Programmatic Excel Generation (`openpyxl` / `xlsxwriter`)
When generating or editing financial workbooks:
1. **Dynamic Formulas over Hardcoded Values**:
   - Always write live Excel formulas (`=SUM(B2:B12)`, `=NPV(C1, C4:C10)`, `=XIRR(D2:D20, A2:A20)`) into calculation cells rather than inserting precomputed static floats.
   - Separate raw inputs/assumptions, intermediate calculations, and summary financial outputs into distinct worksheets or visual sections.
2. **Standard Financial Formatting**:
   - Currency: `_($* #,##0.00_);_($* (#,##0.00);_($* "-"??_);_(@_)`
   - Percentage: `0.0%` or `0.00%`
   - Dates: `YYYY-MM-DD`
   - Highlight inputs in blue font (`#0000FF`) with soft background fills, and computed formulas in standard black font.
3. **Prevent Formula Reference Errors**:
   - Check cell coordinate bounds.
   - Ensure absolute vs. relative references (`$A$1` vs. `A1`) match the intended drag/repetition pattern.

### 2. Standard Financial & Accounting Models
- **3-Statement Modeling**:
  - Income Statement linked to Balance Sheet (Retained Earnings $\leftarrow$ Net Income $-$ Dividends).
  - Balance Sheet linked to Cash Flow Statement (Cash balance feeds ending Cash).
  - Working Capital schedules (DSO, DPO, DIO) driving Accounts Receivable and Accounts Payable.
- **Debt & Loan Amortization Schedule**:
  - Payment: `=-PMT(rate, nper, pv)`
  - Principal: `=-PPMT(rate, per, nper, pv)`
  - Interest: `=-IPMT(rate, per, nper, pv)`
  - Ending Balance: `Beginning Balance - Principal`
- **Investment Return Metrics**:
  - Net Present Value: `=NPV(discount_rate, value1, value2, ...) + initial_investment`
  - Irregular Cash Flow IRR: `=XIRR(cash_flows, dates)`

### 3. Tabular Accounting Data Consolidation
When joining or summarizing multi-tab or multi-file accounting data:
1. Load data via `pandas` or `openpyxl`.
2. Normalize column headers (strip trailing spaces, standardize case).
3. Merge datasets using primary keys (e.g., `account_id`, `cost_center`).
4. Generate summary Pivot Tables or Cross-tabs for variance reporting (Budget vs. Actual, MoM growth).
