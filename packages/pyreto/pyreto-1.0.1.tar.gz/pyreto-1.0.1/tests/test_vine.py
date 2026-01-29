"""Tests for minimalist R‑vine copula engine."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import scipy.stats as stats
import polars as pl
import pyreto as pr


def test_vine_fit_basic():
    """Fit a vine on three variables, check structure exists."""
    # Simulate three correlated uniforms via Gaussian copula
    np.random.seed(42)
    rho = 0.7
    cov = np.array([[1, rho, 0.5], [rho, 1, 0.3], [0.5, 0.3, 1]])
    z = np.random.multivariate_normal(mean=[0, 0, 0], cov=cov, size=500)
    u = 1 - stats.norm.cdf(z)  # map to right tail (loss direction)

    df = pl.DataFrame(u, schema=["SPY", "TLT", "VIX"])

    vine_dict = pr.vine.fit(df, family_set=["gumbel", "t"], method="mle")

    assert "trees" in vine_dict
    assert len(vine_dict["trees"]) == 2  # dim-1
    assert "npars" in vine_dict
    assert "aic" in vine_dict
    assert "loglik" in vine_dict
    assert vine_dict["aic"] < 0  # AIC is negative for good fits


def test_vine_simulate():
    """Simulate from a fitted vine and check output shape."""
    np.random.seed(42)
    rho = 0.6
    cov = np.array([[1, rho], [rho, 1]])
    z = np.random.multivariate_normal(mean=[0, 0], cov=cov, size=200)
    u = 1 - stats.norm.cdf(z)

    df = pl.DataFrame(u, schema=["A", "B"])
    vine_dict = pr.vine.fit(df, family_set=["gumbel"], method="mle")

    sim = pr.vine.simulate(vine_dict, n_draws=5_000, seed=123)

    assert isinstance(sim, pl.DataFrame)
    assert sim.shape == (5_000, 2)
    assert list(sim.columns) == ["asset_0", "asset_1"]
    assert sim.min().min() >= 0.0
    assert sim.max().max() <= 1.0


def test_reproducibility():
    """Same seed → identical draws."""
    np.random.seed(7)
    df = pl.DataFrame(np.random.rand(100, 3), schema=["x", "y", "z"])
    vine_dict = pr.vine.fit(df, family_set=["indep"], method="mle")

    s1 = pr.vine.simulate(vine_dict, n_draws=1_000, seed=99)
    s2 = pr.vine.simulate(vine_dict, n_draws=1_000, seed=99)

    assert (s1["asset_0"] == s2["asset_0"]).all()
    assert (s1["asset_1"] == s2["asset_1"]).all()
    assert (s1["asset_2"] == s2["asset_2"]).all()


def test_vine_aic_better_than_gaussian():
    """On real data, vine with flexible families beats Gaussian."""
    # Load SPY/TLT/VIX data from csv (first 30 rows as in test requirement)
    df = pl.read_csv("spy_returns.csv").slice(0, 31).select(["SPY", "TLT", "VIX"])

    # Fit Gaussian copula (independence in tree>0, but pair‑wise Gaussian)
    gauss_vine = pr.vine.fit(df, family_set=["gaussian"], method="mle")

    # Fit vine with flexible families
    flex_vine = pr.vine.fit(df, family_set=["gumbel", "joe", "t"], method="mle")

    assert flex_vine["aic"] < gauss_vine["aic"], "Flexible vine should have lower AIC"


def test_upper_tail_dependence_spy_vix():
    """λ_U(SPY,VIX) > 0.55 on 2011‑08‑01 … 2011‑08‑31 data."""
    df = pl.read_csv("spy_returns.csv").slice(0, 31).select(["SPY", "TLT", "VIX"])

    vine_dict = pr.vine.fit(df, family_set=["gumbel", "joe", "t"], method="mle")

    lambda_u_spy_vix = pr.vine.upper_tail_dependence(vine_dict, pair=("asset_0", "asset_2"))

    assert lambda_u_spy_vix > 0.55, f"λ_U(SPY,VIX) = {lambda_u_spy_vix:.3f} ≤ 0.55"


def test_upper_tail_dependence_spy_tlt_low():
    """λ_U(SPY,TLT) < 0.25 on same data."""
    df = pl.read_csv("spy_returns.csv").slice(0, 31).select(["SPY", "TLT", "VIX"])

    vine_dict = pr.vine.fit(df, family_set=["gumbel", "joe", "t"], method="mle")

    lambda_u_spy_tlt = pr.vine.upper_tail_dependence(vine_dict, pair=("asset_0", "asset_1"))

    assert lambda_u_spy_tlt < 0.25, f"λ_U(SPY,TLT) = {lambda_u_spy_tlt:.3f} ≥ 0.25"


def test_seed_produces_identical_uniforms():
    """Cross‑platform reproducibility check."""
    df = pl.DataFrame(np.random.rand(100, 3), schema=["x", "y", "z"])
    vine_dict = pr.vine.fit(df, family_set=["indep"], method="mle")

    # Simulate with fixed seed
    u = pr.vine.simulate(vine_dict, n_draws=5_000, seed=42)

    # Check that the first few values are exactly as expected (cross‑platform)
    first_values = u["asset_0"].head(5).to_numpy()

    # These values should be identical across platforms
    expected = np.array([0.37454012, 0.95071431, 0.73199394, 0.59865848, 0.15601864])

    assert np.allclose(first_values, expected, rtol=1e-6), "Seed does not produce identical draws"


def test_error_on_constant_column():
    """Fit must raise ValueError if any column constant."""
    df = pl.DataFrame([[1, 2, 3], [1, 2, 3], [1, 2, 3]], schema=["a", "b", "c"])

    try:
        pr.vine.fit(df, family_set=["gumbel"], method="mle")
        assert False, "Should have raised ValueError for constant column"
    except ValueError as e:
        assert "constant" in str(e).lower()


def test_error_on_too_few_columns():
    """Fit must raise ValueError if fewer than 3 columns."""
    df = pl.DataFrame(np.random.rand(10, 2), schema=["a", "b"])

    try:
        pr.vine.fit(df, family_set=["gumbel"], method="mle")
        assert False, "Should have raised ValueError for too few columns"
    except ValueError as e:
        assert "at least 3" in str(e)

