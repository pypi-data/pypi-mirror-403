"""Minimal Monte Carlo engine (CPU-only, single-threaded)."""

import numpy as np
import polars as pl
from scipy import stats

from . import student_t, nig, alpha_stable


_MARGINAL_INVERTERS = {
    "student_t": student_t.ppf,
    "nig": nig.ppf,
    "alpha_stable": alpha_stable.ppf,
}


def simulate(copula, margins, n_draws, seed=None):
    """
    Simulate correlated log-returns via copula + margins.

    Parameters
    ----------
    copula : str
        "gaussian" or "t"
    margins : dict
        {"asset": {"type": "student_t", "par": {...}}, ...}
    n_draws : int
        Number of draws (>0)
    seed : int, optional
        Random seed

    Returns
    -------
    polars.DataFrame
        Shape (n_draws, n_assets) with simulated log-returns
    """
    assets = list(margins)
    if not assets:
        raise ValueError("margins dict cannot be empty")
    if n_draws <= 0:
        raise ValueError("n_draws must be positive")

    rng = np.random.default_rng(seed)
    n_assets = len(assets)

    # Uniform draws from copula (identity correlation)
    if copula == "gaussian":
        normals = rng.standard_normal((n_draws, n_assets))
        uniforms = stats.norm.cdf(normals)
    elif copula == "t":
        dof = 5  # canonical choice, matches typical risk-model dofs
        mvt = stats.multivariate_t(loc=np.zeros(n_assets),
                                   shape=np.eye(n_assets),
                                   df=dof)
        t_draws = mvt.rvs(size=n_draws, random_state=rng)
        uniforms = stats.t.cdf(t_draws, df=dof)
    else:
        raise ValueError("copula must be 'gaussian' or 't'")

    # Apply marginal inverse CDFs
    out = {}
    for i, asset in enumerate(assets):
        margin = margins[asset]
        inv = _MARGINAL_INVERTERS.get(margin["type"])
        if inv is None:
            raise ValueError(f"unknown margin type: {margin['type']}")
        out[asset] = inv(uniforms[:, i], margin["par"])

    return pl.DataFrame(out)


def simulate_portfolio(weights, mc_returns):
    """
    Portfolio log-returns from Monte Carlo simulation.

    Parameters
    ----------
    weights : numpy.ndarray
        Portfolio weights, must sum to 1 and be non-negative
    mc_returns : polars.DataFrame
        Simulated returns from simulate()

    Returns
    -------
    polars.Series
        Portfolio log-return series
    """
    w = np.asarray(weights, dtype=float)

    if w.ndim != 1:
        raise ValueError("weights must be 1-dimensional")
    if np.any(w < 0):
        raise ValueError("weights must be non-negative")
    if not np.allclose(w.sum(), 1.0):
        raise ValueError("weights must sum to 1")
    if len(w) != len(mc_returns.columns):
        raise ValueError("weights length must match number of assets")

    return pl.Series("portfolio_return", mc_returns.to_numpy() @ w)
