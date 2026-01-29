# Haplotype Proportion Estimation Tutorial

This tutorial walks through estimating founder haplotype proportions in derived lines using VCF data.

## Overview

In breeding programs, derived lines (RILs, NILs, etc.) contain mosaic genomes with segments inherited from different founder parents. Haplophaser quantifies these founder contributions across the genome using diagnostic markers.

## Prerequisites

- Haplophaser installed
- VCF file with founder and derived samples
- Population assignment file

## Input Data

### VCF File

A bgzipped and indexed VCF file containing:
- All founder samples
- All derived samples to analyze
- Genotype calls (GT field required)

```bash
# Index your VCF if needed
bgzip variants.vcf
tabix -p vcf variants.vcf.gz
```

### Population File

A TSV file assigning samples to populations:

```tsv
sample	population	role	ploidy
B73	B73	founder	2
Mo17	Mo17	founder	2
W22	W22	founder	2
RIL_001	derived	derived	2
RIL_002	derived	derived	2
```

**Key points:**
- Each founder typically gets its own population name
- All derived samples share the population name "derived"
- The `role` column distinguishes founders from derived

## Step 1: Find Diagnostic Markers

Diagnostic markers are variants that distinguish between founders.

### Using CLI

```bash
haplophaser find-markers \
    --vcf founders_and_derived.vcf.gz \
    --populations populations.tsv \
    --min-freq-diff 0.7 \
    --output-prefix diagnostic_markers
```

### Using Python API

```python
from haplophaser.io.populations import load_populations
from haplophaser.markers.diagnostic import DiagnosticMarkerFinder

# Load populations
populations = load_populations("populations.tsv")

# Configure marker finder
finder = DiagnosticMarkerFinder(
    min_freq_diff=0.7,      # Minimum allele frequency difference
    min_samples=1,          # Minimum samples per population
    max_missing=0.2,        # Maximum missing rate
    min_maf=0.05,           # Minimum minor allele frequency
)

# Find markers
markers = finder.find_from_vcf("data.vcf.gz", populations)

print(f"Found {len(markers)} diagnostic markers")

# Save markers
finder.save_markers(markers, "diagnostic_markers.tsv")
```

### Understanding Marker Output

The output file contains:

| Column | Description |
|--------|-------------|
| chrom | Chromosome |
| pos | Position |
| ref | Reference allele |
| alt | Alternate allele |
| founder1 | First distinguishing founder |
| founder2 | Second distinguishing founder |
| freq_diff | Allele frequency difference |

## Step 2: Estimate Window Proportions

Estimate founder contributions in sliding windows across the genome.

### Using CLI

```bash
haplophaser proportion \
    --vcf founders_and_derived.vcf.gz \
    --markers diagnostic_markers.tsv \
    --populations populations.tsv \
    --window-size 1000000 \
    --step-size 500000 \
    --output-prefix haplotype_proportions
```

### Using Python API

```python
from haplophaser.proportion.window import WindowProportionEstimator

estimator = WindowProportionEstimator(
    window_size=1_000_000,  # 1 Mb windows
    step_size=500_000,      # 500 kb step (overlapping)
    min_markers=3,          # Minimum markers per window
    method="weighted",      # Weighting method
)

# Estimate proportions
results = estimator.estimate(
    vcf_path="data.vcf.gz",
    markers=markers,
    populations=populations,
)

# Save results
results.to_tsv("haplotype_proportions_windows.tsv")

# Examine results
for sample in results.samples:
    print(f"\nSample: {sample}")
    sample_results = results.get_sample(sample)
    for window in sample_results.windows[:5]:  # First 5 windows
        print(f"  {window.chrom}:{window.start}-{window.end}")
        for founder, prop in window.proportions.items():
            print(f"    {founder}: {prop:.2f}")
```

### Window Output Format

```tsv
sample	chrom	start	end	n_markers	B73	Mo17	W22
RIL_001	chr1	0	1000000	15	0.85	0.10	0.05
RIL_001	chr1	500000	1500000	18	0.82	0.12	0.06
```

## Step 3: Infer Haplotype Blocks (Optional)

Use HMM to infer discrete haplotype blocks from window proportions.

### Using CLI

```bash
haplophaser haplotype-blocks \
    --proportions haplotype_proportions_windows.tsv \
    --genetic-map genetic_map.tsv \
    --min-block-size 100000 \
    --output haplotype_blocks.bed
```

### Using Python API

```python
from haplophaser.proportion.hmm import HaplotypeHMM
from haplophaser.io.genetic_map import load_genetic_map

# Load genetic map (optional but recommended)
genetic_map = load_genetic_map("genetic_map.tsv")

# Configure HMM
hmm = HaplotypeHMM(
    n_states=3,              # Number of founders
    transition_rate=0.001,   # Base transition probability
    genetic_map=genetic_map, # Use genetic distances
)

# Infer blocks
blocks = hmm.infer_blocks(results)

# Print blocks
for block in blocks:
    print(f"{block.sample}\t{block.chrom}:{block.start}-{block.end}\t{block.haplotype}\t{block.confidence:.2f}")

# Save as BED
blocks.to_bed("haplotype_blocks.bed")
```

### Block Output Format

BED format with sample in the name field:

```
chr1	0	5000000	B73	0.95	RIL_001
chr1	5000000	8000000	Mo17	0.88	RIL_001
chr1	8000000	15000000	B73	0.92	RIL_001
```

## Step 4: Calculate Genome-Wide Statistics

Summarize founder contributions across the genome.

```python
# Get genome-wide proportions
genome_props = results.genome_wide_proportions()

for sample, props in genome_props.items():
    print(f"\n{sample}:")
    for founder, proportion in props.items():
        print(f"  {founder}: {proportion:.1%}")

# Expected output for RIL:
# RIL_001:
#   B73: 48.5%
#   Mo17: 51.2%
#   W22: 0.3%
```

## Advanced Options

### Multi-Founder Analysis

For populations with more than 2 founders:

```python
finder = DiagnosticMarkerFinder(
    min_freq_diff=0.5,      # Lower threshold for multi-founder
    require_biallelic=True, # Stick to biallelic markers
)
```

### Using Genetic Map

Genetic maps improve HMM accuracy by accounting for recombination rate variation:

```python
from haplophaser.io.genetic_map import load_genetic_map

genetic_map = load_genetic_map("genetic_map.tsv")

hmm = HaplotypeHMM(
    n_states=3,
    genetic_map=genetic_map,  # Uses cM for transitions
)
```

### Parallelization

Process chromosomes in parallel:

```bash
haplophaser proportion \
    --vcf data.vcf.gz \
    --markers markers.tsv \
    --populations pops.tsv \
    --threads 8 \
    --output-prefix results
```

## Interpreting Results

### Window Proportions

- Values sum to 1.0 within each window
- High values (>0.8) indicate clear haplotype
- Mixed values suggest recombination or noise

### Haplotype Blocks

- Longer blocks indicate fewer recombination events
- Block boundaries may indicate recombination breakpoints
- Low confidence blocks may indicate heterozygosity or noise

### Troubleshooting

**Few diagnostic markers found:**
- Lower `min_freq_diff` threshold
- Check that founders are genetically distinct
- Ensure VCF has sufficient coverage

**Noisy proportion estimates:**
- Increase window size
- Require more markers per window
- Check for sample contamination

**Inconsistent block calls:**
- Adjust HMM transition rate
- Use genetic map if available
- Check for structural variants

## Next Steps

- [Assembly Painting Tutorial](assembly_painting.md) - Paint assemblies by haplotype
- [File Formats](../file_formats.md) - Detailed format specifications
- [CLI Reference](../cli/index.md) - All command options
