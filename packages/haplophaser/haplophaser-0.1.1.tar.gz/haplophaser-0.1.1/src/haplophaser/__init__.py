"""
Haplophaser: Haplotype analysis toolkit for complex genomes.

Haplophaser analyzes haplotype inheritance patterns in derived lines relative to
founder/source populations. Designed with first-class polyploid support for
diploid, autopolyploid, and allopolyploid genomes.

Key capabilities:
    - Estimate haplotype proportions from VCF files
    - Paint assembly contigs by haplotype/subgenome origin
    - Detect chimeric contigs (haplotype switches)
    - Linkage-informed scaffold ordering

Example:
    >>> from haplophaser.core.models import Sample, Population
    >>> founder = Sample(name="B73", ploidy=2)
    >>> population = Population(name="NAM_founders", samples=[founder], role="founder")
"""

__version__ = "0.1.0"
__author__ = "Haplophaser Development Team"

from haplophaser.assembly.chimera import ChimeraReport, ChimericRegion
from haplophaser.assembly.paint import AssemblyPainting, ContigPainting
from haplophaser.assembly.subgenome import SubgenomeAssignment
from haplophaser.core.models import (
    HaplotypeBlock,
    Population,
    PopulationRole,
    Sample,
    Subgenome,
    Variant,
    Window,
)

# Assembly painting classes
from haplophaser.io.assembly import Assembly, Contig

__all__ = [
    "__version__",
    # Core models
    "Sample",
    "Subgenome",
    "Population",
    "PopulationRole",
    "Variant",
    "Window",
    "HaplotypeBlock",
    # Assembly painting
    "Assembly",
    "Contig",
    "AssemblyPainting",
    "ContigPainting",
    "ChimeraReport",
    "ChimericRegion",
    "SubgenomeAssignment",
]
