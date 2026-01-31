# Linear Programming via Regularized Least Squares

The **Linear Programming via Regularized Least Squares (LPPinv)** is a two-stage estimation method that reformulates linear programs as structured least-squares problems. Based on the [Convex Least Squares Programming (CLSP)](https://pypi.org/project/pyclsp/ "Convex Least Squares Programming") framework, LPPinv solves linear inequality, equality, and bound constraints by (1) constructing a canonical constraint system and computing a pseudoinverse projection, followed by (2) a convex-programming correction stage to refine the solution under additional regularization (e.g., Lasso, Ridge, or Elastic Net).
LPPinv is intended for **underdetermined** and **ill-posed** linear problems, for which standard solvers fail.
All calculations are performed in numpy.float64 precision.

## Installation

```bash
pip install pylppinv
```

## Quick Example

```python
import numpy  as     np
from   lppinv import lppinv

# LPRLS/QPRLS, based on an underdetermined and potentially infeasible problem

seed   = 123456789
rng    = np.random.default_rng(seed)

# sample (dataset)
A_ub   = rng.normal(size=(50, 500))                          # underdetermined LP/QP matrix
A_eq   = rng.normal(size=(25, 500))                          # underdetermined LP/QP matrix
b_ub   = rng.normal(size=(50,   1))                          # may be inconsistent with A_ub
b_eq   = rng.normal(size=(25,   1))                          # may be inconsistent with A_eq
model  = lppinv(
             A_ub=A_ub, A_eq=A_eq, b_ub=b_ub, b_eq=b_eq,
             non_negative=False,                             # allow negative values
             r=1,                                            # a solution without refinement
             alpha=1.0                                       # a unique MNBLUE estimator
         )

# results
# (for a summary, use result.summary(display=True))
print("x hat (x_M hat):")
print(np.round(model.x.flatten(), 4))

print("\nNumerical stability:")
print("  kappaC :", round(model.kappaC, 4))
print("  kappaB :", round(model.kappaB, 4))
print("  kappaA :", round(model.kappaA, 4))

print("\nGoodness-of-fit:")
print("  NRMSE                :", round(model.nrmse,              6))
print("  Diagnostic band (min):", np.round(np.min(model.x_lower), 4))
print("  Diagnostic band (max):", np.round(np.max(model.x_upper), 4))
print("  Bootstrap t-test:")
for kw, val in model.ttest(sample_size=30,                   # NRMSE sample
                           seed=seed, distribution="normal", # seed and distribution
               ).items():
    print(f"    {kw}: {float(val):.6f}")
```

## User Reference

For comprehensive information on the estimator’s capabilities, advanced configuration options, and implementation details, please refer to the [pyclsp module](https://pypi.org/project/pyclsp/ "Convex Least Squares Programming"), on which LPPinv is based.

**LPPINV Parameters:**

`c` : *array_like* of shape *(p,)*, optional<br>
Objective function coefficients. Accepted for API parity; not used by CLSP.

`A_ub` : *array_like* of shape *(i, p)*, optional<br>
Matrix for inequality constraints `A_ub @ x <= b_ub`.

`b_ub` : *array_like* of shape *(i,)*, optional<br>
Right-hand side vector for inequality constraints.

`A_eq` : *array_like* of shape *(j, p)*, optional<br>
Matrix for equality constraints `A_eq @ x = b_eq`.

`b_eq` : *array_like* of shape *(j,)*, optional<br>
Right-hand side vector for equality constraints.

`non_negative` : *bool*, default = *True*<br>
If False, no default nonnegativity is applied.

`bounds` : *sequence* of *(low, high)*, optional<br>
Bounds on variables. If a single tuple *(low, high)* is given, it is applied to all variables. If None, defaults to *(0, None)* for each variable (non-negativity).

`replace_value` : *float* or *None*, default = *np.nan*<br>
Final replacement value for any cell in the returned CLSP.x that violates the specified bounds by more than the given tolerance.

`tolerance` : *float*, default = *square root of machine epsilon*<br>
Convergence tolerance for bounds.

Please note that either `A_ub` and `b_ub` or `A_eq` and `b_eq` must be provided.

**CLSP Parameters:**
`final` : *bool*, default = *True*<br>
If *True*, a convex programming problem is solved to refine `zhat`. The resulting solution `z` minimizes a weighted L1/L2 norm around `zhat` subject to `Az = b`.

`alpha` : *float*, *list[float]* or *None*, default = *None*<br>
    Regularization parameter (weight) in the final convex program:<br>
    - `α = 0`: Lasso (L1 norm)<br>
    - `α = 1`: Tikhonov Regularization/Ridge (L2 norm)<br>
    - `0 < α < 1`: Elastic Net<br>
    If a scalar float is provided, that value is used after clipping to [0, 1].<br>
    If a list/iterable of floats is provided, each candidate is evaluated via a full solve, and the α with the smallest NRMSE is selected.<br>
    If None, α is chosen, based on an error rule: α = min(1.0, NRMSE_{α = 0} / (NRMSE_{α = 0} + NRMSE_{α = 1} + tolerance))

`*args`, `**kwargs` : optional<br>
CVXPY arguments passed to the CVXPY solver.

**Returns:**
*self*

`self.A`             : *np.ndarray*<br>
Design matrix `A` = [`C` | `S`; `M` | `Q`], where `Q` is either a zero matrix or *S_residual*.

`self.b`             : *np.ndarray*<br>
Vector of the right-hand side.

`self.zhat`          : *np.ndarray*<br>
Vector of the first-step estimate.

`self.r`             : *int*<br>
Number of refinement iterations performed in the first step.

`self.z`             : *np.ndarray*<br>
Vector of the final solution. If the second step is disabled, it equals `self.zhat`.

`self.x`             : *np.ndarray*<br>
`m × p` matrix or vector containing the variable component of `z`.

`self.y`             : *np.ndarray*<br>
Vector containing the slack component of `z`.

`self.kappaC`        : *float*<br>
Spectral κ() for *C_canon*.

`self.kappaB`        : *float*<br>
Spectral κ() for *B* = *C_canon^+ A*.

`self.kappaA`        : *float*<br>
Spectral κ() for `A`.

`self.rmsa`          : *float*<br>
Total root mean square alignment (RMSA).

`self.r2_partial`    : *float*<br>
R² for the `M` block in `A`.

`self.nrmse`         : *float*<br>
Mean square error calculated from `A` and normalized by standard deviation (NRMSE).

`self.nrmse_partial` : *float*<br>
Mean square error from the `M` block in `A` and normalized by standard deviation (NRMSE).

`self.z_lower`       : *np.ndarray*<br>
Lower bound of the diagnostic interval (confidence band) based on κ(`A`).

`self.z_upper`       : *np.ndarray*<br>
Upper bound of the diagnostic interval (confidence band) based on κ(`A`).

`self.x_lower`       : *np.ndarray*<br>
Lower bound of the diagnostic interval (confidence band) based on κ(`A`).

`self.x_upper`       : *np.ndarray*<br>
Upper bound of the diagnostic interval (confidence band) based on κ(`A`).

`self.y_lower`       : *np.ndarray*<br>
Lower bound of the diagnostic interval (confidence band) based on κ(`A`).

`self.y_upper`       : *np.ndarray*<br>
Upper bound of the diagnostic interval (confidence band) based on κ(`A`).

## Bibliography
Bolotov, I. (2025). CLSP: Linear Algebra Foundations of a Modular Two-Step Convex Optimization-Based Estimator for Ill-Posed Problems. *Mathematics*, *13*(21), 3476. [https://doi.org/10.3390/math13213476](https://doi.org/10.3390/math13213476)

## License

MIT License — see the [LICENSE](LICENSE) file.
