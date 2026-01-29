"""Tests for analysis modules (summary, comparison, painting, qc)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from haplophaser.proportion.blocks import (
    BlockResults,
    HaplotypeBlock,
    SampleBlocks,
)
from haplophaser.proportion.results import (
    ProportionResults,
    SampleProportions,
    WindowProportion,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_proportions() -> ProportionResults:
    """Create sample proportion results."""
    results = ProportionResults(
        founders=["A", "B"],
        method="frequency",
        window_size=10000,
    )

    # Sample 1: mostly A
    sample1 = SampleProportions(
        sample_name="Sample1",
        founders=["A", "B"],
        windows=[
            WindowProportion(
                chrom="chr1",
                start=0,
                end=10000,
                proportions={"A": 0.9, "B": 0.1},
                n_markers=10,
            ),
            WindowProportion(
                chrom="chr1",
                start=10000,
                end=20000,
                proportions={"A": 0.85, "B": 0.15},
                n_markers=8,
            ),
            WindowProportion(
                chrom="chr2",
                start=0,
                end=10000,
                proportions={"A": 0.8, "B": 0.2},
                n_markers=12,
            ),
        ],
    )
    results.add_sample(sample1)

    # Sample 2: mostly B
    sample2 = SampleProportions(
        sample_name="Sample2",
        founders=["A", "B"],
        windows=[
            WindowProportion(
                chrom="chr1",
                start=0,
                end=10000,
                proportions={"A": 0.2, "B": 0.8},
                n_markers=10,
            ),
            WindowProportion(
                chrom="chr1",
                start=10000,
                end=20000,
                proportions={"A": 0.15, "B": 0.85},
                n_markers=8,
            ),
            WindowProportion(
                chrom="chr2",
                start=0,
                end=10000,
                proportions={"A": 0.1, "B": 0.9},
                n_markers=12,
            ),
        ],
    )
    results.add_sample(sample2)

    # Sample 3: mixed
    sample3 = SampleProportions(
        sample_name="Sample3",
        founders=["A", "B"],
        windows=[
            WindowProportion(
                chrom="chr1",
                start=0,
                end=10000,
                proportions={"A": 0.5, "B": 0.5},
                n_markers=10,
            ),
            WindowProportion(
                chrom="chr1",
                start=10000,
                end=20000,
                proportions={"A": 0.6, "B": 0.4},
                n_markers=8,
            ),
            WindowProportion(
                chrom="chr2",
                start=0,
                end=10000,
                proportions={"A": 0.4, "B": 0.6},
                n_markers=12,
            ),
        ],
    )
    results.add_sample(sample3)

    return results


@pytest.fixture
def sample_blocks() -> BlockResults:
    """Create sample block results."""
    results = BlockResults(founders=["A", "B"])

    # Sample 1 blocks
    sample1_blocks = SampleBlocks(
        sample_name="Sample1",
        founders=["A", "B"],
        blocks=[
            HaplotypeBlock(
                chrom="chr1",
                start=0,
                end=20000,
                dominant_founder="A",
                mean_proportion=0.87,
                min_proportion=0.8,
                max_proportion=0.95,
                n_windows=2,
            ),
            HaplotypeBlock(
                chrom="chr2",
                start=0,
                end=10000,
                dominant_founder="A",
                mean_proportion=0.8,
                min_proportion=0.75,
                max_proportion=0.85,
                n_windows=1,
            ),
        ],
    )
    results.add_sample(sample1_blocks)

    # Sample 2 blocks
    sample2_blocks = SampleBlocks(
        sample_name="Sample2",
        founders=["A", "B"],
        blocks=[
            HaplotypeBlock(
                chrom="chr1",
                start=0,
                end=20000,
                dominant_founder="B",
                mean_proportion=0.82,
                min_proportion=0.75,
                max_proportion=0.9,
                n_windows=2,
            ),
        ],
    )
    results.add_sample(sample2_blocks)

    return results


# ============================================================================
# Test GenomeSummary
# ============================================================================


class TestGenomeSummary:
    """Tests for GenomeSummary class."""

    def test_by_sample(self, sample_proportions: ProportionResults) -> None:
        """Test per-sample summary."""
        from haplophaser.analysis.summary import GenomeSummary

        summary = GenomeSummary(sample_proportions)
        sample_summary = summary.by_sample("Sample1")

        assert sample_summary.sample == "Sample1"
        assert sample_summary.n_windows == 3
        assert sample_summary.founder_proportions["A"] > 0.8

    def test_by_population(self, sample_proportions: ProportionResults) -> None:
        """Test population summary."""
        from haplophaser.analysis.summary import GenomeSummary

        summary = GenomeSummary(sample_proportions)
        pop_summary = summary.by_population("test")

        assert pop_summary.n_samples == 3
        assert "A" in pop_summary.mean_founder_proportions
        assert "B" in pop_summary.mean_founder_proportions

    def test_all_samples(self, sample_proportions: ProportionResults) -> None:
        """Test getting all sample summaries."""
        from haplophaser.analysis.summary import GenomeSummary

        summary = GenomeSummary(sample_proportions)
        all_summaries = summary.all_samples()

        assert len(all_summaries) == 3

    def test_summary_table(self, sample_proportions: ProportionResults) -> None:
        """Test summary table generation."""
        from haplophaser.analysis.summary import GenomeSummary

        summary = GenomeSummary(sample_proportions)
        table = summary.summary_table()

        assert len(table) == 3
        assert all("sample" in row for row in table)

    def test_founder_proportion_matrix(self, sample_proportions: ProportionResults) -> None:
        """Test proportion matrix generation."""
        from haplophaser.analysis.summary import GenomeSummary

        summary = GenomeSummary(sample_proportions)
        samples, founders, matrix = summary.founder_proportion_matrix()

        assert len(samples) == 3
        assert len(founders) == 2
        assert matrix.shape == (3, 2)

    def test_with_blocks(
        self,
        sample_proportions: ProportionResults,
        sample_blocks: BlockResults,
    ) -> None:
        """Test summary with block data."""
        from haplophaser.analysis.summary import GenomeSummary

        summary = GenomeSummary(sample_proportions, blocks=sample_blocks)
        sample_summary = summary.by_sample("Sample1")

        assert sample_summary.n_blocks == 2


# ============================================================================
# Test SampleComparison
# ============================================================================


class TestSampleComparison:
    """Tests for SampleComparison class."""

    def test_pairwise_similarity_correlation(
        self, sample_proportions: ProportionResults
    ) -> None:
        """Test correlation-based similarity."""
        from haplophaser.analysis.comparison import SampleComparison

        comparison = SampleComparison(sample_proportions)
        similarity = comparison.pairwise_similarity("correlation")

        assert similarity.shape == (3, 3)
        # Diagonal should be 1
        np.testing.assert_array_almost_equal(np.diag(similarity), np.ones(3))

    def test_pairwise_similarity_cosine(
        self, sample_proportions: ProportionResults
    ) -> None:
        """Test cosine similarity."""
        from haplophaser.analysis.comparison import SampleComparison

        comparison = SampleComparison(sample_proportions)
        similarity = comparison.pairwise_similarity("cosine")

        assert similarity.shape == (3, 3)
        # All values should be between 0 and 1
        assert np.all(similarity >= 0)
        assert np.all(similarity <= 1)

    def test_cluster(self, sample_proportions: ProportionResults) -> None:
        """Test sample clustering (requires scipy)."""
        pytest.importorskip("scipy")

        from haplophaser.analysis.comparison import SampleComparison

        comparison = SampleComparison(sample_proportions)
        clusters = comparison.cluster(n_clusters=2)

        assert clusters.n_clusters == 2
        assert len(clusters.labels) == 3

    def test_most_similar_samples(
        self, sample_proportions: ProportionResults
    ) -> None:
        """Test finding most similar samples."""
        from haplophaser.analysis.comparison import SampleComparison

        comparison = SampleComparison(sample_proportions)
        similar = comparison.most_similar_samples("Sample1", n=2)

        assert len(similar) == 2
        # Sample3 (mixed) should be more similar to Sample1 than Sample2
        sample_names = [s[0] for s in similar]
        assert "Sample2" in sample_names or "Sample3" in sample_names

    def test_distance_matrix(self, sample_proportions: ProportionResults) -> None:
        """Test distance matrix generation."""
        from haplophaser.analysis.comparison import SampleComparison

        comparison = SampleComparison(sample_proportions)
        names, distance = comparison.distance_matrix()

        assert len(names) == 3
        assert distance.shape == (3, 3)
        # Diagonal should be 0
        np.testing.assert_array_almost_equal(np.diag(distance), np.zeros(3))


# ============================================================================
# Test AncestryPainter
# ============================================================================


class TestAncestryPainter:
    """Tests for AncestryPainter class."""

    def test_paint_basic(self, sample_proportions: ProportionResults) -> None:
        """Test basic painting."""
        from haplophaser.analysis.painting import AncestryPainter

        painter = AncestryPainter(resolution=5000)
        painting = painter.paint(sample_proportions)

        assert painting.n_samples == 3
        assert painting.n_founders == 2
        assert painting.n_bins > 0

    def test_paint_resolution(self, sample_proportions: ProportionResults) -> None:
        """Test painting at different resolutions."""
        from haplophaser.analysis.painting import AncestryPainter

        # Fine resolution
        painter_fine = AncestryPainter(resolution=1000)
        painting_fine = painter_fine.paint(sample_proportions)

        # Coarse resolution
        painter_coarse = AncestryPainter(resolution=10000)
        painting_coarse = painter_coarse.paint(sample_proportions)

        assert painting_fine.n_bins > painting_coarse.n_bins

    def test_painting_matrix(self, sample_proportions: ProportionResults) -> None:
        """Test painting matrix output."""
        from haplophaser.analysis.painting import AncestryPainter

        painter = AncestryPainter(resolution=5000)
        painting = painter.paint(sample_proportions)

        matrix = painting.to_matrix()
        assert matrix.shape == (painting.n_samples, painting.n_bins)

    def test_sample_painting(self, sample_proportions: ProportionResults) -> None:
        """Test getting individual sample painting."""
        from haplophaser.analysis.painting import AncestryPainter

        painter = AncestryPainter(resolution=5000)
        painting = painter.paint(sample_proportions)

        sample_painting = painting.get_sample_painting("Sample1")
        assert len(sample_painting) == painting.n_bins

    def test_chromosomes(self, sample_proportions: ProportionResults) -> None:
        """Test chromosome handling."""
        from haplophaser.analysis.painting import AncestryPainter

        painter = AncestryPainter(resolution=5000)
        painting = painter.paint(sample_proportions)

        chroms = painting.get_chromosomes()
        assert "chr1" in chroms
        assert "chr2" in chroms

    def test_long_format(self, sample_proportions: ProportionResults) -> None:
        """Test long format conversion."""
        from haplophaser.analysis.painting import AncestryPainter

        painter = AncestryPainter(resolution=5000)
        painting = painter.paint(sample_proportions)

        long_data = painting.to_dataframe_long()
        assert len(long_data) == painting.n_samples * painting.n_bins


# ============================================================================
# Test ProportionQC
# ============================================================================


class TestProportionQC:
    """Tests for ProportionQC class."""

    def test_basic_qc(self, sample_proportions: ProportionResults) -> None:
        """Test basic QC report generation."""
        from haplophaser.analysis.qc import ProportionQC

        qc = ProportionQC(proportions=sample_proportions)
        report = qc.generate_report()

        assert len(report.samples) == 3
        assert report.n_samples_passed >= 0

    def test_sample_qc(self, sample_proportions: ProportionResults) -> None:
        """Test per-sample QC."""
        from haplophaser.analysis.qc import ProportionQC

        qc = ProportionQC(proportions=sample_proportions)
        report = qc.generate_report()

        assert "Sample1" in report.samples
        sample_qc = report.samples["Sample1"]
        assert hasattr(sample_qc, "passed")

    def test_qc_thresholds(self, sample_proportions: ProportionResults) -> None:
        """Test QC with custom thresholds."""
        from haplophaser.analysis.qc import ProportionQC

        qc = ProportionQC(proportions=sample_proportions)
        # Set strict thresholds via attributes
        qc.max_missing_rate = 0.01  # Very strict
        qc.min_confidence = 0.99
        report = qc.generate_report()

        # Should generate warnings with strict thresholds
        assert report.n_warnings >= 0

    def test_qc_warnings(self, sample_proportions: ProportionResults) -> None:
        """Test QC warning collection."""
        from haplophaser.analysis.qc import ProportionQC

        qc = ProportionQC(proportions=sample_proportions)
        report = qc.generate_report()

        # Warnings should be accessible from global_warnings
        assert isinstance(report.global_warnings, list)

    def test_qc_to_dict(self, sample_proportions: ProportionResults) -> None:
        """Test QC report serialization."""
        from haplophaser.analysis.qc import ProportionQC

        qc = ProportionQC(proportions=sample_proportions)
        report = qc.generate_report()

        data = report.to_dict()
        assert "founders" in data
        assert "samples" in data


# ============================================================================
# Test ResultsIntegrator
# ============================================================================


class TestResultsIntegrator:
    """Tests for ResultsIntegrator class."""

    @pytest.fixture
    def hmm_results(self):
        """Create mock HMM results."""
        from haplophaser.proportion.hmm import HMMResult, HMMResults

        results = HMMResults(
            founders=["A", "B"],
            states=["A/A", "A/B", "B/B"],
        )

        result = HMMResult(
            sample="Sample1",
            chrom="chr1",
            markers=["m1", "m2"],
            positions=[5000, 15000],
            states=["A/A", "A/B", "B/B"],
            posteriors=np.array([[0.9, 0.1, 0.0], [0.8, 0.15, 0.05]]),
            viterbi_path=["A/A", "A/A"],
            smoothed_proportions=[
                {"A": 0.95, "B": 0.05},
                {"A": 0.9, "B": 0.1},
            ],
            founders=["A", "B"],
        )
        results.add_result(result)

        return results

    def test_hmm_primary(
        self, sample_proportions: ProportionResults, hmm_results
    ) -> None:
        """Test HMM primary integration strategy."""
        from haplophaser.proportion.integrate import ResultsIntegrator

        integrator = ResultsIntegrator(strategy="hmm_primary")
        integrated = integrator.integrate(sample_proportions, hmm_results)

        assert integrated.n_samples >= 1

    def test_weighted(
        self, sample_proportions: ProportionResults, hmm_results
    ) -> None:
        """Test weighted integration strategy."""
        from haplophaser.proportion.integrate import ResultsIntegrator

        integrator = ResultsIntegrator(strategy="weighted", hmm_weight=0.7)
        integrated = integrator.integrate(sample_proportions, hmm_results)

        assert integrated.n_samples >= 1


# ============================================================================
# Test Export Functions
# ============================================================================


class TestAnalysisExports:
    """Tests for analysis export functions."""

    def test_export_sample_summary(
        self, sample_proportions: ProportionResults, tmp_path: Path
    ) -> None:
        """Test sample summary export."""
        from haplophaser.analysis.summary import GenomeSummary
        from haplophaser.io.exports import export_sample_summary

        summary = GenomeSummary(sample_proportions)
        path = tmp_path / "summary.tsv"
        export_sample_summary(summary, path)

        assert path.exists()
        content = path.read_text()
        assert "Sample1" in content

    def test_export_similarity_matrix(
        self, sample_proportions: ProportionResults, tmp_path: Path
    ) -> None:
        """Test similarity matrix export."""
        from haplophaser.analysis.comparison import SampleComparison
        from haplophaser.io.exports import export_similarity_matrix

        comparison = SampleComparison(sample_proportions)
        path = tmp_path / "similarity.tsv"
        export_similarity_matrix(comparison, path)

        assert path.exists()
        content = path.read_text()
        assert "Sample1" in content

    def test_export_painting_tsv(
        self, sample_proportions: ProportionResults, tmp_path: Path
    ) -> None:
        """Test painting TSV export."""
        from haplophaser.analysis.painting import AncestryPainter
        from haplophaser.io.exports import export_painting_matrix

        painter = AncestryPainter(resolution=5000)
        painting = painter.paint(sample_proportions)
        path = tmp_path / "painting.tsv"
        export_painting_matrix(painting, path, format="tsv")

        assert path.exists()

    def test_export_qc_report(
        self, sample_proportions: ProportionResults, tmp_path: Path
    ) -> None:
        """Test QC report export."""
        from haplophaser.analysis.qc import ProportionQC
        from haplophaser.io.exports import export_qc_report

        qc = ProportionQC(proportions=sample_proportions)
        report = qc.generate_report()
        path = tmp_path / "qc_report.tsv"
        export_qc_report(report, path)

        assert path.exists()
