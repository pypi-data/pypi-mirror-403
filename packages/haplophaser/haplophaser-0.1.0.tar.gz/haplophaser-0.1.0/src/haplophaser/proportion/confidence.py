"""Confidence interval estimation for haplotype proportions.

This module provides methods for calculating confidence intervals
around proportion estimates.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from haplophaser.markers.diagnostic import DiagnosticMarkerSet
    from haplophaser.proportion.genotypes import SampleMarkerGenotypes
    from haplophaser.proportion.results import ProportionResults

logger = logging.getLogger(__name__)


class ConfidenceMethod(Enum):
    """Method for calculating confidence intervals."""

    BOOTSTRAP = "bootstrap"
    BINOMIAL = "binomial"
    LIKELIHOOD_RATIO = "likelihood_ratio"


class ConfidenceEstimator:
    """Estimate confidence intervals for proportion estimates.

    Supports three methods:
    - bootstrap: Resample markers and recalculate proportions
    - binomial: Assume binomial distribution for allele counts
    - likelihood_ratio: Profile likelihood confidence intervals
    """

    def __init__(
        self,
        method: str | ConfidenceMethod = "bootstrap",
        confidence_level: float = 0.95,
        n_bootstrap: int = 1000,
        random_seed: int | None = None,
    ) -> None:
        """Initialize the confidence estimator.

        Args:
            method: Confidence interval method
            confidence_level: Desired confidence level (default 0.95)
            n_bootstrap: Number of bootstrap iterations
            random_seed: Random seed for reproducibility
        """
        if isinstance(method, str):
            method = ConfidenceMethod(method)
        self.method = method
        self.confidence_level = confidence_level
        self.n_bootstrap = n_bootstrap
        self.rng = np.random.default_rng(random_seed)

    def add_confidence_intervals(
        self,
        results: ProportionResults,
        sample_genotypes: dict[str, SampleMarkerGenotypes],
        markers: DiagnosticMarkerSet,
    ) -> None:
        """Add confidence intervals to existing proportion results.

        Modifies results in-place.

        Args:
            results: Proportion results to add CIs to
            sample_genotypes: Sample genotypes used for estimation
            markers: Diagnostic marker set
        """
        logger.info(f"Calculating {self.method.value} confidence intervals")

        marker_by_id = {m.variant_id: m for m in markers}

        for sample in results:
            genotypes = sample_genotypes.get(sample.sample_name)
            if genotypes is None:
                continue

            for window in sample.windows:
                # Get genotypes and markers for this window
                window_genos = []
                window_markers = []

                for geno in genotypes.get_chromosome_genotypes(window.chrom):
                    if (
                        window.start <= geno.pos < window.end
                        and not geno.is_missing
                    ):
                        marker = marker_by_id.get(geno.variant_id)
                        if marker is not None:
                            window_genos.append(geno)
                            window_markers.append(marker)

                if not window_genos:
                    continue

                # Calculate confidence intervals
                if self.method == ConfidenceMethod.BOOTSTRAP:
                    ci = self._bootstrap_ci(
                        window_genos,
                        window_markers,
                        sample.founders,
                        window.proportions,
                    )
                elif self.method == ConfidenceMethod.BINOMIAL:
                    ci = self._binomial_ci(
                        window_genos,
                        window_markers,
                        sample.founders,
                        window.proportions,
                    )
                else:  # LIKELIHOOD_RATIO
                    ci = self._likelihood_ratio_ci(
                        window_genos,
                        window_markers,
                        sample.founders,
                        window.proportions,
                    )

                window.confidence_intervals = ci

    def _bootstrap_ci(
        self,
        genotypes: list,
        markers: list,
        founders: list[str],
        point_estimates: dict[str, float],
    ) -> dict[str, tuple[float, float]]:
        """Calculate bootstrap confidence intervals.

        Args:
            genotypes: List of genotypes in window
            markers: Corresponding markers
            founders: List of founder names
            point_estimates: Point estimates (for reference)

        Returns:
            Dict mapping founders to (lower, upper) CI bounds
        """
        n_markers = len(genotypes)
        if n_markers == 0:
            return dict.fromkeys(founders, (0.0, 1.0))

        # Bootstrap samples
        bootstrap_estimates = {f: [] for f in founders}

        for _ in range(self.n_bootstrap):
            # Resample with replacement
            indices = self.rng.integers(0, n_markers, size=n_markers)
            boot_genos = [genotypes[i] for i in indices]
            boot_markers = [markers[i] for i in indices]

            # Calculate proportions using frequency method
            props = self._estimate_frequency(boot_genos, boot_markers, founders)

            for f, p in props.items():
                bootstrap_estimates[f].append(p)

        # Calculate percentile confidence intervals
        alpha = 1 - self.confidence_level
        lower_pct = alpha / 2 * 100
        upper_pct = (1 - alpha / 2) * 100

        ci = {}
        for f in founders:
            estimates = np.array(bootstrap_estimates[f])
            lower = np.percentile(estimates, lower_pct)
            upper = np.percentile(estimates, upper_pct)
            ci[f] = (float(lower), float(upper))

        return ci

    def _binomial_ci(
        self,
        genotypes: list,
        markers: list,
        founders: list[str],
        point_estimates: dict[str, float],
    ) -> dict[str, tuple[float, float]]:
        """Calculate binomial (Wilson score) confidence intervals.

        This method treats each allele as a Bernoulli trial.

        Args:
            genotypes: List of genotypes in window
            markers: Corresponding markers
            founders: List of founder names
            point_estimates: Point estimates

        Returns:
            Dict mapping founders to (lower, upper) CI bounds
        """
        from scipy import stats

        n_alleles = sum(len(g.genotype) for g in genotypes if not g.is_missing)

        if n_alleles == 0:
            return dict.fromkeys(founders, (0.0, 1.0))

        z = stats.norm.ppf(1 - (1 - self.confidence_level) / 2)

        ci = {}
        for f in founders:
            p = point_estimates.get(f, 0.5)

            # Wilson score interval
            denominator = 1 + z**2 / n_alleles
            center = (p + z**2 / (2 * n_alleles)) / denominator
            margin = (
                z
                * np.sqrt(p * (1 - p) / n_alleles + z**2 / (4 * n_alleles**2))
                / denominator
            )

            lower = max(0.0, center - margin)
            upper = min(1.0, center + margin)
            ci[f] = (float(lower), float(upper))

        return ci

    def _likelihood_ratio_ci(
        self,
        genotypes: list,
        markers: list,
        founders: list[str],
        point_estimates: dict[str, float],
    ) -> dict[str, tuple[float, float]]:
        """Calculate likelihood ratio confidence intervals.

        Uses the chi-squared approximation for the likelihood ratio.

        Args:
            genotypes: List of genotypes in window
            markers: Corresponding markers
            founders: List of founder names
            point_estimates: Point estimates

        Returns:
            Dict mapping founders to (lower, upper) CI bounds
        """
        from scipy import stats

        n_markers = len(genotypes)
        if n_markers == 0:
            return dict.fromkeys(founders, (0.0, 1.0))

        # Chi-squared critical value for 1 df
        chi2_crit = stats.chi2.ppf(self.confidence_level, df=1)

        ci = {}
        for f in founders:
            p_mle = point_estimates.get(f, 0.5)

            # Calculate log-likelihood at MLE
            ll_mle = self._calc_log_likelihood(genotypes, markers, founders, p_mle, f)

            # Find bounds where 2*(ll_mle - ll) = chi2_crit
            # Search for lower bound
            lower = self._search_likelihood_bound(
                genotypes, markers, founders, f, p_mle, ll_mle, chi2_crit, lower=True
            )

            # Search for upper bound
            upper = self._search_likelihood_bound(
                genotypes, markers, founders, f, p_mle, ll_mle, chi2_crit, lower=False
            )

            ci[f] = (float(lower), float(upper))

        return ci

    def _calc_log_likelihood(
        self,
        genotypes: list,
        markers: list,
        founders: list[str],
        prop: float,
        target_founder: str,
    ) -> float:
        """Calculate log-likelihood for a given proportion value.

        Args:
            genotypes: List of genotypes
            markers: Corresponding markers
            founders: List of founder names
            prop: Proportion value for target founder
            target_founder: Founder to vary proportion for

        Returns:
            Log-likelihood value
        """
        ll = 0.0

        for geno, marker in zip(genotypes, markers, strict=False):
            if marker is None:
                continue

            # Probability of observing genotype
            prob = 0.0
            for f in founders:
                if f == target_founder:
                    f_prop = prop
                else:
                    # Distribute remaining probability equally
                    remaining = 1.0 - prop
                    n_other = len(founders) - 1
                    f_prop = remaining / n_other if n_other > 0 else 0.0

                founder_freqs = marker.founder_frequencies.get(f, {})
                founder_ref = founder_freqs.get(marker.ref, 0.5)
                founder_alt = founder_freqs.get(marker.alt, 0.5)

                # Probability given this founder
                geno_prob = 1.0
                for allele in geno.alleles:
                    if allele == marker.ref:
                        geno_prob *= founder_ref
                    elif allele == marker.alt:
                        geno_prob *= founder_alt

                prob += f_prop * geno_prob

            ll += np.log(max(prob, 1e-10))

        return ll

    def _search_likelihood_bound(
        self,
        genotypes: list,
        markers: list,
        founders: list[str],
        target_founder: str,
        p_mle: float,
        ll_mle: float,
        chi2_crit: float,
        lower: bool,
    ) -> float:
        """Binary search for likelihood ratio CI bound.

        Args:
            genotypes: List of genotypes
            markers: Corresponding markers
            founders: List of founder names
            target_founder: Target founder
            p_mle: MLE proportion
            ll_mle: Log-likelihood at MLE
            chi2_crit: Chi-squared critical value
            lower: If True, search for lower bound; else upper

        Returns:
            CI bound
        """
        if lower:
            left, right = 0.0, p_mle
        else:
            left, right = p_mle, 1.0

        # Binary search
        for _ in range(50):  # Max iterations
            mid = (left + right) / 2
            ll_mid = self._calc_log_likelihood(
                genotypes, markers, founders, mid, target_founder
            )

            # Likelihood ratio statistic
            lr_stat = 2 * (ll_mle - ll_mid)

            if lr_stat < chi2_crit:
                if lower:
                    right = mid
                else:
                    left = mid
            else:
                if lower:
                    left = mid
                else:
                    right = mid

            if abs(right - left) < 0.001:
                break

        return left if lower else right

    def _estimate_frequency(
        self,
        genotypes: list,
        markers: list,
        founders: list[str],
    ) -> dict[str, float]:
        """Estimate proportions using frequency method (for bootstrap)."""
        if not genotypes or not markers:
            return {f: 1.0 / len(founders) for f in founders}

        founder_contributions = dict.fromkeys(founders, 0.0)
        total_weight = 0.0

        for geno, marker in zip(genotypes, markers, strict=False):
            if marker is None:
                continue

            ref_freq = geno.get_allele_frequency(marker.ref)
            alt_freq = geno.get_allele_frequency(marker.alt)
            weight = marker.confidence

            for founder in founders:
                founder_freqs = marker.founder_frequencies.get(founder, {})
                founder_ref = founder_freqs.get(marker.ref, 0.5)
                founder_alt = founder_freqs.get(marker.alt, 0.5)

                similarity = 1.0 - 0.5 * (
                    abs(ref_freq - founder_ref) + abs(alt_freq - founder_alt)
                )

                founder_contributions[founder] += similarity * weight
                total_weight += weight / len(founders)

        if total_weight > 0:
            total = sum(founder_contributions.values())
            if total > 0:
                return {f: v / total for f, v in founder_contributions.items()}

        return {f: 1.0 / len(founders) for f in founders}


def add_confidence_intervals(
    results: ProportionResults,
    sample_genotypes: dict[str, SampleMarkerGenotypes],
    markers: DiagnosticMarkerSet,
    method: str = "bootstrap",
    confidence_level: float = 0.95,
    n_bootstrap: int = 1000,
) -> None:
    """Add confidence intervals to proportion results.

    Convenience function wrapping ConfidenceEstimator.

    Args:
        results: Proportion results to add CIs to
        sample_genotypes: Sample genotypes
        markers: Diagnostic marker set
        method: CI method ("bootstrap", "binomial", "likelihood_ratio")
        confidence_level: Confidence level (default 0.95)
        n_bootstrap: Number of bootstrap samples
    """
    estimator = ConfidenceEstimator(
        method=method,
        confidence_level=confidence_level,
        n_bootstrap=n_bootstrap,
    )
    estimator.add_confidence_intervals(results, sample_genotypes, markers)
