#!/usr/bin/env python3
"""
Maize NAM Haplotype Analysis Example

This script demonstrates haplotype proportion analysis using
the phaser Python API.
"""

from pathlib import Path

# Define paths
DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def main():
    """Run the complete analysis pipeline."""
    from haplophaser.io.populations import load_populations
    from haplophaser.io.markers import load_markers, save_markers
    from haplophaser.markers.diagnostic import DiagnosticMarkerFinder
    from haplophaser.proportion.estimate import WindowProportionEstimator
    from haplophaser.proportion.blocks import HaplotypeBlockCaller
    from haplophaser.viz import plot_haplotype_proportions

    print("=== Maize NAM Haplotype Analysis ===\n")

    # Step 1: Load populations
    print("Step 1: Loading populations...")
    populations = load_populations(DATA_DIR / "populations.tsv")
    founders = populations.get_founders()
    print(f"  Founders: {[f.name for f in founders]}")
    print(f"  Derived samples: {len(populations.get_derived())}")
    print()

    # Step 2: Find diagnostic markers
    print("Step 2: Finding diagnostic markers...")
    finder = DiagnosticMarkerFinder(
        min_freq_diff=0.7,
        min_samples=2,
    )

    markers = finder.find_from_vcf(
        DATA_DIR / "nam_founders_chr1.vcf.gz",
        populations,
    )
    print(f"  Found {len(markers)} diagnostic markers")

    # Save markers
    save_markers(markers, RESULTS_DIR / "markers.tsv")
    markers.to_bed(RESULTS_DIR / "markers.bed")
    print()

    # Step 3: Estimate proportions
    print("Step 3: Estimating haplotype proportions...")
    estimator = WindowProportionEstimator(
        window_size=1_000_000,
        step_size=500_000,
        min_markers=3,
    )

    proportions = estimator.estimate_from_vcf(
        DATA_DIR / "nam_rils_chr1.vcf.gz",
        markers,
        populations,
    )
    print(f"  Analyzed {proportions.n_windows} windows")
    print(f"  Samples: {proportions.n_samples}")

    # Save proportions
    proportions.to_tsv(RESULTS_DIR / "proportions_windows.tsv")
    print()

    # Step 4: Call haplotype blocks
    print("Step 4: Calling haplotype blocks...")
    caller = HaplotypeBlockCaller(
        min_proportion=0.8,
        min_markers=3,
    )

    blocks = caller.call(proportions)
    print(f"  Called {len(blocks)} haplotype blocks")

    # Save blocks
    blocks.to_bed(RESULTS_DIR / "proportions_blocks.bed")
    print()

    # Step 5: Visualize
    print("Step 5: Creating visualizations...")

    plot_haplotype_proportions(
        haplotypes=RESULTS_DIR / "proportions_blocks.bed",
        reference=DATA_DIR / "Zm-B73-v5.fa.fai",
        output=RESULTS_DIR / "chr1_haplotypes.pdf",
        region="chr1",
        founders=[f.name for f in founders[:3]],
        title="Chromosome 1 Haplotype Blocks",
    )
    print("  Created: results/chr1_haplotypes.pdf")
    print()

    # Summary
    print("=== Analysis Complete ===\n")
    print("Results saved to:")
    for f in sorted(RESULTS_DIR.glob("*")):
        print(f"  - {f.name}")


if __name__ == "__main__":
    main()
