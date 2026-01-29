"""
Contig haplotype painting.

Assigns haplotypes to contigs/scaffolds based on diagnostic marker evidence.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from haplophaser.assembly.chimera import ChimericRegion
    from haplophaser.assembly.mapping import MarkerHit, MarkerMappingResult
    from haplophaser.io.assembly import Assembly
    from haplophaser.markers.diagnostic import DiagnosticMarkerSet

logger = logging.getLogger(__name__)


@dataclass
class ContigPainting:
    """Haplotype assignment for a single contig.

    Parameters
    ----------
    contig : str
        Contig name.
    length : int
        Contig length in bp.
    n_markers : int
        Number of markers on contig.
    founder_proportions : dict[str, float]
        Proportion of markers supporting each founder.
    founder_counts : dict[str, int]
        Count of markers supporting each founder.
    assigned_founder : str | None
        Assigned founder haplotype (None if unassigned).
    confidence : float
        Confidence in assignment (0-1).
    is_chimeric : bool
        True if contig shows evidence of chimeric assembly.
    chimeric_regions : list[ChimericRegion] | None
        Details of chimeric regions if detected.
    marker_positions : list[int]
        Positions of markers on contig (0-based).
    marker_founders : list[str]
        Inferred founder for each marker position.
    """

    contig: str
    length: int
    n_markers: int
    founder_proportions: dict[str, float] = field(default_factory=dict)
    founder_counts: dict[str, int] = field(default_factory=dict)
    assigned_founder: str | None = None
    confidence: float = 0.0
    is_chimeric: bool = False
    chimeric_regions: list[ChimericRegion] | None = None
    marker_positions: list[int] = field(default_factory=list)
    marker_founders: list[str] = field(default_factory=list)

    @property
    def is_assigned(self) -> bool:
        """Return True if contig is assigned to a founder."""
        return self.assigned_founder is not None

    @property
    def marker_density(self) -> float:
        """Return markers per Mb."""
        if self.length == 0:
            return 0.0
        return self.n_markers * 1_000_000 / self.length

    @property
    def majority_founder(self) -> str | None:
        """Return founder with highest proportion."""
        if not self.founder_proportions:
            return None
        return max(self.founder_proportions, key=self.founder_proportions.get)

    @property
    def majority_proportion(self) -> float:
        """Return proportion of majority founder."""
        if not self.founder_proportions:
            return 0.0
        return max(self.founder_proportions.values())

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "contig": self.contig,
            "length": self.length,
            "n_markers": self.n_markers,
            "founder_proportions": self.founder_proportions,
            "founder_counts": self.founder_counts,
            "assigned_founder": self.assigned_founder,
            "confidence": self.confidence,
            "is_chimeric": self.is_chimeric,
            "marker_density": self.marker_density,
        }


@dataclass
class AssemblyPainting:
    """Haplotype painting for an entire assembly.

    Parameters
    ----------
    assembly : str
        Assembly name.
    founders : list[str]
        List of founder names.
    contigs : dict[str, ContigPainting]
        Painting results per contig.
    method : str
        Method used for painting.
    parameters : dict
        Parameters used for painting.
    """

    assembly: str
    founders: list[str]
    contigs: dict[str, ContigPainting] = field(default_factory=dict)
    method: str = "marker_proportion"
    parameters: dict = field(default_factory=dict)

    @property
    def n_contigs(self) -> int:
        """Return total number of contigs."""
        return len(self.contigs)

    @property
    def n_assigned(self) -> int:
        """Return number of assigned contigs."""
        return sum(1 for c in self.contigs.values() if c.is_assigned)

    @property
    def n_unassigned(self) -> int:
        """Return number of unassigned contigs."""
        return sum(1 for c in self.contigs.values() if not c.is_assigned)

    @property
    def n_chimeric(self) -> int:
        """Return number of chimeric contigs."""
        return sum(1 for c in self.contigs.values() if c.is_chimeric)

    @property
    def total_assigned_bp(self) -> int:
        """Return total bp assigned to any founder."""
        return sum(c.length for c in self.contigs.values() if c.is_assigned)

    @property
    def total_unassigned_bp(self) -> int:
        """Return total bp not assigned."""
        return sum(c.length for c in self.contigs.values() if not c.is_assigned)

    @property
    def total_chimeric_bp(self) -> int:
        """Return total bp in chimeric contigs."""
        return sum(c.length for c in self.contigs.values() if c.is_chimeric)

    def summary(self) -> dict:
        """Generate summary statistics.

        Returns
        -------
        dict
            Summary statistics.
        """
        total_bp = sum(c.length for c in self.contigs.values())
        total_markers = sum(c.n_markers for c in self.contigs.values())

        # Per-founder statistics
        by_founder: dict[str, dict] = {}
        for founder in self.founders:
            founder_contigs = [
                c for c in self.contigs.values()
                if c.assigned_founder == founder
            ]
            by_founder[founder] = {
                "n_contigs": len(founder_contigs),
                "total_bp": sum(c.length for c in founder_contigs),
                "n_markers": sum(c.n_markers for c in founder_contigs),
            }

        return {
            "assembly": self.assembly,
            "n_contigs": self.n_contigs,
            "n_assigned": self.n_assigned,
            "n_unassigned": self.n_unassigned,
            "n_chimeric": self.n_chimeric,
            "total_bp": total_bp,
            "total_assigned_bp": self.total_assigned_bp,
            "total_unassigned_bp": self.total_unassigned_bp,
            "total_chimeric_bp": self.total_chimeric_bp,
            "assignment_rate_contigs": self.n_assigned / self.n_contigs if self.n_contigs > 0 else 0.0,
            "assignment_rate_bp": self.total_assigned_bp / total_bp if total_bp > 0 else 0.0,
            "total_markers": total_markers,
            "by_founder": by_founder,
            "method": self.method,
        }

    def chimeric_contigs(self) -> list[str]:
        """Return list of chimeric contig names.

        Returns
        -------
        list[str]
            Names of chimeric contigs.
        """
        return [name for name, c in self.contigs.items() if c.is_chimeric]

    def by_founder(self, founder: str) -> list[str]:
        """Return contigs assigned to a specific founder.

        Parameters
        ----------
        founder : str
            Founder name.

        Returns
        -------
        list[str]
            Names of contigs assigned to founder.
        """
        return [
            name for name, c in self.contigs.items()
            if c.assigned_founder == founder
        ]

    def unassigned(self) -> list[str]:
        """Return list of unassigned contig names.

        Returns
        -------
        list[str]
            Names of unassigned contigs.
        """
        return [name for name, c in self.contigs.items() if not c.is_assigned]

    def get_contig(self, name: str) -> ContigPainting | None:
        """Get painting for a specific contig.

        Parameters
        ----------
        name : str
            Contig name.

        Returns
        -------
        ContigPainting | None
            Painting if found, None otherwise.
        """
        return self.contigs.get(name)

    def to_dataframe(self):
        """Convert to pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            Painting results as DataFrame.
        """
        import pandas as pd

        rows = []
        for name, painting in sorted(self.contigs.items()):
            row = {
                "contig": name,
                "length": painting.length,
                "n_markers": painting.n_markers,
                "assigned_founder": painting.assigned_founder or "unassigned",
                "confidence": painting.confidence,
                "is_chimeric": painting.is_chimeric,
                "marker_density": painting.marker_density,
            }
            # Add founder proportions
            for founder in self.founders:
                row[f"{founder}_proportion"] = painting.founder_proportions.get(founder, 0.0)
                row[f"{founder}_count"] = painting.founder_counts.get(founder, 0)
            rows.append(row)

        return pd.DataFrame(rows)


class ContigPainter:
    """Paint contigs with haplotype assignments based on marker evidence.

    Parameters
    ----------
    min_markers : int
        Minimum markers required for assignment.
    min_proportion : float
        Minimum proportion for confident assignment.
    detect_chimeras : bool
        Whether to run chimera detection.
    chimera_window_size : int
        Window size for chimera detection.
    chimera_min_markers_per_window : int
        Minimum markers per window for chimera detection.
    chimera_switch_threshold : float
        Proportion change to call a chimeric switch.
    """

    def __init__(
        self,
        min_markers: int = 5,
        min_proportion: float = 0.8,
        detect_chimeras: bool = True,
        chimera_window_size: int = 100_000,
        chimera_min_markers_per_window: int = 3,
        chimera_switch_threshold: float = 0.5,
    ) -> None:
        self.min_markers = min_markers
        self.min_proportion = min_proportion
        self.detect_chimeras = detect_chimeras
        self.chimera_window_size = chimera_window_size
        self.chimera_min_markers_per_window = chimera_min_markers_per_window
        self.chimera_switch_threshold = chimera_switch_threshold

    def paint(
        self,
        assembly: Assembly,
        marker_hits: MarkerMappingResult | list[MarkerHit],
        diagnostic_markers: DiagnosticMarkerSet | None = None,
    ) -> AssemblyPainting:
        """Paint assembly contigs with haplotype assignments.

        Parameters
        ----------
        assembly : Assembly
            Target assembly.
        marker_hits : MarkerMappingResult | list[MarkerHit]
            Marker hits on assembly.
        diagnostic_markers : DiagnosticMarkerSet | None
            Original diagnostic markers (for founder list).

        Returns
        -------
        AssemblyPainting
            Painting results.
        """
        from haplophaser.assembly.mapping import MarkerMappingResult

        logger.info(f"Painting {assembly.n_contigs} contigs with marker evidence")

        # Extract hits list
        if isinstance(marker_hits, MarkerMappingResult):
            hits = marker_hits.unique_hits()  # Only use uniquely mapped hits
        else:
            hits = [h for h in marker_hits if h.is_unique]

        # Get founder list
        if diagnostic_markers is not None:
            founders = diagnostic_markers.founders
        else:
            # Infer from hits
            all_founders: set[str] = set()
            for hit in hits:
                all_founders.update(hit.founder_alleles.keys())
            founders = sorted(all_founders)

        # Group hits by contig
        hits_by_contig: dict[str, list[MarkerHit]] = {}
        for hit in hits:
            if hit.contig not in hits_by_contig:
                hits_by_contig[hit.contig] = []
            hits_by_contig[hit.contig].append(hit)

        # Paint each contig
        contig_paintings: dict[str, ContigPainting] = {}

        for contig_name, contig in assembly.contigs.items():
            contig_hits = hits_by_contig.get(contig_name, [])
            painting = self._paint_contig(contig_name, contig.length, contig_hits, founders)
            contig_paintings[contig_name] = painting

        # Run chimera detection if enabled
        if self.detect_chimeras:
            from haplophaser.assembly.chimera import ChimeraDetector

            detector = ChimeraDetector(
                window_size=self.chimera_window_size,
                min_markers_per_window=self.chimera_min_markers_per_window,
                switch_threshold=self.chimera_switch_threshold,
            )

            for contig_name, painting in contig_paintings.items():
                if painting.n_markers >= self.chimera_min_markers_per_window * 2:
                    contig_hits = hits_by_contig.get(contig_name, [])
                    chimeras = detector.detect_in_contig(
                        contig_name,
                        assembly.contigs[contig_name].length,
                        contig_hits,
                        founders,
                    )
                    if chimeras:
                        painting.is_chimeric = True
                        painting.chimeric_regions = chimeras
                        # Don't assign chimeric contigs
                        painting.assigned_founder = None
                        painting.confidence = 0.0

        result = AssemblyPainting(
            assembly=assembly.name,
            founders=founders,
            contigs=contig_paintings,
            method="marker_proportion",
            parameters={
                "min_markers": self.min_markers,
                "min_proportion": self.min_proportion,
                "detect_chimeras": self.detect_chimeras,
            },
        )

        logger.info(
            f"Painted {result.n_assigned}/{result.n_contigs} contigs "
            f"({result.n_chimeric} chimeric, {result.n_unassigned} unassigned)"
        )

        return result

    def _paint_contig(
        self,
        contig_name: str,
        contig_length: int,
        hits: list[MarkerHit],
        founders: list[str],
    ) -> ContigPainting:
        """Paint a single contig.

        Parameters
        ----------
        contig_name : str
            Contig name.
        contig_length : int
            Contig length.
        hits : list[MarkerHit]
            Marker hits on contig.
        founders : list[str]
            List of founder names.

        Returns
        -------
        ContigPainting
            Painting result for contig.
        """
        n_markers = len(hits)

        # Count founder assignments from markers
        founder_counts: dict[str, int] = dict.fromkeys(founders, 0)
        marker_positions: list[int] = []
        marker_founders: list[str] = []

        for hit in sorted(hits, key=lambda h: h.position):
            inferred = hit.inferred_founder()
            marker_positions.append(hit.position)
            if inferred and inferred in founder_counts:
                founder_counts[inferred] += 1
                marker_founders.append(inferred)
            else:
                marker_founders.append("unknown")

        # Calculate proportions
        total_assigned = sum(founder_counts.values())
        founder_proportions: dict[str, float] = {}
        for founder in founders:
            if total_assigned > 0:
                founder_proportions[founder] = founder_counts[founder] / total_assigned
            else:
                founder_proportions[founder] = 0.0

        # Determine assignment
        assigned_founder: str | None = None
        confidence = 0.0

        if n_markers >= self.min_markers and total_assigned > 0:
            # Find majority founder
            majority_founder = max(founder_proportions, key=founder_proportions.get)
            majority_proportion = founder_proportions[majority_founder]

            if majority_proportion >= self.min_proportion:
                assigned_founder = majority_founder
                # Confidence based on proportion and sample size
                confidence = self._calculate_confidence(
                    majority_proportion, n_markers, total_assigned
                )

        return ContigPainting(
            contig=contig_name,
            length=contig_length,
            n_markers=n_markers,
            founder_proportions=founder_proportions,
            founder_counts=founder_counts,
            assigned_founder=assigned_founder,
            confidence=confidence,
            marker_positions=marker_positions,
            marker_founders=marker_founders,
        )

    def _calculate_confidence(
        self,
        proportion: float,
        n_markers: int,
        n_assigned: int,
    ) -> float:
        """Calculate confidence score for assignment.

        Parameters
        ----------
        proportion : float
            Proportion of markers supporting assignment.
        n_markers : int
            Total markers on contig.
        n_assigned : int
            Markers with founder assignment.

        Returns
        -------
        float
            Confidence score (0-1).
        """
        # Components:
        # 1. Proportion clarity (how dominant is the majority)
        proportion_score = min(proportion / self.min_proportion, 1.0)

        # 2. Sample size (more markers = more confidence)
        # Logistic function centered at min_markers
        size_score = 1 / (1 + np.exp(-(n_assigned - self.min_markers) / 2))

        # 3. Assignment rate (what fraction of markers had assignments)
        assignment_rate = n_assigned / n_markers if n_markers > 0 else 0.0

        # Weighted combination
        confidence = (
            0.5 * proportion_score +
            0.3 * size_score +
            0.2 * assignment_rate
        )

        return round(min(confidence, 1.0), 3)


def paint_assembly(
    assembly: Assembly,
    marker_hits: MarkerMappingResult | list[MarkerHit],
    diagnostic_markers: DiagnosticMarkerSet | None = None,
    min_markers: int = 5,
    min_proportion: float = 0.8,
    detect_chimeras: bool = True,
) -> AssemblyPainting:
    """Convenience function to paint an assembly.

    Parameters
    ----------
    assembly : Assembly
        Target assembly.
    marker_hits : MarkerMappingResult | list[MarkerHit]
        Marker hits on assembly.
    diagnostic_markers : DiagnosticMarkerSet | None
        Original diagnostic markers.
    min_markers : int
        Minimum markers for assignment.
    min_proportion : float
        Minimum proportion for assignment.
    detect_chimeras : bool
        Whether to detect chimeras.

    Returns
    -------
    AssemblyPainting
        Painting results.
    """
    painter = ContigPainter(
        min_markers=min_markers,
        min_proportion=min_proportion,
        detect_chimeras=detect_chimeras,
    )
    return painter.paint(assembly, marker_hits, diagnostic_markers)
