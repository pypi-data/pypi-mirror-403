"""
KNN-Boosted Random Forest  (Architecture II)
𝕂𝔹ℝ𝔽 – HNSW + proximity-weighted boosting + cache-aware GEMM
"""
import jax
import jax.numpy as jnp
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

@register("𝕂𝔹ℝ𝔽")
def knn_boost_rf_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    HNSW retrieval → proximity weights → GEMM booster update.
    Params: k_max (int), hnsw_M (int), gemm_block (int)
    """
    k_max = params["k_max"]
    M = params["hnsw_M"]
    block = params["gemm_block"]

    # 1. HNSW retrieval (stub – returns k indices + distances)
    indices, dists = params["hnsw_index"].query(state.x, k=k_max)

    # 2. proximity weights (softmax over negative distances)
    weights = jax.nn.softmax(-dists / params.get("temp", 0.5))  # [k]

    # 3. GEMM booster (cache-aligned block matmul)
    X = params["X"][indices]  # [k, d]
    y = params["y"][indices]  # [k]
    # blocked GEMM update
    def gemm_update(w, x, y):
        return w * jnp.outer(y, x)  # rank-1 update
    delta = jax.vmap(gemm_update)(weights, X, y)
    # accumulate in blocks
    new_coefs = state.coef + jnp.sum(delta.reshape(-1, block, delta.shape[-1]), axis=0)

    return state.replace(coef=new_coefs)


def make_knn_boost_rf(k_max: int = 32, hnsw_M: int = 16, gemm_block: int = 64):
    spell = "(𝕂𝔹ℝ𝔽)(k_max={}, hnsw_M={}, gemm_block={})".format(k_max, hnsw_M, gemm_block)
    step_fn = compile_spell(spell)

    state = dict(
        coef=jnp.zeros(128),  # stub coef vector
        x=jnp.zeros(128),     # current sample
    )
    return jax.jit(step_fn), state
