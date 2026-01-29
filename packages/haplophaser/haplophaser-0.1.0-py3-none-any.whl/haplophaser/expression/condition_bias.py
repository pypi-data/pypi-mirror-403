"""
Condition-specific expression bias analysis.

Analyzes how expression bias changes across experimental conditions,
identifying homeolog pairs with condition-dependent bias patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from haplophaser.expression.bias import ExpressionBiasCalculator
from haplophaser.expression.homeolog_expression import HomeologExpressionExtractor
from haplophaser.expression.models import (
    BiasCategory,
    ExpressionBiasResult,
    ExpressionMatrix,
    HomeologExpression,
    HomeologExpressionResult,
)

logger = logging.getLogger(__name__)


@dataclass
class ConditionComparisonParams:
    """Parameters for condition comparison.

    Parameters
    ----------
    log2_diff_threshold : float
        Minimum |log2 ratio difference| for differential bias.
    fdr_threshold : float
        FDR threshold for significance.
    min_samples : int
        Minimum samples per condition.
    """

    log2_diff_threshold: float = 1.0
    fdr_threshold: float = 0.05
    min_samples: int = 2


@dataclass
class DifferentialBias:
    """Differential expression bias between conditions.

    Parameters
    ----------
    pair_id : str
        Homeolog pair identifier.
    gene1_id : str
        First gene identifier.
    gene2_id : str
        Second gene identifier.
    condition1 : str
        First condition.
    condition2 : str
        Second condition.
    log2_ratio_cond1 : float
        Log2 ratio in condition 1.
    log2_ratio_cond2 : float
        Log2 ratio in condition 2.
    log2_ratio_diff : float
        Difference in log2 ratios.
    category_cond1 : BiasCategory
        Bias category in condition 1.
    category_cond2 : BiasCategory
        Bias category in condition 2.
    pvalue : float
        P-value for differential bias.
    fdr : float
        FDR-corrected p-value.
    """

    pair_id: str
    gene1_id: str
    gene2_id: str
    condition1: str
    condition2: str
    log2_ratio_cond1: float
    log2_ratio_cond2: float
    log2_ratio_diff: float
    category_cond1: BiasCategory
    category_cond2: BiasCategory
    pvalue: float
    fdr: float

    @property
    def is_differential(self) -> bool:
        """Return True if bias is differentially expressed."""
        return self.fdr < 0.05

    @property
    def category_changed(self) -> bool:
        """Return True if bias category changed between conditions."""
        return self.category_cond1 != self.category_cond2

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pair_id": self.pair_id,
            "gene1_id": self.gene1_id,
            "gene2_id": self.gene2_id,
            "condition1": self.condition1,
            "condition2": self.condition2,
            "log2_ratio_cond1": self.log2_ratio_cond1,
            "log2_ratio_cond2": self.log2_ratio_cond2,
            "log2_ratio_diff": self.log2_ratio_diff,
            "category_cond1": self.category_cond1.value,
            "category_cond2": self.category_cond2.value,
            "pvalue": self.pvalue,
            "fdr": self.fdr,
            "is_differential": self.is_differential,
            "category_changed": self.category_changed,
        }


@dataclass
class ConditionComparisonResult:
    """Results of condition comparison analysis.

    Parameters
    ----------
    condition1 : str
        First condition.
    condition2 : str
        Second condition.
    differential_biases : list[DifferentialBias]
        Differential bias results.
    condition1_result : ExpressionBiasResult
        Bias results for condition 1.
    condition2_result : ExpressionBiasResult
        Bias results for condition 2.
    """

    condition1: str
    condition2: str
    differential_biases: list[DifferentialBias]
    condition1_result: ExpressionBiasResult
    condition2_result: ExpressionBiasResult

    @property
    def n_differential(self) -> int:
        """Return number of differentially biased pairs."""
        return sum(1 for d in self.differential_biases if d.is_differential)

    @property
    def n_category_changed(self) -> int:
        """Return number of pairs with category change."""
        return sum(1 for d in self.differential_biases if d.category_changed)

    def summary(self) -> dict[str, Any]:
        """Generate summary statistics.

        Returns
        -------
        dict
            Summary statistics.
        """
        return {
            "condition1": self.condition1,
            "condition2": self.condition2,
            "n_pairs": len(self.differential_biases),
            "n_differential": self.n_differential,
            "n_category_changed": self.n_category_changed,
            "condition1_n_significant": self.condition1_result.n_significant,
            "condition2_n_significant": self.condition2_result.n_significant,
        }

    def to_dataframe(self):
        """Convert to pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            Differential bias results.
        """
        import pandas as pd

        if not self.differential_biases:
            return pd.DataFrame()

        rows = [d.to_dict() for d in self.differential_biases]
        return pd.DataFrame(rows)


class ConditionBiasAnalyzer:
    """Analyze expression bias across conditions.

    Compares homeolog expression bias between experimental conditions
    to identify condition-dependent bias patterns.

    Parameters
    ----------
    min_expr : float
        Minimum expression threshold.
    log2_threshold : float
        Log2 ratio threshold for bias.
    log2_diff_threshold : float
        Log2 difference threshold for differential bias.
    test_method : str
        Statistical test method.

    Examples
    --------
    >>> analyzer = ConditionBiasAnalyzer()
    >>> result = analyzer.compare_conditions(
    ...     expression_matrix=matrix,
    ...     homeolog_pairs=homeologs,
    ...     condition1="control",
    ...     condition2="drought",
    ... )
    >>> print(f"Found {result.n_differential} differential pairs")
    """

    def __init__(
        self,
        min_expr: float = 1.0,
        log2_threshold: float = 1.0,
        log2_diff_threshold: float = 1.0,
        test_method: str = "paired_t",
    ) -> None:
        self.min_expr = min_expr
        self.log2_threshold = log2_threshold
        self.log2_diff_threshold = log2_diff_threshold
        self.test_method = test_method

        self.extractor = HomeologExpressionExtractor(min_mean_expr=0.0)
        self.bias_calculator = ExpressionBiasCalculator(
            min_expr=min_expr,
            log2_threshold=log2_threshold,
            test_method=test_method,
        )

    def analyze_all_conditions(
        self,
        expression_matrix: ExpressionMatrix,
        homeolog_pairs,
    ) -> dict[str, ExpressionBiasResult]:
        """Analyze expression bias for all conditions.

        Parameters
        ----------
        expression_matrix : ExpressionMatrix
            Gene expression matrix.
        homeolog_pairs : HomeologResult or list
            Homeolog pairs.

        Returns
        -------
        dict
            Condition to bias result mapping.
        """
        conditions = expression_matrix.conditions()
        results = {}

        for condition in conditions:
            logger.info(f"Analyzing bias for condition: {condition}")

            # Subset to condition
            condition_samples = [
                s.sample_id for s in expression_matrix.samples
                if s.condition == condition
            ]

            if len(condition_samples) < 2:
                logger.warning(
                    f"Skipping {condition}: only {len(condition_samples)} samples"
                )
                continue

            subset_matrix = expression_matrix.subset_samples(condition_samples)

            # Extract homeolog expression
            homeolog_expr = self.extractor.extract(subset_matrix, homeolog_pairs)

            # Calculate bias
            bias_result = self.bias_calculator.calculate(homeolog_expr)

            results[condition] = bias_result

        return results

    def compare_conditions(
        self,
        expression_matrix: ExpressionMatrix,
        homeolog_pairs,
        condition1: str,
        condition2: str,
    ) -> ConditionComparisonResult:
        """Compare expression bias between two conditions.

        Parameters
        ----------
        expression_matrix : ExpressionMatrix
            Gene expression matrix.
        homeolog_pairs : HomeologResult or list
            Homeolog pairs.
        condition1 : str
            First condition.
        condition2 : str
            Second condition.

        Returns
        -------
        ConditionComparisonResult
            Comparison results.
        """
        logger.info(f"Comparing bias: {condition1} vs {condition2}")

        # Get samples for each condition
        cond1_samples = [
            s.sample_id for s in expression_matrix.samples
            if s.condition == condition1
        ]
        cond2_samples = [
            s.sample_id for s in expression_matrix.samples
            if s.condition == condition2
        ]

        if not cond1_samples:
            raise ValueError(f"No samples for condition: {condition1}")
        if not cond2_samples:
            raise ValueError(f"No samples for condition: {condition2}")

        # Subset matrices
        matrix1 = expression_matrix.subset_samples(cond1_samples)
        matrix2 = expression_matrix.subset_samples(cond2_samples)

        # Extract expression and calculate bias
        expr1 = self.extractor.extract(matrix1, homeolog_pairs)
        expr2 = self.extractor.extract(matrix2, homeolog_pairs)

        bias1 = self.bias_calculator.calculate(expr1)
        bias2 = self.bias_calculator.calculate(expr2)

        # Compare biases
        differential = self._compare_biases(
            expr1, expr2, bias1, bias2, condition1, condition2
        )

        return ConditionComparisonResult(
            condition1=condition1,
            condition2=condition2,
            differential_biases=differential,
            condition1_result=bias1,
            condition2_result=bias2,
        )

    def _compare_biases(
        self,
        expr1: HomeologExpressionResult,
        expr2: HomeologExpressionResult,
        bias1: ExpressionBiasResult,
        bias2: ExpressionBiasResult,
        condition1: str,
        condition2: str,
    ) -> list[DifferentialBias]:
        """Compare biases between conditions.

        Parameters
        ----------
        expr1 : HomeologExpressionResult
            Expression in condition 1.
        expr2 : HomeologExpressionResult
            Expression in condition 2.
        bias1 : ExpressionBiasResult
            Bias results for condition 1.
        bias2 : ExpressionBiasResult
            Bias results for condition 2.
        condition1 : str
            First condition name.
        condition2 : str
            Second condition name.

        Returns
        -------
        list[DifferentialBias]
            Differential bias results.
        """
        # Index biases
        bias1_dict = {b.pair_id: b for b in bias1.biases}
        bias2_dict = {b.pair_id: b for b in bias2.biases}

        # Index expression
        expr1_dict = {p.pair_id: p for p in expr1.pairs}
        expr2_dict = {p.pair_id: p for p in expr2.pairs}

        # Find common pairs
        common_pairs = set(bias1_dict.keys()) & set(bias2_dict.keys())

        differential = []
        pvalues = []

        for pair_id in common_pairs:
            b1 = bias1_dict[pair_id]
            b2 = bias2_dict[pair_id]

            log2_diff = b2.log2_ratio - b1.log2_ratio

            # Test for differential bias
            e1 = expr1_dict.get(pair_id)
            e2 = expr2_dict.get(pair_id)

            if e1 is not None and e2 is not None:
                pvalue = self._test_differential_bias(e1, e2)
            else:
                pvalue = 1.0

            pvalues.append(pvalue)

            differential.append(DifferentialBias(
                pair_id=pair_id,
                gene1_id=b1.gene1_id,
                gene2_id=b1.gene2_id,
                condition1=condition1,
                condition2=condition2,
                log2_ratio_cond1=b1.log2_ratio,
                log2_ratio_cond2=b2.log2_ratio,
                log2_ratio_diff=log2_diff,
                category_cond1=b1.category,
                category_cond2=b2.category,
                pvalue=pvalue,
                fdr=1.0,  # Will be updated
            ))

        # FDR correction
        fdrs = self._fdr_correction(np.array(pvalues))

        # Update with FDR
        result = []
        for diff, fdr in zip(differential, fdrs, strict=False):
            result.append(DifferentialBias(
                pair_id=diff.pair_id,
                gene1_id=diff.gene1_id,
                gene2_id=diff.gene2_id,
                condition1=diff.condition1,
                condition2=diff.condition2,
                log2_ratio_cond1=diff.log2_ratio_cond1,
                log2_ratio_cond2=diff.log2_ratio_cond2,
                log2_ratio_diff=diff.log2_ratio_diff,
                category_cond1=diff.category_cond1,
                category_cond2=diff.category_cond2,
                pvalue=diff.pvalue,
                fdr=fdr,
            ))

        return result

    def _test_differential_bias(
        self,
        expr1: HomeologExpression,
        expr2: HomeologExpression,
    ) -> float:
        """Test for differential bias between conditions.

        Parameters
        ----------
        expr1 : HomeologExpression
            Expression in condition 1.
        expr2 : HomeologExpression
            Expression in condition 2.

        Returns
        -------
        float
            P-value for differential bias.
        """
        pc = 0.01

        # Calculate log2 ratios
        ratios1 = np.log2((expr1.gene1_expr + pc) / (expr1.gene2_expr + pc))
        ratios2 = np.log2((expr2.gene1_expr + pc) / (expr2.gene2_expr + pc))

        # Two-sample t-test
        try:
            _, pvalue = stats.ttest_ind(ratios1, ratios2)
            return float(pvalue) if not np.isnan(pvalue) else 1.0
        except Exception:
            return 1.0

    def _fdr_correction(self, pvalues: np.ndarray) -> np.ndarray:
        """Apply Benjamini-Hochberg FDR correction."""
        n = len(pvalues)
        if n == 0:
            return np.array([])

        sorted_indices = np.argsort(pvalues)
        sorted_pvals = pvalues[sorted_indices]

        fdr = np.zeros(n)
        fdr[sorted_indices] = sorted_pvals * n / (np.arange(n) + 1)

        fdr_sorted = fdr[sorted_indices]
        for i in range(n - 2, -1, -1):
            fdr_sorted[i] = min(fdr_sorted[i], fdr_sorted[i + 1])
        fdr[sorted_indices] = fdr_sorted

        return np.minimum(fdr, 1.0)


def analyze_condition_bias(
    expression_matrix: ExpressionMatrix,
    homeolog_pairs,
    condition1: str | None = None,
    condition2: str | None = None,
) -> ConditionComparisonResult | dict[str, ExpressionBiasResult]:
    """Convenience function for condition-specific bias analysis.

    Parameters
    ----------
    expression_matrix : ExpressionMatrix
        Gene expression matrix.
    homeolog_pairs : HomeologResult or list
        Homeolog pairs.
    condition1 : str, optional
        First condition for comparison.
    condition2 : str, optional
        Second condition for comparison.

    Returns
    -------
    ConditionComparisonResult or dict
        Comparison result if both conditions specified,
        otherwise dict of per-condition results.
    """
    analyzer = ConditionBiasAnalyzer()

    if condition1 and condition2:
        return analyzer.compare_conditions(
            expression_matrix, homeolog_pairs, condition1, condition2
        )
    else:
        return analyzer.analyze_all_conditions(expression_matrix, homeolog_pairs)


def write_condition_comparison(
    result: ConditionComparisonResult,
    output: Path | str,
) -> None:
    """Write condition comparison results to file.

    Parameters
    ----------
    result : ConditionComparisonResult
        Comparison results.
    output : Path or str
        Output file path.
    """
    output = Path(output)

    with open(output, "w") as f:
        header = [
            "pair_id", "gene1_id", "gene2_id",
            "condition1", "condition2",
            "log2_ratio_cond1", "log2_ratio_cond2", "log2_ratio_diff",
            "category_cond1", "category_cond2",
            "pvalue", "fdr", "is_differential", "category_changed",
        ]
        f.write("\t".join(header) + "\n")

        for diff in result.differential_biases:
            row = [
                diff.pair_id,
                diff.gene1_id,
                diff.gene2_id,
                diff.condition1,
                diff.condition2,
                f"{diff.log2_ratio_cond1:.4f}",
                f"{diff.log2_ratio_cond2:.4f}",
                f"{diff.log2_ratio_diff:.4f}",
                diff.category_cond1.value,
                diff.category_cond2.value,
                f"{diff.pvalue:.4e}",
                f"{diff.fdr:.4e}",
                str(diff.is_differential).lower(),
                str(diff.category_changed).lower(),
            ]
            f.write("\t".join(row) + "\n")

    logger.info(f"Wrote comparison results to {output}")
