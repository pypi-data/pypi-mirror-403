"""
Enhanced Crosstabs MCP Server

Comprehensive statistical analysis tool for contingency tables with:
- All standard and advanced statistical tests
- Confidence intervals for all estimates
- Assumption checking and recommendations
- Natural language interpretations
- Multiple input format support
- Visualization data export
"""

import json
import math
from typing import Optional, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import numpy as np
from scipy import stats
from scipy.stats import chi2, norm, binomtest
from mcp.server.fastmcp import FastMCP


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class EffectSizeInterpretation(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    VERY_LARGE = "very_large"


@dataclass
class ConfidenceInterval:
    parameter: str
    lower: float
    upper: float
    level: float
    method: str


@dataclass
class EffectSize:
    name: str
    value: float
    interpretation: EffectSizeInterpretation


@dataclass
class AssumptionCheck:
    valid: bool
    warnings: List[str]
    notes: str


@dataclass
class StatisticalResult:
    test_name: str
    statistic: Optional[float]
    p_value: Optional[float]
    df: Optional[int]
    effect_sizes: List[EffectSize]
    confidence_intervals: List[ConfidenceInterval]
    assumptions: AssumptionCheck
    interpretation: str
    recommendations: List[str]
    post_hoc: Optional[dict] = None


# ============================================================================
# STATISTICAL ENGINE
# ============================================================================

class StatisticalEngine:
    """Core statistical computation engine."""

    @staticmethod
    def validate_contingency_table(table: List[List[float]]) -> Tuple[bool, str]:
        """Validate contingency table format."""
        if not table or not table[0]:
            return False, "Empty contingency table"
        if not all(len(row) == len(table[0]) for row in table):
            return False, "Inconsistent row lengths"
        if any(any(x < 0 for x in row) for row in table):
            return False, "Negative cell counts not allowed"
        return True, "Valid"

    @staticmethod
    def check_expected_frequencies(table: List[List[float]]) -> AssumptionCheck:
        """Check chi-square assumptions (expected frequencies)."""
        arr = np.array(table, dtype=float)
        n = arr.sum()
        row_totals = arr.sum(axis=1)
        col_totals = arr.sum(axis=0)

        expected = np.outer(row_totals, col_totals) / n

        warnings = []
        if (expected < 1).any():
            count = (expected < 1).sum()
            warnings.append(f"{count} cells have expected frequency < 1")

        if (expected < 5).any():
            pct = (expected < 5).sum() / expected.size * 100
            warnings.append(f"{pct:.1f}% of cells have expected frequency < 5")

        notes = "Chi-square test valid" if not warnings else "Consider Fisher's exact test or CMH"

        return AssumptionCheck(
            valid=len(warnings) == 0,
            warnings=warnings,
            notes=notes
        )

    @staticmethod
    def chi_square_test(table: List[List[float]]) -> StatisticalResult:
        """Pearson's chi-square test of independence."""
        valid, msg = StatisticalEngine.validate_contingency_table(table)
        if not valid:
            raise ValueError(msg)

        arr = np.array(table, dtype=float)
        chi2_stat, p_val, dof, expected = stats.chi2_contingency(arr)

        # Cramér's V effect size
        n = arr.sum()
        min_dim = min(arr.shape[0] - 1, arr.shape[1] - 1)
        cramers_v = math.sqrt(chi2_stat / (n * min_dim)) if min_dim > 0 else 0

        # Cramér's V interpretation
        cramers_interpretation = StatisticalEngine.interpret_cramers_v(cramers_v, min_dim)

        assumptions = StatisticalEngine.check_expected_frequencies(table)

        interpretation = (
            f"χ² = {chi2_stat:.4f}, df = {int(dof)}, p = {p_val:.4f}. "
            f"{'Significant' if p_val < 0.05 else 'Not significant'} association between variables. "
            f"Effect size (Cramér's V = {cramers_v:.4f}) is {cramers_interpretation.value}."
        )

        return StatisticalResult(
            test_name="Pearson's Chi-Square Test",
            statistic=chi2_stat,
            p_value=p_val,
            df=int(dof),
            effect_sizes=[
                EffectSize("Cramér's V", cramers_v, cramers_interpretation)
            ],
            confidence_intervals=[],
            assumptions=assumptions,
            interpretation=interpretation,
            recommendations=_get_chi_square_recommendations(p_val, assumptions)
        )

    @staticmethod
    def interpret_cramers_v(v: float, min_dim: int) -> EffectSizeInterpretation:
        """Interpret Cramér's V based on degrees of freedom."""
        if v < 0.1:
            return EffectSizeInterpretation.SMALL
        elif v < 0.3:
            return EffectSizeInterpretation.MEDIUM
        elif v < 0.5:
            return EffectSizeInterpretation.LARGE
        else:
            return EffectSizeInterpretation.VERY_LARGE

    @staticmethod
    def fishers_exact_test(table: List[List[float]]) -> StatisticalResult:
        """Fisher's exact test for 2×2 tables."""
        arr = np.array(table, dtype=float)
        if arr.shape != (2, 2):
            raise ValueError("Fisher's exact test requires a 2×2 table")

        a, b, c, d = arr[0, 0], arr[0, 1], arr[1, 0], arr[1, 1]

        # Use scipy's fisher_exact
        odds_ratio, p_val = stats.fisher_exact([[a, b], [c, d]])

        # Odds ratio CI using exact method
        or_ci = StatisticalEngine.odds_ratio_ci_exact(a, b, c, d)

        interpretation = (
            f"Odds Ratio = {odds_ratio:.4f} (95% CI: {or_ci[0]:.4f} - {or_ci[1]:.4f}). "
            f"Two-tailed p = {p_val:.4f}. "
            f"{'Significant' if p_val < 0.05 else 'Not significant'} association."
        )

        return StatisticalResult(
            test_name="Fisher's Exact Test",
            statistic=odds_ratio,
            p_value=p_val,
            df=None,
            effect_sizes=[],
            confidence_intervals=[
                ConfidenceInterval("Odds Ratio", or_ci[0], or_ci[1], 0.95, "Exact")
            ],
            assumptions=AssumptionCheck(
                valid=True,
                warnings=[],
                notes="No distributional assumptions"
            ),
            interpretation=interpretation,
            recommendations=["Exact test appropriate for small samples"]
        )

    @staticmethod
    def mcnemar_test(table: List[List[float]]) -> StatisticalResult:
        """McNemar's test for paired categorical data."""
        arr = np.array(table, dtype=float)
        if arr.shape != (2, 2):
            raise ValueError("McNemar's test requires a 2×2 table")

        # b = discordant (success, failure), c = discordant (failure, success)
        b, c = arr[0, 1], arr[1, 0]

        # Handle edge case: no discordant pairs
        if (b + c) == 0:
            mcnemar_stat = 0.0
            p_val = 1.0
            p_exact = 1.0
        else:
            # McNemar statistic with continuity correction
            mcnemar_stat = (abs(b - c) - 1) ** 2 / (b + c)
            p_val = 1 - chi2.cdf(mcnemar_stat, df=1)

            # Binomial exact test (using updated scipy function)
            result = binomtest(int(min(b, c)), int(b + c), 0.5, alternative='two-sided')
            p_exact = result.pvalue

        interpretation = (
            f"McNemar χ² = {mcnemar_stat:.4f}, p = {p_val:.4f}. "
            f"Exact binomial p = {p_exact:.4f}. "
            f"{'Significant' if p_exact < 0.05 else 'No significant'} difference in paired proportions."
        )

        return StatisticalResult(
            test_name="McNemar's Test",
            statistic=mcnemar_stat,
            p_value=p_val,
            df=1,
            effect_sizes=[],
            confidence_intervals=[],
            assumptions=AssumptionCheck(
                valid=True,
                warnings=[],
                notes="Valid for paired data"
            ),
            interpretation=interpretation,
            recommendations=["Use exact binomial test if b+c < 20"]
        )

    @staticmethod
    def g_test(table: List[List[float]]) -> StatisticalResult:
        """G-test (likelihood ratio test) for contingency tables."""
        valid, msg = StatisticalEngine.validate_contingency_table(table)
        if not valid:
            raise ValueError(msg)

        arr = np.array(table, dtype=float)
        n = arr.sum()
        row_totals = arr.sum(axis=1)
        col_totals = arr.sum(axis=0)
        expected = np.outer(row_totals, col_totals) / n

        # Calculate G statistic
        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = np.where(arr > 0, arr / expected, 1)
            g_stat = 2 * np.nansum(arr * np.log(ratio))

        dof = (arr.shape[0] - 1) * (arr.shape[1] - 1)
        p_val = 1 - chi2.cdf(g_stat, dof)

        # Cramér's V for effect size
        min_dim = min(arr.shape[0] - 1, arr.shape[1] - 1)
        cramers_v = math.sqrt(g_stat / (n * min_dim)) if min_dim > 0 else 0
        cramers_interpretation = StatisticalEngine.interpret_cramers_v(cramers_v, min_dim)

        assumptions = StatisticalEngine.check_expected_frequencies(table)

        interpretation = (
            f"G = {g_stat:.4f}, df = {dof}, p = {p_val:.4f}. "
            f"{'Significant' if p_val < 0.05 else 'Not significant'} association. "
            f"Effect size (Cramér's V = {cramers_v:.4f}) is {cramers_interpretation.value}."
        )

        return StatisticalResult(
            test_name="G-Test (Likelihood Ratio)",
            statistic=g_stat,
            p_value=p_val,
            df=dof,
            effect_sizes=[
                EffectSize("Cramér's V", cramers_v, cramers_interpretation)
            ],
            confidence_intervals=[],
            assumptions=assumptions,
            interpretation=interpretation,
            recommendations=["G-test is preferred for small samples over chi-square"]
        )

    @staticmethod
    def cramers_v_corrected(table: List[List[float]]) -> dict:
        """Bias-corrected Cramér's V (Bergsma 2013)."""
        valid, msg = StatisticalEngine.validate_contingency_table(table)
        if not valid:
            raise ValueError(msg)

        arr = np.array(table, dtype=float)
        chi2_stat, _, _, _ = stats.chi2_contingency(arr)
        n = arr.sum()
        rows, cols = arr.shape

        if n <= 1 or rows <= 1 or cols <= 1:
            return {"cramers_v_corrected": 0, "cramers_v_standard": 0}

        # Standard Cramér's V
        min_dim = min(rows - 1, cols - 1)
        cramers_v_standard = math.sqrt(chi2_stat / (n * min_dim)) if min_dim > 0 else 0

        # Bias-corrected version
        phi2 = chi2_stat / n
        phi2_corrected = max(0, phi2 - ((rows - 1) * (cols - 1)) / (n - 1))
        rows_corrected = rows - ((rows - 1) ** 2) / (n - 1)
        cols_corrected = cols - ((cols - 1) ** 2) / (n - 1)
        min_dim_corrected = min(rows_corrected, cols_corrected) - 1

        cramers_v_corrected = math.sqrt(phi2_corrected / min_dim_corrected) if min_dim_corrected > 0 else 0

        return {
            "cramers_v_corrected": round(cramers_v_corrected, 4),
            "cramers_v_standard": round(cramers_v_standard, 4),
            "interpretation": StatisticalEngine.interpret_cramers_v(cramers_v_corrected, min_dim).value,
            "note": "Bias-corrected version recommended for small samples"
        }

    @staticmethod
    def weighted_kappa(table: List[List[float]], weight_type: str = "quadratic") -> dict:
        """Weighted Cohen's Kappa for ordinal agreement."""
        arr = np.array(table, dtype=float)
        if arr.shape[0] != arr.shape[1]:
            raise ValueError("Weighted kappa requires a square matrix")

        n_categories = arr.shape[0]
        n = arr.sum()

        # Create weight matrix
        weights = np.zeros((n_categories, n_categories))
        for i in range(n_categories):
            for j in range(n_categories):
                if weight_type == "linear":
                    weights[i, j] = 1 - abs(i - j) / (n_categories - 1)
                else:  # quadratic
                    weights[i, j] = 1 - ((i - j) ** 2) / ((n_categories - 1) ** 2)

        # Proportions
        p_observed = arr / n
        row_marginals = arr.sum(axis=1) / n
        col_marginals = arr.sum(axis=0) / n
        p_expected = np.outer(row_marginals, col_marginals)

        # Weighted observed and expected agreement
        po = np.sum(weights * p_observed)
        pe = np.sum(weights * p_expected)

        # Kappa
        kappa = (po - pe) / (1 - pe) if (1 - pe) > 0 else 0

        # Standard error (Fleiss-Cohen)
        se = math.sqrt(2 * (pe + pe**2 - np.sum(weights * (p_expected * (p_observed + p_expected)))) / (n * (1 - pe)**2))

        # Interpretation
        if kappa < 0:
            interp = "poor (less than chance)"
        elif kappa < 0.20:
            interp = "slight"
        elif kappa < 0.40:
            interp = "fair"
        elif kappa < 0.60:
            interp = "moderate"
        elif kappa < 0.80:
            interp = "substantial"
        else:
            interp = "almost perfect"

        return {
            "weighted_kappa": round(kappa, 4),
            "standard_error": round(se, 4),
            "ci_lower": round(kappa - 1.96 * se, 4),
            "ci_upper": round(kappa + 1.96 * se, 4),
            "weight_type": weight_type,
            "interpretation": interp
        }

    @staticmethod
    def cohens_kappa(table: List[List[float]]) -> dict:
        """Cohen's Kappa for agreement (unweighted)."""
        arr = np.array(table, dtype=float)
        if arr.shape[0] != arr.shape[1]:
            raise ValueError("Cohen's kappa requires a square matrix")

        n = arr.sum()

        # Observed agreement
        po = np.trace(arr) / n

        # Expected agreement
        row_marginals = arr.sum(axis=1) / n
        col_marginals = arr.sum(axis=0) / n
        pe = np.sum(row_marginals * col_marginals)

        # Kappa
        kappa = (po - pe) / (1 - pe) if (1 - pe) > 0 else 0

        # Standard error
        se = math.sqrt(po * (1 - po) / (n * (1 - pe)**2))

        # Interpretation
        if kappa < 0:
            interp = "poor (less than chance)"
        elif kappa < 0.20:
            interp = "slight"
        elif kappa < 0.40:
            interp = "fair"
        elif kappa < 0.60:
            interp = "moderate"
        elif kappa < 0.80:
            interp = "substantial"
        else:
            interp = "almost perfect"

        return {
            "kappa": round(kappa, 4),
            "standard_error": round(se, 4),
            "ci_lower": round(kappa - 1.96 * se, 4),
            "ci_upper": round(kappa + 1.96 * se, 4),
            "observed_agreement": round(po, 4),
            "expected_agreement": round(pe, 4),
            "interpretation": interp
        }

    @staticmethod
    def cmh_test(tables: List[List[List[float]]]) -> dict:
        """Cochran-Mantel-Haenszel test for stratified 2x2 tables."""
        for i, table in enumerate(tables):
            if len(table) != 2 or len(table[0]) != 2:
                raise ValueError(f"Stratum {i}: CMH requires all tables to be 2x2")

        numerator = 0
        denominator = 0
        or_num = 0
        or_denom = 0

        for table in tables:
            a, b = table[0][0], table[0][1]
            c, d = table[1][0], table[1][1]
            n = a + b + c + d

            if n == 0:
                continue

            n1 = a + b  # row 1 total
            n0 = c + d  # row 2 total
            m1 = a + c  # col 1 total

            expected_a = (n1 * m1) / n
            var_a = (n1 * n0 * m1 * (n - m1)) / (n * n * (n - 1)) if n > 1 else 0

            numerator += a - expected_a
            denominator += var_a
            or_num += (a * d) / n
            or_denom += (b * c) / n

        chi2_stat = (numerator ** 2) / denominator if denominator > 0 else 0
        p_val = 1 - chi2.cdf(chi2_stat, 1)
        common_or = or_num / or_denom if or_denom > 0 else None

        # CI for common odds ratio
        if common_or and common_or > 0:
            log_or = math.log(common_or)
            # Simplified SE calculation
            se_log_or = 1 / math.sqrt(denominator) if denominator > 0 else 0
            or_ci_lower = math.exp(log_or - 1.96 * se_log_or)
            or_ci_upper = math.exp(log_or + 1.96 * se_log_or)
        else:
            or_ci_lower = or_ci_upper = None

        return {
            "chi2": round(chi2_stat, 4),
            "p_value": round(p_val, 4),
            "df": 1,
            "common_odds_ratio": round(common_or, 4) if common_or else None,
            "or_ci_lower": round(or_ci_lower, 4) if or_ci_lower else None,
            "or_ci_upper": round(or_ci_upper, 4) if or_ci_upper else None,
            "n_strata": len(tables),
            "interpretation": f"{'Significant' if p_val < 0.05 else 'Not significant'} association controlling for strata"
        }

    @staticmethod
    def odds_ratio_ci_exact(a: float, b: float, c: float, d: float) -> Tuple[float, float]:
        """Calculate exact confidence interval for odds ratio using log scale."""
        if a == 0 or b == 0 or c == 0 or d == 0:
            a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5

        or_val = (a * d) / (b * c)
        log_or = math.log(or_val)
        se_log_or = math.sqrt(1/a + 1/b + 1/c + 1/d)
        z_crit = 1.96

        ci_lower = math.exp(log_or - z_crit * se_log_or)
        ci_upper = math.exp(log_or + z_crit * se_log_or)

        return (ci_lower, ci_upper)

    @staticmethod
    def relative_risk(table: List[List[float]]) -> dict:
        """Calculate relative risk with confidence interval for 2x2 table."""
        arr = np.array(table, dtype=float)
        if arr.shape != (2, 2):
            raise ValueError("Relative risk requires a 2×2 table")

        a, b = arr[0, 0], arr[0, 1]
        c, d = arr[1, 0], arr[1, 1]

        # Risk in exposed vs unexposed
        risk_exposed = a / (a + b) if (a + b) > 0 else 0
        risk_unexposed = c / (c + d) if (c + d) > 0 else 0

        rr = risk_exposed / risk_unexposed if risk_unexposed > 0 else float('inf')

        # CI using log transformation
        if a > 0 and b > 0 and c > 0 and d > 0:
            log_rr = math.log(rr)
            se_log_rr = math.sqrt(b/(a*(a+b)) + d/(c*(c+d)))
            ci_lower = math.exp(log_rr - 1.96 * se_log_rr)
            ci_upper = math.exp(log_rr + 1.96 * se_log_rr)
        else:
            ci_lower = ci_upper = None

        return {
            "relative_risk": round(rr, 4) if rr != float('inf') else None,
            "ci_lower": round(ci_lower, 4) if ci_lower else None,
            "ci_upper": round(ci_upper, 4) if ci_upper else None,
            "risk_exposed": round(risk_exposed, 4),
            "risk_unexposed": round(risk_unexposed, 4),
            "interpretation": f"Exposed group has {rr:.2f}x the risk of unexposed group" if rr != float('inf') else "Cannot calculate (zero in unexposed group)"
        }

    @staticmethod
    def risk_difference(table: List[List[float]]) -> dict:
        """Calculate risk difference (absolute risk reduction) for 2x2 table."""
        arr = np.array(table, dtype=float)
        if arr.shape != (2, 2):
            raise ValueError("Risk difference requires a 2×2 table")

        a, b = arr[0, 0], arr[0, 1]
        c, d = arr[1, 0], arr[1, 1]

        n1 = a + b
        n0 = c + d

        risk_exposed = a / n1 if n1 > 0 else 0
        risk_unexposed = c / n0 if n0 > 0 else 0

        rd = risk_exposed - risk_unexposed

        # SE and CI
        se = math.sqrt((a*b)/(n1**3) + (c*d)/(n0**3)) if n1 > 0 and n0 > 0 else 0
        ci_lower = rd - 1.96 * se
        ci_upper = rd + 1.96 * se

        # NNT (Number Needed to Treat)
        nnt = 1 / abs(rd) if rd != 0 else float('inf')

        return {
            "risk_difference": round(rd, 4),
            "ci_lower": round(ci_lower, 4),
            "ci_upper": round(ci_upper, 4),
            "standard_error": round(se, 4),
            "nnt": round(nnt, 1) if nnt != float('inf') else None,
            "interpretation": f"Absolute risk difference: {rd*100:.1f}%"
        }

    @staticmethod
    def proportion_ci(successes: float, total: float, method: str = "wilson") -> Tuple[float, float]:
        """Calculate confidence interval for a proportion."""
        p = successes / total if total > 0 else 0

        if method == "wilson":
            z = 1.96
            denom = 1 + z**2 / total
            center = (p + z**2 / (2 * total)) / denom
            margin = z * math.sqrt(p * (1-p) / total + z**2 / (4 * total**2)) / denom
            return (max(0, center - margin), min(1, center + margin))

        elif method == "agresti":
            z = 1.96
            n_adj = total + z**2
            p_adj = (successes + z**2 / 2) / n_adj
            margin = z * math.sqrt(p_adj * (1 - p_adj) / n_adj)
            return (max(0, p_adj - margin), min(1, p_adj + margin))

        else:  # Normal approximation
            z = 1.96
            margin = z * math.sqrt(p * (1-p) / total)
            return (max(0, p - margin), min(1, p + margin))

    @staticmethod
    def standardized_residuals(table: List[List[float]]) -> List[List[float]]:
        """Calculate standardized residuals from chi-square test."""
        arr = np.array(table, dtype=float)
        n = arr.sum()
        row_totals = arr.sum(axis=1)
        col_totals = arr.sum(axis=0)

        expected = np.outer(row_totals, col_totals) / n
        residuals = (arr - expected) / np.sqrt(expected)

        return residuals.tolist()

    @staticmethod
    def adjusted_residuals(table: List[List[float]]) -> List[List[float]]:
        """Calculate adjusted (standardized) residuals."""
        arr = np.array(table, dtype=float)
        n = arr.sum()
        row_totals = arr.sum(axis=1)
        col_totals = arr.sum(axis=0)

        expected = np.outer(row_totals, col_totals) / n

        # Adjustment factors
        row_props = row_totals / n
        col_props = col_totals / n

        adjusted = np.zeros_like(arr)
        for i in range(arr.shape[0]):
            for j in range(arr.shape[1]):
                denominator = math.sqrt(expected[i, j] * (1 - row_props[i]) * (1 - col_props[j]))
                adjusted[i, j] = (arr[i, j] - expected[i, j]) / denominator if denominator > 0 else 0

        return adjusted.tolist()

    @staticmethod
    def post_hoc_analysis(table: List[List[float]]) -> dict:
        """Generate post-hoc analysis after significant chi-square."""
        residuals = StatisticalEngine.standardized_residuals(table)
        adjusted = StatisticalEngine.adjusted_residuals(table)

        arr = np.array(table, dtype=float)
        n = arr.sum()
        row_totals = arr.sum(axis=1)
        col_totals = arr.sum(axis=0)
        expected = np.outer(row_totals, col_totals) / n

        # Contribution to chi-square
        contributions = ((arr - expected) ** 2) / expected
        chi2_total = contributions.sum()
        contrib_pct = contributions / chi2_total * 100 if chi2_total > 0 else contributions * 0

        return {
            "standardized_residuals": [[round(x, 4) for x in row] for row in residuals],
            "adjusted_residuals": [[round(x, 4) for x in row] for row in adjusted],
            "chi_square_contributions": [[round(x, 4) for x in row] for row in contributions.tolist()],
            "contribution_percentages": [[round(x, 2) for x in row] for row in contrib_pct.tolist()],
            "interpretation": "Cells with |adjusted residual| > 2 deviate significantly from expected"
        }


# ============================================================================
# ORDINAL STATISTICS (from advanced_stats.py)
# ============================================================================

class OrdinalTests:
    """Tests for ordinal categorical data."""

    @staticmethod
    def spearmans_rho(ranks_x: List[float], ranks_y: List[float]) -> dict:
        """Spearman's rank correlation coefficient."""
        rho, p_value = stats.spearmanr(ranks_x, ranks_y)

        # Interpretation
        if abs(rho) < 0.3:
            interp = "weak"
        elif abs(rho) < 0.7:
            interp = "moderate"
        else:
            interp = "strong"

        return {
            "rho": round(float(rho), 4),
            "p_value": round(float(p_value), 4),
            "interpretation": f"{interp} {'positive' if rho > 0 else 'negative'} monotonic relationship"
        }

    @staticmethod
    def kendalls_tau(ranks_x: List[float], ranks_y: List[float]) -> dict:
        """Kendall's tau-b rank correlation."""
        tau, p_value = stats.kendalltau(ranks_x, ranks_y)

        if abs(tau) < 0.3:
            interp = "weak"
        elif abs(tau) < 0.7:
            interp = "moderate"
        else:
            interp = "strong"

        return {
            "tau": round(float(tau), 4),
            "p_value": round(float(p_value), 4),
            "interpretation": f"{interp} {'positive' if tau > 0 else 'negative'} concordance"
        }

    @staticmethod
    def goodman_kruskal_gamma(table: List[List[float]]) -> dict:
        """Goodman-Kruskal's gamma for ordinal association."""
        arr = np.array(table, dtype=float)

        concordant = 0
        discordant = 0

        for i in range(arr.shape[0]):
            for j in range(arr.shape[1]):
                concordant += arr[i, j] * np.sum(arr[i+1:, j+1:])
                discordant += arr[i, j] * np.sum(arr[:i, j+1:])

        if (concordant + discordant) == 0:
            gamma = 0
        else:
            gamma = (concordant - discordant) / (concordant + discordant)

        # ASE for gamma
        n = arr.sum()
        if n > 0 and (concordant + discordant) > 0:
            ase = 2 * math.sqrt(concordant * discordant) / ((concordant + discordant) * math.sqrt(n))
        else:
            ase = 0

        return {
            "gamma": round(float(gamma), 4),
            "ase": round(ase, 4),
            "ci_lower": round(gamma - 1.96 * ase, 4),
            "ci_upper": round(gamma + 1.96 * ase, 4),
            "concordant_pairs": int(concordant),
            "discordant_pairs": int(discordant),
            "interpretation": f"{'Strong' if abs(gamma) > 0.7 else 'Moderate' if abs(gamma) > 0.3 else 'Weak'} ordinal association"
        }


# ============================================================================
# TREND TESTS
# ============================================================================

class TrendTests:
    """Tests for linear trend in ordinal associations."""

    @staticmethod
    def linear_by_linear(table: List[List[float]],
                         row_scores: Optional[List[float]] = None,
                         col_scores: Optional[List[float]] = None) -> dict:
        """Linear-by-linear association test (Cochran-Armitage trend)."""
        arr = np.array(table, dtype=float)
        n = arr.sum()
        rows, cols = arr.shape

        # Default to integer scores if not provided
        if row_scores is None:
            row_scores = list(range(rows))
        if col_scores is None:
            col_scores = list(range(cols))

        r_scores = np.array(row_scores)
        c_scores = np.array(col_scores)

        # M = sum(row_score * col_score * cell_frequency)
        m_stat = 0
        for i, r_score in enumerate(r_scores):
            for j, c_score in enumerate(c_scores):
                m_stat += r_score * c_score * arr[i, j]

        # Calculate mean and variance
        r_mean = np.sum(r_scores * arr.sum(axis=1)) / n
        c_mean = np.sum(c_scores * arr.sum(axis=0)) / n
        m_mean = n * r_mean * c_mean

        r_var = np.sum(((r_scores - r_mean)**2) * arr.sum(axis=1)) / n
        c_var = np.sum(((c_scores - c_mean)**2) * arr.sum(axis=0)) / n
        m_var = n * (r_var * c_var)

        # Z-statistic
        z_stat = (m_stat - m_mean) / math.sqrt(m_var) if m_var > 0 else 0
        p_value = 2 * (1 - norm.cdf(abs(z_stat)))

        return {
            "z_statistic": round(float(z_stat), 4),
            "p_value": round(float(p_value), 4),
            "significant": p_value < 0.05,
            "interpretation": "Significant linear trend" if p_value < 0.05 else "No significant linear trend"
        }


# ============================================================================
# POWER ANALYSIS
# ============================================================================

class PowerAnalysis:
    """Power and sample size calculations."""

    @staticmethod
    def power_two_proportions(p1: float, p2: float,
                              alpha: float = 0.05,
                              n: Optional[float] = None,
                              power: float = 0.80) -> dict:
        """
        Calculate power or sample size for comparing two proportions.
        If n is provided, calculates power. Otherwise calculates required n.
        """
        p = (p1 + p2) / 2

        if n is None:
            # Calculate sample size for target power
            z_alpha = norm.ppf(1 - alpha/2)
            z_beta = norm.ppf(power)

            numerator = (z_alpha + z_beta) ** 2 * 2 * p * (1 - p)
            denominator = (p1 - p2) ** 2

            n_required = math.ceil(numerator / denominator) if denominator > 0 else float('inf')

            return {
                "parameter": "sample_size",
                "n_per_group": int(n_required) if n_required != float('inf') else None,
                "total_n": int(n_required * 2) if n_required != float('inf') else None,
                "alpha": alpha,
                "power": power,
                "p1": p1,
                "p2": p2,
                "effect_size_h": round(PowerAnalysis.cohens_h(p1, p2), 4)
            }
        else:
            # Calculate power given n
            se = math.sqrt(2 * p * (1-p) / n)
            z_alpha = norm.ppf(1 - alpha/2)
            z_effect = abs(p1 - p2) / se if se > 0 else 0
            # Power = P(reject H0 | H1 true) = Phi(z_effect - z_alpha)
            calculated_power = norm.cdf(z_effect - z_alpha)
            # Clamp to [0, 1] for numerical stability
            calculated_power = max(0.0, min(1.0, calculated_power))

            return {
                "parameter": "power",
                "power": round(float(calculated_power), 4),
                "alpha": alpha,
                "n_per_group": int(n),
                "total_n": int(n * 2),
                "p1": p1,
                "p2": p2,
                "effect_size_h": round(PowerAnalysis.cohens_h(p1, p2), 4)
            }

    @staticmethod
    def cohens_h(p1: float, p2: float) -> float:
        """Cohen's h effect size for proportions."""
        h = 2 * (math.asin(math.sqrt(p1)) - math.asin(math.sqrt(p2)))
        return float(h)


# ============================================================================
# MULTIPLE COMPARISON CORRECTIONS
# ============================================================================

class MultipleComparison:
    """Methods for controlling type I error with multiple tests."""

    @staticmethod
    def bonferroni(p_values: List[float], alpha: float = 0.05) -> dict:
        """Bonferroni correction: divide alpha by number of tests."""
        n_tests = len(p_values)
        adjusted_alpha = alpha / n_tests

        results = []
        for i, p in enumerate(p_values):
            results.append({
                "test": i + 1,
                "original_p": round(p, 4),
                "adjusted_p": round(min(p * n_tests, 1.0), 4),
                "significant": p < adjusted_alpha
            })

        return {
            "method": "Bonferroni",
            "n_tests": n_tests,
            "adjusted_alpha": round(adjusted_alpha, 4),
            "results": results,
            "n_significant": sum(1 for r in results if r["significant"])
        }

    @staticmethod
    def benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> dict:
        """Benjamini-Hochberg false discovery rate control."""
        n = len(p_values)
        sorted_indices = np.argsort(p_values)
        sorted_p = np.array(p_values)[sorted_indices]

        # Calculate critical values
        critical_values = alpha * np.arange(1, n + 1) / n

        # Find largest i where P(i) <= critical_value(i)
        significant = np.zeros(n, dtype=bool)
        max_significant = -1
        for i in range(n):
            if sorted_p[i] <= critical_values[i]:
                max_significant = i

        if max_significant >= 0:
            significant[:max_significant + 1] = True

        # Map back to original order
        results = []
        for orig_idx in range(n):
            sorted_pos = np.where(sorted_indices == orig_idx)[0][0]
            results.append({
                "test": orig_idx + 1,
                "original_p": round(p_values[orig_idx], 4),
                "rank": int(sorted_pos + 1),
                "critical_value": round(float(critical_values[sorted_pos]), 4),
                "significant": bool(significant[sorted_pos])
            })

        return {
            "method": "Benjamini-Hochberg FDR",
            "n_tests": n,
            "alpha": alpha,
            "results": results,
            "n_significant": int(np.sum(significant))
        }


# ============================================================================
# VISUALIZATION DATA
# ============================================================================

class VisualizationData:
    """Generate data for visualizations."""

    @staticmethod
    def mosaic_plot_data(table: List[List[float]],
                        row_labels: Optional[List[str]] = None,
                        col_labels: Optional[List[str]] = None) -> dict:
        """Generate coordinates for mosaic plot."""
        arr = np.array(table, dtype=float)
        n = arr.sum()
        rows, cols = arr.shape

        if row_labels is None:
            row_labels = [f"Row_{i}" for i in range(rows)]
        if col_labels is None:
            col_labels = [f"Col_{j}" for j in range(cols)]

        # Calculate residuals for coloring
        row_totals = arr.sum(axis=1)
        col_totals = arr.sum(axis=0)
        expected = np.outer(row_totals, col_totals) / n
        residuals = (arr - expected) / np.sqrt(expected)

        # Normalize to proportions
        proportions = arr / n
        row_props = row_totals / n

        cells = []
        x_pos = 0

        for i, r_prop in enumerate(row_props):
            y_pos = 0
            x_width = float(r_prop)

            for j in range(cols):
                y_height = proportions[i, j] / r_prop if r_prop > 0 else 0
                residual = float(residuals[i, j])

                # Color based on residual
                if residual > 2:
                    color = "strong_positive"
                elif residual > 0:
                    color = "weak_positive"
                elif residual < -2:
                    color = "strong_negative"
                else:
                    color = "weak_negative"

                cells.append({
                    "row": int(i),
                    "col": int(j),
                    "row_label": row_labels[i],
                    "col_label": col_labels[j],
                    "x": round(x_pos, 4),
                    "y": round(y_pos, 4),
                    "width": round(x_width, 4),
                    "height": round(float(y_height), 4),
                    "count": int(arr[i, j]),
                    "residual": round(residual, 4),
                    "color": color
                })

                y_pos += y_height

            x_pos += x_width

        return {
            "type": "mosaic_plot",
            "cells": cells,
            "row_labels": row_labels,
            "col_labels": col_labels,
            "interpretation": "Colors indicate deviation from expected: blue=deficit, red=excess"
        }

    @staticmethod
    def stacked_bar_data(table: List[List[float]],
                        by_rows: bool = True,
                        row_labels: Optional[List[str]] = None,
                        col_labels: Optional[List[str]] = None) -> dict:
        """Generate data for stacked bar chart."""
        arr = np.array(table, dtype=float)
        rows, cols = arr.shape

        if row_labels is None:
            row_labels = [f"Row_{i}" for i in range(rows)]
        if col_labels is None:
            col_labels = [f"Col_{j}" for j in range(cols)]

        if by_rows:
            totals = arr.sum(axis=1)
            proportions = arr / totals[:, np.newaxis]
            groups = row_labels
            categories = col_labels
        else:
            totals = arr.sum(axis=0)
            proportions = arr / totals[np.newaxis, :]
            groups = col_labels
            categories = row_labels

        bars = []
        for i, group in enumerate(groups):
            segments = []
            for j, cat in enumerate(categories):
                if by_rows:
                    prop = proportions[i, j]
                    count = arr[i, j]
                else:
                    prop = proportions[j, i]
                    count = arr[j, i]

                segments.append({
                    "category": cat,
                    "proportion": round(float(prop), 4),
                    "count": int(count)
                })

            bars.append({
                "group": group,
                "segments": segments,
                "total": int(totals[i])
            })

        return {
            "type": "stacked_bar_chart",
            "orientation": "by_rows" if by_rows else "by_columns",
            "bars": bars,
            "categories": categories
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_chi_square_recommendations(p_val: float, assumptions: AssumptionCheck) -> List[str]:
    """Generate recommendations based on chi-square results."""
    recs = []

    if not assumptions.valid:
        recs.append("Assumption violated: Consider Fisher's exact or CMH test")

    if p_val >= 0.05:
        recs.append("No significant association detected; check power")
    elif p_val < 0.001:
        recs.append("Very strong association; examine post-hoc residuals")

    return recs


def format_statistical_result(result: StatisticalResult) -> dict:
    """Convert StatisticalResult to JSON-serializable dict."""
    return {
        "test_name": result.test_name,
        "statistic": result.statistic,
        "p_value": result.p_value,
        "degrees_of_freedom": result.df,
        "effect_sizes": [
            {
                "name": es.name,
                "value": round(es.value, 4),
                "interpretation": es.interpretation.value
            }
            for es in result.effect_sizes
        ],
        "confidence_intervals": [
            {
                "parameter": ci.parameter,
                "lower": round(ci.lower, 4),
                "upper": round(ci.upper, 4),
                "level": ci.level,
                "method": ci.method
            }
            for ci in result.confidence_intervals
        ],
        "assumptions": {
            "valid": result.assumptions.valid,
            "warnings": result.assumptions.warnings,
            "notes": result.assumptions.notes
        },
        "interpretation": result.interpretation,
        "recommendations": result.recommendations,
        "post_hoc": result.post_hoc
    }


def recommend_test(table: List[List[float]], data_type: str = "categorical") -> dict:
    """Recommend appropriate statistical tests based on table characteristics."""
    arr = np.array(table, dtype=float)
    rows, cols = arr.shape

    recommendations = []

    if rows == 2 and cols == 2:
        recommendations.append({
            "test": "Fisher's Exact Test",
            "reason": "2×2 table - exact test is always valid",
            "priority": 1
        })
        recommendations.append({
            "test": "Pearson's Chi-Square",
            "reason": "Fast chi-square alternative",
            "priority": 2
        })
    else:
        recommendations.append({
            "test": "Pearson's Chi-Square",
            "reason": f"{rows}×{cols} table",
            "priority": 1
        })
        recommendations.append({
            "test": "G-Test",
            "reason": "More accurate for small samples",
            "priority": 2
        })

    if data_type == "ordinal":
        recommendations.append({
            "test": "Linear-by-Linear Association",
            "reason": "Data is ordinal",
            "priority": 1
        })
        recommendations.append({
            "test": "Goodman-Kruskal's Gamma",
            "reason": "Ordinal association measure",
            "priority": 2
        })

    assumptions = StatisticalEngine.check_expected_frequencies(table)
    if not assumptions.valid:
        if rows == 2 and cols == 2:
            recommendations[0]["note"] = "Expected frequencies low - Fisher's exact preferred"

    return {
        "table_dimensions": f"{rows}×{cols}",
        "data_type": data_type,
        "recommendations": recommendations,
        "assumptions_valid": assumptions.valid,
        "note": "Choose test based on data characteristics and assumptions"
    }


# ============================================================================
# MCP SERVER SETUP (FastMCP)
# ============================================================================

mcp = FastMCP("crosstabs-enhanced")


# --- Core Tests ---

@mcp.tool()
def chi_square_test(matrix: list[list[float]]) -> dict:
    """
    Perform Pearson's chi-square test of independence.

    Args:
        matrix: 2D contingency table as list of lists

    Returns:
        Test statistic, p-value, effect size (Cramér's V), and interpretation
    """
    result = StatisticalEngine.chi_square_test(matrix)
    return format_statistical_result(result)


@mcp.tool()
def fishers_exact(matrix: list[list[float]]) -> dict:
    """
    Fisher's exact test for 2×2 tables.

    Args:
        matrix: 2×2 contingency table

    Returns:
        Odds ratio, exact p-value, and 95% CI
    """
    result = StatisticalEngine.fishers_exact_test(matrix)
    return format_statistical_result(result)


@mcp.tool()
def mcnemar_test(matrix: list[list[float]]) -> dict:
    """
    McNemar's test for paired categorical data.

    Args:
        matrix: 2×2 table of paired outcomes

    Returns:
        Test statistic and both asymptotic and exact p-values
    """
    result = StatisticalEngine.mcnemar_test(matrix)
    return format_statistical_result(result)


@mcp.tool()
def g_test(matrix: list[list[float]]) -> dict:
    """
    G-test (likelihood ratio test) for contingency tables.
    More accurate than chi-square for small samples.

    Args:
        matrix: Contingency table

    Returns:
        G statistic, p-value, effect size
    """
    result = StatisticalEngine.g_test(matrix)
    return format_statistical_result(result)


# --- 2x2 Measures ---

@mcp.tool()
def odds_ratio(matrix: list[list[float]]) -> dict:
    """
    Calculate odds ratio with 95% confidence interval for 2x2 table.

    Args:
        matrix: 2×2 contingency table [[a,b],[c,d]]

    Returns:
        Odds ratio and confidence interval
    """
    arr = np.array(matrix, dtype=float)
    if arr.shape != (2, 2):
        raise ValueError("Odds ratio requires a 2×2 table")

    a, b, c, d = arr[0, 0], arr[0, 1], arr[1, 0], arr[1, 1]

    or_val = (a * d) / (b * c) if (b * c) > 0 else float('inf')
    ci = StatisticalEngine.odds_ratio_ci_exact(a, b, c, d)

    return {
        "odds_ratio": round(or_val, 4) if or_val != float('inf') else None,
        "ci_lower": round(ci[0], 4),
        "ci_upper": round(ci[1], 4),
        "interpretation": f"OR = {or_val:.2f}: odds in row 1 are {or_val:.2f}x those in row 2"
    }


@mcp.tool()
def relative_risk(matrix: list[list[float]]) -> dict:
    """
    Calculate relative risk with 95% confidence interval for 2x2 table.

    Args:
        matrix: 2×2 contingency table

    Returns:
        Relative risk, CI, and individual risks
    """
    return StatisticalEngine.relative_risk(matrix)


@mcp.tool()
def risk_difference(matrix: list[list[float]]) -> dict:
    """
    Calculate risk difference (absolute risk reduction) for 2x2 table.
    Also calculates NNT (Number Needed to Treat).

    Args:
        matrix: 2×2 contingency table

    Returns:
        Risk difference, CI, and NNT
    """
    return StatisticalEngine.risk_difference(matrix)


# --- Effect Sizes ---

@mcp.tool()
def cramers_v(matrix: list[list[float]]) -> dict:
    """
    Calculate Cramér's V effect size (standard and bias-corrected).

    Args:
        matrix: Contingency table

    Returns:
        Standard and bias-corrected Cramér's V with interpretation
    """
    return StatisticalEngine.cramers_v_corrected(matrix)


@mcp.tool()
def phi_coefficient(matrix: list[list[float]]) -> dict:
    """
    Calculate phi coefficient for 2×2 table.

    Args:
        matrix: 2×2 contingency table

    Returns:
        Phi coefficient and interpretation
    """
    arr = np.array(matrix, dtype=float)
    if arr.shape != (2, 2):
        raise ValueError("Phi coefficient requires a 2×2 table")

    chi2_stat, _, _, _ = stats.chi2_contingency(arr)
    n = arr.sum()
    phi = math.sqrt(chi2_stat / n)

    if phi < 0.1:
        interp = "negligible"
    elif phi < 0.3:
        interp = "small"
    elif phi < 0.5:
        interp = "medium"
    else:
        interp = "large"

    return {
        "phi": round(phi, 4),
        "interpretation": interp
    }


# --- Ordinal Measures ---

@mcp.tool()
def spearmans_rho(ranks_x: list[float], ranks_y: list[float]) -> dict:
    """
    Spearman's rank correlation coefficient.

    Args:
        ranks_x: First set of ranks
        ranks_y: Second set of ranks

    Returns:
        Rho coefficient and p-value
    """
    return OrdinalTests.spearmans_rho(ranks_x, ranks_y)


@mcp.tool()
def kendalls_tau(ranks_x: list[float], ranks_y: list[float]) -> dict:
    """
    Kendall's tau-b rank correlation.

    Args:
        ranks_x: First set of ranks
        ranks_y: Second set of ranks

    Returns:
        Tau coefficient and p-value
    """
    return OrdinalTests.kendalls_tau(ranks_x, ranks_y)


@mcp.tool()
def goodman_kruskal_gamma(matrix: list[list[float]]) -> dict:
    """
    Goodman-Kruskal's gamma for ordinal association.

    Args:
        matrix: Contingency table with ordinal rows and columns

    Returns:
        Gamma coefficient with CI
    """
    return OrdinalTests.goodman_kruskal_gamma(matrix)


@mcp.tool()
def cohens_kappa(matrix: list[list[float]]) -> dict:
    """
    Cohen's Kappa for inter-rater agreement (unweighted).

    Args:
        matrix: Square confusion matrix

    Returns:
        Kappa coefficient with CI and interpretation
    """
    return StatisticalEngine.cohens_kappa(matrix)


@mcp.tool()
def weighted_kappa(matrix: list[list[float]], weights: str = "quadratic") -> dict:
    """
    Weighted Cohen's Kappa for ordinal agreement.

    Args:
        matrix: Square confusion matrix
        weights: "linear" or "quadratic" (default)

    Returns:
        Weighted kappa with CI and interpretation
    """
    return StatisticalEngine.weighted_kappa(matrix, weights)


# --- Stratified Analysis ---

@mcp.tool()
def cmh_test(tables: list[list[list[float]]]) -> dict:
    """
    Cochran-Mantel-Haenszel test for stratified 2×2 tables.
    Tests association while controlling for a stratifying variable.

    Args:
        tables: List of 2×2 contingency tables (one per stratum)

    Returns:
        CMH chi-square, common odds ratio, and interpretation
    """
    return StatisticalEngine.cmh_test(tables)


# --- Trend Tests ---

@mcp.tool()
def linear_trend_test(matrix: list[list[float]],
                     row_scores: list[float] = None,
                     col_scores: list[float] = None) -> dict:
    """
    Linear-by-linear association test (Mantel-Haenszel trend test).

    Args:
        matrix: Contingency table
        row_scores: Optional numeric scores for rows (default: 0, 1, 2, ...)
        col_scores: Optional numeric scores for columns

    Returns:
        Z-statistic and p-value for linear trend
    """
    return TrendTests.linear_by_linear(matrix, row_scores, col_scores)


# --- Power Analysis ---

@mcp.tool()
def power_analysis(p1: float, p2: float,
                   n: float = None,
                   alpha: float = 0.05,
                   power: float = 0.80) -> dict:
    """
    Power or sample size calculation for comparing two proportions.

    Args:
        p1: Proportion in group 1
        p2: Proportion in group 2
        n: Sample size per group (if provided, calculates power)
        alpha: Significance level (default 0.05)
        power: Target power if calculating sample size (default 0.80)

    Returns:
        Either calculated power or required sample size
    """
    return PowerAnalysis.power_two_proportions(p1, p2, alpha, n, power)


# --- Multiple Comparisons ---

@mcp.tool()
def bonferroni_correction(p_values: list[float], alpha: float = 0.05) -> dict:
    """
    Bonferroni correction for multiple testing.

    Args:
        p_values: List of p-values to correct
        alpha: Family-wise error rate (default 0.05)

    Returns:
        Adjusted p-values and significance
    """
    return MultipleComparison.bonferroni(p_values, alpha)


@mcp.tool()
def fdr_correction(p_values: list[float], alpha: float = 0.05) -> dict:
    """
    Benjamini-Hochberg false discovery rate correction.

    Args:
        p_values: List of p-values to correct
        alpha: FDR level (default 0.05)

    Returns:
        Adjusted significance with FDR control
    """
    return MultipleComparison.benjamini_hochberg(p_values, alpha)


# --- Post-hoc Analysis ---

@mcp.tool()
def standardized_residuals(matrix: list[list[float]]) -> dict:
    """
    Calculate standardized residuals from contingency table.

    Values > |2| indicate cells that significantly deviate from expected.

    Args:
        matrix: Contingency table

    Returns:
        Residuals matrix with interpretation
    """
    residuals = StatisticalEngine.standardized_residuals(matrix)

    return {
        "standardized_residuals": [
            [round(x, 4) for x in row] for row in residuals
        ],
        "interpretation": "Values > |2| indicate significant deviation from expected",
        "threshold": 2.0
    }


@mcp.tool()
def post_hoc_chi_square(matrix: list[list[float]]) -> dict:
    """
    Full post-hoc analysis after chi-square test.

    Includes standardized residuals, adjusted residuals, and
    chi-square contributions by cell.

    Args:
        matrix: Contingency table

    Returns:
        Complete post-hoc analysis
    """
    chi_result = StatisticalEngine.chi_square_test(matrix)
    post_hoc = StatisticalEngine.post_hoc_analysis(matrix)

    result = format_statistical_result(chi_result)
    result["post_hoc"] = post_hoc
    return result


# --- Confidence Intervals ---

@mcp.tool()
def proportion_ci(successes: float, total: float, method: str = "wilson") -> dict:
    """
    Calculate confidence interval for a proportion.

    Args:
        successes: Number of successes
        total: Total sample size
        method: "wilson" (recommended), "agresti", or "normal"

    Returns:
        Proportion with 95% CI
    """
    p = successes / total if total > 0 else 0
    lower, upper = StatisticalEngine.proportion_ci(successes, total, method)

    return {
        "proportion": round(p, 4),
        "sample_size": int(total),
        "method": method,
        "ci_lower": round(lower, 4),
        "ci_upper": round(upper, 4),
        "interpretation": f"{int(successes)}/{int(total)} = {p:.1%} (95% CI: {lower:.1%} - {upper:.1%})"
    }


# --- Visualization Data ---

@mcp.tool()
def mosaic_plot_data(matrix: list[list[float]],
                    row_labels: list[str] = None,
                    col_labels: list[str] = None) -> dict:
    """
    Generate coordinates for mosaic plot visualization.

    Args:
        matrix: Contingency table
        row_labels: Optional labels for rows
        col_labels: Optional labels for columns

    Returns:
        Cell coordinates with residual-based coloring
    """
    return VisualizationData.mosaic_plot_data(matrix, row_labels, col_labels)


@mcp.tool()
def stacked_bar_data(matrix: list[list[float]],
                    by_rows: bool = True,
                    row_labels: list[str] = None,
                    col_labels: list[str] = None) -> dict:
    """
    Generate data for stacked bar chart.

    Args:
        matrix: Contingency table
        by_rows: If True, groups are rows; if False, groups are columns
        row_labels: Optional labels for rows
        col_labels: Optional labels for columns

    Returns:
        Stacked bar chart data with proportions
    """
    return VisualizationData.stacked_bar_data(matrix, by_rows, row_labels, col_labels)


# --- Utility Tools ---

@mcp.tool()
def check_assumptions(matrix: list[list[float]]) -> dict:
    """
    Check chi-square test assumptions.

    Verifies expected cell frequencies and provides recommendations.

    Args:
        matrix: Contingency table

    Returns:
        Assumption validity and recommendations
    """
    assumptions = StatisticalEngine.check_expected_frequencies(matrix)
    return {
        "valid": assumptions.valid,
        "warnings": assumptions.warnings,
        "notes": assumptions.notes,
        "recommendation": "Consider Fisher's exact or G-test if assumptions violated"
    }


@mcp.tool()
def recommend_test(matrix: list[list[float]], data_type: str = "categorical") -> dict:
    """
    Recommend appropriate statistical tests for your data.

    Args:
        matrix: Contingency table
        data_type: "categorical" or "ordinal"

    Returns:
        Ranked test recommendations with rationales
    """
    return recommend_test(matrix, data_type)


@mcp.tool()
def crosstab_from_data(data: list[dict], row_var: str, col_var: str) -> dict:
    """
    Create contingency table from raw data.

    Args:
        data: List of data objects with row and column variables
        row_var: Name of row variable
        col_var: Name of column variable

    Returns:
        Contingency table with labels
    """
    from collections import defaultdict

    # Get unique values
    row_vals = sorted(set(d.get(row_var) for d in data if d.get(row_var) is not None))
    col_vals = sorted(set(d.get(col_var) for d in data if d.get(col_var) is not None))

    # Count
    counts = defaultdict(lambda: defaultdict(int))
    for d in data:
        r = d.get(row_var)
        c = d.get(col_var)
        if r is not None and c is not None:
            counts[r][c] += 1

    # Build matrix
    matrix = []
    for r in row_vals:
        row = []
        for c in col_vals:
            row.append(counts[r][c])
        matrix.append(row)

    return {
        "matrix": matrix,
        "row_labels": [str(v) for v in row_vals],
        "col_labels": [str(v) for v in col_vals],
        "n": len(data)
    }


@mcp.tool()
def crosstab_from_csv(csv_text: str, row_var: str, col_var: str) -> dict:
    """
    Parse CSV and create contingency table from two columns.

    Args:
        csv_text: CSV content as string
        row_var: Name of row variable column
        col_var: Name of column variable column

    Returns:
        Contingency table with labels
    """
    import csv
    from io import StringIO
    from collections import defaultdict

    reader = csv.DictReader(StringIO(csv_text))
    data = list(reader)

    if not data:
        raise ValueError("Empty CSV data")

    if row_var not in data[0]:
        raise ValueError(f"Column '{row_var}' not found in CSV")
    if col_var not in data[0]:
        raise ValueError(f"Column '{col_var}' not found in CSV")

    # Get unique values
    row_vals = sorted(set(d[row_var] for d in data if d[row_var]))
    col_vals = sorted(set(d[col_var] for d in data if d[col_var]))

    # Count
    counts = defaultdict(lambda: defaultdict(int))
    for d in data:
        r = d[row_var]
        c = d[col_var]
        if r and c:
            counts[r][c] += 1

    # Build matrix
    matrix = []
    for r in row_vals:
        row = []
        for c in col_vals:
            row.append(counts[r][c])
        matrix.append(row)

    return {
        "matrix": matrix,
        "row_labels": row_vals,
        "col_labels": col_vals,
        "n": len(data)
    }


# ============================================================================
# ADDITIONAL STATISTICAL FUNCTIONS FOR PARITY
# ============================================================================

class AdditionalStats:
    """Additional statistical functions for full parity with web app."""

    @staticmethod
    def somers_d(table: List[List[float]]) -> dict:
        """Somers' D (asymmetric ordinal measure)."""
        arr = np.array(table, dtype=float)
        n = arr.sum()
        rows, cols = arr.shape

        # Count concordant and discordant pairs
        concordant = 0
        discordant = 0
        ties_row = 0
        ties_col = 0

        for i in range(rows):
            for j in range(cols):
                nij = arr[i, j]
                if nij == 0:
                    continue
                # Concordant: cells below and right
                for i2 in range(i + 1, rows):
                    for j2 in range(j + 1, cols):
                        concordant += nij * arr[i2, j2]
                # Discordant: cells below and left
                for i2 in range(i + 1, rows):
                    for j2 in range(0, j):
                        discordant += nij * arr[i2, j2]
                # Ties on row
                for j2 in range(j + 1, cols):
                    ties_row += nij * arr[i, j2]
                # Ties on column
                for i2 in range(i + 1, rows):
                    ties_col += nij * arr[i2, j]

        P, Q = concordant, discordant

        # d(Y|X): Y dependent
        denom_yx = P + Q + ties_col
        d_yx = (P - Q) / denom_yx if denom_yx > 0 else 0

        # d(X|Y): X dependent
        denom_xy = P + Q + ties_row
        d_xy = (P - Q) / denom_xy if denom_xy > 0 else 0

        # Symmetric
        symmetric = (d_yx + d_xy) / 2

        return {
            "d_yx": round(d_yx, 4),
            "d_xy": round(d_xy, 4),
            "symmetric": round(symmetric, 4),
            "concordant_pairs": int(concordant),
            "discordant_pairs": int(discordant),
            "interpretation": "Somers' D measures ordinal association (asymmetric)"
        }

    @staticmethod
    def tau_c(table: List[List[float]]) -> dict:
        """Stuart's tau-c for rectangular tables."""
        arr = np.array(table, dtype=float)
        n = arr.sum()
        rows, cols = arr.shape
        m = min(rows, cols)

        if n <= 1 or m <= 1:
            return {"tau_c": 0, "se": 0, "p_value": 1}

        # Count pairs
        concordant = 0
        discordant = 0
        for i in range(rows):
            for j in range(cols):
                nij = arr[i, j]
                if nij == 0:
                    continue
                for i2 in range(i + 1, rows):
                    for j2 in range(j + 1, cols):
                        concordant += nij * arr[i2, j2]
                for i2 in range(i + 1, rows):
                    for j2 in range(0, j):
                        discordant += nij * arr[i2, j2]

        P, Q = concordant, discordant
        tau_c_val = (2 * m * (P - Q)) / (n * n * (m - 1))

        # ASE
        se = (4 * m) / (n * n * (m - 1)) * math.sqrt(P + Q)
        z = tau_c_val / se if se > 0 else 0
        p = 2 * (1 - norm.cdf(abs(z)))

        return {
            "tau_c": round(tau_c_val, 4),
            "se": round(se, 4),
            "z": round(z, 4),
            "p_value": round(p, 4),
            "interpretation": "Stuart's tau-c for rectangular ordinal tables"
        }

    @staticmethod
    def goodman_kruskal_lambda(table: List[List[float]]) -> dict:
        """Goodman-Kruskal Lambda (PRE measure)."""
        arr = np.array(table, dtype=float)
        n = arr.sum()
        rows, cols = arr.shape
        row_totals = arr.sum(axis=1)
        col_totals = arr.sum(axis=0)

        # Lambda: column given row
        sum_row_max = sum(max(arr[i, :]) for i in range(rows))
        max_col_total = max(col_totals)
        lambda_col_row = (sum_row_max - max_col_total) / (n - max_col_total) if n > max_col_total else 0

        # Lambda: row given column
        sum_col_max = sum(max(arr[:, j]) for j in range(cols))
        max_row_total = max(row_totals)
        lambda_row_col = (sum_col_max - max_row_total) / (n - max_row_total) if n > max_row_total else 0

        # Symmetric
        symmetric = (sum_row_max + sum_col_max - max_col_total - max_row_total) / \
                   (2 * n - max_col_total - max_row_total) if (2 * n - max_col_total - max_row_total) > 0 else 0

        return {
            "lambda_col_given_row": round(lambda_col_row, 4),
            "lambda_row_given_col": round(lambda_row_col, 4),
            "symmetric": round(symmetric, 4),
            "interpretation": "PRE measure: proportional reduction in prediction error"
        }

    @staticmethod
    def uncertainty_coefficient(table: List[List[float]]) -> dict:
        """Uncertainty Coefficient (entropy-based measure)."""
        arr = np.array(table, dtype=float)
        n = arr.sum()
        rows, cols = arr.shape
        row_totals = arr.sum(axis=1)
        col_totals = arr.sum(axis=0)

        # Entropy calculations
        Hx = 0  # Row entropy
        for i in range(rows):
            if row_totals[i] > 0:
                p = row_totals[i] / n
                Hx -= p * math.log(p)

        Hy = 0  # Column entropy
        for j in range(cols):
            if col_totals[j] > 0:
                p = col_totals[j] / n
                Hy -= p * math.log(p)

        Hxy = 0  # Joint entropy
        for i in range(rows):
            for j in range(cols):
                if arr[i, j] > 0:
                    p = arr[i, j] / n
                    Hxy -= p * math.log(p)

        Ixy = Hx + Hy - Hxy  # Mutual information

        return {
            "u_col_given_row": round(Ixy / Hx, 4) if Hx > 0 else 0,
            "u_row_given_col": round(Ixy / Hy, 4) if Hy > 0 else 0,
            "symmetric": round(2 * Ixy / (Hx + Hy), 4) if (Hx + Hy) > 0 else 0,
            "mutual_information": round(Ixy, 4),
            "interpretation": "Entropy-based measure of association"
        }

    @staticmethod
    def breslow_day_test(tables: List[List[List[float]]]) -> dict:
        """Breslow-Day test for homogeneity of odds ratios."""
        if len(tables) < 2:
            raise ValueError("Need at least 2 strata for Breslow-Day test")

        for i, table in enumerate(tables):
            if len(table) != 2 or len(table[0]) != 2:
                raise ValueError(f"Stratum {i}: Breslow-Day requires 2x2 tables")

        # Calculate common OR using Mantel-Haenszel
        num = 0
        denom = 0
        for table in tables:
            a, b = table[0][0], table[0][1]
            c, d = table[1][0], table[1][1]
            n = a + b + c + d
            if n == 0:
                continue
            num += (a * d) / n
            denom += (b * c) / n

        if denom == 0:
            return {"error": "Cannot compute common OR"}

        common_or = num / denom

        # Calculate Breslow-Day statistic
        chi2_bd = 0
        for table in tables:
            a, b = table[0][0], table[0][1]
            c, d = table[1][0], table[1][1]
            n1 = a + b
            n0 = c + d
            m1 = a + c
            n = n1 + n0

            if n == 0:
                continue

            # Solve quadratic for expected a under common OR
            A = common_or - 1
            B = -(common_or * (n1 + m1) + n0 - m1)
            C = common_or * n1 * m1

            if abs(A) < 1e-10:
                a_exp = -C / B if B != 0 else 0
            else:
                disc = B * B - 4 * A * C
                if disc < 0:
                    continue
                a_exp = (-B - math.sqrt(disc)) / (2 * A)

            if a_exp < 0 or a_exp > min(n1, m1):
                continue

            # Variance
            b_exp = n1 - a_exp
            c_exp = m1 - a_exp
            d_exp = n0 - c_exp

            if a_exp > 0 and b_exp > 0 and c_exp > 0 and d_exp > 0:
                v = 1 / (1/a_exp + 1/b_exp + 1/c_exp + 1/d_exp)
                chi2_bd += (a - a_exp) ** 2 / v

        df = len(tables) - 1
        p = 1 - chi2.cdf(chi2_bd, df)

        return {
            "chi2": round(chi2_bd, 4),
            "df": df,
            "p_value": round(p, 4),
            "common_or": round(common_or, 4),
            "homogeneous": p > 0.05,
            "interpretation": "Tests if odds ratios are homogeneous across strata"
        }

    @staticmethod
    def monte_carlo_chi_square(table: List[List[float]], n_sim: int = 10000, seed: int = None) -> dict:
        """Monte Carlo simulation for chi-square p-value."""
        if seed is not None:
            np.random.seed(seed)

        arr = np.array(table, dtype=float)
        n = arr.sum()
        row_totals = arr.sum(axis=1)
        col_totals = arr.sum(axis=0)
        expected = np.outer(row_totals, col_totals) / n

        # Observed chi-square
        obs_chi2 = np.sum((arr - expected) ** 2 / expected)

        # Simulate
        extreme_count = 0
        for _ in range(n_sim):
            sim_table = AdditionalStats._generate_random_table(row_totals, col_totals)
            sim_chi2 = np.sum((sim_table - expected) ** 2 / expected)
            if sim_chi2 >= obs_chi2:
                extreme_count += 1

        return {
            "p_value": round(extreme_count / n_sim, 4),
            "chi2_observed": round(float(obs_chi2), 4),
            "simulations": n_sim,
            "seed": seed,
            "method": "Monte Carlo",
            "interpretation": "Exact p-value via simulation"
        }

    @staticmethod
    def _generate_random_table(row_totals: np.ndarray, col_totals: np.ndarray) -> np.ndarray:
        """Generate random table with fixed margins."""
        rows = len(row_totals)
        cols = len(col_totals)
        matrix = np.zeros((rows, cols))

        row_rem = row_totals.copy().astype(float)
        col_rem = col_totals.copy().astype(float)

        for i in range(rows - 1):
            for j in range(cols - 1):
                remaining = col_rem.sum()
                if remaining == 0:
                    break
                p = col_rem[j] / remaining
                max_val = min(row_rem[i], col_rem[j])
                mean = row_rem[i] * p
                value = max(0, min(max_val, round(mean + (np.random.random() - 0.5) * math.sqrt(mean + 1))))
                matrix[i, j] = value
                row_rem[i] -= value
                col_rem[j] -= value
            matrix[i, cols - 1] = row_rem[i]
            col_rem[cols - 1] -= row_rem[i]

        for j in range(cols):
            matrix[rows - 1, j] = col_rem[j]

        return matrix

    @staticmethod
    def correspondence_analysis(table: List[List[float]],
                                row_labels: List[str] = None,
                                col_labels: List[str] = None) -> dict:
        """Simple correspondence analysis for biplot."""
        arr = np.array(table, dtype=float)
        rows, cols = arr.shape
        n = arr.sum()

        if rows < 2 or cols < 2:
            return {"error": "Need at least 2x2 table"}

        row_totals = arr.sum(axis=1)
        col_totals = arr.sum(axis=0)

        if row_labels is None:
            row_labels = [f"Row_{i}" for i in range(rows)]
        if col_labels is None:
            col_labels = [f"Col_{j}" for j in range(cols)]

        # Correspondence matrix (standardized residuals)
        expected = np.outer(row_totals, col_totals) / n
        Z = (arr - expected) / np.sqrt(expected + 1e-10)

        # SVD
        try:
            U, s, Vt = np.linalg.svd(Z, full_matrices=False)
            eigenvalues = s ** 2

            # First two dimensions
            row_coords = U[:, :2] * s[:2]
            col_coords = Vt[:2, :].T * s[:2]

            total_inertia = sum(eigenvalues)
            dim1_pct = eigenvalues[0] / total_inertia * 100 if total_inertia > 0 else 0
            dim2_pct = eigenvalues[1] / total_inertia * 100 if len(eigenvalues) > 1 and total_inertia > 0 else 0

            return {
                "row_coords": [
                    {"label": row_labels[i], "x": round(float(row_coords[i, 0]), 4), "y": round(float(row_coords[i, 1] if row_coords.shape[1] > 1 else 0), 4)}
                    for i in range(rows)
                ],
                "col_coords": [
                    {"label": col_labels[j], "x": round(float(col_coords[j, 0]), 4), "y": round(float(col_coords[j, 1] if col_coords.shape[1] > 1 else 0), 4)}
                    for j in range(cols)
                ],
                "total_inertia": round(total_inertia, 4),
                "dim1_percent": round(dim1_pct, 2),
                "dim2_percent": round(dim2_pct, 2),
                "explained_variance": round(dim1_pct + dim2_pct, 2),
                "interpretation": "2D biplot showing row and column associations"
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def chi_square_yates(table: List[List[float]]) -> dict:
        """Chi-square with Yates continuity correction for 2x2 tables."""
        arr = np.array(table, dtype=float)
        if arr.shape != (2, 2):
            raise ValueError("Yates correction requires a 2×2 table")

        a, b = arr[0, 0], arr[0, 1]
        c, d = arr[1, 0], arr[1, 1]
        n = a + b + c + d
        r1, r2 = a + b, c + d
        c1, c2 = a + c, b + d

        if r1 == 0 or r2 == 0 or c1 == 0 or c2 == 0:
            return {"error": "Zero marginal total"}

        # Yates correction
        chi2_yates = (max(0, abs(a * d - b * c) - n / 2) ** 2 * n) / (r1 * r2 * c1 * c2)
        p = 1 - chi2.cdf(chi2_yates, 1)

        # Uncorrected for comparison
        chi2_uncorrected = ((a * d - b * c) ** 2 * n) / (r1 * r2 * c1 * c2)

        return {
            "chi2_yates": round(chi2_yates, 4),
            "chi2_uncorrected": round(chi2_uncorrected, 4),
            "p_value": round(p, 4),
            "df": 1,
            "interpretation": "Yates correction reduces chi-square, more conservative"
        }

    @staticmethod
    def attributable_risk(table: List[List[float]]) -> dict:
        """Attributable risk measures for 2x2 tables."""
        arr = np.array(table, dtype=float)
        if arr.shape != (2, 2):
            raise ValueError("Attributable risk requires a 2×2 table")

        a, b = arr[0, 0], arr[0, 1]
        c, d = arr[1, 0], arr[1, 1]
        n1 = a + b  # Exposed
        n0 = c + d  # Unexposed
        total = n1 + n0

        if n1 == 0 or n0 == 0:
            return {"error": "Zero group total"}

        p1 = a / n1  # Risk in exposed
        p0 = c / n0  # Risk in unexposed
        p_total = (a + c) / total

        # Attributable Risk (absolute)
        arr_val = p1 - p0

        # Relative Risk Reduction
        rrr = (p1 - p0) / p1 if p1 > 0 else 0

        # Population Attributable Risk
        par = p_total - p0

        # Population Attributable Fraction
        paf = (p_total - p0) / p_total if p_total > 0 else 0

        # Attributable Fraction (Exposed)
        af = (p1 - p0) / p1 if p1 > 0 else 0

        return {
            "attributable_risk": round(arr_val, 4),
            "relative_risk_reduction": round(rrr, 4),
            "population_attributable_risk": round(par, 4),
            "population_attributable_fraction": round(paf, 4),
            "attributable_fraction_exposed": round(af, 4),
            "risk_exposed": round(p1, 4),
            "risk_unexposed": round(p0, 4),
            "interpretation": "Measures of effect attributable to exposure"
        }

    @staticmethod
    def detect_outliers(values: List[float], method: str = "zscore", threshold: float = 2.0) -> dict:
        """Detect outliers in numeric data."""
        arr = np.array(values)
        n = len(arr)

        if n < 3:
            return {"error": "Need at least 3 values"}

        mean_val = np.mean(arr)
        std_val = np.std(arr, ddof=1)

        if method == "zscore":
            z_scores = (arr - mean_val) / std_val if std_val > 0 else np.zeros(n)
            outliers = []
            for i, (val, z) in enumerate(zip(arr, z_scores)):
                abs_z = abs(z)
                if abs_z >= 3:
                    severity = "extreme"
                elif abs_z >= 2.5:
                    severity = "moderate"
                elif abs_z >= threshold:
                    severity = "mild"
                else:
                    continue
                outliers.append({
                    "index": i,
                    "value": round(float(val), 4),
                    "z_score": round(float(z), 4),
                    "severity": severity
                })

            return {
                "method": "z-score",
                "threshold": threshold,
                "mean": round(float(mean_val), 4),
                "std_dev": round(float(std_val), 4),
                "outlier_count": len(outliers),
                "outliers": outliers
            }

        elif method == "iqr":
            sorted_arr = np.sort(arr)
            q1 = np.percentile(sorted_arr, 25)
            q3 = np.percentile(sorted_arr, 75)
            iqr = q3 - q1
            lower_fence = q1 - 1.5 * iqr
            upper_fence = q3 + 1.5 * iqr

            outliers = [round(float(v), 4) for v in arr if v < lower_fence or v > upper_fence]

            return {
                "method": "IQR",
                "q1": round(float(q1), 4),
                "q3": round(float(q3), 4),
                "iqr": round(float(iqr), 4),
                "lower_fence": round(float(lower_fence), 4),
                "upper_fence": round(float(upper_fence), 4),
                "outlier_count": len(outliers),
                "outliers": outliers
            }


# --- New MCP Tools for Parity ---

@mcp.tool()
def somers_d(matrix: list[list[float]]) -> dict:
    """
    Somers' D (asymmetric ordinal measure).

    Args:
        matrix: Contingency table with ordinal rows and columns

    Returns:
        d(Y|X), d(X|Y), and symmetric versions
    """
    return AdditionalStats.somers_d(matrix)


@mcp.tool()
def tau_c(matrix: list[list[float]]) -> dict:
    """
    Stuart's tau-c for rectangular ordinal tables.

    Args:
        matrix: Contingency table

    Returns:
        Tau-c coefficient with standard error and p-value
    """
    return AdditionalStats.tau_c(matrix)


@mcp.tool()
def lambda_coefficient(matrix: list[list[float]]) -> dict:
    """
    Goodman-Kruskal Lambda (proportional reduction in error).

    Args:
        matrix: Contingency table

    Returns:
        Lambda values (asymmetric and symmetric)
    """
    return AdditionalStats.goodman_kruskal_lambda(matrix)


@mcp.tool()
def uncertainty_coefficient(matrix: list[list[float]]) -> dict:
    """
    Uncertainty Coefficient (entropy-based association measure).

    Args:
        matrix: Contingency table

    Returns:
        Uncertainty coefficients and mutual information
    """
    return AdditionalStats.uncertainty_coefficient(matrix)


@mcp.tool()
def breslow_day_test(tables: list[list[list[float]]]) -> dict:
    """
    Breslow-Day test for homogeneity of odds ratios across strata.

    Args:
        tables: List of 2×2 contingency tables (one per stratum)

    Returns:
        Test statistic, p-value, and whether ORs are homogeneous
    """
    return AdditionalStats.breslow_day_test(tables)


@mcp.tool()
def monte_carlo_chi_square(matrix: list[list[float]],
                           n_sim: int = 10000,
                           seed: int = None) -> dict:
    """
    Monte Carlo simulation for exact chi-square p-value.

    Args:
        matrix: Contingency table
        n_sim: Number of simulations (default 10000)
        seed: Random seed for reproducibility

    Returns:
        Simulated p-value
    """
    return AdditionalStats.monte_carlo_chi_square(matrix, n_sim, seed)


@mcp.tool()
def correspondence_analysis(matrix: list[list[float]],
                           row_labels: list[str] = None,
                           col_labels: list[str] = None) -> dict:
    """
    Correspondence analysis for visualizing associations.

    Args:
        matrix: Contingency table
        row_labels: Optional row labels
        col_labels: Optional column labels

    Returns:
        2D coordinates for biplot and explained variance
    """
    return AdditionalStats.correspondence_analysis(matrix, row_labels, col_labels)


@mcp.tool()
def chi_square_yates(matrix: list[list[float]]) -> dict:
    """
    Chi-square with Yates continuity correction for 2×2 tables.

    Args:
        matrix: 2×2 contingency table

    Returns:
        Yates-corrected chi-square and p-value
    """
    return AdditionalStats.chi_square_yates(matrix)


@mcp.tool()
def attributable_risk(matrix: list[list[float]]) -> dict:
    """
    Attributable risk measures for epidemiological studies.

    Args:
        matrix: 2×2 contingency table (exposed/unexposed × outcome)

    Returns:
        AR, RRR, PAR, PAF, and other risk measures
    """
    return AdditionalStats.attributable_risk(matrix)


@mcp.tool()
def detect_outliers(values: list[float],
                    method: str = "zscore",
                    threshold: float = 2.0) -> dict:
    """
    Detect outliers in numeric data.

    Args:
        values: List of numeric values
        method: "zscore" or "iqr"
        threshold: Z-score threshold (default 2.0)

    Returns:
        Outlier statistics and identified outliers
    """
    return AdditionalStats.detect_outliers(values, method, threshold)


@mcp.tool()
def effect_size(matrix: list[list[float]]) -> dict:
    """
    Calculate multiple effect sizes for contingency table.

    Args:
        matrix: Contingency table

    Returns:
        Cramér's V (corrected), phi, and contingency coefficient
    """
    arr = np.array(matrix, dtype=float)
    chi2_stat, _, _, _ = stats.chi2_contingency(arr)
    n = arr.sum()
    rows, cols = arr.shape
    min_dim = min(rows - 1, cols - 1)

    # Cramér's V
    cramers_v_std = math.sqrt(chi2_stat / (n * min_dim)) if min_dim > 0 else 0

    # Bias-corrected Cramér's V
    phi2 = chi2_stat / n
    phi2_corr = max(0, phi2 - ((rows - 1) * (cols - 1)) / (n - 1)) if n > 1 else 0
    rows_corr = rows - ((rows - 1) ** 2) / (n - 1) if n > 1 else rows
    cols_corr = cols - ((cols - 1) ** 2) / (n - 1) if n > 1 else cols
    min_dim_corr = min(rows_corr, cols_corr) - 1
    cramers_v_corr = math.sqrt(phi2_corr / min_dim_corr) if min_dim_corr > 0 else 0

    # Phi (for 2x2)
    phi = math.sqrt(chi2_stat / n) if n > 0 else 0

    # Contingency coefficient
    c = math.sqrt(chi2_stat / (chi2_stat + n)) if (chi2_stat + n) > 0 else 0

    return {
        "cramers_v": round(cramers_v_std, 4),
        "cramers_v_corrected": round(cramers_v_corr, 4),
        "phi": round(phi, 4),
        "contingency_coefficient": round(c, 4),
        "chi_square": round(chi2_stat, 4),
        "n": int(n)
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
