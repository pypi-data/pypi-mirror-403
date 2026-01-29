"""Haplotype proportion estimation module.

This module provides tools for estimating founder haplotype proportions
in derived samples using diagnostic markers.
"""

from __future__ import annotations

from haplophaser.proportion.blocks import (
    BlockResults,
    HaplotypeBlock,
    HaplotypeBlockCaller,
    SampleBlocks,
    call_haplotype_blocks,
)
from haplophaser.proportion.breakpoints import (
    Breakpoint,
    BreakpointFinder,
    BreakpointMethod,
    BreakpointResults,
    SampleBreakpoints,
    find_breakpoints,
)
from haplophaser.proportion.confidence import (
    ConfidenceEstimator,
    ConfidenceMethod,
    add_confidence_intervals,
)
from haplophaser.proportion.genotypes import (
    MarkerGenotype,
    MarkerGenotypeExtractor,
    SampleMarkerGenotypes,
)
from haplophaser.proportion.results import (
    ProportionResults,
    SampleProportions,
    WindowProportion,
)
from haplophaser.proportion.windows import (
    EstimationMethod,
    WindowProportionEstimator,
)

__all__ = [
    # Genotype extraction
    "MarkerGenotype",
    "MarkerGenotypeExtractor",
    "SampleMarkerGenotypes",
    # Results
    "ProportionResults",
    "SampleProportions",
    "WindowProportion",
    # Window estimation
    "EstimationMethod",
    "WindowProportionEstimator",
    # Confidence intervals
    "ConfidenceEstimator",
    "ConfidenceMethod",
    "add_confidence_intervals",
    # Block calling
    "BlockResults",
    "HaplotypeBlock",
    "HaplotypeBlockCaller",
    "SampleBlocks",
    "call_haplotype_blocks",
    # Breakpoint detection
    "Breakpoint",
    "BreakpointFinder",
    "BreakpointMethod",
    "BreakpointResults",
    "SampleBreakpoints",
    "find_breakpoints",
]
