"""Shared visualization utilities."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import chromoplot as cp

if TYPE_CHECKING:
    from ..proportion.results import ProportionResults


def get_phaser_theme() -> cp.Theme:
    """
    Get the default phaser visualization theme.

    Returns
    -------
    Theme
        Chromoplot theme configured for phaser outputs
    """
    return cp.Theme(
        figure_facecolor="white",
        font_family="sans-serif",
        title_fontsize=12,
        label_fontsize=10,
        tick_fontsize=8,
        spine_color="#333333",
        spine_width=0.5,
        track_spacing=0.08,
    )


def get_founder_colors(
    founders: list[str],
    use_maize_colors: bool = True,
) -> dict[str, str]:
    """
    Get color mapping for founders.

    Parameters
    ----------
    founders : list[str]
        List of founder names
    use_maize_colors : bool
        Use maize NAM heterotic group colors if applicable

    Returns
    -------
    dict[str, str]
        Mapping of founder names to hex colors
    """
    if use_maize_colors:
        # Check if any founders match maize NAM
        from chromoplot.themes.colors import MAIZE_NAM_COLORS

        if any(f in MAIZE_NAM_COLORS for f in founders):
            return cp.maize_nam_colors(founders)

    return cp.founder_colors(founders)


def results_to_bed(
    results: "ProportionResults | list",
    output: str | Path,
    sample: str | None = None,
) -> Path:
    """
    Convert phaser results to BED format for chromoplot.

    Parameters
    ----------
    results : ProportionResults or list[HaplotypeBlock]
        Phaser analysis results
    output : str or Path
        Output BED file path
    sample : str, optional
        Sample to export (if results contain multiple)

    Returns
    -------
    Path
        Path to created BED file
    """
    output = Path(output)

    with open(output, "w") as f:
        f.write("#chrom\tstart\tend\tfounder\tscore\tstrand\n")

        if hasattr(results, "blocks"):
            # ProportionResults object
            blocks = results.blocks
            if sample:
                blocks = [b for b in blocks if b.sample == sample]
        else:
            # List of blocks
            blocks = results

        for block in blocks:
            score = int(block.confidence * 1000) if hasattr(block, "confidence") else 1000
            f.write(
                f"{block.chrom}\t{block.start}\t{block.end}\t"
                f"{block.founder}\t{score}\t.\n"
            )

    return output


def proportions_to_bedgraph(
    results: "ProportionResults",
    output_prefix: str | Path,
    founder: str,
    sample: str | None = None,
) -> Path:
    """
    Convert proportion results to bedGraph for signal track.

    Creates one bedGraph file showing proportion of specified founder.

    Parameters
    ----------
    results : ProportionResults
        Window proportion results
    output_prefix : str or Path
        Output prefix (will add .bedGraph)
    founder : str
        Founder to create track for
    sample : str, optional
        Sample to export

    Returns
    -------
    Path
        Path to created bedGraph file
    """
    output = Path(f"{output_prefix}_{founder}.bedGraph")

    with open(output, "w") as f:
        f.write(f'track type=bedGraph name="{founder}_proportion"\n')

        for window in results.windows:
            if sample and window.sample != sample:
                continue

            proportion = window.founder_proportions.get(founder, 0.0)
            f.write(f"{window.chrom}\t{window.start}\t{window.end}\t{proportion:.4f}\n")

    return output


def expression_to_bed(
    bias_results: "BiasResults",
    output: str | Path,
    value: str = "log2ratio",
) -> Path:
    """
    Convert expression bias results to BED for visualization.

    Parameters
    ----------
    bias_results : BiasResults
        Expression bias analysis results
    output : str or Path
        Output BED file path
    value : str
        Value to use as score: 'log2ratio', 'pvalue', 'confidence'

    Returns
    -------
    Path
        Path to created BED file
    """
    import numpy as np

    output = Path(output)

    with open(output, "w") as f:
        f.write("#chrom\tstart\tend\tgene_pair\tscore\tbias_direction\n")

        for bias in bias_results.homeolog_biases:
            pair = bias.pair

            if value == "log2ratio":
                score = bias.mean_log2ratio
            elif value == "pvalue":
                score = -np.log10(bias.pvalue + 1e-10)
            else:
                score = bias.confidence if hasattr(bias, "confidence") else 0

            f.write(
                f"{pair.gene1_chrom}\t{pair.gene1_start}\t{pair.gene1_end}\t"
                f"{pair.gene1_id}:{pair.gene2_id}\t{score:.4f}\t{bias.bias_direction}\n"
            )

    return output


def load_reference(reference: str | Path) -> cp.GenomeCoordinates:
    """
    Load genome coordinates from various formats.

    Parameters
    ----------
    reference : str or Path
        Path to .fai, .sizes, or FASTA file

    Returns
    -------
    GenomeCoordinates
    """
    path = Path(reference)

    if path.suffix == ".fai":
        return cp.GenomeCoordinates.from_fai(path)
    elif path.suffix == ".sizes" or "chrom.sizes" in path.name:
        return cp.GenomeCoordinates.from_chrom_sizes(path)
    elif path.suffix in (".fa", ".fasta", ".fna"):
        # Try to find .fai
        fai_path = Path(str(path) + ".fai")
        if fai_path.exists():
            return cp.GenomeCoordinates.from_fai(fai_path)
        raise ValueError(f"FASTA index not found: {fai_path}")
    else:
        # Try as .fai
        return cp.GenomeCoordinates.from_fai(path)
