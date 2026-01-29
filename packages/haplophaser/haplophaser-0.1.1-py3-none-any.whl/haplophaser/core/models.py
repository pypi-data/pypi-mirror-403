"""
Core data models for Haplophaser.

All genomic coordinates use 0-based, half-open intervals (BED-style) internally.
Conversion to/from 1-based systems (VCF, GFF) happens at I/O boundaries.

Polyploidy is a first-class concept: samples have explicit ploidy and subgenome
assignments, and genotype calls naturally accommodate multiple alleles per locus.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class PopulationRole(str, Enum):
    """Role of a population in haplotype analysis.

    Attributes
    ----------
    FOUNDER
        Source/reference population from which haplotypes are inherited.
    DERIVED
        Population derived from founders, target of haplotype estimation.
    OUTGROUP
        Outgroup population for rooting or contrast.
    """

    FOUNDER = "founder"
    DERIVED = "derived"
    OUTGROUP = "outgroup"


class Subgenome(BaseModel):
    """Represents a subgenome in polyploid species.

    In allopolyploids (e.g., wheat AABBDD), each subgenome represents
    chromosomes from a distinct ancestral diploid. In autopolyploids,
    subgenomes may be used to track homologous chromosome sets.

    Parameters
    ----------
    name : str
        Subgenome identifier (e.g., "A", "B", "D" for wheat).
    ploidy : int
        Number of chromosome copies in this subgenome (usually 2).
    description : str, optional
        Optional description of subgenome origin.

    Examples
    --------
    >>> subgenome_a = Subgenome(name="A", ploidy=2, description="From T. urartu")
    >>> subgenome_b = Subgenome(name="B", ploidy=2, description="From Ae. speltoides")
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, description="Subgenome identifier")
    ploidy: int = Field(default=2, ge=1, le=8, description="Ploidy of this subgenome")
    description: str | None = Field(default=None, description="Subgenome origin/description")


class Sample(BaseModel):
    """A biological sample with explicit ploidy and subgenome structure.

    Designed to represent samples from diploids through high polyploids.
    For diploids, subgenomes can be omitted. For allopolyploids, subgenomes
    define the distinct ancestral chromosome sets.

    Parameters
    ----------
    name : str
        Unique sample identifier, should match VCF sample column.
    ploidy : int
        Total ploidy (2 for diploid, 4 for tetraploid, 6 for hexaploid, etc.).
    subgenomes : list[Subgenome], optional
        Subgenome definitions for allopolyploids. If omitted for ploidy > 2,
        assumes autopolyploid with undifferentiated homologs.
    population : str, optional
        Population this sample belongs to.
    metadata : dict, optional
        Additional sample metadata.

    Examples
    --------
    >>> # Diploid maize inbred
    >>> b73 = Sample(name="B73", ploidy=2, population="NAM_founders")

    >>> # Tetraploid wheat (AABB)
    >>> wheat = Sample(
    ...     name="Chinese_Spring",
    ...     ploidy=4,
    ...     subgenomes=[
    ...         Subgenome(name="A", ploidy=2),
    ...         Subgenome(name="B", ploidy=2),
    ...     ],
    ... )
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, description="Sample identifier")
    ploidy: int = Field(default=2, ge=1, le=16, description="Total ploidy level")
    subgenomes: list[Subgenome] = Field(
        default_factory=list, description="Subgenome definitions for allopolyploids"
    )
    population: str | None = Field(default=None, description="Population assignment")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @model_validator(mode="after")
    def validate_subgenome_ploidy(self) -> Sample:
        """Ensure subgenome ploidies sum to total ploidy if specified."""
        if self.subgenomes:
            subgenome_sum = sum(sg.ploidy for sg in self.subgenomes)
            if subgenome_sum != self.ploidy:
                raise ValueError(
                    f"Subgenome ploidies ({subgenome_sum}) must sum to total ploidy ({self.ploidy})"
                )
        return self

    @property
    def is_polyploid(self) -> bool:
        """Return True if sample ploidy > 2."""
        return self.ploidy > 2

    @property
    def is_allopolyploid(self) -> bool:
        """Return True if sample has defined subgenomes."""
        return len(self.subgenomes) > 0

    @property
    def n_haplotypes(self) -> int:
        """Number of haplotype calls expected per locus."""
        return self.ploidy


class Population(BaseModel):
    """A collection of samples with a defined role in analysis.

    Populations serve as either founders (source haplotypes) or derived
    (targets for haplotype proportion estimation).

    Parameters
    ----------
    name : str
        Population identifier.
    samples : list[Sample]
        Member samples.
    role : PopulationRole
        Role in haplotype analysis (founder, derived, outgroup).
    description : str, optional
        Population description.

    Examples
    --------
    >>> founders = Population(
    ...     name="NAM_founders",
    ...     samples=[Sample(name="B73"), Sample(name="Mo17")],
    ...     role=PopulationRole.FOUNDER,
    ... )
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, description="Population identifier")
    samples: list[Sample] = Field(default_factory=list, description="Population members")
    role: PopulationRole = Field(..., description="Role in analysis")
    description: str | None = Field(default=None, description="Population description")

    @property
    def sample_names(self) -> list[str]:
        """Return list of sample names in this population."""
        return [s.name for s in self.samples]

    def get_sample(self, name: str) -> Sample | None:
        """Retrieve a sample by name.

        Parameters
        ----------
        name : str
            Sample name to look up.

        Returns
        -------
        Sample or None
            The sample if found, None otherwise.
        """
        for sample in self.samples:
            if sample.name == name:
                return sample
        return None


class Variant(BaseModel):
    """A genomic variant with polyploid-aware genotype representation.

    Coordinates are 0-based, half-open (BED-style). The position refers to
    the first base of the reference allele.

    Genotypes are stored as a dict mapping sample names to allele indices.
    For polyploids, each sample has `ploidy` allele calls.

    Parameters
    ----------
    chrom : str
        Chromosome/contig name.
    pos : int
        0-based position of variant.
    ref : str
        Reference allele.
    alt : list[str]
        Alternate alleles.
    genotypes : dict[str, list[int]]
        Mapping of sample name to allele indices. Index 0 = ref,
        1 = first alt, etc. -1 indicates missing. Length of each
        list equals sample ploidy.
    quality : float, optional
        Variant quality score.
    filter_status : str, optional
        Filter status (PASS or filter name).
    info : dict, optional
        Additional variant annotations.

    Examples
    --------
    >>> # Diploid heterozygote
    >>> var = Variant(
    ...     chrom="chr1",
    ...     pos=1000,
    ...     ref="A",
    ...     alt=["T"],
    ...     genotypes={"B73": [0, 0], "Mo17": [0, 1]},
    ... )

    >>> # Tetraploid with three ref, one alt
    >>> var_tetra = Variant(
    ...     chrom="chr1",
    ...     pos=1000,
    ...     ref="A",
    ...     alt=["T"],
    ...     genotypes={"wheat_sample": [0, 0, 0, 1]},
    ... )
    """

    model_config = ConfigDict(frozen=True)

    chrom: str = Field(..., min_length=1, description="Chromosome/contig")
    pos: int = Field(..., ge=0, description="0-based position")
    ref: str = Field(..., min_length=1, description="Reference allele")
    alt: list[str] = Field(default_factory=list, description="Alternate alleles")
    genotypes: dict[str, list[int]] = Field(
        default_factory=dict, description="Sample genotypes as allele indices"
    )
    quality: float | None = Field(default=None, ge=0, description="Variant quality")
    filter_status: str = Field(default=".", description="Filter status")
    info: dict[str, Any] = Field(default_factory=dict, description="INFO field annotations")

    @field_validator("genotypes")
    @classmethod
    def validate_genotypes(cls, v: dict[str, list[int]]) -> dict[str, list[int]]:
        """Validate that genotype allele indices are sensible."""
        for sample, alleles in v.items():
            if not alleles:
                raise ValueError(f"Sample {sample} has empty genotype")
            for allele in alleles:
                if allele < -1:
                    raise ValueError(f"Invalid allele index {allele} for sample {sample}")
        return v

    @property
    def pos_1based(self) -> int:
        """Return 1-based position (VCF-style)."""
        return self.pos + 1

    @property
    def end(self) -> int:
        """Return 0-based end position (exclusive)."""
        return self.pos + len(self.ref)

    @property
    def n_alleles(self) -> int:
        """Total number of alleles (ref + alts)."""
        return 1 + len(self.alt)

    @property
    def is_snp(self) -> bool:
        """Return True if variant is a SNP."""
        if len(self.ref) != 1:
            return False
        return all(len(a) == 1 for a in self.alt)

    def get_genotype(self, sample: str) -> list[int] | None:
        """Get genotype for a specific sample.

        Parameters
        ----------
        sample : str
            Sample name.

        Returns
        -------
        list[int] or None
            Allele indices if sample present, None otherwise.
        """
        return self.genotypes.get(sample)

    def allele_counts(self, sample: str) -> dict[int, int]:
        """Count occurrences of each allele for a sample.

        Parameters
        ----------
        sample : str
            Sample name.

        Returns
        -------
        dict[int, int]
            Mapping of allele index to count.

        Examples
        --------
        >>> var.allele_counts("wheat_sample")
        {0: 3, 1: 1}  # Three ref, one alt in tetraploid
        """
        gt = self.genotypes.get(sample, [])
        counts: dict[int, int] = {}
        for allele in gt:
            if allele >= 0:  # Skip missing
                counts[allele] = counts.get(allele, 0) + 1
        return counts


class Window(BaseModel):
    """A genomic window containing variants for analysis.

    Windows are the fundamental unit for haplotype block estimation.
    Coordinates are 0-based, half-open.

    Parameters
    ----------
    chrom : str
        Chromosome/contig name.
    start : int
        0-based start position (inclusive).
    end : int
        0-based end position (exclusive).
    variants : list[Variant]
        Variants within this window.
    index : int, optional
        Window index along chromosome.

    Examples
    --------
    >>> window = Window(chrom="chr1", start=0, end=100000)
    >>> len(window)
    100000
    """

    model_config = ConfigDict(frozen=True)

    chrom: str = Field(..., min_length=1, description="Chromosome/contig")
    start: int = Field(..., ge=0, description="0-based start (inclusive)")
    end: int = Field(..., ge=0, description="0-based end (exclusive)")
    variants: list[Variant] = Field(default_factory=list, description="Variants in window")
    index: int | None = Field(default=None, ge=0, description="Window index")

    @model_validator(mode="after")
    def validate_coordinates(self) -> Window:
        """Ensure end > start."""
        if self.end <= self.start:
            raise ValueError(f"Window end ({self.end}) must be > start ({self.start})")
        return self

    def __len__(self) -> int:
        """Return window length in base pairs."""
        return self.end - self.start

    @property
    def midpoint(self) -> int:
        """Return window midpoint position."""
        return (self.start + self.end) // 2

    @property
    def n_variants(self) -> int:
        """Number of variants in window."""
        return len(self.variants)

    def overlaps(self, other: Window) -> bool:
        """Check if this window overlaps another.

        Parameters
        ----------
        other : Window
            Window to compare against.

        Returns
        -------
        bool
            True if windows overlap.
        """
        if self.chrom != other.chrom:
            return False
        return self.start < other.end and other.start < self.end


class HaplotypeBlock(BaseModel):
    """A contiguous region with assigned haplotype origin.

    Represents the output of haplotype painting: a genomic segment in a
    sample assigned to a specific founder haplotype. For polyploids,
    each subgenome/homolog has its own haplotype block assignments.

    Parameters
    ----------
    chrom : str
        Chromosome/contig name.
    start : int
        0-based start position (inclusive).
    end : int
        0-based end position (exclusive).
    sample : str
        Sample this block belongs to.
    subgenome : str, optional
        Subgenome assignment for allopolyploids.
    homolog : int, optional
        Homolog index (0-based) within ploidy level.
    founder : str
        Founder population/sample this haplotype derives from.
    proportion : float
        Confidence/proportion of this assignment (0-1).
    n_variants : int
        Number of informative variants in this block.
    log_likelihood : float, optional
        Log-likelihood of this assignment.
    metadata : dict, optional
        Additional block annotations.

    Examples
    --------
    >>> block = HaplotypeBlock(
    ...     chrom="chr1",
    ...     start=0,
    ...     end=1000000,
    ...     sample="RIL_001",
    ...     homolog=0,
    ...     founder="B73",
    ...     proportion=0.95,
    ...     n_variants=150,
    ... )
    """

    model_config = ConfigDict(frozen=True)

    chrom: str = Field(..., min_length=1, description="Chromosome/contig")
    start: int = Field(..., ge=0, description="0-based start (inclusive)")
    end: int = Field(..., ge=0, description="0-based end (exclusive)")
    sample: str = Field(..., min_length=1, description="Sample name")
    subgenome: str | None = Field(default=None, description="Subgenome for allopolyploids")
    homolog: int = Field(default=0, ge=0, description="Homolog index (0-based)")
    founder: str = Field(..., min_length=1, description="Founder origin")
    proportion: float = Field(..., ge=0, le=1, description="Assignment confidence")
    n_variants: int = Field(default=0, ge=0, description="Informative variants")
    log_likelihood: float | None = Field(default=None, description="Log-likelihood")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional annotations")

    @model_validator(mode="after")
    def validate_coordinates(self) -> HaplotypeBlock:
        """Ensure end > start."""
        if self.end <= self.start:
            raise ValueError(f"Block end ({self.end}) must be > start ({self.start})")
        return self

    def __len__(self) -> int:
        """Return block length in base pairs."""
        return self.end - self.start

    @property
    def midpoint(self) -> int:
        """Return block midpoint position."""
        return (self.start + self.end) // 2

    def overlaps(self, other: HaplotypeBlock) -> bool:
        """Check if this block overlaps another.

        Parameters
        ----------
        other : HaplotypeBlock
            Block to compare against.

        Returns
        -------
        bool
            True if blocks overlap on same chromosome.
        """
        if self.chrom != other.chrom:
            return False
        return self.start < other.end and other.start < self.end

    def to_bed_fields(self) -> tuple[str, int, int, str, int, str]:
        """Convert to BED6 format fields.

        Returns
        -------
        tuple
            (chrom, start, end, name, score, strand)
        """
        name = f"{self.sample}|{self.founder}|h{self.homolog}"
        score = int(self.proportion * 1000)
        strand = "."
        return (self.chrom, self.start, self.end, name, score, strand)


def make_diploid_sample(name: str, population: str | None = None) -> Sample:
    """Convenience function to create a diploid sample.

    Parameters
    ----------
    name : str
        Sample name.
    population : str, optional
        Population assignment.

    Returns
    -------
    Sample
        Diploid sample instance.
    """
    return Sample(name=name, ploidy=2, population=population)


def make_tetraploid_sample(
    name: str,
    subgenome_names: tuple[str, str] = ("A", "B"),
    population: str | None = None,
) -> Sample:
    """Convenience function to create an allotetraploid sample.

    Parameters
    ----------
    name : str
        Sample name.
    subgenome_names : tuple[str, str]
        Names for the two subgenomes.
    population : str, optional
        Population assignment.

    Returns
    -------
    Sample
        Tetraploid sample with two diploid subgenomes.
    """
    subgenomes = [
        Subgenome(name=subgenome_names[0], ploidy=2),
        Subgenome(name=subgenome_names[1], ploidy=2),
    ]
    return Sample(name=name, ploidy=4, subgenomes=subgenomes, population=population)


def make_hexaploid_sample(
    name: str,
    subgenome_names: tuple[str, str, str] = ("A", "B", "D"),
    population: str | None = None,
) -> Sample:
    """Convenience function to create an allohexaploid sample (e.g., wheat).

    Parameters
    ----------
    name : str
        Sample name.
    subgenome_names : tuple[str, str, str]
        Names for the three subgenomes.
    population : str, optional
        Population assignment.

    Returns
    -------
    Sample
        Hexaploid sample with three diploid subgenomes.
    """
    subgenomes = [
        Subgenome(name=subgenome_names[0], ploidy=2),
        Subgenome(name=subgenome_names[1], ploidy=2),
        Subgenome(name=subgenome_names[2], ploidy=2),
    ]
    return Sample(name=name, ploidy=6, subgenomes=subgenomes, population=population)
