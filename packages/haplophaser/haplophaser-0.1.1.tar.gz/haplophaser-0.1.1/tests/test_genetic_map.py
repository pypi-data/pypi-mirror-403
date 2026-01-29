"""Tests for genetic map functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from haplophaser.core.genetic_map import (
    ChromosomeMap,
    GeneticMap,
    MapPosition,
)

# ============================================================================
# Test MapPosition
# ============================================================================


class TestMapPosition:
    """Tests for MapPosition dataclass."""

    def test_creation(self) -> None:
        """Test basic creation."""
        pos = MapPosition(
            chrom="chr1",
            physical_pos=1000000,
            genetic_pos=1.5,
        )

        assert pos.chrom == "chr1"
        assert pos.physical_pos == 1000000
        assert pos.genetic_pos == 1.5

    def test_with_marker(self) -> None:
        """Test creation with marker ID."""
        pos = MapPosition(
            chrom="chr1",
            physical_pos=1000000,
            genetic_pos=1.5,
            marker_id="marker_001",
        )

        assert pos.marker_id == "marker_001"


# ============================================================================
# Test ChromosomeMap
# ============================================================================


class TestChromosomeMap:
    """Tests for ChromosomeMap class."""

    @pytest.fixture
    def simple_chrom_map(self) -> ChromosomeMap:
        """Create a simple chromosome map."""
        positions = [
            MapPosition("chr1", 0, 0.0),
            MapPosition("chr1", 1000000, 1.0),
            MapPosition("chr1", 2000000, 2.5),
            MapPosition("chr1", 3000000, 4.0),
        ]
        return ChromosomeMap(chrom="chr1", positions=positions)

    def test_basic_properties(self, simple_chrom_map: ChromosomeMap) -> None:
        """Test basic properties."""
        assert simple_chrom_map.chrom == "chr1"
        assert simple_chrom_map.n_positions == 4
        assert simple_chrom_map.physical_length == 3000000
        assert simple_chrom_map.genetic_length == 4.0

    def test_physical_to_genetic(self, simple_chrom_map: ChromosomeMap) -> None:
        """Test physical to genetic position conversion."""
        # Exact position
        genetic = simple_chrom_map.physical_to_genetic(1000000)
        assert genetic == pytest.approx(1.0)

        # Interpolated position (midpoint)
        genetic = simple_chrom_map.physical_to_genetic(1500000)
        assert genetic == pytest.approx(1.75)  # (1.0 + 2.5) / 2

        # Start
        genetic = simple_chrom_map.physical_to_genetic(0)
        assert genetic == pytest.approx(0.0)

    def test_genetic_to_physical(self, simple_chrom_map: ChromosomeMap) -> None:
        """Test genetic to physical position conversion."""
        # Exact position
        physical = simple_chrom_map.genetic_to_physical(1.0)
        assert physical == pytest.approx(1000000)

        # Interpolated
        physical = simple_chrom_map.genetic_to_physical(1.75)
        assert physical == pytest.approx(1500000)

    def test_recombination_rate(self, simple_chrom_map: ChromosomeMap) -> None:
        """Test recombination rate calculation."""
        # Rate in cM/Mb
        rate = simple_chrom_map.recombination_rate(500000, 1500000)
        # From 0.5 cM to 1.75 cM over 1 Mb = 1.25 cM/Mb
        assert rate > 0

    def test_out_of_bounds(self, simple_chrom_map: ChromosomeMap) -> None:
        """Test extrapolation for out-of-bounds positions."""
        # Before start - should extrapolate
        genetic = simple_chrom_map.physical_to_genetic(-100000)
        assert genetic <= 0

        # After end - should extrapolate
        genetic = simple_chrom_map.physical_to_genetic(4000000)
        assert genetic >= 4.0


# ============================================================================
# Test GeneticMap
# ============================================================================


class TestGeneticMap:
    """Tests for GeneticMap class."""

    @pytest.fixture
    def multi_chrom_map(self) -> GeneticMap:
        """Create a multi-chromosome map."""
        chrom1 = ChromosomeMap(
            chrom="chr1",
            positions=[
                MapPosition("chr1", 0, 0.0),
                MapPosition("chr1", 1000000, 1.0),
                MapPosition("chr1", 2000000, 2.0),
            ],
        )
        chrom2 = ChromosomeMap(
            chrom="chr2",
            positions=[
                MapPosition("chr2", 0, 0.0),
                MapPosition("chr2", 500000, 0.5),
                MapPosition("chr2", 1000000, 1.0),
            ],
        )
        return GeneticMap(chromosome_maps={"chr1": chrom1, "chr2": chrom2})

    def test_basic_properties(self, multi_chrom_map: GeneticMap) -> None:
        """Test basic properties."""
        assert multi_chrom_map.n_chromosomes == 2
        assert set(multi_chrom_map.chromosome_names) == {"chr1", "chr2"}
        assert multi_chrom_map.total_genetic_length == 3.0

    def test_physical_to_genetic(self, multi_chrom_map: GeneticMap) -> None:
        """Test conversion across chromosomes."""
        genetic = multi_chrom_map.physical_to_genetic("chr1", 1000000)
        assert genetic == pytest.approx(1.0)

        genetic = multi_chrom_map.physical_to_genetic("chr2", 500000)
        assert genetic == pytest.approx(0.5)

    def test_genetic_to_physical(self, multi_chrom_map: GeneticMap) -> None:
        """Test reverse conversion."""
        physical = multi_chrom_map.genetic_to_physical("chr1", 1.5)
        assert physical == pytest.approx(1500000)

    def test_recombination_probability(self, multi_chrom_map: GeneticMap) -> None:
        """Test recombination probability calculation."""
        # Same position
        prob = multi_chrom_map.recombination_probability("chr1", 1000000, 1000000)
        assert prob == pytest.approx(0.0)

        # Close positions
        prob = multi_chrom_map.recombination_probability("chr1", 1000000, 1100000)
        assert 0 < prob < 0.5

        # Far positions
        prob = multi_chrom_map.recombination_probability("chr1", 0, 2000000)
        assert prob > 0

    def test_missing_chromosome(self, multi_chrom_map: GeneticMap) -> None:
        """Test handling of missing chromosome."""
        # Should fall back to default rate for missing chromosomes
        genetic = multi_chrom_map.physical_to_genetic("chr3", 1000000)
        # With default rate of 1.0 cM/Mb, 1000000 bp = 1.0 cM
        assert genetic == pytest.approx(1.0)


# ============================================================================
# Test file loading
# ============================================================================


class TestGeneticMapLoading:
    """Tests for loading genetic maps from files."""

    def test_from_plink_format(self, tmp_path: Path) -> None:
        """Test loading PLINK format map."""
        content = """chr1\tmarker1\t0.0\t1000
chr1\tmarker2\t1.0\t1000000
chr1\tmarker3\t2.0\t2000000
chr2\tmarker4\t0.0\t500
chr2\tmarker5\t0.5\t500000
"""
        path = tmp_path / "test.map"
        path.write_text(content)

        gmap = GeneticMap.from_plink(path)

        assert gmap.n_chromosomes == 2
        assert "chr1" in gmap.chromosome_names

    def test_from_mstmap_format(self, tmp_path: Path) -> None:
        """Test loading MSTmap format."""
        content = """group chr1
marker1\t0.0
marker2\t1.0
marker3\t2.5

group chr2
marker4\t0.0
marker5\t0.8
"""
        path = tmp_path / "test.mstmap"
        path.write_text(content)

        gmap = GeneticMap.from_mstmap(path)

        assert gmap.n_chromosomes == 2

    def test_from_custom_format(self, tmp_path: Path) -> None:
        """Test loading custom TSV format."""
        content = """chrom\tphysical_pos\tgenetic_pos\tmarker_id
chr1\t0\t0.0\tmarker1
chr1\t1000000\t1.0\tmarker2
chr2\t0\t0.0\tmarker3
chr2\t500000\t0.5\tmarker4
"""
        path = tmp_path / "test.tsv"
        path.write_text(content)

        gmap = GeneticMap.from_tsv(path)

        assert gmap.n_chromosomes == 2

    def test_empty_file(self, tmp_path: Path) -> None:
        """Test handling of empty file."""
        path = tmp_path / "empty.map"
        path.write_text("")

        with pytest.raises(ValueError):
            GeneticMap.from_plink(path)


# ============================================================================
# Test mapping functions
# ============================================================================


class TestMappingFunctions:
    """Tests for genetic mapping functions."""

    def test_haldane_to_probability(self) -> None:
        """Test Haldane function."""
        from haplophaser.core.genetic_map import haldane_to_probability

        # 0 cM -> 0 probability
        assert haldane_to_probability(0) == pytest.approx(0.0)

        # 50 cM -> 0.316 (approx)
        assert haldane_to_probability(50) == pytest.approx(0.316, abs=0.01)

        # Very large -> 0.5
        assert haldane_to_probability(1000) == pytest.approx(0.5, abs=0.001)

    def test_kosambi_to_probability(self) -> None:
        """Test Kosambi function."""
        from haplophaser.core.genetic_map import kosambi_to_probability

        # 0 cM -> 0 probability
        assert kosambi_to_probability(0) == pytest.approx(0.0)

        # Large distance -> approaches 0.5
        assert kosambi_to_probability(100) < 0.5
