---
name: math-toolkit
description: |
  Perform rigorous symbolic math, calculus derivations, numerical linear algebra, and mathematical optimization using SymPy, SciPy, NumPy, and CVXPY.
  Trigger when:
  - User asks for mathematical derivations, calculus (integrals, derivatives, limits, series, ODEs/PDEs).
  - User asks for linear algebra computations (eigenvalues, eigenvectors, SVD, matrix rank, null space).
  - User asks to formulate and solve optimization problems (convex optimization, linear programming, quadratic programming with CVXPY or scipy.optimize).
  - User needs numerical simulation, Monte Carlo experiments, or statistical distribution modeling.
  - User requests rigorous mathematical proofs or LaTeX/KaTeX mathematical typesetting.
---

# Mathematics & Quantitative Computing Skill

Guidelines and computational workflows for applied mathematics, scientific computing, and formal derivations.

## Core Workflows

### 1. Symbolic Mathematics & Calculus (`SymPy`)
When deriving exact analytical solutions:
1. Define symbols and assumptions explicitly:
   ```python
   import sympy as sp
   x, y, t = sp.symbols('x y t', real=True)
   n = sp.symbols('n', integer=True, positive=True)
   ```
2. **Derivatives & Integrals**:
   - Compute exact derivatives: `sp.diff(expr, x)`
   - Compute indefinite or definite integrals: `sp.integrate(expr, (x, 0, sp.oo))`
3. **Differential Equations (ODEs)**:
   - Formulate differential equation: `eq = sp.Eq(f(t).diff(t, 2) + omega**2 * f(t), 0)`
   - Solve with boundary/initial conditions: `sp.dsolve(eq, f(t), ics={f(0): 0, f(t).diff(t).subs(t, 0): 1})`
4. Always provide the step-by-step mathematical derivation formatted in LaTeX/KaTeX alongside the code verification.

### 2. Numerical Linear Algebra (`NumPy` / `SciPy.linalg`)
For matrix analysis and numerical decomposition:
- **Eigenvalues & Eigenvectors**:
  ```python
  import numpy as np
  eigenvalues, eigenvectors = np.linalg.eig(A)
  ```
- **Singular Value Decomposition (SVD)**:
  ```python
  U, S, Vt = np.linalg.svd(A, full_matrices=False)
  ```
- **Matrix Conditioning**:
  - Check condition number `np.linalg.cond(A)` to flag ill-conditioned systems prior to inversion.
  - Never compute raw `np.linalg.inv(A)` when solving $Ax = b$; always use `np.linalg.solve(A, b)` or `scipy.linalg.lu_factor`.

### 3. Mathematical Optimization (`CVXPY` / `scipy.optimize`)
For constrained and unconstrained optimization:
1. **Convex Optimization with CVXPY**:
   ```python
   import cvxpy as cp
   x = cp.Variable(n)
   objective = cp.Minimize(0.5 * cp.quad_form(x, P) + q.T @ x)
   constraints = [A @ x == b, G @ x <= h, x >= 0]
   prob = cp.Problem(objective, constraints)
   prob.solve()
   print("Optimal value:", prob.value)
   print("Optimal x:", x.value)
   ```
2. Verify Disciplined Convex Programming (DCP) rules (`prob.is_dcp() == True`).
3. For non-linear unconstrained/constrained optimization, use `scipy.optimize.minimize` specifying the appropriate solver (`BFGS`, `L-BFGS-B`, `SLSQP`).

### 4. Mathematical Rigor & Proofs
- When presenting mathematical proofs, clearly state:
  - **Theorem / Proposition**: Formal statement of the claim.
  - **Assumptions**: Smoothness, continuity, domain, compactness, or dimension constraints.
  - **Step-by-step proof**: Logical deductive progression with intermediate lemmas.
  - **Edge cases / Counterexamples**: Boundaries where the theorem might fail if assumptions are violated.
