"""Pytest configuration and fixtures for Phaser tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from haplophaser.core.config import PhaserConfig
from haplophaser.core.models import (
    HaplotypeBlock,
    Population,
    PopulationRole,
    Sample,
    Subgenome,
    Variant,
    Window,
)

# ============================================================================
# Sample fixtures
# ============================================================================


@pytest.fixture
def diploid_sample() -> Sample:
    """Create a simple diploid sample."""
    return Sample(name="B73", ploidy=2, population="NAM_founders")


@pytest.fixture
def tetraploid_sample() -> Sample:
    """Create a tetraploid sample with subgenomes."""
    return Sample(
        name="Durum_wheat",
        ploidy=4,
        subgenomes=[
            Subgenome(name="A", ploidy=2),
            Subgenome(name="B", ploidy=2),
        ],
        population="wheat_founders",
    )


@pytest.fixture
def hexaploid_sample() -> Sample:
    """Create a hexaploid sample (like bread wheat)."""
    return Sample(
        name="Chinese_Spring",
        ploidy=6,
        subgenomes=[
            Subgenome(name="A", ploidy=2),
            Subgenome(name="B", ploidy=2),
            Subgenome(name="D", ploidy=2),
        ],
        population="wheat_founders",
    )


@pytest.fixture
def sample_list() -> list[Sample]:
    """Create a list of diploid samples."""
    return [
        Sample(name="B73", ploidy=2, population="founders"),
        Sample(name="Mo17", ploidy=2, population="founders"),
        Sample(name="W22", ploidy=2, population="founders"),
        Sample(name="RIL_001", ploidy=2, population="derived"),
        Sample(name="RIL_002", ploidy=2, population="derived"),
    ]


# ============================================================================
# Population fixtures
# ============================================================================


@pytest.fixture
def founder_population(sample_list: list[Sample]) -> Population:
    """Create a founder population."""
    founder_samples = [s for s in sample_list if s.population == "founders"]
    return Population(
        name="NAM_founders",
        samples=founder_samples,
        role=PopulationRole.FOUNDER,
        description="Nested Association Mapping founder lines",
    )


@pytest.fixture
def derived_population(sample_list: list[Sample]) -> Population:
    """Create a derived population."""
    derived_samples = [s for s in sample_list if s.population == "derived"]
    return Population(
        name="NAM_RILs",
        samples=derived_samples,
        role=PopulationRole.DERIVED,
        description="Recombinant inbred lines",
    )


# ============================================================================
# Variant fixtures
# ============================================================================


@pytest.fixture
def snp_variant() -> Variant:
    """Create a simple diploid SNP variant."""
    return Variant(
        chrom="chr1",
        pos=1000,
        ref="A",
        alt=["T"],
        genotypes={
            "B73": [0, 0],
            "Mo17": [1, 1],
            "RIL_001": [0, 1],
        },
        quality=99.0,
        filter_status="PASS",
    )


@pytest.fixture
def tetraploid_variant() -> Variant:
    """Create a tetraploid variant."""
    return Variant(
        chrom="chr1",
        pos=2000,
        ref="G",
        alt=["C"],
        genotypes={
            "Durum_A": [0, 0, 1, 1],  # Heterozygous by subgenome
            "Durum_B": [0, 0, 0, 1],  # 3 ref, 1 alt
        },
        quality=85.0,
        filter_status="PASS",
    )


@pytest.fixture
def multiallelic_variant() -> Variant:
    """Create a multiallelic variant."""
    return Variant(
        chrom="chr1",
        pos=3000,
        ref="C",
        alt=["T", "G"],
        genotypes={
            "B73": [0, 0],
            "Mo17": [1, 1],
            "W22": [2, 2],
            "RIL_001": [0, 2],
        },
        quality=75.0,
    )


@pytest.fixture
def variant_list(snp_variant: Variant) -> list[Variant]:
    """Create a list of variants for testing."""
    variants = [snp_variant]
    for i in range(10):
        variants.append(
            Variant(
                chrom="chr1",
                pos=1000 + (i + 1) * 100,
                ref="A",
                alt=["T"],
                genotypes={
                    "B73": [0, 0],
                    "Mo17": [1, 1],
                    "RIL_001": [i % 2, (i + 1) % 2],
                },
            )
        )
    return variants


# ============================================================================
# Window fixtures
# ============================================================================


@pytest.fixture
def genomic_window(variant_list: list[Variant]) -> Window:
    """Create a genomic window with variants."""
    return Window(
        chrom="chr1",
        start=0,
        end=100_000,
        variants=variant_list,
        index=0,
    )


@pytest.fixture
def empty_window() -> Window:
    """Create an empty genomic window."""
    return Window(
        chrom="chr1",
        start=100_000,
        end=200_000,
        variants=[],
        index=1,
    )


# ============================================================================
# Haplotype block fixtures
# ============================================================================


@pytest.fixture
def haplotype_block() -> HaplotypeBlock:
    """Create a haplotype block."""
    return HaplotypeBlock(
        chrom="chr1",
        start=0,
        end=500_000,
        sample="RIL_001",
        homolog=0,
        founder="B73",
        proportion=0.95,
        n_variants=150,
        log_likelihood=-50.5,
    )


@pytest.fixture
def haplotype_blocks() -> list[HaplotypeBlock]:
    """Create a series of haplotype blocks for one sample."""
    return [
        HaplotypeBlock(
            chrom="chr1",
            start=0,
            end=500_000,
            sample="RIL_001",
            homolog=0,
            founder="B73",
            proportion=0.95,
            n_variants=150,
        ),
        HaplotypeBlock(
            chrom="chr1",
            start=500_000,
            end=1_000_000,
            sample="RIL_001",
            homolog=0,
            founder="Mo17",
            proportion=0.88,
            n_variants=120,
        ),
        HaplotypeBlock(
            chrom="chr1",
            start=0,
            end=750_000,
            sample="RIL_001",
            homolog=1,
            founder="Mo17",
            proportion=0.92,
            n_variants=180,
        ),
        HaplotypeBlock(
            chrom="chr1",
            start=750_000,
            end=1_000_000,
            sample="RIL_001",
            homolog=1,
            founder="B73",
            proportion=0.85,
            n_variants=60,
        ),
    ]


# ============================================================================
# Configuration fixtures
# ============================================================================


@pytest.fixture
def default_config() -> PhaserConfig:
    """Create default configuration."""
    return PhaserConfig()


@pytest.fixture
def custom_config() -> PhaserConfig:
    """Create custom configuration."""
    return PhaserConfig(
        ploidy=4,
        n_threads=4,
        window={"size": 50_000, "min_variants": 5},
        filter={"min_qual": 20.0, "min_maf": 0.05},
    )


# ============================================================================
# File fixtures
# ============================================================================


@pytest.fixture
def tmp_population_tsv(tmp_path: Path) -> Path:
    """Create a temporary population TSV file."""
    content = """sample\tpopulation\trole\tploidy
B73\tNAM_founders\tfounder\t2
Mo17\tNAM_founders\tfounder\t2
W22\tNAM_founders\tfounder\t2
RIL_001\tNAM_RILs\tderived\t2
RIL_002\tNAM_RILs\tderived\t2
"""
    path = tmp_path / "populations.tsv"
    path.write_text(content)
    return path


@pytest.fixture
def tmp_population_yaml(tmp_path: Path) -> Path:
    """Create a temporary population YAML file."""
    content = """populations:
  - name: NAM_founders
    role: founder
    ploidy: 2
    description: Nested Association Mapping founders
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
"""
    path = tmp_path / "populations.yaml"
    path.write_text(content)
    return path


@pytest.fixture
def tmp_config_yaml(tmp_path: Path) -> Path:
    """Create a temporary config YAML file."""
    content = """window:
  size: 50000
  min_variants: 5

filter:
  min_qual: 20.0
  min_maf: 0.05

ploidy: 4
n_threads: 2
"""
    path = tmp_path / "config.yaml"
    path.write_text(content)
    return path


# ============================================================================
# Integration test data fixtures
# ============================================================================


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Return path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def maize_populations(test_data_dir: Path) -> Path:
    """Population assignments for maize test data."""
    return test_data_dir / "maize_populations.tsv"


@pytest.fixture(scope="session")
def maize_genetic_map(test_data_dir: Path) -> Path:
    """Genetic map for maize test region."""
    return test_data_dir / "maize_genetic_map.tsv"


@pytest.fixture(scope="session")
def maize_subgenomes(test_data_dir: Path) -> Path:
    """Known subgenome assignments for maize test region."""
    return test_data_dir / "maize_subgenomes.bed"


@pytest.fixture(scope="session")
def maize_expression(test_data_dir: Path) -> Path:
    """Expression matrix for maize test genes."""
    return test_data_dir / "maize_expression.tsv"


@pytest.fixture(scope="session")
def maize_sample_metadata(test_data_dir: Path) -> Path:
    """Sample metadata for maize expression data."""
    return test_data_dir / "maize_sample_metadata.tsv"


@pytest.fixture(scope="session")
def maize_homeologs(test_data_dir: Path) -> Path:
    """Homeolog pairs for maize test genes."""
    return test_data_dir / "maize_homeologs.tsv"


# ============================================================================
# Visualization test fixtures
# ============================================================================


@pytest.fixture
def test_fai(tmp_path: Path) -> Path:
    """Create a test FAI file for visualization."""
    content = """chr1\t10000000\t6\t80\t81
chr2\t8000000\t10080000\t80\t81
chr3\t6000000\t18080000\t80\t81
"""
    path = tmp_path / "test_genome.fa.fai"
    path.write_text(content)
    return path


@pytest.fixture
def test_haplotypes(tmp_path: Path) -> Path:
    """Create a test haplotype BED file."""
    content = """#chrom\tstart\tend\tfounder\tscore\tstrand
chr1\t0\t2000000\tB73\t950\t.
chr1\t2000000\t5000000\tMo17\t880\t.
chr1\t5000000\t7000000\tB73\t920\t.
chr1\t7000000\t10000000\tW22\t850\t.
chr2\t0\t4000000\tB73\t900\t.
chr2\t4000000\t8000000\tMo17\t870\t.
"""
    path = tmp_path / "haplotypes.bed"
    path.write_text(content)
    return path


@pytest.fixture
def test_expression_bias(tmp_path: Path) -> Path:
    """Create a test expression bias results file."""
    import numpy as np

    np.random.seed(42)
    n_pairs = 50
    log2ratios = np.random.normal(0, 0.5, n_pairs)
    fdrs = np.random.uniform(0, 0.2, n_pairs)
    mean_expr = np.random.uniform(1, 5, n_pairs)

    content = "gene1\tgene2\tmean_log2ratio\tfdr\tmean_expression\n"
    for i in range(n_pairs):
        content += f"gene_{i}_a\tgene_{i}_b\t{log2ratios[i]:.4f}\t{fdrs[i]:.4f}\t{mean_expr[i]:.4f}\n"

    path = tmp_path / "expression_bias.tsv"
    path.write_text(content)
    return path
