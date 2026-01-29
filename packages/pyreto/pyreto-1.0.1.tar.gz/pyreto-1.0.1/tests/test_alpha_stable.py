"""Unit tests for Alpha-Stable distribution."""

import pytest
import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pyreto import alpha_stable
from test_common import generate_test_returns, check_var_es_properties, check_distribution_properties


class TestAlphaStableFit:
    """Test Alpha-Stable fitting functionality."""
    
    def test_fit_basic(self):
        """Test basic fitting functionality."""
        returns = generate_test_returns(seed=1, size=500)
        par = check_distribution_properties(alpha_stable, returns)
        
        # Check specific parameters for Alpha-Stable
        required_params = ['alpha', 'beta', 'c', 'mu']
        for param in required_params:
            assert param in par, f"Alpha-Stable should have '{param}' parameter"
        
        assert 0.1 < par['alpha'] <= 2.0, f"Alpha should be in (0.1, 2.0], got {par['alpha']}"
        assert -1 <= par['beta'] <= 1, f"Beta should be in [-1, 1], got {par['beta']}"
        assert par['c'] > 0, f"c (scale) should be positive, got {par['c']}"
    
    def test_fit_symmetric_case(self):
        """Test fitting symmetric data (beta should be near 0)."""
        np.random.seed(123)
        # Symmetric normal data
        returns = np.random.normal(0, 0.02, 1000)
        
        par = alpha_stable.fit(returns)
        # For symmetric data, beta should be close to 0
        assert abs(par['beta']) < 0.5, f"Beta should be near 0 for symmetric data, got {par['beta']}"
        # Alpha should be near 2 for normal-like data
        assert par['alpha'] > 1.5, f"Alpha should be high for normal-like data, got {par['alpha']}"
    
    def test_fit_validation_empty_array(self):
        """Test that fit raises error for empty array."""
        with pytest.raises(ValueError, match="Returns cannot be empty"):
            alpha_stable.fit([])
    
    def test_fit_validation_nan_values(self):
        """Test that fit raises error for NaN values."""
        returns = [0.01, np.nan, 0.02]
        with pytest.raises(ValueError, match="Returns must be finite"):
            alpha_stable.fit(returns)
    
    def test_fit_validation_inf_values(self):
        """Test that fit raises error for Inf values."""
        returns = [0.01, np.inf, 0.02]
        with pytest.raises(ValueError, match="Returns must be finite"):
            alpha_stable.fit(returns)


class TestAlphaStableRisk:
    """Test Alpha-Stable risk calculations."""
    
    def setup_method(self):
        """Set up test data and parameters."""
        self.returns = generate_test_returns(seed=42, size=500)
        self.par = alpha_stable.fit(self.returns)
    
    @pytest.mark.parametrize("alpha", [0.1, 0.05, 0.01, 0.001])
    def test_var_at_different_levels(self, alpha):
        """Test VaR calculation at different confidence levels."""
        var = alpha_stable.var(alpha, self.par)
        
        assert isinstance(var, float), f"VaR should return float, got {type(var)}"
        assert np.isfinite(var), f"VaR should be finite, got {var}"
        assert not np.isnan(var), f"VaR should not be NaN"
    
    @pytest.mark.parametrize("alpha", [0.1, 0.05, 0.01, 0.001])
    def test_es_at_different_levels(self, alpha):
        """Test ES calculation at different confidence levels."""
        es = alpha_stable.es(alpha, self.par)
        
        assert isinstance(es, float), f"ES should return float, got {type(es)}"
        assert np.isfinite(es), f"ES should be finite, got {es}"
        assert not np.isnan(es), f"ES should not be NaN"
    
    def test_var_es_consistency(self):
        """Test that VaR and ES follow risk measure properties."""
        for alpha in [0.05, 0.01]:
            var = alpha_stable.var(alpha, self.par)
            es = alpha_stable.es(alpha, self.par)
            check_var_es_properties(var, es, alpha)
    
    def test_var_alpha_validation(self):
        """Test that var validates alpha parameter."""
        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            alpha_stable.var(1.5, self.par)
        
        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            alpha_stable.var(-0.1, self.par)
    
    def test_es_alpha_validation(self):
        """Test that es validates alpha parameter."""
        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            alpha_stable.es(1.5, self.par)
        
        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            alpha_stable.es(-0.1, self.par)
    
    def test_var_handles_scalar_return(self):
        """Test that var handles scalar return from ppf (regression test)."""
        # This was the bug: ppf returning scalar caused IndexError
        var = alpha_stable.var(0.05, self.par)
        assert isinstance(var, float)
        assert not np.isnan(var)


class TestAlphaStablePDF:
    """Test Alpha-Stable PDF functionality."""
    
    def test_pdf_scalar_input(self):
        """Test PDF with scalar input."""
        par = {'alpha': 1.8, 'beta': 0.0, 'c': 1.0, 'mu': 0.0}
        result = alpha_stable.pdf(0.0, par)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (1,)
        assert result[0] > 0
        assert np.isfinite(result[0])
        assert not np.isnan(result[0])
    
    def test_pdf_array_input(self):
        """Test PDF with array input."""
        par = {'alpha': 1.8, 'beta': 0.0, 'c': 1.0, 'mu': 0.0}
        x = np.array([-1.0, 0.0, 1.0])
        result = alpha_stable.pdf(x, par)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all(result > 0)
        assert np.all(np.isfinite(result))
        assert np.all(np.logical_not(np.isnan(result)))
    
    def test_pdf_positive(self):
        """Test that PDF values are always positive."""
        returns = generate_test_returns(seed=42, size=100)
        par = alpha_stable.fit(returns)
        
        # Test at various points
        x = np.linspace(-0.1, 0.1, 10)
        result = alpha_stable.pdf(x, par)
        
        assert np.all(result > 0), "All PDF values should be positive"
        assert np.all(np.isfinite(result)), "All PDF values should be finite"
    
    def test_pdf_normal_special_case(self):
        """Test that alpha=2 gives normal distribution."""
        par = {'alpha': 2.0, 'beta': 0.0, 'c': 1.0, 'mu': 0.0}
        
        # At alpha=2, should approximate normal
        result1 = alpha_stable.pdf(0.0, par)
        # Normal PDF at 0 with scale=1
        normal_pdf_0 = 1.0 / np.sqrt(2 * np.pi)
        assert np.isclose(result1[0], normal_pdf_0, rtol=0.1)


class TestAlphaStableCDF:
    """Test Alpha-Stable CDF functionality."""
    
    def test_cdf_scalar_input(self):
        """Test CDF with scalar input."""
        par = {'alpha': 1.8, 'beta': 0.0, 'c': 1.0, 'mu': 0.0}
        result = alpha_stable.cdf(0.0, par)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (1,)
        assert 0 <= result[0] <= 1
    
    def test_cdf_array_input(self):
        """Test CDF with array input."""
        par = {'alpha': 1.8, 'beta': 0.0, 'c': 1.0, 'mu': 0.0}
        x = np.array([-1.0, 0.0, 1.0])
        result = alpha_stable.cdf(x, par)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all((result >= 0) & (result <= 1))
    
    def test_cdf_monotonic(self):
        """Test that CDF is monotonically increasing."""
        returns = generate_test_returns(seed=42, size=200)
        par = alpha_stable.fit(returns)
        
        x = np.linspace(-0.2, 0.2, 9)
        result = alpha_stable.cdf(x, par)
        
        assert np.all(np.diff(result) >= -1e-10), "CDF should be monotonically increasing"
    
    def test_cdf_boundaries(self):
        """Test CDF at extreme values."""
        par = {'alpha': 1.8, 'beta': 0.0, 'c': 1.0, 'mu': 0.0}
        
        # Very negative should be near 0
        result_low = alpha_stable.cdf(-5.0, par)
        assert result_low[0] < 0.1, "CDF at very negative should be near 0"
        
        # Very positive should be near 1
        result_high = alpha_stable.cdf(5.0, par)
        assert result_high[0] > 0.9, "CDF at very positive should be near 1"


class TestAlphaStablePPF:
    """Test Alpha-Stable PPF functionality."""
    
    def test_ppf_scalar_input(self):
        """Test PPF with scalar input."""
        par = {'alpha': 1.8, 'beta': 0.0, 'c': 1.0, 'mu': 0.0}
        result = alpha_stable.ppf(0.5, par)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (1,)
        assert np.isfinite(result[0])
        assert not np.isnan(result[0])
    
    def test_ppf_array_input(self):
        """Test PPF with array input."""
        par = {'alpha': 1.8, 'beta': 0.0, 'c': 1.0, 'mu': 0.0}
        q = np.array([0.1, 0.5, 0.9])
        result = alpha_stable.ppf(q, par)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all(np.isfinite(result))
        assert np.all(np.logical_not(np.isnan(result)))
    
    @pytest.mark.parametrize("q", [0.05, 0.1, 0.5, 0.9, 0.95])
    def test_ppf_cdf_roundtrip(self, q):
        """Test that PPF and CDF are inverses."""
        par = {'alpha': 1.8, 'beta': 0.0, 'c': 1.0, 'mu': 0.0}
        
        ppf_result = alpha_stable.ppf(q, par)
        cdf_result = alpha_stable.cdf(ppf_result, par)
        
        assert np.isclose(cdf_result[0], q, rtol=1e-4, atol=1e-4), \
            f"PPF->CDF roundtrip failed: expected {q}, got {cdf_result[0]}"
    
    def test_ppf_boundaries(self):
        """Test PPF at boundary values."""
        par = {'alpha': 1.8, 'beta': 0.0, 'c': 1.0, 'mu': 0.0}
        
        # Very low quantile should give very negative result
        result_low = alpha_stable.ppf(0.001, par)
        assert result_low[0] < -1.0
        
        # Very high quantile should give very positive result
        result_high = alpha_stable.ppf(0.999, par)
        assert result_high[0] > 1.0
