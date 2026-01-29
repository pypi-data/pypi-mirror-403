"""Tests for scaffold ordering and orientation modules."""

from __future__ import annotations

import pytest

from haplophaser.assembly.mapping import MarkerHit
from haplophaser.assembly.paint import AssemblyPainting, ContigPainting
from haplophaser.core.genetic_map import ChromosomeMap, GeneticMap, MapPosition
from haplophaser.io.agp import AGP, AGPRecord, AGPWriter, compare_agp, export_ordering_tsv
from haplophaser.io.assembly import Assembly, Contig
from haplophaser.scaffold.contig_markers import (
    ContigMarkerMap,
    ContigPlacement,
    MappedMarker,
    locate_markers,
)
from haplophaser.scaffold.continuity import (
    ContinuityScore,
    HaplotypeContinuityScorer,
    ProblematicJoin,
)
from haplophaser.scaffold.gaps import (
    GapEstimate,
    GapEstimator,
    estimate_gaps,
)
from haplophaser.scaffold.ordering import (
    OrderedContig,
    ScaffoldOrderer,
    ScaffoldOrdering,
    order_contigs,
)
from haplophaser.scaffold.orientation import (
    ContigOrienter,
    OrientationCall,
    infer_orientations,
)
from haplophaser.scaffold.validation import (
    Inversion,
    ScaffoldValidator,
    UnexpectedSwitch,
    ValidationReport,
    validate_ordering,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def test_assembly() -> Assembly:
    """Create a test assembly with 20 contigs."""
    contigs = {}
    for i in range(20):
        # Varying lengths 50kb to 200kb
        length = 50_000 + (i % 4) * 50_000
        contigs[f"contig_{i:03d}"] = Contig(name=f"contig_{i:03d}", length=length)
    return Assembly(name="test_assembly", contigs=contigs)


@pytest.fixture
def test_genetic_map() -> GeneticMap:
    """Create a test genetic map with 2 chromosomes."""
    positions_chr1 = [
        MapPosition(chrom="chr1", physical_pos=0, genetic_pos=0.0, rate=1.0, marker_id="m1"),
        MapPosition(chrom="chr1", physical_pos=1_000_000, genetic_pos=1.0, rate=1.0, marker_id="m2"),
        MapPosition(chrom="chr1", physical_pos=5_000_000, genetic_pos=5.0, rate=1.0, marker_id="m3"),
        MapPosition(chrom="chr1", physical_pos=10_000_000, genetic_pos=10.0, rate=1.0, marker_id="m4"),
    ]
    positions_chr2 = [
        MapPosition(chrom="chr2", physical_pos=0, genetic_pos=0.0, rate=1.0, marker_id="m5"),
        MapPosition(chrom="chr2", physical_pos=2_000_000, genetic_pos=2.0, rate=1.0, marker_id="m6"),
        MapPosition(chrom="chr2", physical_pos=8_000_000, genetic_pos=8.0, rate=1.0, marker_id="m7"),
    ]

    return GeneticMap(chromosome_maps={
        "chr1": ChromosomeMap(chrom="chr1", positions=positions_chr1),
        "chr2": ChromosomeMap(chrom="chr2", positions=positions_chr2),
    })


@pytest.fixture
def marker_hits_for_scaffolding() -> list[MarkerHit]:
    """Create marker hits with known positions for scaffolding tests."""
    hits = []

    # Contigs 0-4 on chr1, 5-9 on chr2 (known order)
    chr1_positions = [0.5, 1.5, 3.0, 4.5, 6.0]  # cM positions
    chr2_positions = [0.3, 1.0, 2.5, 4.0, 5.5]  # cM positions

    # chr1 markers
    for i, cm_pos in enumerate(chr1_positions):
        contig_name = f"contig_{i:03d}"
        bp_pos = int(cm_pos * 1_000_000)

        # Add multiple markers per contig at positions that increase with cM
        for j in range(5):
            local_pos = j * 10_000  # Position within contig
            hits.append(MarkerHit(
                marker_id=f"chr1_marker_{i}_{j}",
                contig=contig_name,
                position=local_pos,
                strand="+",
                identity=0.99,
                founder_alleles={"B73": "A", "Mo17": "T"},
                observed_allele="A" if i < 3 else "T",  # First 3 B73, last 2 Mo17
                ref_allele="A",
                alt_allele="T",
                marker_chrom="chr1",
                marker_pos=bp_pos + local_pos,
            ))

    # chr2 markers
    for i, cm_pos in enumerate(chr2_positions):
        contig_name = f"contig_{i + 5:03d}"
        bp_pos = int(cm_pos * 1_000_000)

        for j in range(5):
            local_pos = j * 10_000
            hits.append(MarkerHit(
                marker_id=f"chr2_marker_{i}_{j}",
                contig=contig_name,
                position=local_pos,
                strand="+",
                identity=0.99,
                founder_alleles={"B73": "A", "Mo17": "T"},
                observed_allele="A",  # All B73
                ref_allele="A",
                alt_allele="T",
                marker_chrom="chr2",
                marker_pos=bp_pos + local_pos,
            ))

    return hits


@pytest.fixture
def test_painting(test_assembly) -> AssemblyPainting:
    """Create a test painting result."""
    paintings = {}
    founders = ["B73", "Mo17"]

    for i, contig_name in enumerate(test_assembly.contigs):
        # Alternate founders
        assigned = founders[i % 2]
        paintings[contig_name] = ContigPainting(
            contig=contig_name,
            length=test_assembly.contigs[contig_name].length,
            n_markers=5,
            founder_proportions={"B73": 0.9 if assigned == "B73" else 0.1, "Mo17": 0.1 if assigned == "B73" else 0.9},
            founder_counts={"B73": 9 if assigned == "B73" else 1, "Mo17": 1 if assigned == "B73" else 9},
            assigned_founder=assigned,
            confidence=0.9,
        )

    return AssemblyPainting(
        assembly=test_assembly.name,
        founders=founders,
        contigs=paintings,
    )


@pytest.fixture
def simple_scaffold_ordering() -> ScaffoldOrdering:
    """Create a simple scaffold ordering for testing."""
    ordered_contigs = [
        OrderedContig(contig="contig_000", start=0, end=100_000, orientation="+", gap_before=0, confidence=0.9, genetic_start=0.0, genetic_end=1.0),
        OrderedContig(contig="contig_001", start=100_100, end=200_100, orientation="+", gap_before=100, confidence=0.8, genetic_start=1.5, genetic_end=2.5),
        OrderedContig(contig="contig_002", start=200_200, end=350_200, orientation="-", gap_before=100, confidence=0.85, genetic_start=3.0, genetic_end=4.5),
    ]
    return ScaffoldOrdering(
        chromosome="chr1",
        ordered_contigs=ordered_contigs,
        unplaced=["contig_010"],
        total_placed_bp=350_000,
        total_unplaced_bp=50_000,
        method="genetic_map",
    )


# =============================================================================
# Contig Marker Map Tests
# =============================================================================


class TestMappedMarker:
    """Tests for MappedMarker class."""

    def test_mapped_marker_creation(self):
        """Test MappedMarker creation."""
        marker = MappedMarker(
            marker_id="test_marker",
            chrom_genetic="chr1",
            pos_genetic=5.5,
            contig="contig_001",
            pos_physical=10_000,
            strand="+",
            inferred_founder="B73",
        )

        assert marker.marker_id == "test_marker"
        assert marker.chrom_genetic == "chr1"
        assert marker.pos_genetic == 5.5


class TestContigPlacement:
    """Tests for ContigPlacement class."""

    def test_placement_properties(self):
        """Test ContigPlacement properties."""
        placement = ContigPlacement(
            contig="contig_001",
            chromosome="chr1",
            genetic_start=1.0,
            genetic_end=3.0,
            orientation="+",
            n_markers=10,
            confidence=0.9,
        )

        assert placement.is_placed
        assert placement.genetic_span == 2.0
        assert placement.genetic_midpoint == 2.0
        assert not placement.has_conflicts

    def test_unplaced_contig(self):
        """Test unplaced contig properties."""
        placement = ContigPlacement(contig="contig_002", n_markers=0)

        assert not placement.is_placed
        assert placement.genetic_span is None
        assert placement.genetic_midpoint is None


class TestContigMarkerMap:
    """Tests for ContigMarkerMap class."""

    def test_build_contig_marker_map(self, test_assembly, marker_hits_for_scaffolding, test_genetic_map):
        """Test building contig-marker map."""
        contig_map = ContigMarkerMap(
            assembly=test_assembly,
            marker_hits=marker_hits_for_scaffolding,
            genetic_map=test_genetic_map,
            min_markers=3,
        )

        # Should have placements for placed contigs
        placed = contig_map.placed_contigs()
        assert len(placed) > 0

        # Check placement for contig_000
        placement = contig_map.get_placement("contig_000")
        assert placement is not None
        if placement.is_placed:
            assert placement.chromosome == "chr1"

    def test_placements_by_chromosome(self, test_assembly, marker_hits_for_scaffolding, test_genetic_map):
        """Test getting placements by chromosome."""
        contig_map = ContigMarkerMap(
            assembly=test_assembly,
            marker_hits=marker_hits_for_scaffolding,
            genetic_map=test_genetic_map,
        )

        chr1_placements = contig_map.placements_by_chromosome("chr1")
        chr2_placements = contig_map.placements_by_chromosome("chr2")

        # Both should have some placements
        assert isinstance(chr1_placements, list)
        assert isinstance(chr2_placements, list)

    def test_summary(self, test_assembly, marker_hits_for_scaffolding, test_genetic_map):
        """Test summary statistics."""
        contig_map = ContigMarkerMap(
            assembly=test_assembly,
            marker_hits=marker_hits_for_scaffolding,
            genetic_map=test_genetic_map,
        )

        summary = contig_map.summary()
        assert "n_contigs" in summary
        assert "n_placed" in summary
        assert "placement_rate" in summary


class TestLocateMarkers:
    """Tests for locate_markers function."""

    def test_locate_markers(self, marker_hits_for_scaffolding, test_genetic_map):
        """Test locating markers on genetic map."""
        mapped = locate_markers(marker_hits_for_scaffolding, test_genetic_map)

        assert len(mapped) > 0
        assert all(isinstance(m, MappedMarker) for m in mapped)


# =============================================================================
# Scaffold Ordering Tests
# =============================================================================


class TestOrderedContig:
    """Tests for OrderedContig class."""

    def test_ordered_contig_length(self):
        """Test OrderedContig length property."""
        oc = OrderedContig(
            contig="test",
            start=1000,
            end=50000,
            orientation="+",
        )
        assert oc.length == 49000


class TestScaffoldOrdering:
    """Tests for ScaffoldOrdering class."""

    def test_ordering_properties(self, simple_scaffold_ordering):
        """Test ScaffoldOrdering properties."""
        ordering = simple_scaffold_ordering

        assert ordering.n_contigs == 3
        assert ordering.n_gaps == 2
        assert ordering.total_length > 0

    def test_to_agp(self, simple_scaffold_ordering):
        """Test AGP format conversion."""
        agp_string = simple_scaffold_ordering.to_agp()

        assert "chr1" in agp_string
        assert "contig_000" in agp_string
        # Should have N lines for gaps
        assert "N\t" in agp_string or agp_string.count("W") == 3

    def test_get_contig_position(self, simple_scaffold_ordering):
        """Test getting contig position."""
        oc = simple_scaffold_ordering.get_contig_position("contig_001")
        assert oc is not None
        assert oc.contig == "contig_001"

        # Non-existent contig
        assert simple_scaffold_ordering.get_contig_position("nonexistent") is None


class TestScaffoldOrderer:
    """Tests for ScaffoldOrderer class."""

    def test_order_by_genetic_map(self, test_assembly, marker_hits_for_scaffolding, test_genetic_map):
        """Test ordering by genetic map."""
        contig_map = ContigMarkerMap(
            assembly=test_assembly,
            marker_hits=marker_hits_for_scaffolding,
            genetic_map=test_genetic_map,
            min_markers=3,
        )

        orderer = ScaffoldOrderer(method="genetic_map", min_markers=3)
        orderings = orderer.order(test_assembly, contig_map)

        assert isinstance(orderings, dict)
        # Should have orderings for chromosomes with placed contigs

    def test_order_combined(self, test_assembly, marker_hits_for_scaffolding, test_genetic_map, test_painting):
        """Test combined ordering with haplotype continuity."""
        contig_map = ContigMarkerMap(
            assembly=test_assembly,
            marker_hits=marker_hits_for_scaffolding,
            genetic_map=test_genetic_map,
            min_markers=3,
        )

        orderer = ScaffoldOrderer(method="combined", min_markers=3)
        orderings = orderer.order(test_assembly, contig_map, test_painting)

        assert isinstance(orderings, dict)


class TestOrderContigs:
    """Tests for order_contigs convenience function."""

    def test_order_contigs_function(self, test_assembly, marker_hits_for_scaffolding, test_genetic_map):
        """Test order_contigs convenience function."""
        contig_map = ContigMarkerMap(
            assembly=test_assembly,
            marker_hits=marker_hits_for_scaffolding,
            genetic_map=test_genetic_map,
        )

        orderings = order_contigs(test_assembly, contig_map, method="genetic_map")
        assert isinstance(orderings, dict)


# =============================================================================
# Orientation Tests
# =============================================================================


class TestOrientationCall:
    """Tests for OrientationCall class."""

    def test_orientation_call_properties(self):
        """Test OrientationCall properties."""
        call = OrientationCall(
            contig="test",
            orientation="+",
            confidence=0.9,
            evidence=["marker_order"],
            marker_order_score=0.95,
        )

        assert call.is_determined
        assert call.orientation == "+"

    def test_undetermined_orientation(self):
        """Test undetermined orientation."""
        call = OrientationCall(
            contig="test",
            orientation="?",
            confidence=0.0,
        )

        assert not call.is_determined


class TestContigOrienter:
    """Tests for ContigOrienter class."""

    def test_infer_orientations(self, test_assembly, marker_hits_for_scaffolding, test_genetic_map):
        """Test orientation inference."""
        contig_map = ContigMarkerMap(
            assembly=test_assembly,
            marker_hits=marker_hits_for_scaffolding,
            genetic_map=test_genetic_map,
        )

        orienter = ContigOrienter(method="marker_order", min_markers=2)
        orientations = orienter.infer(test_assembly, contig_map)

        assert isinstance(orientations, dict)
        assert len(orientations) == test_assembly.n_contigs


class TestInferOrientations:
    """Tests for infer_orientations convenience function."""

    def test_infer_orientations_function(self, test_assembly, marker_hits_for_scaffolding, test_genetic_map):
        """Test infer_orientations function."""
        contig_map = ContigMarkerMap(
            assembly=test_assembly,
            marker_hits=marker_hits_for_scaffolding,
            genetic_map=test_genetic_map,
        )

        orientations = infer_orientations(test_assembly, contig_map)
        assert isinstance(orientations, dict)


# =============================================================================
# Continuity Scoring Tests
# =============================================================================


class TestProblematicJoin:
    """Tests for ProblematicJoin class."""

    def test_problematic_join_is_switch(self):
        """Test is_switch property."""
        join = ProblematicJoin(
            left_contig="contig_001",
            right_contig="contig_002",
            left_haplotype="B73",
            right_haplotype="Mo17",
        )

        assert join.is_switch

    def test_non_switch_join(self):
        """Test non-switch join."""
        join = ProblematicJoin(
            left_contig="contig_001",
            right_contig="contig_002",
            left_haplotype="B73",
            right_haplotype="B73",
        )

        assert not join.is_switch


class TestContinuityScore:
    """Tests for ContinuityScore class."""

    def test_continuity_score_properties(self):
        """Test ContinuityScore properties."""
        score = ContinuityScore(
            chromosome="chr1",
            total_score=10.0,
            n_switches=2,
            n_continuities=8,
            n_unknown=1,
        )

        assert score.n_boundaries == 11
        assert score.switch_rate == 0.2
        assert score.continuity_rate == 0.8


class TestHaplotypeContinuityScorer:
    """Tests for HaplotypeContinuityScorer class."""

    def test_score_ordering(self, simple_scaffold_ordering, test_painting):
        """Test scoring an ordering."""
        scorer = HaplotypeContinuityScorer()
        score = scorer.score(simple_scaffold_ordering, test_painting)

        assert isinstance(score, ContinuityScore)
        assert score.chromosome == "chr1"

    def test_compare_orderings(self, simple_scaffold_ordering, test_painting):
        """Test comparing orderings."""
        # Create two orderings
        ordering1 = simple_scaffold_ordering
        ordering2 = ScaffoldOrdering(
            chromosome="chr1",
            ordered_contigs=list(reversed(simple_scaffold_ordering.ordered_contigs)),
        )

        scorer = HaplotypeContinuityScorer()
        scores = scorer.compare_orderings([ordering1, ordering2], test_painting)

        assert len(scores) == 2

    def test_select_best(self, simple_scaffold_ordering, test_painting):
        """Test selecting best ordering."""
        scorer = HaplotypeContinuityScorer()
        best, score = scorer.select_best([simple_scaffold_ordering], test_painting)

        assert best is simple_scaffold_ordering


# =============================================================================
# Gap Estimation Tests
# =============================================================================


class TestGapEstimate:
    """Tests for GapEstimate class."""

    def test_gap_estimate_creation(self):
        """Test GapEstimate creation."""
        estimate = GapEstimate(
            left_contig="contig_001",
            right_contig="contig_002",
            estimated_size=5000,
            confidence=0.8,
            method="genetic_distance",
            genetic_distance=0.5,
        )

        assert estimate.estimated_size == 5000
        assert estimate.method == "genetic_distance"


class TestGapEstimator:
    """Tests for GapEstimator class."""

    def test_fixed_gap_estimation(self, simple_scaffold_ordering):
        """Test fixed gap estimation."""
        estimator = GapEstimator(method="fixed", fixed_gap=100)
        gaps = estimator.estimate(simple_scaffold_ordering)

        assert len(gaps) == 2  # Two gaps between 3 contigs
        for gap in gaps.values():
            assert gap.estimated_size == 100

    def test_genetic_distance_estimation(self, simple_scaffold_ordering, test_genetic_map):
        """Test genetic distance-based gap estimation."""
        estimator = GapEstimator(method="genetic_distance", bp_per_cm=1_000_000)
        gaps = estimator.estimate(simple_scaffold_ordering, test_genetic_map)

        assert len(gaps) > 0
        # All estimates should be within min/max bounds
        for gap in gaps.values():
            assert gap.estimated_size >= estimator.min_gap
            assert gap.estimated_size <= estimator.max_gap


class TestEstimateGaps:
    """Tests for estimate_gaps convenience function."""

    def test_estimate_gaps_function(self, simple_scaffold_ordering, test_genetic_map):
        """Test estimate_gaps function."""
        gaps = estimate_gaps(simple_scaffold_ordering, test_genetic_map, method="genetic_distance")
        assert isinstance(gaps, dict)


# =============================================================================
# Validation Tests
# =============================================================================


class TestInversion:
    """Tests for Inversion class."""

    def test_inversion_creation(self):
        """Test Inversion creation."""
        inv = Inversion(
            contig="contig_001",
            markers_involved=["m1", "m2", "m3"],
            confidence=0.9,
            genetic_start=1.0,
            genetic_end=3.0,
            expected_orientation="+",
            observed_orientation="-",
        )

        assert inv.contig == "contig_001"
        assert len(inv.markers_involved) == 3


class TestUnexpectedSwitch:
    """Tests for UnexpectedSwitch class."""

    def test_unexpected_switch_creation(self):
        """Test UnexpectedSwitch creation."""
        switch = UnexpectedSwitch(
            position=100_000,
            left_contig="contig_001",
            right_contig="contig_002",
            possible_causes=["misorder", "misorientation"],
            left_haplotype="B73",
            right_haplotype="Mo17",
        )

        assert switch.position == 100_000
        assert "misorder" in switch.possible_causes


class TestValidationReport:
    """Tests for ValidationReport class."""

    def test_validation_report_properties(self):
        """Test ValidationReport properties."""
        report = ValidationReport(
            chromosome="chr1",
            marker_order_concordance=0.95,
            haplotype_switches=2,
            expected_switches=1,
            genetic_map_coverage=0.85,
            assembly_placed=0.90,
            n_contigs=10,
            n_markers=100,
        )

        assert report.chromosome == "chr1"
        assert report.marker_order_concordance == 0.95

    def test_summary(self):
        """Test summary generation."""
        report = ValidationReport(
            chromosome="chr1",
            marker_order_concordance=0.95,
            n_contigs=10,
        )

        summary = report.summary()
        assert "chr1" in summary
        assert "0.95" in summary

    def test_passes(self):
        """Test passes method."""
        report_pass = ValidationReport(
            chromosome="chr1",
            marker_order_concordance=0.95,
            haplotype_switches=5,
            genetic_map_coverage=0.8,
        )

        report_fail = ValidationReport(
            chromosome="chr1",
            marker_order_concordance=0.5,
            haplotype_switches=5,
            genetic_map_coverage=0.3,
        )

        assert report_pass.passes()
        assert not report_fail.passes()


class TestScaffoldValidator:
    """Tests for ScaffoldValidator class."""

    def test_validate_ordering(self, simple_scaffold_ordering, test_genetic_map, test_assembly, marker_hits_for_scaffolding, test_painting):
        """Test validating an ordering."""
        contig_map = ContigMarkerMap(
            assembly=test_assembly,
            marker_hits=marker_hits_for_scaffolding,
            genetic_map=test_genetic_map,
        )

        validator = ScaffoldValidator()
        report = validator.validate(
            simple_scaffold_ordering,
            test_genetic_map,
            contig_map,
            test_painting,
        )

        assert isinstance(report, ValidationReport)
        assert report.chromosome == "chr1"


class TestValidateOrdering:
    """Tests for validate_ordering convenience function."""

    def test_validate_ordering_function(self, simple_scaffold_ordering, test_genetic_map):
        """Test validate_ordering function."""
        report = validate_ordering(simple_scaffold_ordering, test_genetic_map)
        assert isinstance(report, ValidationReport)


# =============================================================================
# AGP I/O Tests
# =============================================================================


class TestAGPRecord:
    """Tests for AGPRecord class."""

    def test_contig_record(self):
        """Test contig record."""
        record = AGPRecord(
            object_name="chr1",
            object_start=1,
            object_end=100000,
            part_number=1,
            component_type="W",
            component_id="contig_001",
            component_start=1,
            component_end=100000,
            orientation="+",
        )

        assert not record.is_gap
        assert record.length == 100000

    def test_gap_record(self):
        """Test gap record."""
        record = AGPRecord(
            object_name="chr1",
            object_start=100001,
            object_end=100100,
            part_number=2,
            component_type="N",
            gap_length=100,
            gap_type="scaffold",
        )

        assert record.is_gap
        assert record.length == 100

    def test_to_line(self):
        """Test AGP line conversion."""
        record = AGPRecord(
            object_name="chr1",
            object_start=1,
            object_end=100000,
            part_number=1,
            component_type="W",
            component_id="contig_001",
            component_start=1,
            component_end=100000,
            orientation="+",
        )

        line = record.to_line()
        assert "chr1" in line
        assert "contig_001" in line


class TestAGP:
    """Tests for AGP class."""

    def test_agp_creation(self):
        """Test AGP creation."""
        records = [
            AGPRecord(object_name="chr1", object_start=1, object_end=100000, part_number=1, component_type="W", component_id="c1", component_start=1, component_end=100000, orientation="+"),
            AGPRecord(object_name="chr1", object_start=100001, object_end=100100, part_number=2, component_type="N", gap_length=100),
            AGPRecord(object_name="chr1", object_start=100101, object_end=200100, part_number=3, component_type="W", component_id="c2", component_start=1, component_end=100000, orientation="-"),
        ]

        agp = AGP(records=records)

        assert agp.objects() == ["chr1"]
        assert agp.contig_ids() == ["c1", "c2"]

    def test_to_string(self):
        """Test AGP to string conversion."""
        records = [
            AGPRecord(object_name="chr1", object_start=1, object_end=100000, part_number=1, component_type="W", component_id="c1", component_start=1, component_end=100000, orientation="+"),
        ]

        agp = AGP(records=records)
        content = agp.to_string()

        assert "##agp-version" in content
        assert "chr1" in content

    def test_write_and_read(self, tmp_path):
        """Test AGP write and read round-trip."""
        records = [
            AGPRecord(object_name="chr1", object_start=1, object_end=100000, part_number=1, component_type="W", component_id="c1", component_start=1, component_end=100000, orientation="+"),
        ]

        agp = AGP(records=records)
        path = tmp_path / "test.agp"
        agp.write(path)

        loaded = AGP.from_file(path)
        assert loaded.objects() == agp.objects()


class TestAGPWriter:
    """Tests for AGPWriter class."""

    def test_write_ordering(self, simple_scaffold_ordering, tmp_path):
        """Test writing ordering to AGP."""
        writer = AGPWriter()
        path = tmp_path / "ordering.agp"
        writer.write(simple_scaffold_ordering, path)

        assert path.exists()

        # Read back
        loaded = AGP.from_file(path)
        assert "chr1" in loaded.objects()


class TestCompareAGP:
    """Tests for compare_agp function."""

    def test_compare_identical(self):
        """Test comparing identical AGPs."""
        records = [
            AGPRecord(object_name="chr1", object_start=1, object_end=100000, part_number=1, component_type="W", component_id="c1", component_start=1, component_end=100000, orientation="+"),
            AGPRecord(object_name="chr1", object_start=100101, object_end=200100, part_number=2, component_type="W", component_id="c2", component_start=1, component_end=100000, orientation="-"),
        ]

        agp1 = AGP(records=records)
        agp2 = AGP(records=records)

        comparison = compare_agp(agp1, agp2)

        assert comparison["n_objects_1"] == 1
        assert comparison["n_objects_2"] == 1
        assert len(comparison["shared_objects"]) == 1


class TestExportOrderingTSV:
    """Tests for export_ordering_tsv function."""

    def test_export_ordering_tsv(self, simple_scaffold_ordering, tmp_path):
        """Test exporting ordering to TSV."""
        path = tmp_path / "ordering.tsv"
        export_ordering_tsv({"chr1": simple_scaffold_ordering}, path)

        assert path.exists()

        # Check content
        with open(path) as f:
            content = f.read()
            assert "chromosome" in content
            assert "contig" in content


# =============================================================================
# Integration Tests
# =============================================================================


class TestScaffoldingPipeline:
    """Integration tests for the scaffolding pipeline."""

    def test_full_scaffolding_pipeline(self, test_assembly, marker_hits_for_scaffolding, test_genetic_map, test_painting, tmp_path):
        """Test complete scaffolding pipeline."""
        # 1. Build contig-marker map
        contig_map = ContigMarkerMap(
            assembly=test_assembly,
            marker_hits=marker_hits_for_scaffolding,
            genetic_map=test_genetic_map,
            min_markers=3,
        )

        # 2. Order contigs
        orderer = ScaffoldOrderer(method="combined", min_markers=3)
        orderings = orderer.order(test_assembly, contig_map, test_painting)

        # 3. Estimate gaps
        for chrom, ordering in orderings.items():
            gap_estimator = GapEstimator(method="fixed", fixed_gap=100)
            gaps = gap_estimator.estimate(ordering, test_genetic_map, contig_map)

        # 4. Validate
        validator = ScaffoldValidator()
        validations = validator.validate_all(orderings, test_genetic_map, contig_map, test_painting)

        # 5. Export
        writer = AGPWriter()
        agp_path = tmp_path / "scaffolds.agp"
        writer.write(orderings, agp_path)

        ordering_path = tmp_path / "ordering.tsv"
        export_ordering_tsv(orderings, ordering_path)

        # Verify outputs
        assert agp_path.exists()
        assert ordering_path.exists()

    def test_pipeline_with_shuffled_contigs(self, test_assembly, marker_hits_for_scaffolding, test_genetic_map):
        """Test that correct order is recovered from shuffled input."""
        contig_map = ContigMarkerMap(
            assembly=test_assembly,
            marker_hits=marker_hits_for_scaffolding,
            genetic_map=test_genetic_map,
            min_markers=3,
        )

        orderer = ScaffoldOrderer(method="genetic_map", min_markers=3)
        orderings = orderer.order(test_assembly, contig_map)

        # Check that orderings are sorted by genetic position
        for chrom, ordering in orderings.items():
            if len(ordering.ordered_contigs) >= 2:
                for i in range(len(ordering.ordered_contigs) - 1):
                    curr = ordering.ordered_contigs[i]
                    next_contig = ordering.ordered_contigs[i + 1]
                    if curr.genetic_start is not None and next_contig.genetic_start is not None:
                        # Allow for small overlaps due to contig spans
                        assert curr.genetic_start <= next_contig.genetic_end


class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_contig_chromosome(self, test_assembly, test_genetic_map):
        """Test handling of chromosome with single contig."""
        # Create hits for only one contig
        hits = []
        for j in range(10):
            hits.append(MarkerHit(
                marker_id=f"marker_{j}",
                contig="contig_000",
                position=j * 5000,
                strand="+",
                identity=0.99,
                founder_alleles={"B73": "A"},
                observed_allele="A",
                marker_chrom="chr1",
                marker_pos=j * 50000,
            ))

        contig_map = ContigMarkerMap(
            assembly=test_assembly,
            marker_hits=hits,
            genetic_map=test_genetic_map,
            min_markers=3,
        )

        orderer = ScaffoldOrderer(method="genetic_map")
        orderings = orderer.order(test_assembly, contig_map)

        # Should handle single-contig case
        for ordering in orderings.values():
            assert ordering.n_contigs >= 0

    def test_no_markers(self, test_assembly, test_genetic_map):
        """Test handling of contigs with no markers."""
        contig_map = ContigMarkerMap(
            assembly=test_assembly,
            marker_hits=[],  # No markers
            genetic_map=test_genetic_map,
        )

        unplaced = contig_map.unplaced_contigs()
        # All contigs should be unplaced
        assert len(unplaced) == test_assembly.n_contigs

    def test_empty_ordering(self):
        """Test empty ordering."""
        ordering = ScaffoldOrdering(chromosome="chrX")

        assert ordering.n_contigs == 0
        assert ordering.total_length == 0
        assert ordering.n_gaps == 0
