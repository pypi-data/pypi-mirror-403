"""Analysis module for haplotype proportion results.

This module provides tools for summarizing, comparing, and
visualizing haplotype proportion results.
"""

from __future__ import annotations

from haplophaser.analysis.comparison import (
    SampleComparison,
    SimilarityMethod,
)
from haplophaser.analysis.painting import (
    AncestryPainter,
    AncestryPainting,
)
from haplophaser.analysis.qc import (
    ProportionQC,
    QCReport,
)
from haplophaser.analysis.summary import (
    GenomeSummary,
    PopulationSummary,
    SampleSummary,
)

__all__ = [
    # Summary
    "GenomeSummary",
    "SampleSummary",
    "PopulationSummary",
    # Comparison
    "SampleComparison",
    "SimilarityMethod",
    # Painting
    "AncestryPainter",
    "AncestryPainting",
    # QC
    "ProportionQC",
    "QCReport",
]
