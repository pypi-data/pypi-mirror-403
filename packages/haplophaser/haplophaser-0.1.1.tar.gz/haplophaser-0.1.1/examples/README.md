# Haplophaser Examples

This directory contains example analyses demonstrating phaser capabilities.

## Examples

### 1. Maize NAM Haplotype Analysis

`01_maize_nam/`

Analyze haplotype proportions in maize NAM RILs using diagnostic markers.

### 2. Assembly QC with Haplotype Painting

`02_assembly_qc/`

Validate assembly quality by painting contigs with known haplotypes.

### 3. Subgenome Deconvolution

`03_subgenome/`

Assign genomic regions to ancestral subgenomes in maize.

### 4. Homeolog Expression Bias

`04_expression/`

Analyze expression differences between homeolog pairs.

## Running Examples

Each example directory contains:

- `README.md` - Description and instructions
- `run.sh` - Shell script to run the analysis
- `run.py` - Python script alternative
- `config.yaml` - Configuration file

```bash
cd 01_maize_nam
./run.sh
```

## Test Data

Small test datasets are included. For full analyses, download data:

```bash
./download_data.sh
```

## Quick Start

```bash
# Clone repository and navigate to examples
git clone https://github.com/aseetharam/haplophaser.git
cd phaser/examples

# Run an example
cd 01_maize_nam
./run.sh
```

## Requirements

- phaser installed (`pip install haplophaser`)
- chromoplot installed (comes with phaser)
- Input data files (provided for test examples)

## Example Outputs

Each example produces:

- Analysis results (TSV, BED files)
- Visualization figures (PDF)
- Summary reports (TXT)

See individual README files for specific outputs.
