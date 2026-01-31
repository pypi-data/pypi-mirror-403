"""
Expression language parser.

Parses algebraic expressions into an AST that can be evaluated.

Grammar (simplified):
    expr        := comparison | arith_expr
    comparison  := arith_expr comp_op arith_expr
    arith_expr  := term (('+' | '-') term)*
    term        := factor (('*' | '/') factor)*
    factor      := power | unary
    power       := atom ('^' | '**') factor | atom
    unary       := ('-' | '+') factor | atom
    atom        := number | function_call | sum_expr | indexed_var | variable | '(' expr ')'
    function_call := identifier '(' args ')'
    sum_expr    := 'sum' '(' index_specs ':' expr ')'
    indexed_var := identifier '[' indices ']'
    index_specs := index_spec (',' index_spec)*
    index_spec  := identifier 'in' identifier
"""

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Tuple, Union

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
    SumNode,
    UnaryOpNode,
    VariableNode,
)


class ParseError(Exception):
    """Error during expression parsing."""
    
    def __init__(self, message: str, position: int = -1, expression: str = ""):
        self.position = position
        self.expression = expression
        if position >= 0 and expression:
            pointer = " " * position + "^"
            message = f"{message}\n  {expression}\n  {pointer}"
        super().__init__(message)


class TokenType(Enum):
    """Token types for the lexer."""
    NUMBER = auto()
    IDENTIFIER = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    CARET = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    COLON = auto()
    DOT = auto()
    LEQ = auto()
    GEQ = auto()
    EQ = auto()
    LT = auto()
    GT = auto()
    NEQ = auto()
    IMPLIES = auto()
    EQUIV = auto()
    KEYWORD_SUM = auto()
    KEYWORD_PROD = auto()
    KEYWORD_MIN = auto()
    KEYWORD_MAX = auto()
    KEYWORD_IN = auto()
    KEYWORD_FOR = auto()
    KEYWORD_WHERE = auto()
    EOF = auto()


@dataclass
class Token:
    """Lexer token."""
    type: TokenType
    value: Union[str, float]
    position: int


class Lexer:
    """Tokenize expression strings."""
    
    KEYWORDS = {
        "sum": TokenType.KEYWORD_SUM,
        "prod": TokenType.KEYWORD_PROD,
        "product": TokenType.KEYWORD_PROD,
        "min": TokenType.KEYWORD_MIN,
        "max": TokenType.KEYWORD_MAX,
        "in": TokenType.KEYWORD_IN,
        "for": TokenType.KEYWORD_FOR,
        "where": TokenType.KEYWORD_WHERE,
    }
    
    def __init__(self, expression: str):
        self.expression = expression
        self.pos = 0
        self.length = len(expression)
    
    def tokenize(self) -> List[Token]:
        """Tokenize the expression."""
        tokens = []
        
        while self.pos < self.length:
            # Skip whitespace
            if self.expression[self.pos].isspace():
                self.pos += 1
                continue
            
            token = self._next_token()
            if token:
                tokens.append(token)
        
        tokens.append(Token(TokenType.EOF, "", self.pos))
        return tokens
    
    def _next_token(self) -> Optional[Token]:
        """Get the next token."""
        start_pos = self.pos
        char = self.expression[self.pos]
        
        # Number (integer or float)
        if char.isdigit() or (char == '.' and self.pos + 1 < self.length and self.expression[self.pos + 1].isdigit()):
            return self._read_number()
        
        # Identifier or keyword
        if char.isalpha() or char == '_':
            return self._read_identifier()
        
        # Multi-character operators
        if self.pos + 1 < self.length:
            two_char = self.expression[self.pos:self.pos + 2]
            if two_char == "<=":
                self.pos += 2
                return Token(TokenType.LEQ, "<=", start_pos)
            elif two_char == ">=":
                self.pos += 2
                return Token(TokenType.GEQ, ">=", start_pos)
            elif two_char == "==":
                self.pos += 2
                return Token(TokenType.EQ, "==", start_pos)
            elif two_char == "!=":
                self.pos += 2
                return Token(TokenType.NEQ, "!=", start_pos)
            elif two_char == "=>":
                self.pos += 2
                return Token(TokenType.IMPLIES, "=>", start_pos)
            elif two_char == "**":
                self.pos += 2
                return Token(TokenType.CARET, "**", start_pos)
        
        # Three-character operators
        if self.pos + 2 < self.length:
            three_char = self.expression[self.pos:self.pos + 3]
            if three_char == "<=>":
                self.pos += 3
                return Token(TokenType.EQUIV, "<=>", start_pos)
        
        # Single-character tokens
        single_char_tokens = {
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.STAR,
            '/': TokenType.SLASH,
            '^': TokenType.CARET,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '[': TokenType.LBRACKET,
            ']': TokenType.RBRACKET,
            ',': TokenType.COMMA,
            ':': TokenType.COLON,
            '.': TokenType.DOT,
            '<': TokenType.LT,
            '>': TokenType.GT,
        }
        
        if char in single_char_tokens:
            self.pos += 1
            return Token(single_char_tokens[char], char, start_pos)
        
        raise ParseError(f"Unexpected character: '{char}'", start_pos, self.expression)
    
    def _read_number(self) -> Token:
        """Read a number token."""
        start_pos = self.pos
        result = ""
        has_dot = False
        
        while self.pos < self.length:
            char = self.expression[self.pos]
            if char.isdigit():
                result += char
                self.pos += 1
            elif char == '.' and not has_dot:
                has_dot = True
                result += char
                self.pos += 1
            elif char in ('e', 'E') and result:
                result += char
                self.pos += 1
                if self.pos < self.length and self.expression[self.pos] in ('+', '-'):
                    result += self.expression[self.pos]
                    self.pos += 1
            else:
                break
        
        return Token(TokenType.NUMBER, float(result), start_pos)
    
    def _read_identifier(self) -> Token:
        """Read an identifier or keyword token."""
        start_pos = self.pos
        result = ""
        
        while self.pos < self.length:
            char = self.expression[self.pos]
            if char.isalnum() or char == '_':
                result += char
                self.pos += 1
            else:
                break
        
        # Check if keyword
        token_type = self.KEYWORDS.get(result.lower(), TokenType.IDENTIFIER)
        return Token(token_type, result, start_pos)


class ExpressionParser:
    """
    Parse expression strings into AST nodes.
    
    Example usage:
        parser = ExpressionParser("sum(i in I: cost[i] * x[i])")
        ast = parser.parse()
    """
    
    def __init__(self, expression: str):
        self.expression = expression
        self.lexer = Lexer(expression)
        self.tokens: List[Token] = []
        self.pos = 0
    
    def parse(self) -> ExprNode:
        """Parse the expression and return an AST."""
        self.tokens = self.lexer.tokenize()
        self.pos = 0
        
        result = self._parse_expression()
        
        if not self._is_at_end():
            raise ParseError(
                f"Unexpected token: {self._current().value}",
                self._current().position,
                self.expression
            )
        
        return result
    
    # Token helpers
    def _current(self) -> Token:
        return self.tokens[self.pos]
    
    def _peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]
    
    def _is_at_end(self) -> bool:
        return self._current().type == TokenType.EOF
    
    def _advance(self) -> Token:
        token = self._current()
        if not self._is_at_end():
            self.pos += 1
        return token
    
    def _match(self, *types: TokenType) -> bool:
        if self._current().type in types:
            self._advance()
            return True
        return False
    
    def _expect(self, token_type: TokenType, message: str = "") -> Token:
        if self._current().type == token_type:
            return self._advance()
        raise ParseError(
            message or f"Expected {token_type.name}, got {self._current().type.name}",
            self._current().position,
            self.expression
        )
    
    # Parsing methods
    def _parse_expression(self) -> ExprNode:
        """Parse an expression (may include comparison)."""
        left = self._parse_arith_expression()
        
        comp_ops = {
            TokenType.LEQ: "<=",
            TokenType.GEQ: ">=",
            TokenType.EQ: "==",
            TokenType.LT: "<",
            TokenType.GT: ">",
            TokenType.NEQ: "!=",
        }
        
        if self._current().type in comp_ops:
            op_token = self._advance()
            right = self._parse_arith_expression()
            return ComparisonNode(comp_ops[op_token.type], left, right)
        
        return left
    
    def _parse_arith_expression(self) -> ExprNode:
        """Parse addition/subtraction."""
        left = self._parse_term()
        
        while self._current().type in (TokenType.PLUS, TokenType.MINUS):
            op = "+" if self._current().type == TokenType.PLUS else "-"
            self._advance()
            right = self._parse_term()
            left = BinaryOpNode(op, left, right)
        
        return left
    
    def _parse_term(self) -> ExprNode:
        """Parse multiplication/division."""
        left = self._parse_factor()
        
        while self._current().type in (TokenType.STAR, TokenType.SLASH):
            op = "*" if self._current().type == TokenType.STAR else "/"
            self._advance()
            right = self._parse_factor()
            left = BinaryOpNode(op, left, right)
        
        return left
    
    def _parse_factor(self) -> ExprNode:
        """Parse power or unary."""
        return self._parse_unary()
    
    def _parse_unary(self) -> ExprNode:
        """Parse unary operators."""
        if self._current().type in (TokenType.MINUS, TokenType.PLUS):
            op = self._advance().value
            operand = self._parse_unary()
            return UnaryOpNode(op, operand)
        
        return self._parse_power()
    
    def _parse_power(self) -> ExprNode:
        """Parse power expressions (right-associative)."""
        base = self._parse_atom()
        
        if self._current().type == TokenType.CARET:
            self._advance()
            exponent = self._parse_factor()
            return BinaryOpNode("^", base, exponent)
        
        return base
    
    def _parse_atom(self) -> ExprNode:
        """Parse atomic expressions."""
        token = self._current()
        
        # Number
        if token.type == TokenType.NUMBER:
            self._advance()
            return NumberNode(token.value)
        
        # Parenthesized expression
        if token.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN, "Expected ')'")
            return expr
        
        # Sum expression
        if token.type == TokenType.KEYWORD_SUM:
            return self._parse_sum()
        
        # Min/Max over set
        if token.type in (TokenType.KEYWORD_MIN, TokenType.KEYWORD_MAX):
            return self._parse_minmax()
        
        # Identifier (variable, indexed variable, or function call)
        if token.type == TokenType.IDENTIFIER:
            return self._parse_identifier()
        
        raise ParseError(
            f"Unexpected token: {token.value}",
            token.position,
            self.expression
        )
    
    def _parse_identifier(self) -> ExprNode:
        """Parse identifier-based expressions."""
        name_token = self._advance()
        name = name_token.value
        
        # Check for function call
        if self._current().type == TokenType.LPAREN:
            return self._parse_function_call(name)
        
        # Check for indexing
        if self._current().type == TokenType.LBRACKET:
            return self._parse_indexed_var(name)
        
        # Check for dot notation (parameter reference)
        if self._current().type == TokenType.DOT:
            return self._parse_parameter_ref(name)
        
        # Simple variable
        return VariableNode(name)
    
    def _parse_function_call(self, name: str) -> ExprNode:
        """Parse a function call."""
        self._expect(TokenType.LPAREN)
        
        args = []
        if self._current().type != TokenType.RPAREN:
            args.append(self._parse_expression())
            while self._match(TokenType.COMMA):
                args.append(self._parse_expression())
        
        self._expect(TokenType.RPAREN, "Expected ')' after function arguments")
        
        return FunctionNode(name, args)
    
    def _parse_indexed_var(self, name: str) -> ExprNode:
        """Parse an indexed variable."""
        self._expect(TokenType.LBRACKET)
        
        indices = []
        indices.append(self._parse_index())
        while self._match(TokenType.COMMA):
            indices.append(self._parse_index())
        
        self._expect(TokenType.RBRACKET, "Expected ']'")
        
        return IndexedVarNode(name, indices)
    
    def _parse_index(self) -> Union[ExprNode, str]:
        """Parse a single index (can be identifier or expression)."""
        if self._current().type == TokenType.IDENTIFIER:
            # Check if it's a simple identifier (common case)
            if self._peek(1).type in (TokenType.COMMA, TokenType.RBRACKET):
                return self._advance().value
        
        return self._parse_expression()
    
    def _parse_parameter_ref(self, first_name: str) -> ExprNode:
        """Parse a parameter reference (e.g., data.prices[t])."""
        path = [first_name]
        
        while self._match(TokenType.DOT):
            if self._current().type != TokenType.IDENTIFIER:
                raise ParseError("Expected identifier after '.'", self._current().position, self.expression)
            path.append(self._advance().value)
        
        index = None
        if self._current().type == TokenType.LBRACKET:
            self._advance()
            index = self._parse_index()
            self._expect(TokenType.RBRACKET)
        
        return ParameterRefNode(path, index)
    
    def _parse_sum(self) -> ExprNode:
        """Parse a sum expression."""
        self._expect(TokenType.KEYWORD_SUM)
        self._expect(TokenType.LPAREN)
        
        # Parse index specifications
        index_specs = self._parse_index_specs()
        
        # Parse optional where clause
        condition = None
        if self._current().type == TokenType.KEYWORD_WHERE:
            self._advance()
            condition = self._parse_expression()
        
        # Expect colon
        self._expect(TokenType.COLON, "Expected ':' in sum expression")
        
        # Parse body expression
        body = self._parse_expression()
        
        self._expect(TokenType.RPAREN)
        
        return SumNode(index_specs, body, condition)
    
    def _parse_minmax(self) -> ExprNode:
        """Parse min/max over a set."""
        op_token = self._advance()
        operation = "min" if op_token.type == TokenType.KEYWORD_MIN else "max"
        
        self._expect(TokenType.LPAREN)
        
        # Parse the expression
        expr = self._parse_expression()
        
        # Check for "for" keyword
        if self._current().type == TokenType.KEYWORD_FOR:
            self._advance()
            index_specs = self._parse_index_specs()
            
            condition = None
            if self._current().type == TokenType.KEYWORD_WHERE:
                self._advance()
                condition = self._parse_expression()
            
            self._expect(TokenType.RPAREN)
            return MinMaxNode(operation, expr, index_specs, condition)
        
        # Simple function call (min/max of multiple args)
        args = [expr]
        while self._match(TokenType.COMMA):
            args.append(self._parse_expression())
        
        self._expect(TokenType.RPAREN)
        return FunctionNode(operation, args)
    
    def _parse_index_specs(self) -> List[IndexSetSpec]:
        """Parse index specifications (e.g., "i in I, j in J")."""
        specs = []
        specs.append(self._parse_single_index_spec())
        
        while self._match(TokenType.COMMA):
            # Check if this is another index spec or end of specs
            if self._current().type == TokenType.IDENTIFIER and self._peek(1).type == TokenType.KEYWORD_IN:
                specs.append(self._parse_single_index_spec())
            else:
                # Not an index spec, backtrack
                self.pos -= 1
                break
        
        return specs
    
    def _parse_single_index_spec(self) -> IndexSetSpec:
        """Parse a single index specification (e.g., "i in I")."""
        var_token = self._expect(TokenType.IDENTIFIER, "Expected index variable")
        self._expect(TokenType.KEYWORD_IN, "Expected 'in'")
        set_token = self._expect(TokenType.IDENTIFIER, "Expected set name")
        
        return IndexSetSpec(var_token.value, set_token.value)


def parse_expression(expression: str) -> ExprNode:
    """
    Parse an expression string into an AST.
    
    Args:
        expression: Expression string to parse
        
    Returns:
        ExprNode representing the parsed expression
        
    Raises:
        ParseError: If parsing fails
        
    Examples:
        >>> ast = parse_expression("sum(i in I: cost[i] * x[i])")
        >>> ast = parse_expression("x + y * z")
        >>> ast = parse_expression("sqrt(x^2 + y^2)")
    """
    parser = ExpressionParser(expression)
    return parser.parse()
