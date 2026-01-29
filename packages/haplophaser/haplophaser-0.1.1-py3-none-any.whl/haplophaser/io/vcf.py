"""
VCF file reading and parsing.

This module provides functions to read VCF files and convert them to
Haplophaser's internal Variant representation. Uses cyvcf2 for efficient
parsing of both compressed and uncompressed VCF files.

All coordinates are converted from VCF's 1-based system to internal
0-based, half-open intervals on read.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from haplophaser.core.filters import FilterChain, VariantFilter
from haplophaser.core.models import Variant

if TYPE_CHECKING:
    from cyvcf2 import VCF as CyVCF2
    from cyvcf2 import Variant as CyVariant

logger = logging.getLogger(__name__)


class MultiallelicMode(str, Enum):
    """How to handle multiallelic variants.

    Attributes
    ----------
    KEEP
        Keep multiallelic sites as-is.
    SKIP
        Skip multiallelic sites entirely.
    SPLIT
        Split multiallelic sites into biallelic records.
    """

    KEEP = "keep"
    SKIP = "skip"
    SPLIT = "split"


@dataclass
class VCFStats:
    """Statistics from VCF reading.

    Parameters
    ----------
    n_variants : int
        Total variants read.
    n_samples : int
        Number of samples.
    n_filtered : int
        Variants removed by filters.
    n_multiallelic : int
        Multiallelic variants encountered.
    n_failed_conversion : int
        Variants that failed to convert.
    chromosomes : dict[str, int]
        Variant counts per chromosome.
    """

    n_variants: int = 0
    n_samples: int = 0
    n_filtered: int = 0
    n_multiallelic: int = 0
    n_failed_conversion: int = 0
    chromosomes: dict[str, int] = field(default_factory=dict)

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "VCF Statistics:",
            f"  Total variants: {self.n_variants:,}",
            f"  Samples: {self.n_samples}",
            f"  Filtered: {self.n_filtered:,}",
            f"  Multiallelic: {self.n_multiallelic:,}",
            f"  Failed conversion: {self.n_failed_conversion:,}",
            f"  Chromosomes: {len(self.chromosomes)}",
        ]
        return "\n".join(lines)


@dataclass
class Region:
    """A genomic region for filtering.

    Parameters
    ----------
    chrom : str
        Chromosome name.
    start : int
        0-based start position (inclusive).
    end : int
        0-based end position (exclusive).
    """

    chrom: str
    start: int
    end: int

    def to_region_string(self) -> str:
        """Convert to cyvcf2 region string (1-based)."""
        return f"{self.chrom}:{self.start + 1}-{self.end}"


def load_regions_from_bed(path: Path | str) -> list[Region]:
    """Load regions from a BED file.

    Parameters
    ----------
    path : Path or str
        Path to BED file.

    Returns
    -------
    list[Region]
        List of regions.
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
                regions.append(Region(
                    chrom=fields[0],
                    start=int(fields[1]),
                    end=int(fields[2]),
                ))

    logger.info(f"Loaded {len(regions)} regions from {path}")
    return regions


class VCFReader:
    """Context manager for reading VCF files.

    Wraps cyvcf2.VCF with coordinate conversion, filtering, and
    polyploid genotype support.

    Parameters
    ----------
    path : Path or str
        Path to VCF file (.vcf or .vcf.gz).
    samples : list[str], optional
        Subset of samples to load. None loads all samples.
    regions : list[Region], optional
        Genomic regions to read.
    filters : FilterChain or list[VariantFilter], optional
        Variant filters to apply.
    multiallelic : MultiallelicMode
        How to handle multiallelic variants.
    extract_format_fields : bool
        Extract per-sample FORMAT fields (DP, GQ, AD).

    Examples
    --------
    >>> with VCFReader("variants.vcf.gz") as reader:
    ...     for variant in reader:
    ...         print(variant.chrom, variant.pos)

    >>> filters = FilterChain([MAFFilter(0.05), BiallelicFilter()])
    >>> with VCFReader("variants.vcf.gz", filters=filters) as reader:
    ...     variants = list(reader)
    """

    def __init__(
        self,
        path: Path | str,
        samples: list[str] | None = None,
        regions: list[Region] | None = None,
        filters: FilterChain | list[VariantFilter] | None = None,
        multiallelic: MultiallelicMode = MultiallelicMode.KEEP,
        extract_format_fields: bool = True,
    ) -> None:
        self.path = Path(path)
        self.samples = samples
        self.regions = regions
        self.multiallelic = multiallelic
        self.extract_format_fields = extract_format_fields
        self._vcf: CyVCF2 | None = None
        self._sample_names: list[str] = []
        self._stats = VCFStats()

        # Set up filter chain
        if filters is None:
            self._filters: FilterChain | None = None
        elif isinstance(filters, FilterChain):
            self._filters = filters
        else:
            self._filters = FilterChain(filters)

    def __enter__(self) -> VCFReader:
        """Open VCF file for reading."""
        self._open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close VCF file."""
        self.close()

    def _open(self) -> None:
        """Open the VCF file with cyvcf2."""
        from cyvcf2 import VCF as CyVCF2

        if not self.path.exists():
            raise FileNotFoundError(f"VCF file not found: {self.path}")

        logger.info(f"Opening VCF: {self.path}")

        # Build cyvcf2 arguments
        kwargs: dict[str, Any] = {}
        if self.samples is not None:
            kwargs["samples"] = self.samples

        self._vcf = CyVCF2(str(self.path), **kwargs)
        self._sample_names = list(self._vcf.samples)
        self._stats.n_samples = len(self._sample_names)

        logger.info(f"Loaded {len(self._sample_names)} samples from VCF")

    def close(self) -> None:
        """Close the VCF file handle."""
        if self._vcf is not None:
            self._vcf.close()
            self._vcf = None

    @property
    def sample_names(self) -> list[str]:
        """Return list of sample names in VCF."""
        return self._sample_names

    @property
    def contigs(self) -> list[str]:
        """Return list of contig/chromosome names from VCF header."""
        if self._vcf is None:
            raise RuntimeError("VCF not opened")
        return list(self._vcf.seqnames)

    @property
    def stats(self) -> VCFStats:
        """Return reading statistics."""
        return self._stats

    def __iter__(self) -> Iterator[Variant]:
        """Iterate over all variants in VCF."""
        if self.regions:
            # Iterate over specified regions
            for region in self.regions:
                yield from self._iter_region(region)
        else:
            yield from self._iter_internal()

    def _iter_region(self, region: Region) -> Iterator[Variant]:
        """Iterate over variants in a specific region.

        Parameters
        ----------
        region : Region
            Genomic region to fetch.

        Yields
        ------
        Variant
            Variants in the region.
        """
        yield from self._iter_internal(region.to_region_string())

    def fetch(
        self,
        chrom: str,
        start: int | None = None,
        end: int | None = None,
    ) -> Iterator[Variant]:
        """Fetch variants from a genomic region.

        Requires tabix index for VCF.gz files.

        Parameters
        ----------
        chrom : str
            Chromosome/contig name.
        start : int, optional
            0-based start position (inclusive).
        end : int, optional
            0-based end position (exclusive).

        Yields
        ------
        Variant
            Variants in the specified region.
        """
        if self._vcf is None:
            raise RuntimeError("VCF not opened")

        # Build region string (cyvcf2 uses 1-based coordinates)
        if start is not None and end is not None:
            region_str = f"{chrom}:{start + 1}-{end}"
        elif start is not None:
            region_str = f"{chrom}:{start + 1}-"
        else:
            region_str = chrom

        logger.debug(f"Fetching region: {region_str}")
        yield from self._iter_internal(region_str)

    def _iter_internal(self, region: str | None = None) -> Iterator[Variant]:
        """Internal iteration with optional region filtering.

        Parameters
        ----------
        region : str, optional
            Region string for indexed access.

        Yields
        ------
        Variant
            Filtered and converted variants.
        """
        if self._vcf is None:
            raise RuntimeError("VCF not opened")

        iterator = self._vcf(region) if region else self._vcf

        for record in iterator:
            # Handle multiallelic
            if record.ALT and len(record.ALT) > 1:
                self._stats.n_multiallelic += 1
                if self.multiallelic == MultiallelicMode.SKIP:
                    continue
                elif self.multiallelic == MultiallelicMode.SPLIT:
                    # Split into multiple biallelic records
                    for i, _alt in enumerate(record.ALT):
                        variant = self._convert_record(record, alt_index=i)
                        if variant is not None:
                            yield from self._apply_filters(variant)
                    continue

            # Normal processing
            variant = self._convert_record(record)
            if variant is not None:
                yield from self._apply_filters(variant)

    def _apply_filters(self, variant: Variant) -> Iterator[Variant]:
        """Apply filters to a variant.

        Parameters
        ----------
        variant : Variant
            Variant to filter.

        Yields
        ------
        Variant
            Variant if it passes filters.
        """
        self._stats.n_variants += 1

        # Track chromosome counts
        if variant.chrom not in self._stats.chromosomes:
            self._stats.chromosomes[variant.chrom] = 0
        self._stats.chromosomes[variant.chrom] += 1

        if self._filters is None:
            yield variant
        else:
            # Check all filters
            passed = True
            for f in self._filters.filters:
                if not f(variant):
                    passed = False
                    break

            if passed:
                self._filters._output_count += 1
                yield variant
            else:
                self._stats.n_filtered += 1
            self._filters._input_count += 1

    def _convert_record(
        self,
        record: CyVariant,
        alt_index: int | None = None,
    ) -> Variant | None:
        """Convert cyvcf2 Variant record to Haplophaser Variant.

        Parameters
        ----------
        record : cyvcf2.Variant
            Variant record from cyvcf2.
        alt_index : int, optional
            If splitting multiallelic, which alt allele to use.

        Returns
        -------
        Variant or None
            Converted variant, or None if conversion fails.
        """
        try:
            # Determine alleles
            ref = record.REF
            if alt_index is not None:
                # Splitting multiallelic - take specific alt
                alt = [record.ALT[alt_index]] if record.ALT else []
            else:
                alt = list(record.ALT) if record.ALT else []

            # Extract genotypes
            gt_array = record.genotypes
            genotypes: dict[str, list[int]] = {}

            for i, sample in enumerate(self._sample_names):
                # Get allele indices, excluding phase flag
                alleles = gt_array[i][:-1]

                if alt_index is not None:
                    # When splitting, remap alleles: 0=ref, alt_index+1 -> 1, others -> -1
                    remapped = []
                    for a in alleles:
                        if a < 0:
                            remapped.append(-1)
                        elif a == 0:
                            remapped.append(0)
                        elif a == alt_index + 1:
                            remapped.append(1)
                        else:
                            remapped.append(-1)  # Other alts become missing
                    genotypes[sample] = remapped
                else:
                    genotypes[sample] = [int(a) if a >= 0 else -1 for a in alleles]

            # Build info dict
            info: dict[str, Any] = {}

            # Copy INFO fields
            if record.INFO:
                for key, val in record.INFO:
                    info[key] = val

            # Extract per-sample FORMAT fields if requested
            if self.extract_format_fields:
                self._extract_format_fields(record, info)

            return Variant(
                chrom=record.CHROM,
                pos=record.POS - 1,  # Convert to 0-based
                ref=ref,
                alt=alt,
                genotypes=genotypes,
                quality=record.QUAL if record.QUAL is not None else None,
                filter_status=record.FILTER or "PASS",
                info=info,
            )

        except Exception as e:
            logger.warning(f"Failed to convert variant at {record.CHROM}:{record.POS}: {e}")
            self._stats.n_failed_conversion += 1
            return None

    def _extract_format_fields(self, record: CyVariant, info: dict[str, Any]) -> None:
        """Extract per-sample FORMAT fields into info dict.

        Parameters
        ----------
        record : cyvcf2.Variant
            Variant record.
        info : dict
            Info dict to populate.
        """
        # Extract DP (depth) per sample
        try:
            dp_array = record.format("DP")
            if dp_array is not None:
                sample_dp = {}
                for i, sample in enumerate(self._sample_names):
                    val = dp_array[i]
                    # Handle array vs scalar
                    if hasattr(val, "__len__") and len(val) > 0:
                        val = val[0]
                    sample_dp[sample] = int(val) if val >= 0 else None
                info["sample_dp"] = sample_dp
        except Exception:
            pass

        # Extract GQ (genotype quality) per sample
        try:
            gq_array = record.format("GQ")
            if gq_array is not None:
                sample_gq = {}
                for i, sample in enumerate(self._sample_names):
                    val = gq_array[i]
                    if hasattr(val, "__len__") and len(val) > 0:
                        val = val[0]
                    sample_gq[sample] = int(val) if val >= 0 else None
                info["sample_gq"] = sample_gq
        except Exception:
            pass

        # Extract AD (allelic depth) per sample
        try:
            ad_array = record.format("AD")
            if ad_array is not None:
                sample_ad = {}
                for i, sample in enumerate(self._sample_names):
                    val = ad_array[i]
                    if val is not None and hasattr(val, "__len__"):
                        sample_ad[sample] = [int(v) if v >= 0 else 0 for v in val]
                    else:
                        sample_ad[sample] = None
                info["sample_ad"] = sample_ad
        except Exception:
            pass


# ============================================================================
# Convenience Functions
# ============================================================================


def read_vcf(
    path: Path | str,
    samples: list[str] | None = None,
    regions: list[Region] | str | Path | None = None,
    filters: FilterChain | list[VariantFilter] | None = None,
    multiallelic: MultiallelicMode = MultiallelicMode.KEEP,
) -> Iterator[Variant]:
    """Iterate over variants in a VCF file.

    Convenience function that handles VCF opening and closing.

    Parameters
    ----------
    path : Path or str
        Path to VCF file.
    samples : list[str], optional
        Subset of samples to load.
    regions : list[Region], str, or Path, optional
        Regions to read. If str/Path, loads from BED file.
    filters : FilterChain or list[VariantFilter], optional
        Variant filters to apply.
    multiallelic : MultiallelicMode
        How to handle multiallelic variants.

    Yields
    ------
    Variant
        Variants from the VCF file.

    Examples
    --------
    >>> for variant in read_vcf("data.vcf.gz"):
    ...     process(variant)

    >>> from haplophaser.core.filters import MAFFilter, BiallelicFilter
    >>> filters = [MAFFilter(0.05), BiallelicFilter()]
    >>> for variant in read_vcf("data.vcf.gz", filters=filters):
    ...     process(variant)
    """
    # Handle regions argument
    if isinstance(regions, (str, Path)):
        regions = load_regions_from_bed(regions)

    with VCFReader(
        path,
        samples=samples,
        regions=regions,
        filters=filters,
        multiallelic=multiallelic,
    ) as reader:
        yield from reader


def load_vcf(
    path: Path | str,
    samples: list[str] | None = None,
    regions: list[Region] | str | Path | None = None,
    filters: FilterChain | list[VariantFilter] | None = None,
    multiallelic: MultiallelicMode = MultiallelicMode.KEEP,
    max_variants: int | None = None,
) -> list[Variant]:
    """Load all variants from a VCF file into memory.

    Use for smaller files where in-memory processing is preferred.
    For large files, use read_vcf() for streaming iteration.

    Parameters
    ----------
    path : Path or str
        Path to VCF file.
    samples : list[str], optional
        Subset of samples to load.
    regions : list[Region], str, or Path, optional
        Regions to read.
    filters : FilterChain or list[VariantFilter], optional
        Variant filters to apply.
    multiallelic : MultiallelicMode
        How to handle multiallelic variants.
    max_variants : int, optional
        Maximum variants to load.

    Returns
    -------
    list[Variant]
        List of variants.
    """
    variants = []

    for variant in read_vcf(path, samples, regions, filters, multiallelic):
        variants.append(variant)
        if max_variants is not None and len(variants) >= max_variants:
            break

    return variants


def iter_variants(
    path: Path | str,
    samples: list[str] | None = None,
    filters: FilterChain | list[VariantFilter] | None = None,
) -> Iterator[Variant]:
    """Iterate over variants in a VCF file (legacy function).

    Parameters
    ----------
    path : Path or str
        Path to VCF file.
    samples : list[str], optional
        Subset of samples to load.
    filters : FilterChain or list[VariantFilter], optional
        Variant filters to apply.

    Yields
    ------
    Variant
        Variants from the VCF file.
    """
    yield from read_vcf(path, samples=samples, filters=filters)


def read_vcf_region(
    path: Path | str,
    chrom: str,
    start: int,
    end: int,
    samples: list[str] | None = None,
    filters: FilterChain | list[VariantFilter] | None = None,
) -> list[Variant]:
    """Read all variants in a genomic region.

    Parameters
    ----------
    path : Path or str
        Path to tabix-indexed VCF.gz file.
    chrom : str
        Chromosome/contig name.
    start : int
        0-based start position (inclusive).
    end : int
        0-based end position (exclusive).
    samples : list[str], optional
        Subset of samples to load.
    filters : FilterChain or list[VariantFilter], optional
        Variant filters to apply.

    Returns
    -------
    list[Variant]
        Variants in the specified region.
    """
    region = Region(chrom=chrom, start=start, end=end)
    return load_vcf(path, samples=samples, regions=[region], filters=filters)


def get_sample_names(path: Path | str) -> list[str]:
    """Get sample names from VCF header.

    Parameters
    ----------
    path : Path or str
        Path to VCF file.

    Returns
    -------
    list[str]
        Sample names from VCF.
    """
    with VCFReader(path) as reader:
        return reader.sample_names


def get_vcf_contigs(path: Path | str) -> list[str]:
    """Get contig/chromosome names from VCF header.

    Parameters
    ----------
    path : Path or str
        Path to VCF file.

    Returns
    -------
    list[str]
        Contig names from VCF header.
    """
    with VCFReader(path) as reader:
        return reader.contigs


def count_variants(
    path: Path | str,
    chrom: str | None = None,
    filters: FilterChain | list[VariantFilter] | None = None,
) -> int:
    """Count variants in VCF file or region.

    Parameters
    ----------
    path : Path or str
        Path to VCF file.
    chrom : str, optional
        Restrict count to this chromosome.
    filters : FilterChain or list[VariantFilter], optional
        Only count variants passing filters.

    Returns
    -------
    int
        Number of variants.
    """
    regions = [Region(chrom=chrom, start=0, end=int(1e12))] if chrom else None
    return sum(1 for _ in read_vcf(path, regions=regions, filters=filters))


def get_vcf_stats(
    path: Path | str,
    samples: list[str] | None = None,
    filters: FilterChain | list[VariantFilter] | None = None,
) -> VCFStats:
    """Get statistics from a VCF file.

    Parameters
    ----------
    path : Path or str
        Path to VCF file.
    samples : list[str], optional
        Subset of samples.
    filters : FilterChain or list[VariantFilter], optional
        Filters to apply.

    Returns
    -------
    VCFStats
        Statistics from reading the VCF.
    """
    with VCFReader(path, samples=samples, filters=filters) as reader:
        # Consume iterator to gather stats
        for _ in reader:
            pass
        return reader.stats


def validate_vcf_samples(
    vcf_path: Path | str,
    expected_samples: list[str],
) -> tuple[list[str], list[str]]:
    """Validate that expected samples exist in VCF.

    Parameters
    ----------
    vcf_path : Path or str
        Path to VCF file.
    expected_samples : list[str]
        Sample names that should be present.

    Returns
    -------
    tuple[list[str], list[str]]
        (found_samples, missing_samples)
    """
    vcf_samples = set(get_sample_names(vcf_path))
    found = [s for s in expected_samples if s in vcf_samples]
    missing = [s for s in expected_samples if s not in vcf_samples]
    return found, missing
