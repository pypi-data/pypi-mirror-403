"""
Diagnostic marker identification.

This module identifies SNPs that distinguish between founder populations
and can be used to track haplotype inheritance in derived samples.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from haplophaser.core.frequencies import AlleleFrequencies, VariantAlleleFrequencies

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class MarkerClassification(str, Enum):
    """Classification of diagnostic markers.

    Attributes
    ----------
    FULLY_DIAGNOSTIC
        Allele A fixed (>threshold) in one founder, allele B fixed in another.
    PARTIALLY_DIAGNOSTIC
        Clear differentiation but not fully fixed.
    INFORMATIVE
        Significant frequency difference but not diagnostic.
    NON_INFORMATIVE
        Similar frequencies across founders.
    """

    FULLY_DIAGNOSTIC = "fully_diagnostic"
    PARTIALLY_DIAGNOSTIC = "partially_diagnostic"
    INFORMATIVE = "informative"
    NON_INFORMATIVE = "non_informative"


@dataclass
class DiagnosticMarker:
    """A marker that distinguishes between founder populations.

    Parameters
    ----------
    variant_id : str
        Unique variant identifier (chrom:pos:ref:alt).
    chrom : str
        Chromosome.
    pos : int
        0-based position.
    ref : str
        Reference allele.
    alt : str
        Alternate allele (single alt for biallelic markers).
    founder_alleles : dict[str, str]
        Mapping of founder name to predominant allele.
    founder_frequencies : dict[str, dict[str, float]]
        Full frequency data per founder.
    confidence : float
        Confidence score (0-1) based on frequency clarity and sample size.
    classification : MarkerClassification
        Marker classification type.
    distinguishes : tuple[str, str] | None
        Pair of founders this marker distinguishes (for pairwise markers).
    info : dict
        Additional metadata.
    """

    variant_id: str
    chrom: str
    pos: int
    ref: str
    alt: str
    founder_alleles: dict[str, str]
    founder_frequencies: dict[str, dict[str, float]]
    confidence: float
    classification: MarkerClassification
    distinguishes: tuple[str, str] | None = None
    info: dict = field(default_factory=dict)

    @property
    def pos_1based(self) -> int:
        """Return 1-based position (VCF-style)."""
        return self.pos + 1

    @property
    def is_fully_diagnostic(self) -> bool:
        """Return True if marker is fully diagnostic."""
        return self.classification == MarkerClassification.FULLY_DIAGNOSTIC

    @property
    def is_informative(self) -> bool:
        """Return True if marker is at least informative."""
        return self.classification != MarkerClassification.NON_INFORMATIVE

    def get_founder_allele(self, founder: str) -> str | None:
        """Get the predominant allele for a founder."""
        return self.founder_alleles.get(founder)

    def to_bed_fields(self) -> tuple[str, int, int, str, int, str]:
        """Convert to BED6 format fields.

        Returns
        -------
        tuple
            (chrom, start, end, name, score, strand)
        """
        name = f"{self.ref}>{self.alt}|{self.classification.value}"
        score = int(self.confidence * 1000)
        return (self.chrom, self.pos, self.pos + 1, name, score, ".")


@dataclass
class DiagnosticMarkerSet:
    """Collection of diagnostic markers with metadata.

    Parameters
    ----------
    markers : list[DiagnosticMarker]
        List of diagnostic markers.
    founders : list[str]
        Founder population names.
    parameters : dict
        Parameters used for marker finding.
    """

    markers: list[DiagnosticMarker] = field(default_factory=list)
    founders: list[str] = field(default_factory=list)
    parameters: dict = field(default_factory=dict)

    def __len__(self) -> int:
        """Return number of markers."""
        return len(self.markers)

    def __iter__(self) -> Iterator[DiagnosticMarker]:
        """Iterate over markers."""
        return iter(self.markers)

    def __getitem__(self, idx: int) -> DiagnosticMarker:
        """Get marker by index."""
        return self.markers[idx]

    def add(self, marker: DiagnosticMarker) -> None:
        """Add a marker to the set."""
        self.markers.append(marker)

    @property
    def fully_diagnostic(self) -> list[DiagnosticMarker]:
        """Return fully diagnostic markers."""
        return [m for m in self.markers if m.is_fully_diagnostic]

    @property
    def partially_diagnostic(self) -> list[DiagnosticMarker]:
        """Return partially diagnostic markers."""
        return [
            m for m in self.markers
            if m.classification == MarkerClassification.PARTIALLY_DIAGNOSTIC
        ]

    @property
    def informative(self) -> list[DiagnosticMarker]:
        """Return informative markers."""
        return [
            m for m in self.markers
            if m.classification == MarkerClassification.INFORMATIVE
        ]

    def filter_by_classification(
        self,
        classification: MarkerClassification,
    ) -> list[DiagnosticMarker]:
        """Return markers with a specific classification."""
        return [m for m in self.markers if m.classification == classification]

    def filter_by_chromosome(self, chrom: str) -> list[DiagnosticMarker]:
        """Return markers on a specific chromosome."""
        return [m for m in self.markers if m.chrom == chrom]

    def filter_by_founders(
        self,
        founder1: str,
        founder2: str,
    ) -> list[DiagnosticMarker]:
        """Return markers that distinguish a specific founder pair."""
        pair = (founder1, founder2)
        reverse_pair = (founder2, founder1)
        return [
            m for m in self.markers
            if m.distinguishes in (pair, reverse_pair)
        ]

    def get_chromosomes(self) -> list[str]:
        """Return sorted list of chromosomes with markers."""
        return sorted({m.chrom for m in self.markers})

    def summary(self) -> dict:
        """Generate summary statistics."""
        total = len(self.markers)
        by_class = {
            cls: len(self.filter_by_classification(cls))
            for cls in MarkerClassification
        }
        by_chrom = {}
        for m in self.markers:
            by_chrom[m.chrom] = by_chrom.get(m.chrom, 0) + 1

        return {
            "total": total,
            "by_classification": by_class,
            "by_chromosome": by_chrom,
            "founders": self.founders,
            "parameters": self.parameters,
        }

    def density_by_window(
        self,
        window_size: int = 1_000_000,
    ) -> list[tuple[str, int, int, int, int, int]]:
        """Calculate marker density in genomic windows.

        Parameters
        ----------
        window_size : int
            Window size in base pairs.

        Returns
        -------
        list[tuple]
            List of (chrom, start, end, total_count, diagnostic_count, partial_count).
        """
        # Group markers by chromosome
        by_chrom: dict[str, list[DiagnosticMarker]] = {}
        for m in self.markers:
            if m.chrom not in by_chrom:
                by_chrom[m.chrom] = []
            by_chrom[m.chrom].append(m)

        result = []

        for chrom in sorted(by_chrom.keys()):
            markers = sorted(by_chrom[chrom], key=lambda m: m.pos)
            if not markers:
                continue

            # Find range
            max_pos = max(m.pos for m in markers)

            # Process windows
            for start in range(0, max_pos + window_size, window_size):
                end = start + window_size

                # Count markers in window
                window_markers = [
                    m for m in markers
                    if start <= m.pos < end
                ]

                if window_markers:
                    total = len(window_markers)
                    diag = sum(1 for m in window_markers if m.is_fully_diagnostic)
                    partial = sum(
                        1 for m in window_markers
                        if m.classification == MarkerClassification.PARTIALLY_DIAGNOSTIC
                    )
                    result.append((chrom, start, end, total, diag, partial))

        return result


class DiagnosticMarkerFinder:
    """Find diagnostic markers that distinguish founder populations.

    Parameters
    ----------
    min_freq_diff : float
        Minimum frequency difference between founders for a marker
        to be considered diagnostic.
    max_minor_freq : float
        Maximum minor allele frequency within a founder for the
        marker to be considered fixed.
    min_samples : int
        Minimum samples with data required per population.
    allow_partial : bool
        Include partially diagnostic markers in results.
    fixed_threshold : float
        Frequency threshold for an allele to be considered fixed.
    """

    def __init__(
        self,
        min_freq_diff: float = 0.7,
        max_minor_freq: float = 0.1,
        min_samples: int = 2,
        allow_partial: bool = True,
        fixed_threshold: float = 0.9,
    ) -> None:
        self.min_freq_diff = min_freq_diff
        self.max_minor_freq = max_minor_freq
        self.min_samples = min_samples
        self.allow_partial = allow_partial
        self.fixed_threshold = fixed_threshold

    def find(
        self,
        frequencies: AlleleFrequencies,
        founders: list[str] | None = None,
    ) -> DiagnosticMarkerSet:
        """Find diagnostic markers from allele frequencies.

        Parameters
        ----------
        frequencies : AlleleFrequencies
            Pre-calculated allele frequencies.
        founders : list[str], optional
            Founder population names. If None, uses all populations
            in the frequency data.

        Returns
        -------
        DiagnosticMarkerSet
            Set of identified diagnostic markers.
        """
        if founders is None:
            founders = frequencies.populations

        if len(founders) < 2:
            raise ValueError("Need at least 2 founders to find diagnostic markers")

        result = DiagnosticMarkerSet(
            founders=founders,
            parameters={
                "min_freq_diff": self.min_freq_diff,
                "max_minor_freq": self.max_minor_freq,
                "min_samples": self.min_samples,
                "fixed_threshold": self.fixed_threshold,
            },
        )

        n_processed = 0
        n_diagnostic = 0

        for var_freq in frequencies:
            marker = self._evaluate_variant(var_freq, founders)

            if marker is not None and (marker.is_informative or self.allow_partial):
                result.add(marker)
                if marker.is_fully_diagnostic:
                    n_diagnostic += 1

            n_processed += 1
            if n_processed % 100000 == 0:
                logger.info(
                    f"Processed {n_processed:,} variants, "
                    f"found {len(result):,} markers ({n_diagnostic:,} fully diagnostic)"
                )

        logger.info(
            f"Found {len(result):,} markers "
            f"({n_diagnostic:,} fully diagnostic) from {n_processed:,} variants"
        )

        return result

    def _evaluate_variant(
        self,
        var_freq: VariantAlleleFrequencies,
        founders: list[str],
    ) -> DiagnosticMarker | None:
        """Evaluate a variant for diagnostic potential.

        Parameters
        ----------
        var_freq : VariantAlleleFrequencies
            Allele frequencies for the variant.
        founders : list[str]
            Founder population names.

        Returns
        -------
        DiagnosticMarker or None
            Diagnostic marker if variant qualifies, None otherwise.
        """
        # Check we have data for all founders
        valid_founders = []
        for f in founders:
            pop_freq = var_freq.get_population_freq(f)
            if pop_freq is not None and pop_freq.n_samples >= self.min_samples:
                valid_founders.append(f)

        if len(valid_founders) < 2:
            return None

        # For biallelic markers, we focus on ref vs first alt
        if len(var_freq.alt) != 1:
            # Skip multiallelic for now
            return None

        ref = var_freq.ref
        alt = var_freq.alt[0]

        # Get frequencies for each founder
        founder_freqs: dict[str, dict[str, float]] = {}
        founder_alleles: dict[str, str] = {}

        for f in valid_founders:
            pop_freq = var_freq.get_population_freq(f)
            if pop_freq is None:
                continue

            ref_freq = pop_freq.get_frequency(ref)
            alt_freq = pop_freq.get_frequency(alt)

            founder_freqs[f] = {ref: ref_freq, alt: alt_freq}

            # Determine predominant allele
            if ref_freq >= alt_freq:
                founder_alleles[f] = ref
            else:
                founder_alleles[f] = alt

        if len(founder_freqs) < 2:
            return None

        # Find best pairwise comparison
        best_diff = 0.0
        best_pair: tuple[str, str] | None = None

        for i, f1 in enumerate(valid_founders):
            for f2 in valid_founders[i + 1:]:
                # Check frequency difference for both alleles
                ref_diff = abs(
                    founder_freqs[f1].get(ref, 0) - founder_freqs[f2].get(ref, 0)
                )
                alt_diff = abs(
                    founder_freqs[f1].get(alt, 0) - founder_freqs[f2].get(alt, 0)
                )
                diff = max(ref_diff, alt_diff)

                if diff > best_diff:
                    best_diff = diff
                    best_pair = (f1, f2)

        if best_pair is None or best_diff < self.min_freq_diff:
            return None

        # Classify the marker
        classification = self._classify_marker(
            founder_freqs,
            best_pair,
            ref,
            alt,
        )

        if classification == MarkerClassification.NON_INFORMATIVE:
            return None

        if not self.allow_partial and classification != MarkerClassification.FULLY_DIAGNOSTIC:
            return None

        # Calculate confidence score
        confidence = self._calculate_confidence(
            var_freq,
            valid_founders,
            best_diff,
        )

        return DiagnosticMarker(
            variant_id=var_freq.variant_id,
            chrom=var_freq.chrom,
            pos=var_freq.pos,
            ref=ref,
            alt=alt,
            founder_alleles=founder_alleles,
            founder_frequencies=founder_freqs,
            confidence=confidence,
            classification=classification,
            distinguishes=best_pair,
        )

    def _classify_marker(
        self,
        founder_freqs: dict[str, dict[str, float]],
        pair: tuple[str, str],
        ref: str,
        alt: str,
    ) -> MarkerClassification:
        """Classify a marker based on allele frequencies.

        Parameters
        ----------
        founder_freqs : dict
            Frequency data per founder.
        pair : tuple
            Founder pair being compared.
        ref : str
            Reference allele.
        alt : str
            Alternate allele.

        Returns
        -------
        MarkerClassification
            Classification of the marker.
        """
        f1, f2 = pair

        f1_ref = founder_freqs[f1].get(ref, 0)
        f1_alt = founder_freqs[f1].get(alt, 0)
        f2_ref = founder_freqs[f2].get(ref, 0)
        f2_alt = founder_freqs[f2].get(alt, 0)

        # Check for fully diagnostic (reciprocal fixation)
        f1_fixed_ref = f1_ref >= self.fixed_threshold
        f1_fixed_alt = f1_alt >= self.fixed_threshold
        f2_fixed_ref = f2_ref >= self.fixed_threshold
        f2_fixed_alt = f2_alt >= self.fixed_threshold

        if (f1_fixed_ref and f2_fixed_alt) or (f1_fixed_alt and f2_fixed_ref):
            return MarkerClassification.FULLY_DIAGNOSTIC

        # Check for partially diagnostic
        f1_minor = min(f1_ref, f1_alt)
        f2_minor = min(f2_ref, f2_alt)
        freq_diff = max(abs(f1_ref - f2_ref), abs(f1_alt - f2_alt))

        if (
            freq_diff >= self.min_freq_diff
            and f1_minor <= self.max_minor_freq
            and f2_minor <= self.max_minor_freq
        ):
            return MarkerClassification.PARTIALLY_DIAGNOSTIC

        # Check for informative
        if freq_diff >= self.min_freq_diff:
            return MarkerClassification.INFORMATIVE

        return MarkerClassification.NON_INFORMATIVE

    def _calculate_confidence(
        self,
        var_freq: VariantAlleleFrequencies,
        founders: list[str],
        freq_diff: float,
    ) -> float:
        """Calculate confidence score for a marker.

        Based on frequency clarity and sample size.

        Parameters
        ----------
        var_freq : VariantAlleleFrequencies
            Variant frequency data.
        founders : list[str]
            Founder populations.
        freq_diff : float
            Maximum frequency difference.

        Returns
        -------
        float
            Confidence score (0-1).
        """
        # Component 1: Frequency difference clarity (0-1)
        freq_score = min(freq_diff / 1.0, 1.0)

        # Component 2: Sample size factor
        total_samples = 0
        for f in founders:
            pop_freq = var_freq.get_population_freq(f)
            if pop_freq:
                total_samples += pop_freq.n_samples

        # Diminishing returns on sample size
        sample_score = min(total_samples / 20, 1.0)

        # Component 3: Data completeness (low missing rate)
        total_missing = 0
        for f in founders:
            pop_freq = var_freq.get_population_freq(f)
            if pop_freq:
                total_missing += pop_freq.n_missing

        total_possible = total_samples + total_missing
        completeness = total_samples / total_possible if total_possible > 0 else 0.0

        # Weighted combination
        confidence = (
            0.5 * freq_score +
            0.3 * sample_score +
            0.2 * completeness
        )

        return round(confidence, 3)


def find_diagnostic_markers(
    frequencies: AlleleFrequencies,
    founders: list[str] | None = None,
    min_freq_diff: float = 0.7,
    max_minor_freq: float = 0.1,
    min_samples: int = 2,
) -> DiagnosticMarkerSet:
    """Convenience function to find diagnostic markers.

    Parameters
    ----------
    frequencies : AlleleFrequencies
        Pre-calculated allele frequencies.
    founders : list[str], optional
        Founder populations to compare.
    min_freq_diff : float
        Minimum frequency difference.
    max_minor_freq : float
        Maximum minor allele frequency within founder.
    min_samples : int
        Minimum samples per population.

    Returns
    -------
    DiagnosticMarkerSet
        Identified diagnostic markers.
    """
    finder = DiagnosticMarkerFinder(
        min_freq_diff=min_freq_diff,
        max_minor_freq=max_minor_freq,
        min_samples=min_samples,
    )
    return finder.find(frequencies, founders)
