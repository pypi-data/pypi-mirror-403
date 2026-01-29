"""Ancestry painting for genome-wide visualization.

This module creates genome-wide ancestry matrices for visualization
in heatmaps and chromosome painting plots.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from haplophaser.proportion.hmm import HMMResults
    from haplophaser.proportion.results import ProportionResults

logger = logging.getLogger(__name__)


@dataclass
class GenomicBin:
    """A genomic bin for painting.

    Attributes:
        chrom: Chromosome name
        start: Bin start position
        end: Bin end position
        index: Global bin index
    """

    chrom: str
    start: int
    end: int
    index: int = 0

    @property
    def midpoint(self) -> int:
        """Get bin midpoint."""
        return (self.start + self.end) // 2

    @property
    def length(self) -> int:
        """Get bin length."""
        return self.end - self.start


@dataclass
class AncestryPainting:
    """Genome-wide ancestry painting result.

    Attributes:
        samples: List of sample names
        founders: List of founder names
        bins: List of genomic bins
        matrix: Ancestry matrix (samples x bins)
        probabilities: Full probability matrix (samples x bins x founders)
        method: Painting method used
        resolution: Bin resolution in bp
    """

    samples: list[str]
    founders: list[str]
    bins: list[GenomicBin]
    matrix: np.ndarray  # Shape: (n_samples, n_bins), values are founder indices
    probabilities: np.ndarray | None = None  # Shape: (n_samples, n_bins, n_founders)
    method: str = "majority"
    resolution: int = 100000

    @property
    def n_samples(self) -> int:
        """Get number of samples."""
        return len(self.samples)

    @property
    def n_bins(self) -> int:
        """Get number of bins."""
        return len(self.bins)

    @property
    def n_founders(self) -> int:
        """Get number of founders."""
        return len(self.founders)

    def get_chromosomes(self) -> list[str]:
        """Get list of chromosomes in order."""
        seen = set()
        chroms = []
        for bin in self.bins:
            if bin.chrom not in seen:
                seen.add(bin.chrom)
                chroms.append(bin.chrom)
        return chroms

    def get_chromosome_bins(self, chrom: str) -> list[GenomicBin]:
        """Get bins for a specific chromosome."""
        return [b for b in self.bins if b.chrom == chrom]

    def get_sample_painting(self, sample: str) -> np.ndarray:
        """Get painting for a specific sample.

        Args:
            sample: Sample name

        Returns:
            Array of founder indices for each bin
        """
        if sample not in self.samples:
            return np.array([])
        idx = self.samples.index(sample)
        return self.matrix[idx]

    def get_sample_probabilities(self, sample: str) -> np.ndarray | None:
        """Get probability matrix for a specific sample.

        Args:
            sample: Sample name

        Returns:
            Array of shape (n_bins, n_founders) or None
        """
        if self.probabilities is None or sample not in self.samples:
            return None
        idx = self.samples.index(sample)
        return self.probabilities[idx]

    def to_matrix(self) -> np.ndarray:
        """Get the painting matrix."""
        return self.matrix

    def to_dataframe_long(self) -> list[dict]:
        """Convert to long format suitable for plotting.

        Returns:
            List of dictionaries with sample, chrom, start, end, founder columns
        """
        rows = []
        for i, sample in enumerate(self.samples):
            for j, bin in enumerate(self.bins):
                founder_idx = int(self.matrix[i, j])
                founder = self.founders[founder_idx] if 0 <= founder_idx < len(self.founders) else "Unknown"
                row = {
                    "sample": sample,
                    "chrom": bin.chrom,
                    "start": bin.start,
                    "end": bin.end,
                    "founder": founder,
                    "founder_index": founder_idx,
                }
                if self.probabilities is not None:
                    for k, f in enumerate(self.founders):
                        row[f"{f}_prob"] = float(self.probabilities[i, j, k])
                rows.append(row)
        return rows

    def to_hdf5(self, path: str | Path) -> None:
        """Save to HDF5 format for efficient storage.

        Args:
            path: Output file path
        """
        import h5py

        path = Path(path)
        with h5py.File(path, "w") as f:
            # Metadata
            f.attrs["method"] = self.method
            f.attrs["resolution"] = self.resolution
            f.attrs["n_samples"] = self.n_samples
            f.attrs["n_bins"] = self.n_bins
            f.attrs["n_founders"] = self.n_founders

            # String datasets
            f.create_dataset("samples", data=np.array(self.samples, dtype="S"))
            f.create_dataset("founders", data=np.array(self.founders, dtype="S"))

            # Bin info
            chroms = [b.chrom for b in self.bins]
            starts = [b.start for b in self.bins]
            ends = [b.end for b in self.bins]
            f.create_dataset("bin_chroms", data=np.array(chroms, dtype="S"))
            f.create_dataset("bin_starts", data=np.array(starts))
            f.create_dataset("bin_ends", data=np.array(ends))

            # Matrix
            f.create_dataset("matrix", data=self.matrix, compression="gzip")

            # Probabilities
            if self.probabilities is not None:
                f.create_dataset(
                    "probabilities",
                    data=self.probabilities,
                    compression="gzip",
                )

        logger.info(f"Saved painting to {path}")

    @classmethod
    def from_hdf5(cls, path: str | Path) -> AncestryPainting:
        """Load from HDF5 format.

        Args:
            path: Input file path

        Returns:
            AncestryPainting object
        """
        import h5py

        path = Path(path)
        with h5py.File(path, "r") as f:
            method = f.attrs["method"]
            resolution = f.attrs["resolution"]

            samples = [s.decode() for s in f["samples"][:]]
            founders = [s.decode() for s in f["founders"][:]]

            chroms = [s.decode() for s in f["bin_chroms"][:]]
            starts = f["bin_starts"][:]
            ends = f["bin_ends"][:]

            bins = [
                GenomicBin(chrom=c, start=int(s), end=int(e), index=i)
                for i, (c, s, e) in enumerate(zip(chroms, starts, ends, strict=False))
            ]

            matrix = f["matrix"][:]

            probabilities = None
            if "probabilities" in f:
                probabilities = f["probabilities"][:]

        return cls(
            samples=samples,
            founders=founders,
            bins=bins,
            matrix=matrix,
            probabilities=probabilities,
            method=method,
            resolution=resolution,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "samples": self.samples,
            "founders": self.founders,
            "method": self.method,
            "resolution": self.resolution,
            "n_bins": self.n_bins,
            "chromosomes": self.get_chromosomes(),
        }


class AncestryPainter:
    """Create genome-wide ancestry paintings.

    Converts proportion results to a binned matrix suitable
    for visualization as heatmaps or chromosome paintings.
    """

    def __init__(
        self,
        resolution: int = 100000,
        method: str = "majority",
    ) -> None:
        """Initialize the painter.

        Args:
            resolution: Bin size in bp
            method: Painting method ('majority', 'probability', 'hmm')
        """
        self.resolution = resolution
        self.method = method

    def paint(
        self,
        proportions: ProportionResults,
        chromosome_lengths: dict[str, int] | None = None,
    ) -> AncestryPainting:
        """Create ancestry painting from proportion results.

        Args:
            proportions: Proportion estimation results
            chromosome_lengths: Optional dict of chromosome lengths

        Returns:
            AncestryPainting object
        """
        logger.info(f"Creating ancestry painting (resolution={self.resolution}bp, method={self.method})")

        samples = proportions.sample_names
        founders = proportions.founders
        n_founders = len(founders)

        # Determine chromosome lengths from data if not provided
        if chromosome_lengths is None:
            chromosome_lengths = self._infer_chromosome_lengths(proportions)

        # Generate bins
        bins = self._generate_bins(chromosome_lengths)
        n_bins = len(bins)

        # Initialize matrices
        matrix = np.zeros((len(samples), n_bins), dtype=np.int8)
        probabilities = np.zeros((len(samples), n_bins, n_founders))

        # Fill matrices
        for i, sample_name in enumerate(samples):
            sample = proportions.get_sample(sample_name)
            if sample is None:
                continue

            self._paint_sample(sample, bins, founders, matrix[i], probabilities[i])

        return AncestryPainting(
            samples=samples,
            founders=founders,
            bins=bins,
            matrix=matrix,
            probabilities=probabilities,
            method=self.method,
            resolution=self.resolution,
        )

    def paint_from_hmm(
        self,
        hmm_results: HMMResults,
        chromosome_lengths: dict[str, int] | None = None,
    ) -> AncestryPainting:
        """Create ancestry painting from HMM results.

        Args:
            hmm_results: HMM inference results
            chromosome_lengths: Optional dict of chromosome lengths

        Returns:
            AncestryPainting object
        """
        logger.info("Creating ancestry painting from HMM results")

        samples = hmm_results.samples
        founders = hmm_results.founders
        states = hmm_results.states
        n_founders = len(founders)

        # Determine chromosome lengths
        if chromosome_lengths is None:
            chromosome_lengths = {}
            for result in hmm_results.results.values():
                if result.positions:
                    max_pos = max(result.positions)
                    if result.chrom not in chromosome_lengths:
                        chromosome_lengths[result.chrom] = max_pos + self.resolution
                    else:
                        chromosome_lengths[result.chrom] = max(
                            chromosome_lengths[result.chrom],
                            max_pos + self.resolution,
                        )

        # Generate bins
        bins = self._generate_bins(chromosome_lengths)
        n_bins = len(bins)

        # Initialize matrices
        matrix = np.zeros((len(samples), n_bins), dtype=np.int8)
        probabilities = np.zeros((len(samples), n_bins, n_founders))

        # State to founder mapping
        {s: i for i, s in enumerate(states)}

        for i, sample_name in enumerate(samples):
            for bin_idx, bin in enumerate(bins):
                result = hmm_results.get_result(sample_name, bin.chrom)
                if result is None:
                    continue

                # Find markers in this bin
                bin_mask = [
                    bin.start <= pos < bin.end for pos in result.positions
                ]
                if not any(bin_mask):
                    continue

                # Average posteriors in bin
                bin_posteriors = result.posteriors[bin_mask].mean(axis=0)

                # Convert state posteriors to founder probabilities
                founder_probs = np.zeros(n_founders)
                for state_idx, state in enumerate(states):
                    state_prob = bin_posteriors[state_idx]
                    # Parse state to get founder dosages
                    parts = state.split("/")
                    for part in parts:
                        if part in founders:
                            founder_idx = founders.index(part)
                            founder_probs[founder_idx] += state_prob / len(parts)

                probabilities[i, bin_idx] = founder_probs
                matrix[i, bin_idx] = np.argmax(founder_probs)

        return AncestryPainting(
            samples=samples,
            founders=founders,
            bins=bins,
            matrix=matrix,
            probabilities=probabilities,
            method="hmm",
            resolution=self.resolution,
        )

    def _infer_chromosome_lengths(
        self,
        proportions: ProportionResults,
    ) -> dict[str, int]:
        """Infer chromosome lengths from proportion data.

        Args:
            proportions: Proportion results

        Returns:
            Dict mapping chromosome names to lengths
        """
        lengths = {}

        for sample in proportions:
            for window in sample.windows:
                if window.chrom not in lengths:
                    lengths[window.chrom] = window.end
                else:
                    lengths[window.chrom] = max(lengths[window.chrom], window.end)

        # Round up to resolution
        return {
            chrom: ((length // self.resolution) + 1) * self.resolution
            for chrom, length in lengths.items()
        }

    def _generate_bins(
        self,
        chromosome_lengths: dict[str, int],
    ) -> list[GenomicBin]:
        """Generate genomic bins.

        Args:
            chromosome_lengths: Dict mapping chromosomes to lengths

        Returns:
            List of GenomicBin objects
        """
        bins = []
        global_idx = 0

        for chrom in sorted(chromosome_lengths.keys()):
            length = chromosome_lengths[chrom]
            pos = 0

            while pos < length:
                end = min(pos + self.resolution, length)
                bins.append(GenomicBin(
                    chrom=chrom,
                    start=pos,
                    end=end,
                    index=global_idx,
                ))
                global_idx += 1
                pos = end

        return bins

    def _paint_sample(
        self,
        sample,
        bins: list[GenomicBin],
        founders: list[str],
        matrix_row: np.ndarray,
        prob_row: np.ndarray,
    ) -> None:
        """Paint a single sample.

        Args:
            sample: SampleProportions object
            bins: List of bins
            founders: List of founder names
            matrix_row: Row to fill in matrix
            prob_row: Row to fill in probability matrix
        """
        # Build window lookup by chromosome
        windows_by_chrom: dict[str, list] = {}
        for window in sample.windows:
            if window.chrom not in windows_by_chrom:
                windows_by_chrom[window.chrom] = []
            windows_by_chrom[window.chrom].append(window)

        for window_list in windows_by_chrom.values():
            window_list.sort(key=lambda w: w.start)

        for bin_idx, bin in enumerate(bins):
            chrom_windows = windows_by_chrom.get(bin.chrom, [])
            if not chrom_windows:
                continue

            # Find overlapping windows
            overlapping = []
            for window in chrom_windows:
                if window.end <= bin.start:
                    continue
                if window.start >= bin.end:
                    break

                overlap_start = max(window.start, bin.start)
                overlap_end = min(window.end, bin.end)
                overlap = overlap_end - overlap_start

                if overlap > 0:
                    overlapping.append((window, overlap))

            if not overlapping:
                continue

            # Weighted average of proportions
            total_overlap = sum(o for _, o in overlapping)
            founder_probs = dict.fromkeys(founders, 0.0)

            for window, overlap in overlapping:
                weight = overlap / total_overlap
                for f in founders:
                    founder_probs[f] += window.proportions.get(f, 0.0) * weight

            # Fill probability row
            for f_idx, f in enumerate(founders):
                prob_row[bin_idx, f_idx] = founder_probs[f]

            # Fill matrix with majority founder
            if self.method == "majority":
                max_founder = max(founders, key=lambda f: founder_probs[f])
                matrix_row[bin_idx] = founders.index(max_founder)
            elif self.method == "probability":
                # Weighted random based on probabilities
                probs = np.array([founder_probs[f] for f in founders])
                if probs.sum() > 0:
                    probs /= probs.sum()
                    matrix_row[bin_idx] = np.random.choice(len(founders), p=probs)
                else:
                    matrix_row[bin_idx] = 0
            else:
                # Default to majority
                max_founder = max(founders, key=lambda f: founder_probs[f])
                matrix_row[bin_idx] = founders.index(max_founder)
