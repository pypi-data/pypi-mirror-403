"""Haplotype block calling from proportion estimates.

This module identifies contiguous genomic regions with consistent
founder ancestry based on window proportion estimates.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from haplophaser.proportion.results import ProportionResults, SampleProportions

logger = logging.getLogger(__name__)


@dataclass
class HaplotypeBlock:
    """A contiguous region of consistent founder ancestry.

    Attributes:
        chrom: Chromosome name
        start: Block start position (0-based)
        end: Block end position (exclusive)
        dominant_founder: Primary founder for this block
        mean_proportion: Mean proportion of dominant founder
        min_proportion: Minimum proportion in block
        max_proportion: Maximum proportion in block
        n_windows: Number of windows in this block
        confidence: Confidence score for the block call
        is_mixed: Whether this is a mixed ancestry region
        secondary_founders: Dict of other founders with significant proportions
    """

    chrom: str
    start: int
    end: int
    dominant_founder: str
    mean_proportion: float
    min_proportion: float
    max_proportion: float
    n_windows: int = 1
    confidence: float = 1.0
    is_mixed: bool = False
    secondary_founders: dict[str, float] = field(default_factory=dict)

    @property
    def length(self) -> int:
        """Get block length in base pairs."""
        return self.end - self.start

    @property
    def midpoint(self) -> int:
        """Get block midpoint."""
        return (self.start + self.end) // 2

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "chrom": self.chrom,
            "start": self.start,
            "end": self.end,
            "dominant_founder": self.dominant_founder,
            "mean_proportion": self.mean_proportion,
            "min_proportion": self.min_proportion,
            "max_proportion": self.max_proportion,
            "n_windows": self.n_windows,
            "confidence": self.confidence,
            "is_mixed": self.is_mixed,
            "secondary_founders": self.secondary_founders.copy(),
        }


@dataclass
class SampleBlocks:
    """Collection of haplotype blocks for a single sample.

    Attributes:
        sample_name: Name of the sample
        blocks: List of haplotype blocks
        founders: List of founder names
    """

    sample_name: str
    blocks: list[HaplotypeBlock] = field(default_factory=list)
    founders: list[str] = field(default_factory=list)

    def add_block(self, block: HaplotypeBlock) -> None:
        """Add a haplotype block."""
        self.blocks.append(block)

    @property
    def n_blocks(self) -> int:
        """Get total number of blocks."""
        return len(self.blocks)

    def get_chromosome_blocks(self, chrom: str) -> list[HaplotypeBlock]:
        """Get blocks for a specific chromosome."""
        return [b for b in self.blocks if b.chrom == chrom]

    def get_chromosomes(self) -> list[str]:
        """Get list of chromosomes with blocks."""
        seen = set()
        chroms = []
        for b in self.blocks:
            if b.chrom not in seen:
                seen.add(b.chrom)
                chroms.append(b.chrom)
        return chroms

    def get_founder_coverage(self) -> dict[str, int]:
        """Get total base pairs covered by each founder."""
        coverage = dict.fromkeys(self.founders, 0)
        for block in self.blocks:
            if block.dominant_founder in coverage:
                coverage[block.dominant_founder] += block.length
        return coverage

    def get_block_at_position(self, chrom: str, pos: int) -> HaplotypeBlock | None:
        """Get the block containing a specific position."""
        for block in self.blocks:
            if block.chrom == chrom and block.start <= pos < block.end:
                return block
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "sample_name": self.sample_name,
            "founders": self.founders.copy(),
            "blocks": [b.to_dict() for b in self.blocks],
        }


@dataclass
class BlockResults:
    """Collection of haplotype blocks for multiple samples.

    Attributes:
        samples: Dict mapping sample names to their blocks
        founders: List of founder names
        min_proportion: Threshold used for block calling
        merge_gap: Gap threshold used for merging blocks
    """

    samples: dict[str, SampleBlocks] = field(default_factory=dict)
    founders: list[str] = field(default_factory=list)
    min_proportion: float = 0.7
    merge_gap: int = 0

    def add_sample(self, sample_blocks: SampleBlocks) -> None:
        """Add a sample's blocks."""
        self.samples[sample_blocks.sample_name] = sample_blocks

    def get_sample(self, sample_name: str) -> SampleBlocks | None:
        """Get blocks for a specific sample."""
        return self.samples.get(sample_name)

    @property
    def sample_names(self) -> list[str]:
        """Get list of sample names."""
        return list(self.samples.keys())

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "founders": self.founders.copy(),
            "min_proportion": self.min_proportion,
            "merge_gap": self.merge_gap,
            "samples": {name: s.to_dict() for name, s in self.samples.items()},
        }


class HaplotypeBlockCaller:
    """Call haplotype blocks from proportion estimates.

    Identifies contiguous regions where a single founder dominates
    the ancestry, optionally merging nearby blocks.
    """

    def __init__(
        self,
        min_proportion: float = 0.7,
        merge_gap: int = 0,
        min_block_windows: int = 1,
        mixed_threshold: float = 0.3,
    ) -> None:
        """Initialize the block caller.

        Args:
            min_proportion: Minimum proportion to call a block
            merge_gap: Maximum gap (bp) to merge adjacent blocks
            min_block_windows: Minimum windows to form a block
            mixed_threshold: If max - second_max < this, mark as mixed
        """
        self.min_proportion = min_proportion
        self.merge_gap = merge_gap
        self.min_block_windows = min_block_windows
        self.mixed_threshold = mixed_threshold

    def call_blocks(self, results: ProportionResults) -> BlockResults:
        """Call haplotype blocks from proportion results.

        Args:
            results: Proportion estimation results

        Returns:
            BlockResults with called blocks for all samples
        """
        logger.info(
            f"Calling haplotype blocks (min_prop={self.min_proportion}, "
            f"merge_gap={self.merge_gap})"
        )

        block_results = BlockResults(
            founders=results.founders,
            min_proportion=self.min_proportion,
            merge_gap=self.merge_gap,
        )

        for sample in results:
            sample_blocks = self._call_sample_blocks(sample, results.founders)
            block_results.add_sample(sample_blocks)

        return block_results

    def _call_sample_blocks(
        self,
        sample: SampleProportions,
        founders: list[str],
    ) -> SampleBlocks:
        """Call blocks for a single sample.

        Args:
            sample: Sample proportion results
            founders: List of founder names

        Returns:
            SampleBlocks with called blocks
        """
        sample_blocks = SampleBlocks(
            sample_name=sample.sample_name,
            founders=founders,
        )

        # Process each chromosome
        for chrom in sample.get_chromosomes():
            windows = sample.get_chromosome_windows(chrom)
            if not windows:
                continue

            # Sort by position
            windows = sorted(windows, key=lambda w: w.start)

            # Call blocks
            chrom_blocks = self._call_chromosome_blocks(windows, founders)

            # Merge nearby blocks if configured
            if self.merge_gap > 0:
                chrom_blocks = self._merge_blocks(chrom_blocks)

            # Filter by minimum windows
            for block in chrom_blocks:
                if block.n_windows >= self.min_block_windows:
                    sample_blocks.add_block(block)

        return sample_blocks

    def _call_chromosome_blocks(
        self,
        windows: list,
        founders: list[str],
    ) -> list[HaplotypeBlock]:
        """Call blocks for a single chromosome.

        Args:
            windows: Sorted list of windows for this chromosome
            founders: List of founder names

        Returns:
            List of haplotype blocks
        """
        if not windows:
            return []

        blocks = []
        current_block = None

        for window in windows:
            # Get dominant founder
            dominant = window.dominant_founder
            proportion = window.proportions.get(dominant, 0.0)

            # Check if this meets threshold
            meets_threshold = proportion >= self.min_proportion

            # Check if mixed ancestry
            sorted_props = sorted(window.proportions.values(), reverse=True)
            is_mixed = False
            if len(sorted_props) >= 2:
                is_mixed = (sorted_props[0] - sorted_props[1]) < self.mixed_threshold

            if meets_threshold:
                if (
                    current_block is None
                    or current_block.dominant_founder != dominant
                    or current_block.chrom != window.chrom
                ):
                    # Start new block
                    if current_block is not None:
                        blocks.append(current_block)

                    # Calculate secondary founders
                    secondary = {}
                    for f, p in window.proportions.items():
                        if f != dominant and p > 0.1:
                            secondary[f] = p

                    current_block = HaplotypeBlock(
                        chrom=window.chrom,
                        start=window.start,
                        end=window.end,
                        dominant_founder=dominant,
                        mean_proportion=proportion,
                        min_proportion=proportion,
                        max_proportion=proportion,
                        n_windows=1,
                        is_mixed=is_mixed,
                        secondary_founders=secondary,
                    )
                else:
                    # Extend current block
                    current_block.end = window.end
                    current_block.n_windows += 1
                    current_block.min_proportion = min(
                        current_block.min_proportion, proportion
                    )
                    current_block.max_proportion = max(
                        current_block.max_proportion, proportion
                    )
                    current_block.is_mixed = current_block.is_mixed or is_mixed

                    # Update mean proportion
                    n = current_block.n_windows
                    current_block.mean_proportion = (
                        current_block.mean_proportion * (n - 1) + proportion
                    ) / n

                    # Update secondary founders
                    for f, p in window.proportions.items():
                        if f != dominant and p > 0.1:
                            old_p = current_block.secondary_founders.get(f, 0.0)
                            current_block.secondary_founders[f] = (
                                old_p * (n - 1) + p
                            ) / n

            else:
                # Below threshold - close current block
                if current_block is not None:
                    blocks.append(current_block)
                    current_block = None

        # Close final block
        if current_block is not None:
            blocks.append(current_block)

        # Calculate confidence for each block
        for block in blocks:
            block.confidence = self._calculate_block_confidence(block)

        return blocks

    def _merge_blocks(self, blocks: list[HaplotypeBlock]) -> list[HaplotypeBlock]:
        """Merge nearby blocks with the same dominant founder.

        Args:
            blocks: List of blocks to potentially merge

        Returns:
            List of merged blocks
        """
        if len(blocks) < 2:
            return blocks

        merged = []
        current = blocks[0]

        for next_block in blocks[1:]:
            # Check if can merge
            can_merge = (
                current.chrom == next_block.chrom
                and current.dominant_founder == next_block.dominant_founder
                and (next_block.start - current.end) <= self.merge_gap
            )

            if can_merge:
                # Merge blocks
                total_windows = current.n_windows + next_block.n_windows
                current = HaplotypeBlock(
                    chrom=current.chrom,
                    start=current.start,
                    end=next_block.end,
                    dominant_founder=current.dominant_founder,
                    mean_proportion=(
                        current.mean_proportion * current.n_windows
                        + next_block.mean_proportion * next_block.n_windows
                    )
                    / total_windows,
                    min_proportion=min(
                        current.min_proportion, next_block.min_proportion
                    ),
                    max_proportion=max(
                        current.max_proportion, next_block.max_proportion
                    ),
                    n_windows=total_windows,
                    is_mixed=current.is_mixed or next_block.is_mixed,
                    secondary_founders={
                        **current.secondary_founders,
                        **next_block.secondary_founders,
                    },
                )
            else:
                merged.append(current)
                current = next_block

        merged.append(current)
        return merged

    def _calculate_block_confidence(self, block: HaplotypeBlock) -> float:
        """Calculate confidence score for a block.

        Based on consistency of proportion across windows and
        separation from secondary founders.

        Args:
            block: Block to score

        Returns:
            Confidence score between 0 and 1
        """
        # Factor 1: Consistency (low variance = high confidence)
        range_factor = 1.0 - (block.max_proportion - block.min_proportion)

        # Factor 2: Mean proportion strength
        strength_factor = block.mean_proportion

        # Factor 3: Separation from secondary founders
        max_secondary = max(block.secondary_founders.values()) if block.secondary_founders else 0.0
        separation_factor = block.mean_proportion - max_secondary

        # Combine factors
        confidence = (range_factor + strength_factor + separation_factor) / 3.0

        # Penalty for mixed blocks
        if block.is_mixed:
            confidence *= 0.8

        return max(0.0, min(1.0, confidence))


def call_haplotype_blocks(
    results: ProportionResults,
    min_proportion: float = 0.7,
    merge_gap: int = 0,
) -> BlockResults:
    """Call haplotype blocks from proportion results.

    Convenience function wrapping HaplotypeBlockCaller.

    Args:
        results: Proportion estimation results
        min_proportion: Minimum proportion threshold
        merge_gap: Maximum gap to merge adjacent blocks

    Returns:
        BlockResults with called blocks
    """
    caller = HaplotypeBlockCaller(
        min_proportion=min_proportion,
        merge_gap=merge_gap,
    )
    return caller.call_blocks(results)
