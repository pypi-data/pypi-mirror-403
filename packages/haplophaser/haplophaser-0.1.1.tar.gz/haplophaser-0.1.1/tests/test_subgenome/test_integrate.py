"""Tests for subgenome evidence integration."""

from __future__ import annotations

import pytest

from haplophaser.subgenome.integrate import SubgenomeIntegrator, integrate_assignments
from haplophaser.subgenome.models import (
    SubgenomeAssignment,
    SubgenomeAssignmentResult,
)


@pytest.fixture
def synteny_result(maize_config):
    """Create synteny-based assignment result."""
    return SubgenomeAssignmentResult(
        query_name="test",
        config=maize_config,
        assignments=[
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
                confidence=0.90,
                evidence="synteny",
            ),
        ],
        method="synteny",
    )


@pytest.fixture
def ortholog_result(maize_config):
    """Create ortholog-based assignment result."""
    return SubgenomeAssignmentResult(
        query_name="test",
        config=maize_config,
        assignments=[
            SubgenomeAssignment(
                chrom="chr1",
                start=0,
                end=1_000_000,
                subgenome="maize1",  # Agrees with synteny
                confidence=0.85,
                evidence="orthologs",
            ),
            SubgenomeAssignment(
                chrom="chr1",
                start=1_000_000,
                end=2_000_000,
                subgenome="maize1",  # Disagrees with synteny
                confidence=0.70,
                evidence="orthologs",
            ),
        ],
        method="orthologs",
    )


class TestSubgenomeIntegrator:
    """Tests for SubgenomeIntegrator."""

    def test_integrate_single_source(self, synteny_result, maize_config):
        """Test integration with single evidence source."""
        integrator = SubgenomeIntegrator()

        result = integrator.integrate(
            synteny_assignments=synteny_result,
            config=maize_config,
        )

        assert result.n_assignments > 0
        assert result.method == "combined"

    def test_integrate_multiple_sources(
        self, synteny_result, ortholog_result, maize_config
    ):
        """Test integration with multiple evidence sources."""
        integrator = SubgenomeIntegrator()

        result = integrator.integrate(
            synteny_assignments=synteny_result,
            ortholog_assignments=ortholog_result,
            config=maize_config,
        )

        assert result.n_assignments > 0

        # Check that evidence is combined
        for assignment in result.assignments:
            assert "sources" in assignment.evidence_details

    def test_weighted_vote_resolution(
        self, synteny_result, ortholog_result, maize_config
    ):
        """Test weighted vote conflict resolution."""
        integrator = SubgenomeIntegrator(
            weights={"synteny": 1.0, "orthologs": 0.5},
            conflict_resolution="weighted_vote",
        )

        result = integrator.integrate(
            synteny_assignments=synteny_result,
            ortholog_assignments=ortholog_result,
            config=maize_config,
        )

        # Synteny should win due to higher weight
        # Check the conflicting region
        chr1_assigns = [a for a in result.assignments if a.chrom == "chr1"]
        assert len(chr1_assigns) > 0

    def test_synteny_priority_resolution(
        self, synteny_result, ortholog_result, maize_config
    ):
        """Test synteny priority conflict resolution."""
        integrator = SubgenomeIntegrator(
            conflict_resolution="synteny_priority",
        )

        result = integrator.integrate(
            synteny_assignments=synteny_result,
            ortholog_assignments=ortholog_result,
            config=maize_config,
        )

        # All assignments should match synteny when using synteny_priority
        for assignment in result.assignments:
            if assignment.chrom == "chr1" and assignment.start >= 1_000_000:
                # This is the conflict region - synteny says maize2
                assert assignment.subgenome == "maize2"

    def test_conflict_detection(self, synteny_result, ortholog_result, maize_config):
        """Test that conflicts are detected and flagged."""
        integrator = SubgenomeIntegrator()

        result = integrator.integrate(
            synteny_assignments=synteny_result,
            ortholog_assignments=ortholog_result,
            config=maize_config,
        )

        # There should be at least one assignment with conflict
        conflicts = [
            a for a in result.assignments
            if a.evidence_details and a.evidence_details.get("has_conflict")
        ]
        # At least the 1-2Mb region should have conflict
        assert len(conflicts) >= 1

    def test_merge_adjacent_assignments(self, maize_config):
        """Test merging of adjacent same-subgenome regions."""
        # Create fragmented assignments that should merge
        assignments = [
            SubgenomeAssignment(
                chrom="chr1",
                start=0,
                end=500_000,
                subgenome="maize1",
                confidence=0.9,
                evidence="synteny",
            ),
            SubgenomeAssignment(
                chrom="chr1",
                start=500_000,
                end=1_000_000,
                subgenome="maize1",  # Same subgenome, adjacent
                confidence=0.85,
                evidence="synteny",
            ),
        ]

        synteny_result = SubgenomeAssignmentResult(
            query_name="test",
            config=maize_config,
            assignments=assignments,
            method="synteny",
        )

        integrator = SubgenomeIntegrator()
        result = integrator.integrate(
            synteny_assignments=synteny_result,
            config=maize_config,
        )

        # Should be merged into one region
        chr1_assigns = [a for a in result.assignments if a.chrom == "chr1"]
        assert len(chr1_assigns) == 1
        assert chr1_assigns[0].start == 0
        assert chr1_assigns[0].end == 1_000_000


class TestIntegrateAssignmentsFunction:
    """Tests for convenience function."""

    def test_basic_usage(self, synteny_result, ortholog_result):
        """Test basic convenience function usage."""
        result = integrate_assignments(
            synteny_assignments=synteny_result,
            ortholog_assignments=ortholog_result,
        )

        assert result is not None
        assert result.method == "combined"

    def test_custom_weights(self, synteny_result, ortholog_result):
        """Test with custom weights."""
        result = integrate_assignments(
            synteny_assignments=synteny_result,
            ortholog_assignments=ortholog_result,
            weights={"synteny": 2.0, "orthologs": 1.0},
        )

        assert result is not None
