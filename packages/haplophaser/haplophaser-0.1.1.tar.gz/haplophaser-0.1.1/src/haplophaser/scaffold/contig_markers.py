"""
Contig-to-genetic-map relationships.

Maps contigs to genetic map positions based on marker hits.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
from scipy import stats

if TYPE_CHECKING:
    from haplophaser.assembly.mapping import MarkerHit
    from haplophaser.core.genetic_map import GeneticMap
    from haplophaser.io.assembly import Assembly

logger = logging.getLogger(__name__)


@dataclass
class MappedMarker:
    """A marker mapped to both genetic map and assembly.

    Attributes:
        marker_id: Marker identifier.
        chrom_genetic: Chromosome in genetic map.
        pos_genetic: Position in cM.
        contig: Contig in assembly.
        pos_physical: Position on contig (0-based).
        strand: Strand on contig ('+' or '-').
        inferred_founder: Founder inferred from marker allele.
    """

    marker_id: str
    chrom_genetic: str
    pos_genetic: float
    contig: str
    pos_physical: int
    strand: str
    inferred_founder: str | None = None


@dataclass
class ContigPlacement:
    """Genetic map placement for a contig.

    Attributes:
        contig: Contig name.
        chromosome: Assigned chromosome in genetic map.
        genetic_start: Start position in cM.
        genetic_end: End position in cM.
        orientation: Inferred orientation ('+', '-', or None).
        n_markers: Number of markers supporting placement.
        confidence: Confidence score (0-1).
        conflicts: List of markers suggesting different placement.
        markers: MappedMarker objects on this contig.
        marker_order_correlation: Spearman correlation of marker order.
    """

    contig: str
    chromosome: str | None = None
    genetic_start: float | None = None
    genetic_end: float | None = None
    orientation: str | None = None
    n_markers: int = 0
    confidence: float = 0.0
    conflicts: list[str] | None = None
    markers: list[MappedMarker] = field(default_factory=list)
    marker_order_correlation: float | None = None

    @property
    def is_placed(self) -> bool:
        """Return True if contig has a placement."""
        return self.chromosome is not None

    @property
    def genetic_span(self) -> float | None:
        """Return genetic span in cM."""
        if self.genetic_start is None or self.genetic_end is None:
            return None
        return abs(self.genetic_end - self.genetic_start)

    @property
    def genetic_midpoint(self) -> float | None:
        """Return midpoint position in cM."""
        if self.genetic_start is None or self.genetic_end is None:
            return None
        return (self.genetic_start + self.genetic_end) / 2

    @property
    def has_conflicts(self) -> bool:
        """Return True if placement has conflicts."""
        return self.conflicts is not None and len(self.conflicts) > 0


class ContigMarkerMap:
    """Build contig-to-genetic-map relationships.

    Parameters
    ----------
    assembly : Assembly
        Target assembly.
    marker_hits : list[MarkerHit]
        Marker hits on assembly.
    genetic_map : GeneticMap
        Genetic map with marker positions.
    min_markers : int
        Minimum markers for confident placement.
    max_conflict_rate : float
        Maximum fraction of markers with conflicting chromosome.
    orientation_min_markers : int
        Minimum markers for orientation inference.
    """

    def __init__(
        self,
        assembly: Assembly,
        marker_hits: list[MarkerHit],
        genetic_map: GeneticMap,
        min_markers: int = 3,
        max_conflict_rate: float = 0.1,
        orientation_min_markers: int = 2,
    ) -> None:
        self.assembly = assembly
        self.marker_hits = marker_hits
        self.genetic_map = genetic_map
        self.min_markers = min_markers
        self.max_conflict_rate = max_conflict_rate
        self.orientation_min_markers = orientation_min_markers

        # Build internal data structures
        self._placements: dict[str, ContigPlacement] = {}
        self._mapped_markers: dict[str, list[MappedMarker]] = {}
        self._build_mappings()

    def _build_mappings(self) -> None:
        """Build contig-to-marker mappings."""
        logger.info("Building contig-marker mappings")

        # Group markers by contig
        hits_by_contig: dict[str, list[MarkerHit]] = {}
        for hit in self.marker_hits:
            if hit.is_unique:
                if hit.contig not in hits_by_contig:
                    hits_by_contig[hit.contig] = []
                hits_by_contig[hit.contig].append(hit)

        # Build mapped markers for each contig
        for contig_name, hits in hits_by_contig.items():
            mapped = []
            for hit in hits:
                # Look up marker in genetic map
                if hit.marker_chrom is not None and hit.marker_pos is not None:
                    if self.genetic_map.has_chromosome(hit.marker_chrom):
                        genetic_pos = self.genetic_map.physical_to_genetic(
                            hit.marker_chrom, hit.marker_pos
                        )
                        mapped_marker = MappedMarker(
                            marker_id=hit.marker_id,
                            chrom_genetic=hit.marker_chrom,
                            pos_genetic=genetic_pos,
                            contig=contig_name,
                            pos_physical=hit.position,
                            strand=hit.strand,
                            inferred_founder=hit.inferred_founder(),
                        )
                        mapped.append(mapped_marker)

            self._mapped_markers[contig_name] = mapped

        # Build placements for each contig
        for contig_name in self.assembly.contigs:
            placement = self._compute_placement(contig_name)
            self._placements[contig_name] = placement

        n_placed = sum(1 for p in self._placements.values() if p.is_placed)
        logger.info(f"Placed {n_placed}/{len(self._placements)} contigs on genetic map")

    def _compute_placement(self, contig_name: str) -> ContigPlacement:
        """Compute genetic map placement for a contig.

        Parameters
        ----------
        contig_name : str
            Contig name.

        Returns
        -------
        ContigPlacement
            Computed placement.
        """
        markers = self._mapped_markers.get(contig_name, [])

        if not markers:
            return ContigPlacement(contig=contig_name, n_markers=0)

        # Count markers per chromosome
        chrom_counts: dict[str, int] = {}
        for marker in markers:
            chrom_counts[marker.chrom_genetic] = chrom_counts.get(marker.chrom_genetic, 0) + 1

        total_markers = len(markers)

        # Find majority chromosome
        majority_chrom = max(chrom_counts, key=chrom_counts.get)
        majority_count = chrom_counts[majority_chrom]
        conflict_count = total_markers - majority_count
        conflict_rate = conflict_count / total_markers if total_markers > 0 else 0.0

        # Check for conflicts
        conflicts = None
        if conflict_rate > self.max_conflict_rate:
            conflicts = [
                m.marker_id for m in markers if m.chrom_genetic != majority_chrom
            ]

        # Filter markers to majority chromosome
        chrom_markers = [m for m in markers if m.chrom_genetic == majority_chrom]

        if len(chrom_markers) < self.min_markers:
            return ContigPlacement(
                contig=contig_name,
                chromosome=majority_chrom if len(chrom_markers) > 0 else None,
                n_markers=len(chrom_markers),
                markers=chrom_markers,
                conflicts=conflicts,
                confidence=0.0,
            )

        # Compute genetic positions
        genetic_positions = [m.pos_genetic for m in chrom_markers]
        genetic_start = min(genetic_positions)
        genetic_end = max(genetic_positions)

        # Compute orientation from marker order correlation
        orientation, order_corr = self._infer_orientation(chrom_markers)

        # Compute confidence
        confidence = self._compute_confidence(
            n_markers=len(chrom_markers),
            conflict_rate=conflict_rate,
            order_corr=order_corr,
        )

        return ContigPlacement(
            contig=contig_name,
            chromosome=majority_chrom,
            genetic_start=genetic_start,
            genetic_end=genetic_end,
            orientation=orientation,
            n_markers=len(chrom_markers),
            confidence=confidence,
            conflicts=conflicts,
            markers=chrom_markers,
            marker_order_correlation=order_corr,
        )

    def _infer_orientation(
        self, markers: list[MappedMarker]
    ) -> tuple[str | None, float | None]:
        """Infer contig orientation from marker order.

        Parameters
        ----------
        markers : list[MappedMarker]
            Markers on contig (same chromosome).

        Returns
        -------
        tuple[str | None, float | None]
            (orientation, correlation) or (None, None) if insufficient data.
        """
        if len(markers) < self.orientation_min_markers:
            return None, None

        # Sort by physical position on contig
        sorted_markers = sorted(markers, key=lambda m: m.pos_physical)

        # Get physical and genetic positions
        physical_pos = [m.pos_physical for m in sorted_markers]
        genetic_pos = [m.pos_genetic for m in sorted_markers]

        # Compute Spearman correlation
        if len(set(physical_pos)) < 2 or len(set(genetic_pos)) < 2:
            return None, None

        corr, _ = stats.spearmanr(physical_pos, genetic_pos)

        if np.isnan(corr):
            return None, None

        # Determine orientation
        if corr > 0.5:
            orientation = "+"
        elif corr < -0.5:
            orientation = "-"
        else:
            orientation = None

        return orientation, corr

    def _compute_confidence(
        self,
        n_markers: int,
        conflict_rate: float,
        order_corr: float | None,
    ) -> float:
        """Compute placement confidence score.

        Parameters
        ----------
        n_markers : int
            Number of markers.
        conflict_rate : float
            Fraction of conflicting markers.
        order_corr : float | None
            Marker order correlation.

        Returns
        -------
        float
            Confidence score (0-1).
        """
        # Marker count component (logistic)
        count_score = 1 / (1 + np.exp(-(n_markers - self.min_markers) / 2))

        # Conflict component (penalize conflicts)
        conflict_score = 1.0 - conflict_rate

        # Order correlation component (if available)
        if order_corr is not None:
            order_score = abs(order_corr)
        else:
            order_score = 0.5  # Neutral if unknown

        # Weighted combination
        confidence = 0.4 * count_score + 0.3 * conflict_score + 0.3 * order_score

        return round(min(confidence, 1.0), 3)

    def get_placement(self, contig: str) -> ContigPlacement | None:
        """Get placement for a specific contig.

        Parameters
        ----------
        contig : str
            Contig name.

        Returns
        -------
        ContigPlacement | None
            Placement if contig exists.
        """
        return self._placements.get(contig)

    def all_placements(self) -> dict[str, ContigPlacement]:
        """Get all contig placements.

        Returns
        -------
        dict[str, ContigPlacement]
            All placements keyed by contig name.
        """
        return dict(self._placements)

    def placed_contigs(self) -> list[str]:
        """Get list of placed contig names.

        Returns
        -------
        list[str]
            Names of placed contigs.
        """
        return [name for name, p in self._placements.items() if p.is_placed]

    def unplaced_contigs(self) -> list[str]:
        """Get list of unplaced contig names.

        Returns
        -------
        list[str]
            Names of unplaced contigs.
        """
        return [name for name, p in self._placements.items() if not p.is_placed]

    def conflicting_contigs(self) -> list[str]:
        """Get list of contigs with conflicting markers.

        Returns
        -------
        list[str]
            Names of conflicting contigs.
        """
        return [name for name, p in self._placements.items() if p.has_conflicts]

    def placements_by_chromosome(self, chromosome: str) -> list[ContigPlacement]:
        """Get placements for a specific chromosome.

        Parameters
        ----------
        chromosome : str
            Chromosome name.

        Returns
        -------
        list[ContigPlacement]
            Placements assigned to chromosome, sorted by genetic position.
        """
        placements = [
            p for p in self._placements.values()
            if p.chromosome == chromosome and p.is_placed
        ]
        return sorted(placements, key=lambda p: p.genetic_start or 0.0)

    def get_markers(self, contig: str) -> list[MappedMarker]:
        """Get mapped markers for a contig.

        Parameters
        ----------
        contig : str
            Contig name.

        Returns
        -------
        list[MappedMarker]
            Markers mapped to contig.
        """
        return self._mapped_markers.get(contig, [])

    def chromosomes(self) -> list[str]:
        """Get list of chromosomes with placed contigs.

        Returns
        -------
        list[str]
            Chromosome names.
        """
        chroms = set()
        for p in self._placements.values():
            if p.chromosome:
                chroms.add(p.chromosome)
        return sorted(chroms)

    def summary(self) -> dict:
        """Generate summary statistics.

        Returns
        -------
        dict
            Summary statistics.
        """
        n_contigs = len(self._placements)
        n_placed = len(self.placed_contigs())
        n_unplaced = len(self.unplaced_contigs())
        n_conflicting = len(self.conflicting_contigs())

        # Calculate bp statistics
        placed_bp = sum(
            self.assembly.contigs[p.contig].length
            for p in self._placements.values()
            if p.is_placed and p.contig in self.assembly.contigs
        )
        total_bp = sum(c.length for c in self.assembly.contigs.values())

        # Per-chromosome stats
        by_chromosome: dict[str, dict] = {}
        for chrom in self.chromosomes():
            chrom_placements = self.placements_by_chromosome(chrom)
            by_chromosome[chrom] = {
                "n_contigs": len(chrom_placements),
                "total_bp": sum(
                    self.assembly.contigs[p.contig].length
                    for p in chrom_placements
                    if p.contig in self.assembly.contigs
                ),
                "genetic_span": max(p.genetic_end or 0 for p in chrom_placements)
                - min(p.genetic_start or 0 for p in chrom_placements)
                if chrom_placements
                else 0,
            }

        return {
            "n_contigs": n_contigs,
            "n_placed": n_placed,
            "n_unplaced": n_unplaced,
            "n_conflicting": n_conflicting,
            "placement_rate": n_placed / n_contigs if n_contigs > 0 else 0.0,
            "placed_bp": placed_bp,
            "total_bp": total_bp,
            "placed_bp_rate": placed_bp / total_bp if total_bp > 0 else 0.0,
            "n_chromosomes": len(self.chromosomes()),
            "by_chromosome": by_chromosome,
        }


def locate_markers(
    marker_hits: list[MarkerHit],
    genetic_map: GeneticMap,
) -> list[MappedMarker]:
    """Map marker hits to genetic positions.

    Parameters
    ----------
    marker_hits : list[MarkerHit]
        Marker hits on assembly.
    genetic_map : GeneticMap
        Genetic map with marker positions.

    Returns
    -------
    list[MappedMarker]
        Markers with genetic positions.
    """
    mapped = []
    for hit in marker_hits:
        if hit.marker_chrom is not None and hit.marker_pos is not None:
            if genetic_map.has_chromosome(hit.marker_chrom):
                genetic_pos = genetic_map.physical_to_genetic(
                    hit.marker_chrom, hit.marker_pos
                )
                mapped_marker = MappedMarker(
                    marker_id=hit.marker_id,
                    chrom_genetic=hit.marker_chrom,
                    pos_genetic=genetic_pos,
                    contig=hit.contig,
                    pos_physical=hit.position,
                    strand=hit.strand,
                    inferred_founder=hit.inferred_founder(),
                )
                mapped.append(mapped_marker)

    return mapped
