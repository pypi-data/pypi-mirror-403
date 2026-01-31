"""
Linfa-Fusion – Classical ML via Rust + JAX
Rust-Linfa operators exposed as Synth-Fuse primitives:
𝕃𝕀ℕ𝔽𝔸 (SVM), 𝕂𝕄𝔼𝔸ℕ𝕊 (k-means), 𝔾𝔸𝕌𝕊𝕊 (GMM)
Original: https://crates.io/crates/linfa/0.8.1
Converted to single Synth-Fuse spell:
(𝕃𝕀ℕ𝔽𝔸 ⊗ 𝕂𝕄𝔼𝔸ℕ𝕊 ⊗ 𝔾𝔸𝕌𝕊𝕊)(kernel=rbf, k=5, n_comp=3)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  Rust-Linfa bindings via PyO3 (zero-copy)
# ----------------------------------------------------------
# pip install linfa-py  (our thin PyO3 wheel)
try:
    import linfa_py  # Rust module
except ImportError as e:
    raise RuntimeError("pip install linfa-py>=0.8.1") from e


# ----------------------------------------------------------
# 2.  Registered primitives (JAX-safe wrappers)
# ----------------------------------------------------------
@register("𝕃𝕀ℕ𝔽𝔸")
def linfa_svm_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Rust-Linfa SVM dual update (RBF kernel).
    Params: kernel (str), C (float), eps (float)
    Returns: updated support vectors & dual coefs (still PyTree)
    """
    kernel = params["kernel"]
    C = params["C"]
    eps = params["eps"]

    # call Rust (zero-copy – inputs/outputs are JAX arrays)
    X = params["X"]  # [n, d]
    y = params["y"]  # [n]
    dual_coef, support_mask = linfa_py.svm_fit(X, y, kernel=kernel, C=C, eps=eps)

    # repack into PyTree (still JIT-traceable)
    return dict(dual_coef=dual_coef, support_mask=support_mask)


@register("𝕂𝕄𝔼𝔸ℕ𝕊")
def linfa_kmeans_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Rust-Linfa k-means (Lloyd + k-means++ init).
    Params: k (int), max_iter (int)
    """
    k = params["k"]
    max_iter = params["max_iter"]
    X = params["X"]  # [n, d]

    centroids, labels = linfa_py.kmeans_fit(X, k=k, max_iter=max_iter, seed=int(key[0]))
    return dict(centroids=centroids, labels=labels)


@register("𝔾𝔸𝕌𝕊𝕊")
def linfa_gmm_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Rust-Linfa Gaussian Mixture (EM, full cov).
    Params: n_comp (int), tol (float)
    """
    n_comp = params["n_comp"]
    tol = params["tol"]
    X = params["X"]  # [n, d]

    weights, means, covs = linfa_py.gmm_fit(X, n_components=n_comp, tol=tol)
    return dict(weights=weights, means=means, covs=covs)


# ----------------------------------------------------------
# 3.  Fused spell
# ----------------------------------------------------------
_SPELL = "(𝕃𝕀ℕ𝔽𝔸 ⊗ 𝕂𝕄𝔼𝔸ℕ𝕊 ⊗ 𝔾𝔸𝕌𝕊𝕊)(kernel=rbf, k=5, n_comp=3, C=1.0, eps=1e-3, max_iter=100, tol=1e-4)"


# ----------------------------------------------------------
# 4.  Factory – identical API to fql_rime
# ----------------------------------------------------------
def make_linfa(
    X: jax.Array,  # [n, d] – training data (injected static)
    y: jax.Array,  # [n]    – labels (injected static)
    kernel: str = "rbf",
    C: float = 1.0,
    eps: float = 1e-3,
    k: int = 5,
    max_iter: int = 100,
    n_comp: int = 3,
    tol: float = 1e-4,
):
    spell = "(𝕃𝕀ℕ𝔽𝔸 ⊗ 𝕂𝕄𝔼𝔸ℕ𝕊 ⊗ 𝔾𝔸𝕌𝕊𝕊)(kernel={}, C={}, eps={}, k={}, max_iter={}, n_comp={}, tol={})".format(
        kernel, C, eps, k, max_iter, n_comp, tol
    )
    step_fn = compile_spell(spell)

    # bind static data into params (zero-copy)
    def bound_step(key, state):
        return step_fn(key, state, {
            "X": X,
            "y": y,
            "kernel": kernel,
            "C": C,
            "eps": eps,
            "k": k,
            "max_iter": max_iter,
            "n_comp": n_comp,
            "tol": tol,
        })

    # initial state – empty (Rust fills it)
    state = dict(
        X=X,
        y=y,
        dummy=jnp.zeros(1),  # placeholder
    )

    return jax.jit(bound_step), state
