#!/bin/bash
# Maize NAM Haplotype Analysis Example
#
# This script runs a complete haplotype proportion analysis
# on maize NAM data.

set -e

echo "=== Maize NAM Haplotype Analysis ==="
echo ""

# Create results directory
mkdir -p results

# Step 1: Find diagnostic markers
echo "Step 1: Finding diagnostic markers..."
phaser find-markers \
    --vcf data/nam_founders_chr1.vcf.gz \
    --populations data/populations.tsv \
    --min-freq-diff 0.7 \
    --output-prefix results/markers

echo "  Found markers: $(wc -l < results/markers.tsv) variants"
echo ""

# Step 2: Estimate haplotype proportions in RILs
echo "Step 2: Estimating haplotype proportions..."
phaser proportion \
    --vcf data/nam_rils_chr1.vcf.gz \
    --markers results/markers.tsv \
    --populations data/populations.tsv \
    --window-size 1000000 \
    --call-blocks \
    --output-prefix results/proportions

echo "  Windows analyzed: $(wc -l < results/proportions_windows.tsv)"
echo "  Blocks called: $(grep -v '^#' results/proportions_blocks.bed | wc -l)"
echo ""

# Step 3: Create visualizations
echo "Step 3: Creating visualizations..."

# Single chromosome view
phaser viz proportions \
    -h results/proportions_blocks.bed \
    -r data/Zm-B73-v5.fa.fai \
    --region chr1 \
    --founders B73,Mo17,W22 \
    --title "Chromosome 1 Haplotype Blocks" \
    -o results/chr1_haplotypes.pdf

echo "  Created: results/chr1_haplotypes.pdf"

# Whole genome view (if data available)
if [ -f "data/Zm-B73-v5.fa.fai" ]; then
    phaser viz genome \
        -h results/proportions_blocks.bed \
        -r data/Zm-B73-v5.fa.fai \
        --founders B73,Mo17,W22 \
        --cols 5 \
        -o results/genome_haplotypes.pdf
    echo "  Created: results/genome_haplotypes.pdf"
fi

echo ""
echo "=== Analysis Complete ==="
echo ""
echo "Results in results/:"
ls -la results/
