import numpy as np
import warnings
from typing import Sequence


def validate_returns(returns: Sequence[float] | np.ndarray) -> np.ndarray:
    """
    Convert `returns` to a 1-D float64 NumPy array and run basic checks.

    Returns
    -------
    np.ndarray
        Validated, ravelled copy/view of the input.

    Raises
    ------
    ValueError
        If the array is empty or contains non-finite values.
    """
    # NOTE: should this also warn if len(returns) below certain threshold? below certain length no statistical reasoning makes sense?
    if not isinstance(returns, np.ndarray):
        returns = np.asarray(returns, dtype=np.float64)
    else:
        returns = returns.astype(np.float64, copy=False)

    returns = returns.ravel()

    if returns.size == 0:
        raise ValueError("Returns cannot be empty")
    if not np.isfinite(returns).all():
        raise ValueError("Returns must be finite (no NaN or Inf)")
    if returns.size < 30:
        warnings.warn(
            "Statistical power low with fewer than 30 observations",
            UserWarning,
            stacklevel=2
        )

    return returns


def validate_alpha(alpha: float):
    if not (0 < alpha < 1):
        raise ValueError("Alpha must be between 0 and 1")
