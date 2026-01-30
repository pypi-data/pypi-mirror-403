"""
Tests for the RDHonest Python package.
"""

import numpy as np
import pandas as pd
import pytest

import sys
sys.path.insert(0, str(__file__).replace('/tests/test_rdhonest.py', ''))

from rdhonest import (
    rd_honest, RDHonest,
    rd_honest_bme, RDHonestBME,
    cvb,
    rd_scatter,
    load_lee08, load_cghs,
    create_rd_data,
    triangular_kernel, uniform_kernel, epanechnikov_kernel,
)


class TestCVb:
    """Tests for critical value function."""

    def test_cvb_zero_bias(self):
        """Standard 95% critical value with no bias."""
        cv = cvb(0, alpha=0.05)
        assert np.isclose(cv, 1.96, atol=0.01)

    def test_cvb_positive_bias(self):
        """Critical value with positive bias."""
        cv = cvb(1, alpha=0.05)
        assert cv > 1.96  # Should be larger than unbiased

    def test_cvb_vector(self):
        """Critical values for vector of biases."""
        cv = cvb([0, 0.5, 1], alpha=0.05)
        assert len(cv) == 3
        assert cv[0] < cv[1] < cv[2]

    def test_cvb_90_percent(self):
        """90% critical value."""
        cv = cvb(0, alpha=0.10)
        assert np.isclose(cv, 1.645, atol=0.01)


class TestKernels:
    """Tests for kernel functions."""

    def test_triangular_kernel(self):
        """Test triangular kernel."""
        u = np.array([-1.5, -1, -0.5, 0, 0.5, 1, 1.5])
        k = triangular_kernel(u)
        assert k[0] == 0  # Outside support
        assert k[3] == 1  # Maximum at 0
        assert k[-1] == 0  # Outside support

    def test_uniform_kernel(self):
        """Test uniform kernel."""
        u = np.array([-1.5, -0.5, 0, 0.5, 1.5])
        k = uniform_kernel(u)
        assert k[0] == 0
        assert k[1] == 0.5
        assert k[2] == 0.5
        assert k[-1] == 0

    def test_epanechnikov_kernel(self):
        """Test Epanechnikov kernel."""
        u = np.array([0])
        k = epanechnikov_kernel(u)
        assert np.isclose(k[0], 0.75)


class TestDataLoading:
    """Tests for data loading functions."""

    def test_load_lee08(self):
        """Test Lee 2008 data loading."""
        df = load_lee08()
        assert isinstance(df, pd.DataFrame)
        assert 'voteshare' in df.columns
        assert 'margin' in df.columns
        assert len(df) > 0

    def test_load_cghs(self):
        """Test CGHS data loading."""
        df = load_cghs()
        assert isinstance(df, pd.DataFrame)
        assert 'earnings' in df.columns
        assert 'yearat14' in df.columns


class TestCreateRDData:
    """Tests for data structure creation."""

    def test_create_srd_data(self):
        """Test Sharp RD data creation."""
        np.random.seed(42)
        n = 100
        X = np.random.uniform(-1, 1, n)
        Y = 1 + 2 * (X >= 0) + np.random.normal(0, 0.1, n)

        d = create_rd_data(Y, X, cutoff=0, method="SRD")
        assert d.X is not None
        assert d.Y is not None
        assert np.sum(d.p) > 0
        assert np.sum(d.m) > 0

    def test_create_frd_data(self):
        """Test Fuzzy RD data creation."""
        np.random.seed(42)
        n = 100
        X = np.random.uniform(-1, 1, n)
        D = (X >= 0) * (np.random.random(n) > 0.3)
        Y = 1 + 2 * D + np.random.normal(0, 0.1, n)

        d = create_rd_data(np.column_stack([Y, D]), X, cutoff=0, method="FRD")
        assert d.Y.shape[1] == 2


class TestRDHonest:
    """Tests for main RDHonest function."""

    def test_rd_honest_basic(self):
        """Basic Sharp RD estimation."""
        np.random.seed(42)
        n = 500
        X = np.random.uniform(-1, 1, n)
        Y = 1 + 2 * (X >= 0) + 0.5 * X + np.random.normal(0, 0.5, n)

        results = rd_honest(Y, X, cutoff=0, M=1, h=0.5, kern="triangular")

        assert results is not None
        assert 'estimate' in results.coefficients.columns
        assert 'std.error' in results.coefficients.columns
        assert 'conf.low' in results.coefficients.columns
        assert 'conf.high' in results.coefficients.columns

    def test_rd_honest_different_kernels(self):
        """Test with different kernel types."""
        np.random.seed(42)
        n = 500
        X = np.random.uniform(-1, 1, n)
        Y = 1 + 2 * (X >= 0) + np.random.normal(0, 0.5, n)

        for kern in ["triangular", "uniform", "epanechnikov"]:
            results = rd_honest(Y, X, cutoff=0, M=1, h=0.5, kern=kern)
            assert results is not None

    def test_rd_honest_formula_interface(self):
        """Test R-style formula interface."""
        lee08 = load_lee08()
        results = RDHonest(
            formula="voteshare ~ margin",
            data=lee08,
            cutoff=0,
            M=0.1,
            h=10
        )
        assert results is not None

    def test_rd_honest_se_methods(self):
        """Test different SE estimation methods."""
        np.random.seed(42)
        n = 500
        X = np.random.uniform(-1, 1, n)
        Y = 1 + 2 * (X >= 0) + np.random.normal(0, 0.5, n)

        for se_method in ["nn", "EHW"]:
            results = rd_honest(Y, X, cutoff=0, M=1, h=0.5, se_method=se_method)
            assert results is not None
            assert np.isfinite(results.coefficients.iloc[0]['std.error'])


class TestRDHonestBME:
    """Tests for RDHonestBME function."""

    def test_rd_honest_bme_basic(self):
        """Basic BME estimation."""
        np.random.seed(42)
        n = 500
        X = np.random.randint(-5, 6, n)  # Discrete running variable
        Y = 1 + 2 * (X >= 0) + 0.1 * X + np.random.normal(0, 0.5, n)

        results = rd_honest_bme(Y, X, cutoff=0, h=3, order=1)

        assert results is not None
        assert 'estimate' in results.coefficients.columns

    def test_rd_honest_bme_formula(self):
        """Test BME with formula interface."""
        cghs = load_cghs()
        subset = np.abs(cghs['yearat14'] - 1947) < 10

        results = RDHonestBME(
            formula="earnings ~ yearat14",
            data=cghs[subset],
            cutoff=1947,
            h=3,
            order=1
        )
        assert results is not None


class TestOptimalBandwidth:
    """Tests for bandwidth selection."""

    def test_mse_bandwidth(self):
        """Test MSE optimal bandwidth."""
        np.random.seed(42)
        n = 500
        X = np.random.uniform(-1, 1, n)
        Y = 1 + 2 * (X >= 0) + np.random.normal(0, 0.5, n)

        results = rd_honest(Y, X, cutoff=0, M=1, opt_criterion="MSE")
        assert results is not None
        assert results.coefficients.iloc[0]['bandwidth'] > 0


class TestCovariateAdjustment:
    """Tests for covariate adjustment."""

    def test_with_covariates(self):
        """Test RD with covariate adjustment."""
        np.random.seed(42)
        n = 500
        X = np.random.uniform(-1, 1, n)
        Z = np.random.normal(0, 1, (n, 2))  # 2 covariates
        Y = 1 + 2 * (X >= 0) + Z[:, 0] + 0.5 * Z[:, 1] + np.random.normal(0, 0.5, n)

        results = rd_honest(Y, X, cutoff=0, M=1, h=0.5, covs=Z)
        assert results is not None


class TestSmoothnessClass:
    """Tests for smoothness class options."""

    def test_holder_class(self):
        """Test Holder smoothness class."""
        np.random.seed(42)
        n = 500
        X = np.random.uniform(-1, 1, n)
        Y = 1 + 2 * (X >= 0) + np.random.normal(0, 0.5, n)

        results = rd_honest(Y, X, cutoff=0, M=1, h=0.5, sclass="H")
        assert results.coefficients.iloc[0]['method'] == 'Holder'

    def test_taylor_class(self):
        """Test Taylor smoothness class."""
        np.random.seed(42)
        n = 500
        X = np.random.uniform(-1, 1, n)
        Y = 1 + 2 * (X >= 0) + np.random.normal(0, 0.5, n)

        results = rd_honest(Y, X, cutoff=0, M=1, h=0.5, sclass="T")
        assert results.coefficients.iloc[0]['method'] == 'Taylor'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
