# Quick Start

This guide walks through basic phaser analyses using example data.

## Prerequisites

- Phaser installed (`pip install haplophaser`)
- VCF file with samples
- Population assignment file

## Haplotype Proportion Analysis

### Step 1: Prepare Population File

Create a TSV file assigning samples to populations:

```tsv
sample	population	role	ploidy
B73	B73	founder	2
Mo17	Mo17	founder	2
W22	W22	founder	2
RIL_001	derived	derived	2
RIL_002	derived	derived	2
```

For NAM-style data, each founder is its own population.

### Step 2: Find Diagnostic Markers

```bash
haplophaser find-markers \
    --vcf your_data.vcf.gz \
    --populations populations.tsv \
    --min-freq-diff 0.7 \
    --output-prefix diagnostic_markers
```

This identifies variants that distinguish founders.

### Step 3: Estimate Proportions

```bash
haplophaser proportion \
    --vcf your_data.vcf.gz \
    --markers diagnostic_markers.tsv \
    --populations populations.tsv \
    --window-size 1000000 \
    --output-prefix haplotype_proportions
```

Outputs:
- `haplotype_proportions_windows.tsv` - Per-window proportions
- `haplotype_proportions_blocks.bed` - Haplotype blocks

## Subgenome Analysis

### Step 1: Assign Subgenomes

Using synteny with a reference genome that has known subgenome assignments:

```bash
haplophaser subgenome-assign \
    --assembly query.fasta \
    --reference reference.fasta \
    --reference-assignments known_subgenomes.bed \
    --method synteny \
    --output-dir subgenome_results
```

### Step 2: Analyze Fractionation

```bash
haplophaser subgenome-fractionation \
    --genes genes.gff3 \
    --assignments subgenome_results/subgenome.bed \
    --species maize \
    --output fractionation_report.tsv
```

## Expression Bias Analysis

### Step 1: Prepare Data

You need:
- Expression matrix (TPM values, genes × samples)
- Homeolog pairs file
- Sample metadata (conditions, tissues)

### Step 2: Calculate Expression Bias

```bash
haplophaser expression-bias \
    expression_matrix.tsv \
    homeolog_pairs.tsv \
    --output expression_bias.tsv \
    --metadata sample_metadata.tsv
```

### Step 3: Test Subgenome Dominance

```bash
haplophaser expression-dominance \
    expression_bias.tsv \
    --output dominance_result.txt
```

### Step 4: Generate Full Report

```bash
haplophaser expression-report \
    expression_matrix.tsv \
    homeolog_pairs.tsv \
    --metadata sample_metadata.tsv \
    --output-dir expression_report
```

## Python API Quick Start

```python
from haplophaser.io.populations import load_populations
from haplophaser.io.vcf import load_vcf
from haplophaser.markers.diagnostic import DiagnosticMarkerFinder

# Load populations
populations = load_populations("populations.tsv")

# Find diagnostic markers
finder = DiagnosticMarkerFinder(min_freq_diff=0.7)
markers = finder.find_from_vcf("data.vcf.gz", populations)

print(f"Found {len(markers)} diagnostic markers")
```

## Next Steps

- [Haplotype Proportion Tutorial](tutorials/haplotype_proportion.md) - Detailed walkthrough
- [Assembly Painting Tutorial](tutorials/assembly_painting.md) - Assign contigs to haplotypes
- [Subgenome Analysis Tutorial](tutorials/subgenome_analysis.md) - Deconvolute paleopolyploids
- [Expression Bias Tutorial](tutorials/expression_bias.md) - Analyze homeolog expression
