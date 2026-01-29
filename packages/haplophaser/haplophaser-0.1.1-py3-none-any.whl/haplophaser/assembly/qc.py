"""
Assembly QC for haplotype painting.

Generate quality control metrics for assembly-centric haplotype analysis.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from haplophaser.assembly.chimera import ChimeraReport
    from haplophaser.assembly.mapping import MarkerMappingResult
    from haplophaser.assembly.paint import AssemblyPainting
    from haplophaser.io.assembly import Assembly

logger = logging.getLogger(__name__)


@dataclass
class MarkerMappingQC:
    """QC metrics for marker mapping.

    Parameters
    ----------
    total_markers : int
        Total markers attempted.
    mapped_markers : int
        Markers that mapped.
    unique_markers : int
        Markers with unique mapping.
    multi_hit_markers : int
        Markers with multiple mappings.
    unmapped_markers : int
        Markers that didn't map.
    mapping_rate : float
        Fraction of markers that mapped.
    unique_rate : float
        Fraction with unique mapping.
    mean_identity : float
        Mean alignment identity.
    contigs_with_markers : int
        Number of contigs with at least one marker.
    marker_density_mean : float
        Mean marker density (markers/Mb).
    marker_density_median : float
        Median marker density.
    """

    total_markers: int = 0
    mapped_markers: int = 0
    unique_markers: int = 0
    multi_hit_markers: int = 0
    unmapped_markers: int = 0
    mapping_rate: float = 0.0
    unique_rate: float = 0.0
    mean_identity: float = 0.0
    contigs_with_markers: int = 0
    marker_density_mean: float = 0.0
    marker_density_median: float = 0.0


@dataclass
class PaintingQC:
    """QC metrics for contig painting.

    Parameters
    ----------
    total_contigs : int
        Total contigs.
    assigned_contigs : int
        Contigs assigned to a founder.
    unassigned_contigs : int
        Contigs not assigned.
    chimeric_contigs : int
        Contigs flagged as chimeric.
    assignment_rate_contigs : float
        Fraction of contigs assigned.
    assignment_rate_bp : float
        Fraction of bp assigned.
    assigned_bp : int
        Total bp assigned.
    unassigned_bp : int
        Total bp unassigned.
    chimeric_bp : int
        Total bp in chimeric contigs.
    mean_confidence : float
        Mean assignment confidence.
    low_confidence_contigs : int
        Contigs with low confidence assignment.
    by_founder : dict[str, dict]
        Per-founder statistics.
    """

    total_contigs: int = 0
    assigned_contigs: int = 0
    unassigned_contigs: int = 0
    chimeric_contigs: int = 0
    assignment_rate_contigs: float = 0.0
    assignment_rate_bp: float = 0.0
    assigned_bp: int = 0
    unassigned_bp: int = 0
    chimeric_bp: int = 0
    mean_confidence: float = 0.0
    low_confidence_contigs: int = 0
    by_founder: dict[str, dict] = field(default_factory=dict)


@dataclass
class ChimeraQC:
    """QC metrics for chimera detection.

    Parameters
    ----------
    contigs_analyzed : int
        Contigs with sufficient markers for analysis.
    chimeric_contigs : int
        Contigs with detected chimeras.
    total_switches : int
        Total switch points detected.
    chimera_rate : float
        Fraction of analyzed contigs that are chimeric.
    mean_switches_per_chimera : float
        Mean switches per chimeric contig.
    switches_by_founder_pair : dict[tuple[str, str], int]
        Switch counts by founder pair.
    """

    contigs_analyzed: int = 0
    chimeric_contigs: int = 0
    total_switches: int = 0
    chimera_rate: float = 0.0
    mean_switches_per_chimera: float = 0.0
    switches_by_founder_pair: dict[tuple[str, str], int] = field(default_factory=dict)


@dataclass
class AssemblyQCReport:
    """Complete QC report for assembly painting.

    Parameters
    ----------
    assembly_name : str
        Assembly name.
    assembly_stats : dict
        Basic assembly statistics.
    marker_mapping : MarkerMappingQC
        Marker mapping QC.
    painting : PaintingQC
        Painting QC.
    chimera : ChimeraQC | None
        Chimera detection QC.
    warnings : list[str]
        QC warnings.
    errors : list[str]
        QC errors.
    """

    assembly_name: str
    assembly_stats: dict = field(default_factory=dict)
    marker_mapping: MarkerMappingQC = field(default_factory=MarkerMappingQC)
    painting: PaintingQC = field(default_factory=PaintingQC)
    chimera: ChimeraQC | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def n_warnings(self) -> int:
        """Return number of warnings."""
        return len(self.warnings)

    @property
    def n_errors(self) -> int:
        """Return number of errors."""
        return len(self.errors)

    @property
    def passed(self) -> bool:
        """Return True if no errors."""
        return len(self.errors) == 0

    def summary_text(self) -> str:
        """Generate human-readable summary.

        Returns
        -------
        str
            Summary text.
        """
        lines = [
            f"Assembly QC Report: {self.assembly_name}",
            "=" * 60,
            "",
            "Assembly Statistics:",
            f"  Contigs: {self.assembly_stats.get('n_contigs', 'N/A'):,}",
            f"  Total size: {self.assembly_stats.get('total_size', 0):,} bp",
            f"  N50: {self.assembly_stats.get('n50', 0):,} bp",
            "",
            "Marker Mapping:",
            f"  Total markers: {self.marker_mapping.total_markers:,}",
            f"  Mapped: {self.marker_mapping.mapped_markers:,} ({self.marker_mapping.mapping_rate:.1%})",
            f"  Unique: {self.marker_mapping.unique_markers:,} ({self.marker_mapping.unique_rate:.1%})",
            f"  Mean identity: {self.marker_mapping.mean_identity:.3f}",
            f"  Contigs with markers: {self.marker_mapping.contigs_with_markers:,}",
            f"  Mean density: {self.marker_mapping.marker_density_mean:.1f} markers/Mb",
            "",
            "Contig Assignment:",
            f"  Assigned: {self.painting.assigned_contigs:,} / {self.painting.total_contigs:,} ({self.painting.assignment_rate_contigs:.1%})",
            f"  Assigned bp: {self.painting.assigned_bp:,} ({self.painting.assignment_rate_bp:.1%})",
            f"  Chimeric: {self.painting.chimeric_contigs:,}",
            f"  Mean confidence: {self.painting.mean_confidence:.3f}",
            "",
        ]

        if self.painting.by_founder:
            lines.append("Per-Founder Breakdown:")
            for founder, stats in sorted(self.painting.by_founder.items()):
                lines.append(
                    f"  {founder}: {stats['n_contigs']:,} contigs, "
                    f"{stats['total_bp']:,} bp"
                )
            lines.append("")

        if self.chimera:
            lines.extend([
                "Chimera Detection:",
                f"  Analyzed: {self.chimera.contigs_analyzed:,} contigs",
                f"  Chimeric: {self.chimera.chimeric_contigs:,} ({self.chimera.chimera_rate:.1%})",
                f"  Total switches: {self.chimera.total_switches:,}",
                "",
            ])

        if self.warnings:
            lines.append("Warnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
            lines.append("")

        if self.errors:
            lines.append("ERRORS:")
            for error in self.errors:
                lines.append(f"  - {error}")
            lines.append("")

        status = "PASSED" if self.passed else "FAILED"
        lines.append(f"Status: {status}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns
        -------
        dict
            Report as dictionary.
        """
        return {
            "assembly_name": self.assembly_name,
            "assembly_stats": self.assembly_stats,
            "marker_mapping": {
                "total_markers": self.marker_mapping.total_markers,
                "mapped_markers": self.marker_mapping.mapped_markers,
                "unique_markers": self.marker_mapping.unique_markers,
                "mapping_rate": self.marker_mapping.mapping_rate,
                "unique_rate": self.marker_mapping.unique_rate,
                "mean_identity": self.marker_mapping.mean_identity,
                "contigs_with_markers": self.marker_mapping.contigs_with_markers,
                "marker_density_mean": self.marker_mapping.marker_density_mean,
            },
            "painting": {
                "total_contigs": self.painting.total_contigs,
                "assigned_contigs": self.painting.assigned_contigs,
                "unassigned_contigs": self.painting.unassigned_contigs,
                "chimeric_contigs": self.painting.chimeric_contigs,
                "assignment_rate_contigs": self.painting.assignment_rate_contigs,
                "assignment_rate_bp": self.painting.assignment_rate_bp,
                "mean_confidence": self.painting.mean_confidence,
                "by_founder": self.painting.by_founder,
            },
            "chimera": {
                "contigs_analyzed": self.chimera.contigs_analyzed if self.chimera else 0,
                "chimeric_contigs": self.chimera.chimeric_contigs if self.chimera else 0,
                "total_switches": self.chimera.total_switches if self.chimera else 0,
                "chimera_rate": self.chimera.chimera_rate if self.chimera else 0.0,
            } if self.chimera else None,
            "warnings": self.warnings,
            "errors": self.errors,
            "passed": self.passed,
        }


class AssemblyQC:
    """Generate QC metrics for assembly haplotype painting.

    Parameters
    ----------
    assembly : Assembly
        Target assembly.
    painting : AssemblyPainting | None
        Painting results.
    chimeras : ChimeraReport | None
        Chimera detection results.
    marker_mapping : MarkerMappingResult | None
        Marker mapping results.
    low_confidence_threshold : float
        Threshold for low confidence warnings.
    low_marker_density_threshold : float
        Threshold for low marker density warnings (markers/Mb).
    """

    def __init__(
        self,
        assembly: Assembly,
        painting: AssemblyPainting | None = None,
        chimeras: ChimeraReport | None = None,
        marker_mapping: MarkerMappingResult | None = None,
        low_confidence_threshold: float = 0.7,
        low_marker_density_threshold: float = 1.0,
    ) -> None:
        self.assembly = assembly
        self.painting = painting
        self.chimeras = chimeras
        self.marker_mapping = marker_mapping
        self.low_confidence_threshold = low_confidence_threshold
        self.low_marker_density_threshold = low_marker_density_threshold

    def generate_report(self) -> AssemblyQCReport:
        """Generate QC report.

        Returns
        -------
        AssemblyQCReport
            Complete QC report.
        """
        logger.info(f"Generating QC report for {self.assembly.name}")

        report = AssemblyQCReport(assembly_name=self.assembly.name)

        # Assembly statistics
        report.assembly_stats = self.assembly.summary()

        # Marker mapping QC
        if self.marker_mapping:
            report.marker_mapping = self._analyze_marker_mapping()

        # Painting QC
        if self.painting:
            report.painting = self._analyze_painting()

        # Chimera QC
        if self.chimeras:
            report.chimera = self._analyze_chimeras()

        # Generate warnings and errors
        self._check_quality(report)

        return report

    def _analyze_marker_mapping(self) -> MarkerMappingQC:
        """Analyze marker mapping quality.

        Returns
        -------
        MarkerMappingQC
            Mapping QC metrics.
        """
        mm = self.marker_mapping

        # Calculate identities
        identities = [h.identity for h in mm.hits]
        mean_identity = np.mean(identities) if identities else 0.0

        # Calculate marker densities per contig
        contig_coverage = mm.contig_coverage()
        densities = []
        for contig_name, count in contig_coverage.items():
            contig = self.assembly.get_contig(contig_name)
            if contig and contig.length > 0:
                density = count * 1_000_000 / contig.length
                densities.append(density)

        return MarkerMappingQC(
            total_markers=mm.total_markers,
            mapped_markers=mm.mapped_unique + mm.mapped_multiple,
            unique_markers=mm.mapped_unique,
            multi_hit_markers=mm.mapped_multiple,
            unmapped_markers=mm.unmapped,
            mapping_rate=mm.mapping_rate,
            unique_rate=mm.unique_mapping_rate,
            mean_identity=mean_identity,
            contigs_with_markers=len(contig_coverage),
            marker_density_mean=np.mean(densities) if densities else 0.0,
            marker_density_median=np.median(densities) if densities else 0.0,
        )

    def _analyze_painting(self) -> PaintingQC:
        """Analyze painting quality.

        Returns
        -------
        PaintingQC
            Painting QC metrics.
        """
        p = self.painting

        # Calculate bp totals
        assigned_bp = sum(
            c.length for c in p.contigs.values() if c.is_assigned
        )
        unassigned_bp = sum(
            c.length for c in p.contigs.values() if not c.is_assigned
        )
        chimeric_bp = sum(
            c.length for c in p.contigs.values() if c.is_chimeric
        )
        total_bp = assigned_bp + unassigned_bp

        # Calculate mean confidence
        confidences = [
            c.confidence for c in p.contigs.values() if c.is_assigned
        ]
        mean_confidence = np.mean(confidences) if confidences else 0.0

        # Count low confidence assignments
        low_confidence = sum(
            1 for c in p.contigs.values()
            if c.is_assigned and c.confidence < self.low_confidence_threshold
        )

        # Per-founder breakdown
        by_founder: dict[str, dict] = {}
        for founder in p.founders:
            founder_contigs = [
                c for c in p.contigs.values() if c.assigned_founder == founder
            ]
            by_founder[founder] = {
                "n_contigs": len(founder_contigs),
                "total_bp": sum(c.length for c in founder_contigs),
                "n_markers": sum(c.n_markers for c in founder_contigs),
                "mean_confidence": (
                    np.mean([c.confidence for c in founder_contigs])
                    if founder_contigs else 0.0
                ),
            }

        return PaintingQC(
            total_contigs=p.n_contigs,
            assigned_contigs=p.n_assigned,
            unassigned_contigs=p.n_unassigned,
            chimeric_contigs=p.n_chimeric,
            assignment_rate_contigs=p.n_assigned / p.n_contigs if p.n_contigs > 0 else 0.0,
            assignment_rate_bp=assigned_bp / total_bp if total_bp > 0 else 0.0,
            assigned_bp=assigned_bp,
            unassigned_bp=unassigned_bp,
            chimeric_bp=chimeric_bp,
            mean_confidence=mean_confidence,
            low_confidence_contigs=low_confidence,
            by_founder=by_founder,
        )

    def _analyze_chimeras(self) -> ChimeraQC:
        """Analyze chimera detection results.

        Returns
        -------
        ChimeraQC
            Chimera QC metrics.
        """
        c = self.chimeras

        # Count switches by founder pair
        switches_by_pair: dict[tuple[str, str], int] = {}
        for switch in c.switches:
            pair = tuple(sorted([switch.left_founder, switch.right_founder]))
            switches_by_pair[pair] = switches_by_pair.get(pair, 0) + 1

        return ChimeraQC(
            contigs_analyzed=c.contigs_analyzed,
            chimeric_contigs=c.chimeric_contigs,
            total_switches=c.total_switches,
            chimera_rate=c.chimera_rate,
            mean_switches_per_chimera=(
                c.total_switches / c.chimeric_contigs
                if c.chimeric_contigs > 0 else 0.0
            ),
            switches_by_founder_pair=switches_by_pair,
        )

    def _check_quality(self, report: AssemblyQCReport) -> None:
        """Check for quality issues and add warnings/errors.

        Parameters
        ----------
        report : AssemblyQCReport
            Report to update.
        """
        # Marker mapping checks
        if report.marker_mapping.total_markers > 0:
            if report.marker_mapping.mapping_rate < 0.5:
                report.warnings.append(
                    f"Low marker mapping rate: {report.marker_mapping.mapping_rate:.1%}"
                )
            if report.marker_mapping.unique_rate < 0.5:
                report.warnings.append(
                    f"Low unique mapping rate: {report.marker_mapping.unique_rate:.1%}"
                )
            if report.marker_mapping.mean_identity < 0.9:
                report.warnings.append(
                    f"Low mean alignment identity: {report.marker_mapping.mean_identity:.3f}"
                )
            if report.marker_mapping.marker_density_mean < self.low_marker_density_threshold:
                report.warnings.append(
                    f"Low marker density: {report.marker_mapping.marker_density_mean:.1f} markers/Mb"
                )

        # Painting checks
        if report.painting.total_contigs > 0:
            if report.painting.assignment_rate_contigs < 0.5:
                report.warnings.append(
                    f"Low contig assignment rate: {report.painting.assignment_rate_contigs:.1%}"
                )
            if report.painting.assignment_rate_bp < 0.5:
                report.warnings.append(
                    f"Low bp assignment rate: {report.painting.assignment_rate_bp:.1%}"
                )
            if report.painting.low_confidence_contigs > report.painting.assigned_contigs * 0.2:
                report.warnings.append(
                    f"Many low-confidence assignments: {report.painting.low_confidence_contigs}"
                )

        # Chimera checks
        if report.chimera:
            if report.chimera.chimera_rate > 0.1:
                report.warnings.append(
                    f"High chimera rate: {report.chimera.chimera_rate:.1%}"
                )
            if report.chimera.total_switches > report.chimera.contigs_analyzed * 0.5:
                report.warnings.append(
                    f"Many chimeric switches detected: {report.chimera.total_switches}"
                )

        # Cross-checks
        if self.painting and self.marker_mapping:
            # Check for contigs without markers
            contigs_without_markers = (
                report.assembly_stats.get("n_contigs", 0) -
                report.marker_mapping.contigs_with_markers
            )
            if contigs_without_markers > report.assembly_stats.get("n_contigs", 0) * 0.3:
                report.warnings.append(
                    f"Many contigs without markers: {contigs_without_markers}"
                )

        # Balance check for founders
        if report.painting.by_founder:
            founder_bps = [
                stats.get("total_bp", 0)
                for stats in report.painting.by_founder.values()
            ]
            if founder_bps and max(founder_bps) > 0:
                imbalance = min(founder_bps) / max(founder_bps)
                if imbalance < 0.3:
                    report.warnings.append(
                        f"Imbalanced founder assignments: ratio {imbalance:.2f}"
                    )


def generate_assembly_qc_report(
    assembly: Assembly,
    painting: AssemblyPainting | None = None,
    chimeras: ChimeraReport | None = None,
    marker_mapping: MarkerMappingResult | None = None,
) -> AssemblyQCReport:
    """Convenience function to generate QC report.

    Parameters
    ----------
    assembly : Assembly
        Target assembly.
    painting : AssemblyPainting | None
        Painting results.
    chimeras : ChimeraReport | None
        Chimera detection results.
    marker_mapping : MarkerMappingResult | None
        Marker mapping results.

    Returns
    -------
    AssemblyQCReport
        QC report.
    """
    qc = AssemblyQC(
        assembly=assembly,
        painting=painting,
        chimeras=chimeras,
        marker_mapping=marker_mapping,
    )
    return qc.generate_report()
