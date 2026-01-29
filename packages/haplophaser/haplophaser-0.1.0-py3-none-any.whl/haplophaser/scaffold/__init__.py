"""
Scaffold ordering and orientation module.

This module provides tools for ordering and orienting contigs into
pseudomolecules using genetic map information and haplotype continuity.
"""

from __future__ import annotations

from haplophaser.scaffold.contig_markers import (
    ContigMarkerMap,
    ContigPlacement,
    MappedMarker,
)
from haplophaser.scaffold.continuity import (
    ContinuityScore,
    HaplotypeContinuityScorer,
    ProblematicJoin,
)
from haplophaser.scaffold.gaps import (
    GapEstimate,
    GapEstimator,
)
from haplophaser.scaffold.ordering import (
    OrderedContig,
    ScaffoldOrderer,
    ScaffoldOrdering,
)
from haplophaser.scaffold.orientation import (
    ContigOrienter,
    OrientationCall,
)
from haplophaser.scaffold.validation import (
    Inversion,
    ScaffoldValidator,
    UnexpectedSwitch,
    ValidationReport,
)

__all__ = [
    # Contig markers
    "ContigMarkerMap",
    "ContigPlacement",
    "MappedMarker",
    # Ordering
    "OrderedContig",
    "ScaffoldOrderer",
    "ScaffoldOrdering",
    # Orientation
    "ContigOrienter",
    "OrientationCall",
    # Continuity
    "ContinuityScore",
    "HaplotypeContinuityScorer",
    "ProblematicJoin",
    # Gaps
    "GapEstimate",
    "GapEstimator",
    # Validation
    "Inversion",
    "ScaffoldValidator",
    "UnexpectedSwitch",
    "ValidationReport",
]
