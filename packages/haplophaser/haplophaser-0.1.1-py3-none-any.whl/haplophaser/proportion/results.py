"""Data structures for haplotype proportion results.

This module defines the core data structures for storing and manipulating
haplotype proportion estimates at various levels of granularity.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass
class WindowProportion:
    """Haplotype proportions for a single genomic window.

    Attributes:
        chrom: Chromosome name
        start: Window start position (0-based)
        end: Window end position (exclusive)
        proportions: Dict mapping founder names to proportion estimates
        confidence_intervals: Optional confidence intervals per founder
        n_markers: Number of markers in this window
        method: Estimation method used
    """

    chrom: str
    start: int
    end: int
    proportions: dict[str, float]
    confidence_intervals: dict[str, tuple[float, float]] | None = None
    n_markers: int = 0
    method: str = "frequency"

    @property
    def midpoint(self) -> int:
        """Get the midpoint of the window."""
        return (self.start + self.end) // 2

    @property
    def size(self) -> int:
        """Get the window size in base pairs."""
        return self.end - self.start

    @property
    def founders(self) -> list[str]:
        """Get list of founders."""
        return list(self.proportions.keys())

    def get_proportion(self, founder: str) -> float:
        """Get proportion for a specific founder."""
        return self.proportions.get(founder, 0.0)

    def get_ci(self, founder: str) -> tuple[float, float] | None:
        """Get confidence interval for a specific founder."""
        if self.confidence_intervals is None:
            return None
        return self.confidence_intervals.get(founder)

    @property
    def dominant_founder(self) -> str | None:
        """Get the founder with the highest proportion."""
        if not self.proportions:
            return None
        return max(self.proportions, key=lambda f: self.proportions[f])

    @property
    def is_mixed(self) -> bool:
        """Check if this window shows mixed ancestry (no clear dominant)."""
        if not self.proportions:
            return False
        sorted_props = sorted(self.proportions.values(), reverse=True)
        if len(sorted_props) < 2:
            return False
        # Mixed if top two founders are within 20% of each other
        return sorted_props[0] - sorted_props[1] < 0.2

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        result = {
            "chrom": self.chrom,
            "start": self.start,
            "end": self.end,
            "proportions": self.proportions.copy(),
            "n_markers": self.n_markers,
            "method": self.method,
        }
        if self.confidence_intervals:
            result["confidence_intervals"] = {
                k: list(v) for k, v in self.confidence_intervals.items()
            }
        return result


@dataclass
class SampleProportions:
    """Haplotype proportions for a single sample across the genome.

    Attributes:
        sample_name: Name of the sample
        founders: List of founder names
        windows: List of window proportions
        genome_wide: Genome-wide average proportions
    """

    sample_name: str
    founders: list[str]
    windows: list[WindowProportion] = field(default_factory=list)
    genome_wide: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Calculate genome-wide proportions if not provided."""
        if not self.genome_wide and self.windows:
            self._calculate_genome_wide()

    def _calculate_genome_wide(self) -> None:
        """Calculate genome-wide weighted average proportions."""
        if not self.windows:
            return

        total_markers = sum(w.n_markers for w in self.windows)
        if total_markers == 0:
            # Fall back to unweighted average
            for founder in self.founders:
                props = [w.get_proportion(founder) for w in self.windows]
                self.genome_wide[founder] = sum(props) / len(props) if props else 0.0
            return

        # Weighted average by marker count
        for founder in self.founders:
            weighted_sum = sum(
                w.get_proportion(founder) * w.n_markers for w in self.windows
            )
            self.genome_wide[founder] = weighted_sum / total_markers

    def add_window(self, window: WindowProportion) -> None:
        """Add a window proportion result."""
        self.windows.append(window)

    def get_chromosome_windows(self, chrom: str) -> list[WindowProportion]:
        """Get all windows for a specific chromosome."""
        return [w for w in self.windows if w.chrom == chrom]

    def get_chromosomes(self) -> list[str]:
        """Get list of chromosomes with data."""
        seen = set()
        chroms = []
        for w in self.windows:
            if w.chrom not in seen:
                seen.add(w.chrom)
                chroms.append(w.chrom)
        return chroms

    @property
    def total_windows(self) -> int:
        """Get total number of windows."""
        return len(self.windows)

    @property
    def total_markers(self) -> int:
        """Get total number of markers across all windows."""
        return sum(w.n_markers for w in self.windows)

    def recalculate_genome_wide(self) -> None:
        """Recalculate genome-wide proportions from current windows."""
        self._calculate_genome_wide()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "sample_name": self.sample_name,
            "founders": self.founders.copy(),
            "genome_wide": self.genome_wide.copy(),
            "windows": [w.to_dict() for w in self.windows],
        }


@dataclass
class ProportionResults:
    """Collection of proportion results for multiple samples.

    Attributes:
        samples: Dict mapping sample names to their proportion results
        founders: List of founder names
        method: Estimation method used
        window_size: Window size used for estimation
        step_size: Step size for sliding windows
        min_markers: Minimum markers required per window
    """

    samples: dict[str, SampleProportions] = field(default_factory=dict)
    founders: list[str] = field(default_factory=list)
    method: str = "frequency"
    window_size: int = 1000000
    step_size: int | None = None
    min_markers: int = 1

    def __post_init__(self) -> None:
        """Set default step size if not provided."""
        if self.step_size is None:
            self.step_size = self.window_size // 2

    def add_sample(self, sample: SampleProportions) -> None:
        """Add a sample's proportion results."""
        self.samples[sample.sample_name] = sample

    def get_sample(self, sample_name: str) -> SampleProportions | None:
        """Get proportion results for a specific sample."""
        return self.samples.get(sample_name)

    @property
    def sample_names(self) -> list[str]:
        """Get list of sample names."""
        return list(self.samples.keys())

    @property
    def n_samples(self) -> int:
        """Get number of samples."""
        return len(self.samples)

    def __iter__(self) -> Iterator[SampleProportions]:
        """Iterate over sample proportion results."""
        return iter(self.samples.values())

    def __len__(self) -> int:
        """Get number of samples."""
        return len(self.samples)

    def get_genome_wide_summary(self) -> dict[str, dict[str, float]]:
        """Get genome-wide proportions for all samples.

        Returns:
            Dict mapping sample names to founder proportion dicts
        """
        return {
            name: sample.genome_wide.copy() for name, sample in self.samples.items()
        }

    def get_window_at_position(
        self, sample_name: str, chrom: str, pos: int
    ) -> WindowProportion | None:
        """Get the window containing a specific position.

        Args:
            sample_name: Name of the sample
            chrom: Chromosome
            pos: Position to look up

        Returns:
            WindowProportion containing the position, or None
        """
        sample = self.samples.get(sample_name)
        if sample is None:
            return None

        for window in sample.windows:
            if window.chrom == chrom and window.start <= pos < window.end:
                return window
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "method": self.method,
            "window_size": self.window_size,
            "step_size": self.step_size,
            "min_markers": self.min_markers,
            "founders": self.founders.copy(),
            "samples": {name: s.to_dict() for name, s in self.samples.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> ProportionResults:
        """Create ProportionResults from a dictionary."""
        result = cls(
            founders=data.get("founders", []),
            method=data.get("method", "frequency"),
            window_size=data.get("window_size", 1000000),
            step_size=data.get("step_size"),
            min_markers=data.get("min_markers", 1),
        )

        for sample_name, sample_data in data.get("samples", {}).items():
            windows = []
            for w_data in sample_data.get("windows", []):
                ci = None
                if "confidence_intervals" in w_data:
                    ci = {
                        k: tuple(v)
                        for k, v in w_data["confidence_intervals"].items()
                    }
                windows.append(
                    WindowProportion(
                        chrom=w_data["chrom"],
                        start=w_data["start"],
                        end=w_data["end"],
                        proportions=w_data["proportions"],
                        confidence_intervals=ci,
                        n_markers=w_data.get("n_markers", 0),
                        method=w_data.get("method", "frequency"),
                    )
                )

            sample = SampleProportions(
                sample_name=sample_name,
                founders=sample_data.get("founders", result.founders),
                windows=windows,
                genome_wide=sample_data.get("genome_wide", {}),
            )
            result.add_sample(sample)

        return result
