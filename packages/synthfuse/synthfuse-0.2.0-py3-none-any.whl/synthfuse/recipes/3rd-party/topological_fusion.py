"""
Topological-Fusion – Topological Data Analysis via PyTorch-Topological + JAX
PyTorch-Topological operators exposed as Synth-Fuse primitives:
𝕋𝕆ℙ𝕆 (persistent homology), ℍ𝙾𝙼𝙾𝕃𝙾𝙶𝕐 (betti curves), ℙ𝙴ℝ𝕊𝕀𝕊𝕋𝔼ℕℂ𝔼 (persistence landscapes)
Original: https://github.com/aidos-lab/pytorch-topological
Converted to single Synth-Fuse spell:
(𝕋𝕆ℙ𝕆 ⊗ ℍ𝙾𝙼𝙾𝕃𝙾𝙶𝕐 ⊗ ℙ𝙴ℝ𝕊𝕀𝕊𝕋𝔼ℕℂ𝔼)(dim=2, max_dim=3, coeff=2, landscape_size=10)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  PyTorch-Topological via PythonCall (zero-copy)
# ----------------------------------------------------------
# pip install pytorch-topological juliacall python-call
try:
    from juliacall import Main as jl
except ImportError as e:
    raise RuntimeError("pip install pytorch-topological juliacall python-call") from e


# ----------------------------------------------------------
# 2.  Registered primitives (JAX-safe wrappers)
# ----------------------------------------------------------
@register("𝕋𝕆ℙ𝕆")
def topological_persistence_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    PyTorch-Topological persistent homology (any complex).
    Params: dim (int), max_dim (int), coeff (int)
    Returns: persistence diagram (JAX array)
    """
    dim = params["dim"]
    max_dim = params["max_dim"]
    coeff = params["coeff"]
    X = params["X"]  # JAX array [n, d] point cloud

    # call PyTorch-Topological via Julia (zero-copy – arrays stay in memory)
    jl.seval("using PyTorchTopological")
    jl.dim = dim
    jl.max_dim = max_dim
    jl.coeff = coeff
    jl.X = X
    jl.seval("""
        using PyTorchTopological: persistence_homology
        diagram = persistence_homology(X, dim=dim, max_dim=max_dim, coeff=coeff)
    """)
    diagram = jl.diagram  # PyTree (JAX array)

    return dict(diagram=diagram, dim=dim, max_dim=max_dim, coeff=coeff)


@register("ℍ𝙾𝙼𝙾𝕃𝙾𝙶𝕐")
def homol_betti_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    PyTorch-Topological betti curves (homology dimensions).
    Params: landscape_size (int)
    Returns: betti curves (JAX array)
    """
    landscape_size = params["landscape_size"]
    diagram = state["diagram"]  # from 𝕋𝕆ℙ𝕆 step

    # call PyTorch-Topological via Julia (zero-copy)
    jl.seval("using PyTorchTopological: betti_curves")
    jl.landscape_size = landscape_size
    jl.diagram = diagram
    jl.seval("""
        using PyTorchTopological: betti_curves
        curves = betti_curves(diagram, landscape_size=landscape_size)
    """)
    curves = jl.curves  # PyTree (JAX array)

    return dict(curves=curves, landscape_size=landscape_size)


@register("ℙ𝙴ℝ𝕊𝕀𝕊𝕋𝔼ℕℂ𝔼")
def persistence_landscape_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    PyTorch-Topological persistence landscapes (smooth representation).
    Params: landscape_size (int)
    Returns: persistence landscapes (JAX array)
    """
    landscape_size = params["landscape_size"]
    diagram = state["diagram"]  # from 𝕋𝕆ℙ𝕆 step

    # call PyTorch-Topological via Julia (zero-copy)
    jl.seval("using PyTorchTopological: persistence_landscapes")
    jl.landscape_size = landscape_size
    jl.diagram = diagram
    jl.seval("""
        using PyTorchTopological: persistence_landscapes
        landscapes = persistence_landscapes(diagram, landscape_size=landscape_size)
    """)
    landscapes = jl.landscapes  # PyTree (JAX array)

    return dict(landscapes=landscapes, landscape_size=landscape_size)


# ----------------------------------------------------------
# 4.  Fused spell
# ----------------------------------------------------------
_SPELL = "(𝕋𝕆ℙ𝕆 ⊗ ℍ𝙾𝙼𝙾𝕃𝙾𝙶𝕐 ⊗ ℙ𝙴ℝ𝕊𝕀𝕊𝕋𝔼ℕℂ𝔼)(dim=2, max_dim=3, coeff=2, landscape_size=10)"


# ----------------------------------------------------------
# 5.  Factory – identical API to fql_rime
# ----------------------------------------------------------
def make_topological(
    X: jax.Array,  # [n, d] – point cloud (injected static)
    dim: int = 2,
    max_dim: int = 3,
    coeff: int = 2,
    landscape_size: int = 10,
):
    spell = "(𝕋𝕆ℙ𝕆 ⊗ ℍ𝙾𝙼𝙾𝕃𝙾𝙶𝕐 ⊗ ℙ𝙴ℝ𝕊𝕀𝕊𝕋𝔼ℕℂ𝔼)(dim={}, max_dim={}, coeff={}, landscape_size={})".format(
        dim, max_dim, coeff, landscape_size
    )
    step_fn = compile_spell(spell)

    # bind static point cloud into params (zero-copy)
    def bound_step(key, state):
        return step_fn(key, state, {
            "X": X,
            "dim": dim,
            "max_dim": max_dim,
            "coeff": coeff,
            "landscape_size": landscape_size,
        })

    # initial state – empty (PyTorch-Topological fills it)
    state = dict(
        X=X,
        dummy=jnp.zeros(1),  # placeholder
    )

    return jax.jit(bound_step), state
