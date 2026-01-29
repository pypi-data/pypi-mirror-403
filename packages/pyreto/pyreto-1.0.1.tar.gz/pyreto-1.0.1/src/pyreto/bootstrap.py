"""Block bootstrap for stationary time series (circular & stationary)."""

from typing import Union, Optional, Dict
import numpy as np
import polars as pl
from scipy.optimize import minimize_scalar
from scipy.stats import genpareto


def blocks(returns: Union[np.ndarray, pl.Series],
           n_draws: int = 10_000,
           block_len: Optional[int] = None,
           method: str = "circular",
           seed: Optional[int] = None) -> pl.DataFrame:
    """
    Generate block-bootstrap replicates of a return series.

    Parameters
    ----------
    returns : np.ndarray or pl.Series
        1-D array of returns (any length).
    n_draws : int
        Number of bootstrap replicates (columns) to generate.
    block_len : int or None
        Block length. If None, auto-tuned. If int, used directly.
        For "circular": defaults to ceil(n**(1/3)).
        For "stationary": defaults to Politis-White adaptive length.
    method : str
        "circular" (wraparound) or "stationary" (Geometric block lengths).
    seed : int or None
        Random seed for reproducibility.

    Returns
    -------
    pl.DataFrame
        Shape (len(returns), n_draws), each column is one bootstrap path.
    """
    # Convert to numpy if polars
    if isinstance(returns, pl.Series):
        returns = returns.to_numpy()
    elif not isinstance(returns, np.ndarray):
        returns = np.asarray(returns, dtype=float)

    returns = returns.ravel()
    n = len(returns)

    if n == 0:
        raise ValueError("returns cannot be empty")

    # Auto-tune block length
    if block_len is None:
        if method == "circular":
            block_len = max(1, int(np.ceil(n ** (1 / 3))))
        elif method == "stationary":
            block_len = politis_white(returns)
        else:
            raise ValueError("method must be 'circular' or 'stationary'")

    if block_len < 1 or block_len > n:
        raise ValueError("block_len must be between 1 and n")

    rng = np.random.default_rng(seed)

    if method == "circular":
        # Circular block bootstrap: wraparound indices
        n_blocks = int(np.ceil(n / block_len))
        # Generate start indices for each block
        starts = rng.integers(0, n, size=(n_draws, n_blocks))
        # Create block indices with wraparound
        indices = (starts.reshape(n_draws, n_blocks, 1) +
                   np.arange(block_len).reshape(1, 1, -1)) % n
        # Reshape and truncate to n elements
        indices = indices.reshape(n_draws, -1)[:, :n]
        bootstrap_matrix = returns[indices.T]  # Shape (n, n_draws)

    elif method == "stationary":
        # Stationary block bootstrap: geometric block lengths
        p = 1.0 / block_len
        n_blocks = int(np.ceil(n / block_len * 2))  # Oversample

        # Generate geometric block lengths
        block_lengths = rng.geometric(p, size=(n_draws, n_blocks))

        # Generate start indices
        starts = rng.integers(0, n, size=(n_draws, n_blocks))

        # Build indices
        indices = np.zeros((n_draws, n), dtype=int)
        for i in range(n_draws):
            pos = 0
            for j in range(n_blocks):
                if pos >= n:
                    break
                start = starts[i, j]
                length = min(block_lengths[i, j], n - pos)
                indices[i, pos:pos + length] = (np.arange(start, start + length) % n)
                pos += length

        bootstrap_matrix = returns[indices.T]  # Shape (n, n_draws)

    return pl.DataFrame(bootstrap_matrix.T,
                       schema=[f"draw_{i}" for i in range(n_draws)])


def politis_white(returns: np.ndarray) -> int:
    """
    Adaptive block length via Politis‑White minimisation.

    Parameters
    ----------
    returns : np.ndarray
        Return series.

    Returns
    -------
    int
        Optimal block length ≥ 1.
    """
    n = len(returns)
    if n < 10:
        return 1

    # Rule of thumb starting point
    initial_guess = max(1, int(np.ceil(n ** (1 / 3))))

    # Define objective: variance of bootstrap mean
    def objective(l):
        if l < 1 or l > n // 2:
            return np.inf

        # Simulate with current block length
        n_draws = 200
        rng = np.random.default_rng(42)
        n_blocks = int(np.ceil(n / l))
        starts = rng.integers(0, n, size=(n_draws, n_blocks))
        indices = (starts.reshape(n_draws, n_blocks, 1) +
                   np.arange(int(l)).reshape(1, 1, -1)) % n
        indices = indices.reshape(n_draws, -1)[:, :n]
        bootstrap_data = returns[indices]  # Shape (n_draws, n)

        # Variance of bootstrap mean
        means = bootstrap_data.mean(axis=1)
        return np.var(means, ddof=1)

    # Optimize
    result = minimize_scalar(objective,
                            bounds=(1, min(n // 2, 100)),
                            method='bounded')
    return max(1, int(round(result.x)))


def es_conf(returns: Union[np.ndarray, pl.Series],
            alpha: float = 0.01,
            n_draws: int = 10_000,
            method: str = "circular",
            seed: Optional[int] = 42) -> Dict[str, Union[float, int]]:
    """
    Bootstrap confidence interval for Expected Shortfall.

    Parameters
    ----------
    returns : np.ndarray or pl.Series
        Return series.
    alpha : float
        Significance level for ES.
    n_draws : int
        Number of bootstrap replicates.
    method : str
        "circular" or "stationary" block bootstrap.
    seed : int or None
        Random seed.

    Returns
    -------
    dict
        {"es_mean": float, "es_low": float, "es_high": float, "block_len": int}
    """
    bootstrap_matrix = blocks(returns, n_draws=n_draws, method=method, seed=seed)
    bootstrap_data = bootstrap_matrix.to_numpy()  # Shape (n_draws, n)

    # Calculate ES for each bootstrap draw
    k = max(1, int(alpha * bootstrap_data.shape[1]))
    es_vec = np.array([np.mean(np.sort(draw)[:k]) for draw in bootstrap_data])

    # Get block length used
    n = len(returns)
    block_len = max(1, int(np.ceil(n ** (1 / 3)))) if method == "circular" else politis_white(returns)

    return {
        "es_mean": float(np.mean(es_vec)),
        "es_low": float(np.percentile(es_vec, 5)),
        "es_high": float(np.percentile(es_vec, 95)),
        "block_len": int(block_len),
    }
