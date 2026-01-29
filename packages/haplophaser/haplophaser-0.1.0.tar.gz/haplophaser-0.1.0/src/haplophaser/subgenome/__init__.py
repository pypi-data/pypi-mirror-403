"""
Subgenome deconvolution for paleopolyploid genomes.

This module provides tools for assigning genomic regions to subgenomes in
paleopolyploid species like maize (~5-12 MYA WGD), wheat, and Brassica.
Unlike recent polyploids where subgenomes are clearly distinguishable,
paleopolyploids require multiple evidence sources:

- Synteny to a reference with known subgenome assignments
- Phylogenetic placement using orthologs and outgroups
- Subgenome-diagnostic markers (fixed differences)

Key concepts:

- **Subgenome**: An ancestral diploid genome now present within a polyploid
  (e.g., maize1/maize2, or SG1/SG2 in maize; A/B/D in wheat)

- **Fractionation**: Biased gene loss between subgenomes after polyploidization.
  The "dominant" subgenome (maize1) typically retains more genes and shows
  higher expression.

- **Homeologs**: Gene pairs derived from the whole-genome duplication,
  one copy in each subgenome.

Example usage:

    >>> from haplophaser.subgenome import SubgenomeConfig, SyntenySubgenomeAssigner
    >>>
    >>> # Configure for maize
    >>> config = SubgenomeConfig.maize_default()
    >>>
    >>> # Assign via synteny
    >>> assigner = SyntenySubgenomeAssigner(config)
    >>> assignments = assigner.assign(
    ...     query_assembly="new_maize.fasta",
    ...     synteny_blocks="synteny_to_B73.tsv",
    ...     reference_assignments="B73_subgenomes.bed",
    ... )
"""

from haplophaser.subgenome.fractionation import FractionationAnalyzer, FractionationReport
from haplophaser.subgenome.homeologs import HomeologFinder
from haplophaser.subgenome.integrate import SubgenomeIntegrator
from haplophaser.subgenome.markers import SubgenomeMarkerFinder
from haplophaser.subgenome.models import (
    GeneSubgenomeCall,
    HomeologPair,
    HomeologResult,
    Subgenome,
    SubgenomeAssignment,
    SubgenomeConfig,
    SubgenomeMarker,
    SyntenyBlock,
)
from haplophaser.subgenome.orthologs import OrthologSubgenomeAssigner
from haplophaser.subgenome.synteny import SyntenySubgenomeAssigner

__all__ = [
    # Models
    "Subgenome",
    "SubgenomeAssignment",
    "SubgenomeConfig",
    "SubgenomeMarker",
    "SyntenyBlock",
    "GeneSubgenomeCall",
    "HomeologPair",
    "HomeologResult",
    # Assigners
    "SyntenySubgenomeAssigner",
    "OrthologSubgenomeAssigner",
    "SubgenomeMarkerFinder",
    "SubgenomeIntegrator",
    # Analysis
    "FractionationAnalyzer",
    "FractionationReport",
    "HomeologFinder",
]
