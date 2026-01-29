"""Export functions for proportion estimation results.

This module provides functions for exporting haplotype proportion
results to various file formats.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from haplophaser.proportion.blocks import BlockResults
    from haplophaser.proportion.breakpoints import BreakpointResults
    from haplophaser.proportion.results import ProportionResults

logger = logging.getLogger(__name__)


def export_proportions_tsv(
    results: ProportionResults,
    output_path: str | Path,
    include_ci: bool = True,
) -> Path:
    """Export window proportions to TSV format.

    Creates a tab-separated file with one row per window per sample.

    Args:
        results: Proportion estimation results
        output_path: Output file path
        include_ci: Include confidence intervals if available

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting proportions to {output_path}")

    # Build header
    header = ["sample", "chrom", "start", "end", "n_markers", "method"]
    founders = results.founders
    for f in founders:
        header.append(f"{f}_proportion")
    if include_ci:
        for f in founders:
            header.append(f"{f}_ci_lower")
            header.append(f"{f}_ci_upper")

    lines = ["\t".join(header)]

    for sample in results:
        for window in sample.windows:
            row = [
                sample.sample_name,
                window.chrom,
                str(window.start),
                str(window.end),
                str(window.n_markers),
                window.method,
            ]

            # Add proportions
            for f in founders:
                row.append(f"{window.proportions.get(f, 0.0):.4f}")

            # Add confidence intervals
            if include_ci:
                for f in founders:
                    ci = window.get_ci(f)
                    if ci:
                        row.append(f"{ci[0]:.4f}")
                        row.append(f"{ci[1]:.4f}")
                    else:
                        row.append("NA")
                        row.append("NA")

            lines.append("\t".join(row))

    output_path.write_text("\n".join(lines) + "\n")
    return output_path


def export_proportions_bedgraph(
    results: ProportionResults,
    output_path: str | Path,
    founder: str,
) -> Path:
    """Export proportions for a single founder to BedGraph format.

    Creates a BedGraph file for visualization in genome browsers.

    Args:
        results: Proportion estimation results
        output_path: Output file path
        founder: Founder name to export

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting {founder} proportions to {output_path}")

    lines = [f'track type=bedGraph name="{founder}_proportion"']

    for sample in results:
        # Sort windows by position
        sorted_windows = sorted(sample.windows, key=lambda w: (w.chrom, w.start))

        for window in sorted_windows:
            proportion = window.proportions.get(founder, 0.0)
            lines.append(f"{window.chrom}\t{window.start}\t{window.end}\t{proportion:.4f}")

    output_path.write_text("\n".join(lines) + "\n")
    return output_path


def export_genome_wide_tsv(
    results: ProportionResults,
    output_path: str | Path,
) -> Path:
    """Export genome-wide proportions to TSV format.

    Creates a summary file with one row per sample.

    Args:
        results: Proportion estimation results
        output_path: Output file path

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting genome-wide proportions to {output_path}")

    founders = results.founders
    header = ["sample"] + [f"{f}_proportion" for f in founders]
    lines = ["\t".join(header)]

    for sample in results:
        row = [sample.sample_name]
        for f in founders:
            row.append(f"{sample.genome_wide.get(f, 0.0):.4f}")
        lines.append("\t".join(row))

    output_path.write_text("\n".join(lines) + "\n")
    return output_path


def export_proportions_json(
    results: ProportionResults,
    output_path: str | Path,
) -> Path:
    """Export proportions to JSON format.

    Creates a JSON file with full proportion data.

    Args:
        results: Proportion estimation results
        output_path: Output file path

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting proportions to {output_path}")

    data = results.to_dict()
    output_path.write_text(json.dumps(data, indent=2))
    return output_path


def export_blocks_bed(
    blocks: BlockResults,
    output_path: str | Path,
) -> Path:
    """Export haplotype blocks to BED format.

    Creates a BED file with one entry per block.

    Args:
        blocks: Block calling results
        output_path: Output file path

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting blocks to {output_path}")

    lines = [
        'track name="haplotype_blocks" description="Haplotype blocks" '
        'itemRgb="On"'
    ]

    # Define colors for founders
    founder_colors = _get_founder_colors(blocks.founders)

    for sample_blocks in blocks.samples.values():
        for block in sample_blocks.blocks:
            # BED score (0-1000)
            score = int(block.confidence * 1000)

            # Color based on founder
            color = founder_colors.get(block.dominant_founder, "128,128,128")

            # Name includes sample and founder
            name = f"{sample_blocks.sample_name}:{block.dominant_founder}"

            # BED12 format
            line = "\t".join(
                [
                    block.chrom,
                    str(block.start),
                    str(block.end),
                    name,
                    str(score),
                    ".",  # strand
                    str(block.start),  # thick start
                    str(block.end),  # thick end
                    color,
                ]
            )
            lines.append(line)

    output_path.write_text("\n".join(lines) + "\n")
    return output_path


def export_blocks_tsv(
    blocks: BlockResults,
    output_path: str | Path,
) -> Path:
    """Export haplotype blocks to TSV format.

    Args:
        blocks: Block calling results
        output_path: Output file path

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting blocks to {output_path}")

    header = [
        "sample",
        "chrom",
        "start",
        "end",
        "length",
        "dominant_founder",
        "mean_proportion",
        "min_proportion",
        "max_proportion",
        "n_windows",
        "confidence",
        "is_mixed",
    ]
    lines = ["\t".join(header)]

    for sample_blocks in blocks.samples.values():
        for block in sample_blocks.blocks:
            row = [
                sample_blocks.sample_name,
                block.chrom,
                str(block.start),
                str(block.end),
                str(block.length),
                block.dominant_founder,
                f"{block.mean_proportion:.4f}",
                f"{block.min_proportion:.4f}",
                f"{block.max_proportion:.4f}",
                str(block.n_windows),
                f"{block.confidence:.4f}",
                str(block.is_mixed).lower(),
            ]
            lines.append("\t".join(row))

    output_path.write_text("\n".join(lines) + "\n")
    return output_path


def export_breakpoints_bed(
    breakpoints: BreakpointResults,
    output_path: str | Path,
) -> Path:
    """Export breakpoints to BED format.

    Creates a BED file with one entry per breakpoint.

    Args:
        breakpoints: Breakpoint detection results
        output_path: Output file path

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting breakpoints to {output_path}")

    lines = ['track name="breakpoints" description="Ancestry breakpoints"']

    for sample_bps in breakpoints.samples.values():
        for bp in sample_bps.breakpoints:
            # Create a small region around the breakpoint
            half_width = 500
            start = max(0, bp.position - half_width)
            end = bp.position + half_width

            score = int(bp.confidence * 1000)
            name = f"{sample_bps.sample_name}:{bp.left_founder}->{bp.right_founder}"

            line = "\t".join(
                [
                    bp.chrom,
                    str(start),
                    str(end),
                    name,
                    str(score),
                ]
            )
            lines.append(line)

    output_path.write_text("\n".join(lines) + "\n")
    return output_path


def export_breakpoints_tsv(
    breakpoints: BreakpointResults,
    output_path: str | Path,
) -> Path:
    """Export breakpoints to TSV format.

    Args:
        breakpoints: Breakpoint detection results
        output_path: Output file path

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    logger.info(f"Exporting breakpoints to {output_path}")

    header = [
        "sample",
        "chrom",
        "position",
        "left_founder",
        "right_founder",
        "left_proportion",
        "right_proportion",
        "confidence",
        "method",
    ]
    lines = ["\t".join(header)]

    for sample_bps in breakpoints.samples.values():
        for bp in sample_bps.breakpoints:
            row = [
                sample_bps.sample_name,
                bp.chrom,
                str(bp.position),
                bp.left_founder,
                bp.right_founder,
                f"{bp.left_proportion:.4f}",
                f"{bp.right_proportion:.4f}",
                f"{bp.confidence:.4f}",
                bp.method,
            ]
            lines.append("\t".join(row))

    output_path.write_text("\n".join(lines) + "\n")
    return output_path


def export_all_proportion_formats(
    results: ProportionResults,
    output_prefix: str | Path,
    formats: list[str] | None = None,
    blocks: BlockResults | None = None,
    breakpoints: BreakpointResults | None = None,
) -> dict[str, Path]:
    """Export proportion results to multiple formats.

    Args:
        results: Proportion estimation results
        output_prefix: Prefix for output files
        formats: List of formats to export (default: all available)
        blocks: Optional block calling results
        breakpoints: Optional breakpoint detection results

    Returns:
        Dict mapping format names to output paths
    """
    output_prefix = Path(output_prefix)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)

    available_formats = ["tsv", "json", "genome_wide"]
    if blocks is not None:
        available_formats.extend(["blocks_bed", "blocks_tsv"])
    if breakpoints is not None:
        available_formats.extend(["breakpoints_bed", "breakpoints_tsv"])

    if formats is None:
        formats = available_formats
    else:
        formats = [f for f in formats if f in available_formats]

    outputs = {}

    for fmt in formats:
        if fmt == "tsv":
            path = export_proportions_tsv(results, f"{output_prefix}_windows.tsv")
            outputs["tsv"] = path
        elif fmt == "json":
            path = export_proportions_json(results, f"{output_prefix}.json")
            outputs["json"] = path
        elif fmt == "genome_wide":
            path = export_genome_wide_tsv(results, f"{output_prefix}_genome_wide.tsv")
            outputs["genome_wide"] = path
        elif fmt == "blocks_bed" and blocks is not None:
            path = export_blocks_bed(blocks, f"{output_prefix}_blocks.bed")
            outputs["blocks_bed"] = path
        elif fmt == "blocks_tsv" and blocks is not None:
            path = export_blocks_tsv(blocks, f"{output_prefix}_blocks.tsv")
            outputs["blocks_tsv"] = path
        elif fmt == "breakpoints_bed" and breakpoints is not None:
            path = export_breakpoints_bed(
                breakpoints, f"{output_prefix}_breakpoints.bed"
            )
            outputs["breakpoints_bed"] = path
        elif fmt == "breakpoints_tsv" and breakpoints is not None:
            path = export_breakpoints_tsv(
                breakpoints, f"{output_prefix}_breakpoints.tsv"
            )
            outputs["breakpoints_tsv"] = path

    return outputs


def _get_founder_colors(founders: list[str]) -> dict[str, str]:
    """Generate colors for founders.

    Args:
        founders: List of founder names

    Returns:
        Dict mapping founder names to RGB color strings
    """
    # Predefined color palette
    colors = [
        "230,25,75",  # red
        "60,180,75",  # green
        "0,130,200",  # blue
        "255,225,25",  # yellow
        "245,130,48",  # orange
        "145,30,180",  # purple
        "70,240,240",  # cyan
        "240,50,230",  # magenta
        "128,128,0",  # olive
        "0,128,128",  # teal
    ]

    return {f: colors[i % len(colors)] for i, f in enumerate(founders)}
