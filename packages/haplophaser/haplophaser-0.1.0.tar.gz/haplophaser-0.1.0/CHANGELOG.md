# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Phaser toolkit
- Haplotype proportion estimation from VCF data
  - Diagnostic marker discovery
  - Window-based proportion estimation
  - HMM-based haplotype block inference
- Assembly painting functionality
  - Contig-to-haplotype assignment
  - Chimera detection
- Subgenome analysis for paleopolyploids
  - Synteny-based subgenome assignment
  - Ortholog-based subgenome assignment
  - Integrated evidence assignment
  - Homeolog pair identification
  - Fractionation analysis
- Expression bias analysis
  - Homeolog expression extraction
  - Bias calculation and categorization
  - Subgenome dominance testing
  - Condition-specific bias comparison
- Visualization integration with chromoplot
  - Haplotype proportion figures
  - Whole-genome haplotype layouts
  - Assembly painting visualization
  - Subgenome assignment figures
  - Expression bias plots (MA, distribution)
  - Synteny/comparative visualization
- Command-line interface (CLI) for all analyses
- Visualization CLI commands (`haplophaser viz`)
- Python API for programmatic access
- Comprehensive documentation and tutorials
- Species presets for maize, wheat, and Brassica

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- N/A (initial release)

## [0.1.0] - TBD

Initial public release.

### Features
- Core haplotype analysis functionality
- Expression bias analysis
- Subgenome deconvolution
- Assembly painting
- Full CLI and Python API
- Documentation and tutorials

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 0.1.0 | TBD | Initial release |

[Unreleased]: https://github.com/aseetharam/phaser/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/aseetharam/phaser/releases/tag/v0.1.0
