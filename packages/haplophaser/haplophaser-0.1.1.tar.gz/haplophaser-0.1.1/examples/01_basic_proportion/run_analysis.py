#!/usr/bin/env python3
"""
Basic Haplotype Proportion Analysis Example

This script demonstrates a complete workflow for estimating
founder haplotype proportions in derived lines.
"""

from pathlib import Path

from haplophaser.io.populations import load_populations
from haplophaser.markers.diagnostic import DiagnosticMarkerFinder
from haplophaser.proportion.window import WindowProportionEstimator


def main():
    # Configuration
    data_dir = Path("../data")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    vcf_path = data_dir / "example_variants.vcf.gz"
    pop_path = data_dir / "populations.tsv"

    # Step 1: Load population assignments
    print("Loading population data...")
    populations = load_populations(pop_path)
    print(f"  Founders: {list(populations.get_founders().keys())}")
    print(f"  Derived samples: {len(populations.get_derived())}")

    # Step 2: Find diagnostic markers
    print("\nFinding diagnostic markers...")
    finder = DiagnosticMarkerFinder(
        min_freq_diff=0.7,
        min_samples=1,
        max_missing=0.2,
    )
    markers = finder.find_from_vcf(vcf_path, populations)
    print(f"  Found {len(markers)} diagnostic markers")

    # Save markers
    markers_path = output_dir / "diagnostic_markers.tsv"
    finder.save_markers(markers, markers_path)
    print(f"  Saved to {markers_path}")

    # Step 3: Estimate proportions in windows
    print("\nEstimating haplotype proportions...")
    estimator = WindowProportionEstimator(
        window_size=1_000_000,  # 1 Mb windows
        step_size=500_000,  # 500 kb step
        min_markers=3,
    )

    results = estimator.estimate(
        vcf_path=vcf_path,
        markers=markers,
        populations=populations,
    )
    print(f"  Processed {results.n_windows} windows")

    # Save window results
    windows_path = output_dir / "haplotype_proportions.tsv"
    results.to_tsv(windows_path)
    print(f"  Saved to {windows_path}")

    # Step 4: Calculate genome-wide statistics
    print("\nGenome-wide proportions:")
    genome_props = results.genome_wide_proportions()
    for sample, props in genome_props.items():
        print(f"\n  {sample}:")
        for founder, proportion in sorted(props.items()):
            print(f"    {founder}: {proportion:.1%}")

    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
