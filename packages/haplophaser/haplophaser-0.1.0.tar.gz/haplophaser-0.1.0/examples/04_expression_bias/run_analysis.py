#!/usr/bin/env python3
"""
Expression Bias Analysis Example

This script demonstrates a complete workflow for analyzing
homeolog expression bias and testing subgenome dominance.
"""

from pathlib import Path

from haplophaser.expression.bias import calculate_expression_bias
from haplophaser.expression.condition_bias import ConditionBiasAnalyzer
from haplophaser.expression.dominance import test_subgenome_dominance
from haplophaser.expression.homeolog_expression import extract_homeolog_expression
from haplophaser.io.expression import load_expression_matrix, parse_sample_metadata


def main():
    # Configuration
    data_dir = Path("../data")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    expr_path = data_dir / "expression_matrix.tsv"
    metadata_path = data_dir / "sample_metadata.tsv"
    homeologs_path = data_dir / "homeolog_pairs.tsv"

    # Step 1: Load expression data
    print("Loading expression data...")
    metadata = parse_sample_metadata(metadata_path)
    expr_matrix = load_expression_matrix(expr_path, sample_metadata=metadata)
    print(f"  Genes: {expr_matrix.n_genes}")
    print(f"  Samples: {expr_matrix.n_samples}")
    print(f"  Conditions: {expr_matrix.conditions()}")

    # Step 2: Extract homeolog expression
    print("\nExtracting homeolog expression...")
    homeolog_expr = extract_homeolog_expression(
        expr_matrix,
        homeologs_path,
        min_mean_expr=1.0,  # Filter lowly expressed pairs
    )
    print(f"  Homeolog pairs: {homeolog_expr.n_pairs}")

    # Step 3: Calculate expression bias
    print("\nCalculating expression bias...")
    bias_result = calculate_expression_bias(
        homeolog_expr,
        min_expr=1.0,
        log2_threshold=1.0,
        test_method="paired_t",
    )

    # Print summary
    summary = bias_result.summary()
    print("\n  Bias Summary:")
    print(f"    Total pairs: {summary['n_pairs']}")
    print(f"    Significantly biased: {summary['n_significant']}")
    print(f"    SG1 dominant: {summary['n_sg1_dominant']}")
    print(f"    SG2 dominant: {summary['n_sg2_dominant']}")
    print(f"    Balanced: {summary['n_balanced']}")

    # Save bias results
    bias_path = output_dir / "expression_bias.tsv"
    bias_result.to_tsv(bias_path)
    print(f"\n  Saved to {bias_path}")

    # Step 4: Test subgenome dominance
    print("\nTesting subgenome dominance...")
    dominance = test_subgenome_dominance(bias_result, min_significant=10)

    print(f"  Chi-square statistic: {dominance.chi2_statistic:.2f}")
    print(f"  P-value: {dominance.pvalue:.2e}")
    if dominance.is_significant:
        print(f"  Dominant subgenome: {dominance.dominant_subgenome}")
        print(f"  Effect size: {dominance.effect_size:.2f}")
    else:
        print("  No significant dominance detected")

    # Save dominance results
    dominance_path = output_dir / "dominance_result.txt"
    with open(dominance_path, "w") as f:
        f.write(f"Chi-square: {dominance.chi2_statistic:.4f}\n")
        f.write(f"P-value: {dominance.pvalue:.2e}\n")
        f.write(f"Significant: {dominance.is_significant}\n")
        if dominance.dominant_subgenome:
            f.write(f"Dominant: {dominance.dominant_subgenome}\n")
    print(f"  Saved to {dominance_path}")

    # Step 5: Condition-specific analysis
    print("\nComparing conditions...")
    analyzer = ConditionBiasAnalyzer()

    comparison = analyzer.compare_conditions(
        expr_matrix,
        homeologs_path,
        condition1="control",
        condition2="drought",
    )

    print(f"  Pairs with differential bias: {comparison.n_differential}")
    print(f"  Pairs with category change: {comparison.n_category_changed}")

    # Save condition comparison
    condition_path = output_dir / "condition_comparison.tsv"
    comparison.to_tsv(condition_path)
    print(f"  Saved to {condition_path}")

    # List top changed pairs
    if comparison.n_category_changed > 0:
        print("\n  Top category changes:")
        for pair in comparison.changed_pairs[:5]:
            print(f"    {pair.pair_id}: {pair.category1} -> {pair.category2}")

    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
