import warnings
import numpy                           as np
from   math            import ceil
from   typing          import Sequence
from   collections.abc import Sequence as sq
from   clsp            import CLSP

class TMPinvInputError(Exception):
    """
    Exception class for TMPinv-related input errors.

    Represents internal failures in Tabular Matrix Problems via Pseudoinverse
    Estimation routines due to malformed or missing input. Supports structured
    messaging and optional diagnostic augmentation.

    Parameters
    ----------
    message : str, optional
        Description of the error. Defaults to a generic TMPinv message.

    code : int or str, optional
        Optional error code or identifier for downstream handling.

    Attributes
    ----------
    message : str
        Human-readable error message.

    code : int or str
        Optional error code for custom handling or debugging.

    Usage
    -----
    raise TMPinvInputError("Both b_row and b_col must be provided", code=201)
    """
    def __init__(self, message: str = "An error occurred in TMPinv",
                 code: int | str | None = None):
        self.message = message
        self.code    = code
        full_message = f"{message} (Code: {code})" if code is not None         \
                                                   else message
        super().__init__(full_message)
        
    def __str__(self) -> str:
        return self.message if self.code is None                               \
                            else f"{self.message} [Code: {self.code}]"
    
    def as_dict(self) -> dict:
        """
        Return the error as a dictionary for structured logging or JSON output.
        """
        return {"error": self.message, "code": self.code}

class TMPinvResult:
    """
    Result container for TMPinv estimation.

    Attributes
    ----------
    full : bool
        Indicates if this result comes from the full (non-reduced) model.

    model : CLSP or list of CLSP
        A single CLSP object in the full model, or a list of CLSP objects
        for each reduced block in the reduced model.

    x : np.ndarray
        Final estimated solution matrix of shape (m, p).
    """
    def __init__(self, full: bool, model, x: np.ndarray):
        self.full  = full
        self.model = model
        self.x     = x

    def summarize(self, i: int | None = None, display : bool = False):
        return self.summary(i=i, display=display)

    def summary(self, i: int | None = None, display: bool = False):
        """
        Return or print a summary for the TMPinv estimator.

        Parameters
        ----------
        display : bool, default = False
            If True, prints the summary instead of returning a dictionary.
        """
        if not isinstance(self.model, list):
            return self.model.summarize(display=display)
        if i is None:
            raise TMPinvInputError("Reduced model: please supply the block " +
                                   "index using i=#.")
        idx = int(i)
        if idx < 0 or idx > len(self.model) - 1:
            raise TMPinvInputError(f"i must be in 0..{len(self.model)}-1 "   +
                                   f"for reduced model.")
        return self.model[idx].summarize(display=display)

def TMPinvSolve(
    S:             Sequence[Sequence[float]] | None = None,
    M:             Sequence[Sequence[float]] | None = None,
    b_row:         Sequence[float]           | None = None,
    b_col:         Sequence[float]           | None = None,
    b_val:         Sequence[float]           | None = None,
    i:             int                              = 1,
    j:             int                              = 1,
    zero_diagonal: bool                             = False,
    reduced:       tuple[int, int]           | None = None,
    symmetric:     bool                             = False,
    *args, **kwargs
) -> TMPinvResult:
    """
    Solve a tabular matrix estimation problem via Convex Least Squares
    Programming (CLSP).

    Parameters
    ----------
    S : array_like of shape (m + p, m + p), optional
        A diagonal sign slack (surplus) matrix with entries in {0, ±1}.
        -  0 enforces equality (== b_row or b_col),
        -  1 enforces a lower-than-or-equal (≤) condition,
        - –1 enforces a greater-than-or-equal (≥) condition.
        The first `m` diagonal entries correspond to row constraints,
        and the remaining `p` to column constraints.
    M : array_like of shape (k, m * p), optional
        A model matrix, for example, with entries in {0, 1}. Each row defines a
        linear restriction on the flattened solution matrix. The corresponding
        right-hand side values must be provided in `b_val`. This block is
        used to encode known cell values.
    b_row : array_like of shape (m,)
        Right-hand side vector of row totals.
    b_col : array_like of shape (p,)
        Right-hand side vector of column totals.
    b_val : array_like of shape (k,)
        Right-hand side vector of known cell values.
    i : int, default = 1
        Number of row groups.
    j : int, default = 1
        Number of column groups.
    zero_diagonal : bool, default = False
        If True, enforces the zero diagonal.
    reduced : tuple of (int, int), optional
        Dimensions of the reduced problem.
        If specified, the problem is estimated as a set of reduced problems
        constructed from contiguous submatrices of the original table.
        For example, reduced = (6, 6) implies 5×5 data blocks with 1 slack
        row and 1 slack column each (edge blocks may be smaller).
    symmetric : bool, default = False
        If True, enforces symmetry of the estimated solution matrix as:
        x = 0.5 * (x + x.T)
        Applies to TMPinvResult.x only. For TMPinvResult.model symmetry,
        add explicit symmetry constraints to M in a full-model solve instead
        of using this flag.

    Returns
    -------
    TMPinvResult
        An object containing the fitted CLSP model(s) and the solution
        matrix `x`.

    Notes
    ----
    - In the reduced model, `S` is ignored. Slack behavior is derived implicitly
    from block-wise marginal totals. Likewise, `M` must be a unique row subset
    of an identity matrix (i.e., diagonal-only). Arbitrary or non-diagonal model
    matrices cannot be mapped to reduced blocks, making the model infeasible.
    - This function receives internal keyword arguments ['b_lim' : array_like,
    'C_lim' : array_like] from `tmpinv()` containing cell value bounds. These
    arguments are ignored in the reduced model given its replacement of `S`.
    """
    # (m), (p) Process the parameters, assert conformity, and get dimensions
    if  b_row is None or b_col is None:
        raise TMPinvInputError("Both b_row and b_col must be provided.")
    if  len(b_row) < 2 or len(b_col) < 2:
        raise TMPinvInputError("Minimum length for b_row and b_col is 2.")
    if  not np.isfinite(b_row).all() or not np.isfinite(b_col).all():
        raise TMPinvInputError("b_row and b_col must not contain inf or NaN.")
    b_row = np.asarray(b_row, dtype=np.float64).reshape(-1, 1)
    b_col = np.asarray(b_col, dtype=np.float64).reshape(-1, 1)
    m     = b_row.shape[0] * i
    p     = b_col.shape[0] * j
    if  S     is not None:
        n_rows = m + p + (kwargs.get("C_lim").shape[0]
                          if kwargs.get("C_lim") is not None else 0)
        S      = np.asarray(S, dtype=np.float64)
        if S.shape[0] != n_rows:
            raise TMPinvInputError(f"S must have {n_rows} rows.")
        if (not np.all((S == -1) | (S == 0) | (S == 1)) or
                np.abs(S).sum(axis=0).max() > 1         or
                np.abs(S).sum(axis=1).max() > 1):
            raise TMPinvInputError("S must be a zero-padded subset of ±I.")
    if  M     is not None:
        if  b_val is None:
            raise TMPinvInputError("Both M and b_val must be defined.")
        M = np.asarray(M, dtype=np.float64)
        if  M.ndim == 1:
            M = M.reshape(1, -1)
        if  M.shape[1] != m * p:
            raise TMPinvInputError(f"M must have exactly {m * p} columns.")
    if  b_val is not None:
        if  M     is None:
            raise TMPinvInputError("Both M and b_val must be defined.")
        if not np.isfinite(b_val).all():
            raise TMPinvInputError("b_val must not contain inf or NaN.")
        b_val = np.asarray(b_val, dtype=np.float64).reshape(-1, 1)
    if  M is not None and b_val is not None:
        if  M.shape[0] != b_val.shape[0]:
            raise TMPinvInputError(f"M and b_val must have the same number "
                                   f"of rows: "
                                   f"{M.shape[0]} vs {b_val.shape[0]}")
    kw = {k: v for k, v in kwargs.items() if k not in {"b_lim", "b",
                                                       "C_lim", "S", "M",
                                                       "m", "p",
                                                       "i", "j",
                                                       "zero_diagonal",
                                                       "symmetric"}}

    # perform full estimation and return the result
    if  reduced is None:
        result   = TMPinvResult(True,  None, np.empty((m, p), dtype=float))
        b_blocks = [b_row, b_col]
        if kwargs.get("b_lim") is not None:
            b_blocks.append(np.asarray(kwargs["b_lim"],
                            dtype=np.float64).reshape(-1, 1))
        if b_val is not None:
            b_blocks.append(b_val)
        b = np.vstack(b_blocks)
        result.model = CLSP().solve(*args,
                                    problem='ap', b=b,
                                                  C=kwargs.get("C_lim"),
                                                  S=S,
                                                  M=M,
                                                  m=m,
                                                  p=p,
                                                  i=i,
                                                  j=j,
                                                  zero_diagonal=zero_diagonal,
                                    **kw)
        result.x = result.model.x

    # perform reduced estimation and return the result
    else:
        reduced  = tuple(map(int, reduced))
        if  reduced[0] < 3 or reduced[1] < 3:
            raise TMPinvInputError("Each reduced block must be at least "
                                   "(3, 3) to allow a solvable CLSP submatrix "
                                   "with a slack (surplus) structure.")
        result   = TMPinvResult(False, [], np.empty((m, p), dtype=float))
        m_subset = reduced[0] - 1
        p_subset = reduced[1] - 1

        if  zero_diagonal:                             # not processed by CLSP
            M_diag = np.zeros((min(m, p), m * p))
            b_diag = np.zeros((min(m, p),     1))
            for k in range(min(m, p)):
                M_diag[k, k * p + k] = 1
            M, idx = np.unique(M_diag.copy() if M     is None or M.size     == 0
                                             else np.vstack([M,     M_diag]),
                               axis=0,       return_index=True)
            b_val  = (b_diag.copy()          if b_val is None or b_val.size == 0
                                             else np.vstack([b_val, b_diag])
                     )[idx.reshape(-1)]
            del M_diag, b_diag, idx
        if  M is not None:
            if  not ((np.isclose(M, 0) | np.isclose(M, 1)).all() and
                     (np.isclose(M, 1).sum(axis=1) == 1).all()   and
                     (np.isclose(M, 1).sum(axis=0) <= 1).all()):
                raise TMPinvInputError("M must be a unique row subset of the "
                                       "identity matrix in the reduced model.")
            X_true = np.full((1*m, p), np.nan, dtype=np.float64)
            for idx, row in enumerate(M):
                col  = np.argmax(row)
                r, c = divmod(col, p)                  # M has m * p columns
                X_true[r, c] = b_val.ravel()[idx]
        if kwargs.get("b_lim") is not None:
            X_lim  = np.full((2*m, p), np.nan, dtype=np.float64)
            l_idx  = (lambda x: kwargs["b_lim"].shape[0]    if not x.size else
                     x[0,0])(np.argwhere(S[-kwargs["b_lim"].shape[0]:,:] == -1))
            if l_idx > 0:                              # upper bounds
                for idx, row in enumerate(kwargs["C_lim"][:l_idx,:]):
                    col  = np.argmax(row)
                    r, c = divmod(col, p)
                    X_lim[  r, c] = kwargs["b_lim"].ravel()[      idx]
            if l_idx < kwargs["b_lim"].shape[0]:       # lower bounds
                for idx, row in enumerate(kwargs["C_lim"][l_idx:,:]):
                    col  = np.argmax(row)
                    r, c = divmod(col, p)
                    X_lim[m+r, c] = kwargs["b_lim"].ravel()[l_idx+idx]
        if  S is not None and np.any(S[: S.shape[0] if kwargs.get("b_lim")
                          is  None else -kwargs["b_lim"].shape[0],:] != 0):
            warnings.warn("User-provided S is ignored in the reduced model.",
                          UserWarning)

        for row_block in range(ceil(m / m_subset)):
            for col_block in range(ceil(p / p_subset)):
                m_start  = row_block * m_subset
                m_end    = min(m_start + m_subset, m)
                p_start  = col_block * p_subset
                p_end    = min(p_start + p_subset, p)
                C_subset = None
                S_subset = np.eye((m_end - m_start) + (p_end - p_start))
                b_subset = [b_row[m_start:m_end].reshape(-1, 1),
                            b_col[p_start:p_end].reshape(-1, 1)]
                M_subset = None
                if M                   is not None:
                    subset       = X_true[m_start:m_end, p_start:p_end].ravel()
                    non_empty    = ~np.isnan(subset)
                    if non_empty.any():
                        b_subset.append(subset[non_empty].reshape(-1, 1))
                        M_subset = np.eye(subset.size,
                                          dtype=np.float64)[non_empty,:]
                if kwargs.get("b_lim") is not None:
                    subset       = np.vstack([
                                       X_lim[  m_start:  m_end, p_start:p_end],
                                       X_lim[m+m_start:m+m_end, p_start:p_end]
                                 ]).ravel()
                    non_empty = ~np.isnan(subset)
                    if non_empty.any():
                        b_subset.append(subset[non_empty].reshape(-1, 1))
                        C_subset = np.vstack([np.tile(   np.eye(subset.size//2),
                                             (2,1))])[non_empty,:]
                        S        = np.hstack([np.vstack([np.eye(subset.size//2),
                                                         np.zeros((subset.size//
                                                         2, subset.size//2))
                                                       ])[non_empty,:],
                                              np.vstack([np.zeros((subset.size//
                                                         2, subset.size//2)),
                                                        -np.eye(subset.size//2)
                                                       ])[non_empty,:]      ])
                        S_subset = np.vstack([np.hstack([S_subset, np.zeros((
                                                         S_subset.shape[0],
                                                         S.shape[1]       ))]),
                                              np.hstack([np.zeros((S.shape[0],
                                                         S_subset.shape[1])),
                                                         S])                ])
                tmp      = CLSP().solve(*args,
                                        problem='ap', b=np.vstack(b_subset),
                                                      C=C_subset,
                                                      S=S_subset,
                                                      M=M_subset,
                                                      m=m_end - m_start,
                                                      p=p_end - p_start,
                                                      i=i,
                                                      j=j,
                                                      zero_diagonal=False,
                                        **kw)
                result.model.append(tmp)
                result.x[m_start:m_end, p_start:p_end] = tmp.x

    # enforce symmetry
    if  symmetric:
        if  result.x.shape[0] != result.x.shape[1]:
            raise TMPinvInputError("symmetric=True requires a square matrix "
                                   "(m == p).")
        result.x = float(0.5) * (result.x + result.x.T)

    return result

def tmpinv(
    bounds:          list[tuple[float | None, float | None]] | \
                          tuple[float | None, float | None]  | None = None,
    replace_value:   float                                   | None = np.nan,
    tolerance:       float = np.sqrt(np.finfo(float).eps),
    iteration_limit: int                                   = 50,
    *args, **kwargs
) -> TMPinvResult:
    """
    Solve a tabular matrix estimation problem via Convex Least Squares
    Programming (CLSP) with bound-constrained iterative refinement.

    Parameters
    ----------
    bounds : sequence of (low, high), optional
        Bounds on cell values. If a single tuple (low, high) is given, it
        is applied to all m * p cells. Example: (0, None).
    replace_value : float or None, default = np.nan
        Final replacement value for any cell in the solution matrix that
        violates the specified bounds by more than the given tolerance.
    tolerance : float, optional
        Convergence tolerance for bounds. Default is the square root of
        machine epsilon.
    iteration_limit : int, default = 50
        Maximum number of iterations allowed in the refinement loop.
    *args, **kwargs : additional arguments
        Passed directly to TMPinvSolve().

    Returns
    -------
    TMPinvResult
        An object containing the fitted CLSP model(s) and the solution
        matrix `x`.
    """
    # (n_cells) Perform initial estimation and get cell count
    result  = TMPinvSolve(*args, tolerance=tolerance,
                                 iteration_limit=iteration_limit, **kwargs)
    n_cells = result.x.shape[0] * result.x.shape[1]
    if  bounds is None:
        bounds = (None, None)
    if  isinstance(bounds, tuple):
        bounds = [bounds] * n_cells                    # replicate (low, high)
    elif   isinstance(bounds, sq):                     # normalize bounds
        if len(bounds) > 1 and len(bounds) != n_cells:
            raise TMPinvInputError(f"Bounds length {len(bounds)} does not "
                                   f"match number of variables {n_cells}.")
        elif len(bounds) == 1:
            bounds = bounds * n_cells                  # replicate (low, high)
    if  all(l is None and h is None for l, h in bounds):
        return result                                  # finish if unbounded

    # (result) Perform bound-constrained iterative refinement
    kw    = {k: v for k, v in kwargs.items() if k not in {"b_lim", "b_val",
                                                          "C_lim", "S", "M"}}
    b_lim = np.vstack([np.array([h if h is not None else np.inf  for l, h
                                 in bounds]).reshape(-1, 1),
                       np.array([l if l is not None else -np.inf for l, h
                                 in bounds]).reshape(-1, 1)])
    C_lim = np.vstack([np.tile(np.eye(n_cells), (2,1))])
    S     = (kwargs.get("S") if kwargs.get("S") is not None
             else np.zeros((len(kwargs["b_row"]) + len(kwargs["b_col"]), 0)))
    S     = np.vstack([np.hstack([S, np.zeros((S.shape[0], 2 * n_cells))]),
                       np.hstack([np.zeros((n_cells, S.shape[1])),
                                  np.eye(n_cells), np.zeros((n_cells,
                                                             n_cells))]),
                      -np.hstack([np.zeros((n_cells, S.shape[1] + n_cells)),
                                  np.eye(n_cells)])])
    finite_rows  = np.isfinite(b_lim[:, 0])            # drop rows with ±np.inf
    nonzero_cols = ~np.all(S[np.concatenate([
                                 np.ones(S.shape[0] -
                                         b_lim.shape[0],
                                         dtype=bool),
                                 finite_rows]),
                             :] == 0, axis=0)          # reduce S width
    for _ in range(iteration_limit):
        M_idx, b_val = [], []
        x = result.x.reshape(-1, 1)
        for i, (v, (l, h)) in enumerate(zip(x, bounds)):
            v = float(v.item())
            if ((l is not None and v < l - tolerance) or                       \
                (h is not None and v > h + tolerance)):
                continue                               # skip out-of-bounds
            M_idx.append(i)
            b_val.append(v)
        if len(M_idx) < n_cells:
            M      = np.eye(n_cells, dtype=np.float64)[M_idx]
            result = TMPinvSolve(*args, b_lim=(b_lim[finite_rows, :]),
                                        b_val=b_val,
                                        C_lim=(C_lim[finite_rows, :]),
                                        S=(S[np.concatenate([
                                                 np.ones(S.shape[0] -
                                                         b_lim.shape[0],
                                                         dtype=bool),
                                                 finite_rows]),
                                             :])[:,nonzero_cols],
                                        M=M, tolerance=tolerance,
                                        iteration_limit=iteration_limit, **kw)
        else:
            break

    # (result) Replace out-of-bound values with `replace_value`
    x        = result.x.reshape(-1, 1)
    x_lb     = np.array([l if l is not None else -np.inf
                         for  l, _ in bounds]).reshape(-1, 1)
    x_ub     = np.array([h if h is not None else  np.inf
                         for  _, h in bounds]).reshape(-1, 1)
    x[(x < x_lb - tolerance) | (x > x_ub + tolerance)] = replace_value
    result.x = x.reshape(result.x.shape)

    # enforce (final) symmetry
    if  kwargs.get("symmetric", False):
        if  result.x.shape[0] == result.x.shape[1]:
            result.x = float(0.5) * (result.x + result.x.T)

    return result
