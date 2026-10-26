---
name: financial-analysis
description: |
  Perform financial statement analysis, corporate valuation, equity research, and SEC filing reviews.
  Trigger when:
  - User asks to analyze financial statements (Income Statement, Balance Sheet, Cash Flow).
  - User asks for valuation models (DCF, comparable company analysis, EV/EBITDA, P/E multiples).
  - User asks to extract or summarize SEC filings (10-K, 10-Q, 8-K) or earnings releases.
  - User asks for portfolio performance metrics (Sharpe ratio, beta, volatility, drawdown).
---

# Financial Analysis & Valuation Skill

Frameworks and quantitative workflows for corporate finance, equity valuation, and financial document analysis.

## Core Workflows

### 1. Financial Statement Analysis & Ratio Decomposition
When evaluating a company's financial performance:
1. **Profitability & Margins**:
   - Gross Margin = $\frac{\text{Gross Profit}}{\text{Revenue}}$
   - Operating Margin = $\frac{\text{Operating Income (EBIT)}}{\text{Revenue}}$
   - Net Profit Margin = $\frac{\text{Net Income}}{\text{Revenue}}$
   - Free Cash Flow (FCF) = $\text{Operating Cash Flow} - \text{Capital Expenditures (CapEx)}$
2. **DuPont Analysis (ROE Decomposition)**:
   $$\text{ROE} = \left(\frac{\text{Net Income}}{\text{Revenue}}\right) \times \left(\frac{\text{Revenue}}{\text{Assets}}\right) \times \left(\frac{\text{Assets}}{\text{Equity}}\right)$$
   (Net Margin $\times$ Asset Turnover $\times$ Financial Leverage).
3. **Liquidity & Solvency**:
   - Current Ratio = $\frac{\text{Current Assets}}{\text{Current Liabilities}}$
   - Quick Ratio = $\frac{\text{Cash} + \text{Marketable Securities} + \text{Receivables}}{\text{Current Liabilities}}$
   - Net Debt = $(\text{Short-term Debt} + \text{Long-term Debt}) - \text{Cash \& Equivalents}$
   - Leverage = $\frac{\text{Net Debt}}{\text{EBITDA}}$

### 2. Discounted Cash Flow (DCF) Valuation
When building a DCF model:
1. **Forecast Unlevered Free Cash Flows (UFCF)**:
   $$\text{UFCF} = \text{EBIT} \times (1 - \text{Tax Rate}) + \text{D\&A} - \text{CapEx} - \Delta\text{Net Working Capital}$$
2. **Calculate WACC (Weighted Average Cost of Capital)**:
   $$\text{WACC} = \left(\frac{E}{V} \times K_e\right) + \left(\frac{D}{V} \times K_d \times (1 - t)\right)$$
   Where $K_e = R_f + \beta \times \text{ERP}$.
3. **Terminal Value (Gordon Growth vs. Exit Multiple)**:
   $$\text{Terminal Value} = \frac{\text{UFCF}_{N} \times (1 + g)}{\text{WACC} - g}$$
4. **Enterprise Value to Equity Value Bridge**:
   $$\text{Equity Value} = \text{Enterprise Value} - \text{Net Debt} - \text{Minority Interest} + \text{Investments}$$
   $$\text{Implied Share Price} = \frac{\text{Equity Value}}{\text{Diluted Shares Outstanding}}$$
5. Always generate a sensitivity table (varying WACC by $\pm 1\%$ and Terminal Growth $g$ by $\pm 0.5\%$).

### 3. SEC Filing Extraction (10-K & 10-Q)
When extracting information from annual or quarterly reports:
- **Item 1A (Risk Factors)**: Filter and highlight new risks introduced compared to previous filings, especially supply chain, legal, debt covenant, or regulatory risks.
- **Item 7 (MD&A)**: Summarize management's explanation of revenue drivers, margin contraction/expansion, segment performance, and capital allocation priorities.
- Clearly differentiate GAAP metrics from Non-GAAP (adjusted EBITDA, non-GAAP net income).
