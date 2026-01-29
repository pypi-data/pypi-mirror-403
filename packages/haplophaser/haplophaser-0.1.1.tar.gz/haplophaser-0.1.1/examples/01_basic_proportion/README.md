# Basic Haplotype Proportion Analysis

This example demonstrates estimating founder haplotype proportions in derived lines using VCF data.

## Overview

The workflow:
1. Load population assignments
2. Find diagnostic markers that distinguish founders
3. Estimate founder proportions in sliding windows
4. Calculate genome-wide statistics

## Input Files

Required files in `../data/`:
- `example_variants.vcf.gz` - VCF with founder and derived samples
- `populations.tsv` - Sample population assignments

## Running the Example

### Using Python

```bash
cd examples/01_basic_proportion
python run_analysis.py
```

### Using CLI

```bash
# Find diagnostic markers
phaser find-markers \
    --vcf ../data/example_variants.vcf.gz \
    --populations ../data/populations.tsv \
    --min-freq-diff 0.7 \
    --output-prefix output/markers

# Estimate proportions
phaser proportion \
    --vcf ../data/example_variants.vcf.gz \
    --markers output/markers_markers.tsv \
    --populations ../data/populations.tsv \
    --window-size 1000000 \
    --output-prefix output/proportions
```

## Output Files

- `output/diagnostic_markers.tsv` - Markers distinguishing founders
- `output/haplotype_proportions.tsv` - Per-window proportion estimates

## Expected Results

For RIL samples, you should see:
- ~50% contribution from each parent (for biparental RILs)
- Variation across windows reflecting recombination
- Clear haplotype blocks in individual chromosomes
