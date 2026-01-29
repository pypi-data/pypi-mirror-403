"""Tests for core data models."""

from __future__ import annotations

import pytest

from haplophaser.core.models import (
    HaplotypeBlock,
    Population,
    PopulationRole,
    Sample,
    Subgenome,
    Variant,
    Window,
    make_diploid_sample,
    make_hexaploid_sample,
    make_tetraploid_sample,
)


class TestSubgenome:
    """Tests for Subgenome model."""

    def test_create_subgenome(self) -> None:
        """Test basic subgenome creation."""
        sg = Subgenome(name="A", ploidy=2, description="From T. urartu")
        assert sg.name == "A"
        assert sg.ploidy == 2
        assert sg.description == "From T. urartu"

    def test_subgenome_defaults(self) -> None:
        """Test default values."""
        sg = Subgenome(name="B")
        assert sg.ploidy == 2
        assert sg.description is None

    def test_subgenome_immutable(self) -> None:
        """Test that subgenomes are frozen."""
        sg = Subgenome(name="A", ploidy=2)
        with pytest.raises(Exception):  # ValidationError for frozen model
            sg.name = "B"


class TestSample:
    """Tests for Sample model."""

    def test_create_diploid(self, diploid_sample: Sample) -> None:
        """Test diploid sample creation."""
        assert diploid_sample.name == "B73"
        assert diploid_sample.ploidy == 2
        assert diploid_sample.population == "NAM_founders"
        assert not diploid_sample.is_polyploid
        assert not diploid_sample.is_allopolyploid
        assert diploid_sample.n_haplotypes == 2

    def test_create_tetraploid(self, tetraploid_sample: Sample) -> None:
        """Test tetraploid sample creation."""
        assert tetraploid_sample.ploidy == 4
        assert len(tetraploid_sample.subgenomes) == 2
        assert tetraploid_sample.is_polyploid
        assert tetraploid_sample.is_allopolyploid
        assert tetraploid_sample.n_haplotypes == 4

    def test_create_hexaploid(self, hexaploid_sample: Sample) -> None:
        """Test hexaploid sample creation."""
        assert hexaploid_sample.ploidy == 6
        assert len(hexaploid_sample.subgenomes) == 3
        assert hexaploid_sample.is_polyploid
        assert hexaploid_sample.is_allopolyploid
        assert hexaploid_sample.n_haplotypes == 6

    def test_subgenome_ploidy_validation(self) -> None:
        """Test that subgenome ploidies must sum to total ploidy."""
        with pytest.raises(ValueError, match="must sum to total ploidy"):
            Sample(
                name="bad_sample",
                ploidy=4,
                subgenomes=[
                    Subgenome(name="A", ploidy=2),
                    Subgenome(name="B", ploidy=3),  # Sum = 5, not 4
                ],
            )

    def test_convenience_functions(self) -> None:
        """Test sample creation convenience functions."""
        diploid = make_diploid_sample("B73", "founders")
        assert diploid.ploidy == 2
        assert diploid.population == "founders"

        tetraploid = make_tetraploid_sample("Durum", ("A", "B"))
        assert tetraploid.ploidy == 4
        assert len(tetraploid.subgenomes) == 2
        assert tetraploid.subgenomes[0].name == "A"

        hexaploid = make_hexaploid_sample("Chinese_Spring", ("A", "B", "D"))
        assert hexaploid.ploidy == 6
        assert len(hexaploid.subgenomes) == 3


class TestPopulation:
    """Tests for Population model."""

    def test_create_founder_population(self, founder_population: Population) -> None:
        """Test founder population creation."""
        assert founder_population.name == "NAM_founders"
        assert founder_population.role == PopulationRole.FOUNDER
        assert len(founder_population.samples) == 3
        assert "B73" in founder_population.sample_names

    def test_create_derived_population(self, derived_population: Population) -> None:
        """Test derived population creation."""
        assert derived_population.role == PopulationRole.DERIVED
        assert len(derived_population.samples) == 2

    def test_get_sample(self, founder_population: Population) -> None:
        """Test sample lookup by name."""
        sample = founder_population.get_sample("B73")
        assert sample is not None
        assert sample.name == "B73"

        missing = founder_population.get_sample("NonExistent")
        assert missing is None

    def test_population_roles(self) -> None:
        """Test all population role values."""
        assert PopulationRole.FOUNDER.value == "founder"
        assert PopulationRole.DERIVED.value == "derived"
        assert PopulationRole.OUTGROUP.value == "outgroup"


class TestVariant:
    """Tests for Variant model."""

    def test_create_snp(self, snp_variant: Variant) -> None:
        """Test SNP variant creation."""
        assert snp_variant.chrom == "chr1"
        assert snp_variant.pos == 1000
        assert snp_variant.ref == "A"
        assert snp_variant.alt == ["T"]
        assert snp_variant.is_snp
        assert snp_variant.n_alleles == 2

    def test_coordinate_conversion(self, snp_variant: Variant) -> None:
        """Test 0-based to 1-based coordinate conversion."""
        assert snp_variant.pos == 1000  # 0-based
        assert snp_variant.pos_1based == 1001  # 1-based (VCF-style)

    def test_end_position(self) -> None:
        """Test end position calculation."""
        snp = Variant(chrom="chr1", pos=100, ref="A", alt=["T"])
        assert snp.end == 101

        indel = Variant(chrom="chr1", pos=100, ref="ACGT", alt=["A"])
        assert indel.end == 104

    def test_tetraploid_genotypes(self, tetraploid_variant: Variant) -> None:
        """Test tetraploid genotype handling."""
        gt = tetraploid_variant.get_genotype("Durum_A")
        assert gt is not None
        assert len(gt) == 4
        assert gt == [0, 0, 1, 1]

    def test_allele_counts(self, tetraploid_variant: Variant) -> None:
        """Test allele counting in polyploids."""
        counts = tetraploid_variant.allele_counts("Durum_A")
        assert counts == {0: 2, 1: 2}

        counts_b = tetraploid_variant.allele_counts("Durum_B")
        assert counts_b == {0: 3, 1: 1}

    def test_multiallelic_variant(self, multiallelic_variant: Variant) -> None:
        """Test multiallelic variant."""
        assert multiallelic_variant.n_alleles == 3
        assert multiallelic_variant.is_snp  # Still a SNP (multiallelic SNP: C->T,G)

    def test_missing_genotypes(self) -> None:
        """Test handling of missing genotype values."""
        var = Variant(
            chrom="chr1",
            pos=100,
            ref="A",
            alt=["T"],
            genotypes={
                "B73": [0, 0],
                "Mo17": [-1, -1],  # Missing
                "W22": [0, -1],  # Partially missing
            },
        )
        assert var.get_genotype("Mo17") == [-1, -1]
        counts = var.allele_counts("Mo17")
        assert counts == {}  # Missing calls excluded


class TestWindow:
    """Tests for Window model."""

    def test_create_window(self, genomic_window: Window) -> None:
        """Test window creation."""
        assert genomic_window.chrom == "chr1"
        assert genomic_window.start == 0
        assert genomic_window.end == 100_000
        assert len(genomic_window) == 100_000
        assert genomic_window.n_variants == 11
        assert genomic_window.index == 0

    def test_window_midpoint(self) -> None:
        """Test midpoint calculation."""
        window = Window(chrom="chr1", start=0, end=100_000)
        assert window.midpoint == 50_000

        window2 = Window(chrom="chr1", start=100_000, end=200_000)
        assert window2.midpoint == 150_000

    def test_window_overlap(self) -> None:
        """Test window overlap detection."""
        w1 = Window(chrom="chr1", start=0, end=100_000)
        w2 = Window(chrom="chr1", start=50_000, end=150_000)
        w3 = Window(chrom="chr1", start=100_000, end=200_000)
        w4 = Window(chrom="chr2", start=0, end=100_000)

        assert w1.overlaps(w2)  # Partial overlap
        assert w2.overlaps(w1)  # Symmetric
        assert not w1.overlaps(w3)  # Adjacent, no overlap
        assert not w1.overlaps(w4)  # Different chromosome

    def test_window_coordinate_validation(self) -> None:
        """Test that end must be greater than start."""
        with pytest.raises(ValueError, match="must be > start"):
            Window(chrom="chr1", start=100, end=100)

        with pytest.raises(ValueError, match="must be > start"):
            Window(chrom="chr1", start=100, end=50)


class TestHaplotypeBlock:
    """Tests for HaplotypeBlock model."""

    def test_create_block(self, haplotype_block: HaplotypeBlock) -> None:
        """Test haplotype block creation."""
        assert haplotype_block.chrom == "chr1"
        assert haplotype_block.start == 0
        assert haplotype_block.end == 500_000
        assert haplotype_block.sample == "RIL_001"
        assert haplotype_block.founder == "B73"
        assert haplotype_block.proportion == 0.95
        assert len(haplotype_block) == 500_000

    def test_block_bed_conversion(self, haplotype_block: HaplotypeBlock) -> None:
        """Test BED format conversion."""
        bed_fields = haplotype_block.to_bed_fields()
        assert bed_fields[0] == "chr1"  # chrom
        assert bed_fields[1] == 0  # start
        assert bed_fields[2] == 500_000  # end
        assert "RIL_001" in bed_fields[3]  # name
        assert "B73" in bed_fields[3]  # name includes founder
        assert bed_fields[4] == 950  # score (proportion * 1000)
        assert bed_fields[5] == "."  # strand

    def test_block_overlap(self, haplotype_blocks: list[HaplotypeBlock]) -> None:
        """Test block overlap detection."""
        b1, b2, b3, b4 = haplotype_blocks

        # Blocks on same homolog
        assert not b1.overlaps(b2)  # Adjacent, no overlap

        # Blocks on different homologs can overlap positionally
        assert b1.overlaps(b3)  # 0-500k overlaps 0-750k

    def test_block_coordinate_validation(self) -> None:
        """Test that end must be greater than start."""
        with pytest.raises(ValueError, match="must be > start"):
            HaplotypeBlock(
                chrom="chr1",
                start=100,
                end=100,
                sample="test",
                founder="B73",
                proportion=0.9,
            )

    def test_block_proportion_validation(self) -> None:
        """Test proportion must be 0-1."""
        with pytest.raises(ValueError):
            HaplotypeBlock(
                chrom="chr1",
                start=0,
                end=1000,
                sample="test",
                founder="B73",
                proportion=1.5,  # Invalid
            )


class TestModelIntegration:
    """Integration tests for model interactions."""

    def test_polyploid_workflow(self) -> None:
        """Test typical polyploid analysis workflow."""
        # Create hexaploid wheat sample
        sample = make_hexaploid_sample("CS", ("A", "B", "D"), "founders")

        # Verify structure
        assert sample.n_haplotypes == 6
        assert len(sample.subgenomes) == 3

        # Create variant with proper ploidy
        var = Variant(
            chrom="1A",
            pos=1000,
            ref="G",
            alt=["A"],
            genotypes={"CS": [0, 0, 0, 0, 1, 1]},  # 6 allele calls
        )

        counts = var.allele_counts("CS")
        assert counts[0] == 4
        assert counts[1] == 2

    def test_population_analysis_workflow(
        self,
        founder_population: Population,
        derived_population: Population,
    ) -> None:
        """Test typical population-based analysis setup."""
        # Check roles
        assert founder_population.role == PopulationRole.FOUNDER
        assert derived_population.role == PopulationRole.DERIVED

        # Get all sample names
        all_samples = founder_population.sample_names + derived_population.sample_names
        assert len(all_samples) == 5

        # Create windows for analysis
        windows = [
            Window(chrom="chr1", start=i * 100_000, end=(i + 1) * 100_000, index=i)
            for i in range(10)
        ]
        assert len(windows) == 10
        assert not any(windows[i].overlaps(windows[i + 1]) for i in range(9))
