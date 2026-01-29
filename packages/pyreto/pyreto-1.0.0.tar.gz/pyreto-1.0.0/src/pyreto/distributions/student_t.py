"""Student's T distribution - pure functions."""

import numpy as np
from scipy.stats import t as student_t
from scipy.integrate import quad
from .util import validate_returns, validate_alpha


def fit(returns):
    """Fit Student's T distribution using MLE.

    Parameters
    ----------
    returns : array-like
        Array of returns

    Returns
    -------
    dict
        Fitted parameters: {'df': float, 'loc': float, 'scale': float}
    """
    returns = validate_returns(returns)
    df, loc, scale = student_t.fit(returns)
    return {'df': df, 'loc': loc, 'scale': scale}


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
    return student_t.pdf(x, **par)


def cdf(x, par):
    """Cumulative distribution function.

    Parameters
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
    return student_t.cdf(x, **par)


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
    return student_t.ppf(q, **par)


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
    return float(result) if np.isscalar(result) else float(result[0])


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

    # For Student's T, we can use numerical integration with better bounds
    var_val = var(alpha, par)

    # Use finite integration bounds to avoid quad issues
    lower_bound = var_val - 10 * par['scale']
    if np.isinf(lower_bound):
        lower_bound = -10

    def integrand(x):
        pdf_val = pdf(x, par)
        if np.isscalar(x):
            return x * float(pdf_val)
        return x * pdf_val

    es_val, _ = quad(integrand, lower_bound, var_val, limit=100)
    return es_val / alpha
