"""Unit tests for Normal-Inverse Gaussian (NIG) distribution."""

import pytest
import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pyreto import nig
from test_common import generate_test_returns, check_var_es_properties, check_distribution_properties


class TestNIGFit:
    """Test NIG fitting functionality."""
    
    def test_fit_basic(self):
        """Test basic fitting functionality."""
        returns = generate_test_returns(seed=1, size=500)
        par = check_distribution_properties(nig, returns)
        
        # Check specific parameters for NIG
        required_params = ['alpha', 'beta', 'delta', 'mu', 'gamma']
        for param in required_params:
            assert param in par, f"NIG should have '{param}' parameter"
        
        assert par['alpha'] > 0, f"Alpha should be positive, got {par['alpha']}"
        assert par['delta'] > 0, f"Delta should be positive, got {par['delta']}"
        assert par['gamma'] > 0, f"Gamma should be positive, got {par['gamma']}"
        assert abs(par['beta']) < par['alpha'], "Beta should satisfy |beta| < alpha"
    
    def test_fit_symmetric_case(self):
        """Test fitting symmetric data (beta should be near 0)."""
        np.random.seed(123)
        # Symmetric normal data
        returns = np.random.normal(0, 0.02, 1000)
        
        par = nig.fit(returns)
        # For symmetric data, beta should be close to 0
        assert abs(par['beta']) < 0.5, f"Beta should be near 0 for symmetric data, got {par['beta']}"
    
    def test_fit_validation_empty_array(self):
        """Test that fit raises error for empty array."""
        with pytest.raises(ValueError, match="Returns cannot be empty"):
            nig.fit([])
    
    def test_fit_validation_nan_values(self):
        """Test that fit raises error for NaN values."""
        returns = [0.01, np.nan, 0.02]
        with pytest.raises(ValueError, match="Returns must be finite"):
            nig.fit(returns)
    
    def test_fit_validation_inf_values(self):
        """Test that fit raises error for Inf values."""
        returns = [0.01, np.inf, 0.02]
        with pytest.raises(ValueError, match="Returns must be finite"):
            nig.fit(returns)


class TestNIGRisk:
    """Test NIG risk calculations."""
    
    def setup_method(self):
        """Set up test data and parameters."""
        self.returns = generate_test_returns(seed=42, size=500)
        self.par = nig.fit(self.returns)
    
    @pytest.mark.parametrize("alpha", [0.1, 0.05, 0.01, 0.001])
    def test_var_at_different_levels(self, alpha):
        """Test VaR calculation at different confidence levels."""
        var = nig.var(alpha, self.par)
        
        assert isinstance(var, float), f"VaR should return float, got {type(var)}"
        assert np.isfinite(var), f"VaR should be finite, got {var}"
        assert not np.isnan(var), f"VaR should not be NaN"
    
    @pytest.mark.parametrize("alpha", [0.1, 0.05, 0.01, 0.001])
    def test_es_at_different_levels(self, alpha):
        """Test ES calculation at different confidence levels."""
        es = nig.es(alpha, self.par)
        
        assert isinstance(es, float), f"ES should return float, got {type(es)}"
        assert np.isfinite(es), f"ES should be finite, got {es}"
        assert not np.isnan(es), f"ES should not be NaN"
    
    def test_var_es_consistency(self):
        """Test that VaR and ES follow risk measure properties."""
        for alpha in [0.05, 0.01]:
            var = nig.var(alpha, self.par)
            es = nig.es(alpha, self.par)
            check_var_es_properties(var, es, alpha)
    
    def test_var_alpha_validation(self):
        """Test that var validates alpha parameter."""
        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            nig.var(1.5, self.par)
        
        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            nig.var(-0.1, self.par)
    
    def test_es_alpha_validation(self):
        """Test that es validates alpha parameter."""
        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            nig.es(1.5, self.par)
        
        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            nig.es(-0.1, self.par)
    
    def test_var_handles_scalar_return(self):
        """Test that var handles scalar return from ppf (regression test)."""
        # This was the bug: ppf returning scalar caused IndexError
        var = nig.var(0.05, self.par)
        assert isinstance(var, float)
        assert not np.isnan(var)


class TestNIGPDF:
    """Test NIG PDF functionality."""
    
    def test_pdf_scalar_input(self):
        """Test PDF with scalar input."""
        par = {'alpha': 2.0, 'beta': 0.0, 'delta': 1.0, 'mu': 0.0, 'gamma': 2.0}
        result = nig.pdf(0.0, par)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (1,)
        assert result[0] > 0
        assert np.isfinite(result[0])
        assert not np.isnan(result[0])
    
    def test_pdf_array_input(self):
        """Test PDF with array input."""
        par = {'alpha': 2.0, 'beta': 0.0, 'delta': 1.0, 'mu': 0.0, 'gamma': 2.0}
        x = np.array([-1.0, 0.0, 1.0])
        result = nig.pdf(x, par)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all(result > 0)
        assert np.all(np.isfinite(result))
        assert np.all(np.logical_not(np.isnan(result)))
    
    def test_pdf_positive(self):
        """Test that PDF values are always positive."""
        returns = generate_test_returns(seed=42, size=100)
        par = nig.fit(returns)
        
        # Test at various points
        x = np.linspace(-0.1, 0.1, 10)
        result = nig.pdf(x, par)
        
        assert np.all(result > 0), "All PDF values should be positive"
        assert np.all(np.isfinite(result)), "All PDF values should be finite"


class TestNIGCDF:
    """Test NIG CDF functionality."""
    
    def test_cdf_scalar_input(self):
        """Test CDF with scalar input."""
        par = {'alpha': 2.0, 'beta': 0.0, 'delta': 1.0, 'mu': 0.0, 'gamma': 2.0}
        result = nig.cdf(0.0, par)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (1,)
        assert 0 <= result[0] <= 1
    
    def test_cdf_array_input(self):
        """Test CDF with array input."""
        par = {'alpha': 2.0, 'beta': 0.0, 'delta': 1.0, 'mu': 0.0, 'gamma': 2.0}
        x = np.array([-1.0, 0.0, 1.0])
        result = nig.cdf(x, par)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all((result >= 0) & (result <= 1))
    
    def test_cdf_monotonic(self):
        """Test that CDF is monotonically increasing."""
        returns = generate_test_returns(seed=42, size=200)
        par = nig.fit(returns)
        
        x = np.linspace(-0.2, 0.2, 9)
        result = nig.cdf(x, par)
        
        assert np.all(np.diff(result) >= -1e-10), "CDF should be monotonically increasing"
    
    def test_cdf_boundaries(self):
        """Test CDF at extreme values."""
        returns = generate_test_returns(seed=42, size=200)
        par = nig.fit(returns)
        
        # Very negative should be near 0
        result_low = nig.cdf(-0.5, par)
        assert result_low[0] < 0.01, "CDF at very negative should be near 0"
        
        # Very positive should be near 1
        result_high = nig.cdf(0.5, par)
        assert result_high[0] > 0.99, "CDF at very positive should be near 1"


class TestNIGPPF:
    """Test NIG PPF functionality."""
    
    def test_ppf_scalar_input(self):
        """Test PPF with scalar input."""
        par = {'alpha': 2.0, 'beta': 0.0, 'delta': 1.0, 'mu': 0.0, 'gamma': 2.0}
        result = nig.ppf(0.5, par)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (1,)
        assert np.isfinite(result[0])
        assert not np.isnan(result[0])
    
    def test_ppf_array_input(self):
        """Test PPF with array input."""
        par = {'alpha': 2.0, 'beta': 0.0, 'delta': 1.0, 'mu': 0.0, 'gamma': 2.0}
        q = np.array([0.1, 0.5, 0.9])
        result = nig.ppf(q, par)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all(np.isfinite(result))
        assert np.all(np.logical_not(np.isnan(result)))
    
    @pytest.mark.parametrize("q", [0.05, 0.1, 0.5, 0.9, 0.95])
    def test_ppf_cdf_roundtrip(self, q):
        """Test that PPF and CDF are inverses."""
        par = {'alpha': 2.0, 'beta': 0.0, 'delta': 1.0, 'mu': 0.0, 'gamma': 2.0}
        
        ppf_result = nig.ppf(q, par)
        cdf_result = nig.cdf(ppf_result, par)
        
        assert np.isclose(cdf_result[0], q, rtol=1e-4, atol=1e-4), \
            f"PPF->CDF roundtrip failed: expected {q}, got {cdf_result[0]}"
    
    def test_ppf_boundaries(self):
        """Test PPF at boundary values."""
        par = {'alpha': 2.0, 'beta': 0.0, 'delta': 1.0, 'mu': 0.0, 'gamma': 2.0}
        
        # Very low quantile should give very negative result
        result_low = nig.ppf(0.001, par)
        assert result_low[0] < -1.0
        
        # Very high quantile should give very positive result
        result_high = nig.ppf(0.999, par)
        assert result_high[0] > 1.0
