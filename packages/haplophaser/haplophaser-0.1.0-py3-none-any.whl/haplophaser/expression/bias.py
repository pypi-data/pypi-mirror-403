"""
Expression bias calculation for homeolog pairs.

Calculates log2 ratios, fold changes, and statistical significance
of expression bias between homeologous genes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import stats

from haplophaser.expression.models import (
    BiasCategory,
    ExpressionBias,
    ExpressionBiasResult,
    HomeologExpression,
    HomeologExpressionResult,
)

logger = logging.getLogger(__name__)


@dataclass
class BiasParams:
    """Parameters for bias calculation.

    Parameters
    ----------
    min_expr : float
        Minimum expression to be considered "expressed".
    log2_threshold : float
        |log2 ratio| threshold for bias classification.
    pseudocount : float
        Pseudocount for log2 ratio calculation.
    test_method : str
        Statistical test: 'paired_t', 'wilcoxon', 'bootstrap'.
    n_bootstrap : int
        Number of bootstrap iterations.
    """

    min_expr: float = 1.0
    log2_threshold: float = 1.0
    pseudocount: float = 0.01
    test_method: str = "paired_t"
    n_bootstrap: int = 1000


class ExpressionBiasCalculator:
    """Calculate expression bias for homeolog pairs.

    Performs statistical testing and classification of expression
    bias between homeologous genes.

    Parameters
    ----------
    min_expr : float
        Minimum expression for "expressed" classification.
    log2_threshold : float
        |log2 ratio| threshold for significant bias.
    test_method : str
        Statistical test method.

    Examples
    --------
    >>> calculator = ExpressionBiasCalculator(
    ...     min_expr=1.0,
    ...     log2_threshold=1.0,
    ...     test_method="paired_t",
    ... )
    >>> result = calculator.calculate(homeolog_expression)
    >>> print(f"Found {result.n_significant} significantly biased pairs")
    """

    def __init__(
        self,
        min_expr: float = 1.0,
        log2_threshold: float = 1.0,
        test_method: str = "paired_t",
    ) -> None:
        self.params = BiasParams(
            min_expr=min_expr,
            log2_threshold=log2_threshold,
            test_method=test_method,
        )

    def calculate(
        self,
        homeolog_expression: HomeologExpressionResult | list[HomeologExpression],
    ) -> ExpressionBiasResult:
        """Calculate expression bias for homeolog pairs.

        Parameters
        ----------
        homeolog_expression : HomeologExpressionResult or list[HomeologExpression]
            Expression data for homeolog pairs.

        Returns
        -------
        ExpressionBiasResult
            Bias results with statistics.
        """
        if isinstance(homeolog_expression, HomeologExpressionResult):
            pairs = homeolog_expression.pairs
        else:
            pairs = homeolog_expression

        logger.info(f"Calculating expression bias for {len(pairs)} pairs")

        biases = []
        for pair in pairs:
            bias = self._calculate_pair_bias(pair)
            biases.append(bias)

        # Apply FDR correction
        pvalues = np.array([b.pvalue for b in biases])
        fdrs = self._fdr_correction(pvalues)

        # Update biases with FDR
        corrected_biases = []
        for bias, fdr in zip(biases, fdrs, strict=False):
            corrected_biases.append(ExpressionBias(
                pair_id=bias.pair_id,
                gene1_id=bias.gene1_id,
                gene2_id=bias.gene2_id,
                gene1_subgenome=bias.gene1_subgenome,
                gene2_subgenome=bias.gene2_subgenome,
                log2_ratio=bias.log2_ratio,
                fold_change=bias.fold_change,
                category=bias.category,
                pvalue=bias.pvalue,
                fdr=fdr,
                mean_gene1=bias.mean_gene1,
                mean_gene2=bias.mean_gene2,
            ))

        # Update category based on FDR significance
        final_biases = []
        for bias in corrected_biases:
            category = self._classify_bias(
                bias.log2_ratio,
                bias.fdr,
                bias.mean_gene1,
                bias.mean_gene2,
            )
            final_biases.append(ExpressionBias(
                pair_id=bias.pair_id,
                gene1_id=bias.gene1_id,
                gene2_id=bias.gene2_id,
                gene1_subgenome=bias.gene1_subgenome,
                gene2_subgenome=bias.gene2_subgenome,
                log2_ratio=bias.log2_ratio,
                fold_change=bias.fold_change,
                category=category,
                pvalue=bias.pvalue,
                fdr=bias.fdr,
                mean_gene1=bias.mean_gene1,
                mean_gene2=bias.mean_gene2,
            ))

        logger.info(
            f"Found {sum(1 for b in final_biases if b.is_significant)} "
            "significantly biased pairs"
        )

        return ExpressionBiasResult(
            biases=final_biases,
            parameters={
                "min_expr": self.params.min_expr,
                "log2_threshold": self.params.log2_threshold,
                "test_method": self.params.test_method,
            },
        )

    def _calculate_pair_bias(
        self,
        pair: HomeologExpression,
    ) -> ExpressionBias:
        """Calculate bias for a single pair.

        Parameters
        ----------
        pair : HomeologExpression
            Expression data for homeolog pair.

        Returns
        -------
        ExpressionBias
            Bias result for this pair.
        """
        expr1 = pair.gene1_expr
        expr2 = pair.gene2_expr

        mean1 = np.mean(expr1)
        mean2 = np.mean(expr2)

        # Calculate log2 ratio
        pc = self.params.pseudocount
        log2_ratio = np.mean(np.log2((expr1 + pc) / (expr2 + pc)))

        # Calculate fold change
        if mean2 > pc:
            fold_change = (mean1 + pc) / (mean2 + pc)
        else:
            fold_change = float('inf') if mean1 > pc else 1.0

        # Statistical test
        pvalue = self._test_bias(expr1, expr2)

        # Initial category (will be updated after FDR correction)
        category = BiasCategory.BALANCED

        return ExpressionBias(
            pair_id=pair.pair_id,
            gene1_id=pair.gene1_id,
            gene2_id=pair.gene2_id,
            gene1_subgenome=pair.gene1_subgenome,
            gene2_subgenome=pair.gene2_subgenome,
            log2_ratio=log2_ratio,
            fold_change=fold_change,
            category=category,
            pvalue=pvalue,
            fdr=1.0,  # Will be updated
            mean_gene1=mean1,
            mean_gene2=mean2,
        )

    def _test_bias(
        self,
        expr1: np.ndarray,
        expr2: np.ndarray,
    ) -> float:
        """Perform statistical test for expression bias.

        Parameters
        ----------
        expr1 : np.ndarray
            Expression values for gene1.
        expr2 : np.ndarray
            Expression values for gene2.

        Returns
        -------
        float
            P-value for bias test.
        """
        if len(expr1) < 3 or len(expr2) < 3:
            return 1.0

        # Add pseudocount and log transform
        pc = self.params.pseudocount
        log_expr1 = np.log2(expr1 + pc)
        log_expr2 = np.log2(expr2 + pc)

        if self.params.test_method == "paired_t":
            # Paired t-test on log-transformed values
            try:
                _, pvalue = stats.ttest_rel(log_expr1, log_expr2)
                return float(pvalue) if not np.isnan(pvalue) else 1.0
            except Exception:
                return 1.0

        elif self.params.test_method == "wilcoxon":
            # Wilcoxon signed-rank test
            try:
                _, pvalue = stats.wilcoxon(log_expr1, log_expr2)
                return float(pvalue) if not np.isnan(pvalue) else 1.0
            except Exception:
                return 1.0

        elif self.params.test_method == "bootstrap":
            return self._bootstrap_test(expr1, expr2)

        else:
            raise ValueError(f"Unknown test method: {self.params.test_method}")

    def _bootstrap_test(
        self,
        expr1: np.ndarray,
        expr2: np.ndarray,
    ) -> float:
        """Bootstrap test for expression bias.

        Parameters
        ----------
        expr1 : np.ndarray
            Expression values for gene1.
        expr2 : np.ndarray
            Expression values for gene2.

        Returns
        -------
        float
            Bootstrap p-value.
        """
        pc = self.params.pseudocount
        observed_diff = np.mean(np.log2(expr1 + pc)) - np.mean(np.log2(expr2 + pc))

        n = len(expr1)
        count_extreme = 0

        for _ in range(self.params.n_bootstrap):
            # Resample with replacement
            indices = np.random.choice(n, n, replace=True)
            resampled1 = expr1[indices]
            resampled2 = expr2[indices]

            # Randomly flip signs to simulate null
            flip = np.random.choice([-1, 1], n)
            null_diff = np.mean(flip * (np.log2(resampled1 + pc) - np.log2(resampled2 + pc)))

            if abs(null_diff) >= abs(observed_diff):
                count_extreme += 1

        return count_extreme / self.params.n_bootstrap

    def _classify_bias(
        self,
        log2_ratio: float,
        fdr: float,
        mean1: float,
        mean2: float,
    ) -> BiasCategory:
        """Classify bias based on ratio and significance.

        Parameters
        ----------
        log2_ratio : float
            Log2 ratio of expression.
        fdr : float
            FDR-corrected p-value.
        mean1 : float
            Mean expression of gene1.
        mean2 : float
            Mean expression of gene2.

        Returns
        -------
        BiasCategory
            Bias classification.
        """
        min_expr = self.params.min_expr
        threshold = self.params.log2_threshold

        # Check expression status
        gene1_expressed = mean1 >= min_expr
        gene2_expressed = mean2 >= min_expr

        if not gene1_expressed and not gene2_expressed:
            return BiasCategory.SILENT

        if gene1_expressed and not gene2_expressed:
            return BiasCategory.SG1_ONLY

        if gene2_expressed and not gene1_expressed:
            return BiasCategory.SG2_ONLY

        # Both expressed - check for significant bias
        if fdr >= 0.05:
            return BiasCategory.BALANCED

        if log2_ratio > threshold:
            return BiasCategory.SG1_DOMINANT
        elif log2_ratio < -threshold:
            return BiasCategory.SG2_DOMINANT
        else:
            return BiasCategory.BALANCED

    def _fdr_correction(
        self,
        pvalues: np.ndarray,
        method: str = "bh",
    ) -> np.ndarray:
        """Apply FDR correction to p-values.

        Parameters
        ----------
        pvalues : np.ndarray
            Raw p-values.
        method : str
            Correction method: 'bh' (Benjamini-Hochberg).

        Returns
        -------
        np.ndarray
            FDR-corrected p-values.
        """
        n = len(pvalues)
        if n == 0:
            return np.array([])

        # Benjamini-Hochberg procedure
        sorted_indices = np.argsort(pvalues)
        sorted_pvals = pvalues[sorted_indices]

        # Calculate FDR
        fdr = np.zeros(n)
        fdr[sorted_indices] = sorted_pvals * n / (np.arange(n) + 1)

        # Enforce monotonicity
        fdr_sorted = fdr[sorted_indices]
        for i in range(n - 2, -1, -1):
            fdr_sorted[i] = min(fdr_sorted[i], fdr_sorted[i + 1])
        fdr[sorted_indices] = fdr_sorted

        # Cap at 1.0
        fdr = np.minimum(fdr, 1.0)

        return fdr


def calculate_expression_bias(
    homeolog_expression: HomeologExpressionResult | list[HomeologExpression],
    min_expr: float = 1.0,
    log2_threshold: float = 1.0,
    test_method: str = "paired_t",
) -> ExpressionBiasResult:
    """Convenience function to calculate expression bias.

    Parameters
    ----------
    homeolog_expression : HomeologExpressionResult or list[HomeologExpression]
        Expression data for homeolog pairs.
    min_expr : float
        Minimum expression for "expressed".
    log2_threshold : float
        |log2 ratio| threshold for bias.
    test_method : str
        Statistical test method.

    Returns
    -------
    ExpressionBiasResult
        Bias results.
    """
    calculator = ExpressionBiasCalculator(
        min_expr=min_expr,
        log2_threshold=log2_threshold,
        test_method=test_method,
    )

    return calculator.calculate(homeolog_expression)


def write_expression_bias(
    result: ExpressionBiasResult,
    output: Path | str,
) -> None:
    """Write expression bias results to file.

    Parameters
    ----------
    result : ExpressionBiasResult
        Bias results.
    output : Path or str
        Output file path.
    """
    output = Path(output)

    with open(output, "w") as f:
        header = [
            "pair_id", "gene1_id", "gene2_id",
            "gene1_subgenome", "gene2_subgenome",
            "mean_gene1", "mean_gene2", "log2_ratio", "fold_change",
            "category", "pvalue", "fdr", "is_significant",
        ]
        f.write("\t".join(header) + "\n")

        for bias in result.biases:
            row = [
                bias.pair_id,
                bias.gene1_id,
                bias.gene2_id,
                bias.gene1_subgenome,
                bias.gene2_subgenome,
                f"{bias.mean_gene1:.4f}",
                f"{bias.mean_gene2:.4f}",
                f"{bias.log2_ratio:.4f}",
                f"{bias.fold_change:.4f}",
                bias.category.value,
                f"{bias.pvalue:.4e}",
                f"{bias.fdr:.4e}",
                str(bias.is_significant).lower(),
            ]
            f.write("\t".join(row) + "\n")

    logger.info(f"Wrote {result.n_pairs} bias results to {output}")
