"""
Integrate multiple evidence sources for subgenome assignment.

Combines synteny, ortholog, and marker-based evidence using weighted
voting or priority-based resolution to produce final subgenome assignments.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from haplophaser.subgenome.models import (
    SubgenomeAssignment,
    SubgenomeAssignmentResult,
    SubgenomeConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class IntegrationParams:
    """Parameters for evidence integration.

    Parameters
    ----------
    weights : dict[str, float]
        Weights for each evidence type.
    conflict_resolution : str
        Strategy: 'weighted_vote', 'synteny_priority', 'consensus'.
    min_evidence_types : int
        Minimum evidence types required.
    min_combined_confidence : float
        Minimum combined confidence for assignment.
    """

    weights: dict[str, float] = field(default_factory=lambda: {
        "synteny": 1.0,
        "orthologs": 0.8,
        "markers": 0.6,
    })
    conflict_resolution: str = "weighted_vote"
    min_evidence_types: int = 1
    min_combined_confidence: float = 0.5


@dataclass
class IntegratedAssignment:
    """An assignment with integrated evidence.

    Parameters
    ----------
    chrom : str
        Chromosome.
    start : int
        Start position.
    end : int
        End position.
    subgenome : str
        Assigned subgenome.
    confidence : float
        Combined confidence.
    evidence_sources : list[str]
        Sources that contributed.
    source_confidences : dict[str, float]
        Confidence from each source.
    has_conflict : bool
        Whether sources disagreed.
    conflict_details : dict, optional
        Details about conflicts.
    """

    chrom: str
    start: int
    end: int
    subgenome: str
    confidence: float
    evidence_sources: list[str]
    source_confidences: dict[str, float]
    has_conflict: bool = False
    conflict_details: dict[str, Any] | None = None


class SubgenomeIntegrator:
    """Integrate multiple evidence sources for subgenome assignment.

    Combines assignments from synteny, orthologs, and markers using
    configurable weighting and conflict resolution strategies.

    Parameters
    ----------
    weights : dict[str, float], optional
        Weights for each evidence type.
    conflict_resolution : str
        Resolution strategy: 'weighted_vote', 'synteny_priority', 'consensus'.

    Examples
    --------
    >>> integrator = SubgenomeIntegrator(
    ...     weights={"synteny": 1.0, "orthologs": 0.8, "markers": 0.6},
    ...     conflict_resolution="weighted_vote",
    ... )
    >>> result = integrator.integrate(
    ...     synteny_assignments=synteny_result,
    ...     ortholog_assignments=ortholog_result,
    ...     marker_assignments=marker_result,
    ... )
    """

    def __init__(
        self,
        weights: dict[str, float] | None = None,
        conflict_resolution: str = "weighted_vote",
    ) -> None:
        self.params = IntegrationParams(
            weights=weights or {"synteny": 1.0, "orthologs": 0.8, "markers": 0.6},
            conflict_resolution=conflict_resolution,
        )

    def integrate(
        self,
        synteny_assignments: SubgenomeAssignmentResult | None = None,
        ortholog_assignments: SubgenomeAssignmentResult | None = None,
        marker_assignments: SubgenomeAssignmentResult | None = None,
        config: SubgenomeConfig | None = None,
    ) -> SubgenomeAssignmentResult:
        """Integrate assignments from multiple sources.

        Parameters
        ----------
        synteny_assignments : SubgenomeAssignmentResult, optional
            Synteny-based assignments.
        ortholog_assignments : SubgenomeAssignmentResult, optional
            Ortholog-based assignments.
        marker_assignments : SubgenomeAssignmentResult, optional
            Marker-based assignments.
        config : SubgenomeConfig, optional
            Subgenome configuration.

        Returns
        -------
        SubgenomeAssignmentResult
            Integrated assignments.
        """
        # Collect all assignments
        all_assignments: dict[str, list[SubgenomeAssignment]] = {
            "synteny": [],
            "orthologs": [],
            "markers": [],
        }

        if synteny_assignments:
            all_assignments["synteny"] = synteny_assignments.assignments
            if config is None:
                config = synteny_assignments.config

        if ortholog_assignments:
            all_assignments["orthologs"] = ortholog_assignments.assignments
            if config is None:
                config = ortholog_assignments.config

        if marker_assignments:
            all_assignments["markers"] = marker_assignments.assignments
            if config is None:
                config = marker_assignments.config

        if config is None:
            config = SubgenomeConfig.maize_default()

        # Find all unique regions
        all_regions = self._identify_regions(all_assignments)

        # Integrate each region
        integrated = []
        for chrom, start, end in all_regions:
            assignment = self._integrate_region(
                chrom, start, end, all_assignments
            )
            if assignment:
                integrated.append(assignment)

        # Merge adjacent same-subgenome regions
        merged = self._merge_adjacent(integrated)

        # Convert to SubgenomeAssignment
        final_assignments = [
            SubgenomeAssignment(
                chrom=a.chrom,
                start=a.start,
                end=a.end,
                subgenome=a.subgenome,
                confidence=a.confidence,
                evidence="combined",
                evidence_details={
                    "sources": a.evidence_sources,
                    "source_confidences": a.source_confidences,
                    "has_conflict": a.has_conflict,
                    "conflict_details": a.conflict_details,
                },
            )
            for a in merged
        ]

        query_name = "integrated"
        if synteny_assignments:
            query_name = synteny_assignments.query_name

        return SubgenomeAssignmentResult(
            query_name=query_name,
            config=config,
            assignments=final_assignments,
            method="combined",
            parameters={
                "weights": self.params.weights,
                "conflict_resolution": self.params.conflict_resolution,
            },
        )

    def _identify_regions(
        self,
        all_assignments: dict[str, list[SubgenomeAssignment]],
    ) -> list[tuple[str, int, int]]:
        """Identify all unique regions from all sources.

        Parameters
        ----------
        all_assignments : dict
            Assignments by source.

        Returns
        -------
        list[tuple[str, int, int]]
            List of (chrom, start, end) tuples.
        """
        # Collect all breakpoints by chromosome
        breakpoints: dict[str, set[int]] = defaultdict(set)

        for _source, assignments in all_assignments.items():
            for a in assignments:
                breakpoints[a.chrom].add(a.start)
                breakpoints[a.chrom].add(a.end)

        # Create regions between breakpoints
        regions = []
        for chrom, bps in breakpoints.items():
            sorted_bps = sorted(bps)
            for i in range(len(sorted_bps) - 1):
                regions.append((chrom, sorted_bps[i], sorted_bps[i + 1]))

        return sorted(regions)

    def _integrate_region(
        self,
        chrom: str,
        start: int,
        end: int,
        all_assignments: dict[str, list[SubgenomeAssignment]],
    ) -> IntegratedAssignment | None:
        """Integrate evidence for a single region.

        Parameters
        ----------
        chrom : str
            Chromosome.
        start : int
            Start position.
        end : int
            End position.
        all_assignments : dict
            Assignments by source.

        Returns
        -------
        IntegratedAssignment or None
            Integrated assignment if sufficient evidence.
        """
        # Find overlapping assignments from each source
        source_calls: dict[str, tuple[str, float]] = {}

        for source, assignments in all_assignments.items():
            for a in assignments:
                if a.overlaps(chrom, start, end):
                    # Calculate overlap proportion
                    overlap_start = max(a.start, start)
                    overlap_end = min(a.end, end)
                    overlap_len = overlap_end - overlap_start
                    region_len = end - start

                    if overlap_len / region_len >= 0.5:  # At least 50% overlap
                        if source not in source_calls or a.confidence > source_calls[source][1]:
                            source_calls[source] = (a.subgenome, a.confidence)

        if not source_calls:
            return None

        # Apply conflict resolution
        if self.params.conflict_resolution == "weighted_vote":
            result = self._weighted_vote(source_calls)
        elif self.params.conflict_resolution == "synteny_priority":
            result = self._synteny_priority(source_calls)
        else:  # consensus
            result = self._consensus(source_calls)

        if result is None:
            return None

        subgenome, confidence, has_conflict, conflict_details = result

        return IntegratedAssignment(
            chrom=chrom,
            start=start,
            end=end,
            subgenome=subgenome,
            confidence=confidence,
            evidence_sources=list(source_calls.keys()),
            source_confidences={s: c for s, (_, c) in source_calls.items()},
            has_conflict=has_conflict,
            conflict_details=conflict_details,
        )

    def _weighted_vote(
        self,
        source_calls: dict[str, tuple[str, float]],
    ) -> tuple[str, float, bool, dict | None] | None:
        """Resolve by weighted voting.

        Parameters
        ----------
        source_calls : dict
            (subgenome, confidence) by source.

        Returns
        -------
        tuple or None
            (subgenome, confidence, has_conflict, conflict_details)
        """
        # Calculate weighted score for each subgenome
        sg_scores: dict[str, float] = defaultdict(float)
        sg_sources: dict[str, list[str]] = defaultdict(list)

        for source, (sg, conf) in source_calls.items():
            weight = self.params.weights.get(source, 1.0)
            sg_scores[sg] += weight * conf
            sg_sources[sg].append(source)

        if not sg_scores:
            return None

        # Find winner
        winner = max(sg_scores, key=sg_scores.get)
        total_weight = sum(sg_scores.values())
        winner_score = sg_scores[winner]

        # Check for conflict
        has_conflict = len(sg_scores) > 1
        conflict_details = None
        if has_conflict:
            conflict_details = {
                "subgenome_scores": dict(sg_scores),
                "subgenome_sources": dict(sg_sources),
            }

        # Calculate combined confidence
        confidence = winner_score / total_weight if total_weight > 0 else 0.0

        return winner, round(confidence, 3), has_conflict, conflict_details

    def _synteny_priority(
        self,
        source_calls: dict[str, tuple[str, float]],
    ) -> tuple[str, float, bool, dict | None] | None:
        """Resolve giving priority to synteny.

        Parameters
        ----------
        source_calls : dict
            (subgenome, confidence) by source.

        Returns
        -------
        tuple or None
            (subgenome, confidence, has_conflict, conflict_details)
        """
        # Priority order: synteny > orthologs > markers
        priority = ["synteny", "orthologs", "markers"]

        for source in priority:
            if source in source_calls:
                sg, conf = source_calls[source]

                # Check for conflicts with other sources
                has_conflict = any(
                    source_calls[s][0] != sg for s in source_calls if s != source
                )
                conflict_details = None
                if has_conflict:
                    conflict_details = {
                        "primary_source": source,
                        "overridden_sources": [
                            s for s in source_calls if source_calls[s][0] != sg
                        ],
                    }

                return sg, conf, has_conflict, conflict_details

        return None

    def _consensus(
        self,
        source_calls: dict[str, tuple[str, float]],
    ) -> tuple[str, float, bool, dict | None] | None:
        """Require consensus (all sources agree).

        Parameters
        ----------
        source_calls : dict
            (subgenome, confidence) by source.

        Returns
        -------
        tuple or None
            (subgenome, confidence, has_conflict, conflict_details)
        """
        subgenomes = [sg for sg, _ in source_calls.values()]
        unique_sgs = set(subgenomes)

        if len(unique_sgs) == 1:
            # All agree
            sg = subgenomes[0]
            confidences = [c for _, c in source_calls.values()]
            confidence = float(np.mean(confidences))
            return sg, round(confidence, 3), False, None
        else:
            # Conflict - return None or majority if enough evidence
            if len(source_calls) >= 3:
                # Use majority
                sg_counts: dict[str, int] = defaultdict(int)
                for sg in subgenomes:
                    sg_counts[sg] += 1

                majority = max(sg_counts, key=sg_counts.get)
                if sg_counts[majority] >= len(source_calls) / 2:
                    confidences = [
                        c for sg, c in source_calls.values()
                        if source_calls.get(sg, (None,))[0] == majority
                    ]
                    confidence = float(np.mean(confidences)) * 0.8  # Penalize conflict
                    return majority, round(confidence, 3), True, {"conflict_type": "majority_vote"}

            return None

    def _merge_adjacent(
        self,
        assignments: list[IntegratedAssignment],
    ) -> list[IntegratedAssignment]:
        """Merge adjacent regions with same subgenome.

        Parameters
        ----------
        assignments : list[IntegratedAssignment]
            Assignments to merge.

        Returns
        -------
        list[IntegratedAssignment]
            Merged assignments.
        """
        if not assignments:
            return []

        # Group by chromosome
        by_chrom: dict[str, list[IntegratedAssignment]] = defaultdict(list)
        for a in assignments:
            by_chrom[a.chrom].append(a)

        merged = []

        for _chrom, chrom_assignments in by_chrom.items():
            sorted_assignments = sorted(chrom_assignments, key=lambda x: x.start)

            current = sorted_assignments[0]
            current_confidences = [current.confidence]
            current_sources = set(current.evidence_sources)
            current_conflicts = current.has_conflict

            for next_a in sorted_assignments[1:]:
                # Check if adjacent and same subgenome
                if (next_a.start == current.end and
                    next_a.subgenome == current.subgenome):
                    # Merge
                    current = IntegratedAssignment(
                        chrom=current.chrom,
                        start=current.start,
                        end=next_a.end,
                        subgenome=current.subgenome,
                        confidence=current.confidence,  # Updated below
                        evidence_sources=list(current_sources | set(next_a.evidence_sources)),
                        source_confidences={},  # Simplified for merged
                        has_conflict=current_conflicts or next_a.has_conflict,
                    )
                    current_confidences.append(next_a.confidence)
                    current_sources.update(next_a.evidence_sources)
                    current_conflicts = current_conflicts or next_a.has_conflict
                else:
                    # Finalize current
                    current = IntegratedAssignment(
                        chrom=current.chrom,
                        start=current.start,
                        end=current.end,
                        subgenome=current.subgenome,
                        confidence=round(float(np.mean(current_confidences)), 3),
                        evidence_sources=list(current_sources),
                        source_confidences=current.source_confidences,
                        has_conflict=current_conflicts,
                    )
                    merged.append(current)

                    current = next_a
                    current_confidences = [next_a.confidence]
                    current_sources = set(next_a.evidence_sources)
                    current_conflicts = next_a.has_conflict

            # Add final
            current = IntegratedAssignment(
                chrom=current.chrom,
                start=current.start,
                end=current.end,
                subgenome=current.subgenome,
                confidence=round(float(np.mean(current_confidences)), 3),
                evidence_sources=list(current_sources),
                source_confidences=current.source_confidences,
                has_conflict=current_conflicts,
            )
            merged.append(current)

        return sorted(merged, key=lambda x: (x.chrom, x.start))


def integrate_assignments(
    synteny_assignments: SubgenomeAssignmentResult | None = None,
    ortholog_assignments: SubgenomeAssignmentResult | None = None,
    marker_assignments: SubgenomeAssignmentResult | None = None,
    weights: dict[str, float] | None = None,
    conflict_resolution: str = "weighted_vote",
) -> SubgenomeAssignmentResult:
    """Convenience function to integrate subgenome assignments.

    Parameters
    ----------
    synteny_assignments : SubgenomeAssignmentResult, optional
        Synteny-based assignments.
    ortholog_assignments : SubgenomeAssignmentResult, optional
        Ortholog-based assignments.
    marker_assignments : SubgenomeAssignmentResult, optional
        Marker-based assignments.
    weights : dict[str, float], optional
        Evidence weights.
    conflict_resolution : str
        Resolution strategy.

    Returns
    -------
    SubgenomeAssignmentResult
        Integrated assignments.
    """
    integrator = SubgenomeIntegrator(
        weights=weights,
        conflict_resolution=conflict_resolution,
    )

    return integrator.integrate(
        synteny_assignments=synteny_assignments,
        ortholog_assignments=ortholog_assignments,
        marker_assignments=marker_assignments,
    )
