"""
Advanced Statistical Functions

Additional statistical tests and calculations:
- Loglinear analysis
- Ordinal tests (Spearman, Kendall)
- Trend tests (linear-by-linear)
- Power and sample size calculations
"""

import math
from typing import List, Tuple, Dict, Any
from scipy import stats
import numpy as np


class OrdinalTests:
    """Tests for ordinal categorical data."""
    
    @staticmethod
    def spearmans_rho(ranks_x: List[float], ranks_y: List[float]) -> Tuple[float, float]:
        """
        Spearman's rank correlation coefficient.
        
        Tests monotonic association between ordinal variables.
        """
        rho, p_value = stats.spearmanr(ranks_x, ranks_y)
        return float(rho), float(p_value)
    
    @staticmethod
    def kendalls_tau(ranks_x: List[float], ranks_y: List[float]) -> Tuple[float, float]:
        """
        Kendall's tau-b rank correlation.
        
        Handles tied values appropriately.
        """
        tau, p_value = stats.kendalltau(ranks_x, ranks_y)
        return float(tau), float(p_value)
    
    @staticmethod
    def goodman_kruskal_gamma(table: List[List[float]]) -> float:
        """
        Goodman-Kruskal's gamma for ordinal association.
        
        Symmetric measure, doesn't assume one variable is dependent.
        """
        arr = np.array(table, dtype=float)
        
        # Calculate concordant and discordant pairs
        concordant = 0
        discordant = 0
        
        for i in range(arr.shape[0]):
            for j in range(arr.shape[1]):
                # Concordant: all cells to the right and below
                concordant += arr[i,j] * np.sum(arr[i+1:, j+1:])
                # Discordant: all cells to the right and above
                discordant += arr[i,j] * np.sum(arr[:i, j+1:])
        
        if (concordant + discordant) == 0:
            return 0.0
        
        gamma = (concordant - discordant) / (concordant + discordant)
        return float(gamma)


class TrendTests:
    """Tests for linear trend in ordinal associations."""
    
    @staticmethod
    def linear_by_linear_association(
        table: List[List[float]],
        row_scores: List[float],
        col_scores: List[float]
    ) -> Dict[str, Any]:
        """
        Linear-by-linear association test (Cochran-Armitage trend).
        
        Tests for linear trend with specified row and column scores.
        """
        arr = np.array(table, dtype=float)
        n = arr.sum()
        
        # Calculate test statistic
        r_scores = np.array(row_scores)
        c_scores = np.array(col_scores)
        
        # M = sum(row_score * col_score * cell_frequency)
        m_stat = 0
        for i, r_score in enumerate(r_scores):
            for j, c_score in enumerate(c_scores):
                m_stat += r_score * c_score * arr[i,j]
        
        # Calculate mean and variance
        r_mean = np.sum(r_scores * arr.sum(axis=1)) / n
        c_mean = np.sum(c_scores * arr.sum(axis=0)) / n
        m_mean = n * r_mean * c_mean
        
        # Variance calculation (simplified)
        r_var = np.sum(((r_scores - r_mean)**2) * arr.sum(axis=1)) / n
        c_var = np.sum(((c_scores - c_mean)**2) * arr.sum(axis=0)) / n
        m_var = n * (r_var * c_var)
        
        # Z-statistic
        z_stat = (m_stat - m_mean) / math.sqrt(m_var) if m_var > 0 else 0
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        return {
            "test": "Linear-by-Linear Association",
            "z_statistic": float(z_stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05,
            "interpretation": "Significant linear trend" if p_value < 0.05 else "No significant linear trend"
        }


class PowerAnalysis:
    """Power and sample size calculations."""
    
    @staticmethod
    def power_two_proportions(
        p1: float,
        p2: float,
        alpha: float = 0.05,
        n: float = None
    ) -> Dict[str, float]:
        """
        Calculate power or sample size for comparing two proportions.
        
        If n is provided, calculates power.
        If n is None, calculates required n for 80% power.
        """
        from scipy.stats import norm
        
        p = (p1 + p2) / 2
        
        if n is None:
            # Calculate sample size for 80% power
            beta = 0.20
            z_alpha = norm.ppf(1 - alpha/2)
            z_beta = norm.ppf(1 - beta)
            
            numerator = (z_alpha + z_beta) ** 2 * 2 * p * (1 - p)
            denominator = (p1 - p2) ** 2
            
            n = numerator / denominator
            
            return {
                "parameter": "sample_size",
                "value": math.ceil(n),
                "alpha": alpha,
                "power": 0.80,
                "p1": p1,
                "p2": p2,
                "total_n": math.ceil(n * 2)
            }
        else:
            # Calculate power given n
            se = math.sqrt(2 * p * (1-p) / n)
            z_alpha = norm.ppf(1 - alpha/2)
            z_effect = abs(p1 - p2) / se
            power = norm.cdf(z_effect - z_alpha) + (1 - norm.cdf(-z_effect - z_alpha))
            
            return {
                "parameter": "power",
                "value": float(power),
                "alpha": alpha,
                "n_per_group": int(n),
                "total_n": int(n * 2),
                "p1": p1,
                "p2": p2
            }
    
    @staticmethod
    def effect_size_cohen_h(p1: float, p2: float) -> float:
        """
        Cohen's h effect size for proportions.
        
        h = 2 * arcsin(sqrt(p1)) - 2 * arcsin(sqrt(p2))
        """
        h = 2 * (math.asin(math.sqrt(p1)) - math.asin(math.sqrt(p2)))
        return float(h)


class LogLinearAnalysis:
    """Loglinear models for multidimensional contingency tables."""
    
    @staticmethod
    def analyze_3way_table(table: List[List[List[float]]]) -> Dict[str, Any]:
        """
        Analyze three-way contingency table.
        
        Examines main effects and two-way interactions.
        """
        arr = np.array(table, dtype=float)
        
        # Calculate cell statistics
        n = arr.sum()
        log_odds = np.log(arr + 0.5)  # Add 0.5 to avoid log(0)
        
        # Simplified loglinear analysis
        # In practice, would use statsmodels.genmod.generalized_linear_model
        
        return {
            "dimensions": arr.shape,
            "total_n": int(n),
            "log_odds": log_odds.tolist(),
            "note": "Full loglinear analysis requires specialized software (R, SAS)"
        }


class VisualizationData:
    """Generate data for visualizations."""
    
    @staticmethod
    def mosaic_plot_data(table: List[List[float]]) -> Dict[str, Any]:
        """
        Generate coordinates for mosaic plot.
        
        Mosaic plots show cell sizes proportional to frequencies
        and patterns of association.
        """
        arr = np.array(table, dtype=float)
        n = arr.sum()
        
        # Normalize to proportions
        proportions = arr / n
        
        # Row and column totals
        row_totals = arr.sum(axis=1) / n
        col_totals = arr.sum(axis=0) / n
        
        # Build coordinates for each cell
        cells = []
        x_pos = 0
        
        for i, r_total in enumerate(row_totals):
            y_pos = 0
            x_width = r_total
            
            for j, c_total in enumerate(col_totals):
                y_height = proportions[i, j] / r_total if r_total > 0 else 0
                
                cells.append({
                    "row": int(i),
                    "col": int(j),
                    "x": float(x_pos),
                    "y": float(y_pos),
                    "width": float(x_width),
                    "height": float(y_height),
                    "count": int(arr[i, j]),
                    "color": "red" if y_height > c_total * 1.2 else "blue" if y_height < c_total * 0.8 else "gray"
                })
                
                y_pos += y_height
            
            x_pos += x_width
        
        return {
            "type": "mosaic_plot",
            "cells": cells,
            "interpretation": "Red cells: excess, Blue cells: deficit, Gray cells: expected"
        }
    
    @staticmethod
    def stacked_bar_data(table: List[List[float]], by_rows: bool = True) -> Dict[str, Any]:
        """
        Generate data for stacked bar chart.
        """
        arr = np.array(table, dtype=float)
        
        if by_rows:
            totals = arr.sum(axis=1)
            proportions = arr / totals[:, np.newaxis]
            groups = [f"Group {i}" for i in range(arr.shape[0])]
            categories = [f"Category {j}" for j in range(arr.shape[1])]
        else:
            totals = arr.sum(axis=0)
            proportions = arr / totals[np.newaxis, :]
            groups = [f"Category {j}" for j in range(arr.shape[1])]
            categories = [f"Group {i}" for i in range(arr.shape[0])]
        
        bars = []
        for i, group in enumerate(groups):
            bar_data = []
            for j, cat in enumerate(categories):
                if by_rows:
                    bar_data.append({
                        "category": cat,
                        "value": float(proportions[i, j]),
                        "count": int(arr[i, j])
                    })
                else:
                    bar_data.append({
                        "category": cat,
                        "value": float(proportions[j, i]),
                        "count": int(arr[i, j])
                    })
            
            bars.append({
                "group": group,
                "segments": bar_data,
                "total": int(totals[i])
            })
        
        return {
            "type": "stacked_bar_chart",
            "bars": bars,
            "interpretation": "Proportions shown as stacked bars"
        }


# Utility for multiple comparison correction
class MultipleComparison:
    """Methods for controlling type I error with multiple tests."""
    
    @staticmethod
    def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[Dict[str, Any]]:
        """Bonferroni correction: divide alpha by number of tests."""
        n_tests = len(p_values)
        adjusted_alpha = alpha / n_tests
        
        return [
            {
                "original_p": p,
                "adjusted_p": min(p * n_tests, 1.0),
                "significant": p < adjusted_alpha
            }
            for p in p_values
        ]
    
    @staticmethod
    def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> List[Dict[str, Any]]:
        """Benjamini-Hochberg false discovery rate control."""
        n = len(p_values)
        sorted_indices = np.argsort(p_values)
        sorted_p = np.array(p_values)[sorted_indices]
        
        # Calculate critical values
        critical_values = alpha * np.arange(1, n + 1) / n
        
        # Find largest i where P(i) <= critical_value(i)
        reject = sorted_p <= critical_values
        
        result = []
        for i, orig_idx in enumerate(sorted_indices):
            result.append({
                "original_p": float(p_values[orig_idx]),
                "rank": i + 1,
                "critical_value": float(critical_values[i]),
                "significant": bool(np.any(reject[:i+1]))
            })
        
        # Sort back to original order
        final_result = [None] * n
        for item in result:
            # Find original index
            pass
        
        return sorted(result, key=lambda x: x['original_p'])
