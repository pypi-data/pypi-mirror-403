"""
Semantic-Thermodynamic Compression Loop (STCL)
Minimises free-energy  ℱ = Λ - β·C   where
  Λ = semantic information content  (I_concept - I_surface)
  C = compressed bit-cost
Loop self-stabilises by alternating:
  1. semantic-field update  (increases Λ)
  2. thermodynamic cooling   (decreases C)
  3. free-energy descent     (gradient on manifold)
"""
import jax
import jax.numpy as jnp
import chex
from typing import Any
from synthfuse.alchemj import compile_spell

PyTree = Any


# ------------------------------------------------------------------
# 1.  State container
# ------------------------------------------------------------------
@chex.dataclass
class STCLState:
    representation: PyTree     # current latent code  z
    surface_bits: jax.Array    # bit-count of z
    concept_energy: jax.Array  # Λ(z)
    temperature: float         # β = 1/T
    clock: int


# ------------------------------------------------------------------
# 2.  Semantic field  Λ(z)  (stub: cosine distance to anchor)
# ------------------------------------------------------------------
def semantic_field(z: PyTree, anchor: PyTree) -> float:
    """
    Λ(z) = 1 - cos(z, anchor)   (higher → more concept info)
    """
    flat_z, _ = jax.flatten_util.ravel_pytree(z)
    flat_a, _ = jax.flatten_util.ravel_pytree(anchor)
    cos = jnp.dot(flat_z, flat_a) / (
        jnp.linalg.norm(flat_z) * jnp.linalg.norm(flat_a) + 1e-8
    )
    return 1.0 - cos


# ------------------------------------------------------------------
# 3.  Compression cost  C(z)  (bits)
# ------------------------------------------------------------------
def compression_cost(z: PyTree, quant: float = 1e-3) -> int:
    """
    Simple zero-run-length + quantisation estimate
    Returns bit count (int)
    """
    flat, _ = jax.flatten_util.ravel_pytree(z)
    q = jnp.round(flat / quant)
    # zero-run-length
    zeros = q == 0
    runs = jnp.split(zeros, jnp.where(zeros[:-1] != zeros[1:])[0] + 1)
    run_bits = sum(r.size * (1 + jnp.ceil(jnp.log2(r.size + 1))) for r in runs)
    non_zero_bits = jnp.sum(q != 0) * 16  # 16-bit per non-zero
    return int(run_bits + non_zero_bits)


# ------------------------------------------------------------------
# 4.  Thermodynamic cooling  (quench)
# ------------------------------------------------------------------
def thermodynamic_cool(z: PyTree, cool_rate: float = 0.99) -> PyTree:
    """
    Multiplicative cooling:  z ← z * cool_rate  (manifold preserving)
    """
    return tree_map(lambda a: a * cool_rate, z)


# ------------------------------------------------------------------
# 5.  Free-energy manifold gradient
# ------------------------------------------------------------------
def free_energy_grad(z: PyTree, anchor: PyTree, beta: float, quant: float) -> PyTree:
    """
    ∇_z ℱ = ∇_z Λ - β ∇_z C
    """
    # ∇Λ
    grad_lambda = jax.grad(lambda z: semantic_field(z, anchor))(z)
    # ∇C  (finite-diff)
    eps = 1e-4
    grad_c = jax.tree.map(
        lambda a: (compression_cost(tree_map(lambda v: v + eps, z), quant) -
                   compression_cost(tree_map(lambda v: v - eps, z), quant)) / (2 * eps),
        z,
    )
    # combine
    return jax.tree.map(lambda gl, gc: gl - beta * gc, grad_lambda, grad_c)


# ------------------------------------------------------------------
# 6.  Single STCL step (ready for JIT)
# ------------------------------------------------------------------
@jax.jit
def stcl_step(key: jax.Array, state: STCLState, params: dict) -> STCLState:
    """
    Params: anchor (PyTree), lr, cool_rate, quant
    """
    anchor = params["anchor"]
    lr = params.get("lr", 0.01)
    cool_rate = params.get("cool_rate", 0.99)
    quant = params.get("quant", 1e-3)

    # 1. semantic field update (gradient ascent on Λ)
    grad_f = free_energy_grad(state.representation, anchor, state.temperature, quant)
    new_z = jax.tree.map(lambda z, g: z + lr * g, state.representation, grad_f)

    # 2. thermodynamic cooling (reduce C)
    new_z = thermodynamic_cool(new_z, cool_rate)

    # 3. recompute observables
    new_lambda = semantic_field(new_z, anchor)
    new_bits = compression_cost(new_z, quant)
    new_free_energy = new_lambda - state.temperature * new_bits

    return STCLState(
        representation=new_z,
        surface_bits=new_bits,
        concept_energy=new_lambda,
        temperature=state.temperature,
        clock=state.clock + 1,
    )


# ------------------------------------------------------------------
# 7.  Public factory
# ------------------------------------------------------------------
def make_stcl(anchor: PyTree, z_init: PyTree, temp: float = 1.0) -> tuple[Callable, STCLState]:
    """
    Returns (jit_step, init_state) ready for Synth-Fuse pipeline
    """
    init_state = STCLState(
        representation=z_init,
        surface_bits=compression_cost(z_init),
        concept_energy=semantic_field(z_init, anchor),
        temperature=temp,
        clock=0,
    )
    return stcl_step, init_state