"""
Allele frequency calculation per population.

This module provides functions to calculate allele frequencies for each
population at each variant site. Handles polyploidy correctly by counting
allele dosage rather than genotypes.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from haplophaser.core.models import Population, PopulationRole, Variant

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class AlleleFrequency:
    """Allele frequencies for a single variant at a population.

    Parameters
    ----------
    population : str
        Population name.
    frequencies : dict[str, float]
        Mapping of allele (as string) to frequency.
    allele_counts : dict[str, int]
        Raw counts of each allele.
    total_alleles : int
        Total alleles counted (excluding missing).
    n_samples : int
        Number of samples with data.
    n_missing : int
        Number of samples with missing data.
    """

    population: str
    frequencies: dict[str, float]
    allele_counts: dict[str, int]
    total_alleles: int
    n_samples: int
    n_missing: int

    @property
    def major_allele(self) -> str | None:
        """Return the most frequent allele."""
        if not self.frequencies:
            return None
        return max(self.frequencies.items(), key=lambda x: x[1])[0]

    @property
    def minor_allele(self) -> str | None:
        """Return the least frequent allele (excluding fixed alleles)."""
        if len(self.frequencies) < 2:
            return None
        sorted_alleles = sorted(self.frequencies.items(), key=lambda x: x[1])
        return sorted_alleles[0][0]

    @property
    def maf(self) -> float:
        """Return minor allele frequency."""
        if len(self.frequencies) < 2:
            return 0.0
        return min(self.frequencies.values())

    @property
    def is_fixed(self) -> bool:
        """Return True if one allele is at frequency 1.0."""
        return any(f >= 0.999 for f in self.frequencies.values())

    def get_frequency(self, allele: str) -> float:
        """Get frequency of a specific allele."""
        return self.frequencies.get(allele, 0.0)


@dataclass
class VariantAlleleFrequencies:
    """Allele frequencies for a variant across all populations.

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
    alt : list[str]
        Alternate alleles.
    population_frequencies : dict[str, AlleleFrequency]
        Frequencies per population.
    """

    variant_id: str
    chrom: str
    pos: int
    ref: str
    alt: list[str]
    population_frequencies: dict[str, AlleleFrequency] = field(default_factory=dict)

    @property
    def alleles(self) -> list[str]:
        """Return all alleles (ref + alt)."""
        return [self.ref] + self.alt

    def get_frequency(self, population: str, allele: str) -> float:
        """Get frequency of an allele in a population."""
        if population not in self.population_frequencies:
            return 0.0
        return self.population_frequencies[population].get_frequency(allele)

    def get_population_freq(self, population: str) -> AlleleFrequency | None:
        """Get AlleleFrequency object for a population."""
        return self.population_frequencies.get(population)

    def max_freq_diff(self, allele: str, populations: list[str] | None = None) -> float:
        """Calculate maximum frequency difference for an allele across populations.

        Parameters
        ----------
        allele : str
            Allele to check.
        populations : list[str], optional
            Populations to compare. If None, uses all populations.

        Returns
        -------
        float
            Maximum difference in frequency between any two populations.
        """
        pops = populations or list(self.population_frequencies.keys())
        if len(pops) < 2:
            return 0.0

        freqs = [self.get_frequency(p, allele) for p in pops]
        return max(freqs) - min(freqs)

    def frequency_difference(self, pop1: str, pop2: str, allele: str) -> float:
        """Calculate frequency difference for an allele between two populations."""
        f1 = self.get_frequency(pop1, allele)
        f2 = self.get_frequency(pop2, allele)
        return abs(f1 - f2)


@dataclass
class AlleleFrequencies:
    """Collection of allele frequencies for multiple variants.

    This is the main container for allele frequency data, providing
    convenient accessors for downstream analysis.
    """

    frequencies: dict[str, VariantAlleleFrequencies] = field(default_factory=dict)
    populations: list[str] = field(default_factory=list)

    def __len__(self) -> int:
        """Return number of variants."""
        return len(self.frequencies)

    def __iter__(self) -> Iterator[VariantAlleleFrequencies]:
        """Iterate over variant frequencies."""
        return iter(self.frequencies.values())

    def __getitem__(self, variant_id: str) -> VariantAlleleFrequencies:
        """Get frequencies for a specific variant."""
        return self.frequencies[variant_id]

    def __contains__(self, variant_id: str) -> bool:
        """Check if variant is present."""
        return variant_id in self.frequencies

    def get(self, variant_id: str) -> VariantAlleleFrequencies | None:
        """Get frequencies for a variant, or None if not present."""
        return self.frequencies.get(variant_id)

    def add(self, variant_freq: VariantAlleleFrequencies) -> None:
        """Add frequencies for a variant."""
        self.frequencies[variant_freq.variant_id] = variant_freq

    def variant_ids(self) -> list[str]:
        """Return list of all variant IDs."""
        return list(self.frequencies.keys())

    def filter_by_chromosome(self, chrom: str) -> AlleleFrequencies:
        """Return frequencies for variants on a specific chromosome."""
        filtered = AlleleFrequencies(populations=self.populations)
        for var_freq in self.frequencies.values():
            if var_freq.chrom == chrom:
                filtered.add(var_freq)
        return filtered


class AlleleFrequencyCalculator:
    """Calculate allele frequencies per population from variant data.

    Handles polyploidy correctly by counting allele dosage, not genotype.
    Can use read counts (AD field) for pooled samples if available.

    Parameters
    ----------
    use_read_counts : bool
        If True and AD field available, use read counts instead of
        genotype calls for frequency estimation. Useful for pooled samples.
    min_samples : int
        Minimum samples with data required to report frequency.
    """

    def __init__(
        self,
        use_read_counts: bool = False,
        min_samples: int = 1,
    ) -> None:
        self.use_read_counts = use_read_counts
        self.min_samples = min_samples

    def calculate(
        self,
        variants: Iterable[Variant],
        populations: list[Population],
    ) -> AlleleFrequencies:
        """Calculate allele frequencies for all variants.

        Parameters
        ----------
        variants : Iterable[Variant]
            Variants to process.
        populations : list[Population]
            Populations with sample assignments.

        Returns
        -------
        AlleleFrequencies
            Allele frequencies per population per variant.
        """
        # Build sample -> population mapping
        sample_to_pop = self._build_sample_mapping(populations)
        pop_names = [p.name for p in populations]

        result = AlleleFrequencies(populations=pop_names)
        n_processed = 0

        for variant in variants:
            var_freq = self._calculate_variant(variant, sample_to_pop, pop_names)
            if var_freq is not None:
                result.add(var_freq)

            n_processed += 1
            if n_processed % 100000 == 0:
                logger.info(f"Processed {n_processed:,} variants")

        logger.info(f"Calculated frequencies for {len(result):,} variants")
        return result

    def calculate_single(
        self,
        variant: Variant,
        populations: list[Population],
    ) -> VariantAlleleFrequencies | None:
        """Calculate allele frequencies for a single variant.

        Parameters
        ----------
        variant : Variant
            Variant to process.
        populations : list[Population]
            Populations with sample assignments.

        Returns
        -------
        VariantAlleleFrequencies or None
            Allele frequencies, or None if insufficient data.
        """
        sample_to_pop = self._build_sample_mapping(populations)
        pop_names = [p.name for p in populations]
        return self._calculate_variant(variant, sample_to_pop, pop_names)

    def _build_sample_mapping(
        self,
        populations: list[Population],
    ) -> dict[str, str]:
        """Build mapping of sample name to population name."""
        mapping = {}
        for pop in populations:
            for sample in pop.samples:
                mapping[sample.name] = pop.name
        return mapping

    def _calculate_variant(
        self,
        variant: Variant,
        sample_to_pop: dict[str, str],
        pop_names: list[str],
    ) -> VariantAlleleFrequencies | None:
        """Calculate frequencies for a single variant.

        Parameters
        ----------
        variant : Variant
            Variant to process.
        sample_to_pop : dict[str, str]
            Sample to population mapping.
        pop_names : list[str]
            Population names.

        Returns
        -------
        VariantAlleleFrequencies or None
            Frequencies, or None if insufficient data.
        """
        # Build variant ID
        alt_str = ",".join(variant.alt) if variant.alt else "."
        variant_id = f"{variant.chrom}:{variant.pos}:{variant.ref}:{alt_str}"

        # Initialize per-population counts
        pop_counts: dict[str, dict[str, int]] = {p: {} for p in pop_names}
        pop_samples: dict[str, int] = dict.fromkeys(pop_names, 0)
        pop_missing: dict[str, int] = dict.fromkeys(pop_names, 0)

        # Get alleles
        alleles = [variant.ref] + variant.alt

        # Check if we should use read counts
        use_ad = (
            self.use_read_counts
            and "sample_ad" in variant.info
            and variant.info["sample_ad"]
        )

        # Process each sample
        for sample, genotype in variant.genotypes.items():
            if sample not in sample_to_pop:
                continue

            pop = sample_to_pop[sample]

            # Check for missing genotype
            if all(a == -1 for a in genotype):
                pop_missing[pop] += 1
                continue

            pop_samples[pop] += 1

            if use_ad:
                # Use allelic depths
                ad = variant.info["sample_ad"].get(sample)
                if ad and len(ad) == len(alleles):
                    for i, allele in enumerate(alleles):
                        count = ad[i] if ad[i] > 0 else 0
                        if allele not in pop_counts[pop]:
                            pop_counts[pop][allele] = 0
                        pop_counts[pop][allele] += count
                else:
                    # Fall back to genotype counts
                    self._add_genotype_counts(genotype, alleles, pop_counts[pop])
            else:
                # Use genotype counts (dosage)
                self._add_genotype_counts(genotype, alleles, pop_counts[pop])

        # Convert counts to frequencies
        pop_freqs: dict[str, AlleleFrequency] = {}

        for pop in pop_names:
            if pop_samples[pop] < self.min_samples:
                continue

            counts = pop_counts[pop]
            total = sum(counts.values())

            if total == 0:
                continue

            frequencies = {allele: count / total for allele, count in counts.items()}

            pop_freqs[pop] = AlleleFrequency(
                population=pop,
                frequencies=frequencies,
                allele_counts=counts,
                total_alleles=total,
                n_samples=pop_samples[pop],
                n_missing=pop_missing[pop],
            )

        if not pop_freqs:
            return None

        return VariantAlleleFrequencies(
            variant_id=variant_id,
            chrom=variant.chrom,
            pos=variant.pos,
            ref=variant.ref,
            alt=list(variant.alt),
            population_frequencies=pop_freqs,
        )

    def _add_genotype_counts(
        self,
        genotype: list[int],
        alleles: list[str],
        counts: dict[str, int],
    ) -> None:
        """Add allele counts from a genotype.

        Parameters
        ----------
        genotype : list[int]
            Allele indices for the sample.
        alleles : list[str]
            All alleles (ref + alt).
        counts : dict[str, int]
            Counts dictionary to update.
        """
        for allele_idx in genotype:
            if 0 <= allele_idx < len(alleles):
                allele = alleles[allele_idx]
                if allele not in counts:
                    counts[allele] = 0
                counts[allele] += 1


def calculate_population_frequencies(
    variants: Iterable[Variant],
    populations: list[Population],
    use_read_counts: bool = False,
    min_samples: int = 1,
) -> AlleleFrequencies:
    """Convenience function to calculate allele frequencies.

    Parameters
    ----------
    variants : Iterable[Variant]
        Variants to process.
    populations : list[Population]
        Populations with sample assignments.
    use_read_counts : bool
        Use AD field if available.
    min_samples : int
        Minimum samples required per population.

    Returns
    -------
    AlleleFrequencies
        Allele frequencies per population.
    """
    calculator = AlleleFrequencyCalculator(
        use_read_counts=use_read_counts,
        min_samples=min_samples,
    )
    return calculator.calculate(variants, populations)


def get_founder_frequencies(
    variants: Iterable[Variant],
    populations: list[Population],
    **kwargs,
) -> AlleleFrequencies:
    """Calculate allele frequencies for founder populations only.

    Parameters
    ----------
    variants : Iterable[Variant]
        Variants to process.
    populations : list[Population]
        All populations (will filter to founders).
    **kwargs
        Additional arguments passed to calculate_population_frequencies.

    Returns
    -------
    AlleleFrequencies
        Frequencies for founder populations.
    """
    founders = [p for p in populations if p.role == PopulationRole.FOUNDER]
    return calculate_population_frequencies(variants, founders, **kwargs)
