"""
Visualization preparation for subgenome analysis.

Prepares data for chromoplot and other visualization tools.
Exports subgenome assignments, fractionation data, and homeolog
links in formats suitable for various plotting libraries.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from haplophaser.subgenome.fractionation import FractionationReport
from haplophaser.subgenome.models import (
    HomeologResult,
    SubgenomeAssignment,
    SubgenomeAssignmentResult,
    SubgenomeConfig,
)

logger = logging.getLogger(__name__)


def subgenome_to_bed(
    assignments: list[SubgenomeAssignment] | SubgenomeAssignmentResult,
    output: Path | str,
    include_confidence: bool = True,
) -> None:
    """Export subgenome assignments as BED for chromoplot HaplotypeTrack.

    Parameters
    ----------
    assignments : list[SubgenomeAssignment] or SubgenomeAssignmentResult
        Subgenome assignments.
    output : Path or str
        Output BED file path.
    include_confidence : bool
        Include confidence as score field.

    Examples
    --------
    >>> subgenome_to_bed(assignments, "subgenomes.bed")
    """
    output = Path(output)

    if isinstance(assignments, SubgenomeAssignmentResult):
        assignment_list = assignments.assignments
    else:
        assignment_list = assignments

    with open(output, "w") as f:
        # Write track line
        f.write('track name="Subgenomes" description="Subgenome assignments"\n')

        for a in sorted(assignment_list, key=lambda x: (x.chrom, x.start)):
            score = int(a.confidence * 1000) if include_confidence else 0
            name = a.subgenome

            # BED6 format
            f.write(f"{a.chrom}\t{a.start}\t{a.end}\t{name}\t{score}\t.\n")

    logger.info(f"Wrote {len(assignment_list)} assignments to {output}")


def subgenome_to_chromoplot(
    assignments: list[SubgenomeAssignment] | SubgenomeAssignmentResult,
    config: SubgenomeConfig | None = None,
) -> pd.DataFrame:
    """Format subgenome assignments for chromoplot.

    Parameters
    ----------
    assignments : list[SubgenomeAssignment] or SubgenomeAssignmentResult
        Subgenome assignments.
    config : SubgenomeConfig, optional
        Configuration with colors.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: chrom, start, end, sample, homolog, founder, proportion.
    """
    if isinstance(assignments, SubgenomeAssignmentResult):
        assignment_list = assignments.assignments
        if config is None:
            config = assignments.config
    else:
        assignment_list = assignments

    rows = []
    for a in assignment_list:
        rows.append({
            "chrom": a.chrom,
            "start": a.start,
            "end": a.end,
            "sample": "genome",
            "homolog": 0,
            "founder": a.subgenome,
            "proportion": a.confidence,
        })

    df = pd.DataFrame(rows)

    # Add color column if config has colors
    if config:
        color_map = {sg.name: sg.color for sg in config.subgenomes if sg.color}
        if color_map:
            df["color"] = df["founder"].map(color_map)

    return df


def fractionation_to_plot_data(
    report: FractionationReport,
) -> dict[str, pd.DataFrame]:
    """Format fractionation report for plotting.

    Parameters
    ----------
    report : FractionationReport
        Fractionation analysis results.

    Returns
    -------
    dict[str, pd.DataFrame]
        Dictionary with:
        - 'summary': Genome-wide summary
        - 'by_chromosome': Per-chromosome data
        - 'by_subgenome': Per-subgenome totals
    """
    result = {}

    # Genome-wide summary
    summary_data = {
        "metric": [
            "Total genes",
            "Retained pairs",
            "Singleton genes",
            "Fractionation bias",
            "Bias p-value",
        ],
        "value": [
            report.total_genes,
            report.retained_pairs,
            report.singleton_genes,
            report.fractionation_bias,
            report.bias_pvalue,
        ],
    }
    result["summary"] = pd.DataFrame(summary_data)

    # By subgenome
    sg_rows = []
    for sg, count in report.genes_by_subgenome.items():
        sg_rows.append({
            "subgenome": sg,
            "gene_count": count,
            "retention_rate": report.retention_by_subgenome.get(sg, 0),
        })
    result["by_subgenome"] = pd.DataFrame(sg_rows)

    # By chromosome
    chrom_rows = []
    for chrom, data in report.fractionation_by_chromosome.items():
        for sg, count in data.genes_by_subgenome.items():
            chrom_rows.append({
                "chromosome": chrom,
                "subgenome": sg,
                "gene_count": count,
                "singleton_count": data.singletons_by_subgenome.get(sg, 0),
            })
    result["by_chromosome"] = pd.DataFrame(chrom_rows)

    return result


def homeologs_to_links(
    homeologs: HomeologResult,
    output: Path | str,
    format: str = "circos",
) -> None:
    """Export homeolog pairs as links for circos/ribbon plots.

    Parameters
    ----------
    homeologs : HomeologResult
        Homeolog detection results.
    output : Path or str
        Output file path.
    format : str
        Output format: 'circos', 'tsv', or 'bed_pairs'.

    Examples
    --------
    >>> homeologs_to_links(result, "homeologs.links.txt", format="circos")
    """
    output = Path(output)

    with open(output, "w") as f:
        if format == "circos":
            # Circos links format: chr1 start1 end1 chr2 start2 end2 [options]
            for pair in homeologs.pairs:
                # Need gene positions - use placeholder if not available
                f.write(
                    f"{pair.gene1_chrom} 0 1 "
                    f"{pair.gene2_chrom} 0 1\n"
                )

        elif format == "bed_pairs":
            # BED-like format with pairs
            f.write("# gene1_chrom\tgene1_start\tgene1_end\tgene2_chrom\tgene2_start\tgene2_end\tks\n")
            for pair in homeologs.pairs:
                ks = f"{pair.ks:.4f}" if pair.ks is not None else "."
                f.write(
                    f"{pair.gene1_chrom}\t0\t1\t"
                    f"{pair.gene2_chrom}\t0\t1\t{ks}\n"
                )

        else:  # tsv
            header = [
                "gene1_id", "gene1_chrom", "gene1_subgenome",
                "gene2_id", "gene2_chrom", "gene2_subgenome",
                "ks", "synteny_support",
            ]
            f.write("\t".join(header) + "\n")

            for pair in homeologs.pairs:
                ks = f"{pair.ks:.4f}" if pair.ks is not None else "."
                row = [
                    pair.gene1_id, pair.gene1_chrom, pair.gene1_subgenome,
                    pair.gene2_id, pair.gene2_chrom, pair.gene2_subgenome,
                    ks, str(pair.synteny_support).lower(),
                ]
                f.write("\t".join(row) + "\n")

    logger.info(f"Wrote {len(homeologs.pairs)} homeolog links to {output}")


def homeologs_to_dataframe(homeologs: HomeologResult) -> pd.DataFrame:
    """Convert homeolog results to DataFrame.

    Parameters
    ----------
    homeologs : HomeologResult
        Homeolog detection results.

    Returns
    -------
    pd.DataFrame
        Homeolog pairs as DataFrame.
    """
    return homeologs.to_dataframe()


def assignments_to_summary(
    result: SubgenomeAssignmentResult,
) -> pd.DataFrame:
    """Create summary DataFrame from assignment result.

    Parameters
    ----------
    result : SubgenomeAssignmentResult
        Assignment results.

    Returns
    -------
    pd.DataFrame
        Summary statistics.
    """
    summary = result.summary()

    rows = []

    # Overall stats
    rows.append({
        "category": "overall",
        "metric": "total_regions",
        "value": summary["n_regions"],
    })
    rows.append({
        "category": "overall",
        "metric": "total_bp",
        "value": summary["total_bp"],
    })

    # Per-subgenome stats
    for sg, sg_data in summary.get("by_subgenome", {}).items():
        rows.append({
            "category": f"subgenome_{sg}",
            "metric": "n_regions",
            "value": sg_data["n_regions"],
        })
        rows.append({
            "category": f"subgenome_{sg}",
            "metric": "total_bp",
            "value": sg_data["total_bp"],
        })
        rows.append({
            "category": f"subgenome_{sg}",
            "metric": "mean_confidence",
            "value": sg_data["mean_confidence"],
        })

    # Per-evidence stats
    for evidence, count in summary.get("by_evidence", {}).items():
        rows.append({
            "category": f"evidence_{evidence}",
            "metric": "n_regions",
            "value": count,
        })

    return pd.DataFrame(rows)


def export_subgenome_tracks(
    result: SubgenomeAssignmentResult,
    output_dir: Path | str,
    prefix: str = "subgenome",
) -> dict[str, Path]:
    """Export subgenome assignments in multiple formats.

    Parameters
    ----------
    result : SubgenomeAssignmentResult
        Assignment results.
    output_dir : Path or str
        Output directory.
    prefix : str
        File name prefix.

    Returns
    -------
    dict[str, Path]
        Mapping of format to output file path.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {}

    # BED format
    bed_path = output_dir / f"{prefix}.bed"
    subgenome_to_bed(result, bed_path)
    outputs["bed"] = bed_path

    # TSV with full details
    tsv_path = output_dir / f"{prefix}_detailed.tsv"
    df = result.to_dataframe()
    df.to_csv(tsv_path, sep="\t", index=False)
    outputs["tsv"] = tsv_path

    # Summary statistics
    summary_path = output_dir / f"{prefix}_summary.tsv"
    summary_df = assignments_to_summary(result)
    summary_df.to_csv(summary_path, sep="\t", index=False)
    outputs["summary"] = summary_path

    logger.info(f"Exported subgenome tracks to {output_dir}")
    return outputs


def create_karyotype_file(
    result: SubgenomeAssignmentResult,
    output: Path | str,
    chromosome_sizes: dict[str, int] | None = None,
) -> None:
    """Create karyotype file for circos visualization.

    Parameters
    ----------
    result : SubgenomeAssignmentResult
        Assignment results.
    output : Path or str
        Output file path.
    chromosome_sizes : dict[str, int], optional
        Chromosome sizes. If not provided, inferred from assignments.
    """
    output = Path(output)

    # Get chromosome sizes
    if chromosome_sizes is None:
        chromosome_sizes = {}
        for a in result.assignments:
            current_max = chromosome_sizes.get(a.chrom, 0)
            chromosome_sizes[a.chrom] = max(current_max, a.end)

    # Get colors from config
    color_map = {}
    if result.config:
        for sg in result.config.subgenomes:
            if sg.color:
                color_map[sg.name] = sg.color

    with open(output, "w") as f:
        f.write("# Karyotype file for circos\n")
        f.write("# chr - ID LABEL START END COLOR\n")

        for chrom in sorted(chromosome_sizes.keys()):
            size = chromosome_sizes[chrom]
            # Determine dominant subgenome for coloring
            chrom_assignments = [a for a in result.assignments if a.chrom == chrom]
            if chrom_assignments:
                # Use majority subgenome
                sg_bp: dict[str, int] = {}
                for a in chrom_assignments:
                    sg_bp[a.subgenome] = sg_bp.get(a.subgenome, 0) + a.length
                dominant_sg = max(sg_bp, key=sg_bp.get) if sg_bp else ""
                color = color_map.get(dominant_sg, "grey")
            else:
                color = "grey"

            f.write(f"chr - {chrom} {chrom} 0 {size} {color}\n")

    logger.info(f"Created karyotype file: {output}")


def ks_distribution_data(homeologs: HomeologResult) -> pd.DataFrame:
    """Prepare Ks distribution data for plotting.

    Parameters
    ----------
    homeologs : HomeologResult
        Homeolog detection results.

    Returns
    -------
    pd.DataFrame
        DataFrame with Ks values and metadata.
    """
    rows = []
    for pair in homeologs.pairs:
        if pair.ks is not None:
            rows.append({
                "ks": pair.ks,
                "ka": pair.ka,
                "ka_ks_ratio": pair.ka_ks_ratio,
                "gene1_subgenome": pair.gene1_subgenome,
                "gene2_subgenome": pair.gene2_subgenome,
                "subgenome_pair": f"{pair.gene1_subgenome}-{pair.gene2_subgenome}",
                "synteny_support": pair.synteny_support,
            })

    return pd.DataFrame(rows)
