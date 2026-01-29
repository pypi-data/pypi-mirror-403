# Haplophaser

**P**olyploid **H**aplotype **A**nalysis for **S**equenced **E**ukaryotic **R**eferences

Haplophaser is a comprehensive toolkit for haplotype analysis in complex genomes, with full support for polyploids.

## Features

### Haplotype Proportion Estimation
Quantify founder contributions in derived lines from VCF data using diagnostic markers and statistical methods including HMM-based inference.

### Assembly Painting
Assign contigs to haplotypes or subgenomes based on marker patterns, enabling visualization of haplotype composition across genome assemblies.

### Chimera Detection
Identify potential misassemblies by detecting unexpected haplotype switches within contigs.

### Linkage-Informed Scaffolding
Order and orient contigs using genetic maps combined with haplotype continuity constraints.

### Subgenome Deconvolution
Assign genomic regions to ancestral subgenomes in paleopolyploids like maize, wheat, and Brassica using synteny and ortholog evidence.

### Expression Bias Analysis
Quantify homeolog expression bias and test for subgenome dominance in RNA-seq data.

## Quick Example

```bash
# Find diagnostic markers between founders
haplophaser find-markers \
    --vcf founders.vcf.gz \
    --populations founders.tsv \
    --output markers.tsv

# Estimate haplotype proportions in derived lines
haplophaser proportion \
    --vcf derived.vcf.gz \
    --markers markers.tsv \
    --populations samples.tsv \
    --output-prefix results/proportions

# Analyze expression bias between homeologs
haplophaser expression-bias \
    expression_matrix.tsv \
    homeolog_pairs.tsv \
    --output expression_bias.tsv
```

## Installation

```bash
pip install haplophaser

# Or with conda (coming soon)
conda install -c bioconda phaser
```

See the [Installation Guide](installation.md) for detailed instructions.

## Documentation

- [Installation Guide](installation.md) - Installing phaser and dependencies
- [Quick Start](quickstart.md) - Get started in 5 minutes
- [Tutorials](tutorials/index.md) - Step-by-step analysis guides
- [CLI Reference](cli/index.md) - Command-line interface documentation
- [API Reference](api/index.md) - Python API documentation
- [File Formats](file_formats.md) - Input and output format specifications

## Supported Species

Haplophaser includes built-in configurations for:

- **Maize** (*Zea mays*) - Paleotetraploid with maize1/maize2 subgenomes
- **Wheat** (*Triticum aestivum*) - Hexaploid with A/B/D subgenomes
- **Brassica** (*Brassica napus*) - Allotetraploid with A/C subgenomes

Custom configurations can be created for any polyploid species.

## Citation

If you use Haplophaser in your research, please cite:

> Seetharam AS, et al. (2025). Haplophaser: A comprehensive toolkit for haplotype analysis in polyploid genomes. *In preparation*.

## License

Haplophaser is released under the MIT License. See [LICENSE](https://github.com/aseetharam/haplophaser/blob/main/LICENSE) for details.

## Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/aseetharam/haplophaser/blob/main/CONTRIBUTING.md) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/aseetharam/haplophaser/issues)
- **Discussions**: [GitHub Discussions](https://github.com/aseetharam/haplophaser/discussions)
