"""Extended export functions for analysis results.

This module provides export functions for HMM results, summaries,
ancestry paintings, and QC reports.
"""

from __future__ import annotations

import gzip
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from haplophaser.analysis.comparison import ClusterResult, SampleComparison, SharedBlock
    from haplophaser.analysis.painting import AncestryPainting
    from haplophaser.analysis.qc import QCReport
    from haplophaser.analysis.summary import GenomeSummary, PopulationSummary, SampleSummary
    from haplophaser.proportion.hmm import HMMResults

logger = logging.getLogger(__name__)


# =============================================================================
# HMM Result Exports
# =============================================================================


def export_hmm_posteriors(
    hmm_results: HMMResults,
    output_path: str | Path,
    compress: bool = True,
) -> Path:
    """Export HMM posterior probabilities to TSV format.

    Creates a tab-separated file with posterior probabilities for each
    position and state.

    Args:
        hmm_results: HMM inference results
        output_path: Output file path
        compress: If True, gzip compress the output

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    if compress and not str(output_path).endswith(".gz"):
        output_path = Path(str(output_path) + ".gz")

    logger.info(f"Exporting HMM posteriors to {output_path}")

    states = hmm_results.states
    header = ["sample", "chrom", "position"] + [f"{s}_posterior" for s in states]

    lines = ["\t".join(header)]

    for result in hmm_results.results.values():
        sample = result.sample
        chrom = result.chrom

        for i, pos in enumerate(result.positions):
            row = [sample, chrom, str(pos)]
            for j, _state in enumerate(states):
                row.append(f"{result.posteriors[i, j]:.6f}")
            lines.append("\t".join(row))

    content = "\n".join(lines) + "\n"

    if compress:
        with gzip.open(output_path, "wt") as f:
            f.write(content)
    else:
        output_path.write_text(content)

    return output_path


def export_viterbi_path(
    hmm_results: HMMResults,
    output_path: str | Path,
) -> Path:
    """Export Viterbi path to BED format.

    Creates a BED file with segments of consistent HMM state.

    Args:
        hmm_results: HMM inference results
        output_path: Output file path

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting Viterbi path to {output_path}")

    lines = [
        'track name="viterbi_path" description="HMM Viterbi path" itemRgb="On"'
    ]

    # Define colors for states
    state_colors = _get_state_colors(hmm_results.states)

    for result in hmm_results.results.values():
        if not result.positions or not result.viterbi_path:
            continue

        sample = result.sample
        chrom = result.chrom
        positions = result.positions
        path = result.viterbi_path

        # Identify contiguous segments
        segments = []
        seg_start = positions[0]
        seg_state = path[0]

        for i in range(1, len(positions)):
            if path[i] != seg_state:
                # End current segment
                segments.append((seg_start, positions[i - 1], seg_state))
                seg_start = positions[i]
                seg_state = path[i]

        # Add final segment
        segments.append((seg_start, positions[-1], seg_state))

        for start, end, state_name in segments:
            color = state_colors.get(state_name, "128,128,128")
            name = f"{sample}:{state_name}"

            # BED format
            line = "\t".join([
                chrom,
                str(start),
                str(end + 1),  # BED is 0-based, half-open
                name,
                "1000",  # score
                ".",  # strand
                str(start),
                str(end + 1),
                color,
            ])
            lines.append(line)

    output_path.write_text("\n".join(lines) + "\n")
    return output_path


def export_hmm_smoothed_proportions(
    hmm_results: HMMResults,
    output_path: str | Path,
    compress: bool = True,
) -> Path:
    """Export HMM-smoothed founder proportions to TSV format.

    Args:
        hmm_results: HMM inference results
        output_path: Output file path
        compress: If True, gzip compress the output

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    if compress and not str(output_path).endswith(".gz"):
        output_path = Path(str(output_path) + ".gz")

    logger.info(f"Exporting smoothed proportions to {output_path}")

    founders = hmm_results.founders
    header = ["sample", "chrom", "position"] + [f"{f}_proportion" for f in founders]

    lines = ["\t".join(header)]

    for result in hmm_results.results.values():
        sample = result.sample
        chrom = result.chrom

        for i, pos in enumerate(result.positions):
            row = [sample, chrom, str(pos)]
            for founder in founders:
                prop = result.smoothed_proportions[i].get(founder, 0.0)
                row.append(f"{prop:.6f}")
            lines.append("\t".join(row))

    content = "\n".join(lines) + "\n"

    if compress:
        with gzip.open(output_path, "wt") as f:
            f.write(content)
    else:
        output_path.write_text(content)

    return output_path


# =============================================================================
# Summary Exports
# =============================================================================


def export_sample_summary(
    summary: GenomeSummary | list[SampleSummary],
    output_path: str | Path,
) -> Path:
    """Export sample summaries to TSV format.

    Args:
        summary: GenomeSummary object or list of SampleSummary objects
        output_path: Output file path

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting sample summary to {output_path}")

    # Get sample summaries
    if hasattr(summary, "all_samples"):
        samples = summary.all_samples()
        founders = summary.founders
    else:
        samples = summary
        # Infer founders from first sample
        founders = list(samples[0].founder_proportions.keys()) if samples else []

    if not samples:
        output_path.write_text("")
        return output_path

    # Build header
    header = [
        "sample",
        "genome_size",
        "n_blocks",
        "n_breakpoints",
        "mean_block_size",
        "heterozygosity",
        "coverage",
        "n_markers",
        "n_windows",
    ]
    for f in founders:
        header.append(f"{f}_proportion")
    for f in founders:
        header.append(f"{f}_max_block")

    lines = ["\t".join(header)]

    for s in samples:
        row = [
            s.sample,
            str(s.genome_size),
            str(s.n_blocks),
            str(s.n_breakpoints),
            f"{s.mean_block_size:.1f}",
            f"{s.heterozygosity:.4f}",
            f"{s.coverage:.4f}",
            str(s.n_markers),
            str(s.n_windows),
        ]
        for f in founders:
            row.append(f"{s.founder_proportions.get(f, 0.0):.4f}")
        for f in founders:
            row.append(str(s.max_block_size.get(f, 0)))
        lines.append("\t".join(row))

    output_path.write_text("\n".join(lines) + "\n")
    return output_path


def export_population_summary(
    summary: PopulationSummary,
    output_path: str | Path,
) -> Path:
    """Export population summary to TSV format.

    Args:
        summary: PopulationSummary object
        output_path: Output file path

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting population summary to {output_path}")

    lines = []

    # Population info
    lines.append(f"# Population: {summary.population}")
    lines.append(f"# N samples: {summary.n_samples}")
    lines.append("")

    # Founder proportions
    lines.append("# Founder proportions (mean, std, min, max)")
    lines.append("founder\tmean\tstd\tmin\tmax")
    for f in summary.mean_founder_proportions:
        mean = summary.mean_founder_proportions.get(f, 0.0)
        std = summary.std_founder_proportions.get(f, 0.0)
        min_val, max_val = summary.founder_proportion_range.get(f, (0.0, 0.0))
        lines.append(f"{f}\t{mean:.4f}\t{std:.4f}\t{min_val:.4f}\t{max_val:.4f}")

    lines.append("")

    # Breakpoint density
    if summary.breakpoint_density:
        lines.append("# Breakpoint density (per Mb)")
        lines.append("chrom\tdensity")
        for chrom, density in sorted(summary.breakpoint_density.items()):
            lines.append(f"{chrom}\t{density:.4f}")

    output_path.write_text("\n".join(lines) + "\n")
    return output_path


def export_summary_json(
    summary: GenomeSummary,
    output_path: str | Path,
) -> Path:
    """Export full summary to JSON format.

    Args:
        summary: GenomeSummary object
        output_path: Output file path

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting summary to {output_path}")

    data = summary.to_dict()
    output_path.write_text(json.dumps(data, indent=2))
    return output_path


# =============================================================================
# Ancestry Painting Exports
# =============================================================================


def export_painting_matrix(
    painting: AncestryPainting,
    output_path: str | Path,
    format: str = "auto",
) -> Path:
    """Export ancestry painting matrix.

    Args:
        painting: AncestryPainting object
        output_path: Output file path
        format: Output format ('hdf5', 'tsv', 'auto' to detect from extension)

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)

    # Auto-detect format
    if format == "auto":
        format = "hdf5" if str(output_path).endswith((".h5", ".hdf5")) else "tsv"

    logger.info(f"Exporting painting matrix to {output_path} (format={format})")

    if format == "hdf5":
        painting.to_hdf5(output_path)
    elif format == "tsv":
        _export_painting_tsv(painting, output_path)
    else:
        raise ValueError(f"Unknown format: {format}")

    return output_path


def _export_painting_tsv(
    painting: AncestryPainting,
    output_path: Path,
) -> None:
    """Export painting to TSV format."""
    # Determine if we should compress
    compress = str(output_path).endswith(".gz")

    header = ["sample", "chrom", "start", "end", "founder", "founder_index"]
    for f in painting.founders:
        header.append(f"{f}_prob")

    lines = ["\t".join(header)]

    for row in painting.to_dataframe_long():
        line_parts = [
            row["sample"],
            row["chrom"],
            str(row["start"]),
            str(row["end"]),
            row["founder"],
            str(row["founder_index"]),
        ]
        for f in painting.founders:
            line_parts.append(f"{row.get(f'{f}_prob', 0.0):.4f}")
        lines.append("\t".join(line_parts))

    content = "\n".join(lines) + "\n"

    if compress:
        with gzip.open(output_path, "wt") as f:
            f.write(content)
    else:
        output_path.write_text(content)


def export_painting_bed(
    painting: AncestryPainting,
    output_path: str | Path,
    sample: str | None = None,
) -> Path:
    """Export painting to BED format.

    Args:
        painting: AncestryPainting object
        output_path: Output file path
        sample: Optional sample name (exports all if None)

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting painting to {output_path}")

    lines = [
        'track name="ancestry_painting" description="Ancestry painting" itemRgb="On"'
    ]

    founder_colors = _get_founder_colors(painting.founders)

    samples = [sample] if sample else painting.samples

    for s in samples:
        if s not in painting.samples:
            continue

        sample_idx = painting.samples.index(s)

        for bin_idx, bin in enumerate(painting.bins):
            founder_idx = int(painting.matrix[sample_idx, bin_idx])
            founder = painting.founders[founder_idx] if 0 <= founder_idx < len(painting.founders) else "Unknown"
            color = founder_colors.get(founder, "128,128,128")
            name = f"{s}:{founder}"

            line = "\t".join([
                bin.chrom,
                str(bin.start),
                str(bin.end),
                name,
                "1000",
                ".",
                str(bin.start),
                str(bin.end),
                color,
            ])
            lines.append(line)

    output_path.write_text("\n".join(lines) + "\n")
    return output_path


# =============================================================================
# Comparison Exports
# =============================================================================


def export_similarity_matrix(
    comparison: SampleComparison,
    output_path: str | Path,
    method: str = "correlation",
) -> Path:
    """Export pairwise similarity matrix to TSV format.

    Args:
        comparison: SampleComparison object
        output_path: Output file path
        method: Similarity method

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting similarity matrix to {output_path}")

    similarity = comparison.pairwise_similarity(method)
    samples = comparison.sample_names

    # Header
    header = ["sample"] + samples
    lines = ["\t".join(header)]

    for i, s in enumerate(samples):
        row = [s] + [f"{similarity[i, j]:.4f}" for j in range(len(samples))]
        lines.append("\t".join(row))

    output_path.write_text("\n".join(lines) + "\n")
    return output_path


def export_cluster_results(
    clusters: ClusterResult,
    output_path: str | Path,
) -> Path:
    """Export clustering results to TSV format.

    Args:
        clusters: ClusterResult object
        output_path: Output file path

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting cluster results to {output_path}")

    lines = [
        f"# Clustering method: {clusters.method}",
        f"# N clusters: {clusters.n_clusters}",
        "",
        "sample\tcluster",
    ]

    for sample, label in zip(clusters.sample_names, clusters.labels, strict=False):
        lines.append(f"{sample}\t{label}")

    output_path.write_text("\n".join(lines) + "\n")
    return output_path


def export_shared_blocks(
    blocks: list[SharedBlock],
    output_path: str | Path,
) -> Path:
    """Export shared blocks to TSV format.

    Args:
        blocks: List of SharedBlock objects
        output_path: Output file path

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting shared blocks to {output_path}")

    header = [
        "chrom",
        "start",
        "end",
        "length",
        "founder",
        "n_samples",
        "mean_proportion",
        "samples",
    ]
    lines = ["\t".join(header)]

    for block in blocks:
        row = [
            block.chrom,
            str(block.start),
            str(block.end),
            str(block.length),
            block.founder,
            str(block.n_samples),
            f"{block.mean_proportion:.4f}",
            ",".join(block.samples),
        ]
        lines.append("\t".join(row))

    output_path.write_text("\n".join(lines) + "\n")
    return output_path


# =============================================================================
# QC Report Exports
# =============================================================================


def export_qc_report(
    qc: QCReport,
    output_path: str | Path,
    format: str = "tsv",
) -> Path:
    """Export QC report.

    Args:
        qc: QCReport object
        output_path: Output file path
        format: Output format ('tsv', 'json')

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting QC report to {output_path}")

    if format == "json":
        data = qc.to_dict()
        output_path.write_text(json.dumps(data, indent=2))
    else:
        _export_qc_tsv(qc, output_path)

    return output_path


def _export_qc_tsv(qc: QCReport, output_path: Path) -> None:
    """Export QC report to TSV format."""
    lines = []

    # Calculate overall status
    n_samples = len(qc.samples)
    n_passing = qc.n_samples_passed
    n_failing = n_samples - n_passing
    status = "PASS" if n_failing == 0 else "WARN" if qc.n_errors == 0 else "FAIL"

    # Overall status
    lines.append(f"# QC Report: {status}")
    lines.append(f"# Total samples: {n_samples}")
    lines.append(f"# Samples passing: {n_passing}")
    lines.append(f"# Samples failing: {n_failing}")
    lines.append("")

    # Collect all warnings
    all_warnings = (
        qc.global_warnings
        + [w for s in qc.samples.values() for w in s.warnings]
        + [w for c in qc.chromosomes.values() for w in c.warnings]
    )

    # Summary warnings
    if all_warnings:
        lines.append("# Warnings")
        lines.append("sample\tchrom\tlevel\tcategory\tmessage")
        for w in all_warnings:
            lines.append(f"{w.sample or 'global'}\t{w.chrom or 'genome'}\t{w.level}\t{w.category}\t{w.message}")
        lines.append("")

    # Sample-level QC
    lines.append("# Sample QC metrics")
    header = [
        "sample",
        "passed",
        "missing_rate",
        "mean_confidence",
        "low_confidence_rate",
        "n_warnings",
    ]
    lines.append("\t".join(header))

    for sample_qc in qc.samples.values():
        row = [
            sample_qc.sample,
            "PASS" if sample_qc.passed else "FAIL",
            f"{sample_qc.missing_rate:.4f}",
            f"{sample_qc.mean_confidence:.4f}",
            f"{sample_qc.low_confidence_rate:.4f}",
            str(len(sample_qc.warnings)),
        ]
        lines.append("\t".join(row))

    output_path.write_text("\n".join(lines) + "\n")


def export_qc_warnings(
    qc: QCReport,
    output_path: str | Path,
) -> Path:
    """Export QC warnings to TSV format.

    Args:
        qc: QCReport object
        output_path: Output file path

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting QC warnings to {output_path}")

    header = ["sample", "chrom", "level", "category", "message"]
    lines = ["\t".join(header)]

    # Collect all warnings from all sources
    all_warnings = (
        qc.global_warnings
        + [w for s in qc.samples.values() for w in s.warnings]
        + [w for c in qc.chromosomes.values() for w in c.warnings]
    )

    for w in all_warnings:
        row = [
            w.sample or "global",
            w.chrom or "genome",
            w.level,
            w.category,
            w.message,
        ]
        lines.append("\t".join(row))

    output_path.write_text("\n".join(lines) + "\n")
    return output_path


# =============================================================================
# Utility Functions
# =============================================================================


def _get_founder_colors(founders: list[str]) -> dict[str, str]:
    """Generate colors for founders.

    Args:
        founders: List of founder names

    Returns:
        Dict mapping founder names to RGB color strings
    """
    colors = [
        "230,25,75",   # red
        "60,180,75",   # green
        "0,130,200",   # blue
        "255,225,25",  # yellow
        "245,130,48",  # orange
        "145,30,180",  # purple
        "70,240,240",  # cyan
        "240,50,230",  # magenta
        "128,128,0",   # olive
        "0,128,128",   # teal
    ]
    return {f: colors[i % len(colors)] for i, f in enumerate(founders)}


def _get_state_colors(states: list[str]) -> dict[str, str]:
    """Generate colors for HMM states.

    Args:
        states: List of state names

    Returns:
        Dict mapping state names to RGB color strings
    """
    colors = [
        "230,25,75",   # red
        "60,180,75",   # green
        "0,130,200",   # blue
        "255,225,25",  # yellow
        "245,130,48",  # orange
        "145,30,180",  # purple
        "70,240,240",  # cyan
        "240,50,230",  # magenta
        "128,128,0",   # olive
        "0,128,128",   # teal
        "220,190,255", # lavender
        "170,110,40",  # brown
        "255,250,200", # beige
        "128,0,0",     # maroon
        "170,255,195", # mint
    ]
    return {s: colors[i % len(colors)] for i, s in enumerate(states)}


def export_all_analysis_formats(
    output_prefix: str | Path,
    hmm_results: HMMResults | None = None,
    summary: GenomeSummary | None = None,
    painting: AncestryPainting | None = None,
    comparison: SampleComparison | None = None,
    qc: QCReport | None = None,
) -> dict[str, Path]:
    """Export all analysis results to multiple formats.

    Args:
        output_prefix: Prefix for output files
        hmm_results: Optional HMM results
        summary: Optional genome summary
        painting: Optional ancestry painting
        comparison: Optional sample comparison
        qc: Optional QC report

    Returns:
        Dict mapping output names to file paths
    """
    output_prefix = Path(output_prefix)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)

    outputs = {}

    # HMM exports
    if hmm_results is not None:
        outputs["hmm_posteriors"] = export_hmm_posteriors(
            hmm_results, f"{output_prefix}_hmm_posteriors.tsv.gz"
        )
        outputs["viterbi_path"] = export_viterbi_path(
            hmm_results, f"{output_prefix}_viterbi.bed"
        )
        outputs["hmm_proportions"] = export_hmm_smoothed_proportions(
            hmm_results, f"{output_prefix}_hmm_proportions.tsv.gz"
        )

    # Summary exports
    if summary is not None:
        outputs["sample_summary"] = export_sample_summary(
            summary, f"{output_prefix}_sample_summary.tsv"
        )
        pop_summary = summary.by_population("all")
        outputs["population_summary"] = export_population_summary(
            pop_summary, f"{output_prefix}_population_summary.tsv"
        )
        outputs["summary_json"] = export_summary_json(
            summary, f"{output_prefix}_summary.json"
        )

    # Painting exports
    if painting is not None:
        outputs["painting_tsv"] = export_painting_matrix(
            painting, f"{output_prefix}_painting.tsv.gz", format="tsv"
        )
        outputs["painting_bed"] = export_painting_bed(
            painting, f"{output_prefix}_painting.bed"
        )
        # HDF5 only if h5py is available
        try:
            import h5py
            outputs["painting_hdf5"] = export_painting_matrix(
                painting, f"{output_prefix}_painting.h5", format="hdf5"
            )
        except ImportError:
            logger.warning("h5py not available, skipping HDF5 export")

    # Comparison exports
    if comparison is not None:
        outputs["similarity_matrix"] = export_similarity_matrix(
            comparison, f"{output_prefix}_similarity.tsv"
        )

    # QC exports
    if qc is not None:
        outputs["qc_report"] = export_qc_report(
            qc, f"{output_prefix}_qc_report.tsv"
        )
        outputs["qc_warnings"] = export_qc_warnings(
            qc, f"{output_prefix}_qc_warnings.tsv"
        )

    return outputs
