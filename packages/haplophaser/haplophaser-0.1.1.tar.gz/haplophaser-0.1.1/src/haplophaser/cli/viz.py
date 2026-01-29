"""Visualization CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

viz_app = typer.Typer(
    name="viz",
    help="Visualization commands for phaser analysis results.",
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()


@viz_app.command()
def proportions(
    haplotypes: Annotated[
        Path,
        typer.Option("--haplotypes", "-h", help="Haplotype blocks BED file."),
    ],
    reference: Annotated[
        Path,
        typer.Option("--reference", "-r", help="Reference genome .fai file."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file (PDF/PNG/SVG)."),
    ],
    region: Annotated[
        str | None,
        typer.Option("--region", help="Region to display (e.g., chr1:1-10000000)."),
    ] = None,
    genes: Annotated[
        Path | None,
        typer.Option("--genes", "-g", help="Gene annotation GFF3 file."),
    ] = None,
    founders: Annotated[
        str | None,
        typer.Option("--founders", help="Comma-separated founder names."),
    ] = None,
    title: Annotated[
        str | None,
        typer.Option("--title", help="Figure title."),
    ] = None,
    width: Annotated[
        float,
        typer.Option("--width", help="Figure width."),
    ] = 12.0,
    height: Annotated[
        float,
        typer.Option("--height", help="Figure height."),
    ] = 6.0,
) -> None:
    """
    Plot haplotype proportions.

    Creates a publication-ready figure showing haplotype blocks
    along a genomic region.

    [bold]Example:[/bold]

        phaser viz proportions -h blocks.bed -r genome.fa.fai -o figure.pdf
    """
    from haplophaser.viz import plot_haplotype_proportions

    founder_list = founders.split(",") if founders else None

    plot_haplotype_proportions(
        haplotypes=haplotypes,
        reference=reference,
        output=output,
        region=region,
        genes=genes,
        founders=founder_list,
        title=title,
        figsize=(width, height),
    )

    console.print(f"[green]Saved figure to {output}[/green]")


@viz_app.command()
def genome(
    haplotypes: Annotated[
        Path,
        typer.Option("--haplotypes", "-h", help="Haplotype blocks BED file."),
    ],
    reference: Annotated[
        Path,
        typer.Option("--reference", "-r", help="Reference genome .fai file."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file."),
    ],
    founders: Annotated[
        str | None,
        typer.Option("--founders", help="Comma-separated founder names."),
    ] = None,
    cols: Annotated[
        int,
        typer.Option("--cols", help="Number of columns in grid."),
    ] = 5,
    width: Annotated[
        float | None,
        typer.Option("--width", help="Figure width (auto if not set)."),
    ] = None,
    height: Annotated[
        float | None,
        typer.Option("--height", help="Figure height (auto if not set)."),
    ] = None,
) -> None:
    """
    Plot whole-genome haplotypes.

    Creates a multi-chromosome figure showing haplotype blocks
    across the entire genome.

    [bold]Example:[/bold]

        phaser viz genome -h blocks.bed -r genome.fa.fai -o genome.pdf
    """
    from haplophaser.viz import plot_genome_haplotypes

    founder_list = founders.split(",") if founders else None
    figsize = (width, height) if (width and height) else None

    plot_genome_haplotypes(
        haplotypes=haplotypes,
        reference=reference,
        output=output,
        founders=founder_list,
        n_cols=cols,
        figsize=figsize,
    )

    console.print(f"[green]Saved figure to {output}[/green]")


@viz_app.command()
def assembly(
    painting: Annotated[
        Path,
        typer.Option("--painting", "-p", help="Contig painting BED file."),
    ],
    reference: Annotated[
        Path,
        typer.Option("--reference", "-r", help="Assembly .fai file."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file."),
    ],
    chimeras: Annotated[
        Path | None,
        typer.Option("--chimeras", "-c", help="Chimera breakpoints BED file."),
    ] = None,
    region: Annotated[
        str | None,
        typer.Option("--region", help="Region to display."),
    ] = None,
    founders: Annotated[
        str | None,
        typer.Option("--founders", help="Comma-separated haplotype names."),
    ] = None,
    title: Annotated[
        str | None,
        typer.Option("--title", help="Figure title."),
    ] = None,
    width: Annotated[
        float,
        typer.Option("--width", help="Figure width."),
    ] = 14.0,
    height: Annotated[
        float,
        typer.Option("--height", help="Figure height."),
    ] = 6.0,
) -> None:
    """
    Plot assembly haplotype painting.

    Visualizes contig haplotype assignments with optional
    chimera breakpoint markers.

    [bold]Example:[/bold]

        phaser viz assembly -p painting.bed -r assembly.fa.fai -o figure.pdf
    """
    from haplophaser.viz import plot_assembly_painting

    founder_list = founders.split(",") if founders else None

    plot_assembly_painting(
        painting=painting,
        reference=reference,
        output=output,
        chimeras=chimeras,
        region=region,
        founders=founder_list,
        title=title,
        figsize=(width, height),
    )

    console.print(f"[green]Saved figure to {output}[/green]")


@viz_app.command()
def subgenome(
    assignments: Annotated[
        Path,
        typer.Option("--assignments", "-a", help="Subgenome assignments BED file."),
    ],
    reference: Annotated[
        Path,
        typer.Option("--reference", "-r", help="Reference genome .fai file."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file."),
    ],
    region: Annotated[
        str | None,
        typer.Option("--region", help="Region to display."),
    ] = None,
    subgenomes: Annotated[
        str | None,
        typer.Option("--subgenomes", help="Comma-separated subgenome names."),
    ] = None,
    organism: Annotated[
        str,
        typer.Option("--organism", help="Organism for color presets."),
    ] = "auto",
    gene_density: Annotated[
        Path | None,
        typer.Option("--gene-density", help="Gene density bedGraph file."),
    ] = None,
    title: Annotated[
        str | None,
        typer.Option("--title", help="Figure title."),
    ] = None,
    width: Annotated[
        float,
        typer.Option("--width", help="Figure width."),
    ] = 12.0,
    height: Annotated[
        float,
        typer.Option("--height", help="Figure height."),
    ] = 6.0,
) -> None:
    """
    Plot subgenome assignments.

    Visualizes subgenome assignments along chromosomes.

    [bold]Example:[/bold]

        phaser viz subgenome -a assignments.bed -r genome.fa.fai -o figure.pdf
    """
    from haplophaser.viz import plot_subgenome_assignment

    sg_list = subgenomes.split(",") if subgenomes else None

    plot_subgenome_assignment(
        assignments=assignments,
        reference=reference,
        output=output,
        region=region,
        subgenomes=sg_list,
        organism=organism,
        gene_density=gene_density,
        title=title,
        figsize=(width, height),
    )

    console.print(f"[green]Saved figure to {output}[/green]")


@viz_app.command()
def expression(
    results: Annotated[
        Path,
        typer.Option("--results", "-r", help="Expression bias results TSV file."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file."),
    ],
    plot_type: Annotated[
        str,
        typer.Option(
            "--plot-type",
            help="Plot type: ma, distribution, by_chromosome.",
        ),
    ] = "ma",
    width: Annotated[
        float,
        typer.Option("--width", help="Figure width."),
    ] = 8.0,
    height: Annotated[
        float,
        typer.Option("--height", help="Figure height."),
    ] = 6.0,
) -> None:
    """
    Plot expression bias.

    Creates MA plot or distribution plot of homeolog expression bias.

    [bold]Example:[/bold]

        phaser viz expression -r bias_results.tsv -o ma_plot.pdf --plot-type ma
    """
    from haplophaser.viz import plot_expression_bias

    plot_expression_bias(
        bias_results=results,
        output=output,
        plot_type=plot_type,
        figsize=(width, height),
    )

    console.print(f"[green]Saved figure to {output}[/green]")


@viz_app.command()
def synteny(
    synteny_file: Annotated[
        Path,
        typer.Option("--synteny", "-s", help="Synteny file (PAF, SyRI, etc.)."),
    ],
    ref_fai: Annotated[
        Path,
        typer.Option("--ref-fai", help="Reference genome .fai file."),
    ],
    query_fai: Annotated[
        Path,
        typer.Option("--query-fai", help="Query genome .fai file."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file."),
    ],
    ref_region: Annotated[
        str | None,
        typer.Option("--ref-region", help="Reference region."),
    ] = None,
    query_region: Annotated[
        str | None,
        typer.Option("--query-region", help="Query region."),
    ] = None,
    ref_genes: Annotated[
        Path | None,
        typer.Option("--ref-genes", help="Reference genes GFF3 file."),
    ] = None,
    query_genes: Annotated[
        Path | None,
        typer.Option("--query-genes", help="Query genes GFF3 file."),
    ] = None,
    width: Annotated[
        float,
        typer.Option("--width", help="Figure width."),
    ] = 14.0,
    height: Annotated[
        float,
        typer.Option("--height", help="Figure height."),
    ] = 10.0,
) -> None:
    """
    Plot synteny between two genomes.

    Creates a comparative visualization with synteny ribbons
    connecting corresponding regions.

    [bold]Example:[/bold]

        phaser viz synteny -s alignment.paf --ref-fai ref.fa.fai \\
            --query-fai query.fa.fai -o synteny.pdf
    """
    from haplophaser.viz import plot_synteny

    plot_synteny(
        synteny=synteny_file,
        ref_fai=ref_fai,
        query_fai=query_fai,
        output=output,
        ref_region=ref_region,
        query_region=query_region,
        ref_genes=ref_genes,
        query_genes=query_genes,
        figsize=(width, height),
    )

    console.print(f"[green]Saved figure to {output}[/green]")
