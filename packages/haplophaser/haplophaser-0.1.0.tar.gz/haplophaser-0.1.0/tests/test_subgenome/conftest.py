"""Pytest fixtures for subgenome tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from haplophaser.subgenome.models import (
    GeneSubgenomeCall,
    HomeologPair,
    HomeologResult,
    Subgenome,
    SubgenomeAssignment,
    SubgenomeAssignmentResult,
    SubgenomeConfig,
    SubgenomeMarker,
    SyntenyBlock,
)

# ============================================================================
# Configuration fixtures
# ============================================================================


@pytest.fixture
def maize_config() -> SubgenomeConfig:
    """Create maize subgenome configuration."""
    return SubgenomeConfig.maize_default()


@pytest.fixture
def wheat_config() -> SubgenomeConfig:
    """Create wheat subgenome configuration."""
    return SubgenomeConfig.wheat_default()


@pytest.fixture
def custom_config() -> SubgenomeConfig:
    """Create custom subgenome configuration."""
    return SubgenomeConfig(
        subgenomes=[
            Subgenome("SG1", "Dominant", "#ff0000"),
            Subgenome("SG2", "Recessive", "#0000ff"),
        ],
        reference_species="TestRef",
        outgroup_species=["Outgroup"],
    )


# ============================================================================
# Assignment fixtures
# ============================================================================


@pytest.fixture
def subgenome_assignment() -> SubgenomeAssignment:
    """Create a single subgenome assignment."""
    return SubgenomeAssignment(
        chrom="chr1",
        start=0,
        end=1_000_000,
        subgenome="maize1",
        confidence=0.95,
        evidence="synteny",
        evidence_details={"block_id": "block1"},
    )


@pytest.fixture
def subgenome_assignments() -> list[SubgenomeAssignment]:
    """Create a list of subgenome assignments."""
    return [
        SubgenomeAssignment(
            chrom="chr1",
            start=0,
            end=1_000_000,
            subgenome="maize1",
            confidence=0.95,
            evidence="synteny",
        ),
        SubgenomeAssignment(
            chrom="chr1",
            start=1_000_000,
            end=2_000_000,
            subgenome="maize2",
            confidence=0.85,
            evidence="synteny",
        ),
        SubgenomeAssignment(
            chrom="chr2",
            start=0,
            end=500_000,
            subgenome="maize1",
            confidence=0.90,
            evidence="orthologs",
        ),
    ]


@pytest.fixture
def assignment_result(
    subgenome_assignments: list[SubgenomeAssignment],
    maize_config: SubgenomeConfig,
) -> SubgenomeAssignmentResult:
    """Create a subgenome assignment result."""
    return SubgenomeAssignmentResult(
        query_name="test_assembly",
        config=maize_config,
        assignments=subgenome_assignments,
        method="synteny",
    )


# ============================================================================
# Synteny fixtures
# ============================================================================


@pytest.fixture
def synteny_block() -> SyntenyBlock:
    """Create a single synteny block."""
    return SyntenyBlock(
        query_chrom="chr1",
        query_start=0,
        query_end=1_000_000,
        ref_chrom="chr1",
        ref_start=500_000,
        ref_end=1_500_000,
        orientation="+",
        n_anchors=50,
        identity=0.95,
        block_id="block1",
    )


@pytest.fixture
def synteny_blocks() -> list[SyntenyBlock]:
    """Create a list of synteny blocks."""
    return [
        SyntenyBlock(
            query_chrom="chr1",
            query_start=0,
            query_end=1_000_000,
            ref_chrom="chr1",
            ref_start=0,
            ref_end=1_000_000,
            orientation="+",
            n_anchors=50,
            identity=0.95,
            block_id="block1",
        ),
        SyntenyBlock(
            query_chrom="chr1",
            query_start=1_000_000,
            query_end=2_000_000,
            ref_chrom="chr5",
            ref_start=0,
            ref_end=1_000_000,
            orientation="-",
            n_anchors=40,
            identity=0.90,
            block_id="block2",
        ),
        SyntenyBlock(
            query_chrom="chr2",
            query_start=0,
            query_end=500_000,
            ref_chrom="chr2",
            ref_start=0,
            ref_end=500_000,
            orientation="+",
            n_anchors=25,
            identity=0.92,
            block_id="block3",
        ),
    ]


# ============================================================================
# Marker fixtures
# ============================================================================


@pytest.fixture
def subgenome_marker() -> SubgenomeMarker:
    """Create a single subgenome marker."""
    return SubgenomeMarker(
        marker_id="chr1_1000",
        chrom="chr1",
        pos=1000,
        ref="A",
        alt="G",
        subgenome_alleles={"maize1": "A", "maize2": "G"},
        divergence=0.05,
        synteny_block="block1",
        confidence=0.9,
    )


@pytest.fixture
def subgenome_markers() -> list[SubgenomeMarker]:
    """Create a list of subgenome markers."""
    return [
        SubgenomeMarker(
            marker_id="chr1_1000",
            chrom="chr1",
            pos=1000,
            ref="A",
            alt="G",
            subgenome_alleles={"maize1": "A", "maize2": "G"},
            divergence=0.05,
            confidence=0.9,
        ),
        SubgenomeMarker(
            marker_id="chr1_2000",
            chrom="chr1",
            pos=2000,
            ref="C",
            alt="T",
            subgenome_alleles={"maize1": "C", "maize2": "T"},
            divergence=0.06,
            confidence=0.85,
        ),
        SubgenomeMarker(
            marker_id="chr2_500",
            chrom="chr2",
            pos=500,
            ref="G",
            alt="A",
            subgenome_alleles={"maize1": "G", "maize2": "A"},
            divergence=0.04,
            confidence=0.92,
        ),
    ]


# ============================================================================
# Gene fixtures
# ============================================================================


@pytest.fixture
def gene_call() -> GeneSubgenomeCall:
    """Create a single gene subgenome call."""
    return GeneSubgenomeCall(
        gene_id="Zm00001d001234",
        chrom="chr1",
        start=100_000,
        end=105_000,
        orthogroup="OG0000001",
        subgenome="maize1",
        confidence=0.85,
        tree_support=95.0,
    )


@pytest.fixture
def gene_calls() -> list[GeneSubgenomeCall]:
    """Create a list of gene subgenome calls."""
    return [
        GeneSubgenomeCall(
            gene_id="Zm00001d001234",
            chrom="chr1",
            start=100_000,
            end=105_000,
            orthogroup="OG0000001",
            subgenome="maize1",
            confidence=0.85,
        ),
        GeneSubgenomeCall(
            gene_id="Zm00001d005678",
            chrom="chr1",
            start=200_000,
            end=208_000,
            orthogroup="OG0000002",
            subgenome="maize2",
            confidence=0.80,
        ),
        GeneSubgenomeCall(
            gene_id="Zm00001d009999",
            chrom="chr2",
            start=50_000,
            end=55_000,
            orthogroup="OG0000003",
            subgenome=None,
            confidence=0.0,
        ),
    ]


# ============================================================================
# Homeolog fixtures
# ============================================================================


@pytest.fixture
def homeolog_pair() -> HomeologPair:
    """Create a single homeolog pair."""
    return HomeologPair(
        gene1_id="Zm00001d001234",
        gene1_chrom="chr1",
        gene1_subgenome="maize1",
        gene2_id="Zm00001d054321",
        gene2_chrom="chr5",
        gene2_subgenome="maize2",
        ks=0.15,
        ka=0.02,
        synteny_support=True,
        sequence_identity=0.85,
        confidence=0.95,
    )


@pytest.fixture
def homeolog_pairs() -> list[HomeologPair]:
    """Create a list of homeolog pairs."""
    return [
        HomeologPair(
            gene1_id="Zm00001d001234",
            gene1_chrom="chr1",
            gene1_subgenome="maize1",
            gene2_id="Zm00001d054321",
            gene2_chrom="chr5",
            gene2_subgenome="maize2",
            ks=0.15,
            ka=0.02,
            synteny_support=True,
            sequence_identity=0.85,
            confidence=0.95,
        ),
        HomeologPair(
            gene1_id="Zm00001d002000",
            gene1_chrom="chr1",
            gene1_subgenome="maize1",
            gene2_id="Zm00001d055000",
            gene2_chrom="chr5",
            gene2_subgenome="maize2",
            ks=0.12,
            ka=0.015,
            synteny_support=True,
            sequence_identity=0.88,
            confidence=0.92,
        ),
        HomeologPair(
            gene1_id="Zm00001d003000",
            gene1_chrom="chr2",
            gene1_subgenome="maize2",
            gene2_id="Zm00001d056000",
            gene2_chrom="chr4",
            gene2_subgenome="maize1",
            ks=0.18,
            ka=0.03,
            synteny_support=False,
            sequence_identity=0.82,
            confidence=0.80,
        ),
    ]


@pytest.fixture
def homeolog_result(
    homeolog_pairs: list[HomeologPair],
    maize_config: SubgenomeConfig,
) -> HomeologResult:
    """Create homeolog detection result."""
    return HomeologResult(
        pairs=homeolog_pairs,
        config=maize_config,
        parameters={"method": "synteny", "max_ks": 1.0},
    )


# ============================================================================
# File fixtures
# ============================================================================


@pytest.fixture
def tmp_reference_assignments(tmp_path: Path) -> Path:
    """Create a temporary reference assignments BED file."""
    content = """chr1\t0\t1000000\tmaize1
chr1\t1000000\t2000000\tmaize2
chr2\t0\t500000\tmaize1
chr2\t500000\t1000000\tmaize2
chr5\t0\t1000000\tmaize2
"""
    path = tmp_path / "reference_assignments.bed"
    path.write_text(content)
    return path


@pytest.fixture
def tmp_synteny_tsv(tmp_path: Path) -> Path:
    """Create a temporary synteny TSV file."""
    content = """query_chrom\tquery_start\tquery_end\tref_chrom\tref_start\tref_end\torientation\tn_anchors\tidentity
chr1\t0\t1000000\tchr1\t0\t1000000\t+\t50\t0.95
chr1\t1000000\t2000000\tchr5\t0\t1000000\t-\t40\t0.90
chr2\t0\t500000\tchr2\t0\t500000\t+\t25\t0.92
"""
    path = tmp_path / "synteny.tsv"
    path.write_text(content)
    return path


@pytest.fixture
def tmp_genes_gff(tmp_path: Path) -> Path:
    """Create a temporary genes GFF3 file."""
    content = """##gff-version 3
chr1\ttest\tgene\t100001\t105000\t.\t+\t.\tID=gene1;Name=Gene1
chr1\t test\tgene\t200001\t208000\t.\t-\t.\tID=gene2;Name=Gene2
chr1\ttest\tgene\t500001\t510000\t.\t+\t.\tID=gene3;Name=Gene3
chr2\ttest\tgene\t50001\t55000\t.\t+\t.\tID=gene4;Name=Gene4
chr2\ttest\tgene\t100001\t108000\t.\t-\t.\tID=gene5;Name=Gene5
chr5\ttest\tgene\t200001\t210000\t.\t+\t.\tID=gene6;Name=Gene6
"""
    path = tmp_path / "genes.gff3"
    path.write_text(content)
    return path


@pytest.fixture
def tmp_homeolog_pairs(tmp_path: Path) -> Path:
    """Create a temporary homeolog pairs TSV file."""
    content = """gene1_id\tgene1_chrom\tgene1_subgenome\tgene2_id\tgene2_chrom\tgene2_subgenome\tks\tka\tsynteny_support\tsequence_identity\tconfidence
gene1\tchr1\tmaize1\tgene6\tchr5\tmaize2\t0.15\t0.02\ttrue\t0.85\t0.95
gene3\tchr1\tmaize1\tgene5\tchr2\tmaize2\t0.12\t0.015\ttrue\t0.88\t0.92
"""
    path = tmp_path / "homeolog_pairs.tsv"
    path.write_text(content)
    return path


@pytest.fixture
def tmp_orthogroups(tmp_path: Path) -> Path:
    """Create a temporary orthogroups file."""
    content = """Orthogroup\tSpecies1\tSpecies2\tOutgroup
OG0000001\tgene1, gene2\tref_gene1\toutgroup_gene1
OG0000002\tgene3\tref_gene2, ref_gene3\toutgroup_gene2
OG0000003\tgene4, gene5, gene6\tref_gene4\toutgroup_gene3
"""
    path = tmp_path / "Orthogroups.tsv"
    path.write_text(content)
    return path
