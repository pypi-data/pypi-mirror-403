"""
Multi-founder marker identification.

This module provides tools for identifying markers in populations with
more than 2 founders (e.g., NAM, MAGIC designs). Supports pairwise markers,
unique markers, and hierarchical classification.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from itertools import combinations
from typing import TYPE_CHECKING

from haplophaser.core.frequencies import AlleleFrequencies, VariantAlleleFrequencies
from haplophaser.markers.diagnostic import (
    DiagnosticMarker,
    DiagnosticMarkerFinder,
    DiagnosticMarkerSet,
    MarkerClassification,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class MultiFounderStrategy(str, Enum):
    """Strategy for multi-founder marker identification.

    Attributes
    ----------
    PAIRWISE
        Find markers diagnostic for each founder pair.
    UNIQUE
        Find markers that distinguish one founder from all others.
    HIERARCHICAL
        Find markers that distinguish groups of founders.
    ALL
        Find all types of markers.
    """

    PAIRWISE = "pairwise"
    UNIQUE = "unique"
    HIERARCHICAL = "hierarchical"
    ALL = "all"


@dataclass
class PairwiseMarker:
    """A marker that distinguishes a specific pair of founders.

    Parameters
    ----------
    marker : DiagnosticMarker
        The underlying diagnostic marker.
    founder1 : str
        First founder in the pair.
    founder2 : str
        Second founder in the pair.
    f1_allele : str
        Predominant allele in founder1.
    f2_allele : str
        Predominant allele in founder2.
    freq_diff : float
        Frequency difference between founders.
    """

    marker: DiagnosticMarker
    founder1: str
    founder2: str
    f1_allele: str
    f2_allele: str
    freq_diff: float

    @property
    def pair(self) -> tuple[str, str]:
        """Return founder pair as tuple."""
        return (self.founder1, self.founder2)

    @property
    def variant_id(self) -> str:
        """Return variant ID."""
        return self.marker.variant_id


@dataclass
class UniqueMarker:
    """A marker that distinguishes one founder from all others.

    Parameters
    ----------
    marker : DiagnosticMarker
        The underlying diagnostic marker.
    unique_founder : str
        The founder distinguished by this marker.
    unique_allele : str
        The allele unique to this founder.
    min_freq_diff : float
        Minimum frequency difference from other founders.
    """

    marker: DiagnosticMarker
    unique_founder: str
    unique_allele: str
    min_freq_diff: float

    @property
    def variant_id(self) -> str:
        """Return variant ID."""
        return self.marker.variant_id


@dataclass
class FounderGroup:
    """A group of founders with similar allele patterns.

    Parameters
    ----------
    name : str
        Group name/identifier.
    founders : list[str]
        Founders in this group.
    shared_allele : str
        Allele shared by founders in this group.
    """

    name: str
    founders: list[str]
    shared_allele: str


@dataclass
class HierarchicalMarker:
    """A marker that distinguishes groups of founders.

    Parameters
    ----------
    marker : DiagnosticMarker
        The underlying diagnostic marker.
    groups : list[FounderGroup]
        Groups defined by this marker.
    """

    marker: DiagnosticMarker
    groups: list[FounderGroup]

    @property
    def variant_id(self) -> str:
        """Return variant ID."""
        return self.marker.variant_id


@dataclass
class MultiFounderMarkerSet:
    """Collection of multi-founder markers with metadata.

    Parameters
    ----------
    pairwise : list[PairwiseMarker]
        Pairwise diagnostic markers.
    unique : list[UniqueMarker]
        Unique (founder-specific) markers.
    hierarchical : list[HierarchicalMarker]
        Hierarchical grouping markers.
    founders : list[str]
        All founder names.
    parameters : dict
        Parameters used for marker finding.
    """

    pairwise: list[PairwiseMarker] = field(default_factory=list)
    unique: list[UniqueMarker] = field(default_factory=list)
    hierarchical: list[HierarchicalMarker] = field(default_factory=list)
    founders: list[str] = field(default_factory=list)
    parameters: dict = field(default_factory=dict)

    def __len__(self) -> int:
        """Return total number of unique markers."""
        variant_ids = set()
        for m in self.pairwise:
            variant_ids.add(m.variant_id)
        for m in self.unique:
            variant_ids.add(m.variant_id)
        for m in self.hierarchical:
            variant_ids.add(m.variant_id)
        return len(variant_ids)

    @property
    def n_pairwise(self) -> int:
        """Return number of pairwise markers."""
        return len(self.pairwise)

    @property
    def n_unique(self) -> int:
        """Return number of unique markers."""
        return len(self.unique)

    @property
    def n_hierarchical(self) -> int:
        """Return number of hierarchical markers."""
        return len(self.hierarchical)

    def get_pairwise_markers(
        self,
        founder1: str,
        founder2: str,
    ) -> list[PairwiseMarker]:
        """Get markers for a specific founder pair."""
        result = []
        for m in self.pairwise:
            if m.pair in ((founder1, founder2), (founder2, founder1)):
                result.append(m)
        return result

    def get_unique_markers(self, founder: str) -> list[UniqueMarker]:
        """Get markers unique to a specific founder."""
        return [m for m in self.unique if m.unique_founder == founder]

    def get_all_diagnostic_markers(self) -> DiagnosticMarkerSet:
        """Return all markers as a DiagnosticMarkerSet."""
        seen = set()
        markers = []

        for m in self.pairwise:
            if m.variant_id not in seen:
                markers.append(m.marker)
                seen.add(m.variant_id)

        for m in self.unique:
            if m.variant_id not in seen:
                markers.append(m.marker)
                seen.add(m.variant_id)

        for m in self.hierarchical:
            if m.variant_id not in seen:
                markers.append(m.marker)
                seen.add(m.variant_id)

        result = DiagnosticMarkerSet(
            markers=markers,
            founders=self.founders,
            parameters=self.parameters,
        )
        return result

    def pairwise_coverage(self) -> dict[tuple[str, str], int]:
        """Return marker counts for each founder pair."""
        counts: dict[tuple[str, str], int] = {}

        # Initialize all pairs
        for i, f1 in enumerate(self.founders):
            for f2 in self.founders[i + 1:]:
                counts[(f1, f2)] = 0

        # Count markers
        for m in self.pairwise:
            pair = tuple(sorted(m.pair))
            if pair in counts:
                counts[pair] += 1
            else:
                counts[pair] = 1

        return counts

    def founder_coverage(self) -> dict[str, int]:
        """Return unique marker counts for each founder."""
        counts = dict.fromkeys(self.founders, 0)
        for m in self.unique:
            counts[m.unique_founder] = counts.get(m.unique_founder, 0) + 1
        return counts

    def summary(self) -> dict:
        """Generate summary statistics."""
        return {
            "total_unique_variants": len(self),
            "pairwise_markers": self.n_pairwise,
            "unique_markers": self.n_unique,
            "hierarchical_markers": self.n_hierarchical,
            "founders": self.founders,
            "pairwise_coverage": self.pairwise_coverage(),
            "founder_coverage": self.founder_coverage(),
            "parameters": self.parameters,
        }


class MultiFounderMarkerFinder:
    """Find markers for populations with multiple founders.

    Parameters
    ----------
    founders : list[str]
        Founder population names.
    strategy : MultiFounderStrategy
        Strategy for marker identification.
    min_freq_diff : float
        Minimum frequency difference for pairwise markers.
    max_minor_freq : float
        Maximum minor allele frequency within a founder.
    min_samples : int
        Minimum samples per founder.
    unique_min_diff : float
        Minimum difference for unique markers.
    """

    def __init__(
        self,
        founders: list[str],
        strategy: MultiFounderStrategy | str = MultiFounderStrategy.PAIRWISE,
        min_freq_diff: float = 0.7,
        max_minor_freq: float = 0.1,
        min_samples: int = 2,
        unique_min_diff: float = 0.5,
    ) -> None:
        if len(founders) < 2:
            raise ValueError("Need at least 2 founders")

        self.founders = founders
        self.strategy = (
            MultiFounderStrategy(strategy)
            if isinstance(strategy, str)
            else strategy
        )
        self.min_freq_diff = min_freq_diff
        self.max_minor_freq = max_minor_freq
        self.min_samples = min_samples
        self.unique_min_diff = unique_min_diff

        # Create base diagnostic marker finder
        self._base_finder = DiagnosticMarkerFinder(
            min_freq_diff=min_freq_diff,
            max_minor_freq=max_minor_freq,
            min_samples=min_samples,
            allow_partial=True,
        )

    def find(
        self,
        frequencies: AlleleFrequencies,
    ) -> MultiFounderMarkerSet:
        """Find multi-founder markers from allele frequencies.

        Parameters
        ----------
        frequencies : AlleleFrequencies
            Pre-calculated allele frequencies.

        Returns
        -------
        MultiFounderMarkerSet
            Collection of identified markers.
        """
        result = MultiFounderMarkerSet(
            founders=self.founders,
            parameters={
                "strategy": self.strategy.value,
                "min_freq_diff": self.min_freq_diff,
                "max_minor_freq": self.max_minor_freq,
                "min_samples": self.min_samples,
                "unique_min_diff": self.unique_min_diff,
            },
        )

        n_processed = 0

        for var_freq in frequencies:
            self._process_variant(var_freq, result)

            n_processed += 1
            if n_processed % 100000 == 0:
                logger.info(
                    f"Processed {n_processed:,} variants, "
                    f"found {result.n_pairwise:,} pairwise, "
                    f"{result.n_unique:,} unique markers"
                )

        logger.info(
            f"Found {len(result):,} unique variant positions with markers "
            f"({result.n_pairwise:,} pairwise, {result.n_unique:,} unique)"
        )

        return result

    def _process_variant(
        self,
        var_freq: VariantAlleleFrequencies,
        result: MultiFounderMarkerSet,
    ) -> None:
        """Process a single variant for marker potential.

        Parameters
        ----------
        var_freq : VariantAlleleFrequencies
            Variant frequency data.
        result : MultiFounderMarkerSet
            Result set to update.
        """
        # Check we have data for founders
        valid_founders = []
        for f in self.founders:
            pop_freq = var_freq.get_population_freq(f)
            if pop_freq is not None and pop_freq.n_samples >= self.min_samples:
                valid_founders.append(f)

        if len(valid_founders) < 2:
            return

        # Skip multiallelic
        if len(var_freq.alt) != 1:
            return

        ref = var_freq.ref
        alt = var_freq.alt[0]

        # Get frequencies for valid founders
        founder_freqs: dict[str, dict[str, float]] = {}
        for f in valid_founders:
            pop_freq = var_freq.get_population_freq(f)
            if pop_freq:
                founder_freqs[f] = {
                    ref: pop_freq.get_frequency(ref),
                    alt: pop_freq.get_frequency(alt),
                }

        # Find pairwise markers
        if self.strategy in (MultiFounderStrategy.PAIRWISE, MultiFounderStrategy.ALL):
            self._find_pairwise(var_freq, founder_freqs, ref, alt, result)

        # Find unique markers
        if self.strategy in (MultiFounderStrategy.UNIQUE, MultiFounderStrategy.ALL):
            self._find_unique(var_freq, founder_freqs, ref, alt, result)

        # Find hierarchical markers
        if self.strategy in (MultiFounderStrategy.HIERARCHICAL, MultiFounderStrategy.ALL):
            self._find_hierarchical(var_freq, founder_freqs, ref, alt, result)

    def _find_pairwise(
        self,
        var_freq: VariantAlleleFrequencies,
        founder_freqs: dict[str, dict[str, float]],
        ref: str,
        alt: str,
        result: MultiFounderMarkerSet,
    ) -> None:
        """Find pairwise diagnostic markers."""
        founders = list(founder_freqs.keys())

        for f1, f2 in combinations(founders, 2):
            f1_ref = founder_freqs[f1].get(ref, 0)
            f1_alt = founder_freqs[f1].get(alt, 0)
            f2_ref = founder_freqs[f2].get(ref, 0)
            f2_alt = founder_freqs[f2].get(alt, 0)

            # Check frequency difference
            diff = max(abs(f1_ref - f2_ref), abs(f1_alt - f2_alt))

            if diff < self.min_freq_diff:
                continue

            # Determine predominant alleles
            f1_allele = ref if f1_ref >= f1_alt else alt
            f2_allele = ref if f2_ref >= f2_alt else alt

            # Skip if same predominant allele
            if f1_allele == f2_allele:
                continue

            # Classify marker
            classification = self._classify_pairwise(
                founder_freqs, f1, f2, ref, alt
            )

            # Create base diagnostic marker
            {f: founder_freqs[f] for f in founders}
            marker = DiagnosticMarker(
                variant_id=var_freq.variant_id,
                chrom=var_freq.chrom,
                pos=var_freq.pos,
                ref=ref,
                alt=alt,
                founder_alleles={f: (ref if founder_freqs[f].get(ref, 0) >= founder_freqs[f].get(alt, 0) else alt) for f in founders},
                founder_frequencies=founder_freqs,
                confidence=self._calculate_confidence(var_freq, founders, diff),
                classification=classification,
                distinguishes=(f1, f2),
            )

            pairwise_marker = PairwiseMarker(
                marker=marker,
                founder1=f1,
                founder2=f2,
                f1_allele=f1_allele,
                f2_allele=f2_allele,
                freq_diff=diff,
            )

            result.pairwise.append(pairwise_marker)

    def _find_unique(
        self,
        var_freq: VariantAlleleFrequencies,
        founder_freqs: dict[str, dict[str, float]],
        ref: str,
        alt: str,
        result: MultiFounderMarkerSet,
    ) -> None:
        """Find unique (founder-specific) markers."""
        founders = list(founder_freqs.keys())

        for candidate in founders:
            # Get candidate's predominant allele
            cand_ref = founder_freqs[candidate].get(ref, 0)
            cand_alt = founder_freqs[candidate].get(alt, 0)
            cand_allele = ref if cand_ref >= cand_alt else alt
            cand_freq = max(cand_ref, cand_alt)

            # Check if this allele is unique (different from all others)
            min_diff = float("inf")
            is_unique = True

            for other in founders:
                if other == candidate:
                    continue

                other_freq = founder_freqs[other].get(cand_allele, 0)
                diff = cand_freq - other_freq

                if diff < self.unique_min_diff:
                    is_unique = False
                    break

                min_diff = min(min_diff, diff)

            if is_unique and min_diff != float("inf"):
                # Create diagnostic marker
                marker = DiagnosticMarker(
                    variant_id=var_freq.variant_id,
                    chrom=var_freq.chrom,
                    pos=var_freq.pos,
                    ref=ref,
                    alt=alt,
                    founder_alleles={f: (ref if founder_freqs[f].get(ref, 0) >= founder_freqs[f].get(alt, 0) else alt) for f in founders},
                    founder_frequencies=founder_freqs,
                    confidence=self._calculate_confidence(var_freq, founders, min_diff),
                    classification=MarkerClassification.FULLY_DIAGNOSTIC,
                    distinguishes=None,
                    info={"unique_founder": candidate},
                )

                unique_marker = UniqueMarker(
                    marker=marker,
                    unique_founder=candidate,
                    unique_allele=cand_allele,
                    min_freq_diff=min_diff,
                )

                result.unique.append(unique_marker)

    def _find_hierarchical(
        self,
        var_freq: VariantAlleleFrequencies,
        founder_freqs: dict[str, dict[str, float]],
        ref: str,
        alt: str,
        result: MultiFounderMarkerSet,
    ) -> None:
        """Find hierarchical grouping markers."""
        founders = list(founder_freqs.keys())

        # Group founders by predominant allele
        ref_founders = []
        alt_founders = []

        for f in founders:
            ref_freq = founder_freqs[f].get(ref, 0)
            alt_freq = founder_freqs[f].get(alt, 0)

            if ref_freq >= alt_freq:
                ref_founders.append(f)
            else:
                alt_founders.append(f)

        # Need at least one founder in each group, and not all in one group
        if not ref_founders or not alt_founders:
            return
        if len(ref_founders) == 1 and len(alt_founders) == 1:
            # This is just a pairwise marker
            return

        # Check that groups are well-separated
        ref_min_freq = min(
            founder_freqs[f].get(ref, 0) for f in ref_founders
        )
        alt_min_freq = min(
            founder_freqs[f].get(alt, 0) for f in alt_founders
        )

        if ref_min_freq < 1 - self.max_minor_freq:
            return
        if alt_min_freq < 1 - self.max_minor_freq:
            return

        # Create groups
        groups = [
            FounderGroup(name="ref_group", founders=ref_founders, shared_allele=ref),
            FounderGroup(name="alt_group", founders=alt_founders, shared_allele=alt),
        ]

        # Create marker
        marker = DiagnosticMarker(
            variant_id=var_freq.variant_id,
            chrom=var_freq.chrom,
            pos=var_freq.pos,
            ref=ref,
            alt=alt,
            founder_alleles={f: (ref if founder_freqs[f].get(ref, 0) >= founder_freqs[f].get(alt, 0) else alt) for f in founders},
            founder_frequencies=founder_freqs,
            confidence=self._calculate_confidence(var_freq, founders, 1.0),
            classification=MarkerClassification.FULLY_DIAGNOSTIC,
            distinguishes=None,
            info={"hierarchical": True, "n_groups": 2},
        )

        hierarchical_marker = HierarchicalMarker(
            marker=marker,
            groups=groups,
        )

        result.hierarchical.append(hierarchical_marker)

    def _classify_pairwise(
        self,
        founder_freqs: dict[str, dict[str, float]],
        f1: str,
        f2: str,
        ref: str,
        alt: str,
    ) -> MarkerClassification:
        """Classify a pairwise marker."""
        f1_ref = founder_freqs[f1].get(ref, 0)
        f1_alt = founder_freqs[f1].get(alt, 0)
        f2_ref = founder_freqs[f2].get(ref, 0)
        f2_alt = founder_freqs[f2].get(alt, 0)

        fixed_threshold = 0.9

        f1_fixed_ref = f1_ref >= fixed_threshold
        f1_fixed_alt = f1_alt >= fixed_threshold
        f2_fixed_ref = f2_ref >= fixed_threshold
        f2_fixed_alt = f2_alt >= fixed_threshold

        if (f1_fixed_ref and f2_fixed_alt) or (f1_fixed_alt and f2_fixed_ref):
            return MarkerClassification.FULLY_DIAGNOSTIC

        f1_minor = min(f1_ref, f1_alt)
        f2_minor = min(f2_ref, f2_alt)
        freq_diff = max(abs(f1_ref - f2_ref), abs(f1_alt - f2_alt))

        if (
            freq_diff >= self.min_freq_diff
            and f1_minor <= self.max_minor_freq
            and f2_minor <= self.max_minor_freq
        ):
            return MarkerClassification.PARTIALLY_DIAGNOSTIC

        return MarkerClassification.INFORMATIVE

    def _calculate_confidence(
        self,
        var_freq: VariantAlleleFrequencies,
        founders: list[str],
        freq_diff: float,
    ) -> float:
        """Calculate confidence score."""
        freq_score = min(freq_diff / 1.0, 1.0)

        total_samples = 0
        for f in founders:
            pop_freq = var_freq.get_population_freq(f)
            if pop_freq:
                total_samples += pop_freq.n_samples

        sample_score = min(total_samples / 20, 1.0)

        confidence = 0.6 * freq_score + 0.4 * sample_score

        return round(confidence, 3)


def find_pairwise_markers(
    frequencies: AlleleFrequencies,
    founders: list[str],
    min_freq_diff: float = 0.7,
) -> MultiFounderMarkerSet:
    """Convenience function to find pairwise markers.

    Parameters
    ----------
    frequencies : AlleleFrequencies
        Pre-calculated allele frequencies.
    founders : list[str]
        Founder population names.
    min_freq_diff : float
        Minimum frequency difference.

    Returns
    -------
    MultiFounderMarkerSet
        Identified markers.
    """
    finder = MultiFounderMarkerFinder(
        founders=founders,
        strategy=MultiFounderStrategy.PAIRWISE,
        min_freq_diff=min_freq_diff,
    )
    return finder.find(frequencies)


def find_unique_markers(
    frequencies: AlleleFrequencies,
    founders: list[str],
    min_diff: float = 0.5,
) -> MultiFounderMarkerSet:
    """Convenience function to find unique/founder-specific markers.

    Parameters
    ----------
    frequencies : AlleleFrequencies
        Pre-calculated allele frequencies.
    founders : list[str]
        Founder population names.
    min_diff : float
        Minimum frequency difference from other founders.

    Returns
    -------
    MultiFounderMarkerSet
        Identified markers.
    """
    finder = MultiFounderMarkerFinder(
        founders=founders,
        strategy=MultiFounderStrategy.UNIQUE,
        unique_min_diff=min_diff,
    )
    return finder.find(frequencies)
