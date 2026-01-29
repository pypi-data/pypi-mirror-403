"""
Scaffold ordering engine.

Orders and orients contigs based on genetic map and haplotype continuity.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from haplophaser.assembly.paint import AssemblyPainting
    from haplophaser.io.assembly import Assembly
    from haplophaser.scaffold.contig_markers import ContigMarkerMap, ContigPlacement

logger = logging.getLogger(__name__)


@dataclass
class OrderedContig:
    """A contig in an ordered scaffold.

    Attributes:
        contig: Contig name.
        start: Start position in pseudomolecule (0-based).
        end: End position in pseudomolecule (0-based, exclusive).
        orientation: Orientation ('+' or '-').
        gap_before: Gap size before this contig (bp).
        confidence: Confidence in placement (0-1).
        evidence: Evidence source ('genetic_map', 'haplotype', 'both').
        genetic_start: Genetic map start position (cM).
        genetic_end: Genetic map end position (cM).
    """

    contig: str
    start: int
    end: int
    orientation: str
    gap_before: int = 0
    confidence: float = 1.0
    evidence: str = "genetic_map"
    genetic_start: float | None = None
    genetic_end: float | None = None

    @property
    def length(self) -> int:
        """Return contig length in pseudomolecule."""
        return self.end - self.start


@dataclass
class ScaffoldOrdering:
    """Ordering result for a single chromosome/scaffold.

    Attributes:
        chromosome: Chromosome name.
        ordered_contigs: List of ordered contigs.
        unplaced: List of unplaced contig names.
        total_placed_bp: Total bp in placed contigs.
        total_unplaced_bp: Total bp in unplaced contigs.
        total_gap_bp: Total bp in gaps.
        method: Method used for ordering.
        parameters: Parameters used.
    """

    chromosome: str
    ordered_contigs: list[OrderedContig] = field(default_factory=list)
    unplaced: list[str] = field(default_factory=list)
    total_placed_bp: int = 0
    total_unplaced_bp: int = 0
    total_gap_bp: int = 0
    method: str = "genetic_map"
    parameters: dict = field(default_factory=dict)

    @property
    def n_contigs(self) -> int:
        """Return number of placed contigs."""
        return len(self.ordered_contigs)

    @property
    def total_length(self) -> int:
        """Return total pseudomolecule length."""
        if not self.ordered_contigs:
            return 0
        return self.ordered_contigs[-1].end

    @property
    def n_gaps(self) -> int:
        """Return number of gaps."""
        return max(0, len(self.ordered_contigs) - 1)

    def to_agp(self, gap_type: str = "scaffold", linkage_evidence: str = "map") -> str:
        """Convert to AGP format string.

        Parameters
        ----------
        gap_type : str
            Gap type for AGP (default: 'scaffold').
        linkage_evidence : str
            Linkage evidence for AGP (default: 'map').

        Returns
        -------
        str
            AGP format string.
        """
        lines = []
        component_num = 0

        for i, oc in enumerate(self.ordered_contigs):
            # Add gap before contig (except for first)
            if i > 0 and oc.gap_before > 0:
                component_num += 1
                # AGP uses 1-based coordinates
                gap_start = self.ordered_contigs[i - 1].end + 1
                gap_end = oc.start
                lines.append(
                    f"{self.chromosome}\t{gap_start}\t{gap_end}\t{component_num}\t"
                    f"N\t{oc.gap_before}\t{gap_type}\tyes\t{linkage_evidence}"
                )

            # Add contig
            component_num += 1
            # AGP uses 1-based coordinates
            contig_len = oc.end - oc.start
            lines.append(
                f"{self.chromosome}\t{oc.start + 1}\t{oc.end}\t{component_num}\t"
                f"W\t{oc.contig}\t1\t{contig_len}\t{oc.orientation}"
            )

        return "\n".join(lines)

    def to_fasta(
        self,
        assembly: Assembly,
        gap_char: str = "N",
    ) -> tuple[str, str]:
        """Generate pseudomolecule FASTA sequence.

        Parameters
        ----------
        assembly : Assembly
            Source assembly with sequences.
        gap_char : str
            Character for gaps.

        Returns
        -------
        tuple[str, str]
            (header, sequence) tuple.
        """

        sequences = []

        for i, oc in enumerate(self.ordered_contigs):
            # Add gap before
            if i > 0 and oc.gap_before > 0:
                sequences.append(gap_char * oc.gap_before)

            # Get contig sequence
            contig = assembly.get_contig(oc.contig)
            if contig and contig.sequence:
                seq = contig.sequence
            else:
                # Placeholder if sequence not loaded
                seq = "N" * (oc.end - oc.start)

            # Reverse complement if negative orientation
            if oc.orientation == "-":
                seq = _reverse_complement(seq)

            sequences.append(seq)

        header = f">{self.chromosome}"
        sequence = "".join(sequences)

        return header, sequence

    def get_contig_position(self, contig: str) -> OrderedContig | None:
        """Get position of a contig in the ordering.

        Parameters
        ----------
        contig : str
            Contig name.

        Returns
        -------
        OrderedContig | None
            Ordered contig if found.
        """
        for oc in self.ordered_contigs:
            if oc.contig == contig:
                return oc
        return None


class ScaffoldOrderer:
    """Order contigs based on genetic map and haplotype continuity.

    Parameters
    ----------
    method : str
        Ordering method: 'genetic_map', 'haplotype', or 'combined'.
    min_markers : int
        Minimum markers to place a contig.
    max_conflict_rate : float
        Maximum marker conflict rate to tolerate.
    default_gap : int
        Default gap size when unknown.
    min_confidence : float
        Minimum confidence to include contig.
    """

    def __init__(
        self,
        method: str = "combined",
        min_markers: int = 3,
        max_conflict_rate: float = 0.1,
        default_gap: int = 100,
        min_confidence: float = 0.3,
    ) -> None:
        if method not in ("genetic_map", "haplotype", "combined"):
            raise ValueError(f"Unknown method: {method}")

        self.method = method
        self.min_markers = min_markers
        self.max_conflict_rate = max_conflict_rate
        self.default_gap = default_gap
        self.min_confidence = min_confidence

    def order(
        self,
        assembly: Assembly,
        contig_map: ContigMarkerMap,
        painting: AssemblyPainting | None = None,
        gap_estimates: dict[tuple[str, str], int] | None = None,
    ) -> dict[str, ScaffoldOrdering]:
        """Order contigs for all chromosomes.

        Parameters
        ----------
        assembly : Assembly
            Source assembly.
        contig_map : ContigMarkerMap
            Contig-to-genetic-map relationships.
        painting : AssemblyPainting | None
            Haplotype painting results (for haplotype/combined methods).
        gap_estimates : dict[tuple[str, str], int] | None
            Pre-computed gap estimates between contigs.

        Returns
        -------
        dict[str, ScaffoldOrdering]
            Orderings keyed by chromosome name.
        """
        logger.info(f"Ordering contigs using method: {self.method}")

        orderings = {}
        chromosomes = contig_map.chromosomes()

        for chrom in chromosomes:
            ordering = self._order_chromosome(
                chromosome=chrom,
                assembly=assembly,
                contig_map=contig_map,
                painting=painting,
                gap_estimates=gap_estimates,
            )
            orderings[chrom] = ordering

        # Collect unplaced contigs
        placed_contigs = set()
        for ordering in orderings.values():
            for oc in ordering.ordered_contigs:
                placed_contigs.add(oc.contig)

        all_contigs = set(assembly.contigs.keys())
        global_unplaced = all_contigs - placed_contigs

        total_placed = sum(o.n_contigs for o in orderings.values())
        total_unplaced = len(global_unplaced)

        logger.info(
            f"Ordered {total_placed} contigs across {len(orderings)} chromosomes "
            f"({total_unplaced} unplaced)"
        )

        return orderings

    def _order_chromosome(
        self,
        chromosome: str,
        assembly: Assembly,
        contig_map: ContigMarkerMap,
        painting: AssemblyPainting | None,
        gap_estimates: dict[tuple[str, str], int] | None,
    ) -> ScaffoldOrdering:
        """Order contigs for a single chromosome.

        Parameters
        ----------
        chromosome : str
            Chromosome name.
        assembly : Assembly
            Source assembly.
        contig_map : ContigMarkerMap
            Contig-to-genetic-map relationships.
        painting : AssemblyPainting | None
            Haplotype painting results.
        gap_estimates : dict[tuple[str, str], int] | None
            Gap estimates.

        Returns
        -------
        ScaffoldOrdering
            Ordering for this chromosome.
        """
        # Get placements for this chromosome
        placements = contig_map.placements_by_chromosome(chromosome)

        if not placements:
            return ScaffoldOrdering(
                chromosome=chromosome,
                method=self.method,
                parameters=self._get_parameters(),
            )

        # Filter by minimum confidence
        placements = [
            p for p in placements
            if p.confidence >= self.min_confidence and p.n_markers >= self.min_markers
        ]

        if not placements:
            return ScaffoldOrdering(
                chromosome=chromosome,
                method=self.method,
                parameters=self._get_parameters(),
            )

        # Order by genetic position
        if self.method in ("genetic_map", "combined"):
            ordered_placements = self._order_by_genetic_map(placements)
        else:
            # Haplotype-only method
            if painting is None:
                raise ValueError("Painting required for haplotype method")
            ordered_placements = self._order_by_haplotype(placements, painting)

        # Refine with haplotype continuity if combined method
        if self.method == "combined" and painting is not None:
            ordered_placements = self._refine_with_haplotype(
                ordered_placements, painting
            )

        # Build ordered contigs with positions
        ordered_contigs = []
        current_pos = 0

        for i, placement in enumerate(ordered_placements):
            contig = assembly.get_contig(placement.contig)
            if contig is None:
                continue

            # Determine gap before this contig
            gap_before = 0
            if i > 0:
                prev_contig = ordered_placements[i - 1].contig
                if gap_estimates and (prev_contig, placement.contig) in gap_estimates:
                    gap_before = gap_estimates[(prev_contig, placement.contig)]
                else:
                    gap_before = self.default_gap

                current_pos += gap_before

            # Determine orientation
            orientation = placement.orientation or "+"

            # Determine evidence
            if self.method == "genetic_map":
                evidence = "genetic_map"
            elif self.method == "haplotype":
                evidence = "haplotype"
            else:
                evidence = "both"

            ordered_contig = OrderedContig(
                contig=placement.contig,
                start=current_pos,
                end=current_pos + contig.length,
                orientation=orientation,
                gap_before=gap_before,
                confidence=placement.confidence,
                evidence=evidence,
                genetic_start=placement.genetic_start,
                genetic_end=placement.genetic_end,
            )
            ordered_contigs.append(ordered_contig)
            current_pos = ordered_contig.end

        # Calculate statistics
        total_placed_bp = sum(oc.length for oc in ordered_contigs)
        total_gap_bp = sum(oc.gap_before for oc in ordered_contigs)

        # Find unplaced contigs for this chromosome
        placed_names = {oc.contig for oc in ordered_contigs}
        all_placements = contig_map.placements_by_chromosome(chromosome)
        unplaced = [
            p.contig for p in all_placements
            if p.contig not in placed_names
        ]
        total_unplaced_bp = sum(
            assembly.contigs[name].length
            for name in unplaced
            if name in assembly.contigs
        )

        return ScaffoldOrdering(
            chromosome=chromosome,
            ordered_contigs=ordered_contigs,
            unplaced=unplaced,
            total_placed_bp=total_placed_bp,
            total_unplaced_bp=total_unplaced_bp,
            total_gap_bp=total_gap_bp,
            method=self.method,
            parameters=self._get_parameters(),
        )

    def _order_by_genetic_map(
        self, placements: list[ContigPlacement]
    ) -> list[ContigPlacement]:
        """Order placements by genetic map position.

        Parameters
        ----------
        placements : list[ContigPlacement]
            Placements to order.

        Returns
        -------
        list[ContigPlacement]
            Ordered placements.
        """
        # Sort by genetic start position
        return sorted(placements, key=lambda p: p.genetic_start or 0.0)

    def _order_by_haplotype(
        self,
        placements: list[ContigPlacement],
        painting: AssemblyPainting,
    ) -> list[ContigPlacement]:
        """Order placements by haplotype continuity.

        This is a greedy approach that tries to maximize haplotype continuity.

        Parameters
        ----------
        placements : list[ContigPlacement]
            Placements to order.
        painting : AssemblyPainting
            Haplotype painting results.

        Returns
        -------
        list[ContigPlacement]
            Ordered placements.
        """
        if not placements:
            return []

        # Start with first placement (by genetic position as tiebreaker)
        remaining = sorted(placements, key=lambda p: p.genetic_start or 0.0)
        ordered = [remaining.pop(0)]

        while remaining:
            current = ordered[-1]
            current_haplotype = self._get_contig_haplotype(current.contig, painting)

            # Find best next contig (same haplotype preferred)
            best_idx = 0
            best_score = -1

            for i, candidate in enumerate(remaining):
                candidate_haplotype = self._get_contig_haplotype(
                    candidate.contig, painting
                )
                score = 1.0 if candidate_haplotype == current_haplotype else 0.0

                # Use genetic position as tiebreaker
                if candidate.genetic_start is not None and current.genetic_end is not None:
                    genetic_dist = abs(candidate.genetic_start - current.genetic_end)
                    score += 0.1 / (1 + genetic_dist)

                if score > best_score:
                    best_score = score
                    best_idx = i

            ordered.append(remaining.pop(best_idx))

        return ordered

    def _refine_with_haplotype(
        self,
        placements: list[ContigPlacement],
        painting: AssemblyPainting,
    ) -> list[ContigPlacement]:
        """Refine genetic map ordering with haplotype continuity.

        Looks for local improvements by swapping adjacent contigs
        if it improves haplotype continuity.

        Parameters
        ----------
        placements : list[ContigPlacement]
            Initial ordering.
        painting : AssemblyPainting
            Haplotype painting results.

        Returns
        -------
        list[ContigPlacement]
            Refined ordering.
        """
        if len(placements) < 3:
            return placements

        result = list(placements)
        improved = True
        max_iterations = len(placements)
        iteration = 0

        while improved and iteration < max_iterations:
            improved = False
            iteration += 1

            for i in range(len(result) - 1):
                # Calculate current continuity score
                current_score = self._local_continuity_score(result, i, painting)

                # Try swapping
                result[i], result[i + 1] = result[i + 1], result[i]
                swapped_score = self._local_continuity_score(result, i, painting)

                # Keep swap if improved and doesn't violate genetic order too much
                genetic_violation = self._check_genetic_order_violation(result, i)

                if swapped_score > current_score and not genetic_violation:
                    improved = True
                else:
                    # Revert swap
                    result[i], result[i + 1] = result[i + 1], result[i]

        return result

    def _local_continuity_score(
        self,
        placements: list[ContigPlacement],
        index: int,
        painting: AssemblyPainting,
    ) -> float:
        """Calculate local haplotype continuity score.

        Parameters
        ----------
        placements : list[ContigPlacement]
            Current ordering.
        index : int
            Position to evaluate.
        painting : AssemblyPainting
            Haplotype painting results.

        Returns
        -------
        float
            Continuity score.
        """
        score = 0.0

        # Check continuity with previous
        if index > 0:
            prev_hap = self._get_contig_haplotype(placements[index - 1].contig, painting)
            curr_hap = self._get_contig_haplotype(placements[index].contig, painting)
            if prev_hap and curr_hap and prev_hap == curr_hap:
                score += 1.0

        # Check continuity with next
        if index < len(placements) - 1:
            curr_hap = self._get_contig_haplotype(placements[index].contig, painting)
            next_hap = self._get_contig_haplotype(placements[index + 1].contig, painting)
            if curr_hap and next_hap and curr_hap == next_hap:
                score += 1.0

        return score

    def _check_genetic_order_violation(
        self,
        placements: list[ContigPlacement],
        index: int,
    ) -> bool:
        """Check if genetic order is severely violated at index.

        Parameters
        ----------
        placements : list[ContigPlacement]
            Current ordering.
        index : int
            Position to check.

        Returns
        -------
        bool
            True if violation is too severe.
        """
        # Allow some genetic order violations for haplotype continuity
        # but not too much (e.g., >5 cM out of order)
        max_violation = 5.0  # cM

        if index > 0:
            prev_end = placements[index - 1].genetic_end
            curr_start = placements[index].genetic_start
            if prev_end is not None and curr_start is not None:
                if curr_start < prev_end - max_violation:
                    return True

        if index < len(placements) - 1:
            curr_end = placements[index].genetic_end
            next_start = placements[index + 1].genetic_start
            if curr_end is not None and next_start is not None:
                if next_start < curr_end - max_violation:
                    return True

        return False

    def _get_contig_haplotype(
        self, contig: str, painting: AssemblyPainting
    ) -> str | None:
        """Get assigned haplotype for a contig.

        Parameters
        ----------
        contig : str
            Contig name.
        painting : AssemblyPainting
            Haplotype painting results.

        Returns
        -------
        str | None
            Assigned founder/haplotype or None.
        """
        contig_painting = painting.get_contig(contig)
        if contig_painting:
            return contig_painting.assigned_founder
        return None

    def _get_parameters(self) -> dict:
        """Get parameters as dictionary.

        Returns
        -------
        dict
            Parameters.
        """
        return {
            "method": self.method,
            "min_markers": self.min_markers,
            "max_conflict_rate": self.max_conflict_rate,
            "default_gap": self.default_gap,
            "min_confidence": self.min_confidence,
        }


def _reverse_complement(seq: str) -> str:
    """Reverse complement a DNA sequence.

    Parameters
    ----------
    seq : str
        DNA sequence.

    Returns
    -------
    str
        Reverse complement.
    """
    complement = {"A": "T", "T": "A", "G": "C", "C": "G", "N": "N"}
    return "".join(complement.get(b.upper(), "N") for b in reversed(seq))


def order_contigs(
    assembly: Assembly,
    contig_map: ContigMarkerMap,
    painting: AssemblyPainting | None = None,
    method: str = "combined",
    min_markers: int = 3,
) -> dict[str, ScaffoldOrdering]:
    """Convenience function to order contigs.

    Parameters
    ----------
    assembly : Assembly
        Source assembly.
    contig_map : ContigMarkerMap
        Contig-to-genetic-map relationships.
    painting : AssemblyPainting | None
        Haplotype painting results.
    method : str
        Ordering method.
    min_markers : int
        Minimum markers for placement.

    Returns
    -------
    dict[str, ScaffoldOrdering]
        Orderings keyed by chromosome.
    """
    orderer = ScaffoldOrderer(method=method, min_markers=min_markers)
    return orderer.order(assembly, contig_map, painting)
