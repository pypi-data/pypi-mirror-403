"""
Expression evaluator.

Evaluates parsed AST nodes into concrete values or Pyomo expressions.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from pyoptima.expression.ast import (
    BinaryOpNode,
    ComparisonNode,
    ExprNode,
    FunctionNode,
    IndexedVarNode,
    IndexSetSpec,
    MinMaxNode,
    NumberNode,
    ParameterRefNode,
    ProductNode,
    SumNode,
    UnaryOpNode,
    VariableNode,
)


@dataclass
class EvaluationContext:
    """
    Context for expression evaluation.
    
    Provides access to:
    - Variables (optimization decision variables)
    - Parameters (data values)
    - Sets (index sets)
    - Index bindings (current values of index variables during iteration)
    """
    variables: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    sets: Dict[str, List] = field(default_factory=dict)
    index_bindings: Dict[str, Any] = field(default_factory=dict)
    
    def get_variable(self, name: str, indices: Optional[tuple] = None) -> Any:
        """Get a variable, optionally indexed."""
        if name not in self.variables:
            raise ValueError(f"Variable '{name}' not found")
        
        var = self.variables[name]
        if indices is not None:
            if hasattr(var, '__getitem__'):
                return var[indices] if len(indices) > 1 else var[indices[0]]
            raise ValueError(f"Variable '{name}' is not indexable")
        return var
    
    def get_parameter(self, path: List[str], index: Optional[Any] = None) -> Any:
        """Get a parameter by path, optionally indexed."""
        value = self.parameters
        for part in path:
            if isinstance(value, dict):
                if part not in value:
                    raise ValueError(f"Parameter path not found: {'.'.join(path)}")
                value = value[part]
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                raise ValueError(f"Cannot access '{part}' in parameter path")
        
        if index is not None:
            if isinstance(value, dict):
                return value[index]
            elif hasattr(value, '__getitem__'):
                return value[index]
            else:
                raise ValueError(f"Parameter is not indexable")
        
        return value
    
    def get_set(self, name: str) -> List:
        """Get a set by name."""
        if name not in self.sets:
            raise ValueError(f"Set '{name}' not found")
        return self.sets[name]
    
    def get_index_value(self, name: str) -> Any:
        """Get current value of an index variable."""
        if name not in self.index_bindings:
            raise ValueError(f"Index variable '{name}' not bound")
        return self.index_bindings[name]
    
    def with_index_binding(self, name: str, value: Any) -> "EvaluationContext":
        """Create new context with additional index binding."""
        new_bindings = dict(self.index_bindings)
        new_bindings[name] = value
        return EvaluationContext(
            variables=self.variables,
            parameters=self.parameters,
            sets=self.sets,
            index_bindings=new_bindings
        )


class ExpressionEvaluator:
    """
    Evaluate parsed expressions.
    
    Can evaluate to:
    - Python numeric values (for constant expressions)
    - Pyomo expressions (for expressions involving variables)
    """
    
    # Built-in functions
    FUNCTIONS: Dict[str, Callable] = {
        "sqrt": math.sqrt,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "abs": abs,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "floor": math.floor,
        "ceil": math.ceil,
        "min": min,
        "max": max,
    }
    
    def __init__(self, context: Optional[EvaluationContext] = None, use_pyomo: bool = False):
        """
        Initialize evaluator.
        
        Args:
            context: Evaluation context with variables, parameters, sets
            use_pyomo: If True, generate Pyomo expressions
        """
        self.context = context or EvaluationContext()
        self.use_pyomo = use_pyomo
        
        if use_pyomo:
            try:
                import pyomo.environ as pyo
                self._pyo = pyo
            except ImportError:
                raise ImportError("Pyomo is required for Pyomo expression generation")
    
    def evaluate(self, node: ExprNode) -> Any:
        """
        Evaluate an expression node.
        
        Args:
            node: AST node to evaluate
            
        Returns:
            Evaluated value (numeric or Pyomo expression)
        """
        method_name = f"_eval_{type(node).__name__}"
        method = getattr(self, method_name, None)
        
        if method is None:
            raise NotImplementedError(f"Evaluation not implemented for {type(node).__name__}")
        
        return method(node)
    
    def _eval_NumberNode(self, node: NumberNode) -> float:
        return node.value
    
    def _eval_VariableNode(self, node: VariableNode) -> Any:
        # First check if it's an index binding
        if node.name in self.context.index_bindings:
            return self.context.index_bindings[node.name]
        
        # Then check if it's a variable
        if node.name in self.context.variables:
            return self.context.variables[node.name]
        
        # Then check if it's a parameter
        if node.name in self.context.parameters:
            return self.context.parameters[node.name]
        
        raise ValueError(f"Unknown identifier: {node.name}")
    
    def _eval_IndexedVarNode(self, node: IndexedVarNode) -> Any:
        # Evaluate indices
        indices = []
        for idx in node.indices:
            if isinstance(idx, str):
                # Simple index variable name
                if idx in self.context.index_bindings:
                    indices.append(self.context.index_bindings[idx])
                else:
                    indices.append(idx)
            else:
                indices.append(self.evaluate(idx))
        
        indices_tuple = tuple(indices) if len(indices) > 1 else indices[0]
        
        # Try as variable first
        if node.name in self.context.variables:
            var = self.context.variables[node.name]
            if hasattr(var, '__getitem__'):
                return var[indices_tuple]
            raise ValueError(f"Variable '{node.name}' is not indexable")
        
        # Try as parameter
        if node.name in self.context.parameters:
            param = self.context.parameters[node.name]
            return self._index_parameter(param, indices)
        
        raise ValueError(f"Unknown indexed identifier: {node.name}")
    
    def _index_parameter(self, param: Any, indices: List) -> Any:
        """Index into a parameter (dict, list, or nested structure)."""
        result = param
        for idx in indices:
            if isinstance(result, dict):
                result = result[idx]
            elif isinstance(result, (list, tuple)):
                result = result[idx]
            else:
                raise ValueError(f"Cannot index into {type(result)}")
        return result
    
    def _eval_ParameterRefNode(self, node: ParameterRefNode) -> Any:
        index = None
        if node.index is not None:
            if isinstance(node.index, str):
                if node.index in self.context.index_bindings:
                    index = self.context.index_bindings[node.index]
                else:
                    index = node.index
            else:
                index = self.evaluate(node.index)
        
        return self.context.get_parameter(node.path, index)
    
    def _eval_BinaryOpNode(self, node: BinaryOpNode) -> Any:
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        
        if node.op == "+":
            return left + right
        elif node.op == "-":
            return left - right
        elif node.op == "*":
            return left * right
        elif node.op == "/":
            return left / right
        elif node.op in ("^", "**"):
            if self.use_pyomo:
                return left ** right
            return pow(left, right)
        else:
            raise ValueError(f"Unknown operator: {node.op}")
    
    def _eval_UnaryOpNode(self, node: UnaryOpNode) -> Any:
        operand = self.evaluate(node.operand)
        
        if node.op == "-":
            return -operand
        elif node.op == "+":
            return operand
        else:
            raise ValueError(f"Unknown unary operator: {node.op}")
    
    def _eval_FunctionNode(self, node: FunctionNode) -> Any:
        args = [self.evaluate(arg) for arg in node.args]
        
        func_name = node.name.lower()
        
        if func_name in self.FUNCTIONS:
            return self.FUNCTIONS[func_name](*args)
        
        if self.use_pyomo:
            # Try Pyomo functions
            pyo_funcs = {
                "sqrt": self._pyo.sqrt,
                "log": self._pyo.log,
                "log10": self._pyo.log10,
                "exp": self._pyo.exp,
                "sin": self._pyo.sin,
                "cos": self._pyo.cos,
                "tan": self._pyo.tan,
            }
            if func_name in pyo_funcs:
                return pyo_funcs[func_name](*args)
        
        raise ValueError(f"Unknown function: {node.name}")
    
    def _eval_SumNode(self, node: SumNode) -> Any:
        """Evaluate a summation expression."""
        return self._iterate_over_indices(
            node.index_specs,
            node.expression,
            node.condition,
            lambda vals: sum(vals)
        )
    
    def _eval_ProductNode(self, node: ProductNode) -> Any:
        """Evaluate a product expression."""
        def product(vals):
            result = 1
            for v in vals:
                result *= v
            return result
        
        return self._iterate_over_indices(
            node.index_specs,
            node.expression,
            node.condition,
            product
        )
    
    def _eval_MinMaxNode(self, node: MinMaxNode) -> Any:
        """Evaluate min/max over a set."""
        op = min if node.operation == "min" else max
        return self._iterate_over_indices(
            node.index_specs,
            node.expression,
            node.condition,
            op
        )
    
    def _iterate_over_indices(
        self,
        index_specs: List[IndexSetSpec],
        body: ExprNode,
        condition: Optional[ExprNode],
        aggregator: Callable
    ) -> Any:
        """
        Iterate over index sets and aggregate results.
        
        Args:
            index_specs: List of index specifications
            body: Expression to evaluate for each combination
            condition: Optional filter condition
            aggregator: Function to aggregate results
        """
        values = []
        self._iterate_recursive(index_specs, 0, body, condition, values)
        return aggregator(values)
    
    def _iterate_recursive(
        self,
        index_specs: List[IndexSetSpec],
        spec_idx: int,
        body: ExprNode,
        condition: Optional[ExprNode],
        values: List
    ) -> None:
        """Recursively iterate over index specifications."""
        if spec_idx >= len(index_specs):
            # Check condition
            if condition is not None:
                cond_val = self.evaluate(condition)
                if not cond_val:
                    return
            
            # Evaluate body
            val = self.evaluate(body)
            values.append(val)
            return
        
        spec = index_specs[spec_idx]
        set_elements = self.context.get_set(spec.set_name)
        
        for element in set_elements:
            # Bind index variable
            old_bindings = dict(self.context.index_bindings)
            self.context.index_bindings[spec.variable] = element
            
            # Recurse
            self._iterate_recursive(index_specs, spec_idx + 1, body, condition, values)
            
            # Restore bindings
            self.context.index_bindings = old_bindings
    
    def _eval_ComparisonNode(self, node: ComparisonNode) -> Any:
        """Evaluate a comparison expression."""
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        
        if self.use_pyomo:
            # Return Pyomo constraint expression
            if node.op == "<=":
                return left <= right
            elif node.op == ">=":
                return left >= right
            elif node.op == "==":
                return left == right
            elif node.op == "<":
                return left < right
            elif node.op == ">":
                return left > right
            elif node.op == "!=":
                return left != right
        else:
            # Return boolean
            ops = {
                "<=": lambda a, b: a <= b,
                ">=": lambda a, b: a >= b,
                "==": lambda a, b: a == b,
                "<": lambda a, b: a < b,
                ">": lambda a, b: a > b,
                "!=": lambda a, b: a != b,
            }
            return ops[node.op](left, right)


def evaluate_expression(
    expression: Union[str, ExprNode],
    variables: Optional[Dict[str, Any]] = None,
    parameters: Optional[Dict[str, Any]] = None,
    sets: Optional[Dict[str, List]] = None,
    use_pyomo: bool = False
) -> Any:
    """
    Evaluate an expression with given context.
    
    Args:
        expression: Expression string or AST node
        variables: Optimization variables
        parameters: Data parameters
        sets: Index sets
        use_pyomo: If True, generate Pyomo expressions
        
    Returns:
        Evaluated value
        
    Examples:
        >>> evaluate_expression("2 + 3 * 4")
        14
        >>> evaluate_expression("sum(i in I: cost[i])", 
        ...     parameters={"cost": [1, 2, 3]}, sets={"I": [0, 1, 2]})
        6
    """
    from pyoptima.expression.parser import parse_expression
    
    if isinstance(expression, str):
        expression = parse_expression(expression)
    
    context = EvaluationContext(
        variables=variables or {},
        parameters=parameters or {},
        sets=sets or {}
    )
    
    evaluator = ExpressionEvaluator(context, use_pyomo=use_pyomo)
    return evaluator.evaluate(expression)
