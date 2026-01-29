"""Integration of window-based and HMM proportion results.

This module provides tools for combining different estimation
methods into a unified result set.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from haplophaser.proportion.results import (
    ProportionResults,
    SampleProportions,
    WindowProportion,
)

if TYPE_CHECKING:
    from haplophaser.proportion.hmm import HMMResults

logger = logging.getLogger(__name__)


class IntegrationStrategy(Enum):
    """Strategy for integrating window and HMM results."""

    HMM_PRIMARY = "hmm_primary"
    WINDOW_PRIMARY = "window_primary"
    CONSENSUS = "consensus"
    WEIGHTED = "weighted"


@dataclass
class IntegratedWindow:
    """A window with integrated proportion estimates.

    Attributes:
        chrom: Chromosome name
        start: Window start
        end: Window end
        window_proportions: Proportions from window method
        hmm_proportions: Proportions from HMM method
        integrated_proportions: Final integrated proportions
        confidence: Confidence in the integrated result
        agreement: Agreement between methods (0-1)
        source: Primary source of the integrated result
    """

    chrom: str
    start: int
    end: int
    window_proportions: dict[str, float]
    hmm_proportions: dict[str, float]
    integrated_proportions: dict[str, float]
    confidence: float = 0.0
    agreement: float = 0.0
    source: str = "integrated"


class ResultsIntegrator:
    """Integrate window-based and HMM proportion results.

    Combines results from different estimation methods using
    various strategies to produce a unified result set.
    """

    def __init__(
        self,
        strategy: str | IntegrationStrategy = "hmm_primary",
        hmm_weight: float = 0.7,
        confidence_threshold: float = 0.8,
        agreement_threshold: float = 0.7,
    ) -> None:
        """Initialize the integrator.

        Args:
            strategy: Integration strategy
            hmm_weight: Weight for HMM results in weighted strategy
            confidence_threshold: Confidence threshold for using primary source
            agreement_threshold: Agreement threshold for consensus strategy
        """
        if isinstance(strategy, str):
            strategy = IntegrationStrategy(strategy)
        self.strategy = strategy
        self.hmm_weight = hmm_weight
        self.confidence_threshold = confidence_threshold
        self.agreement_threshold = agreement_threshold

    def integrate(
        self,
        window_proportions: ProportionResults,
        hmm_results: HMMResults,
    ) -> ProportionResults:
        """Integrate window and HMM results.

        Args:
            window_proportions: Window-based proportion results
            hmm_results: HMM inference results

        Returns:
            ProportionResults with integrated estimates
        """
        logger.info(f"Integrating results using {self.strategy.value} strategy")

        founders = window_proportions.founders
        integrated = ProportionResults(
            founders=founders,
            method=f"integrated_{self.strategy.value}",
            window_size=window_proportions.window_size,
            step_size=window_proportions.step_size,
            min_markers=window_proportions.min_markers,
        )

        for sample in window_proportions:
            integrated_sample = self._integrate_sample(
                sample, hmm_results, founders
            )
            integrated.add_sample(integrated_sample)

        return integrated

    def _integrate_sample(
        self,
        window_sample: SampleProportions,
        hmm_results: HMMResults,
        founders: list[str],
    ) -> SampleProportions:
        """Integrate results for a single sample.

        Args:
            window_sample: Window-based results for sample
            hmm_results: HMM results
            founders: List of founder names

        Returns:
            Integrated SampleProportions
        """
        sample_name = window_sample.sample_name
        integrated_windows = []

        for window in window_sample.windows:
            # Get HMM proportions for this window
            hmm_props = self._get_hmm_proportions_for_window(
                sample_name, window, hmm_results, founders
            )

            # Integrate based on strategy
            integrated_window = self._integrate_window(
                window, hmm_props, founders
            )
            integrated_windows.append(integrated_window)

        return SampleProportions(
            sample_name=sample_name,
            founders=founders,
            windows=integrated_windows,
        )

    def _get_hmm_proportions_for_window(
        self,
        sample_name: str,
        window: WindowProportion,
        hmm_results: HMMResults,
        founders: list[str],
    ) -> dict[str, float]:
        """Get HMM proportions averaged over a window.

        Args:
            sample_name: Sample name
            window: Window to query
            hmm_results: HMM results
            founders: List of founders

        Returns:
            Dict mapping founders to proportions
        """
        result = hmm_results.get_result(sample_name, window.chrom)
        if result is None:
            # No HMM data, return uniform
            return {f: 1.0 / len(founders) for f in founders}

        # Find HMM positions within window
        window_indices = [
            i for i, pos in enumerate(result.positions)
            if window.start <= pos < window.end
        ]

        if not window_indices:
            # No HMM data in window, use nearest
            mid = (window.start + window.end) // 2
            return result.get_posterior_at(mid) or {f: 1.0 / len(founders) for f in founders}

        # Average smoothed proportions within window
        avg_props = dict.fromkeys(founders, 0.0)
        for idx in window_indices:
            for f in founders:
                avg_props[f] += result.smoothed_proportions[idx].get(f, 0.0)

        n = len(window_indices)
        return {f: v / n for f, v in avg_props.items()}

    def _integrate_window(
        self,
        window: WindowProportion,
        hmm_props: dict[str, float],
        founders: list[str],
    ) -> WindowProportion:
        """Integrate a single window.

        Args:
            window: Window with window-based proportions
            hmm_props: HMM-based proportions
            founders: List of founders

        Returns:
            WindowProportion with integrated estimates
        """
        window_props = window.proportions

        # Calculate agreement between methods
        agreement = self._calculate_agreement(window_props, hmm_props, founders)

        # Apply integration strategy
        if self.strategy == IntegrationStrategy.HMM_PRIMARY:
            integrated = self._integrate_hmm_primary(
                window_props, hmm_props, founders, agreement
            )
            source = "hmm"
        elif self.strategy == IntegrationStrategy.WINDOW_PRIMARY:
            integrated = self._integrate_window_primary(
                window_props, hmm_props, founders, agreement
            )
            source = "window"
        elif self.strategy == IntegrationStrategy.CONSENSUS:
            integrated, source = self._integrate_consensus(
                window_props, hmm_props, founders, agreement
            )
        else:  # WEIGHTED
            integrated = self._integrate_weighted(
                window_props, hmm_props, founders
            )
            source = "weighted"

        # Calculate confidence
        self._calculate_confidence(integrated, agreement)

        return WindowProportion(
            chrom=window.chrom,
            start=window.start,
            end=window.end,
            proportions=integrated,
            confidence_intervals=window.confidence_intervals,
            n_markers=window.n_markers,
            method=f"integrated_{source}",
        )

    def _calculate_agreement(
        self,
        window_props: dict[str, float],
        hmm_props: dict[str, float],
        founders: list[str],
    ) -> float:
        """Calculate agreement between window and HMM proportions.

        Args:
            window_props: Window-based proportions
            hmm_props: HMM-based proportions
            founders: List of founders

        Returns:
            Agreement score (0-1, higher is more agreement)
        """
        # Use correlation or simple difference
        diffs = []
        for f in founders:
            w_prop = window_props.get(f, 0.0)
            h_prop = hmm_props.get(f, 0.0)
            diffs.append(abs(w_prop - h_prop))

        max_diff = max(diffs)
        return 1.0 - max_diff

    def _integrate_hmm_primary(
        self,
        window_props: dict[str, float],
        hmm_props: dict[str, float],
        founders: list[str],
        agreement: float,
    ) -> dict[str, float]:
        """Use HMM as primary, fall back to window when uncertain.

        Args:
            window_props: Window-based proportions
            hmm_props: HMM-based proportions
            founders: List of founders
            agreement: Agreement score

        Returns:
            Integrated proportions
        """
        # Check if HMM result is confident
        max_hmm = max(hmm_props.values()) if hmm_props else 0
        if max_hmm >= self.confidence_threshold:
            return hmm_props.copy()

        # If agreement is good, use HMM anyway
        if agreement >= self.agreement_threshold:
            return hmm_props.copy()

        # Fall back to window
        return window_props.copy()

    def _integrate_window_primary(
        self,
        window_props: dict[str, float],
        hmm_props: dict[str, float],
        founders: list[str],
        agreement: float,
    ) -> dict[str, float]:
        """Use window as primary, smooth with HMM.

        Args:
            window_props: Window-based proportions
            hmm_props: HMM-based proportions
            founders: List of founders
            agreement: Agreement score

        Returns:
            Integrated proportions
        """
        # If agreement is good, use window
        if agreement >= self.agreement_threshold:
            return window_props.copy()

        # Otherwise, blend with HMM
        weight = 0.3  # Small HMM contribution
        result = {}
        for f in founders:
            w = window_props.get(f, 0.0)
            h = hmm_props.get(f, 0.0)
            result[f] = (1 - weight) * w + weight * h

        # Normalize
        total = sum(result.values())
        if total > 0:
            result = {f: v / total for f, v in result.items()}

        return result

    def _integrate_consensus(
        self,
        window_props: dict[str, float],
        hmm_props: dict[str, float],
        founders: list[str],
        agreement: float,
    ) -> tuple[dict[str, float], str]:
        """Require agreement, flag discordant regions.

        Args:
            window_props: Window-based proportions
            hmm_props: HMM-based proportions
            founders: List of founders
            agreement: Agreement score

        Returns:
            Tuple of (integrated proportions, source)
        """
        if agreement >= self.agreement_threshold:
            # Good agreement - use average
            result = {}
            for f in founders:
                result[f] = (window_props.get(f, 0.0) + hmm_props.get(f, 0.0)) / 2
            return result, "consensus"
        else:
            # Poor agreement - mark as uncertain (use uniform)
            n = len(founders)
            return dict.fromkeys(founders, 1.0 / n), "uncertain"

    def _integrate_weighted(
        self,
        window_props: dict[str, float],
        hmm_props: dict[str, float],
        founders: list[str],
    ) -> dict[str, float]:
        """Weighted average of window and HMM results.

        Args:
            window_props: Window-based proportions
            hmm_props: HMM-based proportions
            founders: List of founders

        Returns:
            Weighted average proportions
        """
        result = {}
        for f in founders:
            w = window_props.get(f, 0.0)
            h = hmm_props.get(f, 0.0)
            result[f] = (1 - self.hmm_weight) * w + self.hmm_weight * h

        # Normalize
        total = sum(result.values())
        if total > 0:
            result = {f: v / total for f, v in result.items()}

        return result

    def _calculate_confidence(
        self,
        integrated: dict[str, float],
        agreement: float,
    ) -> float:
        """Calculate confidence in integrated result.

        Args:
            integrated: Integrated proportions
            agreement: Agreement between methods

        Returns:
            Confidence score (0-1)
        """
        # Base confidence on max proportion
        max_prop = max(integrated.values()) if integrated else 0.0

        # Adjust by agreement
        confidence = (max_prop + agreement) / 2

        return min(1.0, max(0.0, confidence))


def integrate_results(
    window_proportions: ProportionResults,
    hmm_results: HMMResults,
    strategy: str = "hmm_primary",
) -> ProportionResults:
    """Integrate window and HMM proportion results.

    Convenience function wrapping ResultsIntegrator.

    Args:
        window_proportions: Window-based results
        hmm_results: HMM-based results
        strategy: Integration strategy

    Returns:
        Integrated ProportionResults
    """
    integrator = ResultsIntegrator(strategy=strategy)
    return integrator.integrate(window_proportions, hmm_results)
