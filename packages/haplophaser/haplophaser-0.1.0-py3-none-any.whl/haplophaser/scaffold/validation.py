"""
Scaffold ordering validation and QC.

Validates scaffold orderings against genetic maps and haplotype data.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
from scipy import stats

if TYPE_CHECKING:
    from haplophaser.assembly.paint import AssemblyPainting
    from haplophaser.core.genetic_map import GeneticMap
    from haplophaser.scaffold.contig_markers import ContigMarkerMap
    from haplophaser.scaffold.ordering import ScaffoldOrdering

logger = logging.getLogger(__name__)


@dataclass
class Inversion:
    """A detected inversion in scaffold ordering.

    Attributes:
        contig: Contig with inversion.
        markers_involved: List of marker IDs involved.
        confidence: Confidence in inversion call (0-1).
        genetic_start: Genetic start of inverted region.
        genetic_end: Genetic end of inverted region.
        expected_orientation: Expected orientation.
        observed_orientation: Observed orientation.
    """

    contig: str
    markers_involved: list[str]
    confidence: float
    genetic_start: float | None = None
    genetic_end: float | None = None
    expected_orientation: str | None = None
    observed_orientation: str | None = None


@dataclass
class UnexpectedSwitch:
    """An unexpected haplotype switch at a contig boundary.

    Attributes:
        position: Position in pseudomolecule.
        left_contig: Left contig name.
        right_contig: Right contig name.
        possible_causes: List of possible causes.
        left_haplotype: Haplotype in left contig.
        right_haplotype: Haplotype in right contig.
    """

    position: int
    left_contig: str
    right_contig: str
    possible_causes: list[str] = field(default_factory=list)
    left_haplotype: str | None = None
    right_haplotype: str | None = None


@dataclass
class ValidationReport:
    """Validation report for a scaffold ordering.

    Attributes:
        chromosome: Chromosome name.
        marker_order_concordance: Spearman correlation of marker order.
        inversions_detected: List of detected inversions.
        haplotype_switches: Number of haplotype switches.
        expected_switches: Expected number of switches.
        unexpected_switches: List of unexpected switches.
        genetic_map_coverage: Fraction of genetic map covered.
        assembly_placed: Fraction of assembly bp placed.
        n_contigs: Number of contigs in ordering.
        n_markers: Total markers in ordering.
        warnings: List of warning messages.
        errors: List of error messages.
    """

    chromosome: str
    marker_order_concordance: float = 0.0
    inversions_detected: list[Inversion] = field(default_factory=list)
    haplotype_switches: int = 0
    expected_switches: int = 0
    unexpected_switches: list[UnexpectedSwitch] = field(default_factory=list)
    genetic_map_coverage: float = 0.0
    assembly_placed: float = 0.0
    n_contigs: int = 0
    n_markers: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Generate text summary of validation.

        Returns
        -------
        str
            Summary text.
        """
        lines = [
            f"Validation Report: {self.chromosome}",
            "=" * 50,
            f"Contigs: {self.n_contigs}",
            f"Markers: {self.n_markers}",
            f"Marker order concordance: {self.marker_order_concordance:.3f}",
            f"Genetic map coverage: {self.genetic_map_coverage:.1%}",
            f"Assembly placed: {self.assembly_placed:.1%}",
            f"Inversions detected: {len(self.inversions_detected)}",
            f"Haplotype switches: {self.haplotype_switches} (expected: {self.expected_switches})",
            f"Unexpected switches: {len(self.unexpected_switches)}",
        ]

        if self.warnings:
            lines.append("\nWarnings:")
            for w in self.warnings:
                lines.append(f"  - {w}")

        if self.errors:
            lines.append("\nErrors:")
            for e in self.errors:
                lines.append(f"  - {e}")

        return "\n".join(lines)

    def passes(self, thresholds: dict | None = None) -> bool:
        """Check if validation passes given thresholds.

        Parameters
        ----------
        thresholds : dict | None
            Validation thresholds. Default:
            - min_concordance: 0.8
            - max_unexpected_switch_rate: 0.2
            - min_coverage: 0.5

        Returns
        -------
        bool
            True if validation passes.
        """
        if thresholds is None:
            thresholds = {
                "min_concordance": 0.8,
                "max_unexpected_switch_rate": 0.2,
                "min_coverage": 0.5,
            }

        # Check concordance
        if self.marker_order_concordance < thresholds.get("min_concordance", 0.8):
            return False

        # Check unexpected switch rate
        if self.haplotype_switches > 0:
            unexpected_rate = len(self.unexpected_switches) / self.haplotype_switches
            if unexpected_rate > thresholds.get("max_unexpected_switch_rate", 0.2):
                return False

        # Check coverage
        if self.genetic_map_coverage < thresholds.get("min_coverage", 0.5):
            return False

        # Check for errors
        return not self.errors


class ScaffoldValidator:
    """Validate scaffold orderings.

    Parameters
    ----------
    check_marker_order : bool
        Check marker order concordance.
    check_inversions : bool
        Check for inversions.
    check_haplotype_continuity : bool
        Check haplotype continuity.
    min_markers_for_inversion : int
        Minimum markers to detect inversion.
    """

    def __init__(
        self,
        check_marker_order: bool = True,
        check_inversions: bool = True,
        check_haplotype_continuity: bool = True,
        min_markers_for_inversion: int = 3,
    ) -> None:
        self.check_marker_order = check_marker_order
        self.check_inversions = check_inversions
        self.check_haplotype_continuity = check_haplotype_continuity
        self.min_markers_for_inversion = min_markers_for_inversion

    def validate(
        self,
        ordering: ScaffoldOrdering,
        genetic_map: GeneticMap | None = None,
        contig_map: ContigMarkerMap | None = None,
        painting: AssemblyPainting | None = None,
        expected_breakpoints: list[float] | None = None,
    ) -> ValidationReport:
        """Validate a scaffold ordering.

        Parameters
        ----------
        ordering : ScaffoldOrdering
            Ordering to validate.
        genetic_map : GeneticMap | None
            Genetic map.
        contig_map : ContigMarkerMap | None
            Contig-marker map.
        painting : AssemblyPainting | None
            Haplotype painting.
        expected_breakpoints : list[float] | None
            Expected breakpoint positions in cM.

        Returns
        -------
        ValidationReport
            Validation report.
        """
        report = ValidationReport(
            chromosome=ordering.chromosome,
            n_contigs=ordering.n_contigs,
        )

        # Check marker order concordance
        if self.check_marker_order and contig_map:
            concordance, n_markers = self._check_marker_order(
                ordering, contig_map
            )
            report.marker_order_concordance = concordance
            report.n_markers = n_markers

        # Check for inversions
        if self.check_inversions and contig_map:
            inversions = self._detect_inversions(ordering, contig_map)
            report.inversions_detected = inversions
            if inversions:
                report.warnings.append(
                    f"Detected {len(inversions)} potential inversions"
                )

        # Check haplotype continuity
        if self.check_haplotype_continuity and painting:
            switches, unexpected = self._check_haplotype_continuity(
                ordering, painting, expected_breakpoints
            )
            report.haplotype_switches = switches
            report.unexpected_switches = unexpected
            report.expected_switches = len(expected_breakpoints) if expected_breakpoints else 0

            if len(unexpected) > 0:
                report.warnings.append(
                    f"{len(unexpected)} unexpected haplotype switches"
                )

        # Calculate coverage
        if genetic_map and contig_map:
            report.genetic_map_coverage = self._calculate_genetic_coverage(
                ordering, genetic_map, contig_map
            )

        # Calculate assembly placement rate
        report.assembly_placed = self._calculate_placement_rate(ordering)

        return report

    def _check_marker_order(
        self,
        ordering: ScaffoldOrdering,
        contig_map: ContigMarkerMap,
    ) -> tuple[float, int]:
        """Check marker order concordance.

        Parameters
        ----------
        ordering : ScaffoldOrdering
            Ordering to check.
        contig_map : ContigMarkerMap
            Contig-marker map.

        Returns
        -------
        tuple[float, int]
            (concordance, n_markers).
        """
        # Collect all markers in ordering with their positions
        scaffold_positions = []
        genetic_positions = []

        current_pos = 0
        for oc in ordering.ordered_contigs:
            markers = contig_map.get_markers(oc.contig)
            for marker in markers:
                # Calculate position in scaffold
                if oc.orientation == "+":
                    scaffold_pos = current_pos + marker.pos_physical
                else:
                    # For negative orientation, flip position within contig
                    contig_len = oc.end - oc.start
                    scaffold_pos = current_pos + (contig_len - marker.pos_physical)

                scaffold_positions.append(scaffold_pos)
                genetic_positions.append(marker.pos_genetic)

            current_pos = oc.end + oc.gap_before

        if len(scaffold_positions) < 2:
            return 0.0, len(scaffold_positions)

        # Calculate Spearman correlation
        try:
            corr, _ = stats.spearmanr(scaffold_positions, genetic_positions)
            if np.isnan(corr):
                return 0.0, len(scaffold_positions)
            return corr, len(scaffold_positions)
        except Exception:
            return 0.0, len(scaffold_positions)

    def _detect_inversions(
        self,
        ordering: ScaffoldOrdering,
        contig_map: ContigMarkerMap,
    ) -> list[Inversion]:
        """Detect inversions in contigs.

        Parameters
        ----------
        ordering : ScaffoldOrdering
            Ordering to check.
        contig_map : ContigMarkerMap
            Contig-marker map.

        Returns
        -------
        list[Inversion]
            Detected inversions.
        """
        inversions = []

        for oc in ordering.ordered_contigs:
            placement = contig_map.get_placement(oc.contig)
            if not placement or not placement.markers:
                continue

            if len(placement.markers) < self.min_markers_for_inversion:
                continue

            # Check marker order within contig
            sorted_markers = sorted(placement.markers, key=lambda m: m.pos_physical)

            physical_pos = [m.pos_physical for m in sorted_markers]
            genetic_pos = [m.pos_genetic for m in sorted_markers]

            try:
                corr, _ = stats.spearmanr(physical_pos, genetic_pos)
            except Exception:
                continue

            if np.isnan(corr):
                continue

            # Determine expected orientation based on ordering
            expected_orientation = oc.orientation

            # Check if marker order suggests different orientation
            if corr > 0.5:
                observed_orientation = "+"
            elif corr < -0.5:
                observed_orientation = "-"
            else:
                observed_orientation = "?"

            # Inversion if orientations don't match
            if observed_orientation != "?" and observed_orientation != expected_orientation:
                inversion = Inversion(
                    contig=oc.contig,
                    markers_involved=[m.marker_id for m in sorted_markers],
                    confidence=abs(corr),
                    genetic_start=placement.genetic_start,
                    genetic_end=placement.genetic_end,
                    expected_orientation=expected_orientation,
                    observed_orientation=observed_orientation,
                )
                inversions.append(inversion)

        return inversions

    def _check_haplotype_continuity(
        self,
        ordering: ScaffoldOrdering,
        painting: AssemblyPainting,
        expected_breakpoints: list[float] | None,
    ) -> tuple[int, list[UnexpectedSwitch]]:
        """Check haplotype continuity at contig boundaries.

        Parameters
        ----------
        ordering : ScaffoldOrdering
            Ordering to check.
        painting : AssemblyPainting
            Haplotype painting.
        expected_breakpoints : list[float] | None
            Expected breakpoint positions.

        Returns
        -------
        tuple[int, list[UnexpectedSwitch]]
            (total_switches, unexpected_switches).
        """
        total_switches = 0
        unexpected_switches = []
        contigs = ordering.ordered_contigs

        for i in range(len(contigs) - 1):
            left = contigs[i]
            right = contigs[i + 1]

            left_painting = painting.get_contig(left.contig)
            right_painting = painting.get_contig(right.contig)

            if not left_painting or not right_painting:
                continue

            left_haplotype = left_painting.assigned_founder
            right_haplotype = right_painting.assigned_founder

            if left_haplotype and right_haplotype and left_haplotype != right_haplotype:
                total_switches += 1

                # Check if this is at an expected breakpoint
                is_expected = False
                if expected_breakpoints:
                    boundary_genetic = left.genetic_end
                    if boundary_genetic is not None:
                        for bp in expected_breakpoints:
                            if abs(boundary_genetic - bp) < 1.0:  # Within 1 cM
                                is_expected = True
                                break

                if not is_expected:
                    causes = self._diagnose_switch_causes(
                        left, right, left_painting, right_painting
                    )
                    switch = UnexpectedSwitch(
                        position=left.end,
                        left_contig=left.contig,
                        right_contig=right.contig,
                        possible_causes=causes,
                        left_haplotype=left_haplotype,
                        right_haplotype=right_haplotype,
                    )
                    unexpected_switches.append(switch)

        return total_switches, unexpected_switches

    def _diagnose_switch_causes(
        self,
        left,
        right,
        left_painting,
        right_painting,
    ) -> list[str]:
        """Diagnose possible causes of unexpected haplotype switch.

        Parameters
        ----------
        left : OrderedContig
            Left contig.
        right : OrderedContig
            Right contig.
        left_painting : ContigPainting
            Left contig painting.
        right_painting : ContigPainting
            Right contig painting.

        Returns
        -------
        list[str]
            Possible causes.
        """
        causes = []

        # Low confidence assignments
        if left_painting.confidence < 0.5 or right_painting.confidence < 0.5:
            causes.append("low_confidence_assignment")

        # Few markers
        if left_painting.n_markers < 5 or right_painting.n_markers < 5:
            causes.append("few_markers")

        # Could be real breakpoint
        causes.append("real_breakpoint")

        # Could be misorder
        causes.append("misorder")

        # Could be misorientation
        causes.append("misorientation")

        # Could be chimeric contig
        if left_painting.is_chimeric or right_painting.is_chimeric:
            causes.append("chimera")

        return causes

    def _calculate_genetic_coverage(
        self,
        ordering: ScaffoldOrdering,
        genetic_map: GeneticMap,
        contig_map: ContigMarkerMap,
    ) -> float:
        """Calculate genetic map coverage.

        Parameters
        ----------
        ordering : ScaffoldOrdering
            Ordering.
        genetic_map : GeneticMap
            Genetic map.
        contig_map : ContigMarkerMap
            Contig-marker map.

        Returns
        -------
        float
            Coverage fraction (0-1).
        """
        chrom_map = genetic_map.get_chromosome_map(ordering.chromosome)
        if not chrom_map:
            return 0.0

        total_genetic_length = chrom_map.genetic_length

        if total_genetic_length == 0:
            return 0.0

        # Sum genetic spans of placed contigs
        covered = 0.0
        for oc in ordering.ordered_contigs:
            placement = contig_map.get_placement(oc.contig)
            if placement and placement.genetic_span:
                covered += placement.genetic_span

        return min(covered / total_genetic_length, 1.0)

    def _calculate_placement_rate(self, ordering: ScaffoldOrdering) -> float:
        """Calculate assembly placement rate.

        Parameters
        ----------
        ordering : ScaffoldOrdering
            Ordering.

        Returns
        -------
        float
            Placement rate (0-1).
        """
        total_bp = ordering.total_placed_bp + ordering.total_unplaced_bp
        if total_bp == 0:
            return 0.0
        return ordering.total_placed_bp / total_bp

    def validate_all(
        self,
        orderings: dict[str, ScaffoldOrdering],
        genetic_map: GeneticMap | None = None,
        contig_map: ContigMarkerMap | None = None,
        painting: AssemblyPainting | None = None,
    ) -> dict[str, ValidationReport]:
        """Validate all orderings.

        Parameters
        ----------
        orderings : dict[str, ScaffoldOrdering]
            Orderings keyed by chromosome.
        genetic_map : GeneticMap | None
            Genetic map.
        contig_map : ContigMarkerMap | None
            Contig-marker map.
        painting : AssemblyPainting | None
            Haplotype painting.

        Returns
        -------
        dict[str, ValidationReport]
            Reports keyed by chromosome.
        """
        return {
            chrom: self.validate(ordering, genetic_map, contig_map, painting)
            for chrom, ordering in orderings.items()
        }


def validate_ordering(
    ordering: ScaffoldOrdering,
    genetic_map: GeneticMap | None = None,
    contig_map: ContigMarkerMap | None = None,
    painting: AssemblyPainting | None = None,
) -> ValidationReport:
    """Convenience function to validate an ordering.

    Parameters
    ----------
    ordering : ScaffoldOrdering
        Ordering to validate.
    genetic_map : GeneticMap | None
        Genetic map.
    contig_map : ContigMarkerMap | None
        Contig-marker map.
    painting : AssemblyPainting | None
        Haplotype painting.

    Returns
    -------
    ValidationReport
        Validation report.
    """
    validator = ScaffoldValidator()
    return validator.validate(ordering, genetic_map, contig_map, painting)
