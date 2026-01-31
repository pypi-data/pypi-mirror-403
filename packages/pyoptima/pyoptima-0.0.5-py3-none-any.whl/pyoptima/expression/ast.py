"""
Abstract Syntax Tree (AST) nodes for the expression language.

These nodes represent parsed expressions in a tree structure that
can be evaluated or transformed.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple, Union


class ExprNode(ABC):
    """Base class for all expression AST nodes."""
    
    @abstractmethod
    def __repr__(self) -> str:
        pass
    
    @abstractmethod
    def to_string(self) -> str:
        """Convert back to expression string."""
        pass


@dataclass
class NumberNode(ExprNode):
    """Numeric literal node."""
    value: float
    
    def __repr__(self) -> str:
        return f"Number({self.value})"
    
    def to_string(self) -> str:
        if self.value == int(self.value):
            return str(int(self.value))
        return str(self.value)


@dataclass
class VariableNode(ExprNode):
    """Simple variable reference node."""
    name: str
    
    def __repr__(self) -> str:
        return f"Var({self.name})"
    
    def to_string(self) -> str:
        return self.name


@dataclass
class IndexedVarNode(ExprNode):
    """
    Indexed variable reference node (e.g., x[i], cost[i,j]).
    """
    name: str
    indices: List[Union["ExprNode", str]]  # Can be variable names or expressions
    
    def __repr__(self) -> str:
        idx_str = ", ".join(str(i) for i in self.indices)
        return f"IndexedVar({self.name}[{idx_str}])"
    
    def to_string(self) -> str:
        idx_strs = []
        for idx in self.indices:
            if isinstance(idx, str):
                idx_strs.append(idx)
            else:
                idx_strs.append(idx.to_string())
        return f"{self.name}[{', '.join(idx_strs)}]"


@dataclass
class ParameterRefNode(ExprNode):
    """
    Parameter reference node (e.g., ${param_name}, data.prices[t]).
    """
    path: List[str]  # Path components (e.g., ["data", "prices"])
    index: Optional[Union["ExprNode", str]] = None
    
    def __repr__(self) -> str:
        path_str = ".".join(self.path)
        if self.index:
            return f"ParamRef({path_str}[{self.index}])"
        return f"ParamRef({path_str})"
    
    def to_string(self) -> str:
        path_str = ".".join(self.path)
        if self.index:
            idx_str = self.index if isinstance(self.index, str) else self.index.to_string()
            return f"{path_str}[{idx_str}]"
        return path_str


@dataclass
class BinaryOpNode(ExprNode):
    """Binary operation node (e.g., a + b, x * y)."""
    op: str  # "+", "-", "*", "/", "^", "**"
    left: ExprNode
    right: ExprNode
    
    def __repr__(self) -> str:
        return f"BinaryOp({self.op}, {self.left}, {self.right})"
    
    def to_string(self) -> str:
        left_str = self.left.to_string()
        right_str = self.right.to_string()
        
        # Add parentheses for clarity
        if isinstance(self.left, BinaryOpNode):
            left_str = f"({left_str})"
        if isinstance(self.right, BinaryOpNode):
            right_str = f"({right_str})"
        
        if self.op == "^" or self.op == "**":
            return f"{left_str}^{right_str}"
        return f"{left_str} {self.op} {right_str}"


@dataclass
class UnaryOpNode(ExprNode):
    """Unary operation node (e.g., -x)."""
    op: str  # "-", "+"
    operand: ExprNode
    
    def __repr__(self) -> str:
        return f"UnaryOp({self.op}, {self.operand})"
    
    def to_string(self) -> str:
        operand_str = self.operand.to_string()
        if isinstance(self.operand, BinaryOpNode):
            operand_str = f"({operand_str})"
        return f"{self.op}{operand_str}"


@dataclass
class FunctionNode(ExprNode):
    """
    Function call node (e.g., sqrt(x), log(y), abs(z)).
    
    Supported functions:
    - Math: sqrt, log, exp, abs, sin, cos, tan
    - Aggregation: min, max (when not over a set)
    """
    name: str
    args: List[ExprNode]
    
    def __repr__(self) -> str:
        args_str = ", ".join(str(a) for a in self.args)
        return f"Function({self.name}({args_str}))"
    
    def to_string(self) -> str:
        args_str = ", ".join(a.to_string() for a in self.args)
        return f"{self.name}({args_str})"


@dataclass
class IndexSetSpec:
    """
    Index set specification (e.g., "i in I", "i in I, j in J where i < j").
    """
    variable: str  # Index variable name
    set_name: str  # Set name
    
    def __repr__(self) -> str:
        return f"{self.variable} in {self.set_name}"
    
    def to_string(self) -> str:
        return f"{self.variable} in {self.set_name}"


@dataclass
class SumNode(ExprNode):
    """
    Summation node (e.g., sum(i in I: cost[i] * x[i])).
    """
    index_specs: List[IndexSetSpec]
    expression: ExprNode
    condition: Optional[ExprNode] = None  # Optional "where" clause
    
    def __repr__(self) -> str:
        indices = ", ".join(str(s) for s in self.index_specs)
        cond = f" where {self.condition}" if self.condition else ""
        return f"Sum({indices}{cond}: {self.expression})"
    
    def to_string(self) -> str:
        indices = ", ".join(s.to_string() for s in self.index_specs)
        cond = f" where {self.condition.to_string()}" if self.condition else ""
        return f"sum({indices}{cond}: {self.expression.to_string()})"


@dataclass
class ProductNode(ExprNode):
    """
    Product node (e.g., prod(i in I: (1 + r[i]))).
    """
    index_specs: List[IndexSetSpec]
    expression: ExprNode
    condition: Optional[ExprNode] = None
    
    def __repr__(self) -> str:
        indices = ", ".join(str(s) for s in self.index_specs)
        cond = f" where {self.condition}" if self.condition else ""
        return f"Prod({indices}{cond}: {self.expression})"
    
    def to_string(self) -> str:
        indices = ", ".join(s.to_string() for s in self.index_specs)
        cond = f" where {self.condition.to_string()}" if self.condition else ""
        return f"prod({indices}{cond}: {self.expression.to_string()})"


@dataclass
class MinMaxNode(ExprNode):
    """
    Min/Max over a set (e.g., max(x[i] for i in I)).
    """
    operation: str  # "min" or "max"
    expression: ExprNode
    index_specs: List[IndexSetSpec]
    condition: Optional[ExprNode] = None
    
    def __repr__(self) -> str:
        indices = ", ".join(str(s) for s in self.index_specs)
        cond = f" where {self.condition}" if self.condition else ""
        return f"{self.operation.capitalize()}({self.expression} for {indices}{cond})"
    
    def to_string(self) -> str:
        indices = ", ".join(s.to_string() for s in self.index_specs)
        cond = f" where {self.condition.to_string()}" if self.condition else ""
        return f"{self.operation}({self.expression.to_string()} for {indices}{cond})"


@dataclass
class ComparisonNode(ExprNode):
    """
    Comparison node for constraints (e.g., x <= 10, y >= 0).
    """
    op: str  # "<=", ">=", "==", "<", ">", "!="
    left: ExprNode
    right: ExprNode
    
    def __repr__(self) -> str:
        return f"Comparison({self.left} {self.op} {self.right})"
    
    def to_string(self) -> str:
        return f"{self.left.to_string()} {self.op} {self.right.to_string()}"


@dataclass
class ImplicationNode(ExprNode):
    """
    Logical implication node (e.g., x[i] => y[j]).
    
    Used for indicator constraints.
    """
    antecedent: ExprNode
    consequent: ExprNode
    
    def __repr__(self) -> str:
        return f"Implication({self.antecedent} => {self.consequent})"
    
    def to_string(self) -> str:
        return f"{self.antecedent.to_string()} => {self.consequent.to_string()}"


@dataclass
class EquivalenceNode(ExprNode):
    """
    Logical equivalence node (e.g., x[i] <=> y[j]).
    """
    left: ExprNode
    right: ExprNode
    
    def __repr__(self) -> str:
        return f"Equivalence({self.left} <=> {self.right})"
    
    def to_string(self) -> str:
        return f"{self.left.to_string()} <=> {self.right.to_string()}"


@dataclass
class NormNode(ExprNode):
    """
    Norm node (e.g., norm2([x, y, z]), norm1(x)).
    """
    norm_type: int  # 1 for L1, 2 for L2
    args: List[ExprNode]
    
    def __repr__(self) -> str:
        args_str = ", ".join(str(a) for a in self.args)
        return f"Norm{self.norm_type}([{args_str}])"
    
    def to_string(self) -> str:
        args_str = ", ".join(a.to_string() for a in self.args)
        return f"norm{self.norm_type}([{args_str}])"


@dataclass
class PiecewiseNode(ExprNode):
    """
    Piecewise linear function node.
    """
    variable: ExprNode
    breakpoints: List[float]
    slopes: List[float]
    
    def __repr__(self) -> str:
        return f"Piecewise({self.variable}, bp={self.breakpoints}, slopes={self.slopes})"
    
    def to_string(self) -> str:
        bp_str = ", ".join(str(b) for b in self.breakpoints)
        sl_str = ", ".join(str(s) for s in self.slopes)
        return f"piecewise({self.variable.to_string()}, breakpoints=[{bp_str}], slopes=[{sl_str}])"


@dataclass
class ConditionalNode(ExprNode):
    """
    Conditional expression (if-then-else).
    """
    condition: ExprNode
    true_expr: ExprNode
    false_expr: ExprNode
    
    def __repr__(self) -> str:
        return f"If({self.condition}, {self.true_expr}, {self.false_expr})"
    
    def to_string(self) -> str:
        return f"if {self.condition.to_string()} then {self.true_expr.to_string()} else {self.false_expr.to_string()}"
