# 🔫 Phaser

**Haplotype analysis toolkit for complex genomes with full polyploid support.**

Phaser analyzes haplotype inheritance patterns in derived lines relative to founder/source populations. Designed from the ground up for polyploid genomes, from diploids through hexaploids and beyond.

## Features

- **Haplotype Proportion Estimation**: Calculate what fraction of a sample's genome derives from each founder population
- **Chromosome Painting**: Paint genomic regions by haplotype origin using Hidden Markov Models
- **Chimeric Contig Detection**: Identify potential misassemblies through haplotype switches
- **Linkage-Informed Scaffolding**: Order and orient scaffolds using haplotype phase information
- **Full Polyploid Support**: First-class support for diploid, autopolyploid, and allopolyploid genomes

## Installation

### From PyPI (when released)

```bash
pip install haplophaser
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/your-org/phaser.git
cd phaser

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Dependencies

Core dependencies:
- Python 3.10+
- NumPy
- Pydantic v2
- cyvcf2
- PyYAML
- Typer

## Quick Start

### Basic Usage

```bash
# Estimate haplotype proportions
haplophaser proportion variants.vcf.gz -p populations.tsv -o results/

# Paint chromosomes by haplotype origin
haplophaser paint variants.vcf.gz -p populations.tsv -o painted/

# Order scaffolds using linkage
haplophaser scaffold scaffolds.vcf.gz -p populations.tsv -g genetic_map.tsv

# Run quality control checks
haplophaser qc variants.vcf.gz -p populations.tsv
```

### Population File Format

Phaser uses TSV or YAML files to define population structure:

**TSV format** (`populations.tsv`):
```
sample	population	role	ploidy
B73	NAM_founders	founder	2
Mo17	NAM_founders	founder	2
W22	NAM_founders	founder	2
RIL_001	NAM_RILs	derived	2
RIL_002	NAM_RILs	derived	2
```

**YAML format** (`populations.yaml`):
```yaml
populations:
  - name: NAM_founders
    role: founder
    ploidy: 2
    samples:
      - B73
      - Mo17
      - W22

  - name: NAM_RILs
    role: derived
    ploidy: 2
    samples:
      - RIL_001
      - RIL_002
```

### Polyploid Examples

For polyploid species, define subgenomes in YAML:

```yaml
populations:
  - name: wheat_founders
    role: founder
    ploidy: 6
    subgenomes:
      - name: A
        ploidy: 2
      - name: B
        ploidy: 2
      - name: D
        ploidy: 2
    samples:
      - Chinese_Spring
      - Jagger
```

### Configuration

Generate a configuration template:

```bash
haplophaser init-config -o phaser.yaml
```

Then customize and use:

```bash
haplophaser proportion variants.vcf.gz -p populations.tsv -c phaser.yaml
```

## Python API

```python
from haplophaser import Sample, Population, PopulationRole
from haplophaser.core.models import make_hexaploid_sample
from haplophaser.io import load_populations_yaml, VCFReader

# Create samples programmatically
b73 = Sample(name="B73", ploidy=2, population="founders")

# Create polyploid samples
wheat = make_hexaploid_sample("Chinese_Spring", ("A", "B", "D"), "founders")

# Load populations from file
populations = load_populations_yaml("populations.yaml")

# Read VCF files
with VCFReader("variants.vcf.gz") as reader:
    for variant in reader.fetch("chr1", 0, 1_000_000):
        print(f"{variant.chrom}:{variant.pos} {variant.ref}>{variant.alt}")
```

## Coordinate System

Phaser uses **0-based, half-open intervals** (BED-style) internally:
- Position 0 is the first base
- Intervals are `[start, end)` — start is included, end is excluded

Conversion to/from 1-based systems (VCF, GFF) happens automatically during I/O.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=phaser --cov-report=html

# Run specific test file
pytest tests/test_models.py
```

### Code Quality

```bash
# Lint and format check
ruff check src tests

# Format code
ruff format src tests

# Type checking
mypy src
```

### Project Structure

```
phaser/
├── pyproject.toml          # Package configuration
├── README.md
├── src/
│   └── phaser/
│       ├── __init__.py     # Package exports
│       ├── core/
│       │   ├── models.py   # Data models (Sample, Variant, etc.)
│       │   └── config.py   # Configuration system
│       ├── io/
│       │   ├── vcf.py      # VCF reading
│       │   └── populations.py  # Population file I/O
│       └── cli/
│           └── main.py     # CLI commands
├── tests/
│   ├── conftest.py         # Test fixtures
│   ├── test_models.py
│   ├── test_config.py
│   └── test_populations.py
└── docs/
```

## Roadmap

- [x] Core data models with polyploid support
- [x] Configuration system
- [x] Population file I/O
- [x] CLI skeleton
- [ ] VCF reading implementation
- [ ] Window-based analysis
- [ ] HMM-based haplotype inference
- [ ] Chromosome painting
- [ ] Proportion estimation
- [ ] Scaffold ordering
- [ ] Integration with chromoplot for visualization

## Citation

If you use Phaser in your research, please cite:

> Phaser: Haplotype analysis toolkit for complex genomes. (in preparation)

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md for guidelines.
