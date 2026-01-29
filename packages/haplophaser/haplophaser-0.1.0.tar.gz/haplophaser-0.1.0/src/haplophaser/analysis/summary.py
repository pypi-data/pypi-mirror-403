"""Genome-wide summary statistics for haplotype proportions.

This module provides comprehensive summary statistics at both
sample and population levels.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from haplophaser.proportion.blocks import BlockResults
    from haplophaser.proportion.breakpoints import BreakpointResults
    from haplophaser.proportion.results import ProportionResults

logger = logging.getLogger(__name__)


@dataclass
class SampleSummary:
    """Summary statistics for a single sample.

    Attributes:
        sample: Sample name
        genome_size: Total genome size analyzed (bp)
        founder_proportions: Genome-wide founder proportions
        chromosome_proportions: Per-chromosome founder proportions
        n_blocks: Total number of haplotype blocks
        n_breakpoints: Total number of ancestry breakpoints
        mean_block_size: Mean block size (bp)
        max_block_size: Maximum block size per founder
        heterozygosity: Proportion of mixed/transition regions
        coverage: Proportion of genome with confident calls
        n_markers: Total number of markers analyzed
        n_windows: Total number of windows
    """

    sample: str
    genome_size: int = 0
    founder_proportions: dict[str, float] = field(default_factory=dict)
    chromosome_proportions: dict[str, dict[str, float]] = field(default_factory=dict)
    n_blocks: int = 0
    n_breakpoints: int = 0
    mean_block_size: float = 0.0
    max_block_size: dict[str, int] = field(default_factory=dict)
    heterozygosity: float = 0.0
    coverage: float = 0.0
    n_markers: int = 0
    n_windows: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "sample": self.sample,
            "genome_size": self.genome_size,
            "founder_proportions": self.founder_proportions.copy(),
            "chromosome_proportions": {
                k: v.copy() for k, v in self.chromosome_proportions.items()
            },
            "n_blocks": self.n_blocks,
            "n_breakpoints": self.n_breakpoints,
            "mean_block_size": self.mean_block_size,
            "max_block_size": self.max_block_size.copy(),
            "heterozygosity": self.heterozygosity,
            "coverage": self.coverage,
            "n_markers": self.n_markers,
            "n_windows": self.n_windows,
        }

    def to_row(self) -> dict:
        """Convert to a flat dictionary suitable for DataFrame row."""
        row = {
            "sample": self.sample,
            "genome_size": self.genome_size,
            "n_blocks": self.n_blocks,
            "n_breakpoints": self.n_breakpoints,
            "mean_block_size": self.mean_block_size,
            "heterozygosity": self.heterozygosity,
            "coverage": self.coverage,
            "n_markers": self.n_markers,
            "n_windows": self.n_windows,
        }
        for founder, prop in self.founder_proportions.items():
            row[f"{founder}_proportion"] = prop
        for founder, size in self.max_block_size.items():
            row[f"{founder}_max_block"] = size
        return row


@dataclass
class PopulationSummary:
    """Summary statistics for a population of samples.

    Attributes:
        population: Population name
        n_samples: Number of samples
        mean_founder_proportions: Mean founder proportions across samples
        std_founder_proportions: Standard deviation of founder proportions
        founder_proportion_range: Min/max founder proportions
        breakpoint_density: Breakpoints per Mb per chromosome
        shared_blocks: List of shared haplotype block descriptions
        sample_names: List of sample names in population
    """

    population: str
    n_samples: int = 0
    mean_founder_proportions: dict[str, float] = field(default_factory=dict)
    std_founder_proportions: dict[str, float] = field(default_factory=dict)
    founder_proportion_range: dict[str, tuple[float, float]] = field(default_factory=dict)
    breakpoint_density: dict[str, float] = field(default_factory=dict)
    shared_blocks: list[dict] = field(default_factory=list)
    sample_names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "population": self.population,
            "n_samples": self.n_samples,
            "mean_founder_proportions": self.mean_founder_proportions.copy(),
            "std_founder_proportions": self.std_founder_proportions.copy(),
            "founder_proportion_range": {
                k: list(v) for k, v in self.founder_proportion_range.items()
            },
            "breakpoint_density": self.breakpoint_density.copy(),
            "shared_blocks": self.shared_blocks.copy(),
            "sample_names": self.sample_names.copy(),
        }


class GenomeSummary:
    """Generate comprehensive genome-wide summary statistics.

    Computes per-sample and population-level summaries from
    proportion estimation results.
    """

    def __init__(
        self,
        proportions: ProportionResults,
        blocks: BlockResults | None = None,
        breakpoints: BreakpointResults | None = None,
    ) -> None:
        """Initialize summary generator.

        Args:
            proportions: Proportion estimation results
            blocks: Optional haplotype block results
            breakpoints: Optional breakpoint detection results
        """
        self.proportions = proportions
        self.blocks = blocks
        self.breakpoints = breakpoints
        self.founders = proportions.founders

        self._sample_summaries: dict[str, SampleSummary] = {}

    def by_sample(self, sample_name: str) -> SampleSummary:
        """Get summary for a specific sample.

        Args:
            sample_name: Name of the sample

        Returns:
            SampleSummary object
        """
        if sample_name in self._sample_summaries:
            return self._sample_summaries[sample_name]

        sample_props = self.proportions.get_sample(sample_name)
        if sample_props is None:
            return SampleSummary(sample=sample_name)

        # Calculate basic statistics
        genome_size = sum(w.end - w.start for w in sample_props.windows)
        n_markers = sample_props.total_markers
        n_windows = sample_props.total_windows

        # Genome-wide proportions
        founder_proportions = sample_props.genome_wide.copy()

        # Per-chromosome proportions
        chromosome_proportions = {}
        for chrom in sample_props.get_chromosomes():
            chrom_windows = sample_props.get_chromosome_windows(chrom)
            if not chrom_windows:
                continue

            chrom_markers = sum(w.n_markers for w in chrom_windows)
            chrom_props = dict.fromkeys(self.founders, 0.0)

            if chrom_markers > 0:
                for window in chrom_windows:
                    for f in self.founders:
                        chrom_props[f] += window.proportions.get(f, 0.0) * window.n_markers
                for f in self.founders:
                    chrom_props[f] /= chrom_markers

            chromosome_proportions[chrom] = chrom_props

        # Block statistics
        n_blocks = 0
        mean_block_size = 0.0
        max_block_size = dict.fromkeys(self.founders, 0)

        if self.blocks is not None:
            sample_blocks = self.blocks.get_sample(sample_name)
            if sample_blocks:
                n_blocks = sample_blocks.n_blocks
                if n_blocks > 0:
                    block_sizes = [b.length for b in sample_blocks.blocks]
                    mean_block_size = np.mean(block_sizes)

                    for block in sample_blocks.blocks:
                        founder = block.dominant_founder
                        if founder in max_block_size:
                            max_block_size[founder] = max(
                                max_block_size[founder], block.length
                            )

        # Breakpoint statistics
        n_breakpoints = 0
        if self.breakpoints is not None:
            sample_bps = self.breakpoints.get_sample(sample_name)
            if sample_bps:
                n_breakpoints = sample_bps.n_breakpoints

        # Heterozygosity (proportion of windows that are mixed)
        n_mixed = sum(1 for w in sample_props.windows if w.is_mixed)
        heterozygosity = n_mixed / n_windows if n_windows > 0 else 0.0

        # Coverage (proportion of genome with at least 1 marker)
        covered_size = sum(w.end - w.start for w in sample_props.windows if w.n_markers > 0)
        coverage = covered_size / genome_size if genome_size > 0 else 0.0

        summary = SampleSummary(
            sample=sample_name,
            genome_size=genome_size,
            founder_proportions=founder_proportions,
            chromosome_proportions=chromosome_proportions,
            n_blocks=n_blocks,
            n_breakpoints=n_breakpoints,
            mean_block_size=mean_block_size,
            max_block_size=max_block_size,
            heterozygosity=heterozygosity,
            coverage=coverage,
            n_markers=n_markers,
            n_windows=n_windows,
        )

        self._sample_summaries[sample_name] = summary
        return summary

    def by_population(
        self,
        population_name: str,
        sample_names: list[str] | None = None,
    ) -> PopulationSummary:
        """Get summary for a population of samples.

        Args:
            population_name: Name for this population
            sample_names: List of sample names (default: all samples)

        Returns:
            PopulationSummary object
        """
        if sample_names is None:
            sample_names = self.proportions.sample_names

        if not sample_names:
            return PopulationSummary(population=population_name)

        # Get individual summaries
        summaries = [self.by_sample(s) for s in sample_names]

        # Aggregate founder proportions
        founder_props = {f: [] for f in self.founders}
        for summary in summaries:
            for f in self.founders:
                founder_props[f].append(summary.founder_proportions.get(f, 0.0))

        mean_props = {f: np.mean(props) for f, props in founder_props.items()}
        std_props = {f: np.std(props) for f, props in founder_props.items()}
        range_props = {
            f: (float(np.min(props)), float(np.max(props)))
            for f, props in founder_props.items()
        }

        # Breakpoint density per chromosome
        breakpoint_density = {}
        if self.breakpoints is not None:
            chrom_lengths = {}
            chrom_bp_counts = {}

            for sample in sample_names:
                sample_props = self.proportions.get_sample(sample)
                sample_bps = self.breakpoints.get_sample(sample)

                if sample_props:
                    for chrom in sample_props.get_chromosomes():
                        windows = sample_props.get_chromosome_windows(chrom)
                        if windows:
                            length = max(w.end for w in windows) - min(w.start for w in windows)
                            if chrom not in chrom_lengths:
                                chrom_lengths[chrom] = []
                            chrom_lengths[chrom].append(length)

                if sample_bps:
                    for bp in sample_bps.breakpoints:
                        if bp.chrom not in chrom_bp_counts:
                            chrom_bp_counts[bp.chrom] = 0
                        chrom_bp_counts[bp.chrom] += 1

            for chrom, lengths in chrom_lengths.items():
                avg_length = np.mean(lengths)
                n_bps = chrom_bp_counts.get(chrom, 0)
                # Breakpoints per Mb
                if avg_length > 0:
                    breakpoint_density[chrom] = n_bps / (avg_length / 1_000_000) / len(sample_names)

        return PopulationSummary(
            population=population_name,
            n_samples=len(sample_names),
            mean_founder_proportions=mean_props,
            std_founder_proportions=std_props,
            founder_proportion_range=range_props,
            breakpoint_density=breakpoint_density,
            sample_names=sample_names,
        )

    def all_samples(self) -> list[SampleSummary]:
        """Get summaries for all samples.

        Returns:
            List of SampleSummary objects
        """
        return [self.by_sample(s) for s in self.proportions.sample_names]

    def summary_table(self) -> list[dict]:
        """Generate summary table as list of dictionaries.

        Suitable for creating a pandas DataFrame.

        Returns:
            List of dictionaries, one per sample
        """
        return [self.by_sample(s).to_row() for s in self.proportions.sample_names]

    def founder_proportion_matrix(self) -> tuple[list[str], list[str], np.ndarray]:
        """Get founder proportions as a matrix.

        Returns:
            Tuple of (sample_names, founder_names, proportion_matrix)
        """
        samples = self.proportions.sample_names
        matrix = np.zeros((len(samples), len(self.founders)))

        for i, sample in enumerate(samples):
            sample_props = self.proportions.get_sample(sample)
            if sample_props:
                for j, founder in enumerate(self.founders):
                    matrix[i, j] = sample_props.genome_wide.get(founder, 0.0)

        return samples, self.founders, matrix

    def chromosome_coverage(self) -> dict[str, dict[str, float]]:
        """Get coverage statistics per chromosome.

        Returns:
            Dict mapping chromosomes to coverage metrics
        """
        coverage = {}

        for sample in self.proportions:
            for chrom in sample.get_chromosomes():
                if chrom not in coverage:
                    coverage[chrom] = {
                        "total_length": 0,
                        "covered_length": 0,
                        "n_markers": 0,
                        "n_samples": 0,
                    }

                windows = sample.get_chromosome_windows(chrom)
                if windows:
                    length = max(w.end for w in windows) - min(w.start for w in windows)
                    covered = sum(w.end - w.start for w in windows if w.n_markers > 0)
                    markers = sum(w.n_markers for w in windows)

                    coverage[chrom]["total_length"] += length
                    coverage[chrom]["covered_length"] += covered
                    coverage[chrom]["n_markers"] += markers
                    coverage[chrom]["n_samples"] += 1

        # Calculate averages
        for chrom, stats in coverage.items():
            if stats["n_samples"] > 0:
                stats["avg_length"] = stats["total_length"] / stats["n_samples"]
                stats["avg_coverage"] = stats["covered_length"] / stats["total_length"] if stats["total_length"] > 0 else 0
                stats["avg_markers"] = stats["n_markers"] / stats["n_samples"]
                stats["marker_density"] = stats["n_markers"] / (stats["total_length"] / 1_000_000) if stats["total_length"] > 0 else 0

        return coverage

    def to_dict(self) -> dict:
        """Convert full summary to dictionary.

        Returns:
            Dict with all summary information
        """
        samples = self.all_samples()
        population = self.by_population("all", self.proportions.sample_names)

        return {
            "n_samples": len(samples),
            "founders": self.founders,
            "samples": [s.to_dict() for s in samples],
            "population": population.to_dict(),
            "chromosome_coverage": self.chromosome_coverage(),
        }
