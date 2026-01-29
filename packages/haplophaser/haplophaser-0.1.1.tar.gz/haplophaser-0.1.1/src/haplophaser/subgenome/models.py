"""
Core data models for subgenome deconvolution.

Provides data structures for representing subgenomes, assignments,
markers, synteny blocks, and homeologs in paleopolyploid genomes.

All coordinates use 0-based, half-open intervals (BED-style) internally.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class EvidenceSource(str, Enum):
    """Source of evidence for subgenome assignment."""

    SYNTENY = "synteny"
    MARKERS = "markers"
    ORTHOLOGS = "orthologs"
    COMBINED = "combined"


@dataclass
class Subgenome:
    """Represents a subgenome in a paleopolyploid.

    Parameters
    ----------
    name : str
        Subgenome identifier (e.g., "maize1", "SG1", "A").
    description : str, optional
        Description of subgenome (e.g., "dominant subgenome").
    color : str, optional
        Color for visualization (hex or named color).

    Examples
    --------
    >>> sg1 = Subgenome("maize1", "Dominant subgenome", "#e41a1c")
    >>> sg2 = Subgenome("maize2", "Recessive subgenome", "#377eb8")
    """

    name: str
    description: str | None = None
    color: str | None = None

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Subgenome):
            return self.name == other.name
        return False


@dataclass
class SubgenomeConfig:
    """Configuration for subgenome analysis.

    Parameters
    ----------
    subgenomes : list[Subgenome]
        List of subgenomes to identify.
    reference_species : str, optional
        Reference species with known subgenome assignments (e.g., "Zm-B73-v5").
    outgroup_species : list[str], optional
        Outgroup species for phylogenetic rooting (e.g., ["Sorghum_bicolor"]).
    """

    subgenomes: list[Subgenome]
    reference_species: str | None = None
    outgroup_species: list[str] | None = None

    @property
    def subgenome_names(self) -> list[str]:
        """Return list of subgenome names."""
        return [sg.name for sg in self.subgenomes]

    @property
    def n_subgenomes(self) -> int:
        """Return number of subgenomes."""
        return len(self.subgenomes)

    def get_subgenome(self, name: str) -> Subgenome | None:
        """Get subgenome by name.

        Parameters
        ----------
        name : str
            Subgenome name to look up.

        Returns
        -------
        Subgenome or None
            The subgenome if found.
        """
        for sg in self.subgenomes:
            if sg.name == name:
                return sg
        return None

    @classmethod
    def maize_default(cls) -> SubgenomeConfig:
        """Create default configuration for maize.

        Maize is an ancient tetraploid (~5-12 MYA WGD) with two subgenomes.
        maize1 (SG1) is the dominant subgenome with higher gene retention.

        Returns
        -------
        SubgenomeConfig
            Configuration for maize subgenome analysis.
        """
        return cls(
            subgenomes=[
                Subgenome("maize1", "Dominant subgenome", "#e41a1c"),
                Subgenome("maize2", "Recessive subgenome", "#377eb8"),
            ],
            reference_species="Zm-B73-v5",
            outgroup_species=["Sorghum_bicolor"],
        )

    @classmethod
    def wheat_default(cls) -> SubgenomeConfig:
        """Create default configuration for wheat (hexaploid).

        Wheat has three subgenomes from distinct diploid ancestors.

        Returns
        -------
        SubgenomeConfig
            Configuration for wheat subgenome analysis.
        """
        return cls(
            subgenomes=[
                Subgenome("A", "A genome from T. urartu", "#e41a1c"),
                Subgenome("B", "B genome from Ae. speltoides-like", "#377eb8"),
                Subgenome("D", "D genome from Ae. tauschii", "#4daf4a"),
            ],
            reference_species="Chinese_Spring",
            outgroup_species=["Brachypodium_distachyon"],
        )

    @classmethod
    def brassica_default(cls) -> SubgenomeConfig:
        """Create default configuration for Brassica napus (tetraploid).

        B. napus is derived from B. rapa (A) and B. oleracea (C).

        Returns
        -------
        SubgenomeConfig
            Configuration for Brassica subgenome analysis.
        """
        return cls(
            subgenomes=[
                Subgenome("A", "A genome from B. rapa", "#e41a1c"),
                Subgenome("C", "C genome from B. oleracea", "#377eb8"),
            ],
            reference_species="Darmor-bzh",
            outgroup_species=["Arabidopsis_thaliana"],
        )


@dataclass
class SubgenomeAssignment:
    """Subgenome assignment for a genomic region.

    Parameters
    ----------
    chrom : str
        Chromosome/contig name.
    start : int
        0-based start position (inclusive).
    end : int
        0-based end position (exclusive).
    subgenome : str
        Assigned subgenome name.
    confidence : float
        Confidence in assignment (0-1).
    evidence : str
        Evidence source: 'synteny', 'markers', 'orthologs', 'combined'.
    evidence_details : dict, optional
        Additional evidence information.

    Examples
    --------
    >>> assignment = SubgenomeAssignment(
    ...     chrom="chr1",
    ...     start=0,
    ...     end=1_000_000,
    ...     subgenome="maize1",
    ...     confidence=0.95,
    ...     evidence="synteny",
    ... )
    """

    chrom: str
    start: int
    end: int
    subgenome: str
    confidence: float
    evidence: str
    evidence_details: dict[str, Any] | None = None

    @property
    def length(self) -> int:
        """Return length of assigned region in bp."""
        return self.end - self.start

    @property
    def midpoint(self) -> int:
        """Return midpoint of the region."""
        return (self.start + self.end) // 2

    def overlaps(self, chrom: str, start: int, end: int) -> bool:
        """Check if this assignment overlaps a region.

        Parameters
        ----------
        chrom : str
            Chromosome to check.
        start : int
            Start position.
        end : int
            End position.

        Returns
        -------
        bool
            True if overlapping.
        """
        if self.chrom != chrom:
            return False
        return self.start < end and start < self.end

    def to_bed_fields(self) -> tuple[str, int, int, str, int, str]:
        """Convert to BED6 format fields.

        Returns
        -------
        tuple
            (chrom, start, end, name, score, strand)
        """
        name = f"{self.subgenome}|{self.evidence}"
        score = int(self.confidence * 1000)
        strand = "."
        return (self.chrom, self.start, self.end, name, score, strand)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "chrom": self.chrom,
            "start": self.start,
            "end": self.end,
            "subgenome": self.subgenome,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "evidence_details": self.evidence_details,
        }


@dataclass
class SubgenomeMarker:
    """A subgenome-diagnostic marker.

    Parameters
    ----------
    marker_id : str
        Unique marker identifier.
    chrom : str
        Chromosome/contig.
    pos : int
        0-based position.
    ref : str
        Reference allele.
    alt : str
        Alternate allele.
    subgenome_alleles : dict[str, str]
        Mapping of subgenome to expected allele.
    divergence : float
        Sequence divergence at this site.
    synteny_block : str, optional
        Which synteny block contains this marker.
    confidence : float
        Confidence in marker (0-1).

    Examples
    --------
    >>> marker = SubgenomeMarker(
    ...     marker_id="chr1_1000",
    ...     chrom="chr1",
    ...     pos=1000,
    ...     ref="A",
    ...     alt="G",
    ...     subgenome_alleles={"maize1": "A", "maize2": "G"},
    ...     divergence=0.05,
    ...     confidence=0.9,
    ... )
    """

    marker_id: str
    chrom: str
    pos: int
    ref: str
    alt: str
    subgenome_alleles: dict[str, str]
    divergence: float
    synteny_block: str | None = None
    confidence: float = 1.0

    @property
    def pos_1based(self) -> int:
        """Return 1-based position (VCF-style)."""
        return self.pos + 1

    def allele_for_subgenome(self, subgenome: str) -> str | None:
        """Get expected allele for a subgenome.

        Parameters
        ----------
        subgenome : str
            Subgenome name.

        Returns
        -------
        str or None
            Expected allele, or None if not defined.
        """
        return self.subgenome_alleles.get(subgenome)

    def subgenome_for_allele(self, allele: str) -> str | None:
        """Get subgenome for an observed allele.

        Parameters
        ----------
        allele : str
            Observed allele.

        Returns
        -------
        str or None
            Subgenome with this allele, or None if ambiguous.
        """
        matches = [sg for sg, a in self.subgenome_alleles.items() if a == allele]
        return matches[0] if len(matches) == 1 else None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "marker_id": self.marker_id,
            "chrom": self.chrom,
            "pos": self.pos,
            "ref": self.ref,
            "alt": self.alt,
            "subgenome_alleles": self.subgenome_alleles,
            "divergence": self.divergence,
            "synteny_block": self.synteny_block,
            "confidence": self.confidence,
        }


@dataclass
class SyntenyBlock:
    """A block of synteny between query and reference genomes.

    Parameters
    ----------
    query_chrom : str
        Query chromosome/contig.
    query_start : int
        0-based query start.
    query_end : int
        0-based query end.
    ref_chrom : str
        Reference chromosome.
    ref_start : int
        0-based reference start.
    ref_end : int
        0-based reference end.
    orientation : str
        Orientation: '+' (same) or '-' (inverted).
    n_anchors : int
        Number of anchor genes/markers.
    identity : float
        Sequence identity (0-1).
    block_id : str, optional
        Unique block identifier.

    Examples
    --------
    >>> block = SyntenyBlock(
    ...     query_chrom="chr1",
    ...     query_start=0,
    ...     query_end=1_000_000,
    ...     ref_chrom="chr1",
    ...     ref_start=500_000,
    ...     ref_end=1_500_000,
    ...     orientation="+",
    ...     n_anchors=50,
    ...     identity=0.95,
    ... )
    """

    query_chrom: str
    query_start: int
    query_end: int
    ref_chrom: str
    ref_start: int
    ref_end: int
    orientation: str
    n_anchors: int
    identity: float
    block_id: str | None = None

    @property
    def query_length(self) -> int:
        """Return query region length in bp."""
        return self.query_end - self.query_start

    @property
    def ref_length(self) -> int:
        """Return reference region length in bp."""
        return self.ref_end - self.ref_start

    @property
    def is_inverted(self) -> bool:
        """Return True if block is inverted."""
        return self.orientation == "-"

    def query_overlaps(self, chrom: str, start: int, end: int) -> bool:
        """Check if query region overlaps a given region.

        Parameters
        ----------
        chrom : str
            Chromosome to check.
        start : int
            Start position.
        end : int
            End position.

        Returns
        -------
        bool
            True if overlapping.
        """
        if self.query_chrom != chrom:
            return False
        return self.query_start < end and start < self.query_end

    def ref_overlaps(self, chrom: str, start: int, end: int) -> bool:
        """Check if reference region overlaps a given region.

        Parameters
        ----------
        chrom : str
            Chromosome to check.
        start : int
            Start position.
        end : int
            End position.

        Returns
        -------
        bool
            True if overlapping.
        """
        if self.ref_chrom != chrom:
            return False
        return self.ref_start < end and start < self.ref_end

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "block_id": self.block_id,
            "query_chrom": self.query_chrom,
            "query_start": self.query_start,
            "query_end": self.query_end,
            "ref_chrom": self.ref_chrom,
            "ref_start": self.ref_start,
            "ref_end": self.ref_end,
            "orientation": self.orientation,
            "n_anchors": self.n_anchors,
            "identity": self.identity,
        }


@dataclass
class GeneSubgenomeCall:
    """Subgenome assignment for a single gene.

    Parameters
    ----------
    gene_id : str
        Gene identifier.
    chrom : str
        Chromosome/contig.
    start : int
        0-based start.
    end : int
        0-based end.
    orthogroup : str
        OrthoFinder orthogroup ID.
    subgenome : str, optional
        Assigned subgenome.
    confidence : float
        Confidence in assignment.
    tree_support : float, optional
        Bootstrap or posterior support from gene tree.
    outgroup_distance : float, optional
        Phylogenetic distance to outgroup.

    Examples
    --------
    >>> call = GeneSubgenomeCall(
    ...     gene_id="Zm00001d001234",
    ...     chrom="chr1",
    ...     start=100_000,
    ...     end=105_000,
    ...     orthogroup="OG0000001",
    ...     subgenome="maize1",
    ...     confidence=0.85,
    ...     tree_support=95.0,
    ... )
    """

    gene_id: str
    chrom: str
    start: int
    end: int
    orthogroup: str
    subgenome: str | None = None
    confidence: float = 0.0
    tree_support: float | None = None
    outgroup_distance: float | None = None

    @property
    def is_assigned(self) -> bool:
        """Return True if gene is assigned to a subgenome."""
        return self.subgenome is not None

    @property
    def length(self) -> int:
        """Return gene length in bp."""
        return self.end - self.start

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "gene_id": self.gene_id,
            "chrom": self.chrom,
            "start": self.start,
            "end": self.end,
            "orthogroup": self.orthogroup,
            "subgenome": self.subgenome,
            "confidence": self.confidence,
            "tree_support": self.tree_support,
            "outgroup_distance": self.outgroup_distance,
        }


@dataclass
class HomeologPair:
    """A pair of homeologous genes from the WGD.

    Parameters
    ----------
    gene1_id : str
        First gene identifier.
    gene1_chrom : str
        First gene chromosome.
    gene1_subgenome : str
        First gene subgenome.
    gene2_id : str
        Second gene identifier.
    gene2_chrom : str
        Second gene chromosome.
    gene2_subgenome : str
        Second gene subgenome.
    ks : float, optional
        Synonymous substitution rate.
    ka : float, optional
        Non-synonymous substitution rate.
    synteny_support : bool
        Whether pair is supported by synteny.
    sequence_identity : float
        Protein sequence identity.
    confidence : float
        Confidence in homeolog relationship.

    Examples
    --------
    >>> pair = HomeologPair(
    ...     gene1_id="Zm00001d001234",
    ...     gene1_chrom="chr1",
    ...     gene1_subgenome="maize1",
    ...     gene2_id="Zm00001d054321",
    ...     gene2_chrom="chr5",
    ...     gene2_subgenome="maize2",
    ...     ks=0.15,
    ...     synteny_support=True,
    ...     sequence_identity=0.85,
    ...     confidence=0.95,
    ... )
    """

    gene1_id: str
    gene1_chrom: str
    gene1_subgenome: str
    gene2_id: str
    gene2_chrom: str
    gene2_subgenome: str
    ks: float | None = None
    ka: float | None = None
    synteny_support: bool = False
    sequence_identity: float = 0.0
    confidence: float = 0.0

    @property
    def ka_ks_ratio(self) -> float | None:
        """Return Ka/Ks ratio if both values available."""
        if self.ka is not None and self.ks is not None and self.ks > 0:
            return self.ka / self.ks
        return None

    @property
    def is_purifying(self) -> bool | None:
        """Return True if Ka/Ks < 1 (purifying selection)."""
        ratio = self.ka_ks_ratio
        return ratio < 1.0 if ratio is not None else None

    def genes(self) -> tuple[str, str]:
        """Return both gene IDs as a tuple."""
        return (self.gene1_id, self.gene2_id)

    def involves_gene(self, gene_id: str) -> bool:
        """Check if pair involves a specific gene.

        Parameters
        ----------
        gene_id : str
            Gene ID to check.

        Returns
        -------
        bool
            True if gene is in this pair.
        """
        return gene_id in (self.gene1_id, self.gene2_id)

    def partner(self, gene_id: str) -> str | None:
        """Get the partner gene for a given gene.

        Parameters
        ----------
        gene_id : str
            Gene ID to find partner for.

        Returns
        -------
        str or None
            Partner gene ID, or None if gene not in pair.
        """
        if gene_id == self.gene1_id:
            return self.gene2_id
        elif gene_id == self.gene2_id:
            return self.gene1_id
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "gene1_id": self.gene1_id,
            "gene1_chrom": self.gene1_chrom,
            "gene1_subgenome": self.gene1_subgenome,
            "gene2_id": self.gene2_id,
            "gene2_chrom": self.gene2_chrom,
            "gene2_subgenome": self.gene2_subgenome,
            "ks": self.ks,
            "ka": self.ka,
            "synteny_support": self.synteny_support,
            "sequence_identity": self.sequence_identity,
            "confidence": self.confidence,
        }


@dataclass
class HomeologResult:
    """Results of homeolog detection.

    Parameters
    ----------
    pairs : list[HomeologPair]
        Detected homeolog pairs.
    config : SubgenomeConfig
        Configuration used.
    parameters : dict
        Parameters used for detection.

    Examples
    --------
    >>> result = HomeologResult(pairs=pairs, config=config, parameters={})
    >>> print(f"Found {result.n_pairs} homeolog pairs")
    >>> print(f"Median Ks: {result.median_ks:.3f}")
    """

    pairs: list[HomeologPair]
    config: SubgenomeConfig | None = None
    parameters: dict[str, Any] = field(default_factory=dict)

    @property
    def n_pairs(self) -> int:
        """Return number of homeolog pairs."""
        return len(self.pairs)

    @property
    def median_ks(self) -> float:
        """Return median Ks value."""
        import numpy as np

        ks_values = [p.ks for p in self.pairs if p.ks is not None]
        return float(np.median(ks_values)) if ks_values else 0.0

    @property
    def mean_identity(self) -> float:
        """Return mean sequence identity."""
        import numpy as np

        identities = [p.sequence_identity for p in self.pairs]
        return float(np.mean(identities)) if identities else 0.0

    def n_singletons(self, subgenome: str) -> int:
        """Count genes without homeolog partner in a subgenome.

        Note: This requires external gene list to compute accurately.
        Returns count of pairs where one gene is in the specified subgenome.

        Parameters
        ----------
        subgenome : str
            Subgenome name.

        Returns
        -------
        int
            Number of genes from this subgenome that have homeologs.
        """
        count = 0
        for pair in self.pairs:
            if pair.gene1_subgenome == subgenome or pair.gene2_subgenome == subgenome:
                count += 1
        return count

    def singletons(self, subgenome: str, all_genes: set[str] | None = None) -> list[str]:
        """Get genes without homeolog partner.

        Parameters
        ----------
        subgenome : str
            Subgenome to check.
        all_genes : set[str], optional
            All genes in the subgenome. If not provided, returns empty list.

        Returns
        -------
        list[str]
            Gene IDs without homeolog partner.
        """
        if all_genes is None:
            return []

        paired_genes = set()
        for pair in self.pairs:
            if pair.gene1_subgenome == subgenome:
                paired_genes.add(pair.gene1_id)
            if pair.gene2_subgenome == subgenome:
                paired_genes.add(pair.gene2_id)

        return sorted(all_genes - paired_genes)

    def pairs_by_subgenome_combination(
        self, sg1: str, sg2: str
    ) -> list[HomeologPair]:
        """Get pairs between two specific subgenomes.

        Parameters
        ----------
        sg1 : str
            First subgenome.
        sg2 : str
            Second subgenome.

        Returns
        -------
        list[HomeologPair]
            Pairs between these subgenomes.
        """
        result = []
        for pair in self.pairs:
            sgs = {pair.gene1_subgenome, pair.gene2_subgenome}
            if sgs == {sg1, sg2}:
                result.append(pair)
        return result

    def to_dataframe(self):
        """Convert to pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            Homeolog pairs as DataFrame.
        """
        import pandas as pd

        if not self.pairs:
            return pd.DataFrame()

        rows = [p.to_dict() for p in self.pairs]
        df = pd.DataFrame(rows)

        # Add Ka/Ks ratio column
        if "ks" in df.columns and "ka" in df.columns:
            df["ka_ks_ratio"] = df.apply(
                lambda r: r["ka"] / r["ks"] if r["ks"] and r["ks"] > 0 else None,
                axis=1,
            )

        return df


@dataclass
class SubgenomeAssignmentResult:
    """Complete result of subgenome assignment for a genome.

    Parameters
    ----------
    query_name : str
        Name of the query assembly/sample.
    config : SubgenomeConfig
        Configuration used.
    assignments : list[SubgenomeAssignment]
        Regional assignments.
    method : str
        Method used for assignment.
    parameters : dict
        Parameters used.
    """

    query_name: str
    config: SubgenomeConfig
    assignments: list[SubgenomeAssignment] = field(default_factory=list)
    method: str = "synteny"
    parameters: dict[str, Any] = field(default_factory=dict)

    @property
    def n_assignments(self) -> int:
        """Return number of assigned regions."""
        return len(self.assignments)

    @property
    def total_assigned_bp(self) -> int:
        """Return total assigned bases."""
        return sum(a.length for a in self.assignments)

    def assignments_by_subgenome(self, subgenome: str) -> list[SubgenomeAssignment]:
        """Get assignments for a specific subgenome.

        Parameters
        ----------
        subgenome : str
            Subgenome name.

        Returns
        -------
        list[SubgenomeAssignment]
            Assignments for this subgenome.
        """
        return [a for a in self.assignments if a.subgenome == subgenome]

    def assignments_for_region(
        self, chrom: str, start: int, end: int
    ) -> list[SubgenomeAssignment]:
        """Get assignments overlapping a region.

        Parameters
        ----------
        chrom : str
            Chromosome name.
        start : int
            Start position.
        end : int
            End position.

        Returns
        -------
        list[SubgenomeAssignment]
            Overlapping assignments.
        """
        return [a for a in self.assignments if a.overlaps(chrom, start, end)]

    def summary(self) -> dict[str, Any]:
        """Generate summary statistics.

        Returns
        -------
        dict
            Summary statistics.
        """
        by_subgenome: dict[str, dict] = {}
        for sg in self.config.subgenome_names:
            sg_assignments = self.assignments_by_subgenome(sg)
            by_subgenome[sg] = {
                "n_regions": len(sg_assignments),
                "total_bp": sum(a.length for a in sg_assignments),
                "mean_confidence": (
                    sum(a.confidence for a in sg_assignments) / len(sg_assignments)
                    if sg_assignments
                    else 0.0
                ),
            }

        by_evidence: dict[str, int] = {}
        for a in self.assignments:
            by_evidence[a.evidence] = by_evidence.get(a.evidence, 0) + 1

        return {
            "query_name": self.query_name,
            "method": self.method,
            "n_regions": self.n_assignments,
            "total_bp": self.total_assigned_bp,
            "by_subgenome": by_subgenome,
            "by_evidence": by_evidence,
        }

    def to_dataframe(self):
        """Convert to pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            Assignments as DataFrame.
        """
        import pandas as pd

        if not self.assignments:
            return pd.DataFrame()

        rows = [a.to_dict() for a in self.assignments]
        return pd.DataFrame(rows)

    def to_bed(self, output: Path | str) -> None:
        """Export assignments as BED file.

        Parameters
        ----------
        output : Path or str
            Output file path.
        """
        output = Path(output)
        with open(output, "w") as f:
            for a in sorted(self.assignments, key=lambda x: (x.chrom, x.start)):
                fields = a.to_bed_fields()
                f.write("\t".join(str(x) for x in fields) + "\n")
