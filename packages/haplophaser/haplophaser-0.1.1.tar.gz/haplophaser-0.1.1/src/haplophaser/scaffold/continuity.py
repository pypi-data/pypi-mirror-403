"""
Haplotype continuity scoring.

Scores scaffold orderings by haplotype continuity at contig boundaries.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from haplophaser.assembly.paint import AssemblyPainting
    from haplophaser.scaffold.ordering import ScaffoldOrdering

logger = logging.getLogger(__name__)


@dataclass
class ProblematicJoin:
    """A problematic join between contigs.

    Attributes:
        left_contig: Left contig name.
        right_contig: Right contig name.
        left_haplotype: Haplotype at end of left contig.
        right_haplotype: Haplotype at start of right contig.
        confidence: Confidence that this is a real problem (0-1).
        position: Position in pseudomolecule.
    """

    left_contig: str
    right_contig: str
    left_haplotype: str | None
    right_haplotype: str | None
    confidence: float = 0.5
    position: int = 0

    @property
    def is_switch(self) -> bool:
        """Return True if this represents a haplotype switch."""
        return (
            self.left_haplotype is not None
            and self.right_haplotype is not None
            and self.left_haplotype != self.right_haplotype
        )


@dataclass
class ContinuityScore:
    """Haplotype continuity score for an ordering.

    Attributes:
        chromosome: Chromosome name.
        total_score: Overall continuity score.
        n_switches: Number of haplotype switches at boundaries.
        n_continuities: Number of maintained haplotypes at boundaries.
        n_unknown: Number of boundaries with unknown haplotypes.
        problematic_joins: List of problematic joins.
        switch_rate: Fraction of boundaries with switches.
    """

    chromosome: str
    total_score: float = 0.0
    n_switches: int = 0
    n_continuities: int = 0
    n_unknown: int = 0
    problematic_joins: list[ProblematicJoin] = field(default_factory=list)

    @property
    def n_boundaries(self) -> int:
        """Return total number of boundaries evaluated."""
        return self.n_switches + self.n_continuities + self.n_unknown

    @property
    def switch_rate(self) -> float:
        """Return fraction of boundaries with switches."""
        known = self.n_switches + self.n_continuities
        if known == 0:
            return 0.0
        return self.n_switches / known

    @property
    def continuity_rate(self) -> float:
        """Return fraction of boundaries with continuity."""
        known = self.n_switches + self.n_continuities
        if known == 0:
            return 0.0
        return self.n_continuities / known


class HaplotypeContinuityScorer:
    """Score orderings by haplotype continuity.

    Parameters
    ----------
    penalty_switch : float
        Penalty for haplotype switch at boundary.
    penalty_gap : float
        Penalty per marker gap.
    reward_continuity : float
        Reward for maintained haplotype at boundary.
    reward_unknown : float
        Score for unknown boundaries (neutral).
    use_end_markers : int
        Number of markers at contig ends to use for comparison.
    """

    def __init__(
        self,
        penalty_switch: float = 10.0,
        penalty_gap: float = 1.0,
        reward_continuity: float = 5.0,
        reward_unknown: float = 0.0,
        use_end_markers: int = 3,
    ) -> None:
        self.penalty_switch = penalty_switch
        self.penalty_gap = penalty_gap
        self.reward_continuity = reward_continuity
        self.reward_unknown = reward_unknown
        self.use_end_markers = use_end_markers

    def score(
        self,
        ordering: ScaffoldOrdering,
        painting: AssemblyPainting,
    ) -> ContinuityScore:
        """Score a single ordering.

        Parameters
        ----------
        ordering : ScaffoldOrdering
            Scaffold ordering to score.
        painting : AssemblyPainting
            Haplotype painting.

        Returns
        -------
        ContinuityScore
            Continuity score.
        """
        n_switches = 0
        n_continuities = 0
        n_unknown = 0
        total_score = 0.0
        problematic_joins = []

        contigs = ordering.ordered_contigs

        for i in range(len(contigs) - 1):
            left_contig = contigs[i]
            right_contig = contigs[i + 1]

            # Get haplotypes at boundary
            left_haplotype = self._get_boundary_haplotype(
                left_contig.contig,
                left_contig.orientation,
                "right",
                painting,
            )
            right_haplotype = self._get_boundary_haplotype(
                right_contig.contig,
                right_contig.orientation,
                "left",
                painting,
            )

            # Score this boundary
            if left_haplotype is None or right_haplotype is None:
                n_unknown += 1
                total_score += self.reward_unknown
            elif left_haplotype == right_haplotype:
                n_continuities += 1
                total_score += self.reward_continuity
            else:
                n_switches += 1
                total_score -= self.penalty_switch

                # Record problematic join
                join = ProblematicJoin(
                    left_contig=left_contig.contig,
                    right_contig=right_contig.contig,
                    left_haplotype=left_haplotype,
                    right_haplotype=right_haplotype,
                    confidence=0.8,  # Default confidence
                    position=left_contig.end,
                )
                problematic_joins.append(join)

        return ContinuityScore(
            chromosome=ordering.chromosome,
            total_score=total_score,
            n_switches=n_switches,
            n_continuities=n_continuities,
            n_unknown=n_unknown,
            problematic_joins=problematic_joins,
        )

    def _get_boundary_haplotype(
        self,
        contig: str,
        orientation: str,
        boundary: str,
        painting: AssemblyPainting,
    ) -> str | None:
        """Get haplotype at a contig boundary.

        Parameters
        ----------
        contig : str
            Contig name.
        orientation : str
            Contig orientation ('+' or '-').
        boundary : str
            Which boundary ('left' or 'right').
        painting : AssemblyPainting
            Haplotype painting.

        Returns
        -------
        str | None
            Haplotype at boundary or None.
        """
        contig_painting = painting.get_contig(contig)
        if not contig_painting:
            return None

        # If whole contig is assigned to one haplotype, use that
        if contig_painting.assigned_founder:
            return contig_painting.assigned_founder

        # Otherwise, look at markers near the boundary
        if not contig_painting.marker_positions:
            return None

        positions = contig_painting.marker_positions
        founders = contig_painting.marker_founders

        # Sort by position
        sorted_data = sorted(zip(positions, founders, strict=False), key=lambda x: x[0])

        # Determine which end to use
        # Note: orientation affects which physical end corresponds to which boundary
        if orientation == "+":
            if boundary == "left":
                end_data = sorted_data[: self.use_end_markers]
            else:
                end_data = sorted_data[-self.use_end_markers:]
        else:
            if boundary == "left":
                end_data = sorted_data[-self.use_end_markers:]
            else:
                end_data = sorted_data[: self.use_end_markers]

        if not end_data:
            return None

        # Get majority haplotype at boundary
        end_founders = [f for _, f in end_data if f != "unknown"]
        if not end_founders:
            return None

        return max(set(end_founders), key=end_founders.count)

    def compare_orderings(
        self,
        orderings: list[ScaffoldOrdering],
        painting: AssemblyPainting,
    ) -> list[ContinuityScore]:
        """Compare multiple orderings by continuity score.

        Parameters
        ----------
        orderings : list[ScaffoldOrdering]
            Orderings to compare.
        painting : AssemblyPainting
            Haplotype painting.

        Returns
        -------
        list[ContinuityScore]
            Scores for each ordering, in same order.
        """
        return [self.score(o, painting) for o in orderings]

    def select_best(
        self,
        orderings: list[ScaffoldOrdering],
        painting: AssemblyPainting,
    ) -> tuple[ScaffoldOrdering, ContinuityScore]:
        """Select best ordering by continuity score.

        Parameters
        ----------
        orderings : list[ScaffoldOrdering]
            Orderings to compare.
        painting : AssemblyPainting
            Haplotype painting.

        Returns
        -------
        tuple[ScaffoldOrdering, ContinuityScore]
            Best ordering and its score.
        """
        if not orderings:
            raise ValueError("No orderings to compare")

        scores = self.compare_orderings(orderings, painting)

        # Find best (highest total_score)
        best_idx = max(range(len(scores)), key=lambda i: scores[i].total_score)

        return orderings[best_idx], scores[best_idx]

    def score_all(
        self,
        orderings: dict[str, ScaffoldOrdering],
        painting: AssemblyPainting,
    ) -> dict[str, ContinuityScore]:
        """Score all orderings.

        Parameters
        ----------
        orderings : dict[str, ScaffoldOrdering]
            Orderings keyed by chromosome.
        painting : AssemblyPainting
            Haplotype painting.

        Returns
        -------
        dict[str, ContinuityScore]
            Scores keyed by chromosome.
        """
        return {chrom: self.score(ordering, painting) for chrom, ordering in orderings.items()}


def score_ordering(
    ordering: ScaffoldOrdering,
    painting: AssemblyPainting,
    penalty_switch: float = 10.0,
    reward_continuity: float = 5.0,
) -> ContinuityScore:
    """Convenience function to score an ordering.

    Parameters
    ----------
    ordering : ScaffoldOrdering
        Ordering to score.
    painting : AssemblyPainting
        Haplotype painting.
    penalty_switch : float
        Penalty for switches.
    reward_continuity : float
        Reward for continuity.

    Returns
    -------
    ContinuityScore
        Continuity score.
    """
    scorer = HaplotypeContinuityScorer(
        penalty_switch=penalty_switch,
        reward_continuity=reward_continuity,
    )
    return scorer.score(ordering, painting)


def find_problematic_joins(
    orderings: dict[str, ScaffoldOrdering],
    painting: AssemblyPainting,
) -> list[ProblematicJoin]:
    """Find all problematic joins across orderings.

    Parameters
    ----------
    orderings : dict[str, ScaffoldOrdering]
        Orderings keyed by chromosome.
    painting : AssemblyPainting
        Haplotype painting.

    Returns
    -------
    list[ProblematicJoin]
        All problematic joins.
    """
    scorer = HaplotypeContinuityScorer()
    all_joins = []

    for _chrom, ordering in orderings.items():
        score = scorer.score(ordering, painting)
        all_joins.extend(score.problematic_joins)

    return all_joins
