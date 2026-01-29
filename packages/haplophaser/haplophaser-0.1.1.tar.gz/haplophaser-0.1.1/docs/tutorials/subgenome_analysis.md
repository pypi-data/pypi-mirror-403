# Subgenome Analysis Tutorial

This tutorial walks through assigning genomic regions to ancestral subgenomes in paleopolyploid genomes.

## Overview

Paleopolyploid genomes like maize, wheat, and Brassica contain multiple subgenomes from ancient whole-genome duplications (WGDs). Identifying which genes belong to which subgenome is essential for:

- Understanding genome evolution and fractionation
- Identifying homeologous gene pairs
- Analyzing subgenome-specific expression patterns
- Studying biased gene loss (fractionation bias)

## Prerequisites

- Haplophaser installed
- Query genome assembly and annotation
- Reference genome with known subgenome assignments (optional but recommended)
- OrthoFinder installed (for ortholog-based assignment)

## Approach Overview

Haplophaser supports multiple assignment methods:

1. **Synteny-based**: Uses synteny with a reference genome that has known assignments
2. **Ortholog-based**: Uses phylogenetic placement of genes
3. **Integrated**: Combines multiple evidence types

## Method 1: Synteny-Based Assignment

Best when a closely related species has known subgenome assignments.

### Step 1: Prepare Reference Data

You need:
- Reference genome (FASTA)
- Reference gene annotations (GFF3)
- Reference subgenome assignments (BED)

```
# Reference subgenome assignments (BED format)
chr1	0	100000000	maize1	.	.
chr2	0	95000000	maize1	.	.
chr5	0	110000000	maize2	.	.
chr6	0	85000000	maize2	.	.
```

### Step 2: Run Synteny Assignment

#### Using CLI

```bash
haplophaser subgenome-assign \
    --assembly query.fasta \
    --genes query_genes.gff3 \
    --reference reference.fasta \
    --reference-genes reference_genes.gff3 \
    --reference-assignments reference_subgenomes.bed \
    --method synteny \
    --species maize \
    --output-dir subgenome_results
```

#### Using Python API

```python
from haplophaser.subgenome.synteny import SyntenyAssigner
from haplophaser.io.gff import load_gff

# Load gene annotations
query_genes = load_gff("query_genes.gff3")
reference_genes = load_gff("reference_genes.gff3")

# Initialize assigner
assigner = SyntenyAssigner(
    min_block_genes=5,      # Minimum genes for synteny block
    min_confidence=0.7,     # Minimum assignment confidence
    species="maize",        # Species preset
)

# Run assignment
assignments = assigner.assign(
    query_genes=query_genes,
    reference_genes=reference_genes,
    reference_assignments="reference_subgenomes.bed",
)

print(f"Assigned {assignments.n_assigned} of {assignments.n_genes} genes")

# Save results
assignments.to_bed("subgenome_assignments.bed")
assignments.to_tsv("subgenome_assignments.tsv")
```

### Step 3: Examine Results

```python
# Summary statistics
summary = assignments.summary()
print(f"Total genes: {summary['n_genes']}")
print(f"Assigned: {summary['n_assigned']}")
print(f"By subgenome:")
for sg, count in summary['subgenome_counts'].items():
    print(f"  {sg}: {count}")

# High-confidence assignments
confident = assignments.filter(min_confidence=0.9)
print(f"\nHigh confidence: {confident.n_assigned}")

# View individual assignments
for gene in assignments.genes[:10]:
    print(f"{gene.gene_id}: {gene.subgenome} ({gene.confidence:.2f})")
```

## Method 2: Ortholog-Based Assignment

Uses phylogenetic analysis to assign genes based on their relationship to outgroup species.

### Step 1: Run OrthoFinder

First, run OrthoFinder to identify orthologs:

```bash
orthofinder -f protein_sequences/ -t 8
```

### Step 2: Run Ortholog Assignment

#### Using CLI

```bash
haplophaser subgenome-assign \
    --assembly query.fasta \
    --genes query_genes.gff3 \
    --orthofinder-results OrthoFinder/Results_*/Orthogroups/ \
    --outgroup sorghum \
    --method ortholog \
    --output-dir ortholog_results
```

#### Using Python API

```python
from haplophaser.subgenome.ortholog import OrthologAssigner

assigner = OrthologAssigner(
    outgroup_species=["sorghum", "rice"],  # Outgroup species
    min_bootstrap=70,                       # Minimum bootstrap support
)

assignments = assigner.assign(
    query_genes=query_genes,
    orthofinder_dir="OrthoFinder/Results_*/",
)
```

## Method 3: Integrated Assignment

Combines synteny and ortholog evidence for highest accuracy.

### Using CLI

```bash
haplophaser subgenome-assign \
    --assembly query.fasta \
    --genes query_genes.gff3 \
    --reference reference.fasta \
    --reference-genes reference_genes.gff3 \
    --reference-assignments reference_subgenomes.bed \
    --orthofinder-results OrthoFinder/Results_*/ \
    --method integrated \
    --output-dir integrated_results
```

### Using Python API

```python
from haplophaser.subgenome.integrated import IntegratedAssigner

assigner = IntegratedAssigner(
    synteny_weight=0.6,    # Weight for synteny evidence
    ortholog_weight=0.4,   # Weight for ortholog evidence
    min_confidence=0.7,
)

assignments = assigner.assign(
    query_genes=query_genes,
    reference_genes=reference_genes,
    reference_assignments="reference_subgenomes.bed",
    orthofinder_dir="OrthoFinder/Results_*/",
)

# Check evidence sources
for gene in assignments.genes:
    print(f"{gene.gene_id}: {gene.subgenome}")
    print(f"  Synteny evidence: {gene.synteny_confidence:.2f}")
    print(f"  Ortholog evidence: {gene.ortholog_confidence:.2f}")
    print(f"  Integrated: {gene.confidence:.2f}")
```

## Step 4: Identify Homeolog Pairs

Once subgenomes are assigned, identify homeologous gene pairs.

```python
from haplophaser.subgenome.homeologs import find_homeolog_pairs

pairs = find_homeolog_pairs(
    assignments=assignments,
    synteny_blocks=synteny_results,  # From synteny analysis
    max_ks=0.5,                      # Maximum Ks for WGD pairs
)

print(f"Found {len(pairs)} homeolog pairs")

# Save pairs
pairs.to_tsv("homeolog_pairs.tsv")

# Examine pairs
for pair in pairs[:5]:
    print(f"{pair.gene1_id} ({pair.gene1_subgenome}) <-> {pair.gene2_id} ({pair.gene2_subgenome})")
    print(f"  Ks: {pair.ks:.3f}")
    print(f"  Synteny block: {pair.synteny_block}")
```

## Step 5: Analyze Fractionation

Compare gene retention between subgenomes.

### Using CLI

```bash
haplophaser subgenome-fractionation \
    --genes query_genes.gff3 \
    --assignments subgenome_assignments.bed \
    --ancestral-genes ancestral_gene_count.tsv \
    --species maize \
    --output fractionation_report.tsv
```

### Using Python API

```python
from haplophaser.subgenome.fractionation import FractionationAnalyzer

analyzer = FractionationAnalyzer(species="maize")

result = analyzer.analyze(
    genes=query_genes,
    assignments=assignments,
    homeolog_pairs=pairs,
)

print(f"Subgenome 1 genes: {result.sg1_count}")
print(f"Subgenome 2 genes: {result.sg2_count}")
print(f"Fractionation ratio: {result.fractionation_ratio:.2f}")
print(f"Dominant subgenome: {result.dominant_subgenome}")

# By chromosome
for chrom, stats in result.by_chromosome.items():
    print(f"\n{chrom}:")
    print(f"  SG1: {stats['sg1']}")
    print(f"  SG2: {stats['sg2']}")
    print(f"  Ratio: {stats['ratio']:.2f}")
```

## Species-Specific Configurations

### Maize

```python
assigner = SyntenyAssigner(
    species="maize",
    # Maize-specific defaults:
    # - maize1 (dominant) and maize2 subgenomes
    # - Expected Ks ~ 0.15 for WGD pairs
)
```

### Wheat

```python
assigner = SyntenyAssigner(
    species="wheat",
    # Wheat-specific defaults:
    # - A, B, D subgenomes
    # - Accounts for hexaploidy
)
```

### Brassica

```python
assigner = SyntenyAssigner(
    species="brassica",
    # Brassica-specific defaults:
    # - Accounts for paleohexaploidy (Brassiceae triplication)
    # - Then allotetraploidy in B. napus
)
```

## Interpreting Results

### Assignment Confidence

| Confidence | Interpretation |
|------------|----------------|
| > 0.9 | Strong synteny or ortholog support |
| 0.7 - 0.9 | Good support, likely correct |
| 0.5 - 0.7 | Weak support, may need review |
| < 0.5 | Conflicting evidence |

### Fractionation Patterns

- **Biased fractionation**: One subgenome retains more genes
- **Balanced fractionation**: Similar retention between subgenomes
- **Regional variation**: Fractionation may vary across chromosomes

### Common Issues

**Low assignment rate:**
- Reference may be too divergent
- Gene annotations may be incomplete
- Try integrated method with ortholog evidence

**Conflicting assignments:**
- May indicate gene conversion
- Could be annotation error
- Check with manual inspection

**Unexpected fractionation patterns:**
- Verify subgenome assignments are correct
- Check for assembly errors
- Consider alternative evolutionary histories

## Visualization

Export data for visualization:

```python
from haplophaser.subgenome.viz import SubgenomeVizPrep

viz = SubgenomeVizPrep()

# Chromosome painting data
painting = viz.chromosome_painting(assignments)

# Fractionation plot data
frac_data = viz.fractionation_bar_chart(result)

# Ks distribution for homeolog pairs
ks_data = viz.ks_distribution(pairs)
```

## Next Steps

- [Expression Bias Tutorial](expression_bias.md) - Analyze homeolog expression
- [File Formats](../file_formats.md) - Input/output specifications
- [API Reference](../api/index.md) - Detailed API documentation
