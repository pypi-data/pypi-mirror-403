"""
Expression language for declarative optimization.

This module provides a parser and evaluator for algebraic expressions
used in optimization problem specifications.

Supported syntax:
- Summation: sum(i in I: cost[i] * x[i])
- Products: a * x + b * y
- Powers: x^2 or x**2
- Functions: sqrt(x), log(x), exp(x), abs(x)
- Min/Max: min(x[i] for i in I), max(...)
- Comparisons: x <= 10, y >= 0, z == 5
- Indexing: x[i], cost[i,j], data.prices[t]

Examples:
    >>> from pyoptima.expression import parse_expression, evaluate_expression
    >>> expr = parse_expression("sum(i in I: cost[i] * x[i])")
    >>> result = evaluate_expression(expr, data={"cost": [1,2,3], "I": [0,1,2]}, vars={"x": x_vars})
"""

from pyoptima.expression.parser import (
    parse_expression,
    ExpressionParser,
    ParseError,
)
from pyoptima.expression.evaluator import (
    evaluate_expression,
    ExpressionEvaluator,
    EvaluationContext,
)
from pyoptima.expression.ast import (
    ExprNode,
    NumberNode,
    VariableNode,
    IndexedVarNode,
    BinaryOpNode,
    UnaryOpNode,
    FunctionNode,
    SumNode,
    ComparisonNode,
)

__all__ = [
    # Parser
    "parse_expression",
    "ExpressionParser",
    "ParseError",
    # Evaluator
    "evaluate_expression",
    "ExpressionEvaluator",
    "EvaluationContext",
    # AST nodes
    "ExprNode",
    "NumberNode",
    "VariableNode",
    "IndexedVarNode",
    "BinaryOpNode",
    "UnaryOpNode",
    "FunctionNode",
    "SumNode",
    "ComparisonNode",
]
