"""
Composable variant filtering system for Phaser.

Provides a set of filters that can be chained together to create
flexible filtering pipelines. Each filter tracks statistics about
how many variants it removed.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from haplophaser.core.models import Variant

logger = logging.getLogger(__name__)


@dataclass
class FilterStats:
    """Statistics for a single filter's operation.

    Parameters
    ----------
    name : str
        Filter name.
    passed : int
        Number of variants that passed this filter.
    failed : int
        Number of variants that failed this filter.
    """

    name: str
    passed: int = 0
    failed: int = 0

    @property
    def total(self) -> int:
        """Total variants processed."""
        return self.passed + self.failed

    @property
    def pass_rate(self) -> float:
        """Fraction of variants that passed (0-1)."""
        if self.total == 0:
            return 0.0
        return self.passed / self.total

    def __str__(self) -> str:
        """Human-readable summary."""
        return f"{self.name}: {self.passed}/{self.total} passed ({self.pass_rate:.1%})"


@dataclass
class FilterChainStats:
    """Statistics for a complete filter chain.

    Parameters
    ----------
    filter_stats : list[FilterStats]
        Per-filter statistics.
    input_count : int
        Total variants input to chain.
    output_count : int
        Total variants output from chain.
    """

    filter_stats: list[FilterStats] = field(default_factory=list)
    input_count: int = 0
    output_count: int = 0

    @property
    def overall_pass_rate(self) -> float:
        """Overall pass rate through entire chain."""
        if self.input_count == 0:
            return 0.0
        return self.output_count / self.input_count

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "Filter Chain Summary:",
            f"  Input variants: {self.input_count:,}",
            f"  Output variants: {self.output_count:,}",
            f"  Overall pass rate: {self.overall_pass_rate:.1%}",
            "",
            "Per-filter breakdown:",
        ]
        for fs in self.filter_stats:
            lines.append(f"  {fs}")
        return "\n".join(lines)


class VariantFilter(ABC):
    """Abstract base class for variant filters.

    Subclasses implement the `test` method to determine if a variant
    passes the filter criteria.
    """

    def __init__(self, name: str | None = None) -> None:
        """Initialize filter.

        Parameters
        ----------
        name : str, optional
            Filter name for reporting. Defaults to class name.
        """
        self._name = name or self.__class__.__name__
        self._stats = FilterStats(name=self._name)

    @property
    def name(self) -> str:
        """Filter name."""
        return self._name

    @property
    def stats(self) -> FilterStats:
        """Filter statistics."""
        return self._stats

    def reset_stats(self) -> None:
        """Reset filter statistics."""
        self._stats = FilterStats(name=self._name)

    @abstractmethod
    def test(self, variant: Variant) -> bool:
        """Test if a variant passes this filter.

        Parameters
        ----------
        variant : Variant
            Variant to test.

        Returns
        -------
        bool
            True if variant passes, False if it should be filtered out.
        """
        ...

    def __call__(self, variant: Variant) -> bool:
        """Apply filter to a variant, updating statistics.

        Parameters
        ----------
        variant : Variant
            Variant to test.

        Returns
        -------
        bool
            True if variant passes.
        """
        result = self.test(variant)
        if result:
            self._stats.passed += 1
        else:
            self._stats.failed += 1
        return result

    def apply(self, variants: Iterable[Variant]) -> Iterator[Variant]:
        """Apply filter to an iterable of variants.

        Parameters
        ----------
        variants : Iterable[Variant]
            Input variants.

        Yields
        ------
        Variant
            Variants that pass the filter.
        """
        for variant in variants:
            if self(variant):
                yield variant


class FilterChain:
    """A chain of filters applied sequentially.

    Variants must pass all filters to be included in output.

    Parameters
    ----------
    filters : list[VariantFilter]
        List of filters to apply in order.

    Examples
    --------
    >>> chain = FilterChain([
    ...     BialllelicFilter(),
    ...     MaxMissingFilter(max_missing=0.2),
    ...     MAFFilter(min_maf=0.05),
    ... ])
    >>> filtered = list(chain.apply(variants))
    >>> print(chain.stats.summary())
    """

    def __init__(self, filters: list[VariantFilter] | None = None) -> None:
        self._filters = filters or []
        self._input_count = 0
        self._output_count = 0

    @property
    def filters(self) -> list[VariantFilter]:
        """List of filters in chain."""
        return self._filters

    def add(self, filter_: VariantFilter) -> FilterChain:
        """Add a filter to the chain.

        Parameters
        ----------
        filter_ : VariantFilter
            Filter to add.

        Returns
        -------
        FilterChain
            Self for chaining.
        """
        self._filters.append(filter_)
        return self

    def reset_stats(self) -> None:
        """Reset statistics for all filters."""
        self._input_count = 0
        self._output_count = 0
        for f in self._filters:
            f.reset_stats()

    @property
    def stats(self) -> FilterChainStats:
        """Get statistics for entire chain."""
        return FilterChainStats(
            filter_stats=[f.stats for f in self._filters],
            input_count=self._input_count,
            output_count=self._output_count,
        )

    def apply(self, variants: Iterable[Variant]) -> Iterator[Variant]:
        """Apply all filters to variants.

        Parameters
        ----------
        variants : Iterable[Variant]
            Input variants.

        Yields
        ------
        Variant
            Variants that pass all filters.
        """
        for variant in variants:
            self._input_count += 1
            passed = True
            for f in self._filters:
                if not f(variant):
                    passed = False
                    break
            if passed:
                self._output_count += 1
                yield variant


# ============================================================================
# Concrete Filter Implementations
# ============================================================================


class MinQualityFilter(VariantFilter):
    """Filter variants by minimum quality score.

    Parameters
    ----------
    min_qual : float
        Minimum QUAL value.
    """

    def __init__(self, min_qual: float = 30.0) -> None:
        super().__init__(name=f"MinQual({min_qual})")
        self.min_qual = min_qual

    def test(self, variant: Variant) -> bool:
        """Test if variant quality meets threshold."""
        if variant.quality is None:
            return True  # Pass variants without quality
        return variant.quality >= self.min_qual


class MinDepthFilter(VariantFilter):
    """Filter variants by minimum read depth.

    Requires variant.info to contain per-sample depth information,
    or uses total DP from INFO field.

    Parameters
    ----------
    min_dp : int
        Minimum depth.
    per_sample : bool
        If True, all samples must meet threshold. If False, uses
        mean or total depth.
    """

    def __init__(self, min_dp: int = 10, per_sample: bool = False) -> None:
        super().__init__(name=f"MinDepth({min_dp})")
        self.min_dp = min_dp
        self.per_sample = per_sample

    def test(self, variant: Variant) -> bool:
        """Test if variant depth meets threshold."""
        # Check for per-sample depth in info
        sample_depths = variant.info.get("sample_dp", {})

        if self.per_sample and sample_depths:
            # All samples must meet threshold
            return all(not (dp is not None and dp < self.min_dp) for dp in sample_depths.values())

        # Fall back to total/mean DP
        if sample_depths:
            valid_depths = [d for d in sample_depths.values() if d is not None]
            if valid_depths:
                mean_dp = sum(valid_depths) / len(valid_depths)
                return mean_dp >= self.min_dp

        # Check INFO DP field
        total_dp = variant.info.get("DP")
        if total_dp is not None:
            return total_dp >= self.min_dp

        # No depth info, pass by default
        return True


class MinGQFilter(VariantFilter):
    """Filter variants by minimum genotype quality.

    Parameters
    ----------
    min_gq : int
        Minimum GQ value.
    require_all : bool
        If True, all samples must meet threshold.
        If False, at least one sample must meet threshold.
    """

    def __init__(self, min_gq: int = 20, require_all: bool = False) -> None:
        super().__init__(name=f"MinGQ({min_gq})")
        self.min_gq = min_gq
        self.require_all = require_all

    def test(self, variant: Variant) -> bool:
        """Test if variant genotype quality meets threshold."""
        sample_gqs = variant.info.get("sample_gq", {})

        if not sample_gqs:
            return True  # No GQ info, pass by default

        valid_gqs = [gq for gq in sample_gqs.values() if gq is not None]
        if not valid_gqs:
            return True

        if self.require_all:
            return all(gq >= self.min_gq for gq in valid_gqs)
        else:
            return any(gq >= self.min_gq for gq in valid_gqs)


class MaxMissingFilter(VariantFilter):
    """Filter variants by maximum missing data rate.

    Parameters
    ----------
    max_missing : float
        Maximum fraction of samples with missing genotypes (0-1).
    """

    def __init__(self, max_missing: float = 0.2) -> None:
        super().__init__(name=f"MaxMissing({max_missing})")
        self.max_missing = max_missing

    def test(self, variant: Variant) -> bool:
        """Test if variant missing rate is below threshold."""
        if not variant.genotypes:
            return False

        n_missing = sum(
            1 for gt in variant.genotypes.values() if all(a == -1 for a in gt)
        )
        missing_rate = n_missing / len(variant.genotypes)
        return missing_rate <= self.max_missing


class MAFFilter(VariantFilter):
    """Filter variants by minor allele frequency.

    Parameters
    ----------
    min_maf : float
        Minimum minor allele frequency (0-0.5).
    """

    def __init__(self, min_maf: float = 0.05) -> None:
        super().__init__(name=f"MAF({min_maf})")
        self.min_maf = min_maf

    def test(self, variant: Variant) -> bool:
        """Test if variant MAF meets threshold."""
        if not variant.genotypes:
            return False

        # Count alleles across all samples
        allele_counts: dict[int, int] = {}
        total = 0

        for gt in variant.genotypes.values():
            for allele in gt:
                if allele >= 0:  # Skip missing
                    allele_counts[allele] = allele_counts.get(allele, 0) + 1
                    total += 1

        if total == 0 or len(allele_counts) < 2:
            return False

        # MAF is frequency of least common allele
        min_count = min(allele_counts.values())
        maf = min_count / total
        return maf >= self.min_maf


class BiallelicFilter(VariantFilter):
    """Filter to keep only biallelic variants.

    Parameters
    ----------
    include_monomorphic : bool
        If True, also keep monomorphic sites (ref only).
    """

    def __init__(self, include_monomorphic: bool = False) -> None:
        super().__init__(name="Biallelic")
        self.include_monomorphic = include_monomorphic

    def test(self, variant: Variant) -> bool:
        """Test if variant is biallelic."""
        n_alleles = variant.n_alleles
        if n_alleles == 2:
            return True
        return bool(self.include_monomorphic and n_alleles == 1)


class SNPFilter(VariantFilter):
    """Filter to keep only SNPs (single nucleotide polymorphisms)."""

    def __init__(self) -> None:
        super().__init__(name="SNP")

    def test(self, variant: Variant) -> bool:
        """Test if variant is a SNP."""
        return variant.is_snp


class PassFilter(VariantFilter):
    """Filter to keep only variants with PASS filter status."""

    def __init__(self) -> None:
        super().__init__(name="PASS")

    def test(self, variant: Variant) -> bool:
        """Test if variant has PASS status."""
        return variant.filter_status in ("PASS", ".", "")


class RegionFilter(VariantFilter):
    """Filter variants to specified genomic regions.

    Parameters
    ----------
    regions : list[tuple[str, int, int]]
        List of (chrom, start, end) tuples. Coordinates are 0-based, half-open.
    """

    def __init__(self, regions: list[tuple[str, int, int]]) -> None:
        super().__init__(name=f"Region({len(regions)} regions)")
        # Build interval index for efficient lookup
        self._regions: dict[str, list[tuple[int, int]]] = {}
        for chrom, start, end in regions:
            if chrom not in self._regions:
                self._regions[chrom] = []
            self._regions[chrom].append((start, end))
        # Sort regions by start position for each chromosome
        for chrom in self._regions:
            self._regions[chrom].sort()

    @classmethod
    def from_bed(cls, path: Path | str) -> RegionFilter:
        """Load regions from a BED file.

        Parameters
        ----------
        path : Path or str
            Path to BED file (tab-separated: chrom, start, end).

        Returns
        -------
        RegionFilter
            Filter configured with BED regions.
        """
        regions = []
        path = Path(path)

        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("track"):
                    continue
                fields = line.split("\t")
                if len(fields) >= 3:
                    chrom = fields[0]
                    start = int(fields[1])
                    end = int(fields[2])
                    regions.append((chrom, start, end))

        logger.info(f"Loaded {len(regions)} regions from {path}")
        return cls(regions)

    def test(self, variant: Variant) -> bool:
        """Test if variant falls within any region."""
        if variant.chrom not in self._regions:
            return False

        pos = variant.pos
        # Binary search could be used here for large region lists
        for start, end in self._regions[variant.chrom]:
            if start <= pos < end:
                return True
            if start > pos:
                break  # Regions are sorted, no need to check further

        return False


class ChromosomeFilter(VariantFilter):
    """Filter variants to specified chromosomes.

    Parameters
    ----------
    chromosomes : list[str]
        List of chromosome names to include.
    exclude : bool
        If True, exclude listed chromosomes instead of including them.
    """

    def __init__(self, chromosomes: list[str], exclude: bool = False) -> None:
        mode = "exclude" if exclude else "include"
        super().__init__(name=f"Chrom({mode} {len(chromosomes)})")
        self._chromosomes = set(chromosomes)
        self._exclude = exclude

    def test(self, variant: Variant) -> bool:
        """Test if variant is on allowed chromosome."""
        in_set = variant.chrom in self._chromosomes
        return not in_set if self._exclude else in_set


class InformativeFilter(VariantFilter):
    """Filter to keep only informative variants for haplotype analysis.

    A variant is informative if founders differ at that position.

    Parameters
    ----------
    founder_samples : list[str]
        List of founder sample names.
    min_diff_founders : int
        Minimum number of founders that must differ.
    """

    def __init__(
        self,
        founder_samples: list[str],
        min_diff_founders: int = 2,
    ) -> None:
        super().__init__(name=f"Informative({len(founder_samples)} founders)")
        self._founders = set(founder_samples)
        self._min_diff = min_diff_founders

    def test(self, variant: Variant) -> bool:
        """Test if variant is informative (founders differ)."""
        # Get founder genotypes as tuples for comparison
        founder_gts: list[tuple[int, ...]] = []
        for sample, gt in variant.genotypes.items():
            if sample in self._founders:
                # Skip samples with all missing
                if not all(a == -1 for a in gt):
                    founder_gts.append(tuple(sorted(gt)))

        if len(founder_gts) < 2:
            return False

        # Count unique genotypes among founders
        unique_gts = set(founder_gts)
        return len(unique_gts) >= self._min_diff


class PolyploidGenotypeFilter(VariantFilter):
    """Filter for polyploid-specific genotype criteria.

    Parameters
    ----------
    expected_ploidy : int
        Expected ploidy level for all samples.
    strict : bool
        If True, reject variants where any sample has unexpected ploidy.
    """

    def __init__(self, expected_ploidy: int = 2, strict: bool = False) -> None:
        super().__init__(name=f"Ploidy({expected_ploidy})")
        self._expected_ploidy = expected_ploidy
        self._strict = strict

    def test(self, variant: Variant) -> bool:
        """Test if variant has expected ploidy in genotypes."""
        for sample, gt in variant.genotypes.items():
            if len(gt) != self._expected_ploidy:
                if self._strict:
                    return False
                logger.warning(
                    f"Sample {sample} has ploidy {len(gt)}, expected {self._expected_ploidy}"
                )
        return True


# ============================================================================
# Convenience functions
# ============================================================================


def create_default_filter_chain(
    min_qual: float = 30.0,
    max_missing: float = 0.2,
    min_maf: float = 0.01,
    biallelic_only: bool = True,
    snps_only: bool = False,
) -> FilterChain:
    """Create a filter chain with common default settings.

    Parameters
    ----------
    min_qual : float
        Minimum variant quality.
    max_missing : float
        Maximum missing rate.
    min_maf : float
        Minimum minor allele frequency.
    biallelic_only : bool
        Keep only biallelic variants.
    snps_only : bool
        Keep only SNPs.

    Returns
    -------
    FilterChain
        Configured filter chain.
    """
    filters: list[VariantFilter] = [
        PassFilter(),
        MinQualityFilter(min_qual=min_qual),
    ]

    if biallelic_only:
        filters.append(BiallelicFilter())

    if snps_only:
        filters.append(SNPFilter())

    filters.extend([
        MaxMissingFilter(max_missing=max_missing),
        MAFFilter(min_maf=min_maf),
    ])

    return FilterChain(filters)
