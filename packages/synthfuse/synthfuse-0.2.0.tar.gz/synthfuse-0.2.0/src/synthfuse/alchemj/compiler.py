"""
Spell → AST → JAX callable
"""
from lark import Lark, Transformer, v_args
from pathlib import Path
from typing import Callable, Any
import jax
import jax.numpy as jnp
from .registry import get

PyTree = Any
StepFn = Callable[[jax.Array, PyTree, dict], PyTree]

# ---------- load grammar once -----------------------------------------------
_GRAMMAR = Lark.open(Path(__file__).with_name("grammar.lark"), parser="lalr")


# ---------- AST → JAX transformer -------------------------------------------
@v_args(inline=True)
class _AST2Jax(Transformer):
    def __init__(self):
        self._lambda_counter = 0

    # terminals
    def prim(self, symbol, params):
        op = get(str(symbol))
        # bind params early (static)
        return lambda key, x, _: op(key, x, params)

    def seq(self, left, right):
        return lambda key, x, p: right(key, left(key, x, p), p)

    def par(self, left, right):
        # tree-additive parallel fusion
        return lambda key, x, p: jax.tree.map(
            jnp.add, left(key, x, p), right(key, x, p)
        )

    def guard(self, pred_tree, op):
        # pred_tree is (lambda_expr) or primitive returning bool PyTree
        def fn(key, x, p):
            mask = pred_tree(key, x, p)  # bool or float > 0 → True
            return jax.tree.map(
                lambda o, m: jnp.where(m, o, x), op(key, x, p), mask
            )
        return fn

    def lambda_expr(self, params, body):
        # compile-time lambda: params are names, body is stepfn
        # we simply ignore them for now (full λ-calculus TBD)
        return body

    def paren(self, child):
        return child


# ---------- public API -------------------------------------------------------
def compile_spell(source: str) -> StepFn:
    """source string → JIT-ready StepFn"""
    tree = _GRAMMAR.parse(source)
    stepfn = _AST2Jax().transform(tree)
    return jax.jit(stepfn)


#---------2-----
@v_args(inline=True)
class _AST2Jax(Transformer):
    # ------- existing prim / seq / par / guard / paren kept as-is -------

    # ------- containers -----------------------------------------------
    def dict(self, *keyvals):
        return dict(keyvals)

    def keyval(self, key, value):
        # key arrives as a token (string literal) – strip quotes
        return str(key).strip('"'), value

    def list(self, *items):
        return list(items)

    def params(self, arg_list):
        return arg_list or {}

    def no_params(self):
        return {}

    def arg_list(self, *args):
        return dict(args)

    def arg(self, name, value):
        return str(name), value

    # ------- terminals -------------------------------------------------
    def NUMBER(self, tok):
        # Lark gives str – cast to Python number
        try:
            return int(tok)
        except ValueError:
            return float(tok)

    def STRING(self, tok):
        return str(tok).strip('"')

    def BOOLEAN(self, tok):
        return tok.lower() == "true"

    def NAME(self, tok):
        return str(tok)