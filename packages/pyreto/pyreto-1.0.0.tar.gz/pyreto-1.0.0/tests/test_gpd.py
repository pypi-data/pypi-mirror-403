"""Unit tests for Generalised Pareto Distribution (GPD)."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import numpy as np

from pyreto import gpd


def generate_extreme_returns(seed=42, size=500):
    """Generate extreme returns suitable for POT/GPD fitting."""
    np.random.seed(seed)
    # Mix of normal returns and extreme values
    normal_returns = np.random.normal(0, 0.01, size)

    # Add some extreme values (exceedances)
    extreme_prob = 0.05  # 5% extreme events
    extreme_mask = np.random.random(size) < extreme_prob
    extreme_values = -0.03 - np.random.exponential(0.02, size)  # Negative extremes

    returns = normal_returns.copy()
    returns[extreme_mask] = extreme_values[extreme_mask]

    return returns


class TestGPDFit:
    """Test GPD fitting functionality."""

    def test_fit_basic(self):
        """Test basic GPD fitting."""
        returns = generate_extreme_returns(seed=1, size=500)
        par = gpd.fit(returns)

        assert isinstance(par, dict), "Should return dict"
        assert 'c' in par and 'loc' in par and 'scale' in par
        assert par['scale'] > 0, f"Scale should be positive, got {par['scale']}"

    def test_fit_with_heavy_tails(self):
        """Test fitting with heavy-tailed data."""
        np.random.seed(123)
        # Generate data with heavy tails (positive shape parameter)
        # Simulate from GPD with c=0.2 (heavy tail)
        extreme_returns = np.random.standard_t(3, 1000) * 0.02
        extreme_returns = extreme_returns[extreme_returns < -0.02]  # Take left tail

        if len(extreme_returns) > 30:
            par = gpd.fit(extreme_returns)
            assert isinstance(par, dict)
            assert 'c' in par
            assert 'scale' in par and par['scale'] > 0

    def test_fit_validation_empty_array(self):
        """Test that fit raises error for empty array."""
        with pytest.raises(ValueError, match="Returns cannot be empty"):
            gpd.fit([])

    def test_fit_validation_nan_values(self):
        """Test that fit raises error for NaN values."""
        returns = [0.01, np.nan, 0.02]
        with pytest.raises(ValueError, match="Returns must be finite"):
            gpd.fit(returns)

    def test_fit_validation_inf_values(self):
        """Test that fit raises error for Inf values."""
        returns = [0.01, np.inf, 0.02]
        with pytest.raises(ValueError, match="Returns must be finite"):
            gpd.fit(returns)


class TestGPDCDF:
    """Test GPD CDF functionality."""

    def setup_method(self):
        """Set up test parameters."""
        self.par = {'c': 0.1, 'loc': 0.0, 'scale': 1.0}

    def test_cdf_scalar_input(self):
        """Test CDF with scalar input."""
        result = gpd.cdf(0.5, self.par)
        assert isinstance(result, np.ndarray)
        assert result.shape == (1,)
        assert 0 <= result[0] <= 1

    def test_cdf_array_input(self):
        """Test CDF with array input."""
        x = np.array([-1.0, 0.0, 1.0])
        result = gpd.cdf(x, self.par)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all((result >= 0) & (result <= 1))

    def test_cdf_monotonic(self):
        """Test that CDF is monotonically increasing."""
        x = np.linspace(-2.0, 2.0, 10)
        result = gpd.cdf(x, self.par)
        diffs = np.diff(result)
        assert np.all(diffs >= -1e-10), "CDF should be monotonically increasing"

    def test_cdf_boundaries(self):
        """Test CDF at extreme values."""
        # Very negative should be near 0
        result_low = gpd.cdf(-5.0, self.par)
        assert result_low[0] < 0.01, "CDF at very negative should be near 0"

        # Very positive should approach 1
        result_high = gpd.cdf(5.0, self.par)
        assert result_high[0] > 0.99, "CDF at very positive should approach 1"


class TestGPDPDF:
    """Test GPD PDF functionality."""

    def setup_method(self):
        """Set up test parameters."""
        self.par = {'c': 0.1, 'loc': 0.0, 'scale': 1.0}

    def test_pdf_scalar_input(self):
        """Test PDF with scalar input."""
        result = gpd.pdf(0.5, self.par)
        assert isinstance(result, np.ndarray)
        assert result.shape == (1,)
        assert result[0] > 0
        assert np.isfinite(result[0])

    def test_pdf_array_input(self):
        """Test PDF with array input."""
        x = np.array([0.5, 1.0, 2.0])
        result = gpd.pdf(x, self.par)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all(result > 0)
        assert np.all(np.isfinite(result))

    def test_pdf_positive(self):
        """Test that PDF values are always positive."""
        returns = generate_extreme_returns(seed=42, size=100)
        par = gpd.fit(returns)

        x = np.linspace(0, 2, 10)
        result = gpd.pdf(x, par)

        assert np.all(result > 0), "All PDF values should be positive"
        assert np.all(np.isfinite(result)), "All PDF values should be finite"


class TestGPDPPF:
    """Test GPD PPF functionality."""

    def setup_method(self):
        """Set up test parameters."""
        self.par = {'c': 0.1, 'loc': 0.0, 'scale': 1.0}

    def test_ppf_scalar_input(self):
        """Test PPF with scalar input."""
        result = gpd.ppf(0.5, self.par)
        assert isinstance(result, np.ndarray)
        assert result.shape == (1,)
        assert np.isfinite(result[0])

    def test_ppf_array_input(self):
        """Test PPF with array input."""
        q = np.array([0.1, 0.5, 0.9])
        result = gpd.ppf(q, self.par)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.all(np.isfinite(result))

    @pytest.mark.parametrize("q", [0.05, 0.1, 0.5, 0.9, 0.95])
    def test_ppf_cdf_roundtrip(self, q):
        """Test that PPF and CDF are inverses."""
        ppf_result = gpd.ppf(q, self.par)
        cdf_result = gpd.cdf(ppf_result, self.par)
        assert np.isclose(cdf_result[0], q, rtol=1e-5), \
            f"PPF->CDF roundtrip failed: expected {q}, got {cdf_result[0]}"

    def test_ppf_boundaries(self):
        """Test PPF at boundary values."""
        # Very low quantile should give very negative result
        result_low = gpd.ppf(0.001, self.par)
        assert result_low[0] < 0

        # Very high quantile should give positive result
        result_high = gpd.ppf(0.999, self.par)
        assert result_high[0] > 0


class TestGPDRisk:
    """Test GPD risk calculations."""

    def setup_method(self):
        """Set up test data and parameters."""
        self.returns = generate_extreme_returns(seed=42, size=500)
        self.par = gpd.fit(self.returns)

    @pytest.mark.parametrize("alpha", [0.1, 0.05, 0.01, 0.001])
    def test_var_at_different_levels(self, alpha):
        """Test VaR calculation at different confidence levels."""
        var = gpd.var(alpha, self.par)

        assert isinstance(var, float), f"VaR should return float at alpha={alpha}"
        assert np.isfinite(var), f"VaR should be finite, got {var}"
        assert not np.isnan(var), f"VaR should not be NaN"

        # Lower alpha should produce more extreme VaR
        if alpha < 0.05:
            var_5 = gpd.var(0.05, self.par)
            assert var <= var_5, "Lower alpha should produce more extreme VaR"

    @pytest.mark.parametrize("alpha", [0.1, 0.05, 0.01, 0.001])
    def test_es_at_different_levels(self, alpha):
        """Test ES calculation at different confidence levels."""
        es = gpd.es(alpha, self.par)

        assert isinstance(es, float), f"ES should return float at alpha={alpha}"
        assert np.isfinite(es), f"ES should be finite, got {es}"
        assert not np.isnan(es), f"ES should not be NaN"

    def test_var_es_consistency(self):
        """Test that VaR and ES follow risk measure properties."""
        for alpha in [0.05, 0.01]:
            var = gpd.var(alpha, self.par)
            es = gpd.es(alpha, self.par)

            # For loss distributions (negative returns), ES should be more extreme than VaR
            assert es <= var, f"ES ({es}) should be <= VaR ({var}) for alpha={alpha}"

    def test_var_alpha_validation(self):
        """Test that var validates alpha parameter."""
        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            gpd.var(1.5, self.par)

        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            gpd.var(-0.1, self.par)

    def test_es_alpha_validation(self):
        """Test that es validates alpha parameter."""
        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            gpd.es(1.5, self.par)

        with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
            gpd.es(-0.1, self.par)

    def test_var_handles_scalar_return(self):
        """Test that var handles scalar return from ppf (regression test)."""
        var = gpd.var(0.05, self.par)
        assert isinstance(var, float)
        assert not np.isnan(var)


class TestGPDSpecialCases:
    """Test GPD special cases and edge conditions."""

    def test_exponential_case(self):
        """Test GPD with c=0 (exponential distribution)."""
        # When c=0, GPD reduces to exponential distribution
        par = {'c': 0.0, 'loc': 0.0, 'scale': 1.0}

        # Should work without errors
        pdf_val = gpd.pdf(0.5, par)
        cdf_val = gpd.cdf(0.5, par)
        ppf_val = gpd.ppf(0.5, par)

        assert isinstance(pdf_val, np.ndarray)
        assert isinstance(cdf_val, np.ndarray)
        assert isinstance(ppf_val, np.ndarray)
        assert pdf_val[0] > 0
        assert 0 <= cdf_val[0] <= 1

    def test_heavy_tail_case(self):
        """Test GPD with c > 0 (heavy tail)."""
        # Positive shape parameter gives heavy tail
        par = {'c': 0.3, 'loc': 0.0, 'scale': 1.0}

        # Should be able to calculate VaR and ES
        var = gpd.var(0.05, par)
        es = gpd.es(0.05, par)

        assert isinstance(var, float)
        assert isinstance(es, float)
        assert np.isfinite(var)
        assert np.isfinite(es)

    def test_bounded_case(self):
        """Test GPD with c < 0 (bounded tail)."""
        # Negative shape parameter gives bounded tail
        par = {'c': -0.3, 'loc': 0.0, 'scale': 1.0}

        # Should be able to calculate VaR and ES
        var = gpd.var(0.05, par)
        es = gpd.es(0.05, par)

        assert isinstance(var, float)
        assert isinstance(es, float)
        assert np.isfinite(var)
        assert np.isfinite(es)
