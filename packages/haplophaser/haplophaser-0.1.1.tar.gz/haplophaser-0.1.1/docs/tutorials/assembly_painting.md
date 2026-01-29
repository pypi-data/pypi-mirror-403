# Assembly Painting Tutorial

This tutorial walks through assigning contigs in a genome assembly to haplotypes using diagnostic markers.

## Overview

Assembly painting determines which founder haplotype each contig in an assembly most closely resembles. This is useful for:

- Characterizing new assemblies of hybrid genomes
- Identifying misassemblies (chimeric contigs)
- Separating haplotypes in heterozygous assemblies
- Validating phased assemblies

## Prerequisites

- Haplophaser installed
- Genome assembly (FASTA)
- Diagnostic markers from founder analysis
- minimap2 installed (for marker mapping)

## Input Data

### Assembly File

A FASTA file with contigs or scaffolds:

```
>contig_001 length=5000000
ACGTACGT...
>contig_002 length=3500000
ACGTACGT...
```

### Diagnostic Markers

Markers from `haplophaser find-markers` that distinguish haplotypes.

## Step 1: Map Markers to Assembly

First, map diagnostic markers to your assembly.

### Using CLI

```bash
haplophaser assembly-paint \
    --assembly new_assembly.fasta \
    --markers diagnostic_markers.tsv \
    --output-dir painting_results \
    --detect-chimeras
```

### Using Python API

```python
from haplophaser.assembly.painting import AssemblyPainter
from haplophaser.markers.diagnostic import load_markers

# Load markers
markers = load_markers("diagnostic_markers.tsv")

# Initialize painter
painter = AssemblyPainter(
    min_markers=3,          # Minimum markers per contig
    min_confidence=0.7,     # Minimum assignment confidence
    detect_chimeras=True,   # Enable chimera detection
)

# Paint assembly
results = painter.paint(
    assembly_path="new_assembly.fasta",
    markers=markers,
)

print(f"Painted {results.n_assigned} of {results.n_contigs} contigs")
print(f"Detected {results.n_chimeric} potential chimeras")
```

## Step 2: Examine Results

### Contig Assignments

```python
# Print assignments
for contig in results.contigs:
    print(f"{contig.contig_id}:")
    print(f"  Length: {contig.length:,} bp")
    print(f"  Markers: {contig.n_markers}")
    print(f"  Haplotype: {contig.assigned_haplotype}")
    print(f"  Confidence: {contig.confidence:.2f}")
    if contig.is_chimeric:
        print(f"  WARNING: Potential chimera!")

# Save to file
results.to_tsv("contig_assignments.tsv")
```

### Output Format

```tsv
contig_id	length	n_markers	assigned_haplotype	confidence	is_chimeric
contig_001	5000000	45	B73	0.92	False
contig_002	3500000	28	Mo17	0.88	False
contig_003	2000000	15	B73	0.65	True
```

## Step 3: Detect Chimeric Contigs

Chimeric contigs contain segments from different haplotypes, indicating potential misassembly.

### Understanding Chimera Detection

Haplophaser slides a window across each contig and checks for haplotype switches:

```python
# Configure chimera detection
painter = AssemblyPainter(
    detect_chimeras=True,
    chimera_window_size=100_000,   # Window size for detection
    chimera_min_markers=5,         # Min markers per window
    chimera_switch_threshold=0.5,  # Proportion threshold
)

results = painter.paint(assembly_path, markers)

# Examine chimeric contigs
for contig in results.chimeric_contigs:
    print(f"\nChimeric contig: {contig.contig_id}")
    print(f"  Breakpoints:")
    for bp in contig.breakpoints:
        print(f"    Position {bp.position}: {bp.haplotype_before} -> {bp.haplotype_after}")
```

### Chimera Report

```python
# Generate detailed chimera report
chimera_report = results.chimera_report()

for contig_id, details in chimera_report.items():
    print(f"\n{contig_id}:")
    print(f"  Number of switches: {details['n_switches']}")
    for region in details['regions']:
        print(f"    {region['start']}-{region['end']}: {region['haplotype']} ({region['confidence']:.2f})")
```

## Step 4: Generate Visualizations

Export data for visualization tools.

```python
from haplophaser.assembly.viz import AssemblyVizPrep

viz = AssemblyVizPrep()

# Generate data for chromosome/contig painting plot
painting_data = viz.prepare_painting_plot(results)

# Export for external tools
painting_data.to_json("painting_viz.json")

# Generate summary statistics
stats = viz.painting_statistics(results)
print(f"Total assembly size: {stats['total_size']:,} bp")
print(f"Assigned: {stats['assigned_size']:,} bp ({stats['assigned_pct']:.1f}%)")
print(f"By haplotype:")
for hap, size in stats['haplotype_sizes'].items():
    print(f"  {hap}: {size:,} bp")
```

## Step 5: Refine Assignments

### Handling Low-Confidence Contigs

```python
# Get contigs needing review
uncertain = results.filter(max_confidence=0.7)

for contig in uncertain.contigs:
    print(f"{contig.contig_id}: {contig.assigned_haplotype} ({contig.confidence:.2f})")

    # Check marker distribution
    marker_counts = contig.marker_counts_by_haplotype()
    for hap, count in marker_counts.items():
        print(f"  {hap}: {count} markers")
```

### Manual Override

```python
# Override assignment for specific contig
results.set_assignment(
    contig_id="contig_003",
    haplotype="B73",
    confidence=0.9,
    is_chimeric=False,
    note="Manual review confirmed B73"
)

# Save updated results
results.to_tsv("contig_assignments_reviewed.tsv")
```

## Advanced Usage

### Phased Assembly Analysis

For assemblies with haplotype-resolved contigs:

```python
# Analyze haplotype-specific assemblies
painter = AssemblyPainter(
    require_consistent=True,  # Require consistent haplotype
    min_confidence=0.8,
)

hap1_results = painter.paint("haplotype1.fasta", markers)
hap2_results = painter.paint("haplotype2.fasta", markers)

# Compare
from haplophaser.assembly.comparison import compare_haplotype_assemblies

comparison = compare_haplotype_assemblies(hap1_results, hap2_results)
print(f"Hap1 predominantly: {comparison.hap1_dominant}")
print(f"Hap2 predominantly: {comparison.hap2_dominant}")
print(f"Swapped contigs: {comparison.n_swapped}")
```

### Integration with Scaffolding

Use haplotype assignments to guide scaffolding:

```python
from haplophaser.assembly.scaffolding import HaplotypeAwareScaffolder

scaffolder = HaplotypeAwareScaffolder(
    genetic_map=genetic_map,
    painting_results=results,
)

# Scaffold with haplotype continuity constraint
scaffolds = scaffolder.scaffold(
    contigs="assembly.fasta",
    enforce_haplotype_continuity=True,
)
```

## Interpreting Results

### Confidence Scores

| Confidence | Interpretation |
|------------|----------------|
| > 0.9 | High confidence assignment |
| 0.7 - 0.9 | Good assignment, minor noise |
| 0.5 - 0.7 | Low confidence, review recommended |
| < 0.5 | Uncertain or mixed haplotype |

### Chimera Indicators

Signs of chimeric contigs:
- Multiple haplotype switches
- Low overall confidence despite many markers
- Inconsistent marker patterns

### Troubleshooting

**Few markers mapped:**
- Check marker positions are in same coordinate system
- Verify assembly quality
- Increase marker set if available

**Many low-confidence assignments:**
- Founders may be too similar
- Assembly may have high heterozygosity
- Consider using more markers

**Unexpected haplotype patterns:**
- May indicate introgression
- Could be assembly error
- Verify with orthogonal data

## Next Steps

- [Haplotype Proportion Tutorial](haplotype_proportion.md) - Generate diagnostic markers
- [Subgenome Analysis Tutorial](subgenome_analysis.md) - Assign subgenomes in polyploids
- [CLI Reference](../cli/index.md) - Command-line options
