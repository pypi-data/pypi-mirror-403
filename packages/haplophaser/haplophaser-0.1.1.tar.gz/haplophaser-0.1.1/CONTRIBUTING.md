# Contributing to Haplophaser

Thank you for your interest in contributing to Haplophaser! This document provides guidelines and information for contributors.

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to maintain a welcoming and inclusive community.

## How to Contribute

### Reporting Issues

1. **Check existing issues** - Search [GitHub Issues](https://github.com/aseetharam/haplophaser/issues) to see if your issue has already been reported.

2. **Create a new issue** - If not found, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce (for bugs)
   - Expected vs. actual behavior
   - System information (OS, Python version, Haplophaser version)
   - Relevant input data (anonymized if necessary)

### Suggesting Features

1. Open an issue with the "enhancement" label
2. Describe the feature and its use case
3. Explain how it fits with Haplophaser's goals

### Contributing Code

#### Getting Started

1. **Fork the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/haplophaser.git
   cd phaser
   ```

2. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -e ".[dev]"
   ```

3. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### Development Workflow

1. **Make your changes**
   - Follow the coding style (see below)
   - Add tests for new functionality
   - Update documentation as needed

2. **Run tests locally**
   ```bash
   # Run all tests
   pytest tests/ -v

   # Run specific test file
   pytest tests/test_bias.py -v

   # Run with coverage
   pytest tests/ --cov=phaser --cov-report=html
   ```

3. **Run linting**
   ```bash
   # Check code style
   ruff check src/haplophaser tests

   # Format code
   ruff format src/haplophaser tests

   # Type checking
   mypy src/haplophaser
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: description of changes"
   ```

5. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request on GitHub.

### Pull Request Guidelines

- **One feature/fix per PR** - Keep PRs focused
- **Clear description** - Explain what and why
- **Reference issues** - Link related issues
- **Pass CI** - All tests and checks must pass
- **Documentation** - Update docs for user-facing changes
- **Tests** - Add tests for new functionality

## Coding Style

### Python Style

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting.

```python
# Good: Clear, descriptive names
def calculate_expression_bias(
    homeolog_expression: HomeologExpression,
    min_expr: float = 1.0,
    log2_threshold: float = 1.0,
) -> BiasResult:
    """Calculate expression bias for homeolog pairs.

    Args:
        homeolog_expression: Expression data for homeolog pairs.
        min_expr: Minimum expression threshold (TPM).
        log2_threshold: Threshold for significant bias.

    Returns:
        BiasResult containing bias statistics for all pairs.
    """
    ...
```

### Key Conventions

- **Type hints** - Use type annotations for all public functions
- **Docstrings** - Google-style docstrings for all public functions/classes
- **Imports** - Group into standard library, third-party, local
- **Line length** - Maximum 100 characters
- **Naming** - snake_case for functions/variables, PascalCase for classes

### Testing

- Use pytest for all tests
- Aim for high coverage of critical code paths
- Use fixtures for shared test setup
- Test edge cases and error conditions

```python
# Example test
def test_calculate_bias_with_valid_input(sample_homeolog_expr):
    """Test bias calculation with typical input."""
    result = calculate_expression_bias(
        sample_homeolog_expr,
        min_expr=1.0,
    )

    assert result.n_pairs > 0
    assert all(pair.log2_ratio is not None for pair in result.pairs)
```

### Documentation

- Keep docstrings up to date
- Add examples for complex functions
- Update tutorials for significant changes
- Use clear, jargon-free language when possible

## Project Structure

```
phaser/
├── src/haplophaser/          # Main package
│   ├── io/              # Input/output modules
│   ├── markers/         # Marker discovery
│   ├── proportion/      # Proportion estimation
│   ├── assembly/        # Assembly analysis
│   ├── subgenome/       # Subgenome analysis
│   ├── expression/      # Expression analysis
│   ├── models/          # Data models
│   └── cli/             # Command-line interface
├── tests/               # Test suite
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── data/            # Test data
├── docs/                # Documentation
└── examples/            # Example workflows
```

## Areas for Contribution

### Good First Issues

Look for issues labeled "good first issue" for beginner-friendly tasks:
- Documentation improvements
- Test coverage
- Bug fixes with clear reproduction steps

### Wanted Features

- Additional species presets
- New visualization exports
- Performance optimizations
- Additional input format support

## Questions?

- Open a [GitHub Discussion](https://github.com/aseetharam/haplophaser/discussions)
- Check the [FAQ](docs/faq.md)
- Review existing issues and discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
