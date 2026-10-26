---
name: data-analytics
description: |
  High-speed data querying with DuckDB and Polars, statistical inference with Statsmodels, machine learning with Scikit-learn, and interactive chart reporting.
  Trigger when:
  - User asks to query, filter, aggregate, or join large CSV, Parquet, JSON, or Arrow files using DuckDB or Polars.
  - User asks for statistical analysis, hypothesis testing, OLS regression, ANOVA, or time-series modeling.
  - User asks for machine learning pipelines, cross-validation, feature engineering, or model evaluation with Scikit-learn.
  - User asks for Exploratory Data Analysis (EDA), distribution diagnostics, multicollinearity (VIF), or outlier detection.
  - User requests visual dashboards, interactive Plotly charts, or trend analysis from raw datasets.
---

# Modern Data Analytics & Data Science Skill

End-to-end workflows for high-performance data engineering, rigorous statistical modeling, and machine learning pipelines.

## Core Workflows

### 1. High-Performance Data Engineering (`DuckDB` + `Polars`)
Combine DuckDB for SQL data ingestion and Polars for columnar manipulation:
1. **Lazy Execution with Polars**:
   ```python
   import polars as pl

   # Scan lazily to optimize query plans and stream memory
   q = (
       pl.scan_parquet("data/*.parquet")
       .filter(pl.col("status") == "ACTIVE")
       .group_by("category")
       .agg([
           pl.col("amount").sum().alias("total_amount"),
           pl.col("amount").mean().alias("mean_amount"),
           pl.col("user_id").n_unique().alias("unique_users")
       ])
       .sort("total_amount", descending=True)
   )
   df = q.collect()
   ```
2. **DuckDB SQL OLAP Queries**:
   - Zero-copy query directly against Parquet or Polars DataFrames:
   ```python
   import duckdb
   result = duckdb.sql("""
       SELECT 
           date_trunc('month', timestamp) AS month,
           category,
           COUNT(*) AS tx_count,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount) AS median_amount
       FROM read_parquet('transactions/*.parquet')
       GROUP BY 1, 2
       ORDER BY 1, 3 DESC
   """).pl()  # Return directly as Polars DataFrame
   ```

### 2. Statistical Modeling & Hypothesis Testing (`Statsmodels` & `scipy.stats`)
Never rely solely on black-box predictions; analyze statistical significance:
1. **Ordinary Least Squares (OLS) & Multiple Regression**:
   ```python
   import statsmodels.api as sm
   import statsmodels.formula.api as smf

   model = smf.ols('target ~ feature1 + feature2 + C(category)', data=df).fit()
   print(model.summary())
   ```
2. **Regression Diagnostic Checks**:
   - **Normality of Residuals**: Jarque-Bera test ($p > 0.05$ indicates normality).
   - **Homoscedasticity**: Breusch-Pagan or White test for constant residual variance.
   - **Multicollinearity (VIF)**:
     - Variance Inflation Factor: $\text{VIF}_i = \frac{1}{1 - R_i^2}$. Flag predictors with $\text{VIF} > 5$ (severe collinearity).
3. **Hypothesis Testing**:
   - Two-sample comparison: Independent t-test (parametric) or Mann-Whitney U test (non-parametric if skewed).
   - Categorical independence: Chi-Square ($\chi^2$) test of independence.

### 3. Machine Learning & Predictive Modeling (`Scikit-Learn`)
Follow disciplined machine learning standards:
1. **Leak-Free Pipelines**:
   ```python
   from sklearn.pipeline import Pipeline
   from sklearn.compose import ColumnTransformer
   from sklearn.preprocessing import StandardScaler, OneHotEncoder
   from sklearn.impute import SimpleImputer
   from sklearn.model_selection import StratifiedKFold, cross_val_score
   from sklearn.ensemble import HistGradientBoostingClassifier

   num_transformer = Pipeline([('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler())])
   cat_transformer = Pipeline([('imputer', SimpleImputer(strategy='most_frequent')), ('ohe', OneHotEncoder(handle_unknown='ignore'))])

   preprocessor = ColumnTransformer([
       ('num', num_transformer, num_cols),
       ('cat', cat_transformer, cat_cols)
   ])

   pipeline = Pipeline([
       ('preprocessor', preprocessor),
       ('classifier', HistGradientBoostingClassifier(random_state=42))
   ])
   ```
2. **Model Evaluation & Metric Integrity**:
   - For imbalanced classification, report **PR-AUC (Precision-Recall AUC)**, **Brier Score**, and **F1-macro**, never plain accuracy.
   - For regression, report **RMSE**, **MAE**, and **$R^2$**, alongside a residual-vs-fitted plot.

### 4. Interactive Reporting & Visual Diagnostics (`Plotly` / `Seaborn`)
- Generate publication-quality plots:
  - Feature distributions (violin/box plots with quartile markings).
  - Calibration curves and Confusion matrices.
  - Correlation heatmaps with significance masks ($p < 0.05$).
