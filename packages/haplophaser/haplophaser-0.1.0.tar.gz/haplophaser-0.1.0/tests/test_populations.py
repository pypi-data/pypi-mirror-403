"""Tests for population I/O functions."""

from __future__ import annotations

from pathlib import Path

import pytest

from haplophaser.core.models import Population, PopulationRole, Sample
from haplophaser.io.populations import (
    PopulationSpec,
    get_all_samples,
    get_derived_sample_names,
    get_founder_sample_names,
    get_samples_by_role,
    infer_populations_from_vcf,
    load_populations,
    load_populations_tsv,
    load_populations_yaml,
    validate_populations_against_vcf,
    write_populations_tsv,
    write_populations_yaml,
)


class TestPopulationSpec:
    """Tests for PopulationSpec helper class."""

    def test_create_spec(self) -> None:
        """Test creating a population spec."""
        spec = PopulationSpec(
            name="founders",
            role=PopulationRole.FOUNDER,
            samples=["B73", "Mo17"],
            ploidy=2,
        )
        assert spec.name == "founders"
        assert spec.role == PopulationRole.FOUNDER
        assert len(spec.samples) == 2

    def test_parse_role_from_string(self) -> None:
        """Test role parsing from string."""
        spec = PopulationSpec(
            name="test",
            role="founder",
            samples=[],
        )
        assert spec.role == PopulationRole.FOUNDER

    def test_to_population(self) -> None:
        """Test converting spec to Population."""
        spec = PopulationSpec(
            name="founders",
            role=PopulationRole.FOUNDER,
            samples=["B73", "Mo17"],
            ploidy=2,
            description="Test population",
        )
        pop = spec.to_population()

        assert isinstance(pop, Population)
        assert pop.name == "founders"
        assert len(pop.samples) == 2
        assert all(isinstance(s, Sample) for s in pop.samples)
        assert all(s.ploidy == 2 for s in pop.samples)


class TestLoadPopulationsTsv:
    """Tests for TSV population file loading."""

    def test_load_basic_tsv(self, tmp_population_tsv: Path) -> None:
        """Test loading basic TSV file."""
        populations = load_populations_tsv(tmp_population_tsv)

        assert len(populations) == 2

        # Check founder population
        founders = [p for p in populations if p.role == PopulationRole.FOUNDER]
        assert len(founders) == 1
        assert len(founders[0].samples) == 3
        assert "B73" in founders[0].sample_names

        # Check derived population
        derived = [p for p in populations if p.role == PopulationRole.DERIVED]
        assert len(derived) == 1
        assert len(derived[0].samples) == 2

    def test_load_without_ploidy_column(self, tmp_path: Path) -> None:
        """Test loading TSV without ploidy column (uses default)."""
        content = """sample\tpopulation\trole
B73\tfounders\tfounder
Mo17\tfounders\tfounder
"""
        path = tmp_path / "no_ploidy.tsv"
        path.write_text(content)

        populations = load_populations_tsv(path)
        assert len(populations) == 1
        assert all(s.ploidy == 2 for s in populations[0].samples)

    def test_missing_file(self, tmp_path: Path) -> None:
        """Test error on missing file."""
        with pytest.raises(FileNotFoundError):
            load_populations_tsv(tmp_path / "missing.tsv")

    def test_missing_columns(self, tmp_path: Path) -> None:
        """Test error when required columns missing."""
        content = """sample\tpopulation
B73\tfounders
"""
        path = tmp_path / "missing_col.tsv"
        path.write_text(content)

        with pytest.raises(ValueError, match="Missing required columns"):
            load_populations_tsv(path)

    def test_comments_and_blank_lines(self, tmp_path: Path) -> None:
        """Test that comments and blank lines are skipped."""
        content = """sample\tpopulation\trole
# This is a comment
B73\tfounders\tfounder

Mo17\tfounders\tfounder
"""
        path = tmp_path / "with_comments.tsv"
        path.write_text(content)

        populations = load_populations_tsv(path)
        assert len(populations) == 1
        assert len(populations[0].samples) == 2


class TestLoadPopulationsYaml:
    """Tests for YAML population file loading."""

    def test_load_basic_yaml(self, tmp_population_yaml: Path) -> None:
        """Test loading basic YAML file."""
        populations = load_populations_yaml(tmp_population_yaml)

        assert len(populations) == 2

        founders = [p for p in populations if p.name == "NAM_founders"][0]
        assert founders.role == PopulationRole.FOUNDER
        assert len(founders.samples) == 3
        assert founders.description == "Nested Association Mapping founders"

    def test_load_with_subgenomes(self, tmp_path: Path) -> None:
        """Test loading YAML with subgenome definitions."""
        content = """populations:
  - name: wheat
    role: founder
    ploidy: 6
    subgenomes:
      - name: A
        ploidy: 2
      - name: B
        ploidy: 2
      - name: D
        ploidy: 2
    samples:
      - Chinese_Spring
"""
        path = tmp_path / "wheat.yaml"
        path.write_text(content)

        populations = load_populations_yaml(path)
        assert len(populations) == 1

        sample = populations[0].samples[0]
        assert sample.ploidy == 6
        assert len(sample.subgenomes) == 3
        assert sample.subgenomes[0].name == "A"

    def test_load_with_sample_overrides(self, tmp_path: Path) -> None:
        """Test loading YAML with per-sample overrides."""
        content = """populations:
  - name: mixed
    role: derived
    ploidy: 2
    samples:
      - name: diploid_sample
        ploidy: 2
      - name: tetraploid_sample
        ploidy: 4
        subgenomes:
          - name: A
            ploidy: 2
          - name: B
            ploidy: 2
"""
        path = tmp_path / "mixed.yaml"
        path.write_text(content)

        populations = load_populations_yaml(path)
        samples = populations[0].samples

        assert samples[0].ploidy == 2
        assert samples[1].ploidy == 4
        assert len(samples[1].subgenomes) == 2

    def test_missing_file(self, tmp_path: Path) -> None:
        """Test error on missing file."""
        with pytest.raises(FileNotFoundError):
            load_populations_yaml(tmp_path / "missing.yaml")

    def test_empty_file(self, tmp_path: Path) -> None:
        """Test error on empty file."""
        path = tmp_path / "empty.yaml"
        path.write_text("")

        with pytest.raises(ValueError, match="Empty YAML"):
            load_populations_yaml(path)

    def test_missing_populations_key(self, tmp_path: Path) -> None:
        """Test error when populations key missing."""
        content = """samples:
  - B73
"""
        path = tmp_path / "bad.yaml"
        path.write_text(content)

        with pytest.raises(ValueError, match="populations"):
            load_populations_yaml(path)


class TestWritePopulationsTsv:
    """Tests for TSV population file writing."""

    def test_write_basic_tsv(self, tmp_path: Path) -> None:
        """Test writing populations to TSV."""
        populations = [
            Population(
                name="founders",
                role=PopulationRole.FOUNDER,
                samples=[
                    Sample(name="B73", ploidy=2, population="founders"),
                    Sample(name="Mo17", ploidy=2, population="founders"),
                ],
            )
        ]

        path = tmp_path / "output.tsv"
        write_populations_tsv(populations, path)

        assert path.exists()
        content = path.read_text()
        lines = content.strip().split("\n")

        assert len(lines) == 3  # Header + 2 samples
        assert "sample\tpopulation\trole\tploidy" in lines[0]
        assert "B73\tfounders\tfounder\t2" in lines[1]

    def test_write_without_ploidy(self, tmp_path: Path) -> None:
        """Test writing TSV without ploidy column."""
        populations = [
            Population(
                name="test",
                role=PopulationRole.DERIVED,
                samples=[Sample(name="S1", ploidy=2)],
            )
        ]

        path = tmp_path / "no_ploidy.tsv"
        write_populations_tsv(populations, path, include_ploidy=False)

        content = path.read_text()
        assert "ploidy" not in content

    def test_roundtrip_tsv(self, tmp_path: Path, tmp_population_tsv: Path) -> None:
        """Test TSV write/read roundtrip."""
        original = load_populations_tsv(tmp_population_tsv)

        output_path = tmp_path / "roundtrip.tsv"
        write_populations_tsv(original, output_path)
        reloaded = load_populations_tsv(output_path)

        assert len(reloaded) == len(original)
        for orig_pop, reload_pop in zip(original, reloaded):
            assert orig_pop.name == reload_pop.name
            assert len(orig_pop.samples) == len(reload_pop.samples)


class TestWritePopulationsYaml:
    """Tests for YAML population file writing."""

    def test_write_basic_yaml(self, tmp_path: Path) -> None:
        """Test writing populations to YAML."""
        populations = [
            Population(
                name="founders",
                role=PopulationRole.FOUNDER,
                samples=[
                    Sample(name="B73", ploidy=2, population="founders"),
                    Sample(name="Mo17", ploidy=2, population="founders"),
                ],
                description="Test founders",
            )
        ]

        path = tmp_path / "output.yaml"
        write_populations_yaml(populations, path)

        assert path.exists()
        content = path.read_text()
        assert "populations:" in content
        assert "name: founders" in content

    def test_roundtrip_yaml(self, tmp_path: Path, tmp_population_yaml: Path) -> None:
        """Test YAML write/read roundtrip."""
        original = load_populations_yaml(tmp_population_yaml)

        output_path = tmp_path / "roundtrip.yaml"
        write_populations_yaml(original, output_path)
        reloaded = load_populations_yaml(output_path)

        assert len(reloaded) == len(original)
        for orig_pop, reload_pop in zip(original, reloaded):
            assert orig_pop.name == reload_pop.name
            assert len(orig_pop.samples) == len(reload_pop.samples)


class TestInferPopulationsFromVcf:
    """Tests for population inference from VCF samples."""

    def test_infer_single_population(self) -> None:
        """Test inferring default population from sample names."""
        vcf_samples = ["B73", "Mo17", "W22", "RIL_001"]
        populations = infer_populations_from_vcf(vcf_samples)

        assert len(populations) == 1
        pop = populations[0]
        assert pop.name == "default"
        assert pop.role == PopulationRole.DERIVED
        assert len(pop.samples) == 4

    def test_empty_sample_list(self) -> None:
        """Test with empty sample list."""
        populations = infer_populations_from_vcf([])
        assert len(populations) == 1
        assert len(populations[0].samples) == 0


class TestLoadPopulations:
    """Tests for auto-detecting population file format."""

    def test_load_tsv_by_extension(self, tmp_population_tsv: Path) -> None:
        """Test loading TSV by extension."""
        populations = load_populations(tmp_population_tsv)
        assert len(populations) == 2

    def test_load_yaml_by_extension(self, tmp_population_yaml: Path) -> None:
        """Test loading YAML by extension."""
        populations = load_populations(tmp_population_yaml)
        assert len(populations) == 2

    def test_auto_detect_tsv(self, tmp_path: Path) -> None:
        """Test auto-detecting TSV format."""
        content = """sample\tpopulation\trole
B73\tfounders\tfounder
"""
        path = tmp_path / "samples.txt"  # No .tsv extension
        path.write_text(content)

        populations = load_populations(path)
        assert len(populations) == 1


class TestValidatePopulationsAgainstVcf:
    """Tests for population validation against VCF samples."""

    def test_all_samples_found(self) -> None:
        """Test validation when all samples are found."""
        populations = [
            Population(
                name="founders",
                role=PopulationRole.FOUNDER,
                samples=[
                    Sample(name="B73", ploidy=2),
                    Sample(name="Mo17", ploidy=2),
                ],
            )
        ]
        vcf_samples = ["B73", "Mo17", "W22"]

        result = validate_populations_against_vcf(populations, vcf_samples)

        assert result.valid
        assert len(result.found_samples) == 2
        assert len(result.missing_samples) == 0
        assert len(result.extra_vcf_samples) == 1
        assert "W22" in result.extra_vcf_samples

    def test_missing_samples(self) -> None:
        """Test validation when samples are missing."""
        populations = [
            Population(
                name="founders",
                role=PopulationRole.FOUNDER,
                samples=[
                    Sample(name="B73", ploidy=2),
                    Sample(name="NonExistent", ploidy=2),
                ],
            )
        ]
        vcf_samples = ["B73", "Mo17"]

        result = validate_populations_against_vcf(populations, vcf_samples)

        assert result.valid  # Non-strict mode
        assert len(result.missing_samples) == 1
        assert "NonExistent" in result.missing_samples
        assert len(result.warnings) > 0

    def test_strict_mode(self) -> None:
        """Test validation in strict mode."""
        populations = [
            Population(
                name="founders",
                role=PopulationRole.FOUNDER,
                samples=[
                    Sample(name="B73", ploidy=2),
                    Sample(name="NonExistent", ploidy=2),
                ],
            )
        ]
        vcf_samples = ["B73", "Mo17"]

        result = validate_populations_against_vcf(populations, vcf_samples, strict=True)

        assert not result.valid
        assert len(result.errors) > 0

    def test_duplicate_samples(self) -> None:
        """Test detection of duplicate samples across populations."""
        populations = [
            Population(
                name="pop1",
                role=PopulationRole.FOUNDER,
                samples=[Sample(name="B73", ploidy=2)],
            ),
            Population(
                name="pop2",
                role=PopulationRole.DERIVED,
                samples=[Sample(name="B73", ploidy=2)],  # Duplicate
            ),
        ]
        vcf_samples = ["B73"]

        result = validate_populations_against_vcf(populations, vcf_samples)

        assert not result.valid
        assert any("multiple populations" in e for e in result.errors)

    def test_summary_output(self) -> None:
        """Test that summary is generated correctly."""
        populations = [
            Population(
                name="founders",
                role=PopulationRole.FOUNDER,
                samples=[Sample(name="B73", ploidy=2)],
            )
        ]
        vcf_samples = ["B73", "Mo17"]

        result = validate_populations_against_vcf(populations, vcf_samples)
        summary = result.summary()

        assert "PASSED" in summary
        assert "VCF samples: 2" in summary


class TestPopulationHelperFunctions:
    """Tests for population helper functions."""

    @pytest.fixture
    def test_populations(self) -> list[Population]:
        """Create test populations."""
        return [
            Population(
                name="founders",
                role=PopulationRole.FOUNDER,
                samples=[
                    Sample(name="B73", ploidy=2),
                    Sample(name="Mo17", ploidy=2),
                ],
            ),
            Population(
                name="derived",
                role=PopulationRole.DERIVED,
                samples=[
                    Sample(name="RIL_001", ploidy=2),
                    Sample(name="RIL_002", ploidy=2),
                    Sample(name="RIL_003", ploidy=2),
                ],
            ),
        ]

    def test_get_all_samples(self, test_populations: list[Population]) -> None:
        """Test getting all samples from populations."""
        samples = get_all_samples(test_populations)
        assert len(samples) == 5
        assert all(isinstance(s, Sample) for s in samples)

    def test_get_samples_by_role(self, test_populations: list[Population]) -> None:
        """Test getting samples by role."""
        founders = get_samples_by_role(test_populations, PopulationRole.FOUNDER)
        assert len(founders) == 2

        derived = get_samples_by_role(test_populations, PopulationRole.DERIVED)
        assert len(derived) == 3

    def test_get_founder_sample_names(self, test_populations: list[Population]) -> None:
        """Test getting founder sample names."""
        names = get_founder_sample_names(test_populations)
        assert len(names) == 2
        assert "B73" in names
        assert "Mo17" in names

    def test_get_derived_sample_names(self, test_populations: list[Population]) -> None:
        """Test getting derived sample names."""
        names = get_derived_sample_names(test_populations)
        assert len(names) == 3
        assert "RIL_001" in names
