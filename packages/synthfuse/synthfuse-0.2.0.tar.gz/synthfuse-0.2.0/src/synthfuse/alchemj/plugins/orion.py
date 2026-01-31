"""
W-Orion Core  –  Weierstrass-transform neural gravity solver
ϕ(tool_i) → Gaussian field → gradient ascent to nearest semantic cluster
"""
import jax
import jax.numpy as jnp
import chex
from typing import Any
from synthfuse.alchemj.registry import register

PyTree = Any


# ------------------------------------------------------------------
# 1.  State container
# ------------------------------------------------------------------
@chex.dataclass
class OrionState:
    embeddings: jax.Array  # [num_tools, dim]  – fixed “stars”
    temperature: float     # σ  (Weierstrass width)
    density: jaxArray      # manifold curvature scalar field (placeholder)


# ------------------------------------------------------------------
# 2.  Registered primitive  𝕎  –  Weierstrass potential field
# ------------------------------------------------------------------
@register("𝕎")
def weierstrass_potential(key: jax.Array, pos: jax.Array, params: dict) -> jax.Array:
    """
    Returns scalar potential  U(x) = Σᵢ exp( -||x - toolᵢ||² / (2σ²) )
    key   – PRNG (unused, but signature compatible)
    pos   – [batch, dim]  query points
    params – {embeddings: [T, D], temperature: float}
    """
    tools = params["embeddings"]
    sigma = params["temperature"]
    # [batch, 1, D] - [1, T, D]  →  [batch, T, D]
    diff = pos[:, None, :] - tools[None, :, :]
    dist_sq = jnp.sum(diff**2, axis=-1)
    thermal_scale = 2.0 * (sigma**2)
    potential = jnp.exp(-dist_sq / thermal_scale)
    return jnp.sum(potential, axis=-1)  # [batch]


# ------------------------------------------------------------------
# 3.  Gradient oracle  (not registered – caller uses jax.grad)
# ------------------------------------------------------------------
def orion_force(pos: jax.Array, state: OrionState) -> jax.Array:
    """
    ∇ₓ U(x)  –  direction of steepest ascent toward tool cluster
    """
    return jax.grad(lambda p: jnp.sum(weierstrass_potential(None, p, {
        "embeddings": state.embeddings,
        "temperature": state.temperature,
    })))(pos)


# ------------------------------------------------------------------
# 4.  Manifold sculpting  (SDCD-style, stub)
# ------------------------------------------------------------------
@register("𝕆𝕊")  # Orion-Sculpt
def orion_sculpt(key: jax.Array, state: OrionState, params: dict) -> OrionState:
    """
    Meta-update manifold curvature based on recent tool successes.
    Placeholder – returns state unchanged.
    """
    # TODO: plug SDCD spell here
    return state


# ------------------------------------------------------------------
# 5.  Public recipe factory  (like any other Synth-Fuse recipe)
# ------------------------------------------------------------------
def make_orion_solver(embedding_dim: int = 512, num_tools: int = 128, temp: float = 1.0):
    """
    Returns (jit_step_fn, init_state) ready for ALCHEM-J pipeline
    step_fn executes  (𝕎 ⊗ 𝕆𝕊)(temperature=τ)  inside a larger spell
    """
    spell = "(𝕎 ⊗ 𝕆𝕊)(temperature={})".format(temp)
    from synthfuse.alchemj import compile_spell
    step_fn = compile_spell(spell)

    key = jax.random.PRNGKey(0)
    init_state = OrionState(
        embeddings=jax.random.normal(key, (num_tools, embedding_dim)),
        temperature=temp,
        density=jnp.zeros(embedding_dim),
    )
    return jax.jit(step_fn), init_state

# --------------------------------
from synthfuse.alchemj.plugins.orion import make_orion_stcl
import jax

embeds = jax.random.normal(jax.random.PRNGKey(0), (128, 64))
z0 = jax.random.normal(jax.random.PRNGKey(1), (64,))

step, state = make_orion_stcl(embeds, z0, beta_init=0.8, sigma_init=1.2)

# fuse inside any spell
big_step = compile_spell("(𝕎 ⊗ 𝕊𝕋 ⊗ ℍ)(beta=0.8, sigma=1.2, iteration=iter)")