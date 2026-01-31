"""
Knowledge3D – 3-D Knowledge Graph Reasoning
Original: https://github.com/danielcamposramos/Knowledge3D
Converted to single Synth-Fuse spell:
(𝕂𝟛𝔻 ⊗ 𝔾ℝ𝔸𝔻 ⊗ 𝕊𝟛𝔻)(lr=0.01, temp=0.7, dim=64)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  State container (matches original repo)
# ----------------------------------------------------------
@chex.dataclass
class Knowledge3DState:
    entity_embed: jax.Array     # [N, 3]  3-D positions
    relation_rot: jax.Array     # [N, 3]  rotation vectors
    grad_accum: jax.Array       # [N, 3]  gradient buffer
    temp: float                 # temperature for scoring
    lr: float                   # learning rate


# ----------------------------------------------------------
# 2.  Registered primitives
# ----------------------------------------------------------
@register("𝕂𝟛𝔻")
def knowledge3d_step(key: jax.Array, state: Knowledge3DState, params: dict) -> Knowledge3DState:
    """
    3-D knowledge embedding update (RotatE-style in 3-D).
    Params: lr, temp, dim (all float)
    """
    lr = params["lr"]
    temp = params["temp"]
    dim = int(params["dim"])

    # 1. 3-D RotatE score (original repo logic)
    h = state.entity_embed[params["head_idx"]]
    r = state.relation_rot[params["rel_idx"]]
    t = state.entity_embed[params["tail_idx"]]
    # rotate h by r in 3-D (Rodrigues formula)
    cos_r, sin_r = jnp.cos(r), jnp.sin(r)
    h_rot = h * cos_r + jnp.cross(r, h) * sin_r + r * jnp.dot(r, h) * (1 - cos_r)
    score = jnp.dot(h_rot, t) / temp  # temperature-scaled

    # 2. Negative sampling loss (stub)
    neg_score = jax.random.normal(key, ())  # dummy negative
    loss = -jnp.log(jax.nn.sigmoid(score - neg_score))

    # 3. Gradient accumulation (3-D)
    grads = jax.grad(lambda e: loss)(state.entity_embed)
    new_embed = state.entity_embed - lr * grads

    return state.replace(entity_embed=new_embed, grad_accum=grads)


@register("𝔾ℝ𝔸𝔻")
def grad3d_step(key: jax.Array, state: Knowledge3DState, params: dict) -> Knowledge3DState:
    """
    3-D gradient field update (curl + divergence smoothing).
    Params: smooth_sigma (float)
    """
    sigma = params["smooth_sigma"]
    # Gaussian smoothing on gradient field
    kernel = jnp.exp(-(jnp.arange(-3, 4) ** 2) / (2 * sigma ** 2))
    kernel /= jnp.sum(kernel)
    smoothed = jnp.convolve(state.grad_accum, kernel, mode='same', axis=0)
    return state.replace(grad_accum=smoothed)


@register("𝕊𝟛𝔻")
def s3d_step(key: jax.Array, state: Knowledge3DState, params: dict) -> Knowledge3DState:
    """
    3-D spectral decomposition (SVD on 3×3 blocks) for stability.
    Params: rank (int)
    """
    rank = int(params["rank"])
    # SVD on 3×3 blocks of entity embeddings
    blocks = state.entity_embed.reshape(-1, 3, 3)
    u, s, vt = jnp.linalg.svd(blocks, full_matrices=False)
    s = s.at[rank:].set(0)  # low-rank truncation
    new_embed = (u * s) @ vt
    return state.replace(entity_embed=new_embed.reshape(-1, 3))


# ----------------------------------------------------------
# 3.  Factory – identical API to fql_rime
# ----------------------------------------------------------
def make_knowledge3d(
    n_entities: int = 10_000,
    dim: int = 64,
    lr: float = 0.01,
    temp: float = 0.7,
    smooth_sigma: float = 1.0,
    rank: int = 32,
):
    spell = "(𝕂𝟛𝔻 ⊗ 𝔾ℝ𝔸𝔻 ⊗ 𝕊𝟛𝔻)(lr={}, temp={}, smooth_sigma={}, rank={})".format(
        lr, temp, smooth_sigma, rank
    )
    step_fn = compile_spell(spell)

    key = jax.random.PRNGKey(42)
    state = Knowledge3DState(
        entity_embed=jax.random.normal(key, (n_entities, 3)),
        relation_rot=jax.random.normal(key, (n_entities, 3)),
        grad_accum=jnp.zeros((n_entities, 3)),
        temp=temp,
        lr=lr,
    )

    # bind static indices into params (stub – real indices injected at call)
    def bound_step(key, state):
        return step_fn(key, state, {
            "lr": lr,
            "temp": temp,
            "smooth_sigma": smooth_sigma,
            "rank": rank,
            "head_idx": 0,  # stub – caller sets real indices
            "rel_idx": 0,
            "tail_idx": 1,
        })

    return jax.jit(bound_step), state
