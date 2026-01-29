"""Tests for minimalist Monte Carlo engine."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import polars as pl

from pyreto import mc, student_t, nig


def test_gaussian_copula_three_assets():
    """3-asset Gaussian copula, mean portfolio return ≈ 0."""
    margins = {
        "SPY": {"type": "student_t", "par": {"df": 4.0, "loc": 0.0, "scale": 0.01}},
        "TLT": {"type": "student_t", "par": {"df": 5.0, "loc": 0.0, "scale": 0.008}},
        "GLD": {"type": "student_t", "par": {"df": 6.0, "loc": 0.0, "scale": 0.012}},
    }

    returns = mc.simulate("gaussian", margins, n_draws=20_000, seed=42)
    assert isinstance(returns, pl.DataFrame)
    assert returns.shape == (20_000, 3)
    assert list(returns.columns) == ["SPY", "TLT", "GLD"]

    # Equally weighted portfolio
    weights = np.array([1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0])
    port = mc.simulate_portfolio(weights, returns)
    mean_ret = port.mean()

    assert abs(mean_ret) < 1e-2, f"Mean portfolio return {mean_ret} exceeds tolerance"


def test_t_copula_heavier_tails():
    """t-copula with dof=5 produces heavier tails than Gaussian."""
    margins = {
        "SPY": {"type": "student_t", "par": {"df": 4.0, "loc": 0.0, "scale": 0.01}}
    }

    # Gaussian
    gauss = mc.simulate("gaussian", margins, n_draws=50_000, seed=123)
    gauss_kurt = gauss["SPY"].kurtosis()

    # t-copula
    t_draws = mc.simulate("t", margins, n_draws=50_000, seed=123)
    t_kurt = t_draws["SPY"].kurtosis()

    assert (
        t_kurt > gauss_kurt
    ), "t-copula should produce heavier tails than Gaussian"
    assert t_kurt > 3.0, "t-copula tail kurtosis should exceed 3"


def test_reproducibility():
    """Same seed → identical draws."""
    margins = {
        "SPY": {"type": "student_t", "par": {"df": 4.0, "loc": 0.0, "scale": 0.01}}
    }

    r1 = mc.simulate("gaussian", margins, n_draws=10_000, seed=42)
    r2 = mc.simulate("gaussian", margins, n_draws=10_000, seed=42)

    assert (r1["SPY"] == r2["SPY"]).all(), "Same seed must give identical draws"


def test_simulate_portfolio_shape():
    """Portfolio shape and weight validation."""
    margins = {
        "A": {"type": "student_t", "par": {"df": 5.0, "loc": 0.0, "scale": 0.02}},
        "B": {"type": "student_t", "par": {"df": 5.0, "loc": 0.0, "scale": 0.02}},
    }

    returns = mc.simulate("gaussian", margins, n_draws=1_000, seed=1)
    weights = np.array([0.6, 0.4])

    port = mc.simulate_portfolio(weights, returns)
    assert isinstance(port, pl.Series)
    assert len(port) == 1_000
    assert port.name == "portfolio_return"


def test_nig_margins():
    """NIG margins work in simulation."""
    # Fit NIG to some synthetic data
    np.random.seed(7)
    syn = np.random.normal(0, 0.02, 5000)
    par = nig.fit(syn)

    margins = {"asset1": {"type": "nig", "par": par}}
    draws = mc.simulate("gaussian", margins, n_draws=5_000, seed=77)

    assert draws.shape == (5_000, 1)
    assert not draws["asset1"].is_null().any()
    assert draws["asset1"].std() > 0


def test_negative_weights_raise():
    """Negative weights are rejected."""
    margins = {"A": {"type": "student_t", "par": {"df": 5.0, "loc": 0, "scale": 0.02}}}
    returns = mc.simulate("gaussian", margins, n_draws=100, seed=1)

    try:
        mc.simulate_portfolio(np.array([-0.5, 1.5]), returns)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "non-negative" in str(e)


def test_weights_must_sum_to_one():
    """Weights not summing to 1 are rejected."""
    margins = {"A": {"type": "student_t", "par": {"df": 5.0, "loc": 0, "scale": 0.02}}}
    returns = mc.simulate("gaussian", margins, n_draws=100, seed=1)

    try:
        mc.simulate_portfolio(np.array([0.5, 0.5]), returns)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "sum to 1" in str(e)


def test_single_asset_portfolio():
    """Single asset portfolio returns identical to asset."""
    margins = {
        "ONLY": {"type": "student_t", "par": {"df": 5.0, "loc": 0, "scale": 0.02}}
    }

    returns = mc.simulate("gaussian", margins, n_draws=1_000, seed=99)
    port = mc.simulate_portfolio(np.array([1.0]), returns)

    assert (port == returns["ONLY"]).all()


def test_t_copula_dof5_empirical_tail():
    """Empirical check: t-copula gives more 5 % VaR exceedances."""
    margins = {
        "X": {"type": "student_t", "par": {"df": 4.0, "loc": 0.0, "scale": 0.01}}
    }

    gauss = mc.simulate("gaussian", margins, n_draws=100_000, seed=10)
    t_draws = mc.simulate("t", margins, n_draws=100_000, seed=10)

    var_gauss = np.percentile(gauss["X"], 5)
    var_t = np.percentile(t_draws["X"], 5)

    # t-copula should produce more extreme VaR
    assert var_t < var_gauss, "t-copula VaR should be more extreme than Gaussian"


if __name__ == "__main__":
    # Run all tests
    test_gaussian_copula_three_assets()
    print("✓ test_gaussian_copula_three_assets")

    test_t_copula_heavier_tails()
    print("✓ test_t_copula_heavier_tails")

    test_reproducibility()
    print("✓ test_reproducibility")

    test_simulate_portfolio_shape()
    print("✓ test_simulate_portfolio_shape")

    test_nig_margins()
    print("✓ test_nig_margins")

    test_negative_weights_raise()
    print("✓ test_negative_weights_raise")

    test_weights_must_sum_to_one()
    print("✓ test_weights_must_sum_to_one")

    test_single_asset_portfolio()
    print("✓ test_single_asset_portfolio")

    test_t_copula_dof5_empirical_tail()
    print("✓ test_t_copula_dof5_empirical_tail")

    print("\nAll MC tests passed!")
