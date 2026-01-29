# Visualization Guide

Haplophaser integrates with [chromoplot](https://github.com/aseetharam/chromoplot) for publication-ready genome visualizations.

## Quick Plots

### Haplotype Proportions

```bash
# Single region
haplophaser viz proportions \
    -h blocks.bed \
    -r genome.fa.fai \
    --region chr1:1-10000000 \
    -o figure.pdf

# Whole genome
haplophaser viz genome \
    -h blocks.bed \
    -r genome.fa.fai \
    -o genome.pdf
```

### Assembly Painting

```bash
haplophaser viz assembly \
    -p painting.bed \
    -r assembly.fa.fai \
    --chimeras chimeras.bed \
    -o assembly.pdf
```

### Subgenome Assignments

```bash
haplophaser viz subgenome \
    -a assignments.bed \
    -r genome.fa.fai \
    --subgenomes maize1,maize2 \
    -o subgenomes.pdf
```

### Expression Bias

```bash
# MA plot
haplophaser viz expression \
    -r bias_results.tsv \
    --plot-type ma \
    -o ma_plot.pdf

# Distribution plot
haplophaser viz expression \
    -r bias_results.tsv \
    --plot-type distribution \
    -o bias_distribution.pdf
```

### Synteny

```bash
haplophaser viz synteny \
    -s alignment.paf \
    --ref-fai ref.fa.fai \
    --query-fai query.fa.fai \
    -o synteny.pdf
```

## Python API

### ProportionFigure

```python
from haplophaser.viz import ProportionFigure

fig = ProportionFigure(
    "genome.fa.fai",
    region="chr1:1-10000000",
    founders=['B73', 'Mo17', 'W22'],
    title="Chromosome 1 Haplotypes"
)

fig.add_ideogram()
fig.add_genes("genes.gff3")
fig.add_haplotypes("blocks.bed", label="RIL_001")
fig.add_scale_bar()

fig.save("figure.pdf")
```

### Whole Genome

```python
from haplophaser.viz import ProportionGenomeFigure

fig = ProportionGenomeFigure(
    "genome.fa.fai",
    founders=['B73', 'Mo17'],
    n_cols=5
)

fig.add_ideogram()
fig.add_haplotypes("blocks.bed")

fig.save("genome.pdf")
```

### Assembly Painting

```python
from haplophaser.viz import AssemblyPaintingFigure

fig = AssemblyPaintingFigure(
    "assembly.fa.fai",
    founders=['hap1', 'hap2'],
    title="Assembly Haplotype Painting"
)

fig.add_ideogram()
fig.add_painting("painting.bed")
fig.add_chimeras("chimeras.bed")
fig.add_scale_bar()

fig.save("assembly.pdf")
```

### Subgenome Visualization

```python
from haplophaser.viz import SubgenomeFigure

fig = SubgenomeFigure(
    "genome.fa.fai",
    subgenomes=['maize1', 'maize2'],
    organism='maize',
    title="Subgenome Assignments"
)

fig.add_ideogram()
fig.add_subgenome_track("assignments.bed")
fig.add_gene_density("gene_density.bedGraph")
fig.add_scale_bar()

fig.save("subgenomes.pdf")
```

### Expression Bias Plots

```python
from haplophaser.viz import ExpressionBiasFigure

# MA plot
fig = ExpressionBiasFigure("bias_results.tsv")
fig.plot_ma(highlight_significant=True, fdr_threshold=0.05)
fig.save("ma_plot.pdf")

# Distribution
fig = ExpressionBiasFigure("bias_results.tsv")
fig.plot_bias_distribution(bins=50, show_stats=True)
fig.save("distribution.pdf")
```

### Synteny Visualization

```python
from haplophaser.viz import SyntenyFigure

fig = SyntenyFigure(
    ref_reference="ref.fa.fai",
    query_reference="query.fa.fai",
    figsize=(14, 10)
)

fig.add_ref_ideogram()
fig.add_ref_genes("ref_genes.gff3")
fig.add_synteny("alignment.paf")
fig.add_query_genes("query_genes.gff3")
fig.add_query_ideogram()

fig.save("synteny.pdf")
```

## Custom Colors

### Founder Colors

```python
from haplophaser.viz.utils import get_founder_colors

# Automatic maize NAM colors
colors = get_founder_colors(['B73', 'Mo17', 'CML247'])
# Returns: {'B73': '#FFC125', 'Mo17': '#4169E1', 'CML247': '#32CD32'}

# Use in figure
fig = ProportionFigure("genome.fa.fai", founders=['B73', 'Mo17', 'CML247'])
fig.add_haplotypes("blocks.bed", style={'color_map': colors})
```

### Subgenome Colors

```python
from haplophaser.viz.subgenome import get_subgenome_colors

# Organism-specific colors
maize_colors = get_subgenome_colors(['maize1', 'maize2'], organism='maize')
wheat_colors = get_subgenome_colors(['A', 'B', 'D'], organism='wheat')
brassica_colors = get_subgenome_colors(['A', 'C'], organism='brassica')
```

## Available Tracks

| Track Method | Description |
|-------------|-------------|
| `add_ideogram()` | Chromosome backbone |
| `add_haplotypes()` | Haplotype blocks |
| `add_genes()` | Gene models from GFF3 |
| `add_features()` | Generic BED features |
| `add_proportions()` | Signal track (bedGraph) |
| `add_breakpoints()` | Recombination markers |
| `add_scale_bar()` | Scale reference |
| `add_painting()` | Contig painting (assembly) |
| `add_chimeras()` | Chimera breakpoints |
| `add_subgenome_track()` | Subgenome assignments |
| `add_gene_density()` | Gene density signal |
| `add_fractionation()` | Fractionation bias |
| `add_synteny()` | Synteny ribbons |

## Style Parameters

```python
# Haplotype track styling
fig.add_haplotypes(
    "blocks.bed",
    style={
        'block_height': 0.8,
        'block_alpha': 0.9,
        'show_boundaries': True,
        'boundary_color': 'white',
        'show_legend': True,
    }
)

# Signal track styling
fig.add_proportions(
    "signal.bedGraph",
    style={
        'color': '#1f77b4',
        'fill_alpha': 0.3,
        'line_width': 1.5,
    }
)
```

## One-Liner Presets

For quick visualization without customization:

```python
from haplophaser.viz import (
    plot_haplotype_proportions,
    plot_genome_haplotypes,
    plot_assembly_painting,
    plot_subgenome_assignment,
    plot_expression_bias,
    plot_synteny,
)

# Single region haplotypes
plot_haplotype_proportions(
    "blocks.bed", "genome.fa.fai", "figure.pdf",
    region="chr1:1-10000000"
)

# Whole genome
plot_genome_haplotypes(
    "blocks.bed", "genome.fa.fai", "genome.pdf",
    founders=['B73', 'Mo17']
)

# Expression bias
plot_expression_bias(
    "bias_results.tsv", "ma_plot.pdf",
    plot_type="ma"
)
```

## Integration with Chromoplot

For advanced customization, use chromoplot directly:

```python
import chromoplot as cp

fig = cp.GenomeFigure("genome.fa.fai", region="chr1:1-10000000")
fig.add_track(cp.IdeogramTrack())
fig.add_track(cp.GeneTrack("genes.gff3", label="Genes"))
fig.add_track(cp.HaplotypeTrack("blocks.bed", label="Haplotypes"))
fig.add_track(cp.SignalTrack("signal.bedGraph", label="Coverage"))
fig.save("custom_figure.pdf")
```

See [chromoplot documentation](https://chromoplot.readthedocs.io) for full details.

## Output Formats

All figure classes support multiple output formats:

- **PDF** - Vector format, best for publications
- **PNG** - Raster format with adjustable DPI
- **SVG** - Scalable vector format
- **EPS** - PostScript format

```python
# Save in different formats
fig.save("figure.pdf")
fig.save("figure.png", dpi=300)
fig.save("figure.svg")
```
