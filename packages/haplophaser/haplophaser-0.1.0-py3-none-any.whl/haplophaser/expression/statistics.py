"""
Statistical tests for expression bias analysis.

Provides specialized statistical tests for homeolog expression analysis,
including differential expression, ratio testing, and variance analysis.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class StatisticalTestResult:
    """Result of a statistical test.

    Parameters
    ----------
    test_name : str
        Name of the test.
    statistic : float
        Test statistic.
    pvalue : float
        P-value.
    effect_size : float
        Effect size measure.
    confidence_interval : tuple[float, float], optional
        Confidence interval.
    additional_info : dict
        Additional test-specific information.
    """

    test_name: str
    statistic: float
    pvalue: float
    effect_size: float
    confidence_interval: tuple[float, float] | None = None
    additional_info: dict[str, Any] | None = None

    @property
    def is_significant(self) -> bool:
        """Return True if p < 0.05."""
        return self.pvalue < 0.05

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_name": self.test_name,
            "statistic": self.statistic,
            "pvalue": self.pvalue,
            "effect_size": self.effect_size,
            "confidence_interval": self.confidence_interval,
            "is_significant": self.is_significant,
            "additional_info": self.additional_info,
        }


def paired_ratio_test(
    expr1: np.ndarray,
    expr2: np.ndarray,
    pseudocount: float = 0.01,
    method: str = "paired_t",
) -> StatisticalTestResult:
    """Test if expression ratio differs from 1:1.

    Parameters
    ----------
    expr1 : np.ndarray
        Expression values for gene 1.
    expr2 : np.ndarray
        Expression values for gene 2.
    pseudocount : float
        Pseudocount for ratio calculation.
    method : str
        Test method: 'paired_t', 'wilcoxon', 'permutation'.

    Returns
    -------
    StatisticalTestResult
        Test results.
    """
    # Calculate log ratios
    log_ratios = np.log2((expr1 + pseudocount) / (expr2 + pseudocount))

    mean_ratio = np.mean(log_ratios)
    std_ratio = np.std(log_ratios, ddof=1)

    if method == "paired_t":
        # One-sample t-test against 0
        statistic, pvalue = stats.ttest_1samp(log_ratios, 0)

        # Calculate confidence interval
        n = len(log_ratios)
        se = std_ratio / np.sqrt(n)
        ci = stats.t.interval(0.95, n - 1, loc=mean_ratio, scale=se)

    elif method == "wilcoxon":
        # Wilcoxon signed-rank test
        try:
            statistic, pvalue = stats.wilcoxon(log_ratios)
            ci = None
        except ValueError:
            statistic, pvalue = 0.0, 1.0
            ci = None

    elif method == "permutation":
        statistic, pvalue = _permutation_test(log_ratios)
        ci = None

    else:
        raise ValueError(f"Unknown method: {method}")

    # Effect size (Cohen's d for log ratios)
    effect_size = mean_ratio / std_ratio if std_ratio > 0 else 0.0

    return StatisticalTestResult(
        test_name=f"paired_ratio_{method}",
        statistic=float(statistic),
        pvalue=float(pvalue) if not np.isnan(pvalue) else 1.0,
        effect_size=float(effect_size),
        confidence_interval=ci,
        additional_info={
            "mean_log2_ratio": float(mean_ratio),
            "std_log2_ratio": float(std_ratio),
            "n_samples": len(log_ratios),
        },
    )


def differential_ratio_test(
    expr1_cond1: np.ndarray,
    expr2_cond1: np.ndarray,
    expr1_cond2: np.ndarray,
    expr2_cond2: np.ndarray,
    pseudocount: float = 0.01,
    method: str = "t_test",
) -> StatisticalTestResult:
    """Test if expression ratio differs between conditions.

    Parameters
    ----------
    expr1_cond1 : np.ndarray
        Gene 1 expression in condition 1.
    expr2_cond1 : np.ndarray
        Gene 2 expression in condition 1.
    expr1_cond2 : np.ndarray
        Gene 1 expression in condition 2.
    expr2_cond2 : np.ndarray
        Gene 2 expression in condition 2.
    pseudocount : float
        Pseudocount for ratio calculation.
    method : str
        Test method: 't_test', 'mann_whitney'.

    Returns
    -------
    StatisticalTestResult
        Test results.
    """
    # Calculate log ratios for each condition
    ratios1 = np.log2((expr1_cond1 + pseudocount) / (expr2_cond1 + pseudocount))
    ratios2 = np.log2((expr1_cond2 + pseudocount) / (expr2_cond2 + pseudocount))

    mean1 = np.mean(ratios1)
    mean2 = np.mean(ratios2)
    ratio_diff = mean2 - mean1

    if method == "t_test":
        statistic, pvalue = stats.ttest_ind(ratios1, ratios2)
    elif method == "mann_whitney":
        statistic, pvalue = stats.mannwhitneyu(ratios1, ratios2, alternative='two-sided')
    else:
        raise ValueError(f"Unknown method: {method}")

    # Effect size (Cohen's d)
    pooled_std = np.sqrt(
        (np.var(ratios1, ddof=1) * (len(ratios1) - 1) +
         np.var(ratios2, ddof=1) * (len(ratios2) - 1)) /
        (len(ratios1) + len(ratios2) - 2)
    )
    effect_size = ratio_diff / pooled_std if pooled_std > 0 else 0.0

    return StatisticalTestResult(
        test_name=f"differential_ratio_{method}",
        statistic=float(statistic),
        pvalue=float(pvalue) if not np.isnan(pvalue) else 1.0,
        effect_size=float(effect_size),
        additional_info={
            "mean_ratio_cond1": float(mean1),
            "mean_ratio_cond2": float(mean2),
            "ratio_difference": float(ratio_diff),
        },
    )


def variance_ratio_test(
    expr1: np.ndarray,
    expr2: np.ndarray,
) -> StatisticalTestResult:
    """Test if expression variance differs between homeologs.

    Parameters
    ----------
    expr1 : np.ndarray
        Expression values for gene 1.
    expr2 : np.ndarray
        Expression values for gene 2.

    Returns
    -------
    StatisticalTestResult
        Test results (Levene's test).
    """
    statistic, pvalue = stats.levene(expr1, expr2)

    var1 = np.var(expr1, ddof=1)
    var2 = np.var(expr2, ddof=1)
    variance_ratio = var1 / var2 if var2 > 0 else float('inf')

    return StatisticalTestResult(
        test_name="variance_ratio_levene",
        statistic=float(statistic),
        pvalue=float(pvalue),
        effect_size=float(variance_ratio),
        additional_info={
            "variance_gene1": float(var1),
            "variance_gene2": float(var2),
            "cv_gene1": float(np.std(expr1, ddof=1) / np.mean(expr1)) if np.mean(expr1) > 0 else 0,
            "cv_gene2": float(np.std(expr2, ddof=1) / np.mean(expr2)) if np.mean(expr2) > 0 else 0,
        },
    )


def correlation_test(
    expr1: np.ndarray,
    expr2: np.ndarray,
    method: str = "pearson",
) -> StatisticalTestResult:
    """Test correlation between homeolog expression.

    Parameters
    ----------
    expr1 : np.ndarray
        Expression values for gene 1.
    expr2 : np.ndarray
        Expression values for gene 2.
    method : str
        Correlation method: 'pearson', 'spearman'.

    Returns
    -------
    StatisticalTestResult
        Test results.
    """
    if method == "pearson":
        statistic, pvalue = stats.pearsonr(expr1, expr2)
    elif method == "spearman":
        statistic, pvalue = stats.spearmanr(expr1, expr2)
    else:
        raise ValueError(f"Unknown method: {method}")

    return StatisticalTestResult(
        test_name=f"correlation_{method}",
        statistic=float(statistic),
        pvalue=float(pvalue) if not np.isnan(pvalue) else 1.0,
        effect_size=float(statistic),  # Correlation is its own effect size
        additional_info={
            "correlation": float(statistic),
        },
    )


def dominance_proportion_test(
    sg1_count: int,
    sg2_count: int,
    method: str = "binomial",
) -> StatisticalTestResult:
    """Test if dominance proportions differ from 50:50.

    Parameters
    ----------
    sg1_count : int
        Number of pairs dominant for subgenome 1.
    sg2_count : int
        Number of pairs dominant for subgenome 2.
    method : str
        Test method: 'binomial', 'chi2'.

    Returns
    -------
    StatisticalTestResult
        Test results.
    """
    total = sg1_count + sg2_count

    if total == 0:
        return StatisticalTestResult(
            test_name=f"dominance_proportion_{method}",
            statistic=0.0,
            pvalue=1.0,
            effect_size=0.0,
        )

    proportion = sg1_count / total

    if method == "binomial":
        result = stats.binomtest(sg1_count, total, 0.5)
        statistic = sg1_count
        pvalue = result.pvalue
        ci = result.proportion_ci()
        confidence_interval = (ci.low, ci.high)

    elif method == "chi2":
        expected = total / 2
        chi2 = ((sg1_count - expected) ** 2 + (sg2_count - expected) ** 2) / expected
        statistic = chi2
        pvalue = stats.chi2.sf(chi2, df=1)
        confidence_interval = None

    else:
        raise ValueError(f"Unknown method: {method}")

    effect_size = proportion - 0.5

    return StatisticalTestResult(
        test_name=f"dominance_proportion_{method}",
        statistic=float(statistic),
        pvalue=float(pvalue),
        effect_size=float(effect_size),
        confidence_interval=confidence_interval,
        additional_info={
            "sg1_count": sg1_count,
            "sg2_count": sg2_count,
            "total": total,
            "proportion_sg1": proportion,
        },
    )


def _permutation_test(
    values: np.ndarray,
    n_permutations: int = 10000,
) -> tuple[float, float]:
    """Permutation test for mean difference from zero.

    Parameters
    ----------
    values : np.ndarray
        Observed values.
    n_permutations : int
        Number of permutations.

    Returns
    -------
    tuple[float, float]
        (statistic, p-value)
    """
    observed_mean = np.mean(values)

    count_extreme = 0
    for _ in range(n_permutations):
        # Randomly flip signs
        signs = np.random.choice([-1, 1], len(values))
        perm_mean = np.mean(signs * values)
        if abs(perm_mean) >= abs(observed_mean):
            count_extreme += 1

    pvalue = count_extreme / n_permutations

    return observed_mean, pvalue


def fdr_correction(
    pvalues: np.ndarray,
    method: str = "bh",
) -> np.ndarray:
    """Apply FDR correction to p-values.

    Parameters
    ----------
    pvalues : np.ndarray
        Raw p-values.
    method : str
        Correction method: 'bh' (Benjamini-Hochberg), 'by' (Benjamini-Yekutieli).

    Returns
    -------
    np.ndarray
        Corrected p-values (q-values).
    """
    n = len(pvalues)
    if n == 0:
        return np.array([])

    sorted_indices = np.argsort(pvalues)
    sorted_pvals = pvalues[sorted_indices]

    if method == "bh":
        # Benjamini-Hochberg
        correction = n / (np.arange(n) + 1)
    elif method == "by":
        # Benjamini-Yekutieli
        c = np.sum(1 / np.arange(1, n + 1))
        correction = n * c / (np.arange(n) + 1)
    else:
        raise ValueError(f"Unknown method: {method}")

    fdr = np.zeros(n)
    fdr[sorted_indices] = sorted_pvals * correction

    # Enforce monotonicity
    fdr_sorted = fdr[sorted_indices]
    for i in range(n - 2, -1, -1):
        fdr_sorted[i] = min(fdr_sorted[i], fdr_sorted[i + 1])
    fdr[sorted_indices] = fdr_sorted

    return np.minimum(fdr, 1.0)


def bonferroni_correction(pvalues: np.ndarray) -> np.ndarray:
    """Apply Bonferroni correction to p-values.

    Parameters
    ----------
    pvalues : np.ndarray
        Raw p-values.

    Returns
    -------
    np.ndarray
        Corrected p-values.
    """
    n = len(pvalues)
    return np.minimum(pvalues * n, 1.0)
