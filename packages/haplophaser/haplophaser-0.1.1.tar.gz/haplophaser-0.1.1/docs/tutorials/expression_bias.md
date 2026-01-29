# Expression Bias Analysis Tutorial

This tutorial walks through analyzing homeolog expression bias in a paleopolyploid genome using RNA-seq data.

## Overview

In paleopolyploid genomes like maize, most genes have a homeologous partner from the ancient whole-genome duplication (WGD). These homeolog pairs often show biased expression, where one copy is expressed more highly than the other. Haplophaser quantifies this bias and tests for genome-wide subgenome dominance.

## Prerequisites

- Haplophaser installed
- Expression matrix (TPM or counts)
- Homeolog pairs file
- Sample metadata (optional but recommended)

## Input Data

### Expression Matrix

A TSV file with genes as rows and samples as columns:

```
gene_id    control_1    control_2    drought_1    drought_2
Zm00001d001001    15.2    14.8    12.3    11.9
Zm00001d001002    8.5    9.2    10.5    11.2
...
```

### Homeolog Pairs

A TSV file defining homeologous gene pairs:

```
gene1_id    gene1_chrom    gene1_subgenome    gene2_id    gene2_chrom    gene2_subgenome    ks
Zm00001d001001    chr1    maize1    Zm00001d001002    chr5    maize2    0.15
...
```

### Sample Metadata (Optional)

```
sample_id    condition    tissue    replicate
control_1    control    leaf    1
control_2    control    leaf    2
drought_1    drought    leaf    1
drought_2    drought    leaf    2
```

## Step 1: Load and Explore Data

### Using Python API

```python
from haplophaser.io.expression import load_expression_matrix, parse_sample_metadata

# Load metadata
metadata = parse_sample_metadata("sample_metadata.tsv")

# Load expression matrix
expr_matrix = load_expression_matrix(
    "expression_matrix.tsv",
    sample_metadata=metadata
)

print(f"Loaded {expr_matrix.n_genes} genes, {expr_matrix.n_samples} samples")
print(f"Conditions: {expr_matrix.conditions()}")
```

### Supported Input Formats

Haplophaser supports multiple expression data formats:

- **TPM/FPKM matrices** - Tab-separated files
- **Salmon** - `quant.sf` files
- **Kallisto** - `abundance.tsv` files
- **featureCounts** - Direct output

## Step 2: Extract Homeolog Expression

```python
from haplophaser.expression.homeolog_expression import extract_homeolog_expression

homeolog_expr = extract_homeolog_expression(
    expr_matrix,
    "homeolog_pairs.tsv",
    min_mean_expr=1.0,  # Filter lowly expressed pairs
)

print(f"Extracted {homeolog_expr.n_pairs} homeolog pairs")
```

Each homeolog pair contains:
- Expression values for both genes across all samples
- Calculated log2 ratios
- Mean expression values

## Step 3: Calculate Expression Bias

```python
from haplophaser.expression.bias import calculate_expression_bias

bias_result = calculate_expression_bias(
    homeolog_expr,
    min_expr=1.0,          # Minimum TPM for "expressed"
    log2_threshold=1.0,    # |log2 ratio| for significant bias
    test_method="paired_t" # Statistical test
)

# View summary
summary = bias_result.summary()
print(f"Total pairs: {summary['n_pairs']}")
print(f"Significantly biased: {summary['n_significant']}")
print(f"SG1 dominant: {summary['n_sg1_dominant']}")
print(f"SG2 dominant: {summary['n_sg2_dominant']}")
```

### Bias Categories

Pairs are classified into categories:

| Category | Description |
|----------|-------------|
| `sg1_dominant` | Gene1 (SG1) significantly higher |
| `sg2_dominant` | Gene2 (SG2) significantly higher |
| `balanced` | No significant bias |
| `sg1_only` | Only gene1 expressed |
| `sg2_only` | Only gene2 expressed |
| `silent` | Neither gene expressed |

## Step 4: Test Subgenome Dominance

Test whether one subgenome has more highly expressed copies genome-wide:

```python
from haplophaser.expression.dominance import test_subgenome_dominance

dominance = test_subgenome_dominance(bias_result, min_significant=10)

print(f"Chi-square: {dominance.chi2_statistic:.2f}")
print(f"P-value: {dominance.pvalue:.2e}")
if dominance.dominant_subgenome:
    print(f"Dominant subgenome: {dominance.dominant_subgenome}")
```

## Step 5: Condition-Specific Analysis

Compare bias between experimental conditions:

```python
from haplophaser.expression.condition_bias import ConditionBiasAnalyzer

analyzer = ConditionBiasAnalyzer()

# Compare control vs drought
comparison = analyzer.compare_conditions(
    expr_matrix,
    "homeolog_pairs.tsv",
    condition1="control",
    condition2="drought"
)

print(f"Pairs with differential bias: {comparison.n_differential}")
print(f"Pairs with category change: {comparison.n_category_changed}")
```

This identifies homeologs where bias shifts between conditions (e.g., balanced in control but SG1-dominant in drought).

## Step 6: Generate Reports

```python
from haplophaser.expression.report import generate_expression_report

report = generate_expression_report(
    homeolog_expr=homeolog_expr,
    bias_result=bias_result,
    output_dir="expression_report",
    dominance_result=dominance,
)
```

This generates:
- `expression_report.md` - Markdown summary
- `expression_report.json` - Machine-readable results
- `expression_summary.tsv` - Summary statistics

## Using the CLI

All steps can be run from the command line:

```bash
# Full analysis with report
haplophaser expression-report \
    expression_matrix.tsv \
    homeolog_pairs.tsv \
    --metadata sample_metadata.tsv \
    --output-dir expression_results

# Just bias calculation
haplophaser expression-bias \
    expression_matrix.tsv \
    homeolog_pairs.tsv \
    --output bias_results.tsv

# Condition comparison
haplophaser expression-condition \
    expression_matrix.tsv \
    homeolog_pairs.tsv \
    sample_metadata.tsv \
    --condition1 control \
    --condition2 drought \
    --output-dir condition_comparison
```

## Interpreting Results

### Log2 Ratio

- Positive: Gene1 (subgenome 1) higher
- Negative: Gene2 (subgenome 2) higher
- ~0: Balanced expression

### Statistical Significance

- FDR < 0.05: Significant bias
- Multiple testing correction applied

### Subgenome Dominance

- Tests if biased pairs favor one subgenome
- Significant p-value indicates genome-wide bias
- Effect size indicates magnitude

## Best Practices

1. **Filter lowly expressed genes** - Set `min_expr` appropriately
2. **Use biological replicates** - At least 3 per condition
3. **Check for batch effects** - May confound condition comparisons
4. **Validate key findings** - RT-qPCR confirmation recommended

## Visualization

Export data for visualization tools:

```python
from haplophaser.expression.viz import ExpressionVizPrep

viz = ExpressionVizPrep()

# MA plot data
ma_data = viz.bias_ma_plot(bias_result)

# Category distribution
bar_data = viz.bias_category_bar(bias_result)

# For chromoplot integration
from haplophaser.expression.viz import prepare_chromoplot_data

chromoplot_data = prepare_chromoplot_data(
    bias_result,
    gene_positions=gene_position_dict
)
```

## Next Steps

- [Subgenome Analysis Tutorial](subgenome_analysis.md) - Generate homeolog pairs
- [File Formats](../file_formats.md) - Input/output specifications
- [API Reference](../api/expression.md) - Detailed API documentation
