"""Tests for expression I/O."""

from __future__ import annotations

from haplophaser.io.expression import (
    ExpressionFormat,
    detect_expression_format,
    load_expression_matrix,
    load_salmon_quant,
    parse_sample_metadata,
)


class TestDetectExpressionFormat:
    """Tests for format detection."""

    def test_detect_salmon(self, tmp_salmon_dir):
        """Test detection of Salmon format."""
        fmt = detect_expression_format(tmp_salmon_dir)
        assert fmt == ExpressionFormat.SALMON

    def test_detect_tpm_matrix(self, tmp_expression_matrix):
        """Test detection of TPM matrix format."""
        fmt = detect_expression_format(tmp_expression_matrix)
        # Generic matrix should be detected as TPM_MATRIX
        assert fmt in (ExpressionFormat.TPM_MATRIX, ExpressionFormat.RAW_COUNTS)


class TestLoadSalmonQuant:
    """Tests for Salmon loading."""

    def test_load_basic(self, tmp_salmon_dir):
        """Test basic Salmon loading."""
        gene_ids, tpm, counts = load_salmon_quant(tmp_salmon_dir)

        assert len(gene_ids) == 4
        assert "gene1" in gene_ids
        assert len(tpm) == 4
        assert tpm[0] == 10.0


class TestLoadExpressionMatrix:
    """Tests for expression matrix loading."""

    def test_load_tpm_matrix(self, tmp_expression_matrix):
        """Test loading TPM matrix file."""
        matrix = load_expression_matrix(tmp_expression_matrix)

        assert matrix.n_genes == 8
        assert matrix.n_samples == 4
        assert matrix.unit in ("tpm", "counts")

    def test_load_with_metadata(self, tmp_expression_matrix, tmp_sample_metadata):
        """Test loading with sample metadata."""
        metadata = parse_sample_metadata(tmp_sample_metadata)
        matrix = load_expression_matrix(tmp_expression_matrix, sample_metadata=metadata)

        assert matrix.n_genes == 8
        # Check that conditions are assigned
        conditions = [s.condition for s in matrix.samples if s.condition]
        assert len(conditions) == 4


class TestParseSampleMetadata:
    """Tests for sample metadata parsing."""

    def test_parse_basic(self, tmp_sample_metadata):
        """Test basic metadata parsing."""
        metadata = parse_sample_metadata(tmp_sample_metadata)

        assert len(metadata) == 4
        assert "sample1" in metadata
        assert metadata["sample1"]["condition"] == "control"
        assert metadata["sample1"]["tissue"] == "leaf"
        assert metadata["sample1"]["replicate"] == 1

    def test_parse_conditions(self, tmp_sample_metadata):
        """Test parsing of condition information."""
        metadata = parse_sample_metadata(tmp_sample_metadata)

        # Check conditions are correctly parsed
        assert metadata["sample1"]["condition"] == "control"
        assert metadata["sample3"]["condition"] == "drought"
