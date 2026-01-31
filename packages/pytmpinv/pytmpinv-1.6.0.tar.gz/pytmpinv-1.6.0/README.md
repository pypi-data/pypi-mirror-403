# Tabular Matrix Problems via Pseudoinverse Estimation

The **Tabular Matrix Problems via Pseudoinverse Estimation (TMPinv)** is a two-stage estimation method that reformulates structured table-based systems — such as allocation problems, transaction matrices, and input–output tables — as structured least-squares problems. Based on the [Convex Least Squares Programming (CLSP)](https://pypi.org/project/pyclsp/ "Convex Least Squares Programming") framework, TMPinv solves systems with row and column constraints, block structure, and optionally reduced dimensionality by (1) constructing a canonical constraint form and applying a pseudoinverse-based projection, followed by (2) a convex-programming refinement stage to improve fit, coherence, and regularization (e.g., via Lasso, Ridge, or Elastic Net). All calculations are performed in numpy.float64 precision.

## Installation

```bash
pip install tmpinv
```

## Quick Example

```python
import numpy             as     np
from   tmpinv            import tmpinv
import matplotlib.pyplot as     plt

# AP (TM), based on a symmetric input-output table, with 10% of known values

seed   = 123456789
rng    = np.random.default_rng(seed)

# sample (dataset)
m, p   = 20, 20                                              # matrix dimensions (m x p)
X_true = np.abs(rng.normal(size=(m, p)))                     # symmetric non-negative X_true
X_true = (X_true + X_true.T) / 2.0
idx    = rng.choice(m * p, size=max(1, int(0.1 * (m * p))),  # random numbers from
                    replace=False)                           # [0,(m * p) - 1], 10% of total

# model
M      = np.eye(m * p)[idx,:]                                # unit matrix
b_row  = X_true.sum(axis=1)                                  # row sums (length m)
b_col  = X_true.sum(axis=0)                                  # column sums (length p)
b_val  = X_true.reshape(-1, 1)[idx]                          # column vector
bounds = (0, None)                                           # non-negativity
result = tmpinv(
             M=M, b_row=b_row, b_col=b_col, b_val=b_val,
             m=m, p=p, bounds=bounds, symmetric=True,
             r=1,                                            # a solution without refinement
             alpha=1.0                                       # a unique MNBLUE estimator
         )

# helpers
def fmt(v):
    v = float(v)
    return f"{v:.4e}" if abs(v) >= 1e6 or (v != 0 and abs(v) < 1e-4) else f"{v:.6f}"

# results
# (for a summary, use result.summary(display=True) or result.summary(i=0, display=True))
print("true X:")
print(np.round(np.asarray(X_true), 4))
print("X_hat:")
print(np.round(result.x,           4))

print("\nNumerical stability:")
print("  kappaC :", fmt(result.model.kappaC))
print("  kappaB :", fmt(result.model.kappaB))
print("  kappaA :", fmt(result.model.kappaA))
corr = result.model.corr()
plt.figure(figsize=(8, 4))
plt.grid(True, linestyle="--", alpha=0.6)
plt.bar(range(len(corr["rmsa_i"])), corr["rmsa_i"])
plt.xlabel("Constraint index")
plt.ylabel("dRMSA (row deletion effect)")
plt.title(f"CLSP Correlogram (Total RMSA = {result.model.rmsa:.2f})")
plt.tight_layout()
plt.show()

print("\nGoodness-of-fit:")
x_true = X_true.flatten()
x_hat  = result.x.flatten()
ss_res = np.sum((x_true - x_hat) ** 2)
ss_tot = np.sum((x_true - np.mean(x_true)) ** 2)
print("  R2_user_defined      :", fmt(1 - ss_res / ss_tot))
print("  NRMSE                :", fmt(result.model.nrmse))
print("  Diagnostic band (min):", fmt(np.min(result.model.x_lower)))
print("  Diagnostic band (max):", fmt(np.max(result.model.x_upper)))
print("  Bootstrap t-test:")
for kw, val in result.model.ttest(sample_size=30,                    # NRMSE sample
                                  seed=seed, distribution="normal",  # seed and distribution
                                  partial=True).items():
    print(f"    {kw}: {float(val):.6f}")

# AP (TM), based on a trade matrix, with a zero diagonal and 20% of known values

seed   = 123456789
rng    = np.random.default_rng(seed)

# sample (dataset)
m, p   = 40, 40                                              # matrix dimensions (m x p)
X_true = np.abs(rng.normal(size=(m, p)))                     # non-negative X_true
X_true = X_true * (1 - np.eye(m, p))                         # zero diagonal
idx    = rng.choice(m * p, size=max(1, int(0.2 * (m * p))),  # random numbers from
                    replace=False)                           # [0,(m * p) - 1], 20% of total

# model
M      = np.eye(m * p)[idx,:]                                # unit matrix
b_row  = X_true.sum(axis=1)                                  # row sums (length m)
b_col  = X_true.sum(axis=0)                                  # column sums (length p)
b_val  = X_true.reshape(-1, 1)[idx]                          # column vector
bounds = (0, None)                                           # non-negativity
result = tmpinv(
             M=M, b_row=b_row, b_col=b_col, b_val=b_val,
             m=m, p=p, zero_diagonal=True, reduced=(20,20),  # reduced models of (20, 20)
             bounds=bounds,
             r=1,                                            # a solution without refinement
             alpha=1.0                                       # a unique MNBLUE estimator
         )

# helpers
def fmt(v):
    v = float(v)
    return f"{v:.4e}" if abs(v) >= 1e6 or (v != 0 and abs(v) < 1e-4) else f"{v:.6f}"

# results
print("true X:")
print(np.round(np.asarray(X_true), 4))
print("X_hat:")
print(np.round(result.x,           4))

print("\nNumerical stability (min-max across models):")
kappaC = np.array([CLSP.kappaC for CLSP in result.model])
kappaB = np.array([CLSP.kappaB for CLSP in result.model])
kappaA = np.array([CLSP.kappaA for CLSP in result.model])
print("  kappaC :", fmt(np.min(kappaC)), "-", fmt(np.max(kappaC)))
print("  kappaB :", fmt(np.min(kappaB)), "-", fmt(np.max(kappaB)))
print("  kappaA :", fmt(np.min(kappaA)), "-", fmt(np.max(kappaA)))

print("\nGoodness-of-fit (min-max across models):")
x_true = X_true.flatten()
x_hat  = result.x.flatten()
mask   = np.isfinite(x_true) & np.isfinite(x_hat)
if mask.any():
    ss_res = np.sum((x_true[mask] - x_hat[mask])**2)
    ss_tot = np.sum((x_true[mask] - np.mean(x_true[mask]))**2)
nrmse      = np.array(      [CLSP.nrmse                         for CLSP in result.model])
x_lower    = np.concatenate([np.array(CLSP.x_lower).reshape(-1) for CLSP in result.model])
x_upper    = np.concatenate([np.array(CLSP.x_upper).reshape(-1) for CLSP in result.model])
print("  R2_user_defined      :", fmt(1 - ss_res / ss_tot                             ))
print("  NRMSE                :", fmt(np.min(nrmse)),      "-", fmt(np.max(nrmse)     ))
print("  Diagnostic band (min):", fmt(np.min(x_lower)),    "-", fmt(np.max(x_lower)   ))
print("  Diagnostic band (max):", fmt(np.min(x_upper)),    "-", fmt(np.max(x_upper)   ))
print("  Bootstrap t-test:")
ttests     = [CLSP.ttest(sample_size=30, seed=seed,
                         distribution="normal")                 for CLSP in result.model]
keys       = ttests[0].keys()
for kw in keys:
    val    = np.array([t[kw] for t in ttests], dtype=float)
    print(f"    {kw}: {fmt(np.min(val))} - {fmt(np.max(val))}")
```

## User Reference

For comprehensive information on the estimator's capabilities, advanced configuration options, and implementation details, please refer to the [pyclsp module](https://pypi.org/project/pyclsp/ "Convex Least Squares Programming"), on which TMPinv is based.

**TMPinv Parameters:**

`S` : *array_like* of shape *(m + p, m + p)*, optional<br>
A diagonal sign slack (surplus) matrix with entries in *{0, ±1}*.<br>
-   *0* enforces equality (== `b_row` or `b_col`),<br>
-  *1* enforces a lower-than-or-equal (≤) condition,<br>
- *–1* enforces a greater-than-or-equal (≥) condition.

The first `m` diagonal entries correspond to row constraints, and the remaining `p` to column constraints. Please note that, in the reduced model, `S` is ignored: slack behavior is derived implicitly from block-wise marginal totals.

`M` : *array_like* of shape *(k, m * p)*, optional<br>
A model matrix with entries in *{0, 1}*. Each row defines a linear restriction on the flattened solution matrix. The corresponding right-hand side values must be provided in `b_val`. This block is used to encode known cell values. Please note that, in the reduced model, `M` must be a unique row subset of an identity matrix (i.e., diagonal-only). Arbitrary or non-diagonal model matrices cannot be mapped to reduced blocks, making the model infeasible.

`b_row` : *array_like* of shape *(m,)*<br>
Right-hand side vector of row totals. Please note that both `b_row` and `b_col` must be provided.

`b_col` : *array_like* of shape *(p,)*<br>
Right-hand side vector of column totals. Please note that both `b_row` and `b_col` must be provided.

`b_val` : *array_like* of shape *(k,)*<br>
Right-hand side vector of known cell values.

`i` : *int*, default = *1*<br>
Number of row groups.

`j` : *int*, default = *1*<br>
Number of column groups.

`zero_diagonal` : *bool*, default = *False*<br>
If *True*, enforces the zero diagonal.

`reduced` : *tuple* of *(int, int)*, optional<br>
Dimensions of the reduced problem. If specified, the problem is estimated as a set of reduced problems constructed from contiguous submatrices of the original table. For example, `reduced` = *(6, 6)* implies *5×5* data blocks with *1* slack row and *1* slack column each (edge blocks may be smaller).

`symmetric` : *bool*, default = *False*<br>
If True, enforces symmetry of the estimated solution matrix as: x = 0.5 * (x + x.T)
Applies to TMPinvResult.x only. For TMPinvResult.model symmetry, add explicit symmetry constraints to M in a full-model solve instead of using this flag.

`bounds` : *sequence* of *(low, high)*, optional<br>
Bounds on cell values. If a single tuple *(low, high)* is given, it is applied to all `m` * `p` cells. Example: *(0, None)*.

`replace_value` : *float* or *None*, default = *np.nan*<br>
Final replacement value for any cell in the solution matrix that violates the specified bounds by more than the given tolerance.

`tolerance` : *float*, default = *square root of machine epsilon*<br>
Convergence tolerance for bounds.

`iteration_limit` : *int*, default = *50*<br>
Maximum number of iterations allowed in the refinement loop.

**CLSP Parameters:**

`r` : *int*, default = *1*<br>
Number of refinement iterations for the pseudoinverse-based estimator.

`Z` : *np.ndarray* or *None*<br>
A symmetric idempotent matrix (projector) defining the subspace for Bott–Duffin pseudoinversion. If *None*, the identity matrix is used, reducing the Bott–Duffin inverse to the Moore–Penrose case.

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
*TMPinvResult*

`TMPinvResult.full` : *bool*<br>
Indicates if this result comes from the full (non-reduced) model.

`TMPinvResult.model` : *CLSP* or *list* of *CLSP*<br>
A single CLSP object in the full model, or a list of CLSP objects for each reduced block in the reduced model.

`TMPinvResult.x` : *np.ndarray*<br>
Final estimated solution matrix of shape *(m, p)*.

`TMPinvResult.summarize(i, display)`<br>
An alias of TMPinvResult.summary().

`TMPinvResult.summary(i, display)`<br>
Return or print a summary of the underlying CLSP result, where `i` : int, default = *None* is the index of a reduced-block model in TMPinvResult.model.

## Bibliography
Bolotov, I. (2025). CLSP: Linear Algebra Foundations of a Modular Two-Step Convex Optimization-Based Estimator for Ill-Posed Problems. *Mathematics*, *13*(21), 3476. [https://doi.org/10.3390/math13213476](https://doi.org/10.3390/math13213476)

## License

MIT License — see the [LICENSE](LICENSE) file.
