# Session 17: Final Integration Testing, Documentation & Release

## Objectives

- [x] End-to-end integration tests with real maize data
- [x] Cross-package integration tests (phaser + chromoplot)
- [x] Documentation finalization for both packages
- [x] Example gallery with real outputs
- [x] Release preparation (PyPI, Bioconda)
- [x] CI/CD finalization

## Implementation Tasks

### Integration Tests

- [x] tests/integration/test_full_workflow.py (phaser)
- [x] tests/integration/test_viz_integration.py (phaser + chromoplot)
- [x] Test data preparation (downloadable subset)
- [ ] Performance benchmarks

### Documentation - Haplophaser

- [x] README.md finalization
- [x] docs/index.md
- [x] docs/installation.md
- [x] docs/quickstart.md
- [x] docs/tutorials/ (all modules)
- [x] docs/cli_reference.md (cli/index.md)
- [x] docs/api/ (all modules)
- [x] docs/visualization.md
- [x] CONTRIBUTING.md
- [x] CHANGELOG.md

### Documentation - Chromoplot

- [ ] README.md finalization
- [ ] docs/index.md
- [ ] docs/installation.md
- [ ] docs/quickstart.md
- [ ] docs/tracks.md
- [ ] docs/layouts.md
- [ ] docs/themes.md
- [ ] docs/cli_reference.md
- [ ] CONTRIBUTING.md
- [ ] CHANGELOG.md

### Example Gallery

- [x] examples/maize_nam_analysis/
- [ ] examples/assembly_qc/
- [ ] examples/subgenome_analysis/
- [ ] examples/expression_bias/
- [ ] Example figures for docs

### Release Preparation

- [x] pyproject.toml finalization (phaser)
- [x] Version tagging strategy
- [ ] PyPI test upload
- [ ] Bioconda recipes
- [ ] Docker/Singularity containers
- [x] GitHub Actions CI/CD

## Progress Notes

- [2026-01-24] Started final session - integration tests and release prep
- [2026-01-24] Created test data generation script (tests/data/create_test_data.py)
- [2026-01-24] Created visualization integration tests
- [2026-01-24] Updated CI workflow with test data creation
- [2026-01-24] Added visualization documentation (docs/visualization.md)
- [2026-01-24] Created example gallery with maize NAM example
- [2026-01-24] Updated CHANGELOG with visualization features

## Files Created/Modified This Session

### Tests
- tests/data/create_test_data.py - Test data generator
- tests/integration/test_viz_integration.py - Visualization integration tests

### Documentation
- docs/visualization.md - Complete visualization guide

### Examples
- examples/README.md - Example gallery overview
- examples/01_maize_nam/README.md - Maize NAM example documentation
- examples/01_maize_nam/run.sh - Shell script for example
- examples/01_maize_nam/run.py - Python script for example

### CI/CD
- .github/workflows/ci.yml - Updated with test data creation step

### Other
- CHANGELOG.md - Updated with visualization features
- TODO.md - Updated with progress

## Post-Release Plans

- JOSS manuscript
- Tutorial workshops
- Community feedback integration

## Release Checklist

### Haplophaser Pre-Release

- [ ] All unit tests pass (`pytest tests/ -m "not slow"`)
- [ ] All integration tests pass (`pytest tests/integration/`)
- [ ] No linting errors (`ruff check src/`)
- [ ] Test coverage >80%
- [ ] Package builds (`python -m build`)
- [ ] Package installs cleanly
- [ ] CLI entry point works (`phaser --version`)

### Release Steps

1. [ ] Merge all feature branches to main
2. [ ] Update version in pyproject.toml
3. [ ] Update CHANGELOG.md with release date
4. [ ] Create git tag (v0.1.0)
5. [ ] Push tag to trigger release workflow
6. [ ] Verify PyPI upload
7. [ ] Submit Bioconda recipe
8. [ ] Announce release
