"""
Synteny-based subgenome assignment.

Assigns genomic regions to subgenomes based on synteny to a reference
genome with known subgenome assignments. This is the primary method
for subgenome deconvolution in paleopolyploids.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from haplophaser.subgenome.models import (
    SubgenomeAssignment,
    SubgenomeAssignmentResult,
    SubgenomeConfig,
    SyntenyBlock,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class SyntenyAssignmentParams:
    """Parameters for synteny-based assignment.

    Parameters
    ----------
    min_block_size : int
        Minimum synteny block size (bp).
    min_genes : int
        Minimum genes/anchors in block.
    min_identity : float
        Minimum sequence identity.
    min_coverage : float
        Minimum coverage of query region.
    merge_distance : int
        Merge adjacent blocks within this distance.
    conflict_resolution : str
        How to resolve conflicting assignments: 'majority', 'longest', 'highest_identity'.
    """

    min_block_size: int = 50_000
    min_genes: int = 5
    min_identity: float = 0.0
    min_coverage: float = 0.0
    merge_distance: int = 100_000
    conflict_resolution: str = "majority"


class SyntenySubgenomeAssigner:
    """Assign subgenomes based on synteny to reference.

    Uses synteny blocks to transfer known subgenome assignments from
    a reference genome to a query assembly.

    Parameters
    ----------
    config : SubgenomeConfig
        Subgenome configuration.
    min_block_size : int
        Minimum synteny block size.
    min_genes : int
        Minimum genes/anchors in block.
    min_identity : float
        Minimum sequence identity.

    Examples
    --------
    >>> config = SubgenomeConfig.maize_default()
    >>> assigner = SyntenySubgenomeAssigner(config)
    >>> result = assigner.assign(
    ...     synteny_blocks="synteny_to_B73.paf",
    ...     reference_assignments="B73_subgenomes.bed",
    ... )
    """

    def __init__(
        self,
        config: SubgenomeConfig,
        min_block_size: int = 50_000,
        min_genes: int = 5,
        min_identity: float = 0.0,
    ) -> None:
        self.config = config
        self.params = SyntenyAssignmentParams(
            min_block_size=min_block_size,
            min_genes=min_genes,
            min_identity=min_identity,
        )

    def assign(
        self,
        synteny_blocks: Path | str | list[SyntenyBlock],
        reference_assignments: Path | str | dict[str, list[tuple[int, int, str]]],
        query_name: str = "query",
    ) -> SubgenomeAssignmentResult:
        """Assign subgenomes using pre-computed synteny.

        Parameters
        ----------
        synteny_blocks : Path, str, or list[SyntenyBlock]
            Synteny blocks from alignment (file path or parsed blocks).
        reference_assignments : Path, str, or dict
            Known subgenome assignments for reference.
        query_name : str
            Name for the query assembly.

        Returns
        -------
        SubgenomeAssignmentResult
            Subgenome assignments for query regions.
        """
        from haplophaser.io.synteny import load_reference_assignments, load_synteny

        # Load synteny blocks if path provided
        if isinstance(synteny_blocks, (str, Path)):
            blocks = load_synteny(
                synteny_blocks,
                min_length=self.params.min_block_size,
                min_anchors=self.params.min_genes,
                min_identity=self.params.min_identity,
            )
        else:
            blocks = synteny_blocks

        # Load reference assignments if path provided
        if isinstance(reference_assignments, (str, Path)):
            ref_assignments = load_reference_assignments(reference_assignments)
        else:
            ref_assignments = reference_assignments

        logger.info(
            f"Assigning subgenomes using {len(blocks)} synteny blocks"
        )

        # Transfer assignments via synteny
        assignments = self._transfer_assignments(blocks, ref_assignments)

        # Merge adjacent assignments
        merged = self._merge_adjacent_assignments(assignments)

        return SubgenomeAssignmentResult(
            query_name=query_name,
            config=self.config,
            assignments=merged,
            method="synteny",
            parameters={
                "min_block_size": self.params.min_block_size,
                "min_genes": self.params.min_genes,
                "min_identity": self.params.min_identity,
            },
        )

    def assign_with_alignment(
        self,
        query_assembly: Path | str,
        reference_assembly: Path | str,
        reference_assignments: Path | str,
        aligner: str = "minimap2",
        aligner_params: str | None = None,
        threads: int = 4,
    ) -> SubgenomeAssignmentResult:
        """Assign subgenomes by computing synteny on-the-fly.

        Parameters
        ----------
        query_assembly : Path or str
            Query assembly FASTA.
        reference_assembly : Path or str
            Reference assembly FASTA.
        reference_assignments : Path or str
            Known subgenome assignments for reference.
        aligner : str
            Alignment tool to use ('minimap2').
        aligner_params : str, optional
            Additional aligner parameters.
        threads : int
            Number of threads.

        Returns
        -------
        SubgenomeAssignmentResult
            Subgenome assignments.
        """
        import subprocess
        import tempfile

        query_path = Path(query_assembly)
        ref_path = Path(reference_assembly)

        logger.info(f"Computing synteny between {query_path} and {ref_path}")

        # Run minimap2
        with tempfile.NamedTemporaryFile(suffix=".paf", delete=False) as tmp:
            paf_path = Path(tmp.name)

        try:
            cmd = [
                "minimap2",
                "-x", "asm5",
                "-t", str(threads),
                str(ref_path),
                str(query_path),
                "-o", str(paf_path),
            ]

            if aligner_params:
                cmd.extend(aligner_params.split())

            logger.info(f"Running: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, capture_output=True)

            # Use the PAF file for assignment
            return self.assign(
                synteny_blocks=paf_path,
                reference_assignments=reference_assignments,
                query_name=query_path.stem,
            )
        finally:
            # Clean up
            if paf_path.exists():
                paf_path.unlink()

    def _transfer_assignments(
        self,
        blocks: list[SyntenyBlock],
        ref_assignments: dict[str, list[tuple[int, int, str]]],
    ) -> list[SubgenomeAssignment]:
        """Transfer subgenome assignments via synteny blocks.

        Parameters
        ----------
        blocks : list[SyntenyBlock]
            Synteny blocks.
        ref_assignments : dict
            Reference subgenome assignments.

        Returns
        -------
        list[SubgenomeAssignment]
            Transferred assignments.
        """
        assignments = []

        for block in blocks:
            # Skip blocks not meeting criteria
            if block.query_length < self.params.min_block_size:
                continue

            # Find reference assignment for this block's reference region
            ref_chrom_assignments = ref_assignments.get(block.ref_chrom, [])

            # Find overlapping reference assignments
            overlapping = []
            for start, end, sg in ref_chrom_assignments:
                if start < block.ref_end and end > block.ref_start:
                    overlap_start = max(start, block.ref_start)
                    overlap_end = min(end, block.ref_end)
                    overlap_length = overlap_end - overlap_start
                    overlapping.append((sg, overlap_length))

            if not overlapping:
                continue

            # Determine subgenome by majority vote weighted by overlap length
            sg_lengths: dict[str, int] = defaultdict(int)
            for sg, length in overlapping:
                sg_lengths[sg] += length

            total_overlap = sum(sg_lengths.values())
            if total_overlap == 0:
                continue

            # Get majority subgenome
            majority_sg = max(sg_lengths, key=sg_lengths.get)
            proportion = sg_lengths[majority_sg] / total_overlap

            # Calculate confidence based on proportion and block quality
            confidence = self._calculate_confidence(
                proportion=proportion,
                block=block,
                total_overlap=total_overlap,
            )

            assignments.append(
                SubgenomeAssignment(
                    chrom=block.query_chrom,
                    start=block.query_start,
                    end=block.query_end,
                    subgenome=majority_sg,
                    confidence=confidence,
                    evidence="synteny",
                    evidence_details={
                        "block_id": block.block_id,
                        "ref_chrom": block.ref_chrom,
                        "ref_start": block.ref_start,
                        "ref_end": block.ref_end,
                        "identity": block.identity,
                        "n_anchors": block.n_anchors,
                        "proportion": proportion,
                        "overlap_lengths": dict(sg_lengths),
                    },
                )
            )

        logger.info(f"Transferred {len(assignments)} subgenome assignments")
        return assignments

    def _calculate_confidence(
        self,
        proportion: float,
        block: SyntenyBlock,
        total_overlap: int,
    ) -> float:
        """Calculate confidence score for an assignment.

        Parameters
        ----------
        proportion : float
            Proportion of overlap from majority subgenome.
        block : SyntenyBlock
            Synteny block.
        total_overlap : int
            Total overlap length.

        Returns
        -------
        float
            Confidence score (0-1).
        """
        # Base confidence from proportion
        confidence = 0.5 * proportion

        # Bonus for identity
        if block.identity > 0:
            confidence += 0.2 * block.identity

        # Bonus for block size
        size_factor = min(1.0, block.query_length / 1_000_000)
        confidence += 0.2 * size_factor

        # Bonus for number of anchors
        if block.n_anchors >= self.params.min_genes:
            anchor_factor = min(1.0, block.n_anchors / 50)
            confidence += 0.1 * anchor_factor

        return round(min(confidence, 1.0), 3)

    def _merge_adjacent_assignments(
        self,
        assignments: list[SubgenomeAssignment],
    ) -> list[SubgenomeAssignment]:
        """Merge adjacent assignments with same subgenome.

        Parameters
        ----------
        assignments : list[SubgenomeAssignment]
            Assignments to merge.

        Returns
        -------
        list[SubgenomeAssignment]
            Merged assignments.
        """
        if not assignments:
            return []

        # Group by chromosome
        by_chrom: dict[str, list[SubgenomeAssignment]] = defaultdict(list)
        for a in assignments:
            by_chrom[a.chrom].append(a)

        merged = []

        for _chrom, chrom_assignments in by_chrom.items():
            # Sort by position
            sorted_assignments = sorted(chrom_assignments, key=lambda x: x.start)

            current = sorted_assignments[0]
            current_details = current.evidence_details or {}
            current_confidences = [current.confidence]

            for next_a in sorted_assignments[1:]:
                gap = next_a.start - current.end
                same_sg = current.subgenome == next_a.subgenome

                if same_sg and gap <= self.params.merge_distance:
                    # Merge
                    current = SubgenomeAssignment(
                        chrom=current.chrom,
                        start=current.start,
                        end=next_a.end,
                        subgenome=current.subgenome,
                        confidence=current.confidence,  # Will update
                        evidence="synteny",
                        evidence_details={
                            "merged_blocks": current_details.get("merged_blocks", 1) + 1,
                        },
                    )
                    current_confidences.append(next_a.confidence)
                else:
                    # Finalize current and start new
                    current = SubgenomeAssignment(
                        chrom=current.chrom,
                        start=current.start,
                        end=current.end,
                        subgenome=current.subgenome,
                        confidence=round(float(np.mean(current_confidences)), 3),
                        evidence=current.evidence,
                        evidence_details=current.evidence_details,
                    )
                    merged.append(current)

                    current = next_a
                    current_details = next_a.evidence_details or {}
                    current_confidences = [next_a.confidence]

            # Add last assignment
            current = SubgenomeAssignment(
                chrom=current.chrom,
                start=current.start,
                end=current.end,
                subgenome=current.subgenome,
                confidence=round(float(np.mean(current_confidences)), 3),
                evidence=current.evidence,
                evidence_details=current.evidence_details,
            )
            merged.append(current)

        logger.info(
            f"Merged {len(assignments)} assignments into {len(merged)} regions"
        )
        return sorted(merged, key=lambda x: (x.chrom, x.start))


def assign_by_synteny(
    synteny_blocks: Path | str | list[SyntenyBlock],
    reference_assignments: Path | str,
    config: SubgenomeConfig | None = None,
    min_block_size: int = 50_000,
    min_genes: int = 5,
) -> SubgenomeAssignmentResult:
    """Convenience function for synteny-based assignment.

    Parameters
    ----------
    synteny_blocks : Path, str, or list[SyntenyBlock]
        Synteny blocks.
    reference_assignments : Path or str
        Reference subgenome assignments BED file.
    config : SubgenomeConfig, optional
        Subgenome configuration (defaults to maize).
    min_block_size : int
        Minimum block size.
    min_genes : int
        Minimum genes/anchors.

    Returns
    -------
    SubgenomeAssignmentResult
        Assignment result.

    Examples
    --------
    >>> result = assign_by_synteny(
    ...     "alignment.paf",
    ...     "B73_subgenomes.bed",
    ... )
    >>> print(f"Assigned {result.n_assignments} regions")
    """
    if config is None:
        config = SubgenomeConfig.maize_default()

    assigner = SyntenySubgenomeAssigner(
        config=config,
        min_block_size=min_block_size,
        min_genes=min_genes,
    )

    return assigner.assign(
        synteny_blocks=synteny_blocks,
        reference_assignments=reference_assignments,
    )
