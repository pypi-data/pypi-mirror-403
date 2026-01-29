# Frequently Asked Questions

## General

### What is Haplophaser?

Haplophaser (Polyploid Haplotype Analysis for Sequenced Eukaryotic References) is a toolkit for analyzing haplotypes in complex genomes, with full support for polyploids. It handles tasks like:

- Estimating founder haplotype proportions in derived lines
- Painting genome assemblies by haplotype
- Assigning genes to subgenomes in paleopolyploids
- Analyzing homeolog expression bias

### What species does Haplophaser support?

Haplophaser works with any species, but includes built-in configurations for:

- **Maize** (*Zea mays*) - paleotetraploid
- **Wheat** (*Triticum aestivum*) - hexaploid
- **Brassica** (*Brassica napus*) - allotetraploid

Custom configurations can be created for other polyploid species.

### How is Haplophaser licensed?

Haplophaser is released under the MIT License, allowing free use, modification, and distribution.

## Installation

### What Python version is required?

Python 3.10 or higher is required.

### I'm having trouble installing cyvcf2. What should I do?

cyvcf2 requires htslib. Try:

```bash
# Install htslib first
conda install -c bioconda htslib

# Then install cyvcf2
pip install cyvcf2
```

Or use conda to install both:

```bash
conda install -c bioconda cyvcf2
```

### Can I install Haplophaser with conda?

Conda installation via Bioconda is planned for future releases:

```bash
# Coming soon
conda install -c bioconda haplophaser
```

For now, use pip:

```bash
pip install haplophaser
```

## Input Data

### What VCF format is supported?

Standard VCF format version 4.2 or higher. Requirements:

- Must be bgzipped (`.vcf.gz`)
- Must have tabix index (`.vcf.gz.tbi`)
- Must contain GT (genotype) field
- Sample names must match population file

### How do I create a population file?

Create a tab-separated file with columns:

```tsv
sample	population	role	ploidy
B73	B73	founder	2
Mo17	Mo17	founder	2
RIL_001	derived	derived	2
```

- `sample`: Must match VCF sample names
- `population`: Group name (founders typically get unique names)
- `role`: Either "founder" or "derived"
- `ploidy`: Ploidy level (usually 2)

### What expression formats are supported?

- Tab-separated expression matrices (TPM, FPKM, counts)
- Salmon `quant.sf` files
- Kallisto `abundance.tsv` files
- featureCounts output

### How should homeolog pairs be formatted?

Tab-separated file with columns:

```tsv
gene1_id	gene1_chrom	gene1_subgenome	gene2_id	gene2_chrom	gene2_subgenome	ks
Zm00001d001001	chr1	maize1	Zm00001d033001	chr5	maize2	0.15
```

## Haplotype Analysis

### What is a diagnostic marker?

A diagnostic marker is a genetic variant that distinguishes between founder populations. Haplophaser identifies markers where allele frequencies differ significantly between founders.

### How do I choose the min_freq_diff threshold?

- **0.7-0.9**: Stringent, fewer but highly informative markers
- **0.5-0.7**: Moderate, good balance for most analyses
- **0.3-0.5**: Permissive, more markers but potential noise

Start with 0.7 and adjust based on your data.

### What window size should I use?

Depends on marker density and recombination rate:

- **High marker density**: 500 kb - 1 Mb windows
- **Low marker density**: 2-5 Mb windows
- **Fine mapping**: 100-500 kb windows

### How does the HMM improve block calling?

The Hidden Markov Model:

- Smooths noisy window proportions
- Accounts for recombination probabilities
- Uses genetic map distances (if provided)
- Produces discrete haplotype blocks

## Expression Analysis

### What is expression bias?

Expression bias occurs when homeologous genes (duplicated copies from WGD) show different expression levels. One copy may be consistently expressed higher than its homeolog.

### How are bias categories defined?

| Category | Definition |
|----------|------------|
| sg1_dominant | Gene1 significantly higher (|log2 ratio| > threshold, FDR < 0.05) |
| sg2_dominant | Gene2 significantly higher |
| balanced | No significant difference |
| sg1_only | Only gene1 expressed |
| sg2_only | Only gene2 expressed |
| silent | Neither gene expressed |

### What is subgenome dominance?

Subgenome dominance is a genome-wide bias where one subgenome has more highly-expressed genes than the other. Haplophaser tests this using chi-square statistics on the distribution of biased gene pairs.

### How many replicates do I need?

- **Minimum**: 2 replicates per condition
- **Recommended**: 3+ replicates per condition
- More replicates improve statistical power

## Subgenome Analysis

### What's the difference between synteny and ortholog methods?

- **Synteny-based**: Uses genomic colinearity with a reference that has known assignments. Fast and accurate for closely related species.

- **Ortholog-based**: Uses phylogenetic placement relative to outgroup species. Better when no close reference is available.

- **Integrated**: Combines both evidence types for highest confidence.

### How do I identify homeolog pairs?

After subgenome assignment:

```python
from haplophaser.subgenome.homeologs import find_homeolog_pairs

pairs = find_homeolog_pairs(
    assignments=subgenome_assignments,
    synteny_blocks=synteny_results,
    max_ks=0.5,  # Maximum Ks for WGD pairs
)
```

### What is fractionation bias?

Fractionation bias occurs when one subgenome preferentially retains genes while the other loses them. In maize, the "dominant" maize1 subgenome has retained more genes than maize2.

## Assembly Painting

### How are chimeric contigs detected?

Haplophaser slides windows across contigs and checks for haplotype switches. A chimera is flagged when:

- Different windows show different haplotype assignments
- The switch exceeds a confidence threshold
- Sufficient markers support both assignments

### What if my assembly has few markers mapped?

Try:

1. Lowering the minimum markers threshold
2. Using a larger marker set
3. Checking coordinate systems match
4. Verifying marker quality

## Performance

### How do I speed up large analyses?

1. Use `--threads` for parallelization
2. Process chromosomes separately
3. Filter input data to relevant regions
4. Use sufficient memory (16+ GB for large genomes)

### Why is my analysis using so much memory?

Large VCF files can consume significant memory. Solutions:

- Process chromosomes individually
- Use `--region` to limit analysis
- Increase system memory
- Use streaming readers for very large files

## Troubleshooting

### "No diagnostic markers found"

Possible causes:
- Founders not genetically distinct
- VCF missing founder samples
- min_freq_diff threshold too high
- Insufficient variants in VCF

### "Sample not found in expression matrix"

- Check sample names match exactly (case-sensitive)
- Verify metadata file sample IDs match expression column headers
- Remove extra whitespace from files

### "Invalid homeolog pairs file"

Required columns:
- gene1_id, gene2_id
- gene1_subgenome, gene2_subgenome

Check file is tab-separated and has correct headers.

## Getting Help

- **Documentation**: [https://github.com/aseetharam/haplophaser](https://github.com/aseetharam/haplophaser)
- **Issues**: [GitHub Issues](https://github.com/aseetharam/haplophaser/issues)
- **Discussions**: [GitHub Discussions](https://github.com/aseetharam/haplophaser/discussions)
