"""
Chimera detection in assembly contigs.

Detects haplotype switches within contigs that indicate potential misassemblies
(chimeric contigs joining sequences from different haplotypes).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from haplophaser.assembly.mapping import MarkerHit
    from haplophaser.assembly.paint import AssemblyPainting
    from haplophaser.io.assembly import Assembly

logger = logging.getLogger(__name__)


@dataclass
class ChimericRegion:
    """A detected haplotype switch within a contig.

    Parameters
    ----------
    contig : str
        Contig name.
    switch_position : int
        Estimated switch point (0-based).
    switch_position_ci : tuple[int, int]
        Confidence interval for switch position.
    left_founder : str
        Founder on left side of switch.
    right_founder : str
        Founder on right side of switch.
    left_confidence : float
        Confidence in left assignment.
    right_confidence : float
        Confidence in right assignment.
    n_markers_left : int
        Number of markers on left side.
    n_markers_right : int
        Number of markers on right side.
    left_proportion : float
        Proportion of markers supporting left founder.
    right_proportion : float
        Proportion of markers supporting right founder.
    """

    contig: str
    switch_position: int
    switch_position_ci: tuple[int, int]
    left_founder: str
    right_founder: str
    left_confidence: float
    right_confidence: float
    n_markers_left: int
    n_markers_right: int
    left_proportion: float = 0.0
    right_proportion: float = 0.0

    @property
    def switch_position_1based(self) -> int:
        """Return 1-based switch position."""
        return self.switch_position + 1

    @property
    def ci_width(self) -> int:
        """Return width of confidence interval."""
        return self.switch_position_ci[1] - self.switch_position_ci[0]

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "contig": self.contig,
            "switch_position": self.switch_position,
            "switch_position_ci": self.switch_position_ci,
            "left_founder": self.left_founder,
            "right_founder": self.right_founder,
            "left_confidence": self.left_confidence,
            "right_confidence": self.right_confidence,
            "n_markers_left": self.n_markers_left,
            "n_markers_right": self.n_markers_right,
            "left_proportion": self.left_proportion,
            "right_proportion": self.right_proportion,
        }

    def to_bed_breakpoint(self) -> str:
        """Format as BED line for breakpoint.

        Returns
        -------
        str
            BED format line.
        """
        name = f"{self.left_founder}>{self.right_founder}"
        score = int((self.left_confidence + self.right_confidence) * 500)
        # Use CI as the region
        return f"{self.contig}\t{self.switch_position_ci[0]}\t{self.switch_position_ci[1]}\t{name}\t{score}\t."


@dataclass
class ChimeraReport:
    """Report of chimera detection across an assembly.

    Parameters
    ----------
    assembly : str
        Assembly name.
    total_contigs : int
        Total contigs analyzed.
    chimeric_contigs : int
        Number of chimeric contigs.
    total_switches : int
        Total switch points detected.
    switches : list[ChimericRegion]
        List of detected switches.
    contigs_analyzed : int
        Contigs with sufficient markers for analysis.
    method : str
        Detection method used.
    parameters : dict
        Parameters used.
    """

    assembly: str
    total_contigs: int
    chimeric_contigs: int
    total_switches: int
    switches: list[ChimericRegion] = field(default_factory=list)
    contigs_analyzed: int = 0
    method: str = "sliding_window"
    parameters: dict = field(default_factory=dict)

    @property
    def chimera_rate(self) -> float:
        """Return fraction of contigs that are chimeric."""
        if self.contigs_analyzed == 0:
            return 0.0
        return self.chimeric_contigs / self.contigs_analyzed

    def switches_by_contig(self, contig: str) -> list[ChimericRegion]:
        """Get switches for a specific contig.

        Parameters
        ----------
        contig : str
            Contig name.

        Returns
        -------
        list[ChimericRegion]
            Switches on the contig.
        """
        return [s for s in self.switches if s.contig == contig]

    def chimeric_contig_names(self) -> list[str]:
        """Return list of chimeric contig names.

        Returns
        -------
        list[str]
            Unique contig names with chimeras.
        """
        return sorted({s.contig for s in self.switches})

    def summary(self) -> str:
        """Generate summary text.

        Returns
        -------
        str
            Human-readable summary.
        """
        lines = [
            f"Chimera Detection Report: {self.assembly}",
            "=" * 50,
            f"Contigs analyzed: {self.contigs_analyzed}",
            f"Chimeric contigs: {self.chimeric_contigs} ({self.chimera_rate:.1%})",
            f"Total switches: {self.total_switches}",
            "",
        ]

        if self.switches:
            lines.append("Chimeric regions:")
            for switch in sorted(self.switches, key=lambda s: (s.contig, s.switch_position)):
                lines.append(
                    f"  {switch.contig}:{switch.switch_position:,} "
                    f"({switch.left_founder} -> {switch.right_founder})"
                )

        return "\n".join(lines)

    def to_dataframe(self):
        """Convert to pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            Switches as DataFrame.
        """
        import pandas as pd

        if not self.switches:
            return pd.DataFrame(columns=[
                "contig", "switch_position", "ci_lower", "ci_upper",
                "left_founder", "right_founder", "left_confidence",
                "right_confidence", "n_markers_left", "n_markers_right",
            ])

        rows = []
        for s in self.switches:
            rows.append({
                "contig": s.contig,
                "switch_position": s.switch_position,
                "ci_lower": s.switch_position_ci[0],
                "ci_upper": s.switch_position_ci[1],
                "left_founder": s.left_founder,
                "right_founder": s.right_founder,
                "left_confidence": s.left_confidence,
                "right_confidence": s.right_confidence,
                "n_markers_left": s.n_markers_left,
                "n_markers_right": s.n_markers_right,
                "left_proportion": s.left_proportion,
                "right_proportion": s.right_proportion,
            })

        return pd.DataFrame(rows)


class ChimeraDetector:
    """Detect haplotype switches within contigs.

    Uses sliding window analysis to identify regions where the dominant
    founder changes, indicating potential chimeric assemblies.

    Parameters
    ----------
    window_size : int
        Sliding window size in bp.
    min_markers_per_window : int
        Minimum markers per window for analysis.
    switch_threshold : float
        Proportion change required to call a switch.
    min_confidence : float
        Minimum confidence for switch calling.
    step_size : int | None
        Step size for sliding window (default: window_size / 2).
    """

    def __init__(
        self,
        window_size: int = 50_000,
        min_markers_per_window: int = 3,
        switch_threshold: float = 0.5,
        min_confidence: float = 0.7,
        step_size: int | None = None,
    ) -> None:
        self.window_size = window_size
        self.min_markers_per_window = min_markers_per_window
        self.switch_threshold = switch_threshold
        self.min_confidence = min_confidence
        self.step_size = step_size or window_size // 2

    def detect(
        self,
        assembly: Assembly,
        marker_hits: list[MarkerHit],
        founders: list[str],
    ) -> ChimeraReport:
        """Detect chimeras across entire assembly.

        Parameters
        ----------
        assembly : Assembly
            Target assembly.
        marker_hits : list[MarkerHit]
            Marker hits on assembly.
        founders : list[str]
            List of founder names.

        Returns
        -------
        ChimeraReport
            Detection results.
        """
        logger.info(f"Running chimera detection on {assembly.n_contigs} contigs")

        # Group hits by contig
        hits_by_contig: dict[str, list[MarkerHit]] = {}
        for hit in marker_hits:
            if hit.is_unique:
                if hit.contig not in hits_by_contig:
                    hits_by_contig[hit.contig] = []
                hits_by_contig[hit.contig].append(hit)

        all_switches: list[ChimericRegion] = []
        chimeric_contigs: set[str] = set()
        contigs_analyzed = 0

        for contig_name, contig in assembly.contigs.items():
            contig_hits = hits_by_contig.get(contig_name, [])

            # Skip contigs with too few markers
            if len(contig_hits) < self.min_markers_per_window * 2:
                continue

            contigs_analyzed += 1

            switches = self.detect_in_contig(
                contig_name, contig.length, contig_hits, founders
            )

            if switches:
                all_switches.extend(switches)
                chimeric_contigs.add(contig_name)

        report = ChimeraReport(
            assembly=assembly.name,
            total_contigs=assembly.n_contigs,
            chimeric_contigs=len(chimeric_contigs),
            total_switches=len(all_switches),
            switches=all_switches,
            contigs_analyzed=contigs_analyzed,
            method="sliding_window",
            parameters={
                "window_size": self.window_size,
                "min_markers_per_window": self.min_markers_per_window,
                "switch_threshold": self.switch_threshold,
                "min_confidence": self.min_confidence,
            },
        )

        logger.info(
            f"Found {len(all_switches)} switches in "
            f"{len(chimeric_contigs)} chimeric contigs "
            f"(of {contigs_analyzed} analyzed)"
        )

        return report

    def detect_in_contig(
        self,
        contig_name: str,
        contig_length: int,
        hits: list[MarkerHit],
        founders: list[str],
    ) -> list[ChimericRegion]:
        """Detect chimeras within a single contig.

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
        list[ChimericRegion]
            Detected chimeric regions.
        """
        if len(hits) < self.min_markers_per_window * 2:
            return []

        # Sort hits by position
        sorted_hits = sorted(hits, key=lambda h: h.position)

        # Calculate founder proportions in sliding windows
        windows = self._calculate_window_proportions(
            sorted_hits, contig_length, founders
        )

        if len(windows) < 2:
            return []

        # Detect switches
        switches = self._find_switches(windows, contig_name, founders)

        # Refine switch positions
        refined_switches = []
        for switch in switches:
            refined = self._refine_switch_position(
                switch, sorted_hits, contig_name, founders
            )
            if refined:
                refined_switches.append(refined)

        return refined_switches

    def _calculate_window_proportions(
        self,
        sorted_hits: list[MarkerHit],
        contig_length: int,
        founders: list[str],
    ) -> list[dict]:
        """Calculate founder proportions in sliding windows.

        Parameters
        ----------
        sorted_hits : list[MarkerHit]
            Hits sorted by position.
        contig_length : int
            Contig length.
        founders : list[str]
            List of founders.

        Returns
        -------
        list[dict]
            Window statistics.
        """
        windows = []

        for start in range(0, contig_length, self.step_size):
            end = min(start + self.window_size, contig_length)

            # Get hits in window
            window_hits = [
                h for h in sorted_hits
                if start <= h.position < end
            ]

            if len(window_hits) < self.min_markers_per_window:
                continue

            # Count founders
            founder_counts = dict.fromkeys(founders, 0)
            for hit in window_hits:
                inferred = hit.inferred_founder()
                if inferred and inferred in founder_counts:
                    founder_counts[inferred] += 1

            total = sum(founder_counts.values())
            if total == 0:
                continue

            # Calculate proportions
            founder_props = {f: c / total for f, c in founder_counts.items()}

            # Find dominant founder
            dominant = max(founder_props, key=founder_props.get)
            dominant_prop = founder_props[dominant]

            windows.append({
                "start": start,
                "end": end,
                "midpoint": (start + end) // 2,
                "n_markers": len(window_hits),
                "founder_counts": founder_counts,
                "founder_proportions": founder_props,
                "dominant_founder": dominant,
                "dominant_proportion": dominant_prop,
            })

        return windows

    def _find_switches(
        self,
        windows: list[dict],
        contig_name: str,
        founders: list[str],
    ) -> list[ChimericRegion]:
        """Find switch points from window data.

        Parameters
        ----------
        windows : list[dict]
            Window statistics.
        contig_name : str
            Contig name.
        founders : list[str]
            List of founders.

        Returns
        -------
        list[ChimericRegion]
            Detected switches (preliminary).
        """
        switches = []

        for i in range(len(windows) - 1):
            w1 = windows[i]
            w2 = windows[i + 1]

            # Check for founder change
            if w1["dominant_founder"] != w2["dominant_founder"]:
                # Check confidence
                if (w1["dominant_proportion"] >= self.min_confidence and
                    w2["dominant_proportion"] >= self.min_confidence):

                    # Calculate proportion change
                    left_founder = w1["dominant_founder"]
                    right_founder = w2["dominant_founder"]

                    left_prop_change = (
                        w1["founder_proportions"].get(left_founder, 0) -
                        w2["founder_proportions"].get(left_founder, 0)
                    )

                    if abs(left_prop_change) >= self.switch_threshold:
                        # Preliminary switch position is between windows
                        switch_pos = (w1["end"] + w2["start"]) // 2
                        ci_start = w1["midpoint"]
                        ci_end = w2["midpoint"]

                        switch = ChimericRegion(
                            contig=contig_name,
                            switch_position=switch_pos,
                            switch_position_ci=(ci_start, ci_end),
                            left_founder=left_founder,
                            right_founder=right_founder,
                            left_confidence=w1["dominant_proportion"],
                            right_confidence=w2["dominant_proportion"],
                            n_markers_left=w1["n_markers"],
                            n_markers_right=w2["n_markers"],
                            left_proportion=w1["dominant_proportion"],
                            right_proportion=w2["dominant_proportion"],
                        )
                        switches.append(switch)

        return switches

    def _refine_switch_position(
        self,
        switch: ChimericRegion,
        sorted_hits: list[MarkerHit],
        contig_name: str,
        founders: list[str],
    ) -> ChimericRegion | None:
        """Refine switch position using marker-level data.

        Parameters
        ----------
        switch : ChimericRegion
            Preliminary switch.
        sorted_hits : list[MarkerHit]
            Sorted marker hits.
        contig_name : str
            Contig name.
        founders : list[str]
            List of founders.

        Returns
        -------
        ChimericRegion | None
            Refined switch or None if refinement fails.
        """
        ci_start, ci_end = switch.switch_position_ci

        # Get markers in the CI region and surrounding area
        margin = (ci_end - ci_start) // 2
        region_start = max(0, ci_start - margin)
        region_end = ci_end + margin

        region_hits = [
            h for h in sorted_hits
            if region_start <= h.position <= region_end
        ]

        if len(region_hits) < 4:
            return switch  # Can't refine, return original

        # Find the position where founder assignment changes
        # Use binary search approach
        left_founder = switch.left_founder
        right_founder = switch.right_founder

        best_pos = switch.switch_position
        best_score = 0.0

        for i in range(1, len(region_hits)):
            pos = region_hits[i].position

            # Count founders on each side
            left_hits = region_hits[:i]
            right_hits = region_hits[i:]

            left_count = sum(
                1 for h in left_hits
                if h.inferred_founder() == left_founder
            )
            right_count = sum(
                1 for h in right_hits
                if h.inferred_founder() == right_founder
            )

            # Score = how well this split separates the founders
            left_prop = left_count / len(left_hits) if left_hits else 0
            right_prop = right_count / len(right_hits) if right_hits else 0
            score = left_prop + right_prop

            if score > best_score:
                best_score = score
                best_pos = pos

        # Refine CI based on marker positions
        left_markers = [h for h in region_hits if h.position < best_pos]
        right_markers = [h for h in region_hits if h.position >= best_pos]

        if left_markers and right_markers:
            refined_ci_start = left_markers[-1].position
            refined_ci_end = right_markers[0].position
        else:
            refined_ci_start = ci_start
            refined_ci_end = ci_end

        return ChimericRegion(
            contig=contig_name,
            switch_position=best_pos,
            switch_position_ci=(refined_ci_start, refined_ci_end),
            left_founder=left_founder,
            right_founder=right_founder,
            left_confidence=switch.left_confidence,
            right_confidence=switch.right_confidence,
            n_markers_left=len(left_markers),
            n_markers_right=len(right_markers),
            left_proportion=switch.left_proportion,
            right_proportion=switch.right_proportion,
        )

    def from_painting(
        self,
        assembly: Assembly,
        painting: AssemblyPainting,
        marker_hits: list[MarkerHit],
    ) -> ChimeraReport:
        """Run chimera detection on already-painted assembly.

        Parameters
        ----------
        assembly : Assembly
            Target assembly.
        painting : AssemblyPainting
            Existing painting results.
        marker_hits : list[MarkerHit]
            Marker hits on assembly.

        Returns
        -------
        ChimeraReport
            Detection results.
        """
        return self.detect(assembly, marker_hits, painting.founders)


def detect_chimeras(
    assembly: Assembly,
    marker_hits: list[MarkerHit],
    founders: list[str],
    window_size: int = 50_000,
    min_markers_per_window: int = 3,
    switch_threshold: float = 0.5,
) -> ChimeraReport:
    """Convenience function to detect chimeras.

    Parameters
    ----------
    assembly : Assembly
        Target assembly.
    marker_hits : list[MarkerHit]
        Marker hits on assembly.
    founders : list[str]
        List of founder names.
    window_size : int
        Window size for detection.
    min_markers_per_window : int
        Minimum markers per window.
    switch_threshold : float
        Proportion change for switch.

    Returns
    -------
    ChimeraReport
        Detection results.
    """
    detector = ChimeraDetector(
        window_size=window_size,
        min_markers_per_window=min_markers_per_window,
        switch_threshold=switch_threshold,
    )
    return detector.detect(assembly, marker_hits, founders)
