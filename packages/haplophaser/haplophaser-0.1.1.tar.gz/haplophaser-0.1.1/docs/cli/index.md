# CLI Reference

Haplophaser provides a command-line interface for all major analyses.

## Global Options

All commands support these global options:

```
--help          Show help message and exit
--version       Show version and exit
--verbose, -v   Increase verbosity (can be repeated)
--quiet, -q     Suppress non-error output
--threads, -t   Number of threads to use (default: 1)
```

## Commands

### Marker Discovery

#### find-markers

Find diagnostic markers that distinguish founder populations.

```bash
haplophaser find-markers \
    --vcf <vcf_file> \
    --populations <pop_file> \
    --output-prefix <prefix> \
    [options]
```

**Required arguments:**
- `--vcf` - Input VCF file (bgzipped and indexed)
- `--populations` - Population assignment file
- `--output-prefix` - Prefix for output files

**Options:**
- `--min-freq-diff` - Minimum allele frequency difference (default: 0.7)
- `--min-samples` - Minimum samples per population (default: 1)
- `--max-missing` - Maximum missing rate (default: 0.2)
- `--min-maf` - Minimum minor allele frequency (default: 0.05)
- `--region` - Restrict to genomic region (chr:start-end)

**Output files:**
- `<prefix>_markers.tsv` - Diagnostic markers
- `<prefix>_summary.txt` - Summary statistics

---

### Haplotype Analysis

#### proportion

Estimate haplotype proportions in windows.

```bash
haplophaser proportion \
    --vcf <vcf_file> \
    --markers <marker_file> \
    --populations <pop_file> \
    --output-prefix <prefix> \
    [options]
```

**Required arguments:**
- `--vcf` - Input VCF file
- `--markers` - Diagnostic markers file
- `--populations` - Population file
- `--output-prefix` - Output prefix

**Options:**
- `--window-size` - Window size in bp (default: 1000000)
- `--step-size` - Step size in bp (default: window-size)
- `--min-markers` - Minimum markers per window (default: 3)
- `--method` - Estimation method: simple, weighted, bayesian (default: weighted)

**Output files:**
- `<prefix>_windows.tsv` - Per-window proportions
- `<prefix>_genome.tsv` - Genome-wide proportions

#### haplotype-blocks

Infer haplotype blocks using HMM.

```bash
haplophaser haplotype-blocks \
    --proportions <proportions_file> \
    --output <output_file> \
    [options]
```

**Options:**
- `--genetic-map` - Genetic map file for recombination rates
- `--transition-rate` - Base transition rate (default: 0.001)
- `--min-block-size` - Minimum block size in bp (default: 100000)
- `--min-confidence` - Minimum block confidence (default: 0.8)

---

### Assembly Analysis

#### assembly-paint

Paint assembly contigs by haplotype.

```bash
haplophaser assembly-paint \
    --assembly <fasta_file> \
    --markers <marker_file> \
    --output-dir <directory> \
    [options]
```

**Required arguments:**
- `--assembly` - Assembly FASTA file
- `--markers` - Diagnostic markers file
- `--output-dir` - Output directory

**Options:**
- `--min-markers` - Minimum markers per contig (default: 3)
- `--min-confidence` - Minimum assignment confidence (default: 0.7)
- `--detect-chimeras` - Enable chimera detection (default: true)
- `--chimera-window` - Window size for chimera detection (default: 100000)

**Output files:**
- `contig_assignments.tsv` - Per-contig haplotype assignments
- `chimeric_contigs.tsv` - Potential chimeric contigs
- `painting_summary.txt` - Summary statistics

---

### Subgenome Analysis

#### subgenome-assign

Assign genomic regions to subgenomes.

```bash
haplophaser subgenome-assign \
    --assembly <fasta_file> \
    --reference <ref_fasta> \
    --reference-assignments <bed_file> \
    --output-dir <directory> \
    [options]
```

**Options:**
- `--method` - Assignment method: synteny, ortholog, integrated (default: integrated)
- `--min-synteny-genes` - Minimum genes for synteny block (default: 5)
- `--min-confidence` - Minimum assignment confidence (default: 0.7)
- `--species` - Species preset: maize, wheat, brassica

#### subgenome-fractionation

Analyze gene fractionation between subgenomes.

```bash
haplophaser subgenome-fractionation \
    --genes <gff_file> \
    --assignments <bed_file> \
    --output <output_file> \
    [options]
```

**Options:**
- `--ancestral-genes` - Ancestral gene count file
- `--species` - Species preset
- `--by-chromosome` - Report by chromosome

---

### Expression Analysis

#### expression-bias

Calculate homeolog expression bias.

```bash
haplophaser expression-bias \
    <expression_matrix> \
    <homeolog_pairs> \
    --output <output_file> \
    [options]
```

**Required arguments:**
- `expression_matrix` - Expression matrix file (TSV)
- `homeolog_pairs` - Homeolog pairs file

**Options:**
- `--metadata` - Sample metadata file
- `--min-expr` - Minimum expression threshold (default: 1.0)
- `--log2-threshold` - Log2 ratio threshold for bias (default: 1.0)
- `--test-method` - Statistical test: paired_t, wilcoxon (default: paired_t)
- `--condition` - Analyze specific condition only

#### expression-dominance

Test for subgenome dominance.

```bash
haplophaser expression-dominance \
    <bias_results> \
    --output <output_file> \
    [options]
```

**Options:**
- `--min-significant` - Minimum significant pairs for test (default: 10)
- `--method` - Test method: chi_square, binomial (default: chi_square)

#### expression-condition

Compare expression bias between conditions.

```bash
haplophaser expression-condition \
    <expression_matrix> \
    <homeolog_pairs> \
    <sample_metadata> \
    --condition1 <cond1> \
    --condition2 <cond2> \
    --output-dir <directory> \
    [options]
```

**Options:**
- `--min-expr` - Minimum expression threshold
- `--fdr-threshold` - FDR threshold for significance (default: 0.05)

#### expression-report

Generate comprehensive expression analysis report.

```bash
haplophaser expression-report \
    <expression_matrix> \
    <homeolog_pairs> \
    --output-dir <directory> \
    [options]
```

**Options:**
- `--metadata` - Sample metadata file
- `--all-conditions` - Analyze all conditions separately
- `--format` - Report format: markdown, html, json (default: markdown)

---

### Utility Commands

#### check-input

Validate input files.

```bash
haplophaser check-input \
    --type <file_type> \
    <input_file>
```

**File types:**
- `populations` - Population assignment file
- `expression` - Expression matrix
- `homeologs` - Homeolog pairs file
- `markers` - Diagnostic markers file
- `vcf` - VCF file

#### version

Show version information.

```bash
haplophaser version
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Input file error |
| 4 | Output file error |
| 5 | Validation error |

## Environment Variables

- `PHASER_THREADS` - Default thread count
- `PHASER_CACHE_DIR` - Cache directory location
- `PHASER_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
