# Maize NAM Haplotype Analysis

This example demonstrates haplotype proportion analysis using maize NAM (Nested Association Mapping) data.

## Overview

The analysis:

1. Identifies diagnostic markers that distinguish NAM founders
2. Estimates haplotype proportions in RIL (Recombinant Inbred Line) samples
3. Calls haplotype blocks
4. Generates visualization figures

## Input Files

| File | Description |
|------|-------------|
| `data/nam_founders_chr1.vcf.gz` | VCF with NAM founder genotypes |
| `data/nam_rils_chr1.vcf.gz` | VCF with RIL genotypes |
| `data/populations.tsv` | Sample population assignments |
| `data/Zm-B73-v5.fa.fai` | Reference genome index |

## Running the Analysis

### Shell Script

```bash
./run.sh
```

### Python Script

```bash
python run.py
```

### Step by Step

```bash
# 1. Find diagnostic markers
phaser find-markers \
    --vcf data/nam_founders_chr1.vcf.gz \
    --populations data/populations.tsv \
    --min-freq-diff 0.7 \
    --output-prefix results/markers

# 2. Estimate haplotype proportions
phaser proportion \
    --vcf data/nam_rils_chr1.vcf.gz \
    --markers results/markers.tsv \
    --populations data/populations.tsv \
    --window-size 1000000 \
    --output-prefix results/proportions

# 3. Visualize results
phaser viz proportions \
    -h results/proportions_blocks.bed \
    -r data/Zm-B73-v5.fa.fai \
    --region chr1 \
    -o results/chr1_haplotypes.pdf
```

## Output Files

| File | Description |
|------|-------------|
| `results/markers.tsv` | Diagnostic markers |
| `results/markers.bed` | Markers in BED format |
| `results/proportions_windows.tsv` | Per-window proportions |
| `results/proportions_blocks.bed` | Haplotype blocks |
| `results/chr1_haplotypes.pdf` | Visualization |

## Expected Results

- Diagnostic markers: ~5,000-10,000 per chromosome
- Haplotype blocks: 10-50 per chromosome per sample
- Recombination breakpoints: 5-15 per chromosome

## Interpreting Results

### Proportions File

```
sample    chrom    start      end        B73      Mo17     ...
RIL_001   chr1     0          1000000    0.95     0.02     ...
RIL_001   chr1     1000000    2000000    0.85     0.10     ...
```

Each row shows the proportion of each founder in a genomic window.

### Haplotype Blocks

```
chr1    0          2500000    B73    1000    .
chr1    2500000    5000000    Mo17   1000    .
```

Contiguous regions assigned to a single founder.

## Customization

Edit `config.yaml` to adjust:

- Window size
- Minimum marker count
- Proportion threshold for block calling
- Founder colors for visualization

## Reference

For more details on NAM population genetics, see:

- McMullen et al. (2009) Science
- Chia et al. (2012) Nature Genetics
