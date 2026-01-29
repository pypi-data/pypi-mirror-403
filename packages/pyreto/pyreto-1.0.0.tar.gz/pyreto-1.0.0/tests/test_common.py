"""Common utilities for testing pyreto distributions."""

import numpy as np


def generate_test_returns(seed=42, size=200):
    """Generate test returns data with realistic properties."""
    np.random.seed(seed)
    # Mix of normal and some extreme values to simulate fat tails
    normal_returns = np.random.normal(0, 0.02, size)
    extreme_prob = 0.02  # 2% chance of extreme returns
    extreme_mask = np.random.random(size) < extreme_prob
    extreme_values = np.random.choice([-0.05, 0.05], size=size) * np.random.random(size)
    
    returns = normal_returns.copy()
    returns[extreme_mask] = extreme_values[extreme_mask]
    
    return returns


def check_var_es_properties(var, es, alpha):
    """Check that VaR and ES follow basic risk measure properties."""
    # ES should be more extreme (worse) than VaR for same alpha
    if alpha < 0.5:
        assert es <= var, f"ES ({es}) should be <= VaR ({var}) for alpha={alpha}"
    else:
        assert es >= var, f"ES ({es}) should be >= VaR ({var}) for alpha={alpha}"
    
    # VaR should be a float
    assert isinstance(var, float), f"VaR should be float, got {type(var)}"
    assert isinstance(es, float), f"ES should be float, got {type(es)}"


def check_distribution_properties(distro_module, returns, tol=0.1):
    """Check basic properties of fitted distributions."""
    par = distro_module.fit(returns)
    
    # Check that parameters were fit and are valid numbers
    assert isinstance(par, dict), "fit() should return dict"
    assert len(par) > 0, "Parameters should not be empty"
    
    for key, val in par.items():
        assert isinstance(val, (float, np.floating)), \
            f"Parameter {key} should be float-like, got {type(val)}"
        assert np.isfinite(val), f"Parameter {key} should be finite, got {val}"
    
    return par
