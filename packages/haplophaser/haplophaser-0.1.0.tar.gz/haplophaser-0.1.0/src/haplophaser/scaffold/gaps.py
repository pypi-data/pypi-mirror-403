"""
Gap size estimation.

Estimates gap sizes between ordered contigs based on genetic distance.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from haplophaser.core.genetic_map import GeneticMap
    from haplophaser.scaffold.contig_markers import ContigMarkerMap
    from haplophaser.scaffold.ordering import ScaffoldOrdering

logger = logging.getLogger(__name__)


@dataclass
class GapEstimate:
    """Gap size estimate between two contigs.

    Attributes:
        left_contig: Left contig name.
        right_contig: Right contig name.
        estimated_size: Estimated gap size in bp.
        confidence: Confidence in estimate (0-1).
        method: Method used for estimation.
        genetic_distance: Genetic distance in cM (if available).
        bp_per_cm: Physical/genetic ratio used.
    """

    left_contig: str
    right_contig: str
    estimated_size: int
    confidence: float = 0.5
    method: str = "fixed"
    genetic_distance: float | None = None
    bp_per_cm: float | None = None


class GapEstimator:
    """Estimate gap sizes between ordered contigs.

    Parameters
    ----------
    method : str
        Estimation method: 'genetic_distance', 'fixed', or 'local_rate'.
    bp_per_cm : float
        Default physical/genetic ratio (bp per cM).
    min_gap : int
        Minimum gap size (bp).
    max_gap : int
        Maximum gap size (bp).
    fixed_gap : int
        Gap size for 'fixed' method.
    """

    def __init__(
        self,
        method: str = "genetic_distance",
        bp_per_cm: float = 1_000_000,
        min_gap: int = 100,
        max_gap: int = 10_000_000,
        fixed_gap: int = 100,
    ) -> None:
        if method not in ("genetic_distance", "fixed", "local_rate"):
            raise ValueError(f"Unknown method: {method}")

        self.method = method
        self.bp_per_cm = bp_per_cm
        self.min_gap = min_gap
        self.max_gap = max_gap
        self.fixed_gap = fixed_gap

    def estimate(
        self,
        ordering: ScaffoldOrdering,
        genetic_map: GeneticMap | None = None,
        contig_map: ContigMarkerMap | None = None,
    ) -> dict[tuple[str, str], GapEstimate]:
        """Estimate gaps between all adjacent contigs.

        Parameters
        ----------
        ordering : ScaffoldOrdering
            Scaffold ordering.
        genetic_map : GeneticMap | None
            Genetic map (for genetic_distance method).
        contig_map : ContigMarkerMap | None
            Contig-marker map (for local_rate method).

        Returns
        -------
        dict[tuple[str, str], GapEstimate]
            Gap estimates keyed by (left_contig, right_contig).
        """
        gaps = {}
        contigs = ordering.ordered_contigs

        for i in range(len(contigs) - 1):
            left = contigs[i]
            right = contigs[i + 1]

            estimate = self._estimate_gap(
                left_contig=left.contig,
                right_contig=right.contig,
                left_genetic_end=left.genetic_end,
                right_genetic_start=right.genetic_start,
                chromosome=ordering.chromosome,
                genetic_map=genetic_map,
                contig_map=contig_map,
            )

            gaps[(left.contig, right.contig)] = estimate

        return gaps

    def _estimate_gap(
        self,
        left_contig: str,
        right_contig: str,
        left_genetic_end: float | None,
        right_genetic_start: float | None,
        chromosome: str,
        genetic_map: GeneticMap | None,
        contig_map: ContigMarkerMap | None,
    ) -> GapEstimate:
        """Estimate gap between two contigs.

        Parameters
        ----------
        left_contig : str
            Left contig name.
        right_contig : str
            Right contig name.
        left_genetic_end : float | None
            Genetic position at end of left contig.
        right_genetic_start : float | None
            Genetic position at start of right contig.
        chromosome : str
            Chromosome name.
        genetic_map : GeneticMap | None
            Genetic map.
        contig_map : ContigMarkerMap | None
            Contig-marker map.

        Returns
        -------
        GapEstimate
            Gap size estimate.
        """
        if self.method == "fixed":
            return GapEstimate(
                left_contig=left_contig,
                right_contig=right_contig,
                estimated_size=self.fixed_gap,
                confidence=0.3,
                method="fixed",
            )

        if self.method == "genetic_distance":
            return self._estimate_from_genetic_distance(
                left_contig=left_contig,
                right_contig=right_contig,
                left_genetic_end=left_genetic_end,
                right_genetic_start=right_genetic_start,
                chromosome=chromosome,
                genetic_map=genetic_map,
            )

        if self.method == "local_rate":
            return self._estimate_from_local_rate(
                left_contig=left_contig,
                right_contig=right_contig,
                left_genetic_end=left_genetic_end,
                right_genetic_start=right_genetic_start,
                chromosome=chromosome,
                genetic_map=genetic_map,
                contig_map=contig_map,
            )

        # Fallback to fixed
        return GapEstimate(
            left_contig=left_contig,
            right_contig=right_contig,
            estimated_size=self.fixed_gap,
            confidence=0.1,
            method="fallback",
        )

    def _estimate_from_genetic_distance(
        self,
        left_contig: str,
        right_contig: str,
        left_genetic_end: float | None,
        right_genetic_start: float | None,
        chromosome: str,
        genetic_map: GeneticMap | None,
    ) -> GapEstimate:
        """Estimate gap from genetic distance.

        Parameters
        ----------
        left_contig : str
            Left contig.
        right_contig : str
            Right contig.
        left_genetic_end : float | None
            Genetic end of left contig.
        right_genetic_start : float | None
            Genetic start of right contig.
        chromosome : str
            Chromosome name.
        genetic_map : GeneticMap | None
            Genetic map.

        Returns
        -------
        GapEstimate
            Gap estimate.
        """
        # If we have genetic positions, use them
        if left_genetic_end is not None and right_genetic_start is not None:
            genetic_distance = right_genetic_start - left_genetic_end

            # Negative distance means overlapping/misordered - use minimum
            if genetic_distance <= 0:
                return GapEstimate(
                    left_contig=left_contig,
                    right_contig=right_contig,
                    estimated_size=self.min_gap,
                    confidence=0.3,
                    method="genetic_distance",
                    genetic_distance=genetic_distance,
                    bp_per_cm=self.bp_per_cm,
                )

            # Get local bp/cM rate if genetic map available
            bp_per_cm = self.bp_per_cm
            if genetic_map:
                chrom_map = genetic_map.get_chromosome_map(chromosome)
                if chrom_map:
                    # Get average rate in this region
                    mid_genetic = (left_genetic_end + right_genetic_start) / 2
                    mid_physical = genetic_map.genetic_to_physical(chromosome, mid_genetic)
                    local_rate = chrom_map.get_rate_at(mid_physical)
                    if local_rate > 0:
                        bp_per_cm = 1_000_000 / local_rate  # Convert cM/Mb to bp/cM

            # Convert genetic distance to physical
            estimated_bp = int(genetic_distance * bp_per_cm)

            # Clamp to min/max
            estimated_bp = max(self.min_gap, min(estimated_bp, self.max_gap))

            # Confidence based on genetic distance (very small or very large = less confident)
            if genetic_distance < 0.01:
                confidence = 0.3
            elif genetic_distance > 10:
                confidence = 0.4
            else:
                confidence = 0.7

            return GapEstimate(
                left_contig=left_contig,
                right_contig=right_contig,
                estimated_size=estimated_bp,
                confidence=confidence,
                method="genetic_distance",
                genetic_distance=genetic_distance,
                bp_per_cm=bp_per_cm,
            )

        # Fall back to fixed if no genetic positions
        return GapEstimate(
            left_contig=left_contig,
            right_contig=right_contig,
            estimated_size=self.fixed_gap,
            confidence=0.2,
            method="genetic_distance_fallback",
        )

    def _estimate_from_local_rate(
        self,
        left_contig: str,
        right_contig: str,
        left_genetic_end: float | None,
        right_genetic_start: float | None,
        chromosome: str,
        genetic_map: GeneticMap | None,
        contig_map: ContigMarkerMap | None,
    ) -> GapEstimate:
        """Estimate gap using local recombination rate.

        Uses marker density on adjacent contigs to estimate local rate.

        Parameters
        ----------
        left_contig : str
            Left contig.
        right_contig : str
            Right contig.
        left_genetic_end : float | None
            Genetic end of left contig.
        right_genetic_start : float | None
            Genetic start of right contig.
        chromosome : str
            Chromosome name.
        genetic_map : GeneticMap | None
            Genetic map.
        contig_map : ContigMarkerMap | None
            Contig-marker map.

        Returns
        -------
        GapEstimate
            Gap estimate.
        """
        bp_per_cm = self.bp_per_cm

        # Try to calculate local rate from adjacent contigs
        if contig_map:
            left_placement = contig_map.get_placement(left_contig)
            right_placement = contig_map.get_placement(right_contig)

            local_rates = []

            if left_placement and left_placement.markers:
                rate = self._calculate_contig_rate(left_placement.markers)
                if rate:
                    local_rates.append(rate)

            if right_placement and right_placement.markers:
                rate = self._calculate_contig_rate(right_placement.markers)
                if rate:
                    local_rates.append(rate)

            if local_rates:
                avg_rate = sum(local_rates) / len(local_rates)
                if avg_rate > 0:
                    bp_per_cm = 1_000_000 / avg_rate  # Convert cM/Mb to bp/cM

        # Now use this rate with genetic distance
        if left_genetic_end is not None and right_genetic_start is not None:
            genetic_distance = max(0, right_genetic_start - left_genetic_end)
            estimated_bp = int(genetic_distance * bp_per_cm)
            estimated_bp = max(self.min_gap, min(estimated_bp, self.max_gap))

            return GapEstimate(
                left_contig=left_contig,
                right_contig=right_contig,
                estimated_size=estimated_bp,
                confidence=0.6,
                method="local_rate",
                genetic_distance=genetic_distance,
                bp_per_cm=bp_per_cm,
            )

        return GapEstimate(
            left_contig=left_contig,
            right_contig=right_contig,
            estimated_size=self.fixed_gap,
            confidence=0.2,
            method="local_rate_fallback",
        )

    def _calculate_contig_rate(self, markers: list) -> float | None:
        """Calculate recombination rate from markers on a contig.

        Parameters
        ----------
        markers : list[MappedMarker]
            Markers on contig.

        Returns
        -------
        float | None
            Rate in cM/Mb or None.
        """
        if len(markers) < 2:
            return None

        # Sort by physical position
        sorted_markers = sorted(markers, key=lambda m: m.pos_physical)

        physical_span = sorted_markers[-1].pos_physical - sorted_markers[0].pos_physical
        genetic_span = abs(sorted_markers[-1].pos_genetic - sorted_markers[0].pos_genetic)

        if physical_span < 1000:  # Less than 1kb span is unreliable
            return None

        # Rate in cM/Mb
        rate = genetic_span / (physical_span / 1_000_000)
        return rate


def estimate_gaps(
    ordering: ScaffoldOrdering,
    genetic_map: GeneticMap | None = None,
    contig_map: ContigMarkerMap | None = None,
    method: str = "genetic_distance",
    bp_per_cm: float = 1_000_000,
) -> dict[tuple[str, str], GapEstimate]:
    """Convenience function to estimate gaps.

    Parameters
    ----------
    ordering : ScaffoldOrdering
        Scaffold ordering.
    genetic_map : GeneticMap | None
        Genetic map.
    contig_map : ContigMarkerMap | None
        Contig-marker map.
    method : str
        Estimation method.
    bp_per_cm : float
        Default bp per cM.

    Returns
    -------
    dict[tuple[str, str], GapEstimate]
        Gap estimates.
    """
    estimator = GapEstimator(method=method, bp_per_cm=bp_per_cm)
    return estimator.estimate(ordering, genetic_map, contig_map)


def estimate_all_gaps(
    orderings: dict[str, ScaffoldOrdering],
    genetic_map: GeneticMap | None = None,
    contig_map: ContigMarkerMap | None = None,
    method: str = "genetic_distance",
) -> dict[tuple[str, str], GapEstimate]:
    """Estimate gaps for all orderings.

    Parameters
    ----------
    orderings : dict[str, ScaffoldOrdering]
        Orderings keyed by chromosome.
    genetic_map : GeneticMap | None
        Genetic map.
    contig_map : ContigMarkerMap | None
        Contig-marker map.
    method : str
        Estimation method.

    Returns
    -------
    dict[tuple[str, str], GapEstimate]
        All gap estimates.
    """
    estimator = GapEstimator(method=method)
    all_gaps = {}

    for ordering in orderings.values():
        gaps = estimator.estimate(ordering, genetic_map, contig_map)
        all_gaps.update(gaps)

    return all_gaps
