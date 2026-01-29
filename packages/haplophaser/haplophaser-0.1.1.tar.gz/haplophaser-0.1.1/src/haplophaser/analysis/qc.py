"""Quality control for haplotype proportion analysis.

This module provides comprehensive QC metrics and flags
potential issues in proportion estimation results.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from haplophaser.markers.diagnostic import DiagnosticMarkerSet
    from haplophaser.proportion.genotypes import SampleMarkerGenotypes
    from haplophaser.proportion.results import ProportionResults

logger = logging.getLogger(__name__)


@dataclass
class QCWarning:
    """A quality control warning.

    Attributes:
        level: Warning level ('info', 'warning', 'error')
        category: Warning category
        message: Detailed message
        sample: Affected sample (if applicable)
        chrom: Affected chromosome (if applicable)
    """

    level: str
    category: str
    message: str
    sample: str | None = None
    chrom: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "level": self.level,
            "category": self.category,
            "message": self.message,
            "sample": self.sample,
            "chrom": self.chrom,
        }


@dataclass
class SampleQC:
    """QC metrics for a single sample.

    Attributes:
        sample: Sample name
        n_markers: Number of markers with genotypes
        n_missing: Number of missing genotypes
        missing_rate: Proportion of missing genotypes
        mean_confidence: Mean proportion confidence
        low_confidence_rate: Proportion of low-confidence calls
        proportion_sum: Sum of genome-wide proportions
        heterozygosity: Proportion of heterozygous/mixed calls
        warnings: List of QC warnings
    """

    sample: str
    n_markers: int = 0
    n_missing: int = 0
    missing_rate: float = 0.0
    mean_confidence: float = 0.0
    low_confidence_rate: float = 0.0
    proportion_sum: float = 0.0
    heterozygosity: float = 0.0
    warnings: list[QCWarning] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Check if sample passed QC (no errors)."""
        return not any(w.level == "error" for w in self.warnings)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "sample": self.sample,
            "n_markers": self.n_markers,
            "n_missing": self.n_missing,
            "missing_rate": self.missing_rate,
            "mean_confidence": self.mean_confidence,
            "low_confidence_rate": self.low_confidence_rate,
            "proportion_sum": self.proportion_sum,
            "heterozygosity": self.heterozygosity,
            "passed": self.passed,
            "warnings": [w.to_dict() for w in self.warnings],
        }


@dataclass
class ChromosomeQC:
    """QC metrics for a single chromosome.

    Attributes:
        chrom: Chromosome name
        length: Chromosome length analyzed
        n_markers: Number of markers
        marker_density: Markers per Mb
        n_gaps: Number of large gaps
        max_gap: Largest gap in bp
        mean_confidence: Mean confidence across windows
        warnings: List of QC warnings
    """

    chrom: str
    length: int = 0
    n_markers: int = 0
    marker_density: float = 0.0
    n_gaps: int = 0
    max_gap: int = 0
    mean_confidence: float = 0.0
    warnings: list[QCWarning] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "chrom": self.chrom,
            "length": self.length,
            "n_markers": self.n_markers,
            "marker_density": self.marker_density,
            "n_gaps": self.n_gaps,
            "max_gap": self.max_gap,
            "mean_confidence": self.mean_confidence,
            "warnings": [w.to_dict() for w in self.warnings],
        }


@dataclass
class QCReport:
    """Complete QC report for proportion analysis.

    Attributes:
        samples: Dict mapping sample names to SampleQC
        chromosomes: Dict mapping chromosome names to ChromosomeQC
        founders: List of founder names
        global_warnings: Global QC warnings
        summary: Summary statistics
    """

    samples: dict[str, SampleQC] = field(default_factory=dict)
    chromosomes: dict[str, ChromosomeQC] = field(default_factory=dict)
    founders: list[str] = field(default_factory=list)
    global_warnings: list[QCWarning] = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    @property
    def n_samples_passed(self) -> int:
        """Count samples that passed QC."""
        return sum(1 for s in self.samples.values() if s.passed)

    @property
    def n_warnings(self) -> int:
        """Count total warnings."""
        return (
            len(self.global_warnings)
            + sum(len(s.warnings) for s in self.samples.values())
            + sum(len(c.warnings) for c in self.chromosomes.values())
        )

    @property
    def n_errors(self) -> int:
        """Count total errors."""
        all_warnings = (
            self.global_warnings
            + [w for s in self.samples.values() for w in s.warnings]
            + [w for c in self.chromosomes.values() for w in c.warnings]
        )
        return sum(1 for w in all_warnings if w.level == "error")

    def get_warnings_by_level(self, level: str) -> list[QCWarning]:
        """Get all warnings of a specific level."""
        all_warnings = (
            self.global_warnings
            + [w for s in self.samples.values() for w in s.warnings]
            + [w for c in self.chromosomes.values() for w in c.warnings]
        )
        return [w for w in all_warnings if w.level == level]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "n_samples": len(self.samples),
            "n_samples_passed": self.n_samples_passed,
            "n_chromosomes": len(self.chromosomes),
            "n_warnings": self.n_warnings,
            "n_errors": self.n_errors,
            "founders": self.founders,
            "samples": {k: v.to_dict() for k, v in self.samples.items()},
            "chromosomes": {k: v.to_dict() for k, v in self.chromosomes.items()},
            "global_warnings": [w.to_dict() for w in self.global_warnings],
            "summary": self.summary,
        }


class ProportionQC:
    """Quality control for proportion estimation results.

    Performs comprehensive QC checks and generates reports
    with warnings and recommendations.
    """

    def __init__(
        self,
        proportions: ProportionResults,
        marker_genotypes: dict[str, SampleMarkerGenotypes] | None = None,
        diagnostic_markers: DiagnosticMarkerSet | None = None,
        ploidy: int = 2,
    ) -> None:
        """Initialize QC checker.

        Args:
            proportions: Proportion estimation results
            marker_genotypes: Optional marker genotypes
            diagnostic_markers: Optional diagnostic marker set
            ploidy: Expected ploidy
        """
        self.proportions = proportions
        self.marker_genotypes = marker_genotypes
        self.diagnostic_markers = diagnostic_markers
        self.ploidy = ploidy
        self.founders = proportions.founders

        # Thresholds for warnings
        self.max_missing_rate = 0.3
        self.min_marker_density = 10  # per Mb
        self.max_gap_size = 5_000_000  # 5 Mb
        self.min_confidence = 0.7
        self.max_low_confidence_rate = 0.5
        self.proportion_sum_tolerance = 0.1

    def generate_report(self) -> QCReport:
        """Generate comprehensive QC report.

        Returns:
            QCReport with all QC metrics and warnings
        """
        logger.info("Generating QC report")

        report = QCReport(founders=self.founders)

        # Sample-level QC
        for sample in self.proportions:
            sample_qc = self._qc_sample(sample)
            report.samples[sample.sample_name] = sample_qc

        # Chromosome-level QC
        chrom_data = self._aggregate_chromosome_data()
        for chrom, data in chrom_data.items():
            chrom_qc = self._qc_chromosome(chrom, data)
            report.chromosomes[chrom] = chrom_qc

        # Global QC checks
        self._global_qc_checks(report)

        # Generate summary
        report.summary = self._generate_summary(report)

        logger.info(
            f"QC report: {report.n_samples_passed}/{len(report.samples)} samples passed, "
            f"{report.n_warnings} warnings, {report.n_errors} errors"
        )

        return report

    def _qc_sample(self, sample) -> SampleQC:
        """Perform QC for a single sample.

        Args:
            sample: SampleProportions object

        Returns:
            SampleQC object
        """
        warnings = []

        # Get genotype stats if available
        n_markers = sample.total_markers
        n_missing = 0
        missing_rate = 0.0

        if self.marker_genotypes is not None:
            genos = self.marker_genotypes.get(sample.sample_name)
            if genos is not None:
                n_missing = genos.n_missing
                missing_rate = genos.missing_rate

                if missing_rate > self.max_missing_rate:
                    warnings.append(QCWarning(
                        level="warning",
                        category="missing_data",
                        message=f"High missing rate: {missing_rate:.1%}",
                        sample=sample.sample_name,
                    ))

        # Check proportion sum
        proportion_sum = sum(sample.genome_wide.values())
        expected_sum = 1.0  # For proportions (should always sum to 1)

        if abs(proportion_sum - expected_sum) > self.proportion_sum_tolerance:
            warnings.append(QCWarning(
                level="warning",
                category="proportion_sum",
                message=f"Proportions sum to {proportion_sum:.3f}, expected {expected_sum:.3f}",
                sample=sample.sample_name,
            ))

        # Calculate confidence metrics
        confidences = []
        n_low_confidence = 0

        for window in sample.windows:
            # Use max proportion as confidence proxy
            if window.proportions:
                conf = max(window.proportions.values())
                confidences.append(conf)
                if conf < self.min_confidence:
                    n_low_confidence += 1

        mean_confidence = np.mean(confidences) if confidences else 0.0
        low_confidence_rate = n_low_confidence / len(confidences) if confidences else 0.0

        if low_confidence_rate > self.max_low_confidence_rate:
            warnings.append(QCWarning(
                level="warning",
                category="low_confidence",
                message=f"High proportion of low-confidence calls: {low_confidence_rate:.1%}",
                sample=sample.sample_name,
            ))

        # Calculate heterozygosity
        n_mixed = sum(1 for w in sample.windows if w.is_mixed)
        heterozygosity = n_mixed / len(sample.windows) if sample.windows else 0.0

        return SampleQC(
            sample=sample.sample_name,
            n_markers=n_markers,
            n_missing=n_missing,
            missing_rate=missing_rate,
            mean_confidence=mean_confidence,
            low_confidence_rate=low_confidence_rate,
            proportion_sum=proportion_sum,
            heterozygosity=heterozygosity,
            warnings=warnings,
        )

    def _aggregate_chromosome_data(self) -> dict[str, dict]:
        """Aggregate data across samples for each chromosome.

        Returns:
            Dict mapping chromosome to aggregated data
        """
        chrom_data: dict[str, dict] = {}

        for sample in self.proportions:
            for chrom in sample.get_chromosomes():
                if chrom not in chrom_data:
                    chrom_data[chrom] = {
                        "windows": [],
                        "markers": [],
                        "lengths": [],
                    }

                windows = sample.get_chromosome_windows(chrom)
                if windows:
                    chrom_data[chrom]["windows"].extend(windows)
                    chrom_data[chrom]["markers"].append(sum(w.n_markers for w in windows))

                    length = max(w.end for w in windows) - min(w.start for w in windows)
                    chrom_data[chrom]["lengths"].append(length)

        return chrom_data

    def _qc_chromosome(self, chrom: str, data: dict) -> ChromosomeQC:
        """Perform QC for a single chromosome.

        Args:
            chrom: Chromosome name
            data: Aggregated chromosome data

        Returns:
            ChromosomeQC object
        """
        warnings = []

        # Calculate statistics
        length = int(np.mean(data["lengths"])) if data["lengths"] else 0
        n_markers = int(np.mean(data["markers"])) if data["markers"] else 0
        marker_density = n_markers / (length / 1_000_000) if length > 0 else 0

        if marker_density < self.min_marker_density:
            warnings.append(QCWarning(
                level="warning",
                category="low_density",
                message=f"Low marker density: {marker_density:.1f} per Mb",
                chrom=chrom,
            ))

        # Find gaps
        windows = sorted(data["windows"], key=lambda w: w.start)
        gaps = []
        for i in range(1, len(windows)):
            gap = windows[i].start - windows[i - 1].end
            if gap > 0:
                gaps.append(gap)

        n_gaps = sum(1 for g in gaps if g > self.max_gap_size)
        max_gap = max(gaps) if gaps else 0

        if max_gap > self.max_gap_size:
            warnings.append(QCWarning(
                level="warning",
                category="large_gap",
                message=f"Large gap detected: {max_gap:,} bp",
                chrom=chrom,
            ))

        # Calculate mean confidence
        confidences = []
        for window in windows:
            if window.proportions:
                confidences.append(max(window.proportions.values()))

        mean_confidence = np.mean(confidences) if confidences else 0.0

        return ChromosomeQC(
            chrom=chrom,
            length=length,
            n_markers=n_markers,
            marker_density=marker_density,
            n_gaps=n_gaps,
            max_gap=max_gap,
            mean_confidence=mean_confidence,
            warnings=warnings,
        )

    def _global_qc_checks(self, report: QCReport) -> None:
        """Perform global QC checks.

        Args:
            report: QCReport to add warnings to
        """
        # Check founder distinguishability
        if self.diagnostic_markers is not None:
            n_markers = len(self.diagnostic_markers)
            if n_markers < 100:
                report.global_warnings.append(QCWarning(
                    level="warning",
                    category="low_markers",
                    message=f"Low number of diagnostic markers: {n_markers}",
                ))

            # Check marker classification distribution
            n_fully_diagnostic = len(self.diagnostic_markers.fully_diagnostic)
            if n_fully_diagnostic / n_markers < 0.5:
                report.global_warnings.append(QCWarning(
                    level="info",
                    category="marker_quality",
                    message=f"Only {n_fully_diagnostic / n_markers:.1%} of markers are fully diagnostic",
                ))

        # Check for samples with unusual patterns
        proportion_sums = [s.proportion_sum for s in report.samples.values()]
        if proportion_sums:
            mean_sum = np.mean(proportion_sums)
            std_sum = np.std(proportion_sums)

            for sample_name, sample_qc in report.samples.items():
                if std_sum > 0 and abs(sample_qc.proportion_sum - mean_sum) > 3 * std_sum:
                    sample_qc.warnings.append(QCWarning(
                        level="warning",
                        category="outlier",
                        message="Sample has unusual proportion distribution",
                        sample=sample_name,
                    ))

    def _generate_summary(self, report: QCReport) -> dict:
        """Generate summary statistics.

        Args:
            report: QCReport

        Returns:
            Summary dictionary
        """
        sample_qcs = list(report.samples.values())
        chrom_qcs = list(report.chromosomes.values())

        summary = {
            "n_samples_total": len(sample_qcs),
            "n_samples_passed": report.n_samples_passed,
            "n_chromosomes": len(chrom_qcs),
        }

        if sample_qcs:
            summary["mean_missing_rate"] = float(np.mean([s.missing_rate for s in sample_qcs]))
            summary["mean_confidence"] = float(np.mean([s.mean_confidence for s in sample_qcs]))
            summary["mean_heterozygosity"] = float(np.mean([s.heterozygosity for s in sample_qcs]))

        if chrom_qcs:
            summary["mean_marker_density"] = float(np.mean([c.marker_density for c in chrom_qcs]))
            summary["total_markers"] = int(sum(c.n_markers for c in chrom_qcs))

        summary["n_warnings"] = report.n_warnings
        summary["n_errors"] = report.n_errors

        return summary

    def flag_problematic_samples(
        self,
        max_missing: float = 0.3,
        max_low_confidence: float = 0.5,
    ) -> list[str]:
        """Identify samples that may have quality issues.

        Args:
            max_missing: Maximum acceptable missing rate
            max_low_confidence: Maximum acceptable low-confidence rate

        Returns:
            List of potentially problematic sample names
        """
        problematic = []

        for sample in self.proportions:
            # Check missing rate
            if self.marker_genotypes is not None:
                genos = self.marker_genotypes.get(sample.sample_name)
                if genos is not None and genos.missing_rate > max_missing:
                    problematic.append(sample.sample_name)
                    continue

            # Check confidence
            n_low = sum(
                1 for w in sample.windows
                if max(w.proportions.values()) < self.min_confidence
            )
            if len(sample.windows) > 0 and n_low / len(sample.windows) > max_low_confidence:
                problematic.append(sample.sample_name)

        return problematic

    def get_sample_recommendations(self, sample_name: str) -> list[str]:
        """Get recommendations for improving a sample's results.

        Args:
            sample_name: Sample to analyze

        Returns:
            List of recommendation strings
        """
        recommendations = []

        sample = self.proportions.get_sample(sample_name)
        if sample is None:
            return ["Sample not found in results"]

        # Check genotype quality
        if self.marker_genotypes is not None:
            genos = self.marker_genotypes.get(sample_name)
            if genos is not None and genos.missing_rate > 0.2:
                recommendations.append(
                    "Consider using lower quality thresholds or imputation "
                    "to reduce missing data rate"
                )

        # Check window coverage
        if len(sample.windows) < 10:
            recommendations.append(
                "Very few windows with data - consider using smaller window size "
                "or more markers"
            )

        # Check confidence
        confidences = [max(w.proportions.values()) for w in sample.windows if w.proportions]
        if confidences and np.mean(confidences) < 0.6:
            recommendations.append(
                "Low average confidence - results may be unreliable. "
                "Consider using HMM-based inference for smoothing"
            )

        return recommendations
