"""
Phaser visualization module.

Provides convenient wrappers around chromoplot for visualizing
phaser analysis results.

Examples
--------
>>> from haplophaser.viz import plot_haplotype_proportions
>>> plot_haplotype_proportions("proportions_blocks.bed", "genome.fa.fai", "output.pdf")

>>> from haplophaser.viz import ProportionFigure
>>> fig = ProportionFigure("genome.fa.fai", region="chr1")
>>> fig.add_haplotypes("proportions_blocks.bed")
>>> fig.add_genes("genes.gff3")
>>> fig.save("figure.pdf")
"""

# High-level preset functions
from .presets import (
    plot_assembly_painting,
    plot_expression_bias,
    plot_genome_haplotypes,
    plot_haplotype_proportions,
    plot_subgenome_assignment,
    plot_synteny,
)

# Figure classes for customization
from .assembly import AssemblyPaintingFigure
from .comparative import SyntenyFigure
from .expression import ExpressionBiasFigure
from .proportion import ProportionFigure, ProportionGenomeFigure
from .subgenome import SubgenomeFigure

# Utilities
from .utils import (
    get_founder_colors,
    get_phaser_theme,
    results_to_bed,
)

__all__ = [
    # Presets
    "plot_haplotype_proportions",
    "plot_genome_haplotypes",
    "plot_assembly_painting",
    "plot_subgenome_assignment",
    "plot_expression_bias",
    "plot_synteny",
    # Figure classes
    "ProportionFigure",
    "ProportionGenomeFigure",
    "AssemblyPaintingFigure",
    "SubgenomeFigure",
    "ExpressionBiasFigure",
    "SyntenyFigure",
    # Utilities
    "get_phaser_theme",
    "get_founder_colors",
    "results_to_bed",
]
