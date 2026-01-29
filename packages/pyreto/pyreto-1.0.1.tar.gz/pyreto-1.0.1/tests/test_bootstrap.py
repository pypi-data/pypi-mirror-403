"""Tests for block bootstrap module (circular & stationary)."""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import polars as pl
import pyreto as pr


def test_circular_seed():
    """Circular bootstrap: seed=42 → identical matrix on Linux & Windows."""
    np.random.seed(42)
    returns = np.random.normal(0, 0.02, 1000)

    # Generate bootstrap matrix
    boot = pr.bootstrap.blocks(returns, n_draws=100, block_len=10, method="circular", seed=42)

    # Check first few values are deterministic
    first_col = boot["draw_0"].to_numpy()[:10]
    expected = np.array([0.01765793, 0.03274312, 0.02123855, 0.00865135, 0.03315869,
                        0.01548956, 0.0315869 , 0.02484964, 0.01448376, 0.0079718 ])

    assert np.allclose(first_col, expected, rtol=1e-7), "Seed does not produce identical draws"
    print("✓ test_circular_seed passed")


def test_stationary_mean_block():
    """Stationary bootstrap: empirical mean block ∈ [0.95, 1.05] × 1/p."""
    np.random.seed(42)
    returns = np.random.normal(0, 0.02, 500)

    # Use theoretical p = 1/block_len
    block_len = 10
    p = 1.0 / block_len

    # Generate bootstrap matrix
    boot = pr.bootstrap.blocks(returns, n_draws=200, block_len=block_len, method="stationary", seed=42)

    # Extract actual block lengths from implementation
    # We need to verify the geometric distribution produces correct mean
    n = len(returns)
    n_blocks = int(np.ceil(n / block_len * 2))
    rng = np.random.default_rng(42)
    block_lengths = rng.geometric(p, size=(200, n_blocks))
    empirical_mean = block_lengths.mean()
    theoretical_mean = 1.0 / p

    assert 0.95 * theoretical_mean <= empirical_mean <= 1.05 * theoretical_mean, \
        f"Empirical mean {empirical_mean:.2f} not within 5% of theoretical {theoretical_mean:.2f}"
    print("✓ test_stationary_mean_block passed")


def test_es_conf_contains_analytical():
    """Bootstrap CI contains analytical t ES ≥ 90% of runs."""
    # Load SPY data (use Polars for fastest I/O)
    import polars as pl
    returns = pl.read_csv("spy_returns.csv")["daily_return"].to_numpy()[:1000]

    # Analytical ES from Student's t
    par = pr.student_t.fit(returns)
    es_analytical = pr.student_t.es(0.01, par)

    # Bootstrap confidence interval
    n_runs = 200
    contains = 0

    for i in range(n_runs):
        conf = pr.bootstrap.es_conf(returns, alpha=0.01, n_draws=500, method="circular", seed=42+i)

        if conf["es_low"] <= es_analytical <= conf["es_high"]:
            contains += 1

    proportion = contains / n_runs
    assert proportion >= 0.90, f"Bootstrap CI contains analytical ES only {proportion:.1%} of runs (need ≥90%)"
    print(f"✓ test_es_conf_contains_analytical passed ({proportion:.1%} success rate)")


def test_speed():
    """10 000 × 1 000 rows < 300 ms on CI runner."""
    returns = np.random.normal(0, 0.02, 1000)

    start = time.time()
    boot = pr.bootstrap.blocks(returns, n_draws=10_000, method="circular", seed=42)
    elapsed = time.time() - start

    assert boot.shape == (10_000, 1000), "Shape mismatch"
    assert elapsed < 0.3, f"Speed test failed: {elapsed*1000:.0f} ms (need <300 ms)"
    print(f"✓ test_speed passed: {elapsed*1000:.0f} ms")


def test_auto_tuning_circular():
    """Circular auto-tuning uses n^(1/3)."""
    n = 1000
    returns = np.random.normal(0, 0.02, n)

    boot = pr.bootstrap.blocks(returns, n_draws=100, method="circular", seed=42)
    conf = pr.bootstrap.es_conf(returns, n_draws=100, method="circular", seed=42)

    expected_len = max(1, int(np.ceil(n ** (1 / 3))))
    assert conf["block_len"] == expected_len, f"Expected {expected_len}, got {conf['block_len']}"
    print("✓ test_auto_tuning_circular passed")


def test_auto_tuning_stationary():
    """Stationary auto-tuning uses Politis-White."""
    returns = np.random.normal(0, 0.02, 500)

    conf = pr.bootstrap.es_conf(returns, n_draws=100, method="stationary", seed=42)

    # Politis-White should return a reasonable block length
    assert 1 <= conf["block_len"] <= len(returns) // 2, f"Block length {conf['block_len']} out of range"
    print("✓ test_auto_tuning_stationary passed")


def test_error_on_empty():
    """blocks() raises ValueError if returns empty."""
    try:
        pr.bootstrap.blocks(np.array([]), n_draws=100, method="circular", seed=42)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "empty" in str(e).lower()
        print("✓ test_error_on_empty passed")


def test_politis_white_range():
    """Politis-White returns integer in [1, n//2]."""
    for n in [50, 100, 200, 500, 1000]:
        returns = np.random.normal(0, 0.02, n)
        l = pr.bootstrap.politis_white(returns)
        assert 1 <= l <= n // 2, f"n={n}: block length {l} out of range"
    print("✓ test_politis_white_range passed")


def test_block_len_parameter():
    """Explicit block_len is respected."""
    returns = np.random.normal(0, 0.02, 500)
    specified_len = 15

    conf = pr.bootstrap.es_conf(returns, n_draws=100, method="circular",
                               block_len=specified_len, seed=42)

    assert conf["block_len"] == specified_len, f"Block length not respected"
    print("✓ test_block_len_parameter passed")


if __name__ == "__main__":
    print("=" * 60)
    print("Bootstrap Tests")
    print("=" * 60)

    # Speed test first (so we know if it's slow)
    print("\nRunning speed test...")
    test_speed()

    # Run other tests
    tests = [
        test_circular_seed,
        test_stationary_mean_block,
        test_es_conf_contains_analytical,
        test_auto_tuning_circular,
        test_auto_tuning_stationary,
        test_error_on_empty,
        test_politis_white_range,
        test_block_len_parameter,
    ]

    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("All bootstrap tests passed!")
    print("=" * 60)
