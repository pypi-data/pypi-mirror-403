# API Reference

This section documents the Python API for Haplophaser.

## Package Structure

```
phaser/
├── io/                  # Input/output modules
│   ├── vcf.py          # VCF file handling
│   ├── populations.py  # Population file parsing
│   ├── expression.py   # Expression data loading
│   └── gff.py          # GFF/GTF parsing
├── markers/            # Marker discovery
│   ├── diagnostic.py   # Diagnostic marker finding
│   └── filters.py      # Marker filtering
├── proportion/         # Haplotype proportion estimation
│   ├── window.py       # Window-based estimation
│   └── hmm.py          # HMM-based inference
├── assembly/           # Assembly analysis
│   ├── painting.py     # Assembly painting
│   └── chimera.py      # Chimera detection
├── subgenome/          # Subgenome analysis
│   ├── synteny.py      # Synteny-based assignment
│   ├── ortholog.py     # Ortholog-based assignment
│   └── fractionation.py # Fractionation analysis
├── expression/         # Expression analysis
│   ├── homeolog_expression.py
│   ├── bias.py         # Bias calculation
│   ├── dominance.py    # Dominance testing
│   └── condition_bias.py
└── models/             # Data models
    ├── variants.py     # Variant/genotype models
    ├── populations.py  # Population models
    └── expression.py   # Expression models
```

## Core Modules

### haplophaser.io

Input/output utilities for various file formats.

#### haplophaser.io.vcf

```python
from haplophaser.io.vcf import load_vcf, VCFReader

# Load variants from VCF
variants = load_vcf("data.vcf.gz", region="chr1:1-1000000")

# Streaming reader for large files
with VCFReader("data.vcf.gz") as reader:
    for variant in reader:
        process(variant)
```

**Functions:**
- `load_vcf(path, region=None, samples=None)` - Load VCF file
- `VCFReader` - Streaming VCF reader class

#### haplophaser.io.populations

```python
from haplophaser.io.populations import load_populations, PopulationInfo

# Load population assignments
populations = load_populations("populations.tsv")

# Access population info
founders = populations.get_founders()
derived = populations.get_derived()
```

**Functions:**
- `load_populations(path)` - Load population file
- `PopulationInfo` - Population information container

#### haplophaser.io.expression

```python
from haplophaser.io.expression import (
    load_expression_matrix,
    parse_sample_metadata,
    load_salmon_quant,
    load_kallisto_abundance,
)

# Load expression matrix
expr = load_expression_matrix("expression.tsv")

# Load with metadata
metadata = parse_sample_metadata("samples.tsv")
expr = load_expression_matrix("expression.tsv", sample_metadata=metadata)

# Load from quantification tools
expr = load_salmon_quant("quant.sf")
expr = load_kallisto_abundance("abundance.tsv")
```

**Functions:**
- `load_expression_matrix(path, sample_metadata=None)` - Load expression matrix
- `parse_sample_metadata(path)` - Parse sample metadata
- `load_salmon_quant(path)` - Load Salmon quantification
- `load_kallisto_abundance(path)` - Load Kallisto abundance

---

### haplophaser.markers

Diagnostic marker discovery and filtering.

#### haplophaser.markers.diagnostic

```python
from haplophaser.markers.diagnostic import DiagnosticMarkerFinder

finder = DiagnosticMarkerFinder(
    min_freq_diff=0.7,
    min_samples=1,
    max_missing=0.2,
)

# Find markers from VCF
markers = finder.find_from_vcf("data.vcf.gz", populations)

# Find markers from loaded variants
markers = finder.find(variants, populations)

print(f"Found {len(markers)} diagnostic markers")
```

**Classes:**
- `DiagnosticMarkerFinder` - Find diagnostic markers between populations
- `DiagnosticMarker` - Individual marker with metadata

---

### haplophaser.proportion

Haplotype proportion estimation.

#### haplophaser.proportion.window

```python
from haplophaser.proportion.window import WindowProportionEstimator

estimator = WindowProportionEstimator(
    window_size=1_000_000,
    step_size=500_000,
    min_markers=3,
)

# Estimate proportions
results = estimator.estimate(
    vcf_path="data.vcf.gz",
    markers=diagnostic_markers,
    populations=populations,
)

# Access results
for window in results.windows:
    print(f"{window.chrom}:{window.start}-{window.end}")
    print(f"  Proportions: {window.proportions}")
```

#### haplophaser.proportion.hmm

```python
from haplophaser.proportion.hmm import HaplotypeHMM

hmm = HaplotypeHMM(
    n_states=3,  # Number of founder haplotypes
    transition_rate=0.001,
    genetic_map=genetic_map,  # Optional
)

# Infer haplotype blocks
blocks = hmm.infer_blocks(window_proportions)

for block in blocks:
    print(f"{block.chrom}:{block.start}-{block.end} -> {block.haplotype}")
```

---

### haplophaser.expression

Expression analysis modules.

#### haplophaser.expression.homeolog_expression

```python
from haplophaser.expression.homeolog_expression import (
    extract_homeolog_expression,
    HomeologExpression,
)

# Extract expression for homeolog pairs
homeolog_expr = extract_homeolog_expression(
    expr_matrix,
    "homeolog_pairs.tsv",
    min_mean_expr=1.0,
)

print(f"Extracted {homeolog_expr.n_pairs} pairs")
```

#### haplophaser.expression.bias

```python
from haplophaser.expression.bias import (
    calculate_expression_bias,
    BiasResult,
    BiasCategory,
)

# Calculate bias
bias_result = calculate_expression_bias(
    homeolog_expr,
    min_expr=1.0,
    log2_threshold=1.0,
    test_method="paired_t",
)

# Get summary
summary = bias_result.summary()
print(f"SG1 dominant: {summary['n_sg1_dominant']}")
print(f"SG2 dominant: {summary['n_sg2_dominant']}")
print(f"Balanced: {summary['n_balanced']}")

# Iterate over pairs
for pair in bias_result.pairs:
    if pair.category == BiasCategory.SG1_DOMINANT:
        print(f"{pair.gene1_id} > {pair.gene2_id}")
```

**Classes:**
- `BiasResult` - Container for bias analysis results
- `BiasCategory` - Enum of bias categories

#### haplophaser.expression.dominance

```python
from haplophaser.expression.dominance import (
    test_subgenome_dominance,
    DominanceResult,
)

# Test for genome-wide dominance
dominance = test_subgenome_dominance(
    bias_result,
    min_significant=10,
)

print(f"Chi-square: {dominance.chi2_statistic:.2f}")
print(f"P-value: {dominance.pvalue:.2e}")
if dominance.is_significant:
    print(f"Dominant: {dominance.dominant_subgenome}")
```

#### haplophaser.expression.condition_bias

```python
from haplophaser.expression.condition_bias import ConditionBiasAnalyzer

analyzer = ConditionBiasAnalyzer()

# Compare conditions
comparison = analyzer.compare_conditions(
    expr_matrix,
    "homeolog_pairs.tsv",
    condition1="control",
    condition2="drought",
)

print(f"Differential bias: {comparison.n_differential}")
print(f"Category changes: {comparison.n_category_changed}")

# Get pairs that changed
for pair in comparison.changed_pairs:
    print(f"{pair.pair_id}: {pair.category1} -> {pair.category2}")
```

---

### haplophaser.subgenome

Subgenome analysis modules.

#### haplophaser.subgenome.synteny

```python
from haplophaser.subgenome.synteny import SyntenyAssigner

assigner = SyntenyAssigner(
    min_block_genes=5,
    min_confidence=0.7,
)

# Assign based on synteny
assignments = assigner.assign(
    query_genes=query_gff,
    reference_genes=reference_gff,
    reference_subgenomes=ref_assignments,
)
```

#### haplophaser.subgenome.fractionation

```python
from haplophaser.subgenome.fractionation import FractionationAnalyzer

analyzer = FractionationAnalyzer(species="maize")

# Analyze fractionation
result = analyzer.analyze(
    genes=gene_annotations,
    subgenome_assignments=assignments,
)

print(f"SG1 genes: {result.sg1_count}")
print(f"SG2 genes: {result.sg2_count}")
print(f"Fractionation bias: {result.bias_ratio:.2f}")
```

---

### haplophaser.models

Data model classes.

#### haplophaser.models.expression

```python
from haplophaser.models.expression import (
    ExpressionMatrix,
    HomeologPair,
    SampleMetadata,
)

# ExpressionMatrix
matrix = ExpressionMatrix(
    gene_ids=["gene1", "gene2"],
    sample_ids=["s1", "s2"],
    values=np.array([[1.0, 2.0], [3.0, 4.0]]),
)

# Filter genes
filtered = matrix.filter_genes(min_mean_expr=1.0)

# Get expression for gene
expr = matrix.get_gene("gene1")

# HomeologPair
pair = HomeologPair(
    pair_id="pair_001",
    gene1_id="Zm001",
    gene2_id="Zm002",
    gene1_subgenome="maize1",
    gene2_subgenome="maize2",
)
```

---

## Common Patterns

### Chaining Analyses

```python
from haplophaser.io.expression import load_expression_matrix, parse_sample_metadata
from haplophaser.expression.homeolog_expression import extract_homeolog_expression
from haplophaser.expression.bias import calculate_expression_bias
from haplophaser.expression.dominance import test_subgenome_dominance

# Load data
metadata = parse_sample_metadata("samples.tsv")
expr = load_expression_matrix("expression.tsv", sample_metadata=metadata)

# Extract homeolog expression
homeolog_expr = extract_homeolog_expression(expr, "homeologs.tsv")

# Calculate bias
bias = calculate_expression_bias(homeolog_expr)

# Test dominance
dominance = test_subgenome_dominance(bias)

print(f"Dominant subgenome: {dominance.dominant_subgenome}")
```

### Filtering and Subsetting

```python
# Filter expression matrix by samples
samples_of_interest = ["s1", "s2", "s3"]
filtered_expr = expr.subset_samples(samples_of_interest)

# Filter by condition
control_expr = expr.filter_by_condition("control")

# Filter bias results
significant_only = bias_result.filter(fdr_threshold=0.05)
sg1_dominant = bias_result.filter(category=BiasCategory.SG1_DOMINANT)
```

### Error Handling

```python
from haplophaser.io.expression import load_expression_matrix
from haplophaser.exceptions import HaplophaserInputError, HaplophaserValidationError

try:
    expr = load_expression_matrix("expression.tsv")
except HaplophaserInputError as e:
    print(f"Failed to load file: {e}")
except HaplophaserValidationError as e:
    print(f"Invalid data: {e}")
```

---

## Module Documentation

Detailed documentation for each module:

- [haplophaser.io](io.md) - Input/output modules
- [haplophaser.markers](markers.md) - Marker discovery
- [haplophaser.proportion](proportion.md) - Proportion estimation
- [haplophaser.assembly](assembly.md) - Assembly analysis
- [haplophaser.subgenome](subgenome.md) - Subgenome analysis
- [haplophaser.expression](expression.md) - Expression analysis
- [haplophaser.models](models.md) - Data models
