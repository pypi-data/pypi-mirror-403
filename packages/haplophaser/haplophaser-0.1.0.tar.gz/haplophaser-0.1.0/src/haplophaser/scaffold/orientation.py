"""
Contig orientation inference.

Determines contig orientation using marker order and haplotype gradients.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
from scipy import stats

if TYPE_CHECKING:
    from haplophaser.assembly.paint import AssemblyPainting
    from haplophaser.io.assembly import Assembly
    from haplophaser.scaffold.contig_markers import ContigMarkerMap, ContigPlacement

logger = logging.getLogger(__name__)


@dataclass
class OrientationCall:
    """Orientation call for a single contig.

    Attributes:
        contig: Contig name.
        orientation: Orientation ('+', '-', or '?').
        confidence: Confidence in call (0-1).
        evidence: List of evidence sources.
        marker_order_score: Agreement with genetic map order (-1 to 1).
        haplotype_gradient_score: Haplotype proportion trend score.
        n_markers: Number of markers used for inference.
    """

    contig: str
    orientation: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    marker_order_score: float | None = None
    haplotype_gradient_score: float | None = None
    n_markers: int = 0

    @property
    def is_determined(self) -> bool:
        """Return True if orientation is determined (not '?')."""
        return self.orientation in ("+", "-")


class ContigOrienter:
    """Determine contig orientations.

    Parameters
    ----------
    method : str
        Method: 'marker_order', 'haplotype_gradient', or 'combined'.
    min_markers : int
        Minimum markers for orientation inference.
    min_correlation : float
        Minimum absolute correlation for confident call.
    haplotype_window : int
        Window size for haplotype gradient calculation.
    """

    def __init__(
        self,
        method: str = "combined",
        min_markers: int = 2,
        min_correlation: float = 0.5,
        haplotype_window: int = 50_000,
    ) -> None:
        if method not in ("marker_order", "haplotype_gradient", "combined"):
            raise ValueError(f"Unknown method: {method}")

        self.method = method
        self.min_markers = min_markers
        self.min_correlation = min_correlation
        self.haplotype_window = haplotype_window

    def infer(
        self,
        assembly: Assembly,
        contig_map: ContigMarkerMap,
        painting: AssemblyPainting | None = None,
    ) -> dict[str, OrientationCall]:
        """Infer orientations for all contigs.

        Parameters
        ----------
        assembly : Assembly
            Source assembly.
        contig_map : ContigMarkerMap
            Contig-to-genetic-map relationships.
        painting : AssemblyPainting | None
            Haplotype painting (for haplotype_gradient method).

        Returns
        -------
        dict[str, OrientationCall]
            Orientation calls keyed by contig name.
        """
        logger.info(f"Inferring contig orientations using method: {self.method}")

        orientations = {}

        for contig_name in assembly.contigs:
            placement = contig_map.get_placement(contig_name)
            call = self._infer_contig(
                contig_name=contig_name,
                placement=placement,
                contig_map=contig_map,
                painting=painting,
            )
            orientations[contig_name] = call

        n_determined = sum(1 for o in orientations.values() if o.is_determined)
        logger.info(f"Determined orientation for {n_determined}/{len(orientations)} contigs")

        return orientations

    def _infer_contig(
        self,
        contig_name: str,
        placement: ContigPlacement | None,
        contig_map: ContigMarkerMap,
        painting: AssemblyPainting | None,
    ) -> OrientationCall:
        """Infer orientation for a single contig.

        Parameters
        ----------
        contig_name : str
            Contig name.
        placement : ContigPlacement | None
            Genetic map placement.
        contig_map : ContigMarkerMap
            Contig-to-genetic-map relationships.
        painting : AssemblyPainting | None
            Haplotype painting.

        Returns
        -------
        OrientationCall
            Orientation call.
        """
        marker_score = None
        haplotype_score = None
        evidence = []
        n_markers = 0

        # Method 1: Marker order correlation
        if self.method in ("marker_order", "combined") and placement and placement.markers:
            marker_score = self._marker_order_score(placement.markers)
            n_markers = len(placement.markers)
            if marker_score is not None:
                evidence.append("marker_order")

        # Method 2: Haplotype gradient
        if self.method in ("haplotype_gradient", "combined") and painting:
            contig_painting = painting.get_contig(contig_name)
            if contig_painting and contig_painting.marker_positions:
                haplotype_score = self._haplotype_gradient_score(
                    contig_painting.marker_positions,
                    contig_painting.marker_founders,
                )
                if haplotype_score is not None:
                    evidence.append("haplotype_gradient")

        # Combine scores
        orientation, confidence = self._combine_scores(
            marker_score, haplotype_score, n_markers
        )

        return OrientationCall(
            contig=contig_name,
            orientation=orientation,
            confidence=confidence,
            evidence=evidence,
            marker_order_score=marker_score,
            haplotype_gradient_score=haplotype_score,
            n_markers=n_markers,
        )

    def _marker_order_score(
        self, markers: list
    ) -> float | None:
        """Calculate marker order correlation score.

        Computes Spearman correlation between physical position
        on contig and genetic map position.

        Parameters
        ----------
        markers : list[MappedMarker]
            Markers on contig.

        Returns
        -------
        float | None
            Correlation coefficient (-1 to 1) or None if insufficient data.
        """
        if len(markers) < self.min_markers:
            return None

        # Sort by physical position
        sorted_markers = sorted(markers, key=lambda m: m.pos_physical)

        physical_pos = [m.pos_physical for m in sorted_markers]
        genetic_pos = [m.pos_genetic for m in sorted_markers]

        # Check for variation
        if len(set(physical_pos)) < 2 or len(set(genetic_pos)) < 2:
            return None

        try:
            corr, _ = stats.spearmanr(physical_pos, genetic_pos)
            if np.isnan(corr):
                return None
            return corr
        except Exception:
            return None

    def _haplotype_gradient_score(
        self,
        positions: list[int],
        founders: list[str],
    ) -> float | None:
        """Calculate haplotype gradient score.

        Looks for a consistent trend in founder proportions along
        the contig, which can indicate orientation near transitions.

        Parameters
        ----------
        positions : list[int]
            Marker positions on contig.
        founders : list[str]
            Founder assignments at each position.

        Returns
        -------
        float | None
            Gradient score (-1 to 1) or None.
        """
        if len(positions) < self.min_markers:
            return None

        # Create windows and calculate founder proportions
        min_pos = min(positions)
        max_pos = max(positions)

        if max_pos - min_pos < self.haplotype_window:
            return None

        # Sort by position
        sorted_data = sorted(zip(positions, founders, strict=False), key=lambda x: x[0])

        # Calculate running proportion of majority founder
        majority_founder = max(set(founders), key=founders.count)
        window_props = []
        window_positions = []

        for i in range(0, len(sorted_data) - self.min_markers + 1):
            window_founders = [f for _, f in sorted_data[i:i + self.min_markers]]
            prop = sum(1 for f in window_founders if f == majority_founder) / len(window_founders)
            window_props.append(prop)
            window_positions.append(sorted_data[i + self.min_markers // 2][0])

        if len(window_props) < 2:
            return None

        # Check for gradient (monotonic trend)
        try:
            corr, _ = stats.spearmanr(window_positions, window_props)
            if np.isnan(corr):
                return None
            return corr
        except Exception:
            return None

    def _combine_scores(
        self,
        marker_score: float | None,
        haplotype_score: float | None,
        n_markers: int,
    ) -> tuple[str, float]:
        """Combine scores to determine orientation.

        Parameters
        ----------
        marker_score : float | None
            Marker order correlation.
        haplotype_score : float | None
            Haplotype gradient score.
        n_markers : int
            Number of markers.

        Returns
        -------
        tuple[str, float]
            (orientation, confidence) tuple.
        """
        scores = []
        weights = []

        if marker_score is not None:
            scores.append(marker_score)
            # Weight by number of markers (logistic function)
            weight = 1 / (1 + np.exp(-(n_markers - self.min_markers) / 2))
            weights.append(weight * 2)  # Marker order weighted higher

        if haplotype_score is not None:
            scores.append(haplotype_score)
            weights.append(1.0)

        if not scores:
            return "?", 0.0

        # Weighted average
        total_weight = sum(weights)
        weighted_score = sum(s * w for s, w in zip(scores, weights, strict=False)) / total_weight

        # Determine orientation
        if weighted_score > self.min_correlation:
            orientation = "+"
            confidence = min(abs(weighted_score), 1.0)
        elif weighted_score < -self.min_correlation:
            orientation = "-"
            confidence = min(abs(weighted_score), 1.0)
        else:
            orientation = "?"
            confidence = 0.0

        return orientation, round(confidence, 3)

    def infer_from_neighbors(
        self,
        contig: str,
        left_neighbor: str | None,
        right_neighbor: str | None,
        left_haplotype: str | None,
        right_haplotype: str | None,
        painting: AssemblyPainting,
    ) -> OrientationCall:
        """Infer orientation from neighboring contigs.

        Useful when a contig has insufficient markers but
        neighboring contigs have assigned haplotypes.

        Parameters
        ----------
        contig : str
            Target contig.
        left_neighbor : str | None
            Left neighboring contig name.
        right_neighbor : str | None
            Right neighboring contig name.
        left_haplotype : str | None
            Expected haplotype on left end.
        right_haplotype : str | None
            Expected haplotype on right end.
        painting : AssemblyPainting
            Haplotype painting.

        Returns
        -------
        OrientationCall
            Orientation call based on neighbor compatibility.
        """
        contig_painting = painting.get_contig(contig)
        if not contig_painting or not contig_painting.marker_positions:
            return OrientationCall(
                contig=contig,
                orientation="?",
                confidence=0.0,
                evidence=["neighbor_inference"],
            )

        # Get haplotypes at contig ends
        positions = contig_painting.marker_positions
        founders = contig_painting.marker_founders

        if not positions:
            return OrientationCall(
                contig=contig,
                orientation="?",
                confidence=0.0,
                evidence=["neighbor_inference"],
            )

        # Sort by position
        sorted_data = sorted(zip(positions, founders, strict=False), key=lambda x: x[0])

        # Get end haplotypes (using first/last few markers)
        n_end = min(3, len(sorted_data))
        left_end_founders = [f for _, f in sorted_data[:n_end]]
        right_end_founders = [f for _, f in sorted_data[-n_end:]]

        left_end_majority = max(set(left_end_founders), key=left_end_founders.count)
        right_end_majority = max(set(right_end_founders), key=right_end_founders.count)

        # Score orientations
        plus_score = 0
        minus_score = 0

        if left_haplotype:
            if left_end_majority == left_haplotype:
                plus_score += 1
            if right_end_majority == left_haplotype:
                minus_score += 1

        if right_haplotype:
            if right_end_majority == right_haplotype:
                plus_score += 1
            if left_end_majority == right_haplotype:
                minus_score += 1

        # Determine orientation
        if plus_score > minus_score:
            orientation = "+"
            confidence = plus_score / (plus_score + minus_score + 0.1)
        elif minus_score > plus_score:
            orientation = "-"
            confidence = minus_score / (plus_score + minus_score + 0.1)
        else:
            orientation = "?"
            confidence = 0.0

        return OrientationCall(
            contig=contig,
            orientation=orientation,
            confidence=round(confidence, 3),
            evidence=["neighbor_inference"],
            n_markers=len(positions),
        )


def infer_orientations(
    assembly: Assembly,
    contig_map: ContigMarkerMap,
    painting: AssemblyPainting | None = None,
    method: str = "combined",
    min_markers: int = 2,
) -> dict[str, OrientationCall]:
    """Convenience function to infer contig orientations.

    Parameters
    ----------
    assembly : Assembly
        Source assembly.
    contig_map : ContigMarkerMap
        Contig-to-genetic-map relationships.
    painting : AssemblyPainting | None
        Haplotype painting.
    method : str
        Inference method.
    min_markers : int
        Minimum markers for inference.

    Returns
    -------
    dict[str, OrientationCall]
        Orientation calls keyed by contig name.
    """
    orienter = ContigOrienter(method=method, min_markers=min_markers)
    return orienter.infer(assembly, contig_map, painting)
