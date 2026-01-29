"""
OrthoFinder output parsing for subgenome assignment.

Parses OrthoFinder results to support phylogenetic placement of genes
for subgenome assignment in allopolyploid assemblies.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Orthogroup:
    """An orthogroup from OrthoFinder results.

    Parameters
    ----------
    id : str
        Orthogroup identifier (e.g., 'OG0000001').
    genes : dict[str, list[str]]
        Mapping of species to gene IDs in this orthogroup.
    n_species : int
        Number of species with genes in this orthogroup.
    n_genes : int
        Total number of genes in orthogroup.
    is_single_copy : bool
        True if single-copy in all species.
    """

    id: str
    genes: dict[str, list[str]] = field(default_factory=dict)
    n_species: int = 0
    n_genes: int = 0
    is_single_copy: bool = False

    def genes_for_species(self, species: str) -> list[str]:
        """Get genes for a specific species.

        Parameters
        ----------
        species : str
            Species name.

        Returns
        -------
        list[str]
            Gene IDs for species.
        """
        return self.genes.get(species, [])

    def has_species(self, species: str) -> bool:
        """Check if species is in this orthogroup.

        Parameters
        ----------
        species : str
            Species name.

        Returns
        -------
        bool
            True if species has genes in orthogroup.
        """
        return species in self.genes and len(self.genes[species]) > 0

    @property
    def species(self) -> list[str]:
        """Return list of species in orthogroup."""
        return list(self.genes.keys())


@dataclass
class GeneTreeNode:
    """A node in a gene tree.

    Parameters
    ----------
    name : str | None
        Node name (for leaf nodes).
    species : str | None
        Species for this gene (for leaf nodes).
    children : list[GeneTreeNode]
        Child nodes.
    branch_length : float | None
        Branch length to parent.
    support : float | None
        Bootstrap/support value.
    """

    name: str | None = None
    species: str | None = None
    children: list[GeneTreeNode] = field(default_factory=list)
    branch_length: float | None = None
    support: float | None = None

    @property
    def is_leaf(self) -> bool:
        """Return True if this is a leaf node."""
        return len(self.children) == 0

    def get_leaves(self) -> list[GeneTreeNode]:
        """Get all leaf nodes in subtree.

        Returns
        -------
        list[GeneTreeNode]
            All leaf nodes.
        """
        if self.is_leaf:
            return [self]
        leaves = []
        for child in self.children:
            leaves.extend(child.get_leaves())
        return leaves


@dataclass
class PhylogeneticPlacement:
    """Result of phylogenetic placement for a gene.

    Parameters
    ----------
    gene_id : str
        Query gene ID.
    orthogroup : str
        Orthogroup containing this gene.
    closest_species : str | None
        Most closely related species in tree.
    subgenome : str | None
        Inferred subgenome based on placement.
    confidence : float
        Confidence in placement (0-1).
    support_values : dict[str, float]
        Support for each possible subgenome.
    """

    gene_id: str
    orthogroup: str
    closest_species: str | None = None
    subgenome: str | None = None
    confidence: float = 0.0
    support_values: dict[str, float] = field(default_factory=dict)


class OrthoFinderResults:
    """Parser for OrthoFinder output directory.

    Parameters
    ----------
    results_dir : Path
        Path to OrthoFinder Results directory.
    """

    def __init__(self, results_dir: Path | str) -> None:
        self.results_dir = Path(results_dir)
        self._orthogroups: dict[str, Orthogroup] | None = None
        self._single_copy_orthogroups: set[str] | None = None
        self._species: list[str] | None = None
        self._gene_to_orthogroup: dict[str, str] | None = None
        self._subgenome_representatives: dict[str, str] = {}

    @classmethod
    def from_directory(cls, path: Path | str) -> OrthoFinderResults:
        """Load OrthoFinder results from directory.

        Parameters
        ----------
        path : Path | str
            Path to Results directory (can include wildcards for Results_*).

        Returns
        -------
        OrthoFinderResults
            Loaded results.
        """
        path = Path(path)

        # Handle wildcard pattern
        if "*" in str(path):
            import glob
            matches = glob.glob(str(path))
            if not matches:
                raise FileNotFoundError(f"No OrthoFinder results found matching: {path}")
            path = Path(sorted(matches)[-1])  # Use most recent

        if not path.exists():
            raise FileNotFoundError(f"OrthoFinder results not found: {path}")

        logger.info(f"Loading OrthoFinder results from: {path}")
        return cls(path)

    @property
    def species(self) -> list[str]:
        """Return list of species in analysis."""
        if self._species is None:
            self._load_species()
        return self._species

    @property
    def orthogroups(self) -> dict[str, Orthogroup]:
        """Return all orthogroups."""
        if self._orthogroups is None:
            self._load_orthogroups()
        return self._orthogroups

    @property
    def single_copy_orthogroups(self) -> set[str]:
        """Return set of single-copy orthogroup IDs."""
        if self._single_copy_orthogroups is None:
            self._load_single_copy_orthogroups()
        return self._single_copy_orthogroups

    def _load_species(self) -> None:
        """Load species list from SpeciesIDs.txt."""
        species_file = self._find_file("SpeciesIDs.txt")
        if species_file is None:
            # Try to infer from orthogroups
            if self._orthogroups is None:
                self._load_orthogroups()
            if self._orthogroups:
                first_og = next(iter(self._orthogroups.values()))
                self._species = list(first_og.genes.keys())
            else:
                self._species = []
            return

        self._species = []
        with open(species_file) as f:
            for line in f:
                if not line.strip():
                    continue
                parts = line.strip().split(": ")
                if len(parts) >= 2:
                    species_name = parts[1].replace(".fa", "").replace(".fasta", "")
                    self._species.append(species_name)

        logger.info(f"Found {len(self._species)} species")

    def _load_orthogroups(self) -> None:
        """Load orthogroups from Orthogroups.tsv."""
        og_file = self._find_file("Orthogroups/Orthogroups.tsv")
        if og_file is None:
            og_file = self._find_file("Orthogroups.tsv")

        if og_file is None:
            logger.warning("Orthogroups.tsv not found")
            self._orthogroups = {}
            return

        logger.info(f"Loading orthogroups from {og_file}")

        self._orthogroups = {}
        self._gene_to_orthogroup = {}

        with open(og_file) as f:
            header = None
            for line in f:
                line = line.strip()
                if not line:
                    continue

                fields = line.split("\t")

                if header is None:
                    header = fields
                    # First column is Orthogroup, rest are species
                    self._species = [s.strip() for s in fields[1:] if s.strip()]
                    continue

                og_id = fields[0]
                genes: dict[str, list[str]] = {}
                n_genes = 0

                for i, species in enumerate(self._species):
                    col_idx = i + 1
                    if col_idx < len(fields) and fields[col_idx].strip():
                        gene_list = [
                            g.strip() for g in fields[col_idx].split(", ")
                            if g.strip()
                        ]
                        genes[species] = gene_list
                        n_genes += len(gene_list)

                        # Build reverse mapping
                        for gene in gene_list:
                            self._gene_to_orthogroup[gene] = og_id

                # Determine if single-copy
                is_single_copy = all(
                    len(genes.get(s, [])) == 1 for s in self._species
                )

                self._orthogroups[og_id] = Orthogroup(
                    id=og_id,
                    genes=genes,
                    n_species=len([s for s in self._species if s in genes]),
                    n_genes=n_genes,
                    is_single_copy=is_single_copy,
                )

        logger.info(f"Loaded {len(self._orthogroups)} orthogroups")

    def _load_single_copy_orthogroups(self) -> None:
        """Load single-copy orthogroup list."""
        sc_file = self._find_file("Orthogroups/Orthogroups_SingleCopyOrthologues.txt")
        if sc_file is None:
            sc_file = self._find_file("Orthogroups_SingleCopyOrthologues.txt")

        if sc_file is None:
            # Fall back to checking each orthogroup
            if self._orthogroups is None:
                self._load_orthogroups()
            self._single_copy_orthogroups = {
                og_id for og_id, og in self._orthogroups.items()
                if og.is_single_copy
            }
            return

        self._single_copy_orthogroups = set()
        with open(sc_file) as f:
            for line in f:
                og_id = line.strip()
                if og_id:
                    self._single_copy_orthogroups.add(og_id)

        logger.info(f"Found {len(self._single_copy_orthogroups)} single-copy orthogroups")

    def _find_file(self, relative_path: str) -> Path | None:
        """Find a file within the results directory.

        Parameters
        ----------
        relative_path : str
            Relative path to file.

        Returns
        -------
        Path | None
            Full path if found, None otherwise.
        """
        full_path = self.results_dir / relative_path
        if full_path.exists():
            return full_path

        # Try common subdirectories
        for subdir in ["", "Orthogroups", "Orthologues", "Gene_Trees"]:
            test_path = self.results_dir / subdir / Path(relative_path).name
            if test_path.exists():
                return test_path

        return None

    def get_orthogroup(self, og_id: str) -> Orthogroup | None:
        """Get an orthogroup by ID.

        Parameters
        ----------
        og_id : str
            Orthogroup identifier.

        Returns
        -------
        Orthogroup | None
            Orthogroup if found, None otherwise.
        """
        return self.orthogroups.get(og_id)

    def genes_by_species(self, species: str) -> list[str]:
        """Get all genes for a species.

        Parameters
        ----------
        species : str
            Species name.

        Returns
        -------
        list[str]
            Gene IDs for species.
        """
        genes = []
        for og in self.orthogroups.values():
            genes.extend(og.genes_for_species(species))
        return genes

    def get_gene_orthogroup(self, gene_id: str) -> str | None:
        """Get orthogroup containing a gene.

        Parameters
        ----------
        gene_id : str
            Gene identifier.

        Returns
        -------
        str | None
            Orthogroup ID if found.
        """
        if self._gene_to_orthogroup is None:
            self._load_orthogroups()
        return self._gene_to_orthogroup.get(gene_id)

    def set_subgenome_representatives(
        self,
        representatives: dict[str, str],
    ) -> None:
        """Set subgenome representative species.

        Parameters
        ----------
        representatives : dict[str, str]
            Mapping of subgenome name to representative species.
        """
        self._subgenome_representatives = representatives
        logger.info(f"Set subgenome representatives: {representatives}")

    def get_gene_placement(self, gene_id: str) -> str | None:
        """Get subgenome placement for a gene.

        Uses the closest species in the same orthogroup to infer subgenome.

        Parameters
        ----------
        gene_id : str
            Gene identifier.

        Returns
        -------
        str | None
            Inferred subgenome name.
        """
        if not self._subgenome_representatives:
            return None

        og_id = self.get_gene_orthogroup(gene_id)
        if og_id is None:
            return None

        og = self.get_orthogroup(og_id)
        if og is None:
            return None

        # Check which representative species are in this orthogroup
        for subgenome, species in self._subgenome_representatives.items():
            if og.has_species(species):
                return subgenome

        return None

    def phylogenetic_placement(
        self,
        query_genes: list[str],
        reference_species: list[str] | None = None,
        subgenome_representatives: dict[str, str] | None = None,
    ) -> dict[str, PhylogeneticPlacement]:
        """Perform phylogenetic placement for query genes.

        Parameters
        ----------
        query_genes : list[str]
            Gene IDs to place.
        reference_species : list[str] | None
            Outgroup/reference species for rooting.
        subgenome_representatives : dict[str, str] | None
            Subgenome to species mapping.

        Returns
        -------
        dict[str, PhylogeneticPlacement]
            Placement results per gene.
        """
        if subgenome_representatives:
            self._subgenome_representatives = subgenome_representatives

        placements: dict[str, PhylogeneticPlacement] = {}

        for gene_id in query_genes:
            og_id = self.get_gene_orthogroup(gene_id)
            if og_id is None:
                placements[gene_id] = PhylogeneticPlacement(
                    gene_id=gene_id,
                    orthogroup="",
                    confidence=0.0,
                )
                continue

            og = self.get_orthogroup(og_id)

            # Calculate support for each subgenome
            support: dict[str, float] = {}
            for sg, species in self._subgenome_representatives.items():
                if og and og.has_species(species):
                    # Simple support: 1 if present, 0 if not
                    support[sg] = 1.0
                else:
                    support[sg] = 0.0

            # Normalize support
            total_support = sum(support.values())
            if total_support > 0:
                support = {sg: s / total_support for sg, s in support.items()}

            # Find best subgenome
            if support:
                best_sg = max(support, key=support.get)
                best_support = support[best_sg]
            else:
                best_sg = None
                best_support = 0.0

            # Get closest species
            closest_species = None
            if best_sg:
                closest_species = self._subgenome_representatives.get(best_sg)

            placements[gene_id] = PhylogeneticPlacement(
                gene_id=gene_id,
                orthogroup=og_id,
                closest_species=closest_species,
                subgenome=best_sg if best_support > 0.5 else None,
                confidence=best_support,
                support_values=support,
            )

        logger.info(f"Placed {len(placements)} genes phylogenetically")
        return placements

    def iter_orthogroups(self) -> Iterator[Orthogroup]:
        """Iterate over all orthogroups.

        Yields
        ------
        Orthogroup
            Each orthogroup.
        """
        yield from self.orthogroups.values()

    def summary(self) -> dict:
        """Generate summary of OrthoFinder results.

        Returns
        -------
        dict
            Summary statistics.
        """
        n_orthogroups = len(self.orthogroups)
        n_single_copy = len(self.single_copy_orthogroups)
        total_genes = sum(og.n_genes for og in self.orthogroups.values())

        genes_per_species = {s: len(self.genes_by_species(s)) for s in self.species}

        return {
            "results_dir": str(self.results_dir),
            "n_species": len(self.species),
            "species": self.species,
            "n_orthogroups": n_orthogroups,
            "n_single_copy_orthogroups": n_single_copy,
            "total_genes": total_genes,
            "genes_per_species": genes_per_species,
        }


def load_gene_to_contig_mapping(path: Path | str) -> dict[str, str]:
    """Load gene to contig mapping from GFF or TSV file.

    Parameters
    ----------
    path : Path | str
        Path to mapping file.

    Returns
    -------
    dict[str, str]
        Mapping of gene ID to contig name.
    """
    path = Path(path)
    logger.info(f"Loading gene-to-contig mapping from {path}")

    mapping: dict[str, str] = {}

    suffix = path.suffix.lower()

    if suffix in (".gff", ".gff3"):
        # Parse GFF format
        with open(path) as f:
            for line in f:
                if line.startswith("#"):
                    continue
                fields = line.strip().split("\t")
                if len(fields) < 9:
                    continue
                if fields[2] != "gene":
                    continue

                contig = fields[0]
                attributes = fields[8]

                # Parse ID from attributes
                gene_id = None
                for attr in attributes.split(";"):
                    if attr.startswith("ID="):
                        gene_id = attr[3:]
                        break

                if gene_id:
                    mapping[gene_id] = contig

    else:
        # Parse TSV format (gene_id\tcontig)
        with open(path) as f:
            header = None
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                fields = line.split("\t")

                if header is None and ("gene" in line.lower() or "contig" in line.lower()):
                    header = True
                    continue

                if len(fields) >= 2:
                    gene_id = fields[0]
                    contig = fields[1]
                    mapping[gene_id] = contig

    logger.info(f"Loaded {len(mapping)} gene-to-contig mappings")
    return mapping
