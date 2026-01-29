"""
Subgenome dominance analysis for expression bias.

Tests for genome-wide expression dominance of one subgenome over another,
quantifying the overall bias in expression patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from scipy import stats

from haplophaser.expression.models import (
    DominanceResult,
    ExpressionBiasResult,
)

logger = logging.getLogger(__name__)


@dataclass
class DominanceParams:
    """Parameters for dominance analysis.

    Parameters
    ----------
    min_significant : int
        Minimum number of significant pairs for testing.
    test_method : str
        Statistical test: 'chi2', 'binomial'.
    null_proportion : float
        Expected proportion under null hypothesis (0.5 = balanced).
    """

    min_significant: int = 10
    test_method: str = "chi2"
    null_proportion: float = 0.5


class SubgenomeDominanceAnalyzer:
    """Analyze genome-wide subgenome expression dominance.

    Tests whether one subgenome has significantly more highly expressed
    homeolog copies than expected by chance.

    Parameters
    ----------
    min_significant : int
        Minimum significant pairs for testing.
    test_method : str
        Statistical test method.

    Examples
    --------
    >>> analyzer = SubgenomeDominanceAnalyzer()
    >>> result = analyzer.test_dominance(bias_result)
    >>> if result.is_significant:
    ...     print(f"Dominant subgenome: {result.dominant_subgenome}")
    """

    def __init__(
        self,
        min_significant: int = 10,
        test_method: str = "chi2",
    ) -> None:
        self.params = DominanceParams(
            min_significant=min_significant,
            test_method=test_method,
        )

    def test_dominance(
        self,
        bias_result: ExpressionBiasResult,
    ) -> DominanceResult:
        """Test for genome-wide subgenome dominance.

        Parameters
        ----------
        bias_result : ExpressionBiasResult
            Expression bias results.

        Returns
        -------
        DominanceResult
            Dominance test results.
        """
        # Count pairs by dominant subgenome
        subgenome_counts: dict[str, int] = {}

        for bias in bias_result.biases:
            if not bias.is_significant:
                continue

            dominant = bias.dominant_subgenome
            if dominant:
                subgenome_counts[dominant] = subgenome_counts.get(dominant, 0) + 1

        total_biased = sum(subgenome_counts.values())

        logger.info(
            f"Testing dominance: {total_biased} significantly biased pairs"
        )

        if total_biased < self.params.min_significant:
            logger.warning(
                f"Only {total_biased} biased pairs, minimum is {self.params.min_significant}"
            )
            return DominanceResult(
                subgenome_counts=subgenome_counts,
                total_pairs=total_biased,
                chi2_statistic=0.0,
                pvalue=1.0,
                dominant_subgenome=None,
                effect_size=0.0,
            )

        # Perform statistical test
        if self.params.test_method == "chi2":
            chi2, pvalue = self._chi2_test(subgenome_counts, total_biased)
        else:
            chi2, pvalue = self._binomial_test(subgenome_counts, total_biased)

        # Determine dominant subgenome
        dominant_subgenome = None
        if pvalue < 0.05:
            max_count = max(subgenome_counts.values())
            for sg, count in subgenome_counts.items():
                if count == max_count:
                    dominant_subgenome = sg
                    break

        # Calculate effect size
        if len(subgenome_counts) == 2:
            counts = list(subgenome_counts.values())
            effect_size = abs(counts[0] - counts[1]) / total_biased
        else:
            # For more than 2 subgenomes
            effect_size = max(subgenome_counts.values()) / total_biased

        return DominanceResult(
            subgenome_counts=subgenome_counts,
            total_pairs=total_biased,
            chi2_statistic=chi2,
            pvalue=pvalue,
            dominant_subgenome=dominant_subgenome,
            effect_size=effect_size,
        )

    def test_dominance_by_region(
        self,
        bias_result: ExpressionBiasResult,
        regions: dict[str, list[str]],
    ) -> dict[str, DominanceResult]:
        """Test dominance by genomic region.

        Parameters
        ----------
        bias_result : ExpressionBiasResult
            Expression bias results.
        regions : dict[str, list[str]]
            Region name to pair IDs mapping.

        Returns
        -------
        dict[str, DominanceResult]
            Dominance results per region.
        """
        results = {}

        # Index biases by pair ID
        bias_dict = {b.pair_id: b for b in bias_result.biases}

        for region_name, pair_ids in regions.items():
            # Create subset bias result
            subset_biases = [
                bias_dict[pid] for pid in pair_ids
                if pid in bias_dict
            ]

            if not subset_biases:
                continue

            subset_result = ExpressionBiasResult(
                biases=subset_biases,
                parameters=bias_result.parameters,
            )

            results[region_name] = self.test_dominance(subset_result)

        return results

    def test_dominance_by_condition(
        self,
        condition_biases: dict[str, ExpressionBiasResult],
    ) -> dict[str, DominanceResult]:
        """Test dominance across conditions.

        Parameters
        ----------
        condition_biases : dict[str, ExpressionBiasResult]
            Condition to bias result mapping.

        Returns
        -------
        dict[str, DominanceResult]
            Dominance results per condition.
        """
        results = {}

        for condition, bias_result in condition_biases.items():
            results[condition] = self.test_dominance(bias_result)

        return results

    def _chi2_test(
        self,
        counts: dict[str, int],
        total: int,
    ) -> tuple[float, float]:
        """Chi-square test for dominance.

        Parameters
        ----------
        counts : dict[str, int]
            Subgenome to count mapping.
        total : int
            Total biased pairs.

        Returns
        -------
        tuple[float, float]
            (chi2 statistic, p-value)
        """
        n_subgenomes = len(counts)
        expected = total / n_subgenomes

        observed = list(counts.values())
        expected_vals = [expected] * n_subgenomes

        chi2, pvalue = stats.chisquare(observed, expected_vals)

        return float(chi2), float(pvalue)

    def _binomial_test(
        self,
        counts: dict[str, int],
        total: int,
    ) -> tuple[float, float]:
        """Binomial test for dominance (2 subgenomes only).

        Parameters
        ----------
        counts : dict[str, int]
            Subgenome to count mapping.
        total : int
            Total biased pairs.

        Returns
        -------
        tuple[float, float]
            (chi2 equivalent, p-value)
        """
        if len(counts) != 2:
            return self._chi2_test(counts, total)

        k = max(counts.values())

        # Two-sided binomial test
        result = stats.binomtest(k, total, self.params.null_proportion)
        pvalue = result.pvalue

        # Calculate chi2 equivalent for consistency
        expected = total / 2
        observed = list(counts.values())
        chi2 = sum((o - expected) ** 2 / expected for o in observed)

        return float(chi2), float(pvalue)


def analyze_subgenome_dominance(
    bias_result: ExpressionBiasResult,
    min_significant: int = 10,
    test_method: str = "chi2",
) -> DominanceResult:
    """Convenience function to test subgenome dominance.

    Parameters
    ----------
    bias_result : ExpressionBiasResult
        Expression bias results.
    min_significant : int
        Minimum significant pairs.
    test_method : str
        Statistical test method.

    Returns
    -------
    DominanceResult
        Dominance test results.
    """
    analyzer = SubgenomeDominanceAnalyzer(
        min_significant=min_significant,
        test_method=test_method,
    )

    return analyzer.test_dominance(bias_result)


# Backwards-compatible alias (renamed to avoid pytest collection)
# Users should use analyze_subgenome_dominance or the test_subgenome_dominance alias
def test_subgenome_dominance(
    bias_result: ExpressionBiasResult,
    min_significant: int = 10,
    test_method: str = "chi2",
) -> DominanceResult:
    """Alias for analyze_subgenome_dominance (for backwards compatibility)."""
    return analyze_subgenome_dominance(bias_result, min_significant, test_method)


# Tell pytest not to collect this as a test
test_subgenome_dominance.__test__ = False


def write_dominance_result(
    result: DominanceResult,
    output: Path | str,
) -> None:
    """Write dominance result to file.

    Parameters
    ----------
    result : DominanceResult
        Dominance test results.
    output : Path or str
        Output file path.
    """
    output = Path(output)

    with open(output, "w") as f:
        f.write("# Subgenome Dominance Analysis\n\n")
        f.write(f"Total biased pairs: {result.total_pairs}\n\n")

        f.write("Counts by subgenome:\n")
        for sg, count in result.subgenome_counts.items():
            prop = count / result.total_pairs if result.total_pairs > 0 else 0
            f.write(f"  {sg}: {count} ({prop:.1%})\n")

        f.write(f"\nChi-square statistic: {result.chi2_statistic:.4f}\n")
        f.write(f"P-value: {result.pvalue:.4e}\n")
        f.write(f"Effect size: {result.effect_size:.4f}\n")
        f.write(f"Significant: {result.is_significant}\n")

        if result.dominant_subgenome:
            f.write(f"Dominant subgenome: {result.dominant_subgenome}\n")

    logger.info(f"Wrote dominance results to {output}")
