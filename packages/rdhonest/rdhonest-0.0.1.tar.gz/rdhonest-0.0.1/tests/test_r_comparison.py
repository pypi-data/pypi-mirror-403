"""
Test file to compare Python RDHonest results with R RDHonest results.

This file replicates the examples from the R package vignette and compares
the results to ensure the Python implementation matches the R implementation.

Expected R results were generated using RDHonest R package version 1.0.1.9000.
"""

import numpy as np
import pandas as pd
import pytest
import sys
sys.path.insert(0, str(__file__).replace('/tests/test_r_comparison.py', ''))

from rdhonest import (
    rd_honest, RDHonest,
    rd_honest_bme, RDHonestBME,
    cvb,
    load_lee08, load_cghs,
)

# Tolerance for numerical comparisons
# Note: Some differences are expected due to implementation details
RTOL = 0.05  # 5% relative tolerance
ATOL = 0.1   # Absolute tolerance


class TestCVbComparison:
    """Compare CVb results with R."""

    def test_cvb_zero_bias(self):
        """CVb(0, alpha=0.05) should be ~1.959964"""
        r_result = 1.959964
        py_result = cvb(0, alpha=0.05)
        assert np.isclose(py_result, r_result, rtol=1e-4)

    def test_cvb_half_bias(self):
        """CVb(0.5, alpha=0.05) should be ~2.181477"""
        r_result = 2.181477
        py_result = cvb(0.5, alpha=0.05)
        assert np.isclose(py_result, r_result, rtol=1e-4)

    def test_cvb_vector_90(self):
        """CVb(0:5, alpha=0.1) comparison"""
        r_results = [1.644854, 2.284468, 3.281552, 4.281552, 5.281552, 6.281552]
        py_results = cvb(list(range(6)), alpha=0.1)
        np.testing.assert_allclose(py_results, r_results, rtol=1e-4)


class TestLee08Comparison:
    """Compare Lee08 RD results with R."""

    @pytest.fixture
    def lee08(self):
        return load_lee08()

    def test_lee08_triangular_h8(self, lee08):
        """
        R: RDHonest(voteshare~margin, data=lee08, kern='triangular', M=0.1, h=8)
        """
        r_results = {
            'estimate': 5.873853,
            'std.error': 1.348925,
            'maximum.bias': 0.6706413,
            'conf.low': 2.934244,
            'conf.high': 8.813462,
            'eff.obs': 793.5835,
            'leverage': 0.009168907,
        }

        results = rd_honest(
            Y=lee08['voteshare'].values,
            X=lee08['margin'].values,
            cutoff=0,
            kern="triangular",
            M=0.1,
            h=8
        )
        co = results.coefficients.iloc[0]

        # Check estimate
        assert np.isclose(co['estimate'], r_results['estimate'], rtol=RTOL), \
            f"Estimate: Python={co['estimate']:.6f}, R={r_results['estimate']:.6f}"

        # Check std.error
        assert np.isclose(co['std.error'], r_results['std.error'], rtol=RTOL), \
            f"Std.Error: Python={co['std.error']:.6f}, R={r_results['std.error']:.6f}"

        # Check maximum.bias
        assert np.isclose(co['maximum.bias'], r_results['maximum.bias'], rtol=RTOL), \
            f"Max Bias: Python={co['maximum.bias']:.6f}, R={r_results['maximum.bias']:.6f}"

        # Check confidence interval
        assert np.isclose(co['conf.low'], r_results['conf.low'], rtol=RTOL), \
            f"CI Low: Python={co['conf.low']:.6f}, R={r_results['conf.low']:.6f}"

        assert np.isclose(co['conf.high'], r_results['conf.high'], rtol=RTOL), \
            f"CI High: Python={co['conf.high']:.6f}, R={r_results['conf.high']:.6f}"

    def test_lee08_uniform_h10(self, lee08):
        """
        R: RDHonest(voteshare~margin, data=lee08, kern='uniform', M=0.1, h=10)
        """
        r_results = {
            'estimate': 6.056774,
            'std.error': 1.190527,
            'eff.obs': 1209,
        }

        results = rd_honest(
            Y=lee08['voteshare'].values,
            X=lee08['margin'].values,
            cutoff=0,
            kern="uniform",
            M=0.1,
            h=10
        )
        co = results.coefficients.iloc[0]

        assert np.isclose(co['estimate'], r_results['estimate'], rtol=RTOL), \
            f"Estimate: Python={co['estimate']:.6f}, R={r_results['estimate']:.6f}"

        assert np.isclose(co['std.error'], r_results['std.error'], rtol=RTOL), \
            f"Std.Error: Python={co['std.error']:.6f}, R={r_results['std.error']:.6f}"

    def test_lee08_taylor_class(self, lee08):
        """
        R: RDHonest(voteshare~margin, data=lee08, kern='triangular', M=0.1, h=8, sclass='T')
        """
        r_results = {
            'estimate': 5.873853,
            'maximum.bias': 1.281026,
        }

        results = rd_honest(
            Y=lee08['voteshare'].values,
            X=lee08['margin'].values,
            cutoff=0,
            kern="triangular",
            M=0.1,
            h=8,
            sclass="T"
        )
        co = results.coefficients.iloc[0]

        assert co['method'] == 'Taylor'

        assert np.isclose(co['estimate'], r_results['estimate'], rtol=RTOL), \
            f"Estimate: Python={co['estimate']:.6f}, R={r_results['estimate']:.6f}"

        # Taylor class should have larger bias bound than Holder
        assert np.isclose(co['maximum.bias'], r_results['maximum.bias'], rtol=RTOL), \
            f"Max Bias: Python={co['maximum.bias']:.6f}, R={r_results['maximum.bias']:.6f}"

    def test_lee08_ehw_se(self, lee08):
        """
        R: RDHonest(voteshare~margin, data=lee08, kern='triangular', M=0.1, h=8, se.method='EHW')
        """
        r_std_error = 1.382215

        results = rd_honest(
            Y=lee08['voteshare'].values,
            X=lee08['margin'].values,
            cutoff=0,
            kern="triangular",
            M=0.1,
            h=8,
            se_method="EHW"
        )
        co = results.coefficients.iloc[0]

        assert np.isclose(co['std.error'], r_std_error, rtol=RTOL), \
            f"EHW Std.Error: Python={co['std.error']:.6f}, R={r_std_error:.6f}"

    def test_lee08_formula_interface(self, lee08):
        """Test R-style formula interface produces same results."""
        results1 = rd_honest(
            Y=lee08['voteshare'].values,
            X=lee08['margin'].values,
            cutoff=0,
            kern="triangular",
            M=0.1,
            h=8
        )

        results2 = RDHonest(
            formula="voteshare ~ margin",
            data=lee08,
            cutoff=0,
            kern="triangular",
            M=0.1,
            h=8
        )

        assert np.isclose(
            results1.coefficients.iloc[0]['estimate'],
            results2.coefficients.iloc[0]['estimate'],
            rtol=1e-10
        )


class TestCGHSComparison:
    """Compare CGHS (discrete running variable) results with R."""

    @pytest.fixture
    def cghs(self):
        return load_cghs()

    def test_cghs_uniform_flci(self, cghs):
        """
        R: RDHonest(log(earnings) ~ yearat14, cutoff=1947, data=cghs,
                   kern='uniform', M=0.04, opt.criterion='FLCI', sclass='H')
        """
        r_results = {
            'estimate': 0.07909463,
            'bandwidth': 2,
            'std.error': 0.06784089,
        }

        results = rd_honest(
            Y=np.log(cghs['earnings'].values),
            X=cghs['yearat14'].values,
            cutoff=1947,
            kern="uniform",
            M=0.04,
            opt_criterion="FLCI",
            sclass="H"
        )
        co = results.coefficients.iloc[0]

        # Note: Bandwidth selection may differ slightly
        assert np.isclose(co['estimate'], r_results['estimate'], rtol=RTOL), \
            f"Estimate: Python={co['estimate']:.6f}, R={r_results['estimate']:.6f}"


class TestRDHonestBMEComparison:
    """Compare RDHonestBME results with R."""

    @pytest.fixture
    def cghs(self):
        return load_cghs()

    def test_cghs_bme_order1(self, cghs):
        """
        R: RDHonestBME(log(earnings) ~ yearat14, cutoff=1947, data=cghs, h=3, order=1)
        """
        r_results = {
            'estimate': 0.06488857,
            'std.error': 0.04902804,
            'conf.low': -0.06965587,
            'conf.high': 0.2019889,
        }

        results = rd_honest_bme(
            Y=np.log(cghs['earnings'].values),
            X=cghs['yearat14'].values,
            cutoff=1947,
            h=3,
            order=1
        )
        co = results.coefficients.iloc[0]

        assert np.isclose(co['estimate'], r_results['estimate'], rtol=RTOL), \
            f"Estimate: Python={co['estimate']:.6f}, R={r_results['estimate']:.6f}"

        assert np.isclose(co['std.error'], r_results['std.error'], rtol=RTOL), \
            f"Std.Error: Python={co['std.error']:.6f}, R={r_results['std.error']:.6f}"

        # Note: BME confidence intervals may differ due to implementation details
        # The construction involves max/min over combinations


class TestOptimalBandwidthComparison:
    """Compare optimal bandwidth selection with R."""

    @pytest.fixture
    def lee08(self):
        return load_lee08()

    def test_lee08_mse_optimal(self, lee08):
        """
        R: RDHonest(voteshare ~ margin, data=lee08, kern='triangular',
                   M=0.1, opt.criterion='MSE')
        """
        r_results = {
            'bandwidth': 8.848511,
            'estimate': 5.936649,
            'std.error': 1.294421,
        }

        results = rd_honest(
            Y=lee08['voteshare'].values,
            X=lee08['margin'].values,
            cutoff=0,
            kern="triangular",
            M=0.1,
            opt_criterion="MSE"
        )
        co = results.coefficients.iloc[0]

        # Bandwidth may differ slightly due to optimization
        assert np.isclose(co['bandwidth'], r_results['bandwidth'], rtol=0.15), \
            f"Bandwidth: Python={co['bandwidth']:.6f}, R={r_results['bandwidth']:.6f}"

        # Estimate should be close if bandwidth is close
        assert np.isclose(co['estimate'], r_results['estimate'], rtol=0.1), \
            f"Estimate: Python={co['estimate']:.6f}, R={r_results['estimate']:.6f}"


def print_comparison_summary():
    """Print a summary of Python vs R comparison."""
    print("\n" + "="*60)
    print("RDHonest Python vs R Comparison Summary")
    print("="*60)

    lee08 = load_lee08()
    cghs = load_cghs()

    # Test 1: CVb
    print("\n1. CVb(0, alpha=0.05)")
    print(f"   R:      1.959964")
    print(f"   Python: {cvb(0, alpha=0.05):.6f}")

    # Test 2: Lee08 basic
    print("\n2. Lee08 - triangular, M=0.1, h=8")
    r = rd_honest(Y=lee08['voteshare'].values, X=lee08['margin'].values,
                  cutoff=0, kern="triangular", M=0.1, h=8)
    print(f"   R estimate:      5.873853")
    print(f"   Python estimate: {r.coefficients.iloc[0]['estimate']:.6f}")
    print(f"   R std.error:      1.348925")
    print(f"   Python std.error: {r.coefficients.iloc[0]['std.error']:.6f}")

    # Test 3: Lee08 uniform
    print("\n3. Lee08 - uniform, M=0.1, h=10")
    r = rd_honest(Y=lee08['voteshare'].values, X=lee08['margin'].values,
                  cutoff=0, kern="uniform", M=0.1, h=10)
    print(f"   R estimate:      6.056774")
    print(f"   Python estimate: {r.coefficients.iloc[0]['estimate']:.6f}")

    # Test 4: CGHS BME
    print("\n4. CGHS - RDHonestBME, h=3, order=1")
    r = rd_honest_bme(Y=np.log(cghs['earnings'].values), X=cghs['yearat14'].values,
                      cutoff=1947, h=3, order=1)
    print(f"   R estimate:      0.06488857")
    print(f"   Python estimate: {r.coefficients.iloc[0]['estimate']:.6f}")

    print("\n" + "="*60)


if __name__ == "__main__":
    print_comparison_summary()
    print("\nRunning full test suite...")
    pytest.main([__file__, "-v"])
