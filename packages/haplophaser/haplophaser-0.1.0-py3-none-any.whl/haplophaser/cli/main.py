"""
Phaser command-line interface.

Main entry point for all phaser commands. Built with Typer for
type-hint-driven CLI construction.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from haplophaser import __version__
from haplophaser.core.config import (
    get_default_config,
    load_config_with_overrides,
    write_config_template,
)
from haplophaser.core.models import PopulationRole
from haplophaser.io.populations import (
    get_derived_sample_names,
    get_founder_sample_names,
    load_populations,
    validate_populations_against_vcf,
)
from haplophaser.io.vcf import get_sample_names, get_vcf_stats, read_vcf

# Initialize Typer app
app = typer.Typer(
    name="phaser",
    help="Haplotype analysis toolkit for complex genomes with polyploid support.",
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()
logger = logging.getLogger(__name__)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"phaser version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable verbose output."),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress non-error output."),
    ] = False,
) -> None:
    """Phaser: Haplotype analysis for complex genomes.

    Analyze haplotype inheritance patterns in derived lines relative to
    founder populations. Full support for polyploid genomes.
    """
    # Configure logging based on verbosity
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
    )


# ============================================================================
# Proportion estimation command
# ============================================================================


@app.command()
def proportion(
    vcf: Annotated[
        Path,
        typer.Argument(help="Input VCF file with derived sample genotypes."),
    ],
    markers: Annotated[
        Path,
        typer.Option("--markers", "-m", help="Diagnostic markers file (TSV or BED from find-markers)."),
    ],
    populations: Annotated[
        Path,
        typer.Option("--populations", "-p", help="Population assignment file (TSV or YAML)."),
    ],
    output_prefix: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file prefix."),
    ] = Path("proportions"),
    window_size: Annotated[
        int,
        typer.Option("--window-size", "-w", help="Analysis window size (bp)."),
    ] = 1_000_000,
    step_size: Annotated[
        int | None,
        typer.Option("--step-size", help="Window step size (default: window_size/2)."),
    ] = None,
    min_markers: Annotated[
        int,
        typer.Option("--min-markers", help="Minimum markers per window."),
    ] = 1,
    method: Annotated[
        str,
        typer.Option("--method", help="Estimation method: frequency, likelihood, bayesian."),
    ] = "frequency",
    confidence_method: Annotated[
        str | None,
        typer.Option("--ci-method", help="Confidence interval method: bootstrap, binomial, likelihood_ratio."),
    ] = None,
    confidence_level: Annotated[
        float,
        typer.Option("--ci-level", help="Confidence level (e.g., 0.95)."),
    ] = 0.95,
    call_blocks: Annotated[
        bool,
        typer.Option("--call-blocks", help="Call haplotype blocks."),
    ] = False,
    min_block_proportion: Annotated[
        float,
        typer.Option("--min-block-proportion", help="Minimum proportion for block calling."),
    ] = 0.7,
    find_breakpoints: Annotated[
        bool,
        typer.Option("--find-breakpoints", help="Find ancestry breakpoints."),
    ] = False,
    breakpoint_method: Annotated[
        str,
        typer.Option("--breakpoint-method", help="Breakpoint detection: changepoint, threshold, hmm."),
    ] = "changepoint",
    output_formats: Annotated[
        str,
        typer.Option("--output-formats", help="Comma-separated formats: tsv,json,genome_wide,blocks_bed,breakpoints_bed."),
    ] = "tsv,genome_wide",
    samples: Annotated[
        str | None,
        typer.Option("--samples", "-s", help="Comma-separated list of samples to analyze (default: all derived)."),
    ] = None,
    use_hmm: Annotated[
        bool,
        typer.Option("--hmm", help="Use HMM-based inference for smoother results."),
    ] = False,
    hmm_recombination_rate: Annotated[
        float,
        typer.Option("--hmm-recomb-rate", help="HMM recombination rate per bp."),
    ] = 1e-8,
    hmm_error_rate: Annotated[
        float,
        typer.Option("--hmm-error-rate", help="HMM genotyping error rate."),
    ] = 0.01,
    genetic_map: Annotated[
        Path | None,
        typer.Option("--genetic-map", "-g", help="Genetic map file for HMM."),
    ] = None,
    integrate_results: Annotated[
        bool,
        typer.Option("--integrate", help="Integrate window and HMM results."),
    ] = False,
    integration_strategy: Annotated[
        str,
        typer.Option("--integration-strategy", help="Integration strategy: hmm_primary, window_primary, consensus, weighted."),
    ] = "hmm_primary",
) -> None:
    """Estimate haplotype proportions in derived samples.

    Calculate the fraction of each sample's genome derived from each
    founder population using diagnostic markers. Output includes
    genome-wide summaries and per-window proportion estimates.

    [bold]Example:[/bold]

        phaser proportion derived.vcf.gz -m markers.tsv -p samples.tsv -o props

    [bold]Output files:[/bold]

        - props_windows.tsv: Per-window proportion estimates
        - props_genome_wide.tsv: Per-sample genome-wide proportions
        - props.json: Full results in JSON format
        - props_blocks.bed: Haplotype blocks (if --call-blocks)
        - props_breakpoints.tsv: Breakpoints (if --find-breakpoints)
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.io.proportions import export_all_proportion_formats
    from haplophaser.proportion.blocks import HaplotypeBlockCaller
    from haplophaser.proportion.breakpoints import BreakpointFinder
    from haplophaser.proportion.confidence import ConfidenceEstimator
    from haplophaser.proportion.genotypes import MarkerGenotypeExtractor
    from haplophaser.proportion.windows import WindowProportionEstimator

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    # Validate inputs
    if not vcf.exists():
        console.print(f"[red]Error:[/red] VCF file not found: {vcf}")
        raise typer.Exit(code=1)

    if not markers.exists():
        console.print(f"[red]Error:[/red] Markers file not found: {markers}")
        raise typer.Exit(code=1)

    if not populations.exists():
        console.print(f"[red]Error:[/red] Population file not found: {populations}")
        raise typer.Exit(code=1)

    # Parse formats
    formats = [f.strip() for f in output_formats.split(",")]

    # Parse samples
    sample_list = None
    if samples:
        sample_list = [s.strip() for s in samples.split(",")]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load populations
        task = progress.add_task("Loading populations...", total=None)
        pops = load_populations(populations)
        progress.update(task, completed=True)

        founder_names = [p.name for p in pops if p.role == PopulationRole.FOUNDER]
        console.print(f"Found {len(founder_names)} founders: {', '.join(founder_names)}")

        # Get derived samples
        if sample_list is None:
            sample_list = get_derived_sample_names(pops)
            if not sample_list:
                # If no derived samples, use all VCF samples except founders
                founder_samples = set(get_founder_sample_names(pops))
                vcf_samples = get_sample_names(vcf)
                sample_list = [s for s in vcf_samples if s not in founder_samples]

        console.print(f"Analyzing {len(sample_list)} samples")

        # Load markers
        task = progress.add_task("Loading markers...", total=None)
        marker_set = _load_markers_from_file(markers, founder_names)
        progress.update(task, completed=True)
        console.print(f"Loaded {len(marker_set):,} markers")

        # Extract genotypes
        task = progress.add_task("Extracting genotypes at markers...", total=None)
        extractor = MarkerGenotypeExtractor()
        sample_genotypes = extractor.extract(vcf, marker_set, sample_list)
        progress.update(task, completed=True)

        # Estimate proportions
        task = progress.add_task(f"Estimating proportions ({method})...", total=None)
        estimator = WindowProportionEstimator(
            window_size=window_size,
            step_size=step_size,
            min_markers=min_markers,
            method=method,
        )
        results = estimator.estimate(sample_genotypes, marker_set)
        progress.update(task, completed=True)

        # Add confidence intervals if requested
        if confidence_method:
            task = progress.add_task(f"Calculating {confidence_method} CIs...", total=None)
            ci_estimator = ConfidenceEstimator(
                method=confidence_method,
                confidence_level=confidence_level,
            )
            ci_estimator.add_confidence_intervals(results, sample_genotypes, marker_set)
            progress.update(task, completed=True)

        # HMM-based inference if requested
        hmm_results = None
        if use_hmm:
            from haplophaser.core.genetic_map import GeneticMap
            from haplophaser.proportion.hmm import HaplotypeHMM

            task = progress.add_task("Running HMM inference...", total=None)

            # Load genetic map if provided
            gen_map = None
            if genetic_map and genetic_map.exists():
                gen_map = GeneticMap.from_plink(genetic_map)

            hmm = HaplotypeHMM(
                founders=founder_names,
                recombination_rate=hmm_recombination_rate,
                genotyping_error=hmm_error_rate,
                genetic_map=gen_map,
            )
            hmm_results = hmm.fit_predict(sample_genotypes, marker_set, samples=sample_list)
            progress.update(task, completed=True)

            # Integrate results if requested
            if integrate_results:
                from haplophaser.proportion.integrate import ResultsIntegrator

                task = progress.add_task(f"Integrating results ({integration_strategy})...", total=None)
                integrator = ResultsIntegrator(strategy=integration_strategy)
                results = integrator.integrate(results, hmm_results)
                progress.update(task, completed=True)

        # Call blocks if requested
        blocks = None
        if call_blocks:
            task = progress.add_task("Calling haplotype blocks...", total=None)
            block_caller = HaplotypeBlockCaller(min_proportion=min_block_proportion)
            blocks = block_caller.call_blocks(results)
            progress.update(task, completed=True)
            formats.extend(["blocks_bed", "blocks_tsv"])

        # Find breakpoints if requested
        breakpoints = None
        if find_breakpoints:
            task = progress.add_task("Finding breakpoints...", total=None)
            bp_finder = BreakpointFinder(method=breakpoint_method)
            breakpoints = bp_finder.find_breakpoints(results)
            progress.update(task, completed=True)
            formats.extend(["breakpoints_bed", "breakpoints_tsv"])

    # Report results
    console.print()
    console.print("[bold]Results Summary:[/bold]")

    # Show genome-wide proportions
    from rich.table import Table as RichTable

    summary_table = RichTable(title="Genome-wide Proportions")
    summary_table.add_column("Sample", style="cyan")
    for f in founder_names:
        summary_table.add_column(f, justify="right")

    for sample in results:
        row = [sample.sample_name]
        for f in founder_names:
            prop = sample.genome_wide.get(f, 0.0)
            row.append(f"{prop:.3f}")
        summary_table.add_row(*row)

    console.print(summary_table)
    console.print()

    # Show block summary if called
    if blocks:
        n_blocks = sum(sb.n_blocks for sb in blocks.samples.values())
        console.print(f"Called {n_blocks} haplotype blocks")

    # Show breakpoint summary
    if breakpoints:
        n_bps = breakpoints.total_breakpoints
        console.print(f"Found {n_bps} ancestry breakpoints")

    console.print()

    # Export files
    console.print("[bold]Exporting files:[/bold]")
    outputs = export_all_proportion_formats(
        results,
        output_prefix,
        formats=formats,
        blocks=blocks,
        breakpoints=breakpoints,
    )

    for fmt, path in outputs.items():
        console.print(f"  {fmt}: {path}")

    # Export HMM results if generated
    if hmm_results:
        from haplophaser.io.exports import (
            export_hmm_posteriors,
            export_hmm_smoothed_proportions,
            export_viterbi_path,
        )
        console.print()
        console.print("[bold]HMM output files:[/bold]")
        hmm_path = export_hmm_posteriors(hmm_results, f"{output_prefix}_hmm_posteriors.tsv.gz")
        console.print(f"  posteriors: {hmm_path}")
        vit_path = export_viterbi_path(hmm_results, f"{output_prefix}_viterbi.bed")
        console.print(f"  viterbi: {vit_path}")
        smooth_path = export_hmm_smoothed_proportions(hmm_results, f"{output_prefix}_hmm_proportions.tsv.gz")
        console.print(f"  smoothed: {smooth_path}")

    console.print()
    console.print("[green bold]Done![/green bold]")
    raise typer.Exit(code=0)


def _load_markers_from_file(
    path: Path,
    founders: list[str],
) -> DiagnosticMarkerSet:
    """Load markers from TSV or BED file.

    Args:
        path: Path to marker file
        founders: List of founder names

    Returns:
        DiagnosticMarkerSet
    """
    from haplophaser.markers.diagnostic import (
        DiagnosticMarker,
        DiagnosticMarkerSet,
        MarkerClassification,
    )

    markers = []
    suffix = path.suffix.lower()

    with open(path) as f:
        header = None
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Skip BED track line
            if line.startswith("track"):
                continue

            fields = line.split("\t")

            if header is None and suffix == ".tsv":
                # First non-comment line is header for TSV
                if "variant_id" in line or "chrom" in line:
                    header = {col: i for i, col in enumerate(fields)}
                    continue

            # Parse as TSV with header
            if header:
                chrom = fields[header.get("chrom", 0)]
                pos = int(fields[header.get("pos", 1)])
                ref = fields[header.get("ref", 2)]
                alt = fields[header.get("alt", 3)]
                variant_id = fields[header.get("variant_id", 0)] if "variant_id" in header else f"{chrom}:{pos}:{ref}:{alt}"
                confidence = float(fields[header.get("confidence", 5)]) if "confidence" in header else 0.9
                classification_str = fields[header.get("classification", 4)] if "classification" in header else "FULLY_DIAGNOSTIC"
            else:
                # Parse as BED (0-based start)
                chrom = fields[0]
                pos = int(fields[1])  # BED is 0-based
                # Try to parse name field for alleles
                if len(fields) >= 4:
                    name = fields[3]
                    if ":" in name:
                        parts = name.split(":")
                        if len(parts) >= 4:
                            ref = parts[2]
                            alt = parts[3]
                        else:
                            ref = "N"
                            alt = "N"
                    else:
                        ref = "N"
                        alt = "N"
                else:
                    ref = "N"
                    alt = "N"
                variant_id = f"{chrom}:{pos}:{ref}:{alt}"
                confidence = 0.9
                classification_str = "FULLY_DIAGNOSTIC"

            # Parse classification
            try:
                classification = MarkerClassification[classification_str.upper()]
            except KeyError:
                classification = MarkerClassification.FULLY_DIAGNOSTIC

            # Create marker (we don't have full founder info from file)
            marker = DiagnosticMarker(
                variant_id=variant_id,
                chrom=chrom,
                pos=pos,
                ref=ref,
                alt=alt,
                founder_alleles={},
                founder_frequencies={f: {ref: 0.5, alt: 0.5} for f in founders},
                confidence=confidence,
                classification=classification,
            )
            markers.append(marker)

    return DiagnosticMarkerSet(markers=markers, founders=founders)


# ============================================================================
# Summarize command
# ============================================================================


@app.command()
def summarize(
    proportions_file: Annotated[
        Path,
        typer.Argument(help="Input proportions file (TSV or JSON from proportion command)."),
    ],
    output_prefix: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file prefix."),
    ] = Path("summary"),
    blocks_file: Annotated[
        Path | None,
        typer.Option("--blocks", "-b", help="Haplotype blocks file (TSV)."),
    ] = None,
    breakpoints_file: Annotated[
        Path | None,
        typer.Option("--breakpoints", help="Breakpoints file (TSV)."),
    ] = None,
    population_name: Annotated[
        str,
        typer.Option("--population", "-p", help="Population name for summary."),
    ] = "all",
    output_formats: Annotated[
        str,
        typer.Option("--output-formats", help="Comma-separated formats: tsv,json."),
    ] = "tsv,json",
) -> None:
    """Generate genome-wide summary statistics.

    Calculate per-sample and population-level statistics from
    proportion estimation results.

    [bold]Example:[/bold]

        phaser summarize props_windows.tsv -o summary

    [bold]Output files:[/bold]

        - summary_sample.tsv: Per-sample statistics
        - summary_population.tsv: Population-level statistics
        - summary.json: Full summary in JSON format
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.analysis.summary import GenomeSummary
    from haplophaser.io.exports import (
        export_population_summary,
        export_sample_summary,
        export_summary_json,
    )

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    # Validate inputs
    if not proportions_file.exists():
        console.print(f"[red]Error:[/red] Proportions file not found: {proportions_file}")
        raise typer.Exit(code=1)

    formats = [f.strip() for f in output_formats.split(",")]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load proportions
        task = progress.add_task("Loading proportions...", total=None)
        proportions = _load_proportions_from_file(proportions_file)
        progress.update(task, completed=True)
        console.print(f"Loaded {len(proportions.sample_names)} samples")

        # Load blocks if provided
        blocks = None
        if blocks_file and blocks_file.exists():
            task = progress.add_task("Loading blocks...", total=None)
            blocks = _load_blocks_from_file(blocks_file)
            progress.update(task, completed=True)

        # Load breakpoints if provided
        breakpoints = None
        if breakpoints_file and breakpoints_file.exists():
            task = progress.add_task("Loading breakpoints...", total=None)
            breakpoints = _load_breakpoints_from_file(breakpoints_file)
            progress.update(task, completed=True)

        # Generate summary
        task = progress.add_task("Generating summary...", total=None)
        summary = GenomeSummary(proportions, blocks=blocks, breakpoints=breakpoints)
        progress.update(task, completed=True)

    # Display summary
    console.print()
    console.print("[bold]Summary Statistics:[/bold]")

    from rich.table import Table as RichTable

    pop_summary = summary.by_population(population_name)

    stat_table = RichTable(title="Population Summary")
    stat_table.add_column("Metric", style="cyan")
    stat_table.add_column("Value", justify="right")

    stat_table.add_row("Samples", str(pop_summary.n_samples))

    # Founder proportions
    for founder, prop in pop_summary.mean_founder_proportions.items():
        std = pop_summary.std_founder_proportions.get(founder, 0.0)
        stat_table.add_row(f"{founder} proportion", f"{prop:.3f} +/- {std:.3f}")

    console.print(stat_table)
    console.print()

    # Export files
    console.print("[bold]Exporting files:[/bold]")
    outputs = {}

    if "tsv" in formats:
        sample_path = export_sample_summary(summary, f"{output_prefix}_sample.tsv")
        outputs["sample_tsv"] = sample_path
        console.print(f"  sample_tsv: {sample_path}")

        pop_path = export_population_summary(pop_summary, f"{output_prefix}_population.tsv")
        outputs["population_tsv"] = pop_path
        console.print(f"  population_tsv: {pop_path}")

    if "json" in formats:
        json_path = export_summary_json(summary, f"{output_prefix}.json")
        outputs["json"] = json_path
        console.print(f"  json: {json_path}")

    console.print()
    console.print("[green bold]Done![/green bold]")
    raise typer.Exit(code=0)


# ============================================================================
# Compare command
# ============================================================================


@app.command()
def compare(
    proportions_file: Annotated[
        Path,
        typer.Argument(help="Input proportions file (TSV or JSON)."),
    ],
    output_prefix: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file prefix."),
    ] = Path("comparison"),
    blocks_file: Annotated[
        Path | None,
        typer.Option("--blocks", "-b", help="Haplotype blocks file (TSV)."),
    ] = None,
    similarity_method: Annotated[
        str,
        typer.Option("--similarity", "-s", help="Similarity method: correlation, ibs, jaccard, cosine, euclidean."),
    ] = "correlation",
    cluster: Annotated[
        bool,
        typer.Option("--cluster", "-c", help="Perform sample clustering."),
    ] = False,
    n_clusters: Annotated[
        int,
        typer.Option("--n-clusters", help="Number of clusters."),
    ] = 3,
    cluster_method: Annotated[
        str,
        typer.Option("--cluster-method", help="Clustering method: hierarchical, kmeans."),
    ] = "hierarchical",
    find_shared: Annotated[
        bool,
        typer.Option("--find-shared", help="Find shared haplotype blocks."),
    ] = False,
    min_shared_samples: Annotated[
        int,
        typer.Option("--min-shared-samples", help="Minimum samples for shared blocks."),
    ] = 2,
    output_formats: Annotated[
        str,
        typer.Option("--output-formats", help="Comma-separated formats: tsv,json."),
    ] = "tsv",
) -> None:
    """Compare haplotype patterns across samples.

    Calculate pairwise similarity, cluster samples, and find
    shared haplotype blocks.

    [bold]Example:[/bold]

        phaser compare props_windows.tsv -o comparison --cluster

    [bold]Output files:[/bold]

        - comparison_similarity.tsv: Pairwise similarity matrix
        - comparison_clusters.tsv: Cluster assignments (if --cluster)
        - comparison_shared_blocks.tsv: Shared blocks (if --find-shared)
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.analysis.comparison import SampleComparison
    from haplophaser.io.exports import (
        export_cluster_results,
        export_shared_blocks,
        export_similarity_matrix,
    )

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    # Validate inputs
    if not proportions_file.exists():
        console.print(f"[red]Error:[/red] Proportions file not found: {proportions_file}")
        raise typer.Exit(code=1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load proportions
        task = progress.add_task("Loading proportions...", total=None)
        proportions = _load_proportions_from_file(proportions_file)
        progress.update(task, completed=True)
        console.print(f"Loaded {len(proportions.sample_names)} samples")

        # Load blocks if provided
        blocks = None
        if blocks_file and blocks_file.exists():
            task = progress.add_task("Loading blocks...", total=None)
            blocks = _load_blocks_from_file(blocks_file)
            progress.update(task, completed=True)

        # Create comparison
        task = progress.add_task("Computing similarity matrix...", total=None)
        comparison = SampleComparison(proportions, blocks=blocks)
        similarity = comparison.pairwise_similarity(similarity_method)
        progress.update(task, completed=True)

        # Cluster if requested
        cluster_result = None
        if cluster:
            task = progress.add_task(f"Clustering samples ({cluster_method})...", total=None)
            cluster_result = comparison.cluster(
                n_clusters=n_clusters,
                method=cluster_method,
                similarity_method=similarity_method,
            )
            progress.update(task, completed=True)

        # Find shared blocks if requested
        shared_blocks = []
        if find_shared and blocks:
            task = progress.add_task("Finding shared blocks...", total=None)
            shared_blocks = comparison.find_shared_blocks(min_samples=min_shared_samples)
            progress.update(task, completed=True)

    # Display results
    console.print()
    console.print("[bold]Comparison Results:[/bold]")

    from rich.table import Table as RichTable

    stat_table = RichTable(title="Summary")
    stat_table.add_column("Metric", style="cyan")
    stat_table.add_column("Value", justify="right")

    stat_table.add_row("Samples", str(len(proportions.sample_names)))
    stat_table.add_row("Similarity method", similarity_method)

    import numpy as np
    # Mean off-diagonal similarity
    mask = ~np.eye(len(proportions.sample_names), dtype=bool)
    mean_sim = np.mean(similarity[mask])
    stat_table.add_row("Mean pairwise similarity", f"{mean_sim:.3f}")

    if cluster_result:
        stat_table.add_row("Clusters", str(cluster_result.n_clusters))

    if shared_blocks:
        stat_table.add_row("Shared blocks", str(len(shared_blocks)))

    console.print(stat_table)
    console.print()

    # Export files
    console.print("[bold]Exporting files:[/bold]")
    outputs = {}

    sim_path = export_similarity_matrix(comparison, f"{output_prefix}_similarity.tsv", similarity_method)
    outputs["similarity"] = sim_path
    console.print(f"  similarity: {sim_path}")

    if cluster_result:
        cluster_path = export_cluster_results(cluster_result, f"{output_prefix}_clusters.tsv")
        outputs["clusters"] = cluster_path
        console.print(f"  clusters: {cluster_path}")

    if shared_blocks:
        shared_path = export_shared_blocks(shared_blocks, f"{output_prefix}_shared_blocks.tsv")
        outputs["shared_blocks"] = shared_path
        console.print(f"  shared_blocks: {shared_path}")

    console.print()
    console.print("[green bold]Done![/green bold]")
    raise typer.Exit(code=0)


def _load_proportions_from_file(path: Path) -> ProportionResults:
    """Load proportions from TSV or JSON file."""
    from haplophaser.proportion.results import ProportionResults, SampleProportions, WindowProportion

    suffix = path.suffix.lower()

    if suffix == ".json":
        import json
        data = json.loads(path.read_text())
        return ProportionResults.from_dict(data)

    # Load from TSV
    founders = set()
    windows_by_sample: dict[str, list] = {}

    with open(path) as f:
        header = None
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            fields = line.split("\t")
            if header is None:
                header = {col: i for i, col in enumerate(fields)}
                # Extract founders from header
                for col in fields:
                    if col.endswith("_proportion") and not col.endswith("_ci_lower") and not col.endswith("_ci_upper"):
                        founder = col.replace("_proportion", "")
                        founders.add(founder)
                continue

            sample = fields[header["sample"]]
            chrom = fields[header["chrom"]]
            start = int(fields[header["start"]])
            end = int(fields[header["end"]])
            n_markers = int(fields[header.get("n_markers", 0)]) if "n_markers" in header else 0
            method = fields[header.get("method", "frequency")] if "method" in header else "frequency"

            proportions = {}
            for f in founders:
                col = f"{f}_proportion"
                if col in header:
                    proportions[f] = float(fields[header[col]])

            window = WindowProportion(
                chrom=chrom,
                start=start,
                end=end,
                proportions=proportions,
                n_markers=n_markers,
                method=method,
            )

            if sample not in windows_by_sample:
                windows_by_sample[sample] = []
            windows_by_sample[sample].append(window)

    founders_list = sorted(founders)
    results = ProportionResults(founders=founders_list)

    for sample_name, windows in windows_by_sample.items():
        sample = SampleProportions(
            sample_name=sample_name,
            founders=founders_list,
            windows=windows,
        )
        results.add_sample(sample)

    return results


def _load_blocks_from_file(path: Path) -> BlockResults:
    """Load blocks from TSV file."""
    from haplophaser.proportion.blocks import BlockResults, HaplotypeBlock, SampleBlocks

    blocks_by_sample: dict[str, list] = {}
    founders = set()

    with open(path) as f:
        header = None
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            fields = line.split("\t")
            if header is None:
                header = {col: i for i, col in enumerate(fields)}
                continue

            sample = fields[header["sample"]]
            chrom = fields[header["chrom"]]
            start = int(fields[header["start"]])
            end = int(fields[header["end"]])
            founder = fields[header["dominant_founder"]]
            mean_prop = float(fields[header.get("mean_proportion", 0.8)])
            confidence = float(fields[header.get("confidence", 0.9)])

            founders.add(founder)

            block = HaplotypeBlock(
                chrom=chrom,
                start=start,
                end=end,
                dominant_founder=founder,
                mean_proportion=mean_prop,
                confidence=confidence,
            )

            if sample not in blocks_by_sample:
                blocks_by_sample[sample] = []
            blocks_by_sample[sample].append(block)

    founders_list = sorted(founders)
    results = BlockResults(founders=founders_list)

    for sample_name, blocks in blocks_by_sample.items():
        sample_blocks = SampleBlocks(
            sample_name=sample_name,
            founders=founders_list,
            blocks=blocks,
        )
        results.add_sample(sample_blocks)

    return results


def _load_breakpoints_from_file(path: Path) -> BreakpointResults:
    """Load breakpoints from TSV file."""
    from haplophaser.proportion.breakpoints import (
        AncestryBreakpoint,
        BreakpointResults,
        SampleBreakpoints,
    )

    bps_by_sample: dict[str, list] = {}

    with open(path) as f:
        header = None
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            fields = line.split("\t")
            if header is None:
                header = {col: i for i, col in enumerate(fields)}
                continue

            sample = fields[header["sample"]]
            chrom = fields[header["chrom"]]
            position = int(fields[header["position"]])
            left_founder = fields[header["left_founder"]]
            right_founder = fields[header["right_founder"]]
            confidence = float(fields[header.get("confidence", 0.9)])

            bp = AncestryBreakpoint(
                chrom=chrom,
                position=position,
                left_founder=left_founder,
                right_founder=right_founder,
                confidence=confidence,
            )

            if sample not in bps_by_sample:
                bps_by_sample[sample] = []
            bps_by_sample[sample].append(bp)

    results = BreakpointResults()

    for sample_name, bps in bps_by_sample.items():
        sample_bps = SampleBreakpoints(
            sample_name=sample_name,
            breakpoints=bps,
        )
        results.add_sample(sample_bps)

    return results


# ============================================================================
# Haplotype painting command
# ============================================================================


@app.command()
def paint(
    proportions: Annotated[
        Path,
        typer.Argument(help="Input proportions file (from 'phaser proportion' command)."),
    ],
    output_prefix: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file prefix."),
    ] = Path("painting"),
    resolution: Annotated[
        int,
        typer.Option("--resolution", "-r", help="Bin resolution in base pairs."),
    ] = 100_000,
    method: Annotated[
        str,
        typer.Option("--method", "-m", help="Painting method: majority, probability, hmm."),
    ] = "majority",
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: tsv, h5, both."),
    ] = "tsv",
    sample: Annotated[
        str | None,
        typer.Option("--sample", "-s", help="Paint only this sample."),
    ] = None,
    chromosome: Annotated[
        str | None,
        typer.Option("--chromosome", "--chrom", help="Paint only this chromosome."),
    ] = None,
) -> None:
    """Paint chromosomes by haplotype origin.

    Create a genome-wide ancestry matrix from proportion estimates.
    Output can be used for visualization with genome browsers or
    heatmap plotting tools.

    [bold]Example:[/bold]

        phaser paint proportions_windows.tsv -o painting -r 100000

    [bold]Output files:[/bold]

        - {output}_matrix.tsv: Ancestry painting matrix
        - {output}_matrix.h5: HDF5 format (if --format h5 or both)
    """
    from haplophaser.analysis.painting import AncestryPainter
    from haplophaser.io.exports import export_painting_matrix
    from haplophaser.io.proportions import load_proportions

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    # Validate inputs
    if not proportions.exists():
        console.print(f"[red]Error:[/red] Proportions file not found: {proportions}")
        raise typer.Exit(code=1)

    console.print("[bold]Generating ancestry painting...[/bold]")
    console.print()

    # Load proportions
    console.print(f"  Loading proportions from: {proportions}")
    try:
        prop_results = load_proportions(proportions)
    except Exception as e:
        console.print(f"[red]Error loading proportions:[/red] {e}")
        raise typer.Exit(code=1)

    # Filter by sample if specified
    if sample and sample not in prop_results.samples:
        console.print(f"[red]Error:[/red] Sample '{sample}' not found in proportions")
        raise typer.Exit(code=1)

    console.print(f"  Resolution: {resolution:,} bp")
    console.print(f"  Method: {method}")
    console.print()

    # Create painter
    painter = AncestryPainter(
        resolution=resolution,
        method=method,
    )

    # Generate painting
    painting = painter.paint(prop_results)

    # Export
    output_prefix.parent.mkdir(parents=True, exist_ok=True)

    if output_format in ("tsv", "both"):
        tsv_path = export_painting_matrix(
            painting,
            f"{output_prefix}_matrix.tsv.gz",
            format="tsv",
        )
        console.print(f"  Written: {tsv_path}")

    if output_format in ("h5", "both"):
        h5_path = export_painting_matrix(
            painting,
            f"{output_prefix}_matrix.h5",
            format="h5",
        )
        console.print(f"  Written: {h5_path}")

    console.print()
    console.print("[green]Painting complete![/green]")

    raise typer.Exit(code=0)


# ============================================================================
# Scaffold ordering command
# ============================================================================


@app.command()
def scaffold(
    vcf: Annotated[
        Path,
        typer.Argument(help="Input VCF file with scaffold variants."),
    ],
    populations: Annotated[
        Path,
        typer.Option("--populations", "-p", help="Population assignment file."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output directory."),
    ] = Path("phaser_output"),
    genetic_map: Annotated[
        Path | None,
        typer.Option("--genetic-map", "-g", help="Genetic map file."),
    ] = None,
    min_markers: Annotated[
        int,
        typer.Option("--min-markers", help="Minimum markers per scaffold."),
    ] = 10,
) -> None:
    """Order scaffolds using linkage information.

    Use haplotype phase information to order and orient scaffolds
    relative to a reference genetic map or chromosome-level assembly.

    [bold]Example:[/bold]

        phaser scaffold scaffolds.vcf.gz -p samples.tsv -g map.tsv

    [bold]Output files:[/bold]

        - scaffold_order.tsv: Ordered scaffold list with orientations
        - scaffold_groups.tsv: Linkage group assignments
    """
    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    console.print("[yellow]scaffold[/yellow] command not yet implemented")
    console.print()
    console.print("Would order scaffolds:")
    console.print(f"  VCF: {vcf}")
    console.print(f"  Populations: {populations}")
    console.print(f"  Genetic map: {genetic_map or 'not provided'}")
    console.print(f"  Min markers: {min_markers}")

    # TODO: Implement scaffold ordering
    raise typer.Exit(code=0)


# ============================================================================
# Quality control command
# ============================================================================


@app.command()
def qc(
    proportions: Annotated[
        Path,
        typer.Argument(help="Input proportions file (from 'phaser proportion' command)."),
    ],
    markers: Annotated[
        Path | None,
        typer.Option("--markers", "-m", help="Diagnostic markers file (for additional QC)."),
    ] = None,
    output_prefix: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file prefix."),
    ] = Path("qc_report"),
    low_confidence_threshold: Annotated[
        float,
        typer.Option("--low-confidence", help="Threshold for low confidence calls."),
    ] = 0.5,
    high_missing_threshold: Annotated[
        float,
        typer.Option("--high-missing", help="Threshold for high missing rate."),
    ] = 0.3,
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: tsv, json, both."),
    ] = "tsv",
) -> None:
    """Run quality control checks on proportion estimates.

    Analyze proportion results for potential issues:
    - High missing data rates per sample
    - Low confidence calls
    - Chromosome coverage gaps
    - Samples with unusual patterns

    [bold]Example:[/bold]

        phaser qc proportions_windows.tsv -o qc_report

    [bold]Output files:[/bold]

        - {output}_summary.tsv: QC summary per sample
        - {output}_warnings.tsv: Detailed warnings
    """
    from haplophaser.analysis.qc import ProportionQC
    from haplophaser.io.exports import export_qc_report, export_qc_warnings
    from haplophaser.io.proportions import load_proportions

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    # Validate inputs
    if not proportions.exists():
        console.print(f"[red]Error:[/red] Proportions file not found: {proportions}")
        raise typer.Exit(code=1)

    console.print("[bold]Running quality control analysis...[/bold]")
    console.print()

    # Load proportions
    console.print(f"  Loading proportions from: {proportions}")
    try:
        prop_results = load_proportions(proportions)
    except Exception as e:
        console.print(f"[red]Error loading proportions:[/red] {e}")
        raise typer.Exit(code=1)

    console.print(f"  Found {len(prop_results.samples)} samples")
    console.print()

    # Create QC analyzer
    qc_analyzer = ProportionQC(
        proportions=prop_results,
        low_confidence_threshold=low_confidence_threshold,
        high_missing_threshold=high_missing_threshold,
    )

    # Generate report
    qc_report = qc_analyzer.generate_report()

    # Display summary
    console.print("[bold]QC Summary:[/bold]")
    console.print(f"  Total samples: {len(qc_report.samples)}")
    console.print(f"  Samples passing: {qc_report.n_samples_passed}")
    console.print(f"  Total warnings: {qc_report.n_warnings}")
    console.print(f"  Total errors: {qc_report.n_errors}")
    console.print()

    # Export
    output_prefix.parent.mkdir(parents=True, exist_ok=True)

    if output_format in ("tsv", "both"):
        report_path = export_qc_report(
            qc_report,
            f"{output_prefix}_summary.tsv",
            format="tsv",
        )
        console.print(f"  Written: {report_path}")

        if qc_report.n_warnings > 0 or qc_report.n_errors > 0:
            warnings_path = export_qc_warnings(
                qc_report,
                f"{output_prefix}_warnings.tsv",
            )
            console.print(f"  Written: {warnings_path}")

    if output_format in ("json", "both"):
        report_path = export_qc_report(
            qc_report,
            f"{output_prefix}_summary.json",
            format="json",
        )
        console.print(f"  Written: {report_path}")

    console.print()

    # Report status
    if qc_report.n_errors > 0:
        console.print("[red]QC completed with errors![/red]")
        console.print("Check the warnings file for details.")
        raise typer.Exit(code=1)
    elif qc_report.n_warnings > 0:
        console.print("[yellow]QC completed with warnings.[/yellow]")
        console.print("Check the warnings file for details.")
    else:
        console.print("[green]QC passed - no issues found![/green]")

    raise typer.Exit(code=0)


# ============================================================================
# Input validation command
# ============================================================================


@app.command("check-input")
def check_input(
    vcf: Annotated[
        Path,
        typer.Option("--vcf", "-v", help="Input VCF file."),
    ],
    populations: Annotated[
        Path,
        typer.Option("--populations", "-p", help="Population assignment file (TSV or YAML)."),
    ],
    strict: Annotated[
        bool,
        typer.Option("--strict", "-s", help="Fail on any validation warning."),
    ] = False,
) -> None:
    """Validate VCF and population files before analysis.

    Checks that input files are valid and compatible:
    - VCF file can be read and parsed
    - Population file format is valid
    - All population samples exist in the VCF
    - No duplicate sample assignments

    Reports summary statistics about the input data.

    [bold]Example:[/bold]

        phaser check-input --vcf variants.vcf.gz --populations samples.tsv

    [bold]Exit codes:[/bold]

        0: Validation passed
        1: Validation failed (errors found)
    """
    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()
    console.print("[bold]Validating input files...[/bold]")
    console.print()

    has_errors = False

    # Check VCF file exists
    if not vcf.exists():
        console.print(f"[red]Error:[/red] VCF file not found: {vcf}")
        raise typer.Exit(code=1)

    # Check population file exists
    if not populations.exists():
        console.print(f"[red]Error:[/red] Population file not found: {populations}")
        raise typer.Exit(code=1)

    # Load and validate VCF
    console.print(f"[cyan]VCF file:[/cyan] {vcf}")
    try:
        vcf_stats = get_vcf_stats(vcf)
        vcf_samples = get_sample_names(vcf)

        vcf_table = Table(show_header=False, box=None, padding=(0, 2))
        vcf_table.add_column("Label", style="dim")
        vcf_table.add_column("Value")

        vcf_table.add_row("  Samples:", str(vcf_stats.n_samples))
        vcf_table.add_row("  Variants:", f"{vcf_stats.n_variants:,}")
        vcf_table.add_row("  Chromosomes:", ", ".join(sorted(vcf_stats.chromosomes)))

        console.print(vcf_table)
        console.print()

    except Exception as e:
        console.print(f"[red]Error reading VCF:[/red] {e}")
        raise typer.Exit(code=1)

    # Load and validate populations
    console.print(f"[cyan]Population file:[/cyan] {populations}")
    try:
        pops = load_populations(populations)

        founder_names = get_founder_sample_names(pops)
        derived_names = get_derived_sample_names(pops)

        pop_table = Table(show_header=False, box=None, padding=(0, 2))
        pop_table.add_column("Label", style="dim")
        pop_table.add_column("Value")

        pop_table.add_row("  Populations:", str(len(pops)))
        pop_table.add_row("  Founder samples:", str(len(founder_names)))
        pop_table.add_row("  Derived samples:", str(len(derived_names)))
        pop_table.add_row("  Total samples:", str(len(founder_names) + len(derived_names)))

        console.print(pop_table)
        console.print()

        # Show population details
        detail_table = Table(title="Population Details")
        detail_table.add_column("Name", style="cyan")
        detail_table.add_column("Role", style="green")
        detail_table.add_column("Samples")
        detail_table.add_column("Ploidy")

        for pop in pops:
            role_color = "blue" if pop.role == PopulationRole.FOUNDER else "yellow"
            ploidy_values = {s.ploidy for s in pop.samples}
            ploidy_str = ", ".join(str(p) for p in sorted(ploidy_values))
            detail_table.add_row(
                pop.name,
                f"[{role_color}]{pop.role.value}[/{role_color}]",
                str(len(pop.samples)),
                ploidy_str,
            )

        console.print(detail_table)
        console.print()

    except Exception as e:
        console.print(f"[red]Error reading population file:[/red] {e}")
        raise typer.Exit(code=1)

    # Validate populations against VCF
    console.print("[bold]Cross-validation:[/bold]")
    result = validate_populations_against_vcf(pops, vcf_samples, strict=strict)

    if result.missing_samples:
        console.print(f"  [yellow]Warning:[/yellow] {len(result.missing_samples)} samples not in VCF:")
        for sample in result.missing_samples[:5]:
            console.print(f"    - {sample}")
        if len(result.missing_samples) > 5:
            console.print(f"    ... and {len(result.missing_samples) - 5} more")

    if result.extra_vcf_samples:
        console.print(f"  [dim]Info:[/dim] {len(result.extra_vcf_samples)} VCF samples not in population file")

    if result.warnings:
        for warning in result.warnings:
            console.print(f"  [yellow]Warning:[/yellow] {warning}")

    if result.errors:
        has_errors = True
        for error in result.errors:
            console.print(f"  [red]Error:[/red] {error}")

    console.print()

    # Final status
    if has_errors or (strict and not result.valid):
        console.print("[red bold]Validation FAILED[/red bold]")
        raise typer.Exit(code=1)
    elif result.warnings and not strict:
        console.print("[yellow bold]Validation PASSED with warnings[/yellow bold]")
        raise typer.Exit(code=0)
    else:
        console.print("[green bold]Validation PASSED[/green bold]")
        raise typer.Exit(code=0)


# ============================================================================
# Diagnostic marker finding command
# ============================================================================


@app.command("find-markers")
def find_markers(
    vcf: Annotated[
        Path,
        typer.Argument(help="Input VCF file with founder genotypes."),
    ],
    populations: Annotated[
        Path,
        typer.Option("--populations", "-p", help="Population assignment file (TSV or YAML)."),
    ],
    output_prefix: Annotated[
        Path,
        typer.Option("--output-prefix", "-o", help="Output file prefix."),
    ] = Path("diagnostic_markers"),
    min_freq_diff: Annotated[
        float,
        typer.Option("--min-freq-diff", help="Minimum allele frequency difference between founders."),
    ] = 0.7,
    max_minor_freq: Annotated[
        float,
        typer.Option("--max-minor-freq", help="Maximum minor allele frequency within a founder."),
    ] = 0.1,
    min_samples: Annotated[
        int,
        typer.Option("--min-samples", help="Minimum samples per founder for reliable frequency."),
    ] = 2,
    output_formats: Annotated[
        str,
        typer.Option("--output-formats", help="Comma-separated output formats: bed,tsv,vcf,summary."),
    ] = "bed,tsv,vcf",
    founders_only: Annotated[
        bool,
        typer.Option("--founders-only", help="Only use founder populations for frequency calculation."),
    ] = True,
) -> None:
    """Find diagnostic markers that distinguish founder populations.

    Identifies SNPs with significant allele frequency differences between
    founders, suitable for tracking haplotype inheritance in derived samples.

    [bold]Example:[/bold]

        phaser find-markers founders.vcf.gz -p founders.tsv -o markers

    [bold]Output files:[/bold]

        - markers.bed: BED format for genome browsers
        - markers.tsv: Full annotation with frequencies
        - markers.vcf: VCF format for downstream tools
        - markers_summary.txt: Quality report (if summary in formats)
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.core.filters import BiallelicFilter, FilterChain, PassFilter
    from haplophaser.core.frequencies import AlleleFrequencyCalculator
    from haplophaser.io.markers import export_all_marker_formats
    from haplophaser.markers.diagnostic import DiagnosticMarkerFinder
    from haplophaser.markers.quality import MarkerQualityAssessment

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    # Validate inputs
    if not vcf.exists():
        console.print(f"[red]Error:[/red] VCF file not found: {vcf}")
        raise typer.Exit(code=1)

    if not populations.exists():
        console.print(f"[red]Error:[/red] Population file not found: {populations}")
        raise typer.Exit(code=1)

    # Parse output formats
    formats = [f.strip() for f in output_formats.split(",")]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load populations
        task = progress.add_task("Loading populations...", total=None)
        pops = load_populations(populations)
        progress.update(task, completed=True)

        if founders_only:
            pops = [p for p in pops if p.role == PopulationRole.FOUNDER]

        if len(pops) < 2:
            console.print("[red]Error:[/red] Need at least 2 founder populations")
            raise typer.Exit(code=1)

        founder_names = [p.name for p in pops]
        console.print(f"Using {len(pops)} populations: {', '.join(founder_names)}")

        # Set up filters for biallelic, PASS variants
        filters = FilterChain([
            PassFilter(),
            BiallelicFilter(),
        ])

        # Load and filter variants
        task = progress.add_task("Loading variants...", total=None)
        variants = list(read_vcf(vcf, filters=filters))
        progress.update(task, completed=True)
        console.print(f"Loaded {len(variants):,} biallelic variants")

        # Calculate allele frequencies
        task = progress.add_task("Calculating allele frequencies...", total=None)
        freq_calc = AlleleFrequencyCalculator(min_samples=min_samples)
        frequencies = freq_calc.calculate(variants, pops)
        progress.update(task, completed=True)
        console.print(f"Calculated frequencies for {len(frequencies):,} variants")

        # Find diagnostic markers
        task = progress.add_task("Finding diagnostic markers...", total=None)
        finder = DiagnosticMarkerFinder(
            min_freq_diff=min_freq_diff,
            max_minor_freq=max_minor_freq,
            min_samples=min_samples,
            allow_partial=True,
        )
        markers = finder.find(frequencies, founder_names)
        progress.update(task, completed=True)

    # Report results
    console.print()
    console.print("[bold]Results:[/bold]")

    results_table = Table(show_header=False, box=None, padding=(0, 2))
    results_table.add_column("Label", style="dim")
    results_table.add_column("Value")

    results_table.add_row("  Total markers:", f"{len(markers):,}")
    results_table.add_row("  Fully diagnostic:", f"{len(markers.fully_diagnostic):,}")
    results_table.add_row("  Partially diagnostic:", f"{len(markers.partially_diagnostic):,}")
    results_table.add_row("  Informative:", f"{len(markers.informative):,}")

    console.print(results_table)
    console.print()

    # Quality assessment
    assessment = MarkerQualityAssessment(markers)

    # Show chromosome summary
    if markers.markers:
        chrom_table = Table(title="Markers by Chromosome")
        chrom_table.add_column("Chrom", style="cyan")
        chrom_table.add_column("Markers", justify="right")
        chrom_table.add_column("Diagnostic", justify="right")
        chrom_table.add_column("Density/Mb", justify="right")
        chrom_table.add_column("Gaps", justify="right")

        for chrom in assessment.chromosomes[:10]:
            summary = assessment.chromosome_summary(chrom)
            if summary:
                chrom_table.add_row(
                    chrom,
                    f"{summary.n_markers:,}",
                    f"{summary.n_fully_diagnostic:,}",
                    f"{summary.density:.1f}",
                    str(summary.n_gaps),
                )

        if len(assessment.chromosomes) > 10:
            chrom_table.add_row("...", "...", "...", "...", "...")

        console.print(chrom_table)
        console.print()

    # Export files
    console.print("[bold]Exporting files:[/bold]")

    # Include summary if requested

    outputs = export_all_marker_formats(
        markers,
        output_prefix,
        formats=[f for f in formats if f not in ("summary", "gaps", "density")],
        assessment=assessment if "summary" in formats else None,
    )

    # Export summary if requested
    if "summary" in formats:
        from haplophaser.io.markers import export_quality_report
        summary_path = Path(str(output_prefix) + "_summary.txt")
        export_quality_report(assessment, summary_path)
        outputs["summary"] = summary_path

    for fmt, path in outputs.items():
        console.print(f"  {fmt}: {path}")

    console.print()
    console.print("[green bold]Done![/green bold]")
    raise typer.Exit(code=0)


# ============================================================================
# Configuration utilities
# ============================================================================


@app.command("init-config")
def init_config(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output configuration file path."),
    ] = Path("phaser.yaml"),
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing file."),
    ] = False,
) -> None:
    """Generate a template configuration file.

    Creates a YAML configuration file with all available options
    and their default values, with explanatory comments.

    [bold]Example:[/bold]

        phaser init-config -o my_analysis.yaml
    """
    if output.exists() and not force:
        console.print(f"[red]Error:[/red] {output} already exists. Use --force to overwrite.")
        raise typer.Exit(code=1)

    write_config_template(output)
    console.print(f"[green]Created configuration template:[/green] {output}")


@app.command("show-config")
def show_config(
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Configuration file to display."),
    ] = None,
) -> None:
    """Display current configuration.

    Shows either the loaded configuration from file or default values.
    """
    cfg = load_config_with_overrides(path=config) if config else get_default_config()

    table = Table(title="Phaser Configuration")
    table.add_column("Section", style="cyan")
    table.add_column("Parameter", style="green")
    table.add_column("Value")

    # Window settings
    table.add_row("window", "size", f"{cfg.window.size:,} bp")
    table.add_row("window", "step", f"{cfg.window.step:,} bp" if cfg.window.step else "same as size")
    table.add_row("window", "min_variants", str(cfg.window.min_variants))

    # Filter settings
    table.add_row("filter", "min_qual", str(cfg.filter.min_qual))
    table.add_row("filter", "min_maf", str(cfg.filter.min_maf))
    table.add_row("filter", "max_missing", str(cfg.filter.max_missing))
    table.add_row("filter", "biallelic_only", str(cfg.filter.biallelic_only))

    # HMM settings
    table.add_row("hmm", "transition_rate", f"{cfg.hmm.transition_rate:.2e}")
    table.add_row("hmm", "error_rate", str(cfg.hmm.error_rate))
    table.add_row("hmm", "min_confidence", str(cfg.hmm.min_confidence))

    # General settings
    table.add_row("general", "ploidy", str(cfg.ploidy))
    table.add_row("general", "n_threads", str(cfg.n_threads))

    console.print(table)


# ============================================================================
# Info command
# ============================================================================


@app.command()
def info() -> None:
    """Display package information and dependencies."""
    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()
    console.print("Haplotype analysis toolkit for complex genomes")
    console.print()

    table = Table(title="Environment")
    table.add_column("Component", style="cyan")
    table.add_column("Version/Status")

    table.add_row("Python", sys.version.split()[0])
    table.add_row("Phaser", __version__)

    # Check dependencies
    try:
        import numpy
        table.add_row("NumPy", numpy.__version__)
    except ImportError:
        table.add_row("NumPy", "[red]not installed[/red]")

    try:
        import pydantic
        table.add_row("Pydantic", pydantic.__version__)
    except ImportError:
        table.add_row("Pydantic", "[red]not installed[/red]")

    try:
        import cyvcf2
        table.add_row("cyvcf2", cyvcf2.__version__)
    except ImportError:
        table.add_row("cyvcf2", "[yellow]not installed[/yellow]")

    console.print(table)


# ============================================================================
# Assembly painting commands
# ============================================================================


@app.command("map-markers")
def map_markers(
    assembly: Annotated[
        Path,
        typer.Option("--assembly", "-a", help="Assembly FASTA file."),
    ],
    markers: Annotated[
        Path,
        typer.Option("--markers", "-m", help="Diagnostic markers TSV file."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output marker hits TSV file."),
    ] = Path("marker_hits.tsv"),
    vcf: Annotated[
        Path | None,
        typer.Option("--vcf", "-v", help="VCF file called against assembly (alternative to mapping)."),
    ] = None,
    marker_sequences: Annotated[
        Path | None,
        typer.Option("--marker-sequences", help="FASTA with marker flank sequences."),
    ] = None,
    reference_fasta: Annotated[
        Path | None,
        typer.Option("--reference", "-r", help="Reference FASTA for extracting marker flanks."),
    ] = None,
    method: Annotated[
        str,
        typer.Option("--method", help="Mapping method: minimap2, exact, vcf."),
    ] = "minimap2",
    min_identity: Annotated[
        float,
        typer.Option("--min-identity", help="Minimum alignment identity (0-1)."),
    ] = 0.95,
    populations: Annotated[
        Path | None,
        typer.Option("--populations", "-p", help="Population file for loading marker founder info."),
    ] = None,
) -> None:
    """Map diagnostic markers to assembly coordinates.

    Maps markers to the assembly using minimap2 or from a VCF file
    called against the assembly.

    [bold]Example:[/bold]

        phaser map-markers -a contigs.fasta -m markers.tsv -o hits.tsv

    [bold]Alternative using VCF:[/bold]

        phaser map-markers -a contigs.fasta -m markers.tsv --vcf variants.vcf.gz
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.assembly.mapping import MarkerMapper, export_marker_hits_tsv
    from haplophaser.io.assembly import Assembly

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    # Validate inputs
    if not assembly.exists():
        console.print(f"[red]Error:[/red] Assembly file not found: {assembly}")
        raise typer.Exit(code=1)

    if not markers.exists():
        console.print(f"[red]Error:[/red] Markers file not found: {markers}")
        raise typer.Exit(code=1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load assembly
        task = progress.add_task("Loading assembly...", total=None)
        if assembly.suffix == ".fai":
            asm = Assembly.from_fai(assembly)
        else:
            asm = Assembly.from_fai(Path(str(assembly) + ".fai")) if Path(str(assembly) + ".fai").exists() else Assembly.from_fasta(assembly, load_sequences=False)
        progress.update(task, completed=True)
        console.print(f"Loaded assembly: {asm.n_contigs:,} contigs, {asm.total_size:,} bp")

        # Load markers
        task = progress.add_task("Loading markers...", total=None)
        founder_names = []
        if populations and populations.exists():
            pops = load_populations(populations)
            founder_names = [p.name for p in pops if p.role == PopulationRole.FOUNDER]

        marker_set = _load_markers_from_file(markers, founder_names)
        progress.update(task, completed=True)
        console.print(f"Loaded {len(marker_set):,} markers")

        # Map markers
        task = progress.add_task("Mapping markers...", total=None)

        if vcf and vcf.exists():
            # Use VCF-based mapping
            mapper = MarkerMapper(method="vcf")
            results = mapper.from_vcf(vcf, marker_set, asm)
        else:
            # Use alignment-based mapping
            mapper = MarkerMapper(
                method=method,
                min_identity=min_identity,
            )
            results = mapper.map(
                marker_set,
                asm,
                marker_sequences=marker_sequences,
                reference_fasta=reference_fasta,
                assembly_fasta=assembly if assembly.suffix not in (".fai",) else None,
            )
        progress.update(task, completed=True)

    # Report results
    console.print()
    console.print("[bold]Mapping Results:[/bold]")
    console.print(f"  Unique mappings: {results.mapped_unique:,}")
    console.print(f"  Multi-hit: {results.mapped_multiple:,}")
    console.print(f"  Unmapped: {results.unmapped:,}")
    console.print(f"  Mapping rate: {results.mapping_rate:.1%}")
    console.print()

    # Export
    output_path = export_marker_hits_tsv(results, output)
    console.print(f"[green]Written:[/green] {output_path}")

    raise typer.Exit(code=0)


@app.command("paint-assembly")
def paint_assembly_cmd(
    assembly: Annotated[
        Path,
        typer.Option("--assembly", "-a", help="Assembly FASTA or FAI file."),
    ],
    marker_hits: Annotated[
        Path,
        typer.Option("--marker-hits", "-h", help="Marker hits TSV from map-markers."),
    ],
    markers: Annotated[
        Path | None,
        typer.Option("--markers", "-m", help="Original diagnostic markers TSV."),
    ] = None,
    output_prefix: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file prefix."),
    ] = Path("painted_assembly"),
    min_markers: Annotated[
        int,
        typer.Option("--min-markers", help="Minimum markers for assignment."),
    ] = 5,
    min_proportion: Annotated[
        float,
        typer.Option("--min-proportion", help="Minimum proportion for assignment."),
    ] = 0.8,
    detect_chimeras: Annotated[
        bool,
        typer.Option("--detect-chimeras/--no-detect-chimeras", help="Detect chimeric contigs."),
    ] = True,
    chimera_window: Annotated[
        int,
        typer.Option("--chimera-window", help="Window size for chimera detection."),
    ] = 100_000,
    output_formats: Annotated[
        str,
        typer.Option("--output-formats", help="Comma-separated formats: tsv,bed,json."),
    ] = "tsv,bed",
    populations: Annotated[
        Path | None,
        typer.Option("--populations", "-p", help="Population file for founder names."),
    ] = None,
) -> None:
    """Paint assembly contigs by haplotype origin.

    Assigns each contig to a founder haplotype based on diagnostic
    marker evidence. Optionally detects chimeric contigs.

    [bold]Example:[/bold]

        phaser paint-assembly -a contigs.fasta -h hits.tsv -o painted

    [bold]Output files:[/bold]

        - painted_assignments.tsv: Contig assignments
        - painted_haplotypes.bed: BED with colors by founder
        - painted_chimeras.tsv: Chimera breakpoints (if detected)
        - painted_qc_report.txt: QC summary
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.assembly.mapping import load_marker_hits
    from haplophaser.assembly.paint import ContigPainter
    from haplophaser.assembly.qc import generate_assembly_qc_report
    from haplophaser.io.assembly import Assembly
    from haplophaser.io.assembly_export import export_all_painting_formats

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    # Validate inputs
    if not assembly.exists():
        console.print(f"[red]Error:[/red] Assembly file not found: {assembly}")
        raise typer.Exit(code=1)

    if not marker_hits.exists():
        console.print(f"[red]Error:[/red] Marker hits file not found: {marker_hits}")
        raise typer.Exit(code=1)

    formats = [f.strip() for f in output_formats.split(",")]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load assembly
        task = progress.add_task("Loading assembly...", total=None)
        if assembly.suffix == ".fai":
            asm = Assembly.from_fai(assembly)
        else:
            fai_path = Path(str(assembly) + ".fai")
            asm = Assembly.from_fai(fai_path) if fai_path.exists() else Assembly.from_fasta(assembly, load_sequences=False)
        progress.update(task, completed=True)
        console.print(f"Loaded assembly: {asm.n_contigs:,} contigs")

        # Load marker hits
        task = progress.add_task("Loading marker hits...", total=None)
        hits = load_marker_hits(marker_hits)
        progress.update(task, completed=True)
        console.print(f"Loaded {len(hits):,} marker hits")

        # Load markers if provided
        marker_set = None
        if markers and markers.exists():
            task = progress.add_task("Loading markers...", total=None)
            founder_names = []
            if populations and populations.exists():
                pops = load_populations(populations)
                founder_names = [p.name for p in pops if p.role == PopulationRole.FOUNDER]
            marker_set = _load_markers_from_file(markers, founder_names)
            progress.update(task, completed=True)

        # Paint contigs
        task = progress.add_task("Painting contigs...", total=None)
        painter = ContigPainter(
            min_markers=min_markers,
            min_proportion=min_proportion,
            detect_chimeras=detect_chimeras,
            chimera_window_size=chimera_window,
        )
        painting = painter.paint(asm, hits, marker_set)
        progress.update(task, completed=True)

        # Generate QC report
        task = progress.add_task("Generating QC report...", total=None)
        qc_report = generate_assembly_qc_report(
            asm, painting=painting, chimeras=None
        )
        progress.update(task, completed=True)

    # Report results
    console.print()
    console.print("[bold]Painting Results:[/bold]")

    from rich.table import Table as RichTable

    summary = painting.summary()

    results_table = RichTable(show_header=False, box=None, padding=(0, 2))
    results_table.add_column("Label", style="dim")
    results_table.add_column("Value")

    results_table.add_row("  Assigned:", f"{summary['n_assigned']:,} / {summary['n_contigs']:,} contigs ({summary['assignment_rate_contigs']:.1%})")
    results_table.add_row("  Assigned bp:", f"{summary['total_assigned_bp']:,} ({summary['assignment_rate_bp']:.1%})")
    results_table.add_row("  Chimeric:", f"{summary['n_chimeric']:,}")
    results_table.add_row("  Unassigned:", f"{summary['n_unassigned']:,}")

    console.print(results_table)
    console.print()

    # Per-founder breakdown
    if summary['by_founder']:
        founder_table = RichTable(title="Per-Founder Breakdown")
        founder_table.add_column("Founder", style="cyan")
        founder_table.add_column("Contigs", justify="right")
        founder_table.add_column("Total bp", justify="right")
        founder_table.add_column("Markers", justify="right")

        for founder, stats in sorted(summary['by_founder'].items()):
            founder_table.add_row(
                founder,
                f"{stats['n_contigs']:,}",
                f"{stats['total_bp']:,}",
                f"{stats['n_markers']:,}",
            )

        console.print(founder_table)
        console.print()

    # Export files
    console.print("[bold]Exporting files:[/bold]")
    outputs = export_all_painting_formats(
        painting,
        output_prefix,
        qc_report=qc_report,
        formats=formats,
    )

    for name, path in outputs.items():
        console.print(f"  {name}: {path}")

    console.print()
    console.print("[green bold]Done![/green bold]")
    raise typer.Exit(code=0)


@app.command("detect-chimeras")
def detect_chimeras_cmd(
    assembly: Annotated[
        Path,
        typer.Option("--assembly", "-a", help="Assembly FASTA or FAI file."),
    ],
    marker_hits: Annotated[
        Path,
        typer.Option("--marker-hits", "-h", help="Marker hits TSV from map-markers."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output chimera report TSV."),
    ] = Path("chimera_report.tsv"),
    window_size: Annotated[
        int,
        typer.Option("--window-size", "-w", help="Sliding window size."),
    ] = 50_000,
    min_markers_per_window: Annotated[
        int,
        typer.Option("--min-markers", help="Minimum markers per window."),
    ] = 3,
    switch_threshold: Annotated[
        float,
        typer.Option("--switch-threshold", help="Proportion change for switch calling."),
    ] = 0.5,
    populations: Annotated[
        Path | None,
        typer.Option("--populations", "-p", help="Population file for founder names."),
    ] = None,
) -> None:
    """Detect chimeric contigs with haplotype switches.

    Identifies contigs where the dominant founder changes along the
    sequence, indicating potential misassemblies.

    [bold]Example:[/bold]

        phaser detect-chimeras -a contigs.fasta -h hits.tsv -o chimeras.tsv
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.assembly.chimera import ChimeraDetector
    from haplophaser.assembly.mapping import load_marker_hits
    from haplophaser.io.assembly import Assembly
    from haplophaser.io.assembly_export import export_chimeras_bed, export_chimeras_tsv

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    # Validate inputs
    if not assembly.exists():
        console.print(f"[red]Error:[/red] Assembly file not found: {assembly}")
        raise typer.Exit(code=1)

    if not marker_hits.exists():
        console.print(f"[red]Error:[/red] Marker hits file not found: {marker_hits}")
        raise typer.Exit(code=1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load assembly
        task = progress.add_task("Loading assembly...", total=None)
        if assembly.suffix == ".fai":
            asm = Assembly.from_fai(assembly)
        else:
            fai_path = Path(str(assembly) + ".fai")
            asm = Assembly.from_fai(fai_path) if fai_path.exists() else Assembly.from_fasta(assembly, load_sequences=False)
        progress.update(task, completed=True)

        # Load marker hits
        task = progress.add_task("Loading marker hits...", total=None)
        hits = load_marker_hits(marker_hits)
        progress.update(task, completed=True)

        # Get founders from hits
        all_founders: set[str] = set()
        for hit in hits:
            all_founders.update(hit.founder_alleles.keys())
        founders = sorted(all_founders)

        if populations and populations.exists():
            pops = load_populations(populations)
            founders = [p.name for p in pops if p.role == PopulationRole.FOUNDER]

        console.print(f"Analyzing chimeras for founders: {', '.join(founders)}")

        # Detect chimeras
        task = progress.add_task("Detecting chimeras...", total=None)
        detector = ChimeraDetector(
            window_size=window_size,
            min_markers_per_window=min_markers_per_window,
            switch_threshold=switch_threshold,
        )
        report = detector.detect(asm, hits, founders)
        progress.update(task, completed=True)

    # Report results
    console.print()
    console.print("[bold]Chimera Detection Results:[/bold]")
    console.print(f"  Contigs analyzed: {report.contigs_analyzed:,}")
    console.print(f"  Chimeric contigs: {report.chimeric_contigs:,} ({report.chimera_rate:.1%})")
    console.print(f"  Total switches: {report.total_switches:,}")
    console.print()

    # Export
    tsv_path = export_chimeras_tsv(report, output)
    console.print(f"[green]Written:[/green] {tsv_path}")

    bed_path = export_chimeras_bed(report, str(output).replace(".tsv", ".bed"))
    console.print(f"[green]Written:[/green] {bed_path}")

    raise typer.Exit(code=0)


@app.command("assign-subgenomes")
def assign_subgenomes_cmd(
    assembly: Annotated[
        Path,
        typer.Option("--assembly", "-a", help="Assembly FASTA or FAI file."),
    ],
    marker_hits: Annotated[
        Path | None,
        typer.Option("--marker-hits", "-h", help="Marker hits TSV from map-markers."),
    ] = None,
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output subgenome assignments TSV."),
    ] = Path("subgenome_assignments.tsv"),
    subgenomes: Annotated[
        str,
        typer.Option("--subgenomes", "-s", help="Comma-separated subgenome names (e.g., 'A,B')."),
    ] = "A,B",
    method: Annotated[
        str,
        typer.Option("--method", "-m", help="Assignment method: markers, orthologs, combined."),
    ] = "markers",
    orthofinder_dir: Annotated[
        Path | None,
        typer.Option("--orthofinder-dir", help="OrthoFinder Results directory."),
    ] = None,
    gene_mapping: Annotated[
        Path | None,
        typer.Option("--gene-mapping", help="Gene-to-contig mapping (GFF or TSV)."),
    ] = None,
    subgenome_representatives: Annotated[
        str | None,
        typer.Option("--subgenome-reps", help="Subgenome:species mappings (e.g., 'A:Triticum_urartu,B:Aegilops_speltoides')."),
    ] = None,
    min_markers: Annotated[
        int,
        typer.Option("--min-markers", help="Minimum markers for assignment."),
    ] = 5,
    min_proportion: Annotated[
        float,
        typer.Option("--min-proportion", help="Minimum proportion for assignment."),
    ] = 0.7,
) -> None:
    """Assign contigs to subgenomes in allopolyploids.

    Uses subgenome-diagnostic markers and/or ortholog phylogenetic
    placement to assign contigs to ancestral subgenomes.

    [bold]Example:[/bold]

        phaser assign-subgenomes -a contigs.fasta -h hits.tsv -s A,B

    [bold]With orthologs:[/bold]

        phaser assign-subgenomes -a contigs.fasta --method combined \\
            --orthofinder-dir OrthoFinder/Results/ \\
            --gene-mapping genes.gff -s A,B
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.assembly.mapping import load_marker_hits
    from haplophaser.assembly.subgenome import SubgenomeAssigner
    from haplophaser.io.assembly import Assembly
    from haplophaser.io.assembly_export import export_subgenome_assignments_tsv

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    # Validate inputs
    if not assembly.exists():
        console.print(f"[red]Error:[/red] Assembly file not found: {assembly}")
        raise typer.Exit(code=1)

    # Parse subgenomes
    subgenome_list = [s.strip() for s in subgenomes.split(",")]
    console.print(f"Subgenomes: {', '.join(subgenome_list)}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load assembly
        task = progress.add_task("Loading assembly...", total=None)
        if assembly.suffix == ".fai":
            asm = Assembly.from_fai(assembly)
        else:
            fai_path = Path(str(assembly) + ".fai")
            asm = Assembly.from_fai(fai_path) if fai_path.exists() else Assembly.from_fasta(assembly, load_sequences=False)
        progress.update(task, completed=True)

        # Load marker hits
        hits = None
        if marker_hits and marker_hits.exists():
            task = progress.add_task("Loading marker hits...", total=None)
            hits = load_marker_hits(marker_hits)
            progress.update(task, completed=True)
            console.print(f"Loaded {len(hits):,} marker hits")

        # Load OrthoFinder results
        ortho_results = None
        gene_to_contig = None
        if orthofinder_dir and orthofinder_dir.exists():
            from haplophaser.io.orthofinder import OrthoFinderResults, load_gene_to_contig_mapping

            task = progress.add_task("Loading OrthoFinder results...", total=None)
            ortho_results = OrthoFinderResults.from_directory(orthofinder_dir)
            progress.update(task, completed=True)

            if gene_mapping and gene_mapping.exists():
                task = progress.add_task("Loading gene mapping...", total=None)
                gene_to_contig = load_gene_to_contig_mapping(gene_mapping)
                progress.update(task, completed=True)

            # Set subgenome representatives
            if subgenome_representatives:
                reps = {}
                for pair in subgenome_representatives.split(","):
                    sg, species = pair.split(":")
                    reps[sg.strip()] = species.strip()
                ortho_results.set_subgenome_representatives(reps)

        # Assign subgenomes
        task = progress.add_task("Assigning subgenomes...", total=None)
        assigner = SubgenomeAssigner(
            subgenomes=subgenome_list,
            method=method,
            min_markers=min_markers,
            min_proportion=min_proportion,
        )
        assignments = assigner.assign(
            asm,
            marker_hits=hits,
            orthologs=ortho_results,
            gene_to_contig=gene_to_contig,
        )
        progress.update(task, completed=True)

    # Report results
    console.print()
    console.print("[bold]Subgenome Assignment Results:[/bold]")

    summary = assignments.summary()
    console.print(f"  Assigned: {summary['n_assigned']:,} / {summary['n_contigs']:,} ({summary['assignment_rate']:.1%})")
    console.print()

    from rich.table import Table as RichTable

    sg_table = RichTable(title="Per-Subgenome Breakdown")
    sg_table.add_column("Subgenome", style="cyan")
    sg_table.add_column("Contigs", justify="right")
    sg_table.add_column("Total bp", justify="right")
    sg_table.add_column("Mean confidence", justify="right")

    for sg, stats in sorted(summary['by_subgenome'].items()):
        sg_table.add_row(
            sg,
            f"{stats['n_contigs']:,}",
            f"{stats['total_bp']:,}",
            f"{stats['mean_confidence']:.3f}",
        )

    console.print(sg_table)
    console.print()

    # Export
    output_path = export_subgenome_assignments_tsv(assignments, output)
    console.print(f"[green]Written:[/green] {output_path}")

    raise typer.Exit(code=0)


# ============================================================================
# Scaffolding commands
# ============================================================================


@app.command("map-to-genetic")
def map_to_genetic_cmd(
    assembly: Annotated[
        Path,
        typer.Option("--assembly", "-a", help="Assembly FASTA or FAI file."),
    ],
    marker_hits: Annotated[
        Path,
        typer.Option("--marker-hits", "-h", help="Marker hits TSV from map-markers."),
    ],
    genetic_map: Annotated[
        Path,
        typer.Option("--genetic-map", "-g", help="Genetic map file (PLINK, MSTmap, or TSV)."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output contig placements TSV."),
    ] = Path("contig_genetic_positions.tsv"),
    min_markers: Annotated[
        int,
        typer.Option("--min-markers", help="Minimum markers for placement."),
    ] = 3,
    max_conflict_rate: Annotated[
        float,
        typer.Option("--max-conflict-rate", help="Maximum marker conflict rate."),
    ] = 0.1,
    map_format: Annotated[
        str | None,
        typer.Option("--format", help="Genetic map format: plink, mstmap, custom."),
    ] = None,
) -> None:
    """Map contigs to genetic map positions.

    Creates contig-to-genetic-map relationships based on marker hits.
    Output includes genetic positions and orientations for each contig.

    [bold]Example:[/bold]

        phaser map-to-genetic -a contigs.fasta -h hits.tsv -g map.map -o placements.tsv
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.assembly.mapping import load_marker_hits
    from haplophaser.core.genetic_map import GeneticMap
    from haplophaser.io.assembly import Assembly
    from haplophaser.scaffold.contig_markers import ContigMarkerMap

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    # Validate inputs
    for path, name in [(assembly, "Assembly"), (marker_hits, "Marker hits"), (genetic_map, "Genetic map")]:
        if not path.exists():
            console.print(f"[red]Error:[/red] {name} file not found: {path}")
            raise typer.Exit(code=1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load assembly
        task = progress.add_task("Loading assembly...", total=None)
        if assembly.suffix == ".fai":
            asm = Assembly.from_fai(assembly)
        else:
            fai_path = Path(str(assembly) + ".fai")
            asm = Assembly.from_fai(fai_path) if fai_path.exists() else Assembly.from_fasta(assembly, load_sequences=False)
        progress.update(task, completed=True)
        console.print(f"Loaded assembly: {asm.n_contigs:,} contigs")

        # Load genetic map
        task = progress.add_task("Loading genetic map...", total=None)
        gmap = GeneticMap.from_file(genetic_map, format=map_format)
        progress.update(task, completed=True)
        console.print(f"Loaded genetic map: {gmap.n_chromosomes} chromosomes")

        # Load marker hits
        task = progress.add_task("Loading marker hits...", total=None)
        hits = load_marker_hits(marker_hits)
        progress.update(task, completed=True)
        console.print(f"Loaded {len(hits):,} marker hits")

        # Build contig-marker map
        task = progress.add_task("Building contig-marker relationships...", total=None)
        contig_map = ContigMarkerMap(
            assembly=asm,
            marker_hits=hits,
            genetic_map=gmap,
            min_markers=min_markers,
            max_conflict_rate=max_conflict_rate,
        )
        progress.update(task, completed=True)

    # Report results
    summary = contig_map.summary()
    console.print()
    console.print("[bold]Mapping Results:[/bold]")
    console.print(f"  Placed contigs: {summary['n_placed']:,} / {summary['n_contigs']:,} ({summary['placement_rate']:.1%})")
    console.print(f"  Placed bp: {summary['placed_bp']:,} / {summary['total_bp']:,} ({summary['placed_bp_rate']:.1%})")
    console.print(f"  Conflicting: {summary['n_conflicting']:,}")
    console.print(f"  Chromosomes: {summary['n_chromosomes']}")
    console.print()

    # Export placements
    with open(output, "w") as f:
        columns = ["contig", "chromosome", "genetic_start", "genetic_end", "orientation", "n_markers", "confidence", "has_conflicts"]
        f.write("\t".join(columns) + "\n")

        for contig_name, placement in sorted(contig_map.all_placements().items()):
            row = [
                contig_name,
                placement.chromosome or "",
                f"{placement.genetic_start:.3f}" if placement.genetic_start is not None else "",
                f"{placement.genetic_end:.3f}" if placement.genetic_end is not None else "",
                placement.orientation or "?",
                str(placement.n_markers),
                f"{placement.confidence:.3f}",
                str(placement.has_conflicts).lower(),
            ]
            f.write("\t".join(row) + "\n")

    console.print(f"[green]Written:[/green] {output}")
    raise typer.Exit(code=0)


@app.command("scaffold")
def scaffold_cmd(
    assembly: Annotated[
        Path,
        typer.Option("--assembly", "-a", help="Assembly FASTA or FAI file."),
    ],
    contig_positions: Annotated[
        Path,
        typer.Option("--contig-positions", "-c", help="Contig positions TSV from map-to-genetic."),
    ],
    output_prefix: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file prefix."),
    ] = Path("scaffolded"),
    painting: Annotated[
        Path | None,
        typer.Option("--painting", "-p", help="Assembly painting TSV for haplotype continuity."),
    ] = None,
    genetic_map: Annotated[
        Path | None,
        typer.Option("--genetic-map", "-g", help="Genetic map for gap estimation."),
    ] = None,
    marker_hits: Annotated[
        Path | None,
        typer.Option("--marker-hits", "-h", help="Marker hits TSV for contig map."),
    ] = None,
    method: Annotated[
        str,
        typer.Option("--method", help="Ordering method: genetic_map, haplotype, combined."),
    ] = "combined",
    min_markers: Annotated[
        int,
        typer.Option("--min-markers", help="Minimum markers for placement."),
    ] = 3,
    min_confidence: Annotated[
        float,
        typer.Option("--min-confidence", help="Minimum confidence for placement."),
    ] = 0.3,
    gap_method: Annotated[
        str,
        typer.Option("--gap-method", help="Gap estimation: genetic_distance, fixed, local_rate."),
    ] = "genetic_distance",
    fixed_gap: Annotated[
        int,
        typer.Option("--fixed-gap", help="Fixed gap size (bp) when genetic distance unavailable."),
    ] = 100,
) -> None:
    """Order and orient contigs into pseudomolecules.

    Orders contigs based on genetic map positions and optionally refines
    using haplotype continuity from assembly painting.

    [bold]Example:[/bold]

        phaser scaffold -a contigs.fasta -c placements.tsv -o scaffolded

    [bold]With haplotype continuity:[/bold]

        phaser scaffold -a contigs.fasta -c placements.tsv -p painted.tsv --method combined

    [bold]Output files:[/bold]

        - scaffolded.agp: AGP format scaffold structure
        - scaffolded_ordering.tsv: Detailed ordering information
        - scaffolded_validation.txt: QC report
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.core.genetic_map import GeneticMap
    from haplophaser.io.agp import AGPWriter, export_ordering_tsv
    from haplophaser.io.assembly import Assembly
    from haplophaser.scaffold.gaps import GapEstimator
    from haplophaser.scaffold.ordering import ScaffoldOrderer
    from haplophaser.scaffold.validation import ScaffoldValidator

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    # Validate inputs
    if not assembly.exists():
        console.print(f"[red]Error:[/red] Assembly file not found: {assembly}")
        raise typer.Exit(code=1)

    if not contig_positions.exists():
        console.print(f"[red]Error:[/red] Contig positions file not found: {contig_positions}")
        raise typer.Exit(code=1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load assembly
        task = progress.add_task("Loading assembly...", total=None)
        if assembly.suffix == ".fai":
            asm = Assembly.from_fai(assembly)
        else:
            fai_path = Path(str(assembly) + ".fai")
            asm = Assembly.from_fai(fai_path) if fai_path.exists() else Assembly.from_fasta(assembly, load_sequences=False)
        progress.update(task, completed=True)
        console.print(f"Loaded assembly: {asm.n_contigs:,} contigs")

        # Load contig positions
        task = progress.add_task("Loading contig positions...", total=None)
        placements = _load_contig_placements(contig_positions, asm)
        progress.update(task, completed=True)

        # Build mock contig map from placements
        contig_map = _build_contig_map_from_placements(asm, placements, genetic_map, marker_hits)

        # Load painting if provided
        painting_result = None
        if painting and painting.exists():
            task = progress.add_task("Loading painting...", total=None)
            painting_result = _load_painting(painting, asm)
            progress.update(task, completed=True)
            console.print(f"Loaded painting: {painting_result.n_assigned} assigned contigs")

        # Load genetic map if provided
        gmap = None
        if genetic_map and genetic_map.exists():
            task = progress.add_task("Loading genetic map...", total=None)
            gmap = GeneticMap.from_file(genetic_map)
            progress.update(task, completed=True)

        # Order contigs
        task = progress.add_task("Ordering contigs...", total=None)
        orderer = ScaffoldOrderer(
            method=method,
            min_markers=min_markers,
            min_confidence=min_confidence,
            default_gap=fixed_gap,
        )
        orderings = orderer.order(asm, contig_map, painting_result)
        progress.update(task, completed=True)

        # Estimate gaps
        if gap_method != "fixed" and gmap:
            task = progress.add_task("Estimating gap sizes...", total=None)
            gap_estimator = GapEstimator(method=gap_method, fixed_gap=fixed_gap)
            for chrom, ordering in orderings.items():
                gaps = gap_estimator.estimate(ordering, gmap, contig_map)
                # Update ordering with gap estimates
                for oc in ordering.ordered_contigs[1:]:
                    key = (ordering.ordered_contigs[ordering.ordered_contigs.index(oc) - 1].contig, oc.contig)
                    if key in gaps:
                        oc.gap_before = gaps[key].estimated_size
            progress.update(task, completed=True)

        # Validate
        task = progress.add_task("Validating ordering...", total=None)
        validator = ScaffoldValidator()
        validations = validator.validate_all(orderings, gmap, contig_map, painting_result)
        progress.update(task, completed=True)

    # Report results
    console.print()
    console.print("[bold]Scaffolding Results:[/bold]")

    total_placed = sum(o.n_contigs for o in orderings.values())
    total_placed_bp = sum(o.total_placed_bp for o in orderings.values())
    console.print(f"  Chromosomes: {len(orderings)}")
    console.print(f"  Placed contigs: {total_placed:,}")
    console.print(f"  Placed bp: {total_placed_bp:,}")
    console.print()

    # Chromosome summary table
    from rich.table import Table as RichTable

    chrom_table = RichTable(title="Per-Chromosome Summary")
    chrom_table.add_column("Chromosome", style="cyan")
    chrom_table.add_column("Contigs", justify="right")
    chrom_table.add_column("Length", justify="right")
    chrom_table.add_column("Concordance", justify="right")

    for chrom in sorted(orderings.keys()):
        ordering = orderings[chrom]
        validation = validations.get(chrom)
        concordance = f"{validation.marker_order_concordance:.3f}" if validation else "N/A"
        chrom_table.add_row(
            chrom,
            str(ordering.n_contigs),
            f"{ordering.total_length:,}",
            concordance,
        )

    console.print(chrom_table)
    console.print()

    # Write outputs
    agp_path = Path(f"{output_prefix}.agp")
    ordering_path = Path(f"{output_prefix}_ordering.tsv")
    validation_path = Path(f"{output_prefix}_validation.txt")

    writer = AGPWriter()
    writer.write(orderings, agp_path)
    console.print(f"[green]Written:[/green] {agp_path}")

    export_ordering_tsv(orderings, ordering_path)
    console.print(f"[green]Written:[/green] {ordering_path}")

    with open(validation_path, "w") as f:
        for chrom, validation in sorted(validations.items()):
            f.write(validation.summary() + "\n\n")
    console.print(f"[green]Written:[/green] {validation_path}")

    raise typer.Exit(code=0)


@app.command("validate-scaffold")
def validate_scaffold_cmd(
    agp: Annotated[
        Path,
        typer.Argument(help="AGP file to validate."),
    ],
    genetic_map: Annotated[
        Path | None,
        typer.Option("--genetic-map", "-g", help="Genetic map file."),
    ] = None,
    marker_hits: Annotated[
        Path | None,
        typer.Option("--marker-hits", "-h", help="Marker hits TSV."),
    ] = None,
    painting: Annotated[
        Path | None,
        typer.Option("--painting", "-p", help="Assembly painting TSV."),
    ] = None,
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output validation report."),
    ] = Path("validation_report.txt"),
) -> None:
    """Validate an existing scaffold AGP file.

    Checks marker order concordance and haplotype continuity.

    [bold]Example:[/bold]

        phaser validate-scaffold scaffolds.agp -g map.map -p painted.tsv
    """
    from haplophaser.core.genetic_map import GeneticMap
    from haplophaser.io.agp import AGP

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    if not agp.exists():
        console.print(f"[red]Error:[/red] AGP file not found: {agp}")
        raise typer.Exit(code=1)

    # Load AGP
    existing_agp = AGP.from_file(agp)
    console.print(f"Loaded AGP: {len(existing_agp.objects())} objects, {len(existing_agp.contig_ids())} contigs")

    # Load genetic map if provided
    gmap = None
    if genetic_map and genetic_map.exists():
        gmap = GeneticMap.from_file(genetic_map)
        console.print(f"Loaded genetic map: {gmap.n_chromosomes} chromosomes")

    console.print()
    console.print("[bold]Validation:[/bold]")

    # Basic validation
    warnings = []
    errors = []

    for obj in existing_agp.objects():
        records = existing_agp.records_for_object(obj)

        # Check for sequential part numbers
        part_nums = [r.part_number for r in records]
        if part_nums != list(range(1, len(records) + 1)):
            warnings.append(f"{obj}: Non-sequential part numbers")

        # Check for overlapping coordinates
        for i in range(len(records) - 1):
            if records[i].object_end >= records[i + 1].object_start:
                errors.append(f"{obj}: Overlapping coordinates at parts {records[i].part_number}-{records[i + 1].part_number}")

    if errors:
        console.print("[red]Errors found:[/red]")
        for e in errors:
            console.print(f"  - {e}")
    else:
        console.print("[green]No errors found[/green]")

    if warnings:
        console.print("[yellow]Warnings:[/yellow]")
        for w in warnings:
            console.print(f"  - {w}")

    # Write report
    with open(output, "w") as f:
        f.write("Scaffold Validation Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"AGP file: {agp}\n")
        f.write(f"Objects: {len(existing_agp.objects())}\n")
        f.write(f"Contigs: {len(existing_agp.contig_ids())}\n")
        f.write(f"Errors: {len(errors)}\n")
        f.write(f"Warnings: {len(warnings)}\n\n")

        if errors:
            f.write("Errors:\n")
            for e in errors:
                f.write(f"  - {e}\n")
            f.write("\n")

        if warnings:
            f.write("Warnings:\n")
            for w in warnings:
                f.write(f"  - {w}\n")

    console.print()
    console.print(f"[green]Written:[/green] {output}")
    raise typer.Exit(code=0)


@app.command("compare-scaffolds")
def compare_scaffolds_cmd(
    agp1: Annotated[
        Path,
        typer.Argument(help="First AGP file."),
    ],
    agp2: Annotated[
        Path,
        typer.Argument(help="Second AGP file."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output comparison TSV."),
    ] = Path("comparison.tsv"),
) -> None:
    """Compare two scaffold AGP files.

    Compares contig ordering between two AGP files.

    [bold]Example:[/bold]

        phaser compare-scaffolds method1.agp method2.agp -o comparison.tsv
    """
    from haplophaser.io.agp import AGP, compare_agp

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    for path, name in [(agp1, "AGP1"), (agp2, "AGP2")]:
        if not path.exists():
            console.print(f"[red]Error:[/red] {name} file not found: {path}")
            raise typer.Exit(code=1)

    # Load AGPs
    existing_agp1 = AGP.from_file(agp1)
    existing_agp2 = AGP.from_file(agp2)

    console.print(f"AGP1: {len(existing_agp1.objects())} objects, {len(existing_agp1.contig_ids())} contigs")
    console.print(f"AGP2: {len(existing_agp2.objects())} objects, {len(existing_agp2.contig_ids())} contigs")
    console.print()

    # Compare
    comparison = compare_agp(existing_agp1, existing_agp2)

    console.print("[bold]Comparison Results:[/bold]")
    console.print(f"  Shared objects: {len(comparison['shared_objects'])}")
    console.print(f"  Only in AGP1: {len(comparison['only_in_1'])}")
    console.print(f"  Only in AGP2: {len(comparison['only_in_2'])}")
    console.print(f"  Mean order concordance: {comparison['mean_concordance']:.3f}")
    console.print()

    # Write comparison
    with open(output, "w") as f:
        f.write("object\tconcordance\tstatus\n")
        for obj in comparison['shared_objects']:
            conc = comparison['order_concordance'].get(obj)
            conc_str = f"{conc:.3f}" if conc is not None else "N/A"
            f.write(f"{obj}\t{conc_str}\tshared\n")
        for obj in comparison['only_in_1']:
            f.write(f"{obj}\tN/A\tonly_in_agp1\n")
        for obj in comparison['only_in_2']:
            f.write(f"{obj}\tN/A\tonly_in_agp2\n")

    console.print(f"[green]Written:[/green] {output}")
    raise typer.Exit(code=0)


# ============================================================================
# Subgenome commands
# ============================================================================


@app.command("subgenome-markers")
def subgenome_markers(
    vcf: Annotated[
        Path,
        typer.Argument(help="VCF file with variants."),
    ],
    reference_assignments: Annotated[
        Path,
        typer.Option("--reference-assignments", "-r", help="BED file with known subgenome assignments."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output markers file."),
    ] = Path("subgenome_markers.tsv"),
    config: Annotated[
        str | None,
        typer.Option("--config", "-c", help="Species config: maize, wheat, brassica."),
    ] = "maize",
    min_divergence: Annotated[
        float,
        typer.Option("--min-divergence", help="Minimum sequence divergence for marker."),
    ] = 0.05,
    synteny_blocks: Annotated[
        Path | None,
        typer.Option("--synteny", help="Synteny blocks file for context."),
    ] = None,
) -> None:
    """Find subgenome-diagnostic markers from VCF.

    Identifies markers that distinguish between subgenomes based on
    fixed differences in homeologous regions.

    [bold]Example:[/bold]

        phaser subgenome-markers variants.vcf.gz -r B73_subgenomes.bed -o markers.tsv
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.subgenome.markers import SubgenomeMarkerFinder, write_markers
    from haplophaser.subgenome.models import SubgenomeConfig

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    # Validate inputs
    if not vcf.exists():
        console.print(f"[red]Error:[/red] VCF file not found: {vcf}")
        raise typer.Exit(code=1)

    if not reference_assignments.exists():
        console.print(f"[red]Error:[/red] Reference assignments not found: {reference_assignments}")
        raise typer.Exit(code=1)

    # Get config
    if config == "maize":
        sg_config = SubgenomeConfig.maize_default()
    elif config == "wheat":
        sg_config = SubgenomeConfig.wheat_default()
    elif config == "brassica":
        sg_config = SubgenomeConfig.brassica_default()
    else:
        console.print(f"[red]Error:[/red] Unknown config: {config}")
        raise typer.Exit(code=1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Finding subgenome markers...", total=None)

        finder = SubgenomeMarkerFinder(
            config=sg_config,
            min_divergence=min_divergence,
        )

        markers = finder.from_vcf(
            vcf=vcf,
            reference_assignments=reference_assignments,
            synteny_blocks=synteny_blocks,
        )

        progress.update(task, completed=True)

    console.print(f"Found {len(markers)} subgenome-diagnostic markers")

    # Write output
    write_markers(markers, output)
    console.print(f"[green]Written:[/green] {output}")

    raise typer.Exit(code=0)


@app.command("subgenome-assign")
def subgenome_assign(
    method: Annotated[
        str,
        typer.Argument(help="Assignment method: synteny, orthologs, or combined."),
    ],
    output_prefix: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file prefix."),
    ] = Path("subgenome"),
    assembly: Annotated[
        Path | None,
        typer.Option("--assembly", "-a", help="Query assembly FASTA."),
    ] = None,
    synteny: Annotated[
        Path | None,
        typer.Option("--synteny", "-s", help="Synteny blocks file (PAF, TSV, etc.)."),
    ] = None,
    reference_assignments: Annotated[
        Path | None,
        typer.Option("--reference-assignments", "-r", help="Known subgenome assignments BED."),
    ] = None,
    genes: Annotated[
        Path | None,
        typer.Option("--genes", "-g", help="Gene annotations GFF3."),
    ] = None,
    proteins: Annotated[
        Path | None,
        typer.Option("--proteins", "-p", help="Protein sequences FASTA."),
    ] = None,
    orthofinder_dir: Annotated[
        Path | None,
        typer.Option("--orthofinder-dir", help="OrthoFinder results directory."),
    ] = None,
    outgroup: Annotated[
        str | None,
        typer.Option("--outgroup", help="Outgroup species name."),
    ] = None,
    config: Annotated[
        str,
        typer.Option("--config", "-c", help="Species config: maize, wheat, brassica."),
    ] = "maize",
    min_block_size: Annotated[
        int,
        typer.Option("--min-block-size", help="Minimum synteny block size."),
    ] = 50_000,
) -> None:
    """Assign genomic regions to subgenomes.

    Uses synteny and/or ortholog evidence to assign regions to subgenomes.

    [bold]Methods:[/bold]

        - synteny: Use synteny blocks to transfer known assignments
        - orthologs: Use gene phylogenetic placement
        - combined: Integrate both evidence sources

    [bold]Examples:[/bold]

        phaser subgenome-assign synteny -s synteny.paf -r B73_subgenomes.bed

        phaser subgenome-assign orthologs -g genes.gff3 --orthofinder-dir OrthoFinder/

        phaser subgenome-assign combined -s synteny.paf -r B73_subgenomes.bed \\
            -g genes.gff3 --orthofinder-dir OrthoFinder/
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.subgenome.models import SubgenomeConfig

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    # Get config
    if config == "maize":
        sg_config = SubgenomeConfig.maize_default()
    elif config == "wheat":
        sg_config = SubgenomeConfig.wheat_default()
    elif config == "brassica":
        sg_config = SubgenomeConfig.brassica_default()
    else:
        console.print(f"[red]Error:[/red] Unknown config: {config}")
        raise typer.Exit(code=1)

    # Validate method-specific requirements
    if method == "synteny":
        if not synteny or not reference_assignments:
            console.print("[red]Error:[/red] Synteny method requires --synteny and --reference-assignments")
            raise typer.Exit(code=1)
    elif method == "orthologs":
        if not genes:
            console.print("[red]Error:[/red] Orthologs method requires --genes")
            raise typer.Exit(code=1)
    elif method == "combined" and not genes:
        console.print("[red]Error:[/red] Combined method requires --genes")
        raise typer.Exit(code=1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        result = None

        if method in ("synteny", "combined"):
            task = progress.add_task("Assigning by synteny...", total=None)

            from haplophaser.subgenome.synteny import SyntenySubgenomeAssigner

            assigner = SyntenySubgenomeAssigner(
                config=sg_config,
                min_block_size=min_block_size,
            )

            synteny_result = assigner.assign(
                synteny_blocks=synteny,
                reference_assignments=reference_assignments,
                query_name=assembly.stem if assembly else "query",
            )
            progress.update(task, completed=True)

            console.print(f"Synteny: {len(synteny_result.assignments)} assignments")
            result = synteny_result

        if method in ("orthologs", "combined"):
            task = progress.add_task("Assigning by orthologs...", total=None)

            from haplophaser.subgenome.orthologs import OrthologSubgenomeAssigner

            assigner = OrthologSubgenomeAssigner(
                config=sg_config,
            )

            ortholog_result = assigner.assign(
                query_genes=genes,
                query_proteins=proteins,
                orthofinder_dir=orthofinder_dir,
                outgroup=outgroup,
                reference_assignments=reference_assignments,
            )
            progress.update(task, completed=True)

            console.print(f"Orthologs: {len(ortholog_result.assignments)} assignments")

            if method == "orthologs":
                result = ortholog_result

        if method == "combined" and result:
            task = progress.add_task("Integrating evidence...", total=None)

            from haplophaser.subgenome.integrate import SubgenomeIntegrator

            integrator = SubgenomeIntegrator()
            result = integrator.integrate(
                synteny_assignments=synteny_result,
                ortholog_assignments=ortholog_result,
                config=sg_config,
            )
            progress.update(task, completed=True)

            console.print(f"Combined: {len(result.assignments)} assignments")

    # Export results
    if result:
        bed_path = Path(f"{output_prefix}_assignments.bed")
        result.to_bed(bed_path)
        console.print(f"[green]Written:[/green] {bed_path}")

        tsv_path = Path(f"{output_prefix}_assignments.tsv")
        df = result.to_dataframe()
        df.to_csv(tsv_path, sep="\t", index=False)
        console.print(f"[green]Written:[/green] {tsv_path}")

        # Summary
        console.print()
        console.print("[bold]Summary:[/bold]")
        summary = result.summary()
        for sg, sg_data in summary.get("by_subgenome", {}).items():
            bp_mb = sg_data["total_bp"] / 1_000_000
            console.print(f"  {sg}: {sg_data['n_regions']} regions, {bp_mb:.1f} Mb")

    raise typer.Exit(code=0)


@app.command("subgenome-fractionation")
def subgenome_fractionation(
    genes: Annotated[
        Path,
        typer.Argument(help="Gene annotations GFF3 file."),
    ],
    assignments: Annotated[
        Path,
        typer.Option("--assignments", "-a", help="Subgenome assignments BED file."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output report file."),
    ] = Path("fractionation_report.tsv"),
    homeolog_pairs: Annotated[
        Path | None,
        typer.Option("--homeologs", "-H", help="Homeolog pairs TSV file."),
    ] = None,
    config: Annotated[
        str,
        typer.Option("--config", "-c", help="Species config: maize, wheat, brassica."),
    ] = "maize",
) -> None:
    """Analyze fractionation patterns between subgenomes.

    Examines biased gene loss following whole-genome duplication.

    [bold]Example:[/bold]

        phaser subgenome-fractionation genes.gff3 -a subgenomes.bed -o fractionation.tsv
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.subgenome.fractionation import FractionationAnalyzer, write_fractionation_report
    from haplophaser.subgenome.models import SubgenomeConfig

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    # Validate inputs
    if not genes.exists():
        console.print(f"[red]Error:[/red] Genes file not found: {genes}")
        raise typer.Exit(code=1)

    if not assignments.exists():
        console.print(f"[red]Error:[/red] Assignments file not found: {assignments}")
        raise typer.Exit(code=1)

    # Get config
    if config == "maize":
        sg_config = SubgenomeConfig.maize_default()
    elif config == "wheat":
        sg_config = SubgenomeConfig.wheat_default()
    elif config == "brassica":
        sg_config = SubgenomeConfig.brassica_default()
    else:
        console.print(f"[red]Error:[/red] Unknown config: {config}")
        raise typer.Exit(code=1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing fractionation...", total=None)

        analyzer = FractionationAnalyzer(sg_config)
        report = analyzer.analyze(
            genes=genes,
            subgenome_assignments=assignments,
            homeolog_pairs=homeolog_pairs,
        )

        progress.update(task, completed=True)

    # Display summary
    console.print()
    console.print(report.summary())

    # Write report
    write_fractionation_report(report, output)
    console.print()
    console.print(f"[green]Written:[/green] {output}")

    raise typer.Exit(code=0)


@app.command("subgenome-homeologs")
def subgenome_homeologs(
    genes: Annotated[
        Path,
        typer.Argument(help="Gene annotations GFF3 file."),
    ],
    assignments: Annotated[
        Path,
        typer.Option("--assignments", "-a", help="Subgenome assignments BED file."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output homeolog pairs file."),
    ] = Path("homeolog_pairs.tsv"),
    synteny_blocks: Annotated[
        Path | None,
        typer.Option("--synteny", "-s", help="Synteny blocks file."),
    ] = None,
    proteins: Annotated[
        Path | None,
        typer.Option("--proteins", "-p", help="Protein sequences for Ks calculation."),
    ] = None,
    method: Annotated[
        str,
        typer.Option("--method", "-m", help="Detection method: synteny, sequence, combined."),
    ] = "synteny",
    max_ks: Annotated[
        float,
        typer.Option("--max-ks", help="Maximum Ks for homeologs."),
    ] = 1.0,
    config: Annotated[
        str,
        typer.Option("--config", "-c", help="Species config: maize, wheat, brassica."),
    ] = "maize",
) -> None:
    """Find homeologous gene pairs between subgenomes.

    Identifies gene pairs derived from the whole-genome duplication.

    [bold]Example:[/bold]

        phaser subgenome-homeologs genes.gff3 -a subgenomes.bed -s synteny.tsv -o homeologs.tsv
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.subgenome.homeologs import HomeologFinder, write_homeolog_pairs
    from haplophaser.subgenome.models import SubgenomeConfig

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print()

    # Validate inputs
    if not genes.exists():
        console.print(f"[red]Error:[/red] Genes file not found: {genes}")
        raise typer.Exit(code=1)

    if not assignments.exists():
        console.print(f"[red]Error:[/red] Assignments file not found: {assignments}")
        raise typer.Exit(code=1)

    # Get config
    if config == "maize":
        sg_config = SubgenomeConfig.maize_default()
    elif config == "wheat":
        sg_config = SubgenomeConfig.wheat_default()
    elif config == "brassica":
        sg_config = SubgenomeConfig.brassica_default()
    else:
        console.print(f"[red]Error:[/red] Unknown config: {config}")
        raise typer.Exit(code=1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Finding homeolog pairs...", total=None)

        finder = HomeologFinder(
            config=sg_config,
            method=method,
            max_ks=max_ks,
        )

        result = finder.find(
            genes=genes,
            subgenome_assignments=assignments,
            synteny_blocks=synteny_blocks,
            proteins=proteins,
        )

        progress.update(task, completed=True)

    # Display summary
    console.print()
    console.print(f"Found {result.n_pairs} homeolog pairs")
    console.print(f"Median Ks: {result.median_ks:.3f}")
    console.print(f"Mean identity: {result.mean_identity:.3f}")

    # Write output
    write_homeolog_pairs(result, output)
    console.print()
    console.print(f"[green]Written:[/green] {output}")

    raise typer.Exit(code=0)


@app.command("subgenome-pipeline")
def subgenome_pipeline(
    assembly: Annotated[
        Path,
        typer.Argument(help="Query assembly FASTA."),
    ],
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", help="Output directory."),
    ] = Path("subgenome_analysis"),
    genes: Annotated[
        Path | None,
        typer.Option("--genes", "-g", help="Gene annotations GFF3."),
    ] = None,
    proteins: Annotated[
        Path | None,
        typer.Option("--proteins", "-p", help="Protein sequences FASTA."),
    ] = None,
    reference: Annotated[
        Path | None,
        typer.Option("--reference", help="Reference assembly FASTA."),
    ] = None,
    reference_genes: Annotated[
        Path | None,
        typer.Option("--reference-genes", help="Reference gene annotations."),
    ] = None,
    reference_assignments: Annotated[
        Path | None,
        typer.Option("--reference-assignments", "-r", help="Known subgenome assignments."),
    ] = None,
    orthofinder_dir: Annotated[
        Path | None,
        typer.Option("--orthofinder-dir", help="OrthoFinder results directory."),
    ] = None,
    outgroup: Annotated[
        str | None,
        typer.Option("--outgroup", help="Outgroup species name."),
    ] = None,
    config: Annotated[
        str,
        typer.Option("--config", "-c", help="Species config: maize, wheat, brassica."),
    ] = "maize",
    threads: Annotated[
        int,
        typer.Option("--threads", "-t", help="Number of threads."),
    ] = 4,
) -> None:
    """Run complete subgenome deconvolution pipeline.

    Performs synteny-based assignment, ortholog analysis, fractionation
    analysis, and homeolog detection.

    [bold]Example:[/bold]

        phaser subgenome-pipeline query.fasta -o subgenome_out/ \\
            -g genes.gff3 -p proteins.faa \\
            --reference B73.fasta --reference-assignments B73_subgenomes.bed \\
            --orthofinder-dir OrthoFinder/Results/
    """
    import subprocess

    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.subgenome.fractionation import FractionationAnalyzer, write_fractionation_report
    from haplophaser.subgenome.homeologs import HomeologFinder, write_homeolog_pairs
    from haplophaser.subgenome.integrate import SubgenomeIntegrator
    from haplophaser.subgenome.models import SubgenomeConfig
    from haplophaser.subgenome.orthologs import OrthologSubgenomeAssigner
    from haplophaser.subgenome.synteny import SyntenySubgenomeAssigner
    from haplophaser.subgenome.viz import export_subgenome_tracks

    console.print(f"[bold blue]Phaser[/bold blue] v{__version__}")
    console.print("[bold]Subgenome Deconvolution Pipeline[/bold]")
    console.print()

    # Validate inputs
    if not assembly.exists():
        console.print(f"[red]Error:[/red] Assembly not found: {assembly}")
        raise typer.Exit(code=1)

    # Get config
    if config == "maize":
        sg_config = SubgenomeConfig.maize_default()
    elif config == "wheat":
        sg_config = SubgenomeConfig.wheat_default()
    elif config == "brassica":
        sg_config = SubgenomeConfig.brassica_default()
    else:
        console.print(f"[red]Error:[/red] Unknown config: {config}")
        raise typer.Exit(code=1)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    synteny_result = None
    ortholog_result = None
    final_result = None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Step 1: Compute synteny if reference provided
        if reference and reference_assignments:
            task = progress.add_task("Computing synteny...", total=None)

            # Run minimap2
            paf_path = output_dir / "synteny.paf"

            try:
                cmd = [
                    "minimap2",
                    "-x", "asm5",
                    "-t", str(threads),
                    str(reference),
                    str(assembly),
                    "-o", str(paf_path),
                ]
                subprocess.run(cmd, check=True, capture_output=True)

                # Assign by synteny
                assigner = SyntenySubgenomeAssigner(config=sg_config)
                synteny_result = assigner.assign(
                    synteny_blocks=paf_path,
                    reference_assignments=reference_assignments,
                    query_name=assembly.stem,
                )

                progress.update(task, completed=True)
                console.print(f"  Synteny: {len(synteny_result.assignments)} assignments")

            except subprocess.CalledProcessError:
                progress.update(task, completed=True)
                console.print("[yellow]Warning:[/yellow] minimap2 failed, skipping synteny")

        # Step 2: Ortholog-based assignment
        if genes and orthofinder_dir:
            task = progress.add_task("Ortholog-based assignment...", total=None)

            assigner = OrthologSubgenomeAssigner(config=sg_config)
            ortholog_result = assigner.assign(
                query_genes=genes,
                query_proteins=proteins,
                orthofinder_dir=orthofinder_dir,
                outgroup=outgroup,
                reference_assignments=reference_assignments,
            )

            progress.update(task, completed=True)
            console.print(f"  Orthologs: {len(ortholog_result.assignments)} assignments")

        # Step 3: Integrate evidence
        if synteny_result or ortholog_result:
            task = progress.add_task("Integrating evidence...", total=None)

            integrator = SubgenomeIntegrator()
            final_result = integrator.integrate(
                synteny_assignments=synteny_result,
                ortholog_assignments=ortholog_result,
                config=sg_config,
            )

            progress.update(task, completed=True)
            console.print(f"  Combined: {len(final_result.assignments)} assignments")

            # Export assignments
            export_subgenome_tracks(final_result, output_dir, prefix="subgenome")

        # Step 4: Fractionation analysis
        if genes and final_result:
            task = progress.add_task("Analyzing fractionation...", total=None)

            assignments_bed = output_dir / "subgenome.bed"
            if assignments_bed.exists():
                analyzer = FractionationAnalyzer(sg_config)
                frac_report = analyzer.analyze(
                    genes=genes,
                    subgenome_assignments=assignments_bed,
                )

                write_fractionation_report(frac_report, output_dir / "fractionation_report.tsv")
                progress.update(task, completed=True)
                console.print(f"  Fractionation bias: {frac_report.fractionation_bias:.2f}")

        # Step 5: Homeolog detection
        if genes and final_result:
            task = progress.add_task("Finding homeologs...", total=None)

            assignments_bed = output_dir / "subgenome.bed"
            synteny_file = output_dir / "synteny.paf"

            finder = HomeologFinder(config=sg_config, method="synteny")
            homeolog_result = finder.find(
                genes=genes,
                subgenome_assignments=assignments_bed,
                synteny_blocks=synteny_file if synteny_file.exists() else None,
                proteins=proteins,
            )

            write_homeolog_pairs(homeolog_result, output_dir / "homeolog_pairs.tsv")
            progress.update(task, completed=True)
            console.print(f"  Homeologs: {homeolog_result.n_pairs} pairs")

    # Summary
    console.print()
    console.print("[bold]Pipeline complete![/bold]")
    console.print()
    console.print(f"Output directory: {output_dir}")
    console.print("Files generated:")

    for f in sorted(output_dir.glob("*")):
        console.print(f"  - {f.name}")

    raise typer.Exit(code=0)


# ============================================================================
# Helper functions for scaffolding
# ============================================================================


def _load_contig_placements(path: Path, assembly) -> dict:
    """Load contig placements from TSV file."""
    from haplophaser.scaffold.contig_markers import ContigPlacement

    placements = {}

    with open(path) as f:
        header = None
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            fields = line.split("\t")
            if header is None:
                header = {col: i for i, col in enumerate(fields)}
                continue

            contig = fields[header["contig"]]
            chromosome = fields[header.get("chromosome", 1)] or None
            genetic_start = float(fields[header["genetic_start"]]) if fields[header.get("genetic_start", 2)] else None
            genetic_end = float(fields[header["genetic_end"]]) if fields[header.get("genetic_end", 3)] else None
            orientation = fields[header.get("orientation", 4)] or None
            n_markers = int(fields[header.get("n_markers", 5)]) if header.get("n_markers") else 0
            confidence = float(fields[header.get("confidence", 6)]) if header.get("confidence") else 0.0

            placements[contig] = ContigPlacement(
                contig=contig,
                chromosome=chromosome if chromosome else None,
                genetic_start=genetic_start,
                genetic_end=genetic_end,
                orientation=orientation if orientation != "?" else None,
                n_markers=n_markers,
                confidence=confidence,
            )

    return placements


def _build_contig_map_from_placements(assembly, placements, genetic_map_path, marker_hits_path):
    """Build ContigMarkerMap from pre-computed placements."""
    from haplophaser.assembly.mapping import load_marker_hits
    from haplophaser.core.genetic_map import GeneticMap, create_uniform_map
    from haplophaser.scaffold.contig_markers import ContigMarkerMap

    # Load genetic map or create uniform map
    if genetic_map_path and genetic_map_path.exists():
        gmap = GeneticMap.from_file(genetic_map_path)
    else:
        # Create uniform map from chromosome lengths
        chrom_lengths = {}
        for _contig, placement in placements.items():
            if placement.chromosome:
                if placement.chromosome not in chrom_lengths:
                    chrom_lengths[placement.chromosome] = 0
                if placement.genetic_end:
                    chrom_lengths[placement.chromosome] = max(
                        chrom_lengths[placement.chromosome],
                        int(placement.genetic_end * 1_000_000)  # Rough bp estimate
                    )
        gmap = create_uniform_map(chrom_lengths) if chrom_lengths else GeneticMap()

    # Load marker hits if available
    hits = []
    if marker_hits_path and marker_hits_path.exists():
        hits = load_marker_hits(marker_hits_path)

    # Build contig map
    contig_map = ContigMarkerMap(
        assembly=assembly,
        marker_hits=hits,
        genetic_map=gmap,
    )

    # Override with loaded placements
    contig_map._placements = placements

    return contig_map


def _load_painting(path: Path, assembly):
    """Load assembly painting from TSV file."""
    from haplophaser.assembly.paint import AssemblyPainting, ContigPainting

    paintings = {}
    founders = set()

    with open(path) as f:
        header = None
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            fields = line.split("\t")
            if header is None:
                header = {col: i for i, col in enumerate(fields)}
                continue

            contig = fields[header["contig"]]
            assigned = fields[header.get("assigned_founder", 1)] or None
            if assigned and assigned != "unassigned":
                founders.add(assigned)

            confidence = float(fields[header.get("confidence", 2)]) if header.get("confidence") else 0.0
            n_markers = int(fields[header.get("n_markers", 3)]) if header.get("n_markers") else 0
            length = assembly.contigs[contig].length if contig in assembly.contigs else 0

            paintings[contig] = ContigPainting(
                contig=contig,
                length=length,
                n_markers=n_markers,
                assigned_founder=assigned if assigned != "unassigned" else None,
                confidence=confidence,
            )

    return AssemblyPainting(
        assembly=assembly.name,
        founders=sorted(founders),
        contigs=paintings,
    )


# ============================================================================
# Expression analysis commands
# ============================================================================


@app.command("expression-bias")
def expression_bias(
    expression: Annotated[
        Path,
        typer.Argument(
            help="Expression matrix (TPM or counts) or directory with Salmon/Kallisto output.",
            exists=True,
        ),
    ],
    homeologs: Annotated[
        Path,
        typer.Argument(
            help="Homeolog pairs TSV file.",
            exists=True,
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output", "-o",
            help="Output file path for bias results.",
        ),
    ] = Path("expression_bias.tsv"),
    metadata: Annotated[
        Path | None,
        typer.Option(
            "--metadata", "-m",
            help="Sample metadata TSV with condition, tissue columns.",
        ),
    ] = None,
    min_expr: Annotated[
        float,
        typer.Option(
            "--min-expr",
            help="Minimum expression (TPM) for 'expressed'.",
        ),
    ] = 1.0,
    log2_threshold: Annotated[
        float,
        typer.Option(
            "--log2-threshold",
            help="|log2 ratio| threshold for significant bias.",
        ),
    ] = 1.0,
    test_method: Annotated[
        str,
        typer.Option(
            "--test-method",
            help="Statistical test: paired_t, wilcoxon, bootstrap.",
        ),
    ] = "paired_t",
) -> None:
    """Analyze expression bias between homeolog pairs.

    Calculates log2 ratios and statistical significance of expression
    bias for homeologous gene pairs.
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.expression.bias import calculate_expression_bias, write_expression_bias
    from haplophaser.expression.homeolog_expression import extract_homeolog_expression
    from haplophaser.io.expression import (
        load_expression_matrix,
        load_multiple_samples,
        parse_sample_metadata,
    )

    console.print("[bold]Expression Bias Analysis[/bold]")
    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load expression data
        task = progress.add_task("Loading expression data...", total=None)

        sample_meta = None
        if metadata and metadata.exists():
            sample_meta = parse_sample_metadata(metadata)

        if expression.is_dir():
            # Multiple Salmon/Kallisto directories
            sample_dirs = [d for d in expression.iterdir() if d.is_dir()]
            expr_matrix = load_multiple_samples(sample_dirs, sample_metadata=sample_meta)
        else:
            expr_matrix = load_expression_matrix(expression, sample_metadata=sample_meta)

        progress.update(task, completed=True)
        console.print(f"  Loaded {expr_matrix.n_genes} genes, {expr_matrix.n_samples} samples")

        # Extract homeolog expression
        task = progress.add_task("Extracting homeolog expression...", total=None)
        homeolog_expr = extract_homeolog_expression(expr_matrix, homeologs)
        progress.update(task, completed=True)
        console.print(f"  Found {homeolog_expr.n_pairs} homeolog pairs with expression")

        # Calculate bias
        task = progress.add_task("Calculating expression bias...", total=None)
        bias_result = calculate_expression_bias(
            homeolog_expr,
            min_expr=min_expr,
            log2_threshold=log2_threshold,
            test_method=test_method,
        )
        progress.update(task, completed=True)

    # Write results
    write_expression_bias(bias_result, output)

    # Summary
    console.print()
    summary = bias_result.summary()
    console.print("[bold]Summary:[/bold]")
    console.print(f"  Pairs analyzed: {summary['n_pairs']}")
    console.print(f"  Significantly biased: {summary['n_significant']} ({summary['n_significant']/max(summary['n_pairs'],1)*100:.1f}%)")
    console.print(f"  Subgenome 1 dominant: {summary['n_sg1_dominant']}")
    console.print(f"  Subgenome 2 dominant: {summary['n_sg2_dominant']}")
    console.print(f"  Balanced: {summary['n_balanced']}")
    console.print()
    console.print(f"Output: {output}")

    raise typer.Exit(code=0)


@app.command("expression-dominance")
def expression_dominance(
    bias_file: Annotated[
        Path,
        typer.Argument(
            help="Expression bias results from expression-bias command.",
            exists=True,
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output", "-o",
            help="Output file path for dominance results.",
        ),
    ] = Path("dominance_result.txt"),
    min_significant: Annotated[
        int,
        typer.Option(
            "--min-significant",
            help="Minimum number of significant pairs for testing.",
        ),
    ] = 10,
) -> None:
    """Test for genome-wide subgenome expression dominance.

    Determines if one subgenome has significantly more highly expressed
    copies across all homeolog pairs.
    """
    from haplophaser.expression.dominance import test_subgenome_dominance, write_dominance_result
    from haplophaser.expression.models import BiasCategory, ExpressionBias, ExpressionBiasResult

    console.print("[bold]Subgenome Dominance Analysis[/bold]")
    console.print()

    # Load bias results
    biases = []
    with open(bias_file) as f:
        header = f.readline().strip().split("\t")
        cols = {col: i for i, col in enumerate(header)}

        for line in f:
            fields = line.strip().split("\t")
            if len(fields) < 10:
                continue

            cat_str = fields[cols.get("category", 9)]
            try:
                category = BiasCategory(cat_str)
            except ValueError:
                category = BiasCategory.BALANCED

            biases.append(ExpressionBias(
                pair_id=fields[cols.get("pair_id", 0)],
                gene1_id=fields[cols.get("gene1_id", 1)],
                gene2_id=fields[cols.get("gene2_id", 2)],
                gene1_subgenome=fields[cols.get("gene1_subgenome", 3)],
                gene2_subgenome=fields[cols.get("gene2_subgenome", 4)],
                mean_gene1=float(fields[cols.get("mean_gene1", 5)]),
                mean_gene2=float(fields[cols.get("mean_gene2", 6)]),
                log2_ratio=float(fields[cols.get("log2_ratio", 7)]),
                fold_change=float(fields[cols.get("fold_change", 8)]),
                category=category,
                pvalue=float(fields[cols.get("pvalue", 10)]),
                fdr=float(fields[cols.get("fdr", 11)]),
            ))

    bias_result = ExpressionBiasResult(biases=biases)
    console.print(f"Loaded {len(biases)} bias results")

    # Test dominance
    result = test_subgenome_dominance(bias_result, min_significant=min_significant)

    # Write result
    write_dominance_result(result, output)

    # Summary
    console.print()
    console.print("[bold]Results:[/bold]")
    console.print(f"  Total biased pairs: {result.total_pairs}")
    for sg, count in result.subgenome_counts.items():
        prop = count / result.total_pairs if result.total_pairs > 0 else 0
        console.print(f"  {sg}: {count} ({prop:.1%})")
    console.print(f"  Chi-square: {result.chi2_statistic:.2f}")
    console.print(f"  P-value: {result.pvalue:.2e}")

    if result.dominant_subgenome:
        console.print(f"  [bold green]Dominant subgenome: {result.dominant_subgenome}[/bold green]")
    else:
        console.print("  [yellow]No significant dominance detected[/yellow]")

    console.print()
    console.print(f"Output: {output}")

    raise typer.Exit(code=0)


@app.command("expression-condition")
def expression_condition(
    expression: Annotated[
        Path,
        typer.Argument(
            help="Expression matrix or directory with sample outputs.",
            exists=True,
        ),
    ],
    homeologs: Annotated[
        Path,
        typer.Argument(
            help="Homeolog pairs TSV file.",
            exists=True,
        ),
    ],
    metadata: Annotated[
        Path,
        typer.Argument(
            help="Sample metadata TSV with condition column.",
            exists=True,
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir", "-o",
            help="Output directory.",
        ),
    ] = Path("condition_bias"),
    condition1: Annotated[
        str | None,
        typer.Option(
            "--condition1", "-c1",
            help="First condition for comparison (optional).",
        ),
    ] = None,
    condition2: Annotated[
        str | None,
        typer.Option(
            "--condition2", "-c2",
            help="Second condition for comparison (optional).",
        ),
    ] = None,
) -> None:
    """Analyze condition-specific expression bias.

    Compare expression bias between experimental conditions to identify
    homeolog pairs with condition-dependent bias patterns.
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.expression.bias import write_expression_bias
    from haplophaser.expression.condition_bias import (
        ConditionBiasAnalyzer,
        write_condition_comparison,
    )
    from haplophaser.io.expression import (
        load_expression_matrix,
        load_multiple_samples,
        parse_sample_metadata,
    )

    console.print("[bold]Condition-Specific Bias Analysis[/bold]")
    console.print()

    output_dir.mkdir(parents=True, exist_ok=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load data
        task = progress.add_task("Loading expression data...", total=None)
        sample_meta = parse_sample_metadata(metadata)

        if expression.is_dir():
            sample_dirs = [d for d in expression.iterdir() if d.is_dir()]
            expr_matrix = load_multiple_samples(sample_dirs, sample_metadata=sample_meta)
        else:
            expr_matrix = load_expression_matrix(expression, sample_metadata=sample_meta)

        progress.update(task, completed=True)

        conditions = expr_matrix.conditions()
        console.print(f"  Conditions found: {', '.join(conditions)}")

        # Analyze
        analyzer = ConditionBiasAnalyzer()

        if condition1 and condition2:
            # Compare two conditions
            task = progress.add_task(f"Comparing {condition1} vs {condition2}...", total=None)
            result = analyzer.compare_conditions(
                expr_matrix, homeologs, condition1, condition2
            )
            progress.update(task, completed=True)

            # Write results
            write_condition_comparison(result, output_dir / "condition_comparison.tsv")
            write_expression_bias(result.condition1_result, output_dir / f"bias_{condition1}.tsv")
            write_expression_bias(result.condition2_result, output_dir / f"bias_{condition2}.tsv")

            console.print()
            console.print("[bold]Comparison Results:[/bold]")
            console.print(f"  Pairs compared: {len(result.differential_biases)}")
            console.print(f"  Differentially biased: {result.n_differential}")
            console.print(f"  Category changed: {result.n_category_changed}")

        else:
            # Analyze all conditions
            task = progress.add_task("Analyzing all conditions...", total=None)
            results = analyzer.analyze_all_conditions(expr_matrix, homeologs)
            progress.update(task, completed=True)

            # Write results for each condition
            for cond, bias_result in results.items():
                write_expression_bias(bias_result, output_dir / f"bias_{cond}.tsv")

            console.print()
            console.print("[bold]Per-Condition Results:[/bold]")
            for cond, bias_result in results.items():
                console.print(f"  {cond}: {bias_result.n_significant} significant pairs")

    console.print()
    console.print(f"Output directory: {output_dir}")

    raise typer.Exit(code=0)


@app.command("expression-report")
def expression_report_cmd(
    expression: Annotated[
        Path,
        typer.Argument(
            help="Expression matrix or directory.",
            exists=True,
        ),
    ],
    homeologs: Annotated[
        Path,
        typer.Argument(
            help="Homeolog pairs TSV file.",
            exists=True,
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir", "-o",
            help="Output directory for reports.",
        ),
    ] = Path("expression_report"),
    metadata: Annotated[
        Path | None,
        typer.Option(
            "--metadata", "-m",
            help="Sample metadata TSV.",
        ),
    ] = None,
) -> None:
    """Generate comprehensive expression analysis report.

    Runs full expression bias analysis and generates reports in multiple
    formats (Markdown, JSON, TSV).
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from haplophaser.expression.bias import calculate_expression_bias, write_expression_bias
    from haplophaser.expression.dominance import test_subgenome_dominance
    from haplophaser.expression.homeolog_expression import extract_homeolog_expression
    from haplophaser.expression.report import generate_expression_report
    from haplophaser.io.expression import (
        load_expression_matrix,
        load_multiple_samples,
        parse_sample_metadata,
    )

    console.print("[bold]Expression Analysis Report[/bold]")
    console.print()

    output_dir.mkdir(parents=True, exist_ok=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load data
        task = progress.add_task("Loading expression data...", total=None)
        sample_meta = parse_sample_metadata(metadata) if metadata else None

        if expression.is_dir():
            sample_dirs = [d for d in expression.iterdir() if d.is_dir()]
            expr_matrix = load_multiple_samples(sample_dirs, sample_metadata=sample_meta)
        else:
            expr_matrix = load_expression_matrix(expression, sample_metadata=sample_meta)
        progress.update(task, completed=True)

        # Extract and analyze
        task = progress.add_task("Extracting homeolog expression...", total=None)
        homeolog_expr = extract_homeolog_expression(expr_matrix, homeologs)
        progress.update(task, completed=True)

        task = progress.add_task("Calculating expression bias...", total=None)
        bias_result = calculate_expression_bias(homeolog_expr)
        progress.update(task, completed=True)

        task = progress.add_task("Testing subgenome dominance...", total=None)
        dominance_result = test_subgenome_dominance(bias_result)
        progress.update(task, completed=True)

        # Generate report
        task = progress.add_task("Generating reports...", total=None)
        generate_expression_report(
            homeolog_expr=homeolog_expr,
            bias_result=bias_result,
            output_dir=output_dir,
            dominance_result=dominance_result,
            parameters={
                "expression_file": str(expression),
                "homeologs_file": str(homeologs),
                "n_samples": expr_matrix.n_samples,
            },
        )

        # Also write the detailed bias results
        write_expression_bias(bias_result, output_dir / "expression_bias.tsv")

        progress.update(task, completed=True)

    console.print()
    console.print("[bold]Analysis Complete![/bold]")
    console.print()

    summary = bias_result.summary()
    console.print(f"  Homeolog pairs: {homeolog_expr.n_pairs}")
    console.print(f"  Significantly biased: {summary['n_significant']}")

    if dominance_result.dominant_subgenome:
        console.print(f"  Dominant subgenome: {dominance_result.dominant_subgenome}")

    console.print()
    console.print(f"Output directory: {output_dir}")
    console.print("Reports generated:")
    for f in sorted(output_dir.glob("*")):
        console.print(f"  - {f.name}")

    raise typer.Exit(code=0)


# Register visualization subcommands
from haplophaser.cli.viz import viz_app

app.add_typer(viz_app, name="viz")


if __name__ == "__main__":
    app()
