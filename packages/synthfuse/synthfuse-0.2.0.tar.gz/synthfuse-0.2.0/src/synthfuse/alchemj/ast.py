# src/synthfuse/alchemj/ast.py
"""
ALCHEM-J Spell Parser: Recursive descent parser for symbolic fusion expressions.
Grammar:
    spell        → expr
    expr         → term (⊕ term)*
    term         → factor (⊗ factor)*
    factor       → primary (∘ primary)*
    primary      → SYMBOL (params)? | '(' expr ')'
    params       → '(' param_list ')'
    param_list   → param (',' param)*
    param        → IDENT '=' LITERAL
    LITERAL      → NUMBER | STRING
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Union, Optional, Any
import math

# ──────────────── AST Nodes ────────────────

@dataclass(frozen=True)
class Param:
    name: str
    value: Any  # float, int, str

@dataclass(frozen=True)
class Primitive:
    symbol: str
    params: Dict[str, Any]  # e.g., {"r": 3.8}

@dataclass(frozen=True)
class Combinator:
    op: str  # "⊗", "⊕", "∘"
    left: Expr
    right: Expr

Expr = Union[Primitive, Combinator]

# ──────────────── Lexer ────────────────

class Token:
    def __init__(self, type_: str, value: Any, pos: int):
        self.type = type_
        self.value = value
        self.pos = pos

    def __repr__(self):
        return f"Token({self.type}, {self.value})"

class Lexer:
    KEYWORDS = {"true", "false", "null"}
    
    def __init__(self, text: str):
        self.text = text.strip()
        self.pos = 0
        self.tokens: List[Token] = []
        self.tokenize()

    def tokenize(self):
        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch.isspace():
                self.pos += 1
            elif ch in '()':
                self.tokens.append(Token(ch, ch, self.pos))
                self.pos += 1
            elif ch in '⊗⊕∘':
                self.tokens.append(Token('OP', ch, self.pos))
                self.pos += 1
            elif ch.isalpha() or ch == '_':
                self.tokens.append(self._read_symbol())
            elif ch.isdigit() or ch == '.':
                self.tokens.append(self._read_number())
            elif ch == '=':
                self.tokens.append(Token('EQUALS', '=', self.pos))
                self.pos += 1
            elif ch == ',':
                self.tokens.append(Token('COMMA', ',', self.pos))
                self.pos += 1
            elif ch == '"':
                self.tokens.append(self._read_string())
            else:
                raise SyntaxError(f"Unexpected character '{ch}' at position {self.pos}")

    def _read_symbol(self) -> Token:
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] in '𝔻𝕂𝕊𝕍ℝℂℤℍ𝕃𝕀ℛ∇̃𝓜𝓐_'):
            self.pos += 1
        value = self.text[start:self.pos]
        return Token('SYMBOL', value, start)

    def _read_number(self) -> Token:
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isdigit() or self.text[self.pos] in '.eE+-'):
            self.pos += 1
        value_str = self.text[start:self.pos]
        try:
            if '.' in value_str or 'e' in value_str.lower():
                value = float(value_str)
                # Handle special floats
                if math.isnan(value):
                    value = float('nan')
                elif math.isinf(value):
                    value = float('inf')
            else:
                value = int(value_str)
        except ValueError:
            raise SyntaxError(f"Invalid number '{value_str}' at position {start}")
        return Token('NUMBER', value, start)

    def _read_string(self) -> Token:
        self.pos += 1  # skip opening "
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] != '"':
            if self.text[self.pos] == '\\':
                self.pos += 2  # skip escape
            else:
                self.pos += 1
        value = self.text[start:self.pos]
        self.pos += 1  # skip closing "
        return Token('STRING', value, start)

# ──────────────── Parser ────────────────

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset=0) -> Optional[Token]:
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else None

    def consume(self, expected_type: str) -> Token:
        tok = self.peek()
        if tok and tok.type == expected_type:
            self.pos += 1
            return tok
        raise SyntaxError(f"Expected {expected_type}, got {tok} at position {tok.pos if tok else 'EOF'}")

    def parse(self) -> Expr:
        expr = self.parse_expr()
        if self.pos < len(self.tokens):
            raise SyntaxError(f"Unexpected token after expression: {self.tokens[self.pos]}")
        return expr

    def parse_expr(self) -> Expr:
        # expr → term (⊕ term)*
        left = self.parse_term()
        while self.peek() and self.peek().type == 'OP' and self.peek().value == '⊕':
            self.consume('OP')
            right = self.parse_term()
            left = Combinator('⊕', left, right)
        return left

    def parse_term(self) -> Expr:
        # term → factor (⊗ factor)*
        left = self.parse_factor()
        while self.peek() and self.peek().type == 'OP' and self.peek().value == '⊗':
            self.consume('OP')
            right = self.parse_factor()
            left = Combinator('⊗', left, right)
        return left

    def parse_factor(self) -> Expr:
        # factor → primary (∘ primary)*
        left = self.parse_primary()
        while self.peek() and self.peek().type == 'OP' and self.peek().value == '∘':
            self.consume('OP')
            right = self.parse_primary()
            left = Combinator('∘', left, right)
        return left

    def parse_primary(self) -> Expr:
        # primary → SYMBOL (params)? | '(' expr ')'
        tok = self.peek()
        if tok and tok.type == 'SYMBOL':
            self.consume('SYMBOL')
            symbol = tok.value
            params = {}
            if self.peek() and self.peek().type == '(':
                params = self.parse_params()
            return Primitive(symbol, params)
        elif tok and tok.type == '(':
            self.consume('(')
            expr = self.parse_expr()
            self.consume(')')
            return expr
        else:
            raise SyntaxError(f"Expected SYMBOL or '(', got {tok}")

    def parse_params(self) -> Dict[str, Any]:
        # params → '(' param_list ')'
        self.consume('(')
        params = {}
        if self.peek() and self.peek().type != ')':
            while True:
                param = self.parse_param()
                params[param.name] = param.value
                if self.peek() and self.peek().type == ',':
                    self.consume(',')
                else:
                    break
        self.consume(')')
        return params

    def parse_param(self) -> Param:
        # param → IDENT '=' LITERAL
        ident_tok = self.consume('SYMBOL')
        self.consume('EQUALS')
        lit_tok = self.peek()
        if lit_tok and lit_tok.type in ('NUMBER', 'STRING'):
            self.pos += 1
            return Param(ident_tok.value, lit_tok.value)
        else:
            raise SyntaxError(f"Expected NUMBER or STRING after '=', got {lit_tok}")

# ──────────────── Public API ────────────────

def parse_spell_ast(spell: str) -> Expr:
    """Parse a spell string into an AST."""
    if not spell.strip():
        raise ValueError("Empty spell")
    lexer = Lexer(spell)
    parser = Parser(lexer.tokens)
    return parser.parse()

def ast_to_spell(ast_node: Expr) -> str:
    """Convert AST back to spell string (lossless for round-trip)."""
    if isinstance(ast_node, Primitive):
        if ast_node.params:
            params_str = ", ".join(f"{k}={v}" for k, v in ast_node.params.items())
            return f"{ast_node.symbol}({params_str})"
        else:
            return ast_node.symbol
    elif isinstance(ast_node, Combinator):
        left_str = ast_to_spell(ast_node.left)
        right_str = ast_to_spell(ast_node.right)
        # Add parens for clarity in nested ops
        return f"({left_str} {ast_node.op} {right_str})"
    else:
        raise TypeError(f"Unknown AST node: {ast_node}")

# ──────────────── Utility: Parameter Manipulation ────────────────

def update_param_in_spell(spell: str, symbol: str, param_name: str, new_value: Any) -> str:
    """Safely update a parameter in a spell string."""
    ast = parse_spell_ast(spell)
    updated_ast = _update_param_in_ast(ast, symbol, param_name, new_value)
    return ast_to_spell(updated_ast)

def _update_param_in_ast(node: Expr, symbol: str, param_name: str, new_value: Any) -> Expr:
    if isinstance(node, Primitive):
        if node.symbol == symbol:
            new_params = {**node.params, param_name: new_value}
            return Primitive(symbol, new_params)
        else:
            return node
    elif isinstance(node, Combinator):
        new_left = _update_param_in_ast(node.left, symbol, param_name, new_value)
        new_right = _update_param_in_ast(node.right, symbol, param_name, new_value)
        return Combinator(node.op, new_left, new_right)
    else:
        return node
