# Installation

## Requirements

- Python 3.10 or higher
- NumPy >= 1.24
- cyvcf2 >= 0.30 (for VCF parsing)
- pydantic >= 2.0
- typer >= 0.9 (CLI)
- rich >= 13.0 (terminal output)

### Optional Dependencies

- scipy >= 1.10 (for statistical tests)
- pandas >= 2.0 (for DataFrame operations)
- pysam >= 0.21 (for BAM/FASTA handling)

## Installation Methods

### From PyPI (Recommended)

```bash
pip install haplophaser
```

### From Source

```bash
git clone https://github.com/aseetharam/haplophaser.git
cd phaser
pip install -e .
```

### Development Installation

For development with testing and linting tools:

```bash
git clone https://github.com/aseetharam/haplophaser.git
cd phaser
pip install -e ".[dev]"
```

### With Conda (Coming Soon)

```bash
conda install -c bioconda phaser
```

## Verifying Installation

After installation, verify that phaser is working:

```bash
# Check version
haplophaser --version

# Show help
haplophaser --help

# Run a quick test
haplophaser check-input --help
```

## External Tools

Some phaser features require external bioinformatics tools:

### For Assembly Analysis

- **minimap2** - For aligning assemblies and mapping markers
  ```bash
  conda install -c bioconda minimap2
  ```

### For Subgenome Analysis

- **OrthoFinder** - For ortholog-based subgenome assignment
  ```bash
  conda install -c bioconda orthofinder
  ```

### For Expression Analysis

- **Salmon** or **Kallisto** - For RNA-seq quantification (optional, phaser can use pre-computed matrices)

## Troubleshooting

### cyvcf2 Installation Issues

If you encounter issues installing cyvcf2:

```bash
# Install htslib first
conda install -c bioconda htslib

# Then install cyvcf2
pip install cyvcf2
```

### Memory Issues with Large VCFs

For large VCF files, consider:
- Splitting by chromosome
- Using `--threads` option to parallelize
- Increasing system memory

### Permission Issues

If you encounter permission errors:

```bash
pip install --user phaser
```

Or use a virtual environment:

```bash
python -m venv phaser_env
source phaser_env/bin/activate
pip install haplophaser
```
