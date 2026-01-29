"""Window-based haplotype proportion estimation.

This module provides the core algorithm for estimating founder haplotype
proportions using sliding windows across the genome.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

from haplophaser.proportion.genotypes import SampleMarkerGenotypes
from haplophaser.proportion.results import (
    ProportionResults,
    SampleProportions,
    WindowProportion,
)

if TYPE_CHECKING:
    from haplophaser.markers.diagnostic import DiagnosticMarkerSet

logger = logging.getLogger(__name__)


class EstimationMethod(Enum):
    """Method for estimating founder proportions."""

    FREQUENCY = "frequency"
    LIKELIHOOD = "likelihood"
    BAYESIAN = "bayesian"


@dataclass
class WindowDefinition:
    """Definition of a genomic window.

    Attributes:
        chrom: Chromosome name
        start: Start position (0-based)
        end: End position (exclusive)
    """

    chrom: str
    start: int
    end: int

    @property
    def size(self) -> int:
        """Get window size in base pairs."""
        return self.end - self.start

    @property
    def midpoint(self) -> int:
        """Get window midpoint."""
        return (self.start + self.end) // 2


class WindowProportionEstimator:
    """Estimate founder proportions in sliding windows.

    This class implements three estimation methods:
    - frequency: Simple allele frequency matching
    - likelihood: Maximum likelihood estimation
    - bayesian: Bayesian estimation with Dirichlet prior
    """

    def __init__(
        self,
        window_size: int = 1000000,
        step_size: int | None = None,
        min_markers: int = 1,
        method: str | EstimationMethod = "frequency",
        prior_weight: float = 0.1,
    ) -> None:
        """Initialize the estimator.

        Args:
            window_size: Size of windows in base pairs
            step_size: Step size for sliding windows (default: window_size // 2)
            min_markers: Minimum number of markers required per window
            method: Estimation method ("frequency", "likelihood", "bayesian")
            prior_weight: Weight for Dirichlet prior (bayesian method only)
        """
        self.window_size = window_size
        self.step_size = step_size if step_size is not None else window_size // 2
        self.min_markers = min_markers
        self.prior_weight = prior_weight

        if isinstance(method, str):
            method = EstimationMethod(method)
        self.method = method

    def estimate(
        self,
        sample_genotypes: dict[str, SampleMarkerGenotypes],
        markers: DiagnosticMarkerSet,
        chromosome_lengths: dict[str, int] | None = None,
    ) -> ProportionResults:
        """Estimate proportions for all samples.

        Args:
            sample_genotypes: Dict mapping sample names to marker genotypes
            markers: Diagnostic marker set
            chromosome_lengths: Optional dict of chromosome lengths

        Returns:
            ProportionResults with estimates for all samples
        """
        logger.info(
            f"Estimating proportions using {self.method.value} method "
            f"(window={self.window_size}, step={self.step_size})"
        )

        founders = markers.founders
        results = ProportionResults(
            founders=founders,
            method=self.method.value,
            window_size=self.window_size,
            step_size=self.step_size,
            min_markers=self.min_markers,
        )

        # Generate windows
        windows = self._generate_windows(markers, chromosome_lengths)
        logger.debug(f"Generated {len(windows)} windows")

        # Estimate for each sample
        for sample_name, genotypes in sample_genotypes.items():
            logger.debug(f"Processing sample {sample_name}")
            sample_props = self._estimate_sample(
                sample_name, genotypes, markers, windows, founders
            )
            results.add_sample(sample_props)

        return results

    def _generate_windows(
        self,
        markers: DiagnosticMarkerSet,
        chromosome_lengths: dict[str, int] | None = None,
    ) -> list[WindowDefinition]:
        """Generate sliding windows across all chromosomes.

        Args:
            markers: Marker set to determine chromosomes
            chromosome_lengths: Optional chromosome lengths

        Returns:
            List of window definitions
        """
        windows = []

        # Get chromosome extents from markers
        chrom_extents = {}
        for marker in markers:
            if marker.chrom not in chrom_extents:
                chrom_extents[marker.chrom] = [marker.pos, marker.pos]
            else:
                chrom_extents[marker.chrom][0] = min(
                    chrom_extents[marker.chrom][0], marker.pos
                )
                chrom_extents[marker.chrom][1] = max(
                    chrom_extents[marker.chrom][1], marker.pos
                )

        # Generate windows for each chromosome
        for chrom in sorted(chrom_extents.keys()):
            if chromosome_lengths and chrom in chromosome_lengths:
                chrom_len = chromosome_lengths[chrom]
            else:
                # Extend past last marker
                chrom_len = chrom_extents[chrom][1] + self.window_size

            # Start before first marker
            start_pos = max(0, chrom_extents[chrom][0] - self.window_size // 2)

            pos = start_pos
            while pos < chrom_len:
                end = min(pos + self.window_size, chrom_len)
                windows.append(WindowDefinition(chrom=chrom, start=pos, end=end))
                pos += self.step_size

        return windows

    def _estimate_sample(
        self,
        sample_name: str,
        genotypes: SampleMarkerGenotypes,
        markers: DiagnosticMarkerSet,
        windows: list[WindowDefinition],
        founders: list[str],
    ) -> SampleProportions:
        """Estimate proportions for a single sample.

        Args:
            sample_name: Name of the sample
            genotypes: Sample's marker genotypes
            markers: Diagnostic marker set
            windows: List of window definitions
            founders: List of founder names

        Returns:
            SampleProportions with window estimates
        """
        sample_props = SampleProportions(
            sample_name=sample_name,
            founders=founders,
        )

        # Build marker position index
        marker_by_id = {m.variant_id: m for m in markers}

        for window in windows:
            # Get genotypes in this window
            window_genotypes = []
            window_markers = []

            for geno in genotypes.get_chromosome_genotypes(window.chrom):
                if window.start <= geno.pos < window.end:
                    window_genotypes.append(geno)
                    marker = marker_by_id.get(geno.variant_id)
                    if marker is not None:
                        window_markers.append(marker)

            # Skip windows with too few markers
            non_missing = [g for g in window_genotypes if not g.is_missing]
            if len(non_missing) < self.min_markers:
                continue

            # Estimate proportions using selected method
            if self.method == EstimationMethod.FREQUENCY:
                proportions = self._estimate_frequency(
                    non_missing, window_markers, founders
                )
            elif self.method == EstimationMethod.LIKELIHOOD:
                proportions = self._estimate_likelihood(
                    non_missing, window_markers, founders
                )
            else:  # BAYESIAN
                proportions = self._estimate_bayesian(
                    non_missing, window_markers, founders
                )

            # Create window proportion
            window_prop = WindowProportion(
                chrom=window.chrom,
                start=window.start,
                end=window.end,
                proportions=proportions,
                n_markers=len(non_missing),
                method=self.method.value,
            )

            sample_props.add_window(window_prop)

        # Recalculate genome-wide proportions
        sample_props.recalculate_genome_wide()

        return sample_props

    def _estimate_frequency(
        self,
        genotypes: list,
        markers: list,
        founders: list[str],
    ) -> dict[str, float]:
        """Estimate proportions using frequency matching.

        For each marker, compare sample allele frequencies to founder
        frequencies and calculate weighted contributions.

        Args:
            genotypes: List of non-missing genotypes
            markers: Corresponding marker information
            founders: List of founder names

        Returns:
            Dict mapping founders to proportion estimates
        """
        if not genotypes or not markers:
            return {f: 1.0 / len(founders) for f in founders}

        # Accumulate founder contributions
        founder_contributions = dict.fromkeys(founders, 0.0)
        total_weight = 0.0

        for geno, marker in zip(genotypes, markers, strict=False):
            if marker is None:
                continue

            # Get sample allele frequencies
            ref_freq = geno.get_allele_frequency(marker.ref)
            alt_freq = geno.get_allele_frequency(marker.alt)

            # Weight by marker confidence
            weight = marker.confidence

            # Calculate contribution from each founder
            for founder in founders:
                founder_freqs = marker.founder_frequencies.get(founder, {})
                founder_ref = founder_freqs.get(marker.ref, 0.5)
                founder_alt = founder_freqs.get(marker.alt, 0.5)

                # Similarity between sample and founder
                similarity = 1.0 - 0.5 * (
                    abs(ref_freq - founder_ref) + abs(alt_freq - founder_alt)
                )

                founder_contributions[founder] += similarity * weight
                total_weight += weight / len(founders)

        # Normalize to sum to 1
        if total_weight > 0:
            total = sum(founder_contributions.values())
            if total > 0:
                return {f: v / total for f, v in founder_contributions.items()}

        return {f: 1.0 / len(founders) for f in founders}

    def _estimate_likelihood(
        self,
        genotypes: list,
        markers: list,
        founders: list[str],
    ) -> dict[str, float]:
        """Estimate proportions using maximum likelihood.

        Model: P(genotype | proportions) = sum_f(proportion_f * P(genotype | founder_f))

        Args:
            genotypes: List of non-missing genotypes
            markers: Corresponding marker information
            founders: List of founder names

        Returns:
            Dict mapping founders to proportion estimates
        """
        if not genotypes or not markers:
            return {f: 1.0 / len(founders) for f in founders}

        n_founders = len(founders)

        # Build likelihood matrix
        # log_likes[i, j] = log P(genotype_i | founder_j)
        n_markers = len(genotypes)
        log_likes = np.zeros((n_markers, n_founders))

        for i, (geno, marker) in enumerate(zip(genotypes, markers, strict=False)):
            if marker is None:
                continue

            for j, founder in enumerate(founders):
                founder_freqs = marker.founder_frequencies.get(founder, {})
                founder_ref = founder_freqs.get(marker.ref, 0.5)
                founder_alt = founder_freqs.get(marker.alt, 0.5)

                # Probability of observing sample genotype given founder
                # For diploid: P(genotype) = product over alleles
                prob = 1.0
                for allele in geno.alleles:
                    if allele == marker.ref:
                        prob *= max(founder_ref, 0.001)
                    elif allele == marker.alt:
                        prob *= max(founder_alt, 0.001)
                    else:
                        prob *= 0.001

                log_likes[i, j] = np.log(max(prob, 1e-10))

        # Sum log-likelihoods for each founder
        total_log_likes = np.sum(log_likes, axis=0)

        # Convert to probabilities (softmax)
        max_ll = np.max(total_log_likes)
        exp_likes = np.exp(total_log_likes - max_ll)
        proportions = exp_likes / np.sum(exp_likes)

        return {f: float(proportions[i]) for i, f in enumerate(founders)}

    def _estimate_bayesian(
        self,
        genotypes: list,
        markers: list,
        founders: list[str],
    ) -> dict[str, float]:
        """Estimate proportions using Bayesian approach.

        Uses Dirichlet prior and updates with observed genotypes.

        Args:
            genotypes: List of non-missing genotypes
            markers: Corresponding marker information
            founders: List of founder names

        Returns:
            Dict mapping founders to proportion estimates
        """
        if not genotypes or not markers:
            return {f: 1.0 / len(founders) for f in founders}

        n_founders = len(founders)

        # Dirichlet prior (uniform)
        alpha = np.ones(n_founders) * self.prior_weight

        # Update prior with evidence from each marker
        for geno, marker in zip(genotypes, markers, strict=False):
            if marker is None:
                continue

            # Calculate likelihood for each founder
            likelihoods = np.zeros(n_founders)

            for j, founder in enumerate(founders):
                founder_freqs = marker.founder_frequencies.get(founder, {})
                founder_ref = founder_freqs.get(marker.ref, 0.5)
                founder_alt = founder_freqs.get(marker.alt, 0.5)

                # Probability of observing sample genotype
                prob = 1.0
                for allele in geno.alleles:
                    if allele == marker.ref:
                        prob *= max(founder_ref, 0.001)
                    elif allele == marker.alt:
                        prob *= max(founder_alt, 0.001)

                likelihoods[j] = prob

            # Normalize likelihoods and update alpha
            if np.sum(likelihoods) > 0:
                normalized = likelihoods / np.sum(likelihoods)
                alpha += normalized * marker.confidence

        # Posterior mean of Dirichlet
        proportions = alpha / np.sum(alpha)

        return {f: float(proportions[i]) for i, f in enumerate(founders)}

    def estimate_at_position(
        self,
        sample_genotypes: SampleMarkerGenotypes,
        markers: DiagnosticMarkerSet,
        chrom: str,
        pos: int,
    ) -> dict[str, float]:
        """Estimate proportions at a specific position.

        Uses a window centered on the position.

        Args:
            sample_genotypes: Sample's marker genotypes
            markers: Diagnostic marker set
            chrom: Chromosome
            pos: Position

        Returns:
            Dict mapping founders to proportion estimates
        """
        founders = markers.founders
        half_window = self.window_size // 2

        # Get markers in window
        window_start = max(0, pos - half_window)
        window_end = pos + half_window

        marker_by_id = {m.variant_id: m for m in markers}

        window_genotypes = []
        window_markers = []

        for geno in sample_genotypes.get_chromosome_genotypes(chrom):
            if window_start <= geno.pos < window_end and not geno.is_missing:
                window_genotypes.append(geno)
                marker = marker_by_id.get(geno.variant_id)
                if marker is not None:
                    window_markers.append(marker)

        if len(window_genotypes) < self.min_markers:
            return {f: 1.0 / len(founders) for f in founders}

        if self.method == EstimationMethod.FREQUENCY:
            return self._estimate_frequency(window_genotypes, window_markers, founders)
        elif self.method == EstimationMethod.LIKELIHOOD:
            return self._estimate_likelihood(window_genotypes, window_markers, founders)
        else:
            return self._estimate_bayesian(window_genotypes, window_markers, founders)
