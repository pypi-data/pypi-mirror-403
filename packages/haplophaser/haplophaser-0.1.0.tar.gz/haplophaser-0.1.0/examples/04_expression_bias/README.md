# Expression Bias Analysis

This example demonstrates analyzing homeolog expression bias and testing for subgenome dominance in RNA-seq data.

## Overview

The workflow:
1. Load expression matrix and sample metadata
2. Extract expression values for homeolog pairs
3. Calculate expression bias statistics
4. Test for genome-wide subgenome dominance
5. Compare bias between experimental conditions

## Input Files

Required files in `../data/`:
- `expression_matrix.tsv` - Gene expression values (TPM)
- `sample_metadata.tsv` - Sample condition assignments
- `homeolog_pairs.tsv` - Homeologous gene pairs

## Running the Example

### Using Python

```bash
cd examples/04_expression_bias
python run_analysis.py
```

### Using CLI

```bash
# Calculate expression bias
phaser expression-bias \
    ../data/expression_matrix.tsv \
    ../data/homeolog_pairs.tsv \
    --metadata ../data/sample_metadata.tsv \
    --output output/expression_bias.tsv

# Test subgenome dominance
phaser expression-dominance \
    output/expression_bias.tsv \
    --output output/dominance_result.txt

# Compare conditions
phaser expression-condition \
    ../data/expression_matrix.tsv \
    ../data/homeolog_pairs.tsv \
    ../data/sample_metadata.tsv \
    --condition1 control \
    --condition2 drought \
    --output-dir output/condition_comparison

# Generate full report
phaser expression-report \
    ../data/expression_matrix.tsv \
    ../data/homeolog_pairs.tsv \
    --metadata ../data/sample_metadata.tsv \
    --output-dir output/report
```

## Output Files

- `output/expression_bias.tsv` - Per-pair bias statistics
- `output/dominance_result.txt` - Subgenome dominance test results
- `output/condition_comparison.tsv` - Differential bias between conditions

## Interpreting Results

### Bias Categories

| Category | Description |
|----------|-------------|
| sg1_dominant | Subgenome 1 copy expressed higher |
| sg2_dominant | Subgenome 2 copy expressed higher |
| balanced | No significant difference |
| sg1_only | Only subgenome 1 copy expressed |
| sg2_only | Only subgenome 2 copy expressed |

### Subgenome Dominance

- Significant p-value (< 0.05) indicates genome-wide bias
- Effect size indicates magnitude of the bias
- Positive effect = SG1 dominant, negative = SG2 dominant

### Condition Comparison

Identifies homeologs where expression bias changes between conditions, such as:
- Balanced in control, but biased under stress
- Reversal of bias direction
- Gain/loss of expression in one copy
