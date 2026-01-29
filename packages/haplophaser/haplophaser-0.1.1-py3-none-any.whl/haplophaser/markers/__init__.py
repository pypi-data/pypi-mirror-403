"""
Marker identification and analysis modules.

This package provides tools for identifying diagnostic markers that
differentiate founder populations and can be used to track haplotype
inheritance in derived samples.
"""

from haplophaser.markers.diagnostic import (
    DiagnosticMarker,
    DiagnosticMarkerFinder,
    MarkerClassification,
)
from haplophaser.markers.multifounder import (
    MultiFounderMarkerFinder,
    PairwiseMarker,
)
from haplophaser.markers.quality import (
    MarkerDensity,
    MarkerGap,
    MarkerQualityAssessment,
)

__all__ = [
    # diagnostic
    "DiagnosticMarker",
    "DiagnosticMarkerFinder",
    "MarkerClassification",
    # multifounder
    "MultiFounderMarkerFinder",
    "PairwiseMarker",
    # quality
    "MarkerQualityAssessment",
    "MarkerDensity",
    "MarkerGap",
]
