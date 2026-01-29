"""Unit tests for Student's T distribution."""

import pytest
import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pyreto import student_t
from test_common import generate_test_returns, check_var_es_properties, check_distribution_properties


class TestStudentTFit:
    """Test Student's T fitting functionality."""
    
    def test_fit_basic(self):
        """Test basic fitting functionality."""
        returns = generate_test_returns(seed=1, size=500)
        par = check_distribution_properties(student_t, returns)
        
        # Check specific parameters for Student's T
        assert 'df' in par, "Student's T should have 'df' parameter"
        assert 'loc' in par, "Student's T should have 'loc' parameter"
        assert 'scale' in par, "Student's T should have 'scale' parameter"
        
        assert par['df'] > 0, f"Degrees of freedom should be positive, got {par['df']}"
        assert par['scale'] > 0, f"Scale should be positive, got {par['scale']}"
    
    def test_fit_with_leptokurtic_data(self):
        """Test fitting with fat-tailed data."""
        np.random.seed(123)
        # Generate data with heavier tails
        normal = np.random.normal(0, 0.01, 1000)
        extreme = np.random.choice([-0.1, 0.1], size=50)
        returns = np.concatenate([normal, extreme])
        
        par = student_t.fit(returns)
        # Fat-tailed data should result in lower df (degrees of freedom)
        assert 0 < par['df'] < 10, f"Expected low df for fat tails, got {par['df']}"
    
    def test_fit_validation_empty_array(self):
        """Test that fit raises error for empty array."""
        with pytest.raises(ValueError, match="Returns cannot be empty"):
            student_t.fit([])
    
    def test_fit_validation_nan_values(self):
        """Test that fit raises error for NaN values."""
        returns = [0.01, np.nan, 0.02]
        with pytest.raises(ValueError, match="Returns must be finite"):
            student_t.fit(returns)
    
    def test_fit_validation_inf_values(self):
        """Test that fit raises error for Inf values."""
        returns = [0.01, np.inf, 0.02]
        with pytest.raises(ValueError, match="Returns must be finite"):
            student_t.fit(returns)


class TestStudentTRisk:
    """Test Student's T risk calculations."""
    
    def setup_method(self):
        """Set up test data and parameters."""
        self.returns = generate_test_returns(seed=42, size=500)
        self.par = student_t.fit(self.returns)
    
    @pytest.mark.parametrize("alpha", [0.1, 0.05, 0.01, 0.001])
    def test_var_at_different_levels(self, alpha):
        """Test VaR calculation at different confidence levels."""
        var = student_t.var(alpha, self.par)
        
        assert isinstance(var, float), f"VaR should return float, got {type(var)}"
        assert np.isfinite(var), f"VaR should be finite, got {var}"
        
        # Lower alpha should produce more extreme VaR
        if alpha < 0.05:
            var_5 = student_t.var(0.05, self.par)
            assert var <= var_5, "Lower alpha should produce more extreme VaR"
    
    @pytest.mark.parametrize("alpha", [0.1, 0.05, 0.01, 0.001])
    def test_es_at_different_levels(self, alpha):
        """Test ES calculation at different confidence levels."""
        es = student_t.es(alpha, self.par)
        
        assert isinstance(es, float), f"ES should return float, got {type(es)}"
        assert np.isfinite(es), f"ES should be finite, got {es}"
    
    def test_var_es_consistency(self):
        """Test that VaR and ES follow risk measure properties."""
        for alpha in [0.05, 0.01]:
            var = student_t.var(alpha, self.par)
            es = student_t.es(alpha, self.par)
            check_var_es_properties(var, es, alpha)
    
    def test_var_alpha_validation(self):
        """Test that var validates alpha parameter."""
        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            student_t.var(1.5, self.par)
        
        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            student_t.var(-0.1, self.par)
    
    def test_es_alpha_validation(self):
        """Test that es validates alpha parameter."""
        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            student_t.es(1.5, self.par)
        
        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            student_t.es(-0.1, self.par)
    
    def test_var_handles_scalar_return(self):
        """Test that var handles scalar return from ppf (regression test)."""
        # This was the bug: ppf returning scalar caused IndexError
        var = student_t.var(0.05, self.par)
        assert isinstance(var, float)
        assert not np.isnan(var)
    
    def test_var_handles_0d_array(self):
        """Test that var handles 0-dimensional array return from ppf."""
        # Some internal functions return 0-d arrays
        alpha = np.float64(0.05)  # This can cause 0-d array from scipy
        var = student_t.var(alpha, self.par)
        assert isinstance(var, float)
        assert not np.isnan(var)


class TestStudentTPDF:
    """Test Student's T PDF functionality."""
    
    def setup_method(self):
        """Set up test parameters."""
        self.par = {'df': 5.0, 'loc': 0.0, 'scale': 1.0}
    
    def test_pdf_scalar_input(self):
        """Test PDF with scalar input."""
        result = student_t.pdf(0.0, self.par)
        assert isinstance(result, np.ndarray)
        assert result.shape == (1,)
        assert result[0] > 0
        assert np.isfinite(result[0])
    
    def test_pdf_array_input(self):
        """Test PDF with array input."""
        x = np.array([-1.0, 0.0, 1.0])
        result = student_t.pdf(x, self.par)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all(result > 0)
        assert np.all(np.isfinite(result))
    
    def test_pdf_symmetry(self):
        """Test that PDF is symmetric for location=0."""
        x = np.array([-1.0, 1.0])
        result = student_t.pdf(x, self.par)
        assert np.isclose(result[0], result[1], rtol=1e-5)
    
    def test_pdf_location_shift(self):
        """Test that location parameter shifts the distribution."""
        par_shifted = {'df': 5.0, 'loc': 2.0, 'scale': 1.0}
        result_center = student_t.pdf(2.0, self.par)
        result_shifted = student_t.pdf(4.0, par_shifted)
        # Value at 2.0 for centered should equal value at 4.0 for shifted by 2
        assert np.isclose(result_center[0], result_shifted[0], rtol=1e-5)


class TestStudentTCDF:
    """Test Student's T CDF functionality."""
    
    def setup_method(self):
        """Set up test parameters."""
        self.par = {'df': 5.0, 'loc': 0.0, 'scale': 1.0}
    
    def test_cdf_scalar_input(self):
        """Test CDF with scalar input."""
        result = student_t.cdf(0.0, self.par)
        assert isinstance(result, np.ndarray)
        assert result.shape == (1,)
        assert 0 <= result[0] <= 1
    
    def test_cdf_array_input(self):
        """Test CDF with array input."""
        x = np.array([-1.0, 0.0, 1.0])
        result = student_t.cdf(x, self.par)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all((result >= 0) & (result <= 1))
    
    def test_cdf_monotonic(self):
        """Test that CDF is monotonically increasing."""
        x = np.linspace(-3.0, 3.0, 7)
        result = student_t.cdf(x, self.par)
        assert np.all(np.diff(result) >= 0), "CDF should be monotonically increasing"


class TestStudentTPPF:
    """Test Student's T PPF functionality."""
    
    def setup_method(self):
        """Set up test parameters."""
        self.par = {'df': 5.0, 'loc': 0.0, 'scale': 1.0}
    
    def test_ppf_scalar_input(self):
        """Test PPF with scalar input."""
        result = student_t.ppf(0.5, self.par)
        assert isinstance(result, np.ndarray)
        assert result.shape == (1,)
        assert np.isfinite(result[0])
    
    def test_ppf_array_input(self):
        """Test PPF with array input."""
        q = np.array([0.1, 0.5, 0.9])
        result = student_t.ppf(q, self.par)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all(np.isfinite(result))
    
    @pytest.mark.parametrize("q", [0.01, 0.05, 0.1, 0.5, 0.9, 0.95, 0.99])
    def test_ppf_cdf_roundtrip(self, q):
        """Test that PPF and CDF are inverses."""
        ppf_result = student_t.ppf(q, self.par)
        cdf_result = student_t.cdf(ppf_result, self.par)
        assert np.isclose(cdf_result[0], q, rtol=1e-5), \
            f"PPF->CDF roundtrip failed: expected {q}, got {cdf_result[0]}"
    
    def test_ppf_boundaries(self):
        """Test PPF at boundary values."""
        # Extremely small quantile should give very negative result
        result_low = student_t.ppf(0.001, self.par)
        assert result_low[0] < -2.0
        
        # Extremely high quantile should give very positive result
        result_high = student_t.ppf(0.999, self.par)
        assert result_high[0] > 2.0
