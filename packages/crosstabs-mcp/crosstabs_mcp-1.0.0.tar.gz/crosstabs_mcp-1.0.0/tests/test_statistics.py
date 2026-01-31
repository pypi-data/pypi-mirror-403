"""
Test Suite for Crosstabs MCP Server

Comprehensive tests for all statistical functions.
Run with: pytest tests/ -v
"""

import pytest
import math
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from crosstabs_mcp.server import (
    StatisticalEngine, OrdinalTests, TrendTests, PowerAnalysis,
    MultipleComparison, VisualizationData, AdditionalStats,
    ConfidenceInterval
)


class TestChiSquare:
    """Test chi-square functionality."""

    def test_chi_square_basic(self):
        """Test basic chi-square calculation."""
        table = [[6, 4], [2, 8]]
        result = StatisticalEngine.chi_square_test(table)

        assert result.statistic is not None
        assert result.p_value is not None
        assert result.df == 1
        assert len(result.effect_sizes) > 0
        assert result.effect_sizes[0].name == "Cramér's V"

    def test_chi_square_large_table(self):
        """Test chi-square with larger contingency table."""
        table = [
            [50, 10, 5],
            [20, 30, 10],
            [5, 15, 25]
        ]
        result = StatisticalEngine.chi_square_test(table)

        assert result.df == 4  # (3-1) * (3-1)
        assert result.statistic > 0
        assert result.p_value >= 0

    def test_chi_square_assumptions(self):
        """Test assumption checking."""
        table = [[50, 2], [1, 1]]
        assumptions = StatisticalEngine.check_expected_frequencies(table)

        assert not assumptions.valid
        assert len(assumptions.warnings) > 0

    def test_chi_square_perfect_association(self):
        """Test chi-square with perfect association."""
        table = [[100, 0], [0, 100]]
        result = StatisticalEngine.chi_square_test(table)

        assert result.statistic > 0
        assert result.p_value < 0.001


class TestGTest:
    """Test G-test (likelihood ratio)."""

    def test_g_test_basic(self):
        """Test basic G-test calculation."""
        table = [[50, 30], [20, 40]]
        result = StatisticalEngine.g_test(table)

        assert result.statistic > 0
        assert result.p_value is not None
        assert result.df == 1

    def test_g_test_significance(self):
        """G-test should detect significant association."""
        table = [[80, 20], [30, 70]]
        result = StatisticalEngine.g_test(table)

        assert result.p_value < 0.05


class TestFishersExact:
    """Test Fisher's exact test."""

    def test_fishers_exact_basic(self):
        """Test basic Fisher's exact test."""
        table = [[3, 1], [1, 3]]
        result = StatisticalEngine.fishers_exact_test(table)

        assert result.statistic > 0
        assert result.p_value > 0
        assert len(result.confidence_intervals) > 0

    def test_fishers_exact_ci(self):
        """Test odds ratio confidence interval."""
        table = [[10, 5], [5, 10]]
        result = StatisticalEngine.fishers_exact_test(table)

        ci = result.confidence_intervals[0]
        assert ci.parameter == "Odds Ratio"
        assert ci.lower <= ci.upper
        assert ci.level == 0.95

    def test_fishers_exact_perfect_separation(self):
        """Test with perfect separation (extreme case)."""
        table = [[10, 0], [0, 10]]
        result = StatisticalEngine.fishers_exact_test(table)

        assert result.statistic is not None

    def test_fishers_exact_wrong_dimensions(self):
        """Test error handling for non-2x2 table."""
        table = [[1, 2, 3], [4, 5, 6]]

        with pytest.raises(ValueError):
            StatisticalEngine.fishers_exact_test(table)


class TestMcNemar:
    """Test McNemar's test for paired data."""

    def test_mcnemar_basic(self):
        """Test basic McNemar's test."""
        table = [[45, 10], [4, 41]]
        result = StatisticalEngine.mcnemar_test(table)

        assert result.statistic is not None
        assert result.p_value is not None
        assert result.df == 1

    def test_mcnemar_concordant_only(self):
        """Test McNemar with mostly concordant pairs."""
        table = [[50, 0], [0, 50]]
        result = StatisticalEngine.mcnemar_test(table)

        assert result.statistic == 0
        assert result.p_value == 1.0


class TestProportionCI:
    """Test confidence interval calculations."""

    def test_proportion_ci_wilson(self):
        """Test Wilson score confidence interval."""
        lower, upper = StatisticalEngine.proportion_ci(20, 100, method="wilson")

        assert 0 <= lower <= upper <= 1
        assert lower < 0.2 < upper

    def test_proportion_ci_agresti(self):
        """Test Agresti-Coull confidence interval."""
        lower, upper = StatisticalEngine.proportion_ci(20, 100, method="agresti")

        assert 0 <= lower <= upper <= 1
        assert lower < 0.2 < upper

    def test_proportion_ci_normal(self):
        """Test normal approximation interval."""
        lower, upper = StatisticalEngine.proportion_ci(80, 100, method="normal")

        assert 0 <= lower <= upper <= 1
        assert lower < 0.8 < upper


class TestPostHoc:
    """Test post-hoc analysis."""

    def test_post_hoc_residuals(self):
        """Test standardized residuals calculation."""
        table = [[50, 10], [20, 20]]
        residuals = StatisticalEngine.standardized_residuals(table)

        assert len(residuals) == 2
        assert len(residuals[0]) == 2

    def test_post_hoc_chi_square_contributions(self):
        """Test chi-square contributions by cell."""
        table = [[50, 10], [20, 20]]
        post_hoc = StatisticalEngine.post_hoc_analysis(table)

        assert "standardized_residuals" in post_hoc
        assert "chi_square_contributions" in post_hoc
        assert "contribution_percentages" in post_hoc


class TestKappa:
    """Test Cohen's Kappa."""

    def test_cohens_kappa_basic(self):
        """Test basic Cohen's kappa."""
        table = [[20, 5], [3, 22]]
        result = StatisticalEngine.cohens_kappa(table)

        assert "kappa" in result
        assert 0 < result["kappa"] < 1

    def test_weighted_kappa(self):
        """Test weighted kappa."""
        table = [[20, 5, 0], [3, 15, 2], [0, 4, 18]]
        result = StatisticalEngine.weighted_kappa(table, "quadratic")

        assert "weighted_kappa" in result
        assert 0 < result["weighted_kappa"] < 1


class TestCMH:
    """Test Cochran-Mantel-Haenszel."""

    def test_cmh_basic(self):
        """Test CMH with two strata."""
        tables = [
            [[10, 5], [3, 12]],
            [[8, 6], [4, 10]]
        ]
        result = StatisticalEngine.cmh_test(tables)

        assert "chi2" in result
        assert "common_odds_ratio" in result
        assert result["n_strata"] == 2


class TestOrdinalTests:
    """Test ordinal statistics."""

    def test_spearmans_rho(self):
        """Test Spearman's rho."""
        ranks_x = [1, 2, 3, 4, 5]
        ranks_y = [1, 3, 2, 5, 4]
        result = OrdinalTests.spearmans_rho(ranks_x, ranks_y)

        assert "rho" in result
        assert -1 <= result["rho"] <= 1

    def test_kendalls_tau(self):
        """Test Kendall's tau."""
        ranks_x = [1, 2, 3, 4, 5]
        ranks_y = [1, 3, 2, 5, 4]
        result = OrdinalTests.kendalls_tau(ranks_x, ranks_y)

        assert "tau" in result
        assert -1 <= result["tau"] <= 1

    def test_goodman_kruskal_gamma(self):
        """Test Goodman-Kruskal gamma."""
        table = [[20, 5, 2], [3, 15, 8], [1, 6, 20]]
        result = OrdinalTests.goodman_kruskal_gamma(table)

        assert "gamma" in result
        assert -1 <= result["gamma"] <= 1


class TestTrendTests:
    """Test trend analysis."""

    def test_linear_trend(self):
        """Test linear-by-linear association."""
        table = [[30, 15, 5], [15, 20, 15], [5, 15, 30]]
        result = TrendTests.linear_by_linear(table)

        assert "z_statistic" in result
        assert "p_value" in result


class TestPowerAnalysis:
    """Test power and sample size."""

    def test_sample_size_calculation(self):
        """Test sample size calculation."""
        result = PowerAnalysis.power_two_proportions(0.3, 0.5)

        assert result["parameter"] == "sample_size"
        assert result["n_per_group"] > 0

    def test_power_calculation(self):
        """Test power calculation."""
        result = PowerAnalysis.power_two_proportions(0.3, 0.5, n=100)

        assert result["parameter"] == "power"
        assert 0 <= result["power"] <= 1


class TestMultipleComparison:
    """Test multiple comparison corrections."""

    def test_bonferroni(self):
        """Test Bonferroni correction."""
        p_values = [0.01, 0.03, 0.05, 0.10]
        result = MultipleComparison.bonferroni(p_values)

        assert result["method"] == "Bonferroni"
        assert result["n_tests"] == 4

    def test_fdr(self):
        """Test Benjamini-Hochberg FDR."""
        p_values = [0.01, 0.03, 0.05, 0.10]
        result = MultipleComparison.benjamini_hochberg(p_values)

        assert result["method"] == "Benjamini-Hochberg FDR"
        assert result["n_tests"] == 4


class TestVisualization:
    """Test visualization data generation."""

    def test_mosaic_plot_data(self):
        """Test mosaic plot coordinates."""
        table = [[30, 20], [10, 40]]
        result = VisualizationData.mosaic_plot_data(table)

        assert "cells" in result
        assert len(result["cells"]) == 4

    def test_stacked_bar_data(self):
        """Test stacked bar chart data."""
        table = [[30, 20], [10, 40]]
        result = VisualizationData.stacked_bar_data(table)

        assert "bars" in result
        assert len(result["bars"]) == 2


class TestAdditionalStats:
    """Test additional statistics for parity."""

    def test_somers_d(self):
        """Test Somers' D."""
        table = [[20, 5, 2], [3, 15, 8], [1, 6, 20]]
        result = AdditionalStats.somers_d(table)

        assert "d_yx" in result
        assert "d_xy" in result
        assert "symmetric" in result

    def test_tau_c(self):
        """Test Stuart's tau-c."""
        table = [[20, 5, 2], [3, 15, 8], [1, 6, 20]]
        result = AdditionalStats.tau_c(table)

        assert "tau_c" in result
        assert "p_value" in result

    def test_lambda(self):
        """Test Goodman-Kruskal lambda."""
        table = [[30, 10], [15, 45]]
        result = AdditionalStats.goodman_kruskal_lambda(table)

        assert "lambda_col_given_row" in result
        assert "symmetric" in result

    def test_uncertainty_coefficient(self):
        """Test uncertainty coefficient."""
        table = [[30, 10], [15, 45]]
        result = AdditionalStats.uncertainty_coefficient(table)

        assert "u_col_given_row" in result
        assert "mutual_information" in result

    def test_breslow_day(self):
        """Test Breslow-Day test."""
        tables = [
            [[10, 5], [3, 12]],
            [[8, 6], [4, 10]],
            [[12, 3], [5, 15]]
        ]
        result = AdditionalStats.breslow_day_test(tables)

        assert "chi2" in result
        assert "homogeneous" in result

    def test_monte_carlo(self):
        """Test Monte Carlo chi-square."""
        table = [[5, 3], [2, 8]]
        result = AdditionalStats.monte_carlo_chi_square(table, n_sim=1000, seed=42)

        assert "p_value" in result
        assert "chi2_observed" in result

    def test_correspondence_analysis(self):
        """Test correspondence analysis."""
        table = [[20, 10, 5], [5, 25, 10], [3, 8, 30]]
        result = AdditionalStats.correspondence_analysis(table)

        assert "row_coords" in result
        assert "col_coords" in result
        assert "total_inertia" in result

    def test_yates_correction(self):
        """Test Yates correction."""
        table = [[10, 5], [3, 12]]
        result = AdditionalStats.chi_square_yates(table)

        assert "chi2_yates" in result
        assert "chi2_uncorrected" in result
        assert result["chi2_yates"] <= result["chi2_uncorrected"]

    def test_attributable_risk(self):
        """Test attributable risk measures."""
        table = [[30, 70], [10, 90]]  # Exposed vs unexposed
        result = AdditionalStats.attributable_risk(table)

        assert "attributable_risk" in result
        assert "population_attributable_fraction" in result

    def test_detect_outliers_zscore(self):
        """Test z-score outlier detection."""
        values = [1, 2, 3, 4, 5, 100]  # 100 is outlier
        result = AdditionalStats.detect_outliers(values, method="zscore")

        assert result["outlier_count"] >= 1

    def test_detect_outliers_iqr(self):
        """Test IQR outlier detection."""
        values = [1, 2, 3, 4, 5, 100]
        result = AdditionalStats.detect_outliers(values, method="iqr")

        assert len(result["outliers"]) >= 1


class TestValidation:
    """Test input validation."""

    def test_validate_good_table(self):
        """Test validation of good table."""
        valid, msg = StatisticalEngine.validate_contingency_table([[1, 2], [3, 4]])
        assert valid

    def test_validate_empty_table(self):
        """Test validation of empty table."""
        valid, msg = StatisticalEngine.validate_contingency_table([])
        assert not valid

    def test_validate_inconsistent_rows(self):
        """Test validation of inconsistent row lengths."""
        valid, msg = StatisticalEngine.validate_contingency_table([[1, 2], [3, 4, 5]])
        assert not valid

    def test_validate_negative_cells(self):
        """Test validation with negative values."""
        valid, msg = StatisticalEngine.validate_contingency_table([[1, -2], [3, 4]])
        assert not valid


class TestInterpretations:
    """Test effect size interpretations."""

    def test_cramers_v_small(self):
        """Test Cramér's V small effect interpretation."""
        interpretation = StatisticalEngine.interpret_cramers_v(0.05, 1)
        assert interpretation.value == "small"

    def test_cramers_v_medium(self):
        """Test Cramér's V medium effect interpretation."""
        interpretation = StatisticalEngine.interpret_cramers_v(0.2, 1)
        assert interpretation.value == "medium"

    def test_cramers_v_large(self):
        """Test Cramér's V large effect interpretation."""
        interpretation = StatisticalEngine.interpret_cramers_v(0.4, 1)
        assert interpretation.value == "large"


class TestIntegration:
    """Integration tests with realistic scenarios."""

    def test_clinical_trial_analysis(self):
        """Test complete analysis of clinical trial data."""
        table = [[6, 4], [2, 8]]

        chi_sq = StatisticalEngine.chi_square_test(table)
        assert chi_sq.p_value is not None

        post_hoc = StatisticalEngine.post_hoc_analysis(table)
        assert "standardized_residuals" in post_hoc

    def test_survey_data_analysis(self):
        """Test analysis of survey response data."""
        table = [
            [120, 30, 10],
            [40, 100, 20],
            [20, 30, 50]
        ]

        result = StatisticalEngine.chi_square_test(table)
        assert result.p_value < 0.05
        assert result.df == 4

    def test_matched_pairs_analysis(self):
        """Test McNemar analysis for matched pairs."""
        table = [[45, 10], [4, 41]]
        result = StatisticalEngine.mcnemar_test(table)
        assert result.statistic is not None


class TestPerformance:
    """Performance/benchmark tests."""

    def test_chi_square_performance(self):
        """Chi-square should be very fast."""
        import time

        # Use non-zero values to avoid chi-square issues
        table = [[i + 1 for i in range(10)] for _ in range(10)]

        start = time.time()
        for _ in range(100):
            StatisticalEngine.chi_square_test(table)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Chi-square took {elapsed}s for 100 iterations"


# ============================================================================
# Main Test Runner
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
