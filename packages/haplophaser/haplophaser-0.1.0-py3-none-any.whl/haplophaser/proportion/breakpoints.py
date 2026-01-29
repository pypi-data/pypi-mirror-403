"""Breakpoint detection for ancestry transitions.

This module provides methods for detecting recombination breakpoints
where founder ancestry changes along the chromosome.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from haplophaser.proportion.results import ProportionResults, SampleProportions

logger = logging.getLogger(__name__)


class BreakpointMethod(Enum):
    """Method for detecting breakpoints."""

    CHANGEPOINT = "changepoint"
    THRESHOLD = "threshold"
    HMM = "hmm"


@dataclass
class Breakpoint:
    """A detected ancestry transition point.

    Attributes:
        chrom: Chromosome name
        position: Estimated breakpoint position
        left_founder: Dominant founder before breakpoint
        right_founder: Dominant founder after breakpoint
        confidence: Confidence score for this breakpoint
        left_proportion: Proportion of left founder before breakpoint
        right_proportion: Proportion of right founder after breakpoint
        method: Detection method used
        support_windows: Number of windows supporting this breakpoint
    """

    chrom: str
    position: int
    left_founder: str
    right_founder: str
    confidence: float = 1.0
    left_proportion: float = 0.0
    right_proportion: float = 0.0
    method: str = "changepoint"
    support_windows: int = 1

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "chrom": self.chrom,
            "position": self.position,
            "left_founder": self.left_founder,
            "right_founder": self.right_founder,
            "confidence": self.confidence,
            "left_proportion": self.left_proportion,
            "right_proportion": self.right_proportion,
            "method": self.method,
            "support_windows": self.support_windows,
        }


@dataclass
class SampleBreakpoints:
    """Collection of breakpoints for a single sample.

    Attributes:
        sample_name: Name of the sample
        breakpoints: List of detected breakpoints
        founders: List of founder names
    """

    sample_name: str
    breakpoints: list[Breakpoint] = field(default_factory=list)
    founders: list[str] = field(default_factory=list)

    def add_breakpoint(self, bp: Breakpoint) -> None:
        """Add a breakpoint."""
        self.breakpoints.append(bp)

    @property
    def n_breakpoints(self) -> int:
        """Get total number of breakpoints."""
        return len(self.breakpoints)

    def get_chromosome_breakpoints(self, chrom: str) -> list[Breakpoint]:
        """Get breakpoints for a specific chromosome."""
        return sorted(
            [b for b in self.breakpoints if b.chrom == chrom],
            key=lambda b: b.position,
        )

    def get_chromosomes(self) -> list[str]:
        """Get list of chromosomes with breakpoints."""
        seen = set()
        chroms = []
        for b in self.breakpoints:
            if b.chrom not in seen:
                seen.add(b.chrom)
                chroms.append(b.chrom)
        return chroms

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "sample_name": self.sample_name,
            "founders": self.founders.copy(),
            "breakpoints": [b.to_dict() for b in self.breakpoints],
        }


@dataclass
class BreakpointResults:
    """Collection of breakpoints for multiple samples.

    Attributes:
        samples: Dict mapping sample names to their breakpoints
        founders: List of founder names
        method: Detection method used
    """

    samples: dict[str, SampleBreakpoints] = field(default_factory=dict)
    founders: list[str] = field(default_factory=list)
    method: str = "changepoint"

    def add_sample(self, sample_bps: SampleBreakpoints) -> None:
        """Add a sample's breakpoints."""
        self.samples[sample_bps.sample_name] = sample_bps

    def get_sample(self, sample_name: str) -> SampleBreakpoints | None:
        """Get breakpoints for a specific sample."""
        return self.samples.get(sample_name)

    @property
    def sample_names(self) -> list[str]:
        """Get list of sample names."""
        return list(self.samples.keys())

    @property
    def total_breakpoints(self) -> int:
        """Get total breakpoints across all samples."""
        return sum(s.n_breakpoints for s in self.samples.values())

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "founders": self.founders.copy(),
            "method": self.method,
            "samples": {name: s.to_dict() for name, s in self.samples.items()},
        }


class BreakpointFinder:
    """Detect ancestry breakpoints in proportion data.

    Supports three detection methods:
    - changepoint: Statistical changepoint detection
    - threshold: Simple threshold-based detection
    - hmm: Hidden Markov Model-based detection
    """

    def __init__(
        self,
        method: str | BreakpointMethod = "changepoint",
        min_change: float = 0.3,
        min_confidence: float = 0.5,
        window_size: int = 3,
    ) -> None:
        """Initialize the breakpoint finder.

        Args:
            method: Detection method
            min_change: Minimum change in proportion to detect
            min_confidence: Minimum confidence for reported breakpoints
            window_size: Window size for smoothing (changepoint method)
        """
        if isinstance(method, str):
            method = BreakpointMethod(method)
        self.method = method
        self.min_change = min_change
        self.min_confidence = min_confidence
        self.window_size = window_size

    def find_breakpoints(self, results: ProportionResults) -> BreakpointResults:
        """Find breakpoints in proportion results.

        Args:
            results: Proportion estimation results

        Returns:
            BreakpointResults with detected breakpoints
        """
        logger.info(f"Finding breakpoints using {self.method.value} method")

        bp_results = BreakpointResults(
            founders=results.founders,
            method=self.method.value,
        )

        for sample in results:
            sample_bps = self._find_sample_breakpoints(sample, results.founders)
            bp_results.add_sample(sample_bps)

        logger.info(f"Found {bp_results.total_breakpoints} total breakpoints")
        return bp_results

    def _find_sample_breakpoints(
        self,
        sample: SampleProportions,
        founders: list[str],
    ) -> SampleBreakpoints:
        """Find breakpoints for a single sample.

        Args:
            sample: Sample proportion results
            founders: List of founder names

        Returns:
            SampleBreakpoints with detected breakpoints
        """
        sample_bps = SampleBreakpoints(
            sample_name=sample.sample_name,
            founders=founders,
        )

        for chrom in sample.get_chromosomes():
            windows = sample.get_chromosome_windows(chrom)
            if len(windows) < 2:
                continue

            # Sort by position
            windows = sorted(windows, key=lambda w: w.start)

            # Detect breakpoints using selected method
            if self.method == BreakpointMethod.CHANGEPOINT:
                breakpoints = self._detect_changepoint(windows, founders)
            elif self.method == BreakpointMethod.THRESHOLD:
                breakpoints = self._detect_threshold(windows, founders)
            else:  # HMM
                breakpoints = self._detect_hmm(windows, founders)

            # Filter by confidence and add
            for bp in breakpoints:
                if bp.confidence >= self.min_confidence:
                    sample_bps.add_breakpoint(bp)

        return sample_bps

    def _detect_changepoint(
        self,
        windows: list,
        founders: list[str],
    ) -> list[Breakpoint]:
        """Detect breakpoints using changepoint analysis.

        Uses a sliding window to detect significant changes in
        proportion values.

        Args:
            windows: Sorted list of windows
            founders: List of founder names

        Returns:
            List of detected breakpoints
        """
        breakpoints = []

        if len(windows) < self.window_size * 2:
            return breakpoints

        # Convert to proportion array
        n_windows = len(windows)
        n_founders = len(founders)
        prop_matrix = np.zeros((n_windows, n_founders))

        for i, window in enumerate(windows):
            for j, founder in enumerate(founders):
                prop_matrix[i, j] = window.proportions.get(founder, 0.0)

        # Calculate local means before and after each point
        for i in range(self.window_size, n_windows - self.window_size):
            left_mean = np.mean(prop_matrix[i - self.window_size : i], axis=0)
            right_mean = np.mean(prop_matrix[i : i + self.window_size], axis=0)

            # Check for significant change
            max_change = np.max(np.abs(right_mean - left_mean))

            if max_change >= self.min_change:
                # Identify founders involved
                left_dominant_idx = np.argmax(left_mean)
                right_dominant_idx = np.argmax(right_mean)

                if left_dominant_idx != right_dominant_idx:
                    # Calculate confidence based on change magnitude and consistency
                    confidence = self._calculate_changepoint_confidence(
                        prop_matrix, i, left_dominant_idx, right_dominant_idx
                    )

                    bp = Breakpoint(
                        chrom=windows[i].chrom,
                        position=(windows[i - 1].end + windows[i].start) // 2,
                        left_founder=founders[left_dominant_idx],
                        right_founder=founders[right_dominant_idx],
                        confidence=confidence,
                        left_proportion=float(left_mean[left_dominant_idx]),
                        right_proportion=float(right_mean[right_dominant_idx]),
                        method="changepoint",
                        support_windows=self.window_size * 2,
                    )
                    breakpoints.append(bp)

        # Merge nearby breakpoints
        breakpoints = self._merge_nearby_breakpoints(breakpoints)

        return breakpoints

    def _detect_threshold(
        self,
        windows: list,
        founders: list[str],
    ) -> list[Breakpoint]:
        """Detect breakpoints using simple threshold detection.

        Finds points where the dominant founder changes.

        Args:
            windows: Sorted list of windows
            founders: List of founder names

        Returns:
            List of detected breakpoints
        """
        breakpoints = []

        prev_dominant = windows[0].dominant_founder
        prev_props = windows[0].proportions

        for i in range(1, len(windows)):
            curr_dominant = windows[i].dominant_founder
            curr_props = windows[i].proportions

            if curr_dominant != prev_dominant:
                # Check if change is significant by looking at the
                # proportion change for the transitioning founders
                # Use max change across all founders
                max_change = max(
                    abs(curr_props.get(f, 0.0) - prev_props.get(f, 0.0))
                    for f in founders
                )

                if max_change >= self.min_change:
                    bp = Breakpoint(
                        chrom=windows[i].chrom,
                        position=(windows[i - 1].end + windows[i].start) // 2,
                        left_founder=prev_dominant,
                        right_founder=curr_dominant,
                        confidence=min(1.0, max_change),
                        left_proportion=prev_props.get(prev_dominant, 0.0),
                        right_proportion=curr_props.get(curr_dominant, 0.0),
                        method="threshold",
                        support_windows=2,
                    )
                    breakpoints.append(bp)

            prev_dominant = curr_dominant
            prev_props = curr_props

        return breakpoints

    def _detect_hmm(
        self,
        windows: list,
        founders: list[str],
    ) -> list[Breakpoint]:
        """Detect breakpoints using Hidden Markov Model.

        Models founder states and detects transitions.

        Args:
            windows: Sorted list of windows
            founders: List of founder names

        Returns:
            List of detected breakpoints
        """
        breakpoints = []
        n_windows = len(windows)
        n_founders = len(founders)

        if n_windows < 2:
            return breakpoints

        # Build observation matrix (proportions)
        observations = np.zeros((n_windows, n_founders))
        for i, window in enumerate(windows):
            for j, founder in enumerate(founders):
                observations[i, j] = window.proportions.get(founder, 0.0)

        # Simple HMM: Viterbi-like decoding
        # Transition probability (favor staying in same state)
        transition_prob = 0.95

        # Initialize
        log_probs = np.log(observations[0] + 1e-10)
        path = [[j] for j in range(n_founders)]

        # Forward pass
        for i in range(1, n_windows):
            new_log_probs = np.zeros(n_founders)
            new_path = []

            for j in range(n_founders):
                # Transition from each state
                trans_probs = np.zeros(n_founders)
                for k in range(n_founders):
                    if k == j:
                        trans_probs[k] = np.log(transition_prob)
                    else:
                        trans_probs[k] = np.log((1 - transition_prob) / (n_founders - 1))

                # Best previous state
                scores = log_probs + trans_probs + np.log(observations[i, j] + 1e-10)
                best_prev = np.argmax(scores)

                new_log_probs[j] = scores[best_prev]
                new_path.append(path[best_prev] + [j])

            log_probs = new_log_probs
            path = new_path

        # Best final state
        best_final = np.argmax(log_probs)
        best_path = path[best_final]

        # Find transitions in path
        for i in range(1, len(best_path)):
            if best_path[i] != best_path[i - 1]:
                left_founder = founders[best_path[i - 1]]
                right_founder = founders[best_path[i]]

                # Calculate confidence
                left_prop = observations[i - 1, best_path[i - 1]]
                right_prop = observations[i, best_path[i]]
                confidence = (left_prop + right_prop) / 2

                bp = Breakpoint(
                    chrom=windows[i].chrom,
                    position=(windows[i - 1].end + windows[i].start) // 2,
                    left_founder=left_founder,
                    right_founder=right_founder,
                    confidence=float(confidence),
                    left_proportion=float(left_prop),
                    right_proportion=float(right_prop),
                    method="hmm",
                    support_windows=2,
                )
                breakpoints.append(bp)

        return breakpoints

    def _calculate_changepoint_confidence(
        self,
        prop_matrix: np.ndarray,
        position: int,
        left_idx: int,
        right_idx: int,
    ) -> float:
        """Calculate confidence for a changepoint.

        Args:
            prop_matrix: Proportion matrix
            position: Changepoint position index
            left_idx: Left dominant founder index
            right_idx: Right dominant founder index

        Returns:
            Confidence score
        """
        n_windows = prop_matrix.shape[0]

        # Get proportions around the changepoint
        left_start = max(0, position - self.window_size)
        right_end = min(n_windows, position + self.window_size)

        left_region = prop_matrix[left_start:position]
        right_region = prop_matrix[position:right_end]

        if len(left_region) == 0 or len(right_region) == 0:
            return 0.5

        # Factor 1: Consistency of left region
        left_consistency = 1.0 - np.std(left_region[:, left_idx])

        # Factor 2: Consistency of right region
        right_consistency = 1.0 - np.std(right_region[:, right_idx])

        # Factor 3: Magnitude of change
        left_mean = np.mean(left_region[:, left_idx])
        right_mean = np.mean(right_region[:, right_idx])
        change_magnitude = (left_mean + right_mean) / 2

        confidence = (left_consistency + right_consistency + change_magnitude) / 3
        return max(0.0, min(1.0, confidence))

    def _merge_nearby_breakpoints(
        self,
        breakpoints: list[Breakpoint],
        min_distance: int = 10000,
    ) -> list[Breakpoint]:
        """Merge breakpoints that are very close together.

        Args:
            breakpoints: List of breakpoints
            min_distance: Minimum distance between breakpoints

        Returns:
            Merged list of breakpoints
        """
        if len(breakpoints) < 2:
            return breakpoints

        # Sort by position
        breakpoints = sorted(breakpoints, key=lambda b: b.position)

        merged = []
        current = breakpoints[0]

        for next_bp in breakpoints[1:]:
            if (
                next_bp.chrom == current.chrom
                and abs(next_bp.position - current.position) < min_distance
            ):
                # Merge: keep the one with higher confidence
                if next_bp.confidence > current.confidence:
                    current = next_bp
            else:
                merged.append(current)
                current = next_bp

        merged.append(current)
        return merged


def find_breakpoints(
    results: ProportionResults,
    method: str = "changepoint",
    min_change: float = 0.3,
) -> BreakpointResults:
    """Find ancestry breakpoints in proportion results.

    Convenience function wrapping BreakpointFinder.

    Args:
        results: Proportion estimation results
        method: Detection method
        min_change: Minimum change to detect

    Returns:
        BreakpointResults with detected breakpoints
    """
    finder = BreakpointFinder(method=method, min_change=min_change)
    return finder.find_breakpoints(results)
