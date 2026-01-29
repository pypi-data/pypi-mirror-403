"""Normal-Inverse Gaussian distribution - pure functions."""

import numpy as np
from scipy.optimize import minimize
from scipy.special import kv as bessel_k
from scipy.integrate import quad
from scipy.optimize import brentq
from .util import validate_returns, validate_alpha


def _pdf_single(x, alpha, beta, delta, mu):
    """PDF for single point."""
    gamma = np.sqrt(alpha**2 - beta**2)
    z = (x - mu) / delta
    factor = alpha * delta * np.sqrt(1 + z**2)
    numerator = alpha * delta * bessel_k(1, factor)
    denominator = np.pi * np.sqrt(1 + z**2)
    return (numerator / denominator) * np.exp(delta * gamma + beta * (x - mu))


def fit(returns):
    """Fit Normal-Inverse Gaussian distribution using MLE.

    Parameters
    ----------
    returns : array-like
        Array of returns

    Returns
    -------
    dict
        Fitted parameters: {'alpha': float, 'beta': float, 
                           'delta': float, 'mu': float, 'gamma': float}
    """
    returns = validate_returns(returns)

    def neg_loglik(params):
        alpha, beta, delta, mu = params
        if alpha <= 0 or delta <= 0 or abs(beta) >= alpha:
            return 1e10
        try:
            pdf_vals = [_pdf_single(x, alpha, beta, delta, mu)
                        for x in returns]
            return -np.sum(np.log(pdf_vals))
        except:
            return 1e10

    mu0 = np.mean(returns)
    delta0 = np.std(returns) * 0.8
    alpha0 = 2.0
    beta0 = 0.0
    x0 = np.array([alpha0, beta0, delta0, mu0])
    bounds = [(1e-4, 50), (-49, 49), (1e-4, 50), (None, None)]

    res = minimize(neg_loglik, x0, method='SLSQP', bounds=bounds,
                   options={'ftol': 1e-8, 'maxiter': 1000})

    alpha, beta, delta, mu = res.x
    return {'alpha': alpha, 'beta': beta, 'delta': delta, 'mu': mu,
            'gamma': np.sqrt(alpha**2 - beta**2)}


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
    x = np.atleast_1d(x)
    results = np.zeros_like(x)
    for i, xi in enumerate(x):
        results[i] = _pdf_single(
            xi, par['alpha'], par['beta'], par['delta'], par['mu'])
    return results


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
    x = np.atleast_1d(x)
    results = np.zeros_like(x)
    for i, xi in enumerate(x):
        results[i], _ = quad(lambda xx: pdf(xx, par), -np.inf, xi)
    return results


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
    q = np.atleast_1d(q)
    results = np.zeros_like(q)

    for i, qi in enumerate(q):
        def f(x):
            return cdf(np.array([x]), par)[0] - qi
        results[i] = brentq(f, -10, 10)

    return results


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
    return ppf(alpha, par)[0]


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

    es_val, _ = quad(integrand, -np.inf, var_val)
    return es_val / alpha
