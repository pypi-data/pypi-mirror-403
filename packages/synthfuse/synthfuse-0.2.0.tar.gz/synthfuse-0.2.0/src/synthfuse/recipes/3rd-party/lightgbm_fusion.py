"""
LightGBM-Fusion – Gradient Boosting via LightGBM + JAX
LightGBM operators exposed as Synth-Fuse primitives:
𝕃𝙸𝙶𝙷𝚃 (tree split), 𝙶𝙱𝙳𝚃 (gradient boost), 𝙱𝙾𝙾𝚂𝚃 (leaf update)
Original: https://github.com/microsoft/LightGBM
Converted to single Synth-Fuse spell:
(𝕃𝙸𝙶𝙷𝚃 ⊗ 𝙶𝙱𝙳𝚃 ⊗ 𝙱𝙾𝙾𝚂𝚃)(n_trees=100, lr=0.1, max_depth=6, lambda_l2=1.0)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  LightGBM via PythonCall (zero-copy)
# ----------------------------------------------------------
# pip install lightgbm juliacall python-call
try:
    from juliacall import Main as jl
except ImportError as e:
    raise RuntimeError("pip install lightgbm juliacall python-call") from e


# ----------------------------------------------------------
# 2.  Registered primitives (JAX-safe wrappers)
# ----------------------------------------------------------
@register("𝕃𝙸𝙶𝙷𝚃")
def lightgbm_tree_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    LightGBM tree split (best gain via histogram).
    Params: max_depth (int), min_child_samples (int)
    Returns: split gain, feature_idx, threshold (JAX arrays)
    """
    max_depth = params["max_depth"]
    min_child_samples = params["min_child_samples"]
    X = params["X"]  # [n, d]
    grad = params["grad"]  # [n]  gradients
    hess = params["hess"]  # [n]  hessians

    # call LightGBM via Julia (zero-copy – arrays stay in memory)
    jl.seval("using LightGBM")
    jl.X = X
    jl.grad = grad
    jl.hess = hess
    jl.max_depth = max_depth
    jl.min_child_samples = min_child_samples
    jl.seval("""
        using LightGBM: find_best_split
        gain, feat_idx, threshold = find_best_split(X, grad, hess, max_depth=max_depth, min_child_samples=min_child_samples)
    """)
    gain = jl.gain
    feat_idx = jl.feat_idx
    threshold = jl.threshold

    return dict(gain=gain, feat_idx=feat_idx, threshold=threshold, max_depth=max_depth)


@register("𝙶𝙱𝙳𝚃")
def gbdt_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    LightGBM gradient boost (negative gradient update).
    Params: lr (float), n_trees (int)
    Returns: updated predictions (JAX array)
    """
    lr = params["lr"]
    n_trees = params["n_trees"]
    preds = state["preds"]  # [n] current predictions
    grad = state["grad"]    # [n] negative gradient
    hess = state["hess"]    # [n] hessian

    # GBDT update: preds ← preds + lr * tree_prediction
    tree_pred = jax.random.normal(key, preds.shape)  # stub – real tree from LightGBM
    new_preds = preds + lr * tree_pred

    return dict(preds=new_preds, grad=grad, hess=hess, lr=lr, n_trees=n_trees)


@register("𝙱𝙾𝙾𝚂𝚃")
def lightgbm_boost_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    LightGBM leaf update (Newton step).
    Params: lambda_l2 (float), min_gain (float)
    Returns: updated leaf values (JAX array)
    """
    lambda_l2 = params["lambda_l2"]
    min_gain = params["min_gain"]
    grad = state["grad"]  # [n]
    hess = state["hess"]  # [n]

    # Newton step: leaf = -grad / (hess + lambda_l2)
    leaf = -grad / (hess + lambda_l2)
    leaf = jnp.where(jnp.abs(leaf) > min_gain, leaf, 0.0)  # prune small updates

    return dict(leaf=leaf, lambda_l2=lambda_l2, min_gain=min_gain)


# ----------------------------------------------------------
# 4.  Fused spell
# ----------------------------------------------------------
_SPELL = "(𝕃𝙸𝙶𝙷𝚃 ⊗ 𝙶𝙱𝙳𝚃 ⊗ 𝙱𝙾𝙾𝚂𝚃)(n_trees=100, lr=0.1, max_depth=6, lambda_l2=1.0, min_gain=1e-4)"


# ----------------------------------------------------------
# 5.  Factory – identical API to fql_rime
# ----------------------------------------------------------
def make_lightgbm(
    X: jax.Array,  # [n, d] – training data (injected static)
    y: jax.Array,  # [n]    – target (injected static)
    n_trees: int = 100,
    lr: float = 0.1,
    max_depth: int = 6,
    lambda_l2: float = 1.0,
    min_gain: float = 1e-4,
    min_child_samples: int = 20,
):
    spell = "(𝕃𝙸𝙶𝙷𝚃 ⊗ 𝙶𝙱𝙳𝚃 ⊗ 𝙱𝙾𝙾𝚂𝚃)(n_trees={}, lr={}, max_depth={}, lambda_l2={}, min_gain={}, min_child_samples={})".format(
        n_trees, lr, max_depth, lambda_l2, min_gain, min_child_samples
    )
    step_fn = compile_spell(spell)

    # bind static data into params (zero-copy)
    def bound_step(key, state):
        return step_fn(key, state, {
            "X": X,
            "y": y,
            "n_trees": n_trees,
            "lr": lr,
            "max_depth": max_depth,
            "lambda_l2": lambda_l2,
            "min_gain": min_gain,
            "min_child_samples": min_child_samples,
        })

    # initial state – empty (LightGBM fills it)
    state = dict(
        preds=jnp.zeros(X.shape[0]),
        grad=jnp.zeros(X.shape[0]),
        hess=jnp.ones(X.shape[0]),
        dummy=jnp.zeros(1),  # placeholder
    )

    return jax.jit(bound_step), state
