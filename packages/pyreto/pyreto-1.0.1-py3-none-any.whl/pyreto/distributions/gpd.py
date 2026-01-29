"""Generalised Pareto Distribution - pure functions for Peaks Over Threshold."""

import numpy as np
from scipy.stats import genpareto
from scipy.integrate import quad

from .util import validate_returns, validate_alpha


def fit(returns):
    """Fit Generalised Pareto Distribution using MLE.

    Parameters
    ----------
    returns : array-like
        Array of returns (extreme values / exceedances)

    Returns
    -------
    dict
        Fitted parameters: {'c': float, 'loc': float, 'scale': float}
        c: shape parameter
        loc: location parameter (threshold)
        scale: scale parameter
    """
    returns = validate_returns(returns)

    # For GPD, we typically model exceedances over a threshold
    # Here we let scipy handle the fitting
    c, loc, scale = genpareto.fit(returns)

    return {'c': c, 'loc': loc, 'scale': scale}


def pdf(x, par):
    """Probability density function.

    Parameters
    ----------
    x : array-like
        Points at which to evaluate PDF
    par : dict
        Parameters from fit()

    Returns
    -------
    ndarray
        PDF values
    """
    result = genpareto.pdf(x, **par)
    if np.ndim(result) == 0:
        return np.array([result])
    return result


def cdf(x, par):
    """Cumulative distribution function.

    Parameters
    ----------
    ----------
    x : array-like
        Points at which to evaluate CDF
    par : dict
        Parameters from fit()

    Returns
    -------
    ndarray
        CDF values
    """
    result = genpareto.cdf(x, **par)
    if np.ndim(result) == 0:
        return np.array([result])
    return result


def ppf(q, par):
    """Percent point function (inverse CDF).

    Parameters
    ----------
    q : array-like
        Quantiles to evaluate
    par : dict
        Parameters from fit()

    Returns
    -------
    ndarray
        PPF values
    """
    result = genpareto.ppf(q, **par)
    if np.ndim(result) == 0:
        return np.array([result])
    return result


def var(alpha, par):
    """Value at Risk at significance level alpha.

    Parameters
    ----------
    alpha : float
        Significance level (0 < alpha < 1)
    par : dict
        Parameters from fit()

    Returns
    -------
    float
        VaR value
    """
    validate_alpha(alpha)
    result = ppf(alpha, par)
    if np.ndim(result) == 0:
        return float(result)
    else:
        return float(result[0])


def es(alpha, par):
    """Expected Shortfall at significance level alpha.

    Parameters
    ----------
    alpha : float
        Significance level (0 < alpha < 1)
    par : dict
        Parameters from fit()

    Returns
    -------
    float
        ES value
    """
    validate_alpha(alpha)
    var_val = var(alpha, par)

    def integrand(x):
        return x * pdf(x, par)[0]

    # Use finite integration bounds for GPD
    # For c > 0, distribution has finite upper bound at loc - scale/c
    # For c <= 0, distribution is unbounded to the right
    if par['c'] > 0:
        upper_bound = par['loc'] - par['scale'] / par['c']
        es_val, _ = quad(integrand, -np.inf, min(var_val, upper_bound - 1e-6))
    else:
        es_val, _ = quad(integrand, -np.inf, var_val)

    return es_val / alpha
