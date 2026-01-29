"""
Expression analysis for homeolog expression bias in paleopolyploids.

This module provides tools for quantifying and analyzing expression patterns
of homeologous genes, including expression bias detection, condition-specific
analysis, and subgenome dominance testing.
"""

from __future__ import annotations

from haplophaser.expression.bias import (
    ExpressionBiasCalculator,
    calculate_expression_bias,
)
from haplophaser.expression.condition_bias import (
    ConditionBiasAnalyzer,
    analyze_condition_bias,
)
from haplophaser.expression.dominance import (
    SubgenomeDominanceAnalyzer,
    test_subgenome_dominance,
)
from haplophaser.expression.homeolog_expression import (
    HomeologExpressionExtractor,
    extract_homeolog_expression,
)
from haplophaser.expression.models import (
    ConditionBiasResult,
    DominanceResult,
    ExpressionBias,
    ExpressionBiasResult,
    ExpressionMatrix,
    ExpressionSample,
    HomeologExpression,
    HomeologExpressionResult,
)

__all__ = [
    # Models
    "ExpressionSample",
    "ExpressionMatrix",
    "HomeologExpression",
    "HomeologExpressionResult",
    "ExpressionBias",
    "ExpressionBiasResult",
    "ConditionBiasResult",
    "DominanceResult",
    # Homeolog expression
    "HomeologExpressionExtractor",
    "extract_homeolog_expression",
    # Bias calculation
    "ExpressionBiasCalculator",
    "calculate_expression_bias",
    # Condition analysis
    "ConditionBiasAnalyzer",
    "analyze_condition_bias",
    # Dominance testing
    "SubgenomeDominanceAnalyzer",
    "test_subgenome_dominance",
]
