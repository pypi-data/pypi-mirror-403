import numpy                           as np
from   typing          import Sequence
from   collections.abc import Sequence as sq
from   clsp            import CLSP

class LPPinvInputError(Exception):
    """
    Exception class for LPPinv-related input errors.

    Represents internal failures in Linear Programming via Regularized Least
    Squares routines due to malformed or incompatible input. Supports
    structured messaging and optional diagnostic augmentation.

    Parameters
    ----------
    message : str, optional
        Description of the error. Defaults to a generic LPPinv message.

    code : int or str, optional
        Optional error code or identifier for downstream handling.

    Usage
    -----
    raise LPPinvInputError("A_ub and b_ub are incompatible", code=201)
    """
    
    def __init__(self, message: str = "An error occurred in LPPinv",
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

def lppinv(
    c:             Sequence[float]                         | None = None,
    A_ub:          Sequence[Sequence[float]]               | None = None,
    b_ub:          Sequence[float]                         | None = None,
    A_eq:          Sequence[Sequence[float]]               | None = None,
    b_eq:          Sequence[float]                         | None = None,
    non_negative:  bool                                           = True,
    bounds:        list[tuple[float | None, float | None]] |                   \
                        tuple[float | None, float | None]  | None = None,
    replace_value: float                                   | None = np.nan,
    tolerance:     float = np.sqrt(np.finfo(float).eps),
    *args, **kwargs
) -> CLSP:
    """
    Solve a linear program via Convex Least Squares Programming (CLSP)
    estimator.

    Parameters (SciPy linprog-compatible)
    -------------------------------------
    c : array_like of shape (p,), optional
        Objective function coefficients. Accepted for API parity; not used
        by CLSP.
    A_ub : array_like of shape (i, p), optional
        Matrix for inequality constraints A_ub @ x <= b_ub.
    b_ub : array_like of shape (i,), optional
        Right-hand side vector for inequality constraints.
    A_eq : array_like of shape (j, p), optional
        Matrix for equality constraints A_eq @ x = b_eq.
    b_eq : array_like of shape (j,), optional
        Right-hand side vector for equality constraints.
    non_negative : bool, default = True
        If False, no default nonnegativity is applied.
    bounds : sequence of (low, high), optional
        Bounds on variables. If a single tuple (low, high) is given, it is
        applied to all variables. If None, defaults to (0, None) for each
        variable (non-negativity).
    replace_value : float or None, default = np.nan
        Final replacement value for any cell in the returned CLSP.x that
        violates the specified bounds by more than the given tolerance.
    tolerance : float, optional
        Convergence tolerance for bounds. Default is the square root of
        machine epsilon.

    Returns
    -------
    CLSP
        The fitted CLSP object. Consult https://pypi.org/project/pyclsp/
    """
    # assert conformability of constraint sets (A_ub, b_ub) and (A_eq, b_eq)
    if  not ((A_ub is not None and b_ub is not None)  or
             (A_eq is not None and b_eq is not None))                          \
        or  ((A_ub is None) ^ (b_ub is None))                                  \
        or  ((A_eq is None) ^ (b_eq is None)):
        raise LPPinvInputError("At least one complete constraint set "
                               "(A_ub, b_ub) or (A_eq, b_eq) must be "
                               "provided.")
    if  A_ub is not None:
        A_ub = np.asarray(A_ub, dtype=np.float64)
        if A_ub.ndim == 1:
            A_ub = A_ub.reshape(1, -1)
        b_ub = np.asarray(b_ub, dtype=np.float64).reshape(-1, 1)
        if A_ub.shape[0] != b_ub.shape[0]:
            raise LPPinvInputError(f"A_ub and b_ub must have the same number "
                                   f"of rows: "
                                   f"{A_ub.shape[0]} vs {b_ub.shape[0]}")
        n_vars = A_ub.shape[1]                         # number of variables
    if  A_eq is not None:
        A_eq = np.asarray(A_eq, dtype=np.float64)
        if A_eq.ndim == 1:
            A_eq = A_eq.reshape(1, -1)
        b_eq = np.asarray(b_eq, dtype=np.float64).reshape(-1, 1)
        if A_eq.shape[0] != b_eq.shape[0]:
            raise LPPinvInputError(f"A_eq and b_eq must have the same number "
                                   f"of rows: "
                                   f"{A_eq.shape[0]} vs {b_eq.shape[0]}")
        n_vars = A_eq.shape[1]                         # number of variables

    # (b) Construct the right-hand side vector
    if  bounds is None:                                # normalize bounds
        bounds = (0 if non_negative else None, None)
    if  isinstance(bounds, tuple):
        bounds = [bounds] * n_vars                     # replicate (low, high)
    elif   isinstance(bounds, sq):
        if len(bounds) > 1 and len(bounds) != n_vars:
            raise LPPinvInputError(f"Bounds length {len(bounds)} does not "
                                   f"match number of variables {n_vars}.")
        elif len(bounds) == 1:
            bounds = bounds * n_vars                   # replicate (low, high)
    if non_negative and any((l is not None and l < 0) or
                            (h is not None and h < 0) for l, h in bounds):
        raise LPPinvInputError("Negative lower or upper bounds are not "
                               "allowed in linear programs.")
    b = np.empty((0, 1))
    if b_ub is not None:
        b = b_ub
    if b_eq is not None:
        b = np.vstack([b, b_eq])
    b = np.vstack([b, np.array([h if h is not None else np.inf    for l, h
                                in bounds]).reshape(-1, 1),
                      np.array([l if l is not None else (0 if non_negative else
                                                         -np.inf) for l, h
                                in bounds]).reshape(-1, 1)])

    # (C), (S) Construct conformable blocks for the design matrix A
    if  A_ub is not None and A_eq is not None:
        if A_ub.shape[1] != A_eq.shape[1]:
            raise LPPinvInputError(f"A_ub and A_eq must have the same number "
                                   f"of columns: "
                                   f"{A_ub.shape[1]} vs {A_eq.shape[1]}")
    C = np.empty((0, n_vars))
    S = np.empty((0, 0))
    if  A_ub is not None:
        C = A_ub
        S = np.eye(A_ub.shape[0])
    if  A_eq is not None:
        C = np.vstack([C, A_eq])
        S = np.vstack([S, np.zeros((A_eq.shape[0], S.shape[1]))])
    C = np.vstack([C, np.tile(np.eye(n_vars), (2,1))])
    S = np.vstack([np.hstack([S, np.zeros((S.shape[0], 2 * n_vars))]),
                   np.hstack([np.zeros((n_vars, S.shape[1])),
                              np.eye(n_vars), np.zeros((n_vars, n_vars))]),
                  -np.hstack([np.zeros((n_vars, S.shape[1] + n_vars)),
                              np.eye(n_vars)])])

    # (result) Perform the estimation
    assert C.shape[0] == S.shape[0] == b.shape[0],                             \
           f"Row mismatch: C={C.shape}, S={S.shape}, b={b.shape}"
    kw = {k: v for k, v in kwargs.items() if k not in {"C", "S", "b"}}
    finite_rows  = np.isfinite(b[:, 0])                # drop rows with ±np.inf
    nonzero_cols = ~np.all(S[finite_rows, :] == 0,
                           axis=0)                     # reduce S width
    result   = CLSP().solve(*args,
                            problem='general', C=(C[finite_rows, :]),
                                               S=(S[finite_rows, :]
                                                  )[:,nonzero_cols],
                                               b=(b[finite_rows, :]),
                                               tolerance=tolerance,
                            **kw)

    # (result) Replace out-of-bound values with `replace_value`
    x        = result.x.reshape(-1, 1)
    x_lb     = np.array([l if l is not None else (0 if non_negative else
                                                  -np.inf)
                         for  l, _ in bounds]).reshape(-1, 1)
    x_ub     = np.array([h if h is not None else  np.inf
                         for  _, h in bounds]).reshape(-1, 1)
    x[(x < x_lb - tolerance) | (x > x_ub + tolerance)] = replace_value
    result.x = x.reshape(result.x.shape)

    return result
