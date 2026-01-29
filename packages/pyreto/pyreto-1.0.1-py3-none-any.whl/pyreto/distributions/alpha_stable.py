"""Alpha-Stable distribution - pure functions."""

import numpy as np
from scipy.optimize import minimize
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.stats import norm
from .util import validate_returns, validate_alpha


def _char_func(t, alpha, beta, c, mu):
    """Characteristic function."""
    if alpha == 1:
        return np.exp(1j * mu * t - c * np.abs(t) *
                      (1 + 1j * beta * np.sign(t) * np.log(np.abs(t))))
    else:
        return np.exp(1j * mu * t - c**alpha * np.abs(t)**alpha *
                      (1 - 1j * beta * np.sign(t) * np.tan(np.pi * alpha / 2)))


def _pdf_single(x, alpha, beta, c, mu):
    """PDF for single point."""
    if alpha == 2.0:
        return norm.pdf(x, loc=mu, scale=c)

    t = np.linspace(-50, 50, 1024)
    cf = _char_func(t, alpha, beta, c, mu - x)
    dt = t[1] - t[0]
    cf_sym = np.concatenate([cf, np.conj(cf[-1:0:-1])])
    pdf_component = np.fft.ifft(cf_sym).real[:len(t)] * len(t) / (2 * np.pi)
    return max(abs(pdf_component[0]), 1e-10)


def fit(returns):
    """Fit Alpha-Stable distribution using MLE.

    Parameters
    ----------
    returns : array-like
        Array of returns

    Returns
    -------
    dict
        Fitted parameters: {'alpha': float, 'beta': float, 'c': float, 'mu': float}
    """
    returns = validate_returns(returns)

    def neg_loglik(params):
        alpha, beta, c, mu = params
        if not (0.1 < alpha <= 2.0) or not (-1 <= beta <= 1) or c <= 0:
            return 1e10
        try:
            pdf_vals = [_pdf_single(x, alpha, beta, c, mu) for x in returns]
            if any(p <= 0 for p in pdf_vals):
                return 1e10
            return -np.sum(np.log(pdf_vals))
        except:
            return 1e10

    mu0 = np.mean(returns)
    c0 = np.std(returns) / np.sqrt(2)
    alpha0 = 1.8
    beta0 = 0.0
    x0 = np.array([alpha0, beta0, c0, mu0])
    bounds = [(0.1, 2.0), (-0.999, 0.999), (1e-6, 10.0), (None, None)]

    res = minimize(neg_loglik, x0, method='Nelder-Mead',
                   options={'maxiter': 500, 'xatol': 1e-6, 'fatol': 1e-6})

    alpha, beta, c, mu = res.x
    return {'alpha': alpha, 'beta': beta, 'c': c, 'mu': mu}


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
            xi, par['alpha'], par['beta'], par['c'], par['mu'])
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
