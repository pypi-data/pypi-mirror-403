"""
ALCHEM-J Operator Registry
Maps symbols → pure JAX functions with uniform signature
Φ(key, x, params) -> new_x
"""
from typing import Callable, Dict, Any
import jax
import jax.numpy as jnp
import jax.random as jr
from functools import partial

PyTree = Any
StepFn = Callable[[jax.Array, PyTree, Dict[str, Any]], PyTree]

# ----- internal table ---------------------------------------------------------
_REGISTRY: Dict[str, StepFn] = {}


# ----- public decorator -------------------------------------------------------
def register(symbol: str):
    """@register('𝕀') def iso_step(key,x,p): ..."""
    if len(symbol) != 1:
        raise ValueError("Symbol must be single Unicode code-point")
    def decorator(fn: StepFn):
        _REGISTRY[symbol] = fn
        return fn
    return decorator


# ----- lookup -----------------------------------------------------------------
def get(symbol: str) -> StepFn:
    if symbol not in _REGISTRY:
        raise KeyError(f"Symbol {symbol} not registered")
    return _REGISTRY[symbol]


# ----- built-ins (loaded automatically) ---------------------------------------
@register("𝕀")
def _iso(key, x, p):
    """Dummy ISO/RIME step: x + ε·N(0,1)"""
    eps = p.get("eps", 0.01)
    return x + eps * jr.normal(key, jax.tree.map(jnp.shape, x))


@register("ℝ")
def _rl(key, x, p):
    """Dummy RL policy update: identity (real impl in plugins.rl)"""
    return x


@register("𝕃")
def _levy(key, x, p):
    """Lévy noise injection (simplified symmetric α-stable)"""
    alpha = p.get("alpha", 1.5)
    scale = p.get("scale", 0.1)
    # α-stable with scale ~ N(0,1) for demo
    noise = jr.normal(key, jax.tree.map(jnp.shape, x))
    return jax.tree.map(lambda n: scale * n * (1 / alpha), noise)


@register("𝕊")
def _svd_proj(key, x, p):
    """Low-rank SVD projection (matrix leaves only)"""
    rank = p.get("rank", min(8, *(x.shape[-2:])))
    U, S, Vt = jnp.linalg.svd(x, full_matrices=False)
    return (U[:, :rank] * S[:rank]) @ Vt[:rank, :]


@register("ℤ")
def _zeta(key, x, p):
    """Zeta-transform placeholder: identity"""
    return x


@register("ℂ")
def _chaos(key, x, p):
    """Logistic chaos map (element-wise)"""
    r = p.get("r", 3.8)
    return jax.tree.map(lambda a: r * a * (1 - a), x)


@register("𝜑")
def _meta(key, x, p):
    """Meta-gradient correction placeholder: identity"""
    return x