"""
Marker quality assessment.

This module provides tools for assessing the quality and coverage
of diagnostic marker sets, including density analysis, gap detection,
and founder pair coverage.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from haplophaser.markers.diagnostic import (
    DiagnosticMarker,
    DiagnosticMarkerSet,
    MarkerClassification,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class MarkerDensity:
    """Marker density information for a genomic region.

    Parameters
    ----------
    chrom : str
        Chromosome.
    start : int
        0-based start position.
    end : int
        0-based end position (exclusive).
    total_markers : int
        Total number of markers in region.
    fully_diagnostic : int
        Number of fully diagnostic markers.
    partially_diagnostic : int
        Number of partially diagnostic markers.
    informative : int
        Number of informative markers.
    markers_per_mb : float
        Marker density (markers per megabase).
    """

    chrom: str
    start: int
    end: int
    total_markers: int
    fully_diagnostic: int
    partially_diagnostic: int
    informative: int
    markers_per_mb: float

    @property
    def length(self) -> int:
        """Return region length in bp."""
        return self.end - self.start

    @property
    def diagnostic_markers(self) -> int:
        """Return total diagnostic markers (full + partial)."""
        return self.fully_diagnostic + self.partially_diagnostic


@dataclass
class MarkerGap:
    """A region lacking diagnostic markers.

    Parameters
    ----------
    chrom : str
        Chromosome.
    start : int
        0-based start position.
    end : int
        0-based end position (exclusive).
    length : int
        Gap length in bp.
    flanking_markers : tuple[DiagnosticMarker | None, DiagnosticMarker | None]
        Markers flanking the gap (left, right).
    """

    chrom: str
    start: int
    end: int
    length: int
    flanking_markers: tuple[DiagnosticMarker | None, DiagnosticMarker | None] = field(
        default_factory=lambda: (None, None)
    )

    def to_bed_fields(self) -> tuple[str, int, int, str, int, str]:
        """Convert to BED6 format fields."""
        name = f"gap_{self.length // 1000}kb"
        score = 0
        return (self.chrom, self.start, self.end, name, score, ".")


@dataclass
class FounderPairCoverage:
    """Marker coverage for a founder pair.

    Parameters
    ----------
    founder1 : str
        First founder.
    founder2 : str
        Second founder.
    n_markers : int
        Number of markers distinguishing this pair.
    n_fully_diagnostic : int
        Number of fully diagnostic markers.
    chroms_covered : list[str]
        Chromosomes with markers for this pair.
    avg_density : float
        Average markers per Mb across covered chromosomes.
    """

    founder1: str
    founder2: str
    n_markers: int
    n_fully_diagnostic: int
    chroms_covered: list[str]
    avg_density: float

    @property
    def pair(self) -> tuple[str, str]:
        """Return founder pair."""
        return (self.founder1, self.founder2)


@dataclass
class ChromosomeSummary:
    """Summary statistics for a chromosome.

    Parameters
    ----------
    chrom : str
        Chromosome name.
    n_markers : int
        Total markers.
    n_fully_diagnostic : int
        Fully diagnostic markers.
    n_partially_diagnostic : int
        Partially diagnostic markers.
    span : int
        Span from first to last marker (bp).
    density : float
        Markers per Mb.
    n_gaps : int
        Number of gaps exceeding threshold.
    largest_gap : int
        Size of largest gap (bp).
    """

    chrom: str
    n_markers: int
    n_fully_diagnostic: int
    n_partially_diagnostic: int
    span: int
    density: float
    n_gaps: int
    largest_gap: int


@dataclass
class GenomeInfo:
    """Genome information for coverage calculations.

    Parameters
    ----------
    chrom_sizes : dict[str, int]
        Chromosome sizes in bp.
    """

    chrom_sizes: dict[str, int] = field(default_factory=dict)

    def get_size(self, chrom: str) -> int | None:
        """Get size of a chromosome."""
        return self.chrom_sizes.get(chrom)

    def total_size(self) -> int:
        """Get total genome size."""
        return sum(self.chrom_sizes.values())

    @classmethod
    def from_vcf_stats(cls, stats: dict[str, int]) -> GenomeInfo:
        """Create from VCF chromosome stats (variant positions)."""
        # Estimate sizes from max variant positions (rough approximation)
        return cls(chrom_sizes=stats)


class MarkerQualityAssessment:
    """Assess quality and coverage of a marker set.

    Parameters
    ----------
    markers : DiagnosticMarkerSet
        Set of diagnostic markers to assess.
    genome_info : GenomeInfo, optional
        Genome information for coverage calculations.
    gap_threshold : int
        Minimum size (bp) for a region to be considered a gap.
    window_size : int
        Window size for density calculations.
    """

    def __init__(
        self,
        markers: DiagnosticMarkerSet,
        genome_info: GenomeInfo | None = None,
        gap_threshold: int = 500_000,
        window_size: int = 1_000_000,
    ) -> None:
        self.markers = markers
        self.genome_info = genome_info or GenomeInfo()
        self.gap_threshold = gap_threshold
        self.window_size = window_size

        # Organize markers by chromosome
        self._by_chrom: dict[str, list[DiagnosticMarker]] = defaultdict(list)
        for m in markers:
            self._by_chrom[m.chrom].append(m)

        # Sort by position
        for chrom in self._by_chrom:
            self._by_chrom[chrom].sort(key=lambda m: m.pos)

    @property
    def total_markers(self) -> int:
        """Return total number of markers."""
        return len(self.markers)

    @property
    def n_fully_diagnostic(self) -> int:
        """Return number of fully diagnostic markers."""
        return len(self.markers.fully_diagnostic)

    @property
    def n_partially_diagnostic(self) -> int:
        """Return number of partially diagnostic markers."""
        return len(self.markers.partially_diagnostic)

    @property
    def n_informative(self) -> int:
        """Return number of informative markers."""
        return len(self.markers.informative)

    @property
    def chromosomes(self) -> list[str]:
        """Return sorted list of chromosomes with markers."""
        return sorted(self._by_chrom.keys())

    def chromosome_summary(self, chrom: str) -> ChromosomeSummary | None:
        """Get summary statistics for a chromosome.

        Parameters
        ----------
        chrom : str
            Chromosome name.

        Returns
        -------
        ChromosomeSummary or None
            Summary statistics, or None if no markers on chromosome.
        """
        markers = self._by_chrom.get(chrom, [])
        if not markers:
            return None

        n_full = sum(1 for m in markers if m.is_fully_diagnostic)
        n_partial = sum(
            1 for m in markers
            if m.classification == MarkerClassification.PARTIALLY_DIAGNOSTIC
        )

        positions = [m.pos for m in markers]
        span = max(positions) - min(positions) + 1

        density = len(markers) / (span / 1_000_000) if span > 0 else 0

        gaps = self.find_gaps(chrom)

        return ChromosomeSummary(
            chrom=chrom,
            n_markers=len(markers),
            n_fully_diagnostic=n_full,
            n_partially_diagnostic=n_partial,
            span=span,
            density=round(density, 2),
            n_gaps=len(gaps),
            largest_gap=max((g.length for g in gaps), default=0),
        )

    def density_by_window(
        self,
        chrom: str | None = None,
        window_size: int | None = None,
    ) -> list[MarkerDensity]:
        """Calculate marker density in genomic windows.

        Parameters
        ----------
        chrom : str, optional
            Restrict to specific chromosome.
        window_size : int, optional
            Window size in bp. Uses default if not specified.

        Returns
        -------
        list[MarkerDensity]
            Density information per window.
        """
        window_size = window_size or self.window_size
        result = []

        chroms = [chrom] if chrom else self.chromosomes

        for c in chroms:
            markers = self._by_chrom.get(c, [])
            if not markers:
                continue

            # Find range
            max_pos = max(m.pos for m in markers)
            chrom_size = self.genome_info.get_size(c) or (max_pos + window_size)

            # Process windows
            for start in range(0, chrom_size, window_size):
                end = min(start + window_size, chrom_size)

                # Count markers in window
                window_markers = [
                    m for m in markers
                    if start <= m.pos < end
                ]

                total = len(window_markers)
                n_full = sum(1 for m in window_markers if m.is_fully_diagnostic)
                n_partial = sum(
                    1 for m in window_markers
                    if m.classification == MarkerClassification.PARTIALLY_DIAGNOSTIC
                )
                n_info = sum(
                    1 for m in window_markers
                    if m.classification == MarkerClassification.INFORMATIVE
                )

                length_mb = (end - start) / 1_000_000
                density = total / length_mb if length_mb > 0 else 0

                result.append(MarkerDensity(
                    chrom=c,
                    start=start,
                    end=end,
                    total_markers=total,
                    fully_diagnostic=n_full,
                    partially_diagnostic=n_partial,
                    informative=n_info,
                    markers_per_mb=round(density, 2),
                ))

        return result

    def find_gaps(
        self,
        chrom: str | None = None,
        threshold: int | None = None,
    ) -> list[MarkerGap]:
        """Find regions lacking diagnostic markers.

        Parameters
        ----------
        chrom : str, optional
            Restrict to specific chromosome.
        threshold : int, optional
            Minimum gap size in bp. Uses default if not specified.

        Returns
        -------
        list[MarkerGap]
            List of gaps.
        """
        threshold = threshold or self.gap_threshold
        result = []

        chroms = [chrom] if chrom else self.chromosomes

        for c in chroms:
            markers = self._by_chrom.get(c, [])
            if len(markers) < 2:
                continue

            # Check consecutive markers
            for i in range(len(markers) - 1):
                m1 = markers[i]
                m2 = markers[i + 1]

                gap_size = m2.pos - m1.pos

                if gap_size >= threshold:
                    result.append(MarkerGap(
                        chrom=c,
                        start=m1.pos,
                        end=m2.pos,
                        length=gap_size,
                        flanking_markers=(m1, m2),
                    ))

        return sorted(result, key=lambda g: -g.length)

    def founder_pair_coverage(self) -> list[FounderPairCoverage]:
        """Calculate marker coverage for each founder pair.

        Returns
        -------
        list[FounderPairCoverage]
            Coverage information per founder pair.
        """
        # Group markers by founder pair
        pair_markers: dict[tuple[str, str], list[DiagnosticMarker]] = defaultdict(list)

        for m in self.markers:
            if m.distinguishes:
                pair = tuple(sorted(m.distinguishes))
                pair_markers[pair].append(m)

        result = []

        for pair, markers in pair_markers.items():
            f1, f2 = pair

            n_full = sum(1 for m in markers if m.is_fully_diagnostic)

            chroms = sorted({m.chrom for m in markers})

            # Calculate average density
            total_density = 0
            for c in chroms:
                chrom_markers = [m for m in markers if m.chrom == c]
                if len(chrom_markers) >= 2:
                    positions = [m.pos for m in chrom_markers]
                    span = max(positions) - min(positions) + 1
                    density = len(chrom_markers) / (span / 1_000_000)
                    total_density += density

            avg_density = total_density / len(chroms) if chroms else 0

            result.append(FounderPairCoverage(
                founder1=f1,
                founder2=f2,
                n_markers=len(markers),
                n_fully_diagnostic=n_full,
                chroms_covered=chroms,
                avg_density=round(avg_density, 2),
            ))

        return sorted(result, key=lambda c: c.pair)

    def distinguishability_matrix(self) -> dict[tuple[str, str], int]:
        """Create a matrix of pairwise marker counts.

        Returns
        -------
        dict[tuple[str, str], int]
            Mapping of founder pairs to marker counts.
        """
        matrix: dict[tuple[str, str], int] = {}

        for m in self.markers:
            if m.distinguishes:
                pair = tuple(sorted(m.distinguishes))
                matrix[pair] = matrix.get(pair, 0) + 1

        return matrix

    def recommended_windows(
        self,
        min_markers: int = 5,
    ) -> list[tuple[str, int, int, int]]:
        """Identify windows with sufficient marker density.

        Parameters
        ----------
        min_markers : int
            Minimum markers required for a window to be recommended.

        Returns
        -------
        list[tuple]
            List of (chrom, start, end, n_markers) for recommended windows.
        """
        density = self.density_by_window()
        return [
            (d.chrom, d.start, d.end, d.total_markers)
            for d in density
            if d.total_markers >= min_markers
        ]

    def summary(self) -> str:
        """Generate human-readable summary report.

        Returns
        -------
        str
            Formatted summary report.
        """
        lines = [
            "=" * 60,
            "Diagnostic Marker Quality Assessment",
            "=" * 60,
            "",
            "Overall Statistics:",
            f"  Total markers: {self.total_markers:,}",
            f"  Fully diagnostic: {self.n_fully_diagnostic:,} ({self._pct(self.n_fully_diagnostic, self.total_markers)}%)",
            f"  Partially diagnostic: {self.n_partially_diagnostic:,} ({self._pct(self.n_partially_diagnostic, self.total_markers)}%)",
            f"  Informative: {self.n_informative:,} ({self._pct(self.n_informative, self.total_markers)}%)",
            "",
            "Founder populations: " + ", ".join(self.markers.founders),
            "",
            "Coverage by Chromosome:",
        ]

        for chrom in self.chromosomes:
            summary = self.chromosome_summary(chrom)
            if summary:
                lines.append(
                    f"  {chrom}: {summary.n_markers:,} markers, "
                    f"{summary.density:.1f}/Mb, "
                    f"{summary.n_gaps} gaps >500kb"
                )

        # Gaps
        gaps = self.find_gaps()
        if gaps:
            lines.extend([
                "",
                f"Gaps (>{self.gap_threshold // 1000}kb without markers):",
                f"  Total gaps: {len(gaps)}",
            ])
            for gap in gaps[:5]:
                lines.append(
                    f"  {gap.chrom}:{gap.start:,}-{gap.end:,} ({gap.length // 1000}kb)"
                )
            if len(gaps) > 5:
                lines.append(f"  ... and {len(gaps) - 5} more")

        # Founder pair coverage
        coverage = self.founder_pair_coverage()
        if coverage:
            lines.extend([
                "",
                "Founder Pair Coverage:",
            ])
            for cov in coverage[:10]:
                lines.append(
                    f"  {cov.founder1} vs {cov.founder2}: "
                    f"{cov.n_markers:,} markers ({cov.n_fully_diagnostic:,} diagnostic)"
                )

        lines.extend([
            "",
            "=" * 60,
        ])

        return "\n".join(lines)

    def _pct(self, num: int, denom: int) -> str:
        """Calculate percentage as string."""
        if denom == 0:
            return "0"
        return f"{100 * num / denom:.1f}"

    def to_dict(self) -> dict:
        """Convert assessment to dictionary format.

        Returns
        -------
        dict
            Assessment data as dictionary.
        """
        return {
            "total_markers": self.total_markers,
            "fully_diagnostic": self.n_fully_diagnostic,
            "partially_diagnostic": self.n_partially_diagnostic,
            "informative": self.n_informative,
            "founders": self.markers.founders,
            "chromosomes": {
                chrom: {
                    "n_markers": self.chromosome_summary(chrom).n_markers,
                    "density": self.chromosome_summary(chrom).density,
                    "n_gaps": self.chromosome_summary(chrom).n_gaps,
                }
                for chrom in self.chromosomes
                if self.chromosome_summary(chrom)
            },
            "gaps": [
                {
                    "chrom": g.chrom,
                    "start": g.start,
                    "end": g.end,
                    "length": g.length,
                }
                for g in self.find_gaps()
            ],
            "pair_coverage": {
                f"{c.founder1}_vs_{c.founder2}": c.n_markers
                for c in self.founder_pair_coverage()
            },
        }


def assess_marker_quality(
    markers: DiagnosticMarkerSet,
    genome_info: GenomeInfo | None = None,
    gap_threshold: int = 500_000,
) -> MarkerQualityAssessment:
    """Convenience function to assess marker quality.

    Parameters
    ----------
    markers : DiagnosticMarkerSet
        Markers to assess.
    genome_info : GenomeInfo, optional
        Genome information.
    gap_threshold : int
        Gap detection threshold.

    Returns
    -------
    MarkerQualityAssessment
        Quality assessment.
    """
    return MarkerQualityAssessment(
        markers=markers,
        genome_info=genome_info,
        gap_threshold=gap_threshold,
    )
