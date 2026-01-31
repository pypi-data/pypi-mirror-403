"""
RFLF – Recursive Free-Energy/Latent Flow
Original: https://github.com/deskiziarecords/RFLF
Converted to a single Synth-Fuse spell:
(𝕣𝕗𝕝𝕗 ⊗ 𝕎 ⊗ 𝕊𝕋)(beta=0.7, sigma=1.2, rank=32)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  State container (matches original RFLF)
# ----------------------------------------------------------
@chex.dataclass
class RFLFState:
    latent: jax.Array        # [batch, d]  latent flow vector
    free_energy: float       # ℱ = Λ − β·C
    beta: float              # inverse temperature
    sigma: float             # Weierstrass width
    clock: int


# ----------------------------------------------------------
# 2.  Registered primitive  𝕣𝕗𝕝𝕗  (RFLF core step)
# ----------------------------------------------------------
@register("𝕣𝕗𝕝𝕗")
def rflf_step(key: jax.Array, state: RFLFState, params: dict) -> RFLFState:
    """
    Recursive Free-Energy/Latent Flow update.
    Params: beta, sigma, rank (all float)
    """
    beta = params["beta"]
    sigma = params["sigma"]
    rank = int(params["rank"])

    # 1.  Chebyshev latent flow (original RFLF basis)
    x = state.latent
    cheb = jax.scipy.special.eval_chebyt(jnp.arange(rank), x)  # [rank, batch]

    # 2.  SVD low-rank projection (stability)
    u, s, vt = jnp.linalg.svd(cheb, full_matrices=False)
    s = s.at[rank:].set(0)
    latent_new = (u * s) @ vt  # [batch, d]

    # 3.  Free-energy = Λ − β·C
    Λ = jnp.sum(jnp.abs(latent_new))            # semantic load
    C = jnp.sum(jnp.log(1.0 + latent_new**2))   # compression surrogate
    free_energy_new = Λ - beta * C

    # 4.  Weierstrass smoothing (external field injection)
    #    (assumes params["orion_field"] exists – injected at build)
    field = params["orion_field"]
    smooth_latent = latent_new + jax.random.normal(key, latent_new.shape) * sigma

    return RFLFState(
        latent=smooth_latent,
        free_energy=free_energy_new,
        beta=beta,
        sigma=sigma,
        clock=state.clock + 1,
    )


# ----------------------------------------------------------
# 3.  Factory – identical API to fql_rime
# ----------------------------------------------------------
def make_rflf(
    embedding_dim: int = 512,
    beta_init: float = 0.7,
    sigma_init: float = 1.2,
    rank: int = 32,
):
    """
    Returns (jit_step_fn, init_state) ready for Synth-Fuse pipeline.
    External Orion field is injected as static param.
    """
    spell = "(𝕣𝕗𝕝𝕗 ⊗ 𝕎 ⊗ 𝕊𝕋)(beta={}, sigma={}, rank={})".format(beta_init, sigma_init, rank)
    step_fn = compile_spell(spell)

    # build Orion field (static – same shape as latent)
    key = jax.random.PRNGKey(42)
    orion_field = jax.random.normal(key, (embedding_dim,))

    state = RFLFState(
        latent=jax.random.normal(key, (embedding_dim,)),
        free_energy=0.0,
        beta=beta_init,
        sigma=sigma_init,
        clock=0,
    )

    # bind external field into params (static)
    def bound_step(key, state):
        return step_fn(key, state, {
            "orion_field": orion_field,
            "beta": beta_init,
            "sigma": sigma_init,
            "rank": rank,
        })

    return jax.jit(bound_step), state
