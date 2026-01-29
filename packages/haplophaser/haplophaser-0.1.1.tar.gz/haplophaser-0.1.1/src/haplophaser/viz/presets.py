"""
Pre-configured visualization functions.

One-liner functions for common phaser visualization tasks.
"""

from __future__ import annotations

from pathlib import Path

from .assembly import AssemblyPaintingFigure
from .comparative import SyntenyFigure
from .expression import ExpressionBiasFigure
from .proportion import ProportionFigure, ProportionGenomeFigure
from .subgenome import SubgenomeFigure


def plot_haplotype_proportions(
    haplotypes: str | Path,
    reference: str | Path,
    output: str | Path,
    region: str | None = None,
    genes: str | Path | None = None,
    founders: list[str] | None = None,
    title: str | None = None,
    figsize: tuple[float, float] = (12, 6),
) -> None:
    """
    Quick haplotype proportion plot.

    Parameters
    ----------
    haplotypes : str or Path
        Path to haplotype blocks BED file
    reference : str or Path
        Reference genome (.fai)
    output : str or Path
        Output file path
    region : str, optional
        Region to display
    genes : str or Path, optional
        Gene annotation GFF3
    founders : list[str], optional
        Founder names for colors
    title : str, optional
        Figure title
    figsize : tuple
        Figure size

    Examples
    --------
    >>> plot_haplotype_proportions(
    ...     "haplotypes.bed",
    ...     "genome.fa.fai",
    ...     "figure.pdf",
    ...     region="chr1:1-10000000"
    ... )
    """
    fig = ProportionFigure(
        reference=reference,
        region=region,
        founders=founders,
        title=title,
        figsize=figsize,
    )

    fig.add_ideogram()

    if genes:
        fig.add_genes(genes)

    fig.add_haplotypes(haplotypes)
    fig.add_scale_bar()

    fig.save(output)


def plot_genome_haplotypes(
    haplotypes: str | Path,
    reference: str | Path,
    output: str | Path,
    founders: list[str] | None = None,
    n_cols: int = 5,
    figsize: tuple[float, float] | None = None,
) -> None:
    """
    Quick whole-genome haplotype plot.

    Parameters
    ----------
    haplotypes : str or Path
        Path to haplotype blocks BED file
    reference : str or Path
        Reference genome (.fai)
    output : str or Path
        Output file path
    founders : list[str], optional
        Founder names
    n_cols : int
        Number of columns in grid
    figsize : tuple, optional
        Figure size (auto if None)

    Examples
    --------
    >>> plot_genome_haplotypes("haplotypes.bed", "genome.fa.fai", "genome.pdf")
    """
    fig = ProportionGenomeFigure(
        reference=reference,
        founders=founders,
        n_cols=n_cols,
        figsize=figsize,
    )

    fig.add_ideogram()
    fig.add_haplotypes(haplotypes)

    fig.save(output)


def plot_assembly_painting(
    painting: str | Path,
    reference: str | Path,
    output: str | Path,
    chimeras: str | Path | None = None,
    region: str | None = None,
    founders: list[str] | None = None,
    title: str | None = None,
    figsize: tuple[float, float] = (14, 6),
) -> None:
    """
    Quick assembly painting plot.

    Parameters
    ----------
    painting : str or Path
        Contig painting BED file
    reference : str or Path
        Assembly .fai file
    output : str or Path
        Output file path
    chimeras : str or Path, optional
        Chimera breakpoints BED
    region : str, optional
        Region to display
    founders : list[str], optional
        Haplotype names
    title : str, optional
        Figure title
    figsize : tuple
        Figure size
    """
    fig = AssemblyPaintingFigure(
        reference=reference,
        region=region,
        founders=founders,
        title=title,
        figsize=figsize,
    )

    fig.add_ideogram()
    fig.add_painting(painting)

    if chimeras:
        fig.add_chimeras(chimeras)

    fig.add_scale_bar()

    fig.save(output)


def plot_subgenome_assignment(
    assignments: str | Path,
    reference: str | Path,
    output: str | Path,
    region: str | None = None,
    subgenomes: list[str] | None = None,
    organism: str = "auto",
    gene_density: str | Path | None = None,
    title: str | None = None,
    figsize: tuple[float, float] = (12, 6),
) -> None:
    """
    Quick subgenome assignment plot.

    Parameters
    ----------
    assignments : str or Path
        Subgenome assignment BED file
    reference : str or Path
        Reference genome .fai
    output : str or Path
        Output file path
    region : str, optional
        Region to display
    subgenomes : list[str], optional
        Subgenome names
    organism : str
        Organism for color presets
    gene_density : str or Path, optional
        Gene density bedGraph
    title : str, optional
        Figure title
    figsize : tuple
        Figure size
    """
    fig = SubgenomeFigure(
        reference=reference,
        region=region,
        subgenomes=subgenomes,
        organism=organism,
        title=title,
        figsize=figsize,
    )

    fig.add_ideogram()
    fig.add_subgenome_track(assignments)

    if gene_density:
        fig.add_gene_density(gene_density)

    fig.add_scale_bar()

    fig.save(output)


def plot_expression_bias(
    bias_results: str | Path,
    output: str | Path,
    plot_type: str = "ma",
    figsize: tuple[float, float] = (8, 6),
    **kwargs,
) -> None:
    """
    Quick expression bias plot.

    Parameters
    ----------
    bias_results : str or Path
        Expression bias results TSV
    output : str or Path
        Output file path
    plot_type : str
        Plot type: 'ma', 'distribution', 'by_chromosome'
    figsize : tuple
        Figure size
    """
    fig = ExpressionBiasFigure(bias_results, figsize=figsize)

    if plot_type == "ma":
        fig.plot_ma(**kwargs)
    elif plot_type == "distribution":
        fig.plot_bias_distribution(**kwargs)
    elif plot_type == "by_chromosome":
        fig.plot_bias_by_chromosome(**kwargs)
    else:
        raise ValueError(f"Unknown plot type: {plot_type}")

    fig.save(output)


def plot_synteny(
    synteny: str | Path,
    ref_fai: str | Path,
    query_fai: str | Path,
    output: str | Path,
    ref_region: str | None = None,
    query_region: str | None = None,
    ref_genes: str | Path | None = None,
    query_genes: str | Path | None = None,
    figsize: tuple[float, float] = (14, 10),
) -> None:
    """
    Quick synteny/comparative plot.

    Parameters
    ----------
    synteny : str or Path
        Synteny file (PAF, SyRI, etc.)
    ref_fai : str or Path
        Reference genome .fai
    query_fai : str or Path
        Query genome .fai
    output : str or Path
        Output file path
    ref_region : str, optional
        Reference region
    query_region : str, optional
        Query region
    ref_genes : str or Path, optional
        Reference genes GFF3
    query_genes : str or Path, optional
        Query genes GFF3
    figsize : tuple
        Figure size
    """
    fig = SyntenyFigure(
        ref_reference=ref_fai,
        query_reference=query_fai,
        ref_region=ref_region,
        query_region=query_region,
        figsize=figsize,
    )

    # Reference tracks
    fig.add_ref_ideogram()
    if ref_genes:
        fig.add_ref_genes(ref_genes)

    # Synteny
    fig.add_synteny(synteny)

    # Query tracks
    if query_genes:
        fig.add_query_genes(query_genes)
    fig.add_query_ideogram()

    fig.save(output)
