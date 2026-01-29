# File Formats

This document describes all input and output file formats used by Haplophaser.

## Input Formats

### Population File

Tab-separated file defining sample populations and roles.

**Required columns:**
- `sample` - Sample identifier (must match VCF sample names)
- `population` - Population assignment
- `role` - Either `founder` or `derived`

**Optional columns:**
- `ploidy` - Ploidy level (default: 2)
- `group` - Grouping for multi-family analyses

**Example:**
```tsv
sample	population	role	ploidy
B73	B73	founder	2
Mo17	Mo17	founder	2
W22	W22	founder	2
RIL_001	derived	derived	2
RIL_002	derived	derived	2
```

### Genetic Map File

Tab-separated file with genetic map positions.

**Required columns:**
- `marker_id` - Marker identifier
- `chrom` - Chromosome name
- `pos` - Physical position (bp)
- `cM` - Genetic position (centiMorgans)

**Example:**
```tsv
marker_id	chrom	pos	cM
marker_001	chr1	1000000	0.5
marker_002	chr1	2000000	1.2
marker_003	chr1	5000000	3.1
```

### Homeolog Pairs File

Tab-separated file defining homeologous gene pairs.

**Required columns:**
- `gene1_id` - Gene identifier for first copy
- `gene1_chrom` - Chromosome of first copy
- `gene1_subgenome` - Subgenome assignment (e.g., maize1)
- `gene2_id` - Gene identifier for second copy
- `gene2_chrom` - Chromosome of second copy
- `gene2_subgenome` - Subgenome assignment (e.g., maize2)

**Optional columns:**
- `ks` - Synonymous substitution rate
- `ka` - Non-synonymous substitution rate
- `synteny_block` - Synteny block identifier

**Example:**
```tsv
gene1_id	gene1_chrom	gene1_subgenome	gene2_id	gene2_chrom	gene2_subgenome	ks
Zm00001d001001	chr1	maize1	Zm00001d033001	chr5	maize2	0.15
Zm00001d001002	chr1	maize1	Zm00001d033002	chr5	maize2	0.14
```

### Expression Matrix

Tab-separated file with expression values (TPM, FPKM, or counts).

**Format:**
- First column: `gene_id`
- Subsequent columns: Sample names
- Values: Expression levels

**Example:**
```tsv
gene_id	control_1	control_2	control_3	drought_1	drought_2	drought_3
Zm00001d001001	15.2	14.8	16.1	12.3	11.9	13.0
Zm00001d001002	8.5	9.2	8.8	10.5	11.2	10.8
```

### Sample Metadata

Tab-separated file with sample information for expression analyses.

**Required columns:**
- `sample_id` - Sample identifier (must match expression matrix columns)
- `condition` - Experimental condition

**Optional columns:**
- `tissue` - Tissue type
- `replicate` - Replicate number
- `batch` - Batch identifier

**Example:**
```tsv
sample_id	condition	tissue	replicate
control_1	control	leaf	1
control_2	control	leaf	2
drought_1	drought	leaf	1
drought_2	drought	leaf	2
```

### Subgenome Assignments (BED)

BED format file with subgenome assignments for genomic regions.

**Columns:**
1. `chrom` - Chromosome name
2. `start` - Start position (0-based)
3. `end` - End position
4. `subgenome` - Subgenome assignment
5. `score` - Confidence score (optional)
6. `strand` - Strand (optional, typically `.`)

**Example:**
```
chr1	0	10000000	maize1	0.95	.
chr1	10000000	20000000	maize1	0.92	.
chr5	0	15000000	maize2	0.98	.
```

### VCF Files

Standard VCF format (version 4.2+) with genotype calls.

**Requirements:**
- Must be bgzipped and indexed (`.vcf.gz` + `.vcf.gz.tbi`)
- Must contain GT (genotype) field
- Sample names must match population file

**Recommended:**
- Include DP (depth) and GQ (genotype quality) fields
- Filter low-quality variants before analysis

## Output Formats

### Diagnostic Markers

Tab-separated file of diagnostic markers.

**Columns:**
- `chrom` - Chromosome
- `pos` - Position
- `ref` - Reference allele
- `alt` - Alternate allele
- `founder1` - First founder with this allele pattern
- `founder2` - Second founder with different allele
- `freq_diff` - Allele frequency difference
- `diagnostic_type` - Type of diagnostic pattern

### Haplotype Proportions (Windows)

Tab-separated file with per-window haplotype proportions.

**Columns:**
- `sample` - Sample identifier
- `chrom` - Chromosome
- `start` - Window start position
- `end` - Window end position
- `n_markers` - Number of markers in window
- One column per founder population with proportion values

**Example:**
```tsv
sample	chrom	start	end	n_markers	B73	Mo17	W22
RIL_001	chr1	0	1000000	15	0.85	0.10	0.05
RIL_001	chr1	1000000	2000000	12	0.90	0.08	0.02
```

### Haplotype Blocks (BED)

BED format file with inferred haplotype blocks.

**Columns:**
1. `chrom` - Chromosome
2. `start` - Block start
3. `end` - Block end
4. `haplotype` - Assigned haplotype/founder
5. `confidence` - Assignment confidence
6. `sample` - Sample identifier

### Expression Bias Results

Tab-separated file with expression bias statistics.

**Columns:**
- `pair_id` - Homeolog pair identifier
- `gene1_id` - First gene identifier
- `gene2_id` - Second gene identifier
- `gene1_mean` - Mean expression of gene1
- `gene2_mean` - Mean expression of gene2
- `log2_ratio` - log2(gene1/gene2)
- `pvalue` - Statistical test p-value
- `fdr` - FDR-adjusted p-value
- `category` - Bias category (sg1_dominant, sg2_dominant, balanced, etc.)

**Example:**
```tsv
pair_id	gene1_id	gene2_id	gene1_mean	gene2_mean	log2_ratio	pvalue	fdr	category
pair_001	Zm00001d001001	Zm00001d033001	15.0	8.0	0.91	0.001	0.01	sg1_dominant
pair_002	Zm00001d001002	Zm00001d033002	9.5	10.2	-0.10	0.45	0.60	balanced
```

### Assembly Painting Results

Tab-separated file with contig haplotype assignments.

**Columns:**
- `contig_id` - Contig identifier
- `length` - Contig length
- `assigned_haplotype` - Assigned haplotype
- `confidence` - Assignment confidence
- `n_markers` - Number of markers on contig
- `is_chimeric` - Whether contig is potentially chimeric

### Subgenome Assignment Results

Tab-separated file with gene subgenome assignments.

**Columns:**
- `gene_id` - Gene identifier
- `chrom` - Chromosome
- `start` - Gene start
- `end` - Gene end
- `assigned_subgenome` - Assigned subgenome
- `method` - Assignment method (synteny, ortholog, integrated)
- `confidence` - Assignment confidence
- `evidence` - Supporting evidence description

## Compression and Indexing

### Recommended Practices

1. **Large TSV files**: Compress with gzip (`.tsv.gz`)
2. **VCF files**: Use bgzip and create tabix index
3. **BED files**: Sort by chromosome and position

### Creating Indexes

```bash
# VCF indexing
bgzip variants.vcf
tabix -p vcf variants.vcf.gz

# BED sorting
sort -k1,1 -k2,2n regions.bed > regions.sorted.bed
```

## Validation

Haplophaser includes validation utilities for all input formats:

```bash
# Validate population file
haplophaser check-input --type populations populations.tsv

# Validate expression matrix
haplophaser check-input --type expression expression_matrix.tsv

# Validate homeolog pairs
haplophaser check-input --type homeologs homeolog_pairs.tsv
```

Common validation checks:
- Required columns present
- No duplicate entries
- Valid data types
- Consistent sample names across files
