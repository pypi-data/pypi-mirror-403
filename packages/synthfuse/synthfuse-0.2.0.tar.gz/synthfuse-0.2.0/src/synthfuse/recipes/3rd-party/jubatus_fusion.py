"""
Jubatus-Fusion – Online ML via Jubatus + JAX
Jubatus operators exposed as Synth-Fuse primitives:
𝕁𝕌𝔹𝔸𝚃𝚄𝚂 (online model), 𝙺𝙼𝙴𝙰𝙽𝚂 (k-means), 𝙶𝙰𝚄𝚂𝚂 (GMM), 𝚂𝚅𝙼 (online SVM)
Original: https://github.com/jubatus/jubatus
Converted to single Synth-Fuse spell:
(𝕁𝕌𝔹𝔸𝚃𝚄𝚂 ⊗ 𝙺𝙼𝙴𝙰𝙽𝚂 ⊗ 𝙶𝙰𝚄𝚂𝚂 ⊗ 𝚂𝚅𝙼)(model=fv_converter, k=5, comp=3, C=1.0)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  Jubatus via PythonCall (zero-copy)
# ----------------------------------------------------------
# pip install juliacall jubatus python-call
try:
    from juliacall import Main as jl
except ImportError as e:
    raise RuntimeError("pip install juliacall jubatus python-call") from e


# ----------------------------------------------------------
# 2.  Registered primitives (JAX-safe wrappers)
# ----------------------------------------------------------
@register("𝕁𝕌𝔹𝔸𝚃𝚄𝚂")
def jubatus_online_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Jubatus online update (any model via RPC-free Julia wrapper).
    Params: model (str), batch_size (int)
    Returns: updated model state (still PyTree)
    """
    model = params["model"]
    batch_size = params["batch_size"]
    x = params["x"]  # JAX array [batch, d]

    # call Julia (zero-copy – arrays stay in memory)
    jl.seval("using Jubatus")
    jl.model = model
    jl.x = x
    jl.batch_size = batch_size
    jl.seval("""
        using Jubatus: OnlineModel, update!
        model = OnlineModel(Symbol(model))
        for i in 1:batch_size
            update!(model, x[i,:])
        end
        state = get_state(model)
    """)
    state_jl = jl.state  # Julia dict → PyTree

    return dict(model_state=state_jl, batch_size=batch_size)


@register("𝙺𝙼𝙴𝙰𝙽𝚂")
def jubatus_kmeans_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Jubatus online k-means (RPC-free).
    Params: k (int), max_iter (int)
    """
    k = params["k"]
    max_iter = params["max_iter"]
    x = params["x"]  # [n, d]

    jl.seval("using Jubatus: KMeans, update!")
    jl.k = k
    jl.max_iter = max_iter
    jl.x = x
    jl.seval("""
        kmeans = KMeans(k=k)
        for _ in 1:max_iter
            update!(kmeans, x)
        end
        centroids = get_centroids(kmeans)
        labels = assign(kmeans, x)
    """)
    centroids = jl.centroids
    labels = jl.labels

    return dict(centroids=centroids, labels=labels, k=k)


@register("𝙶𝙰𝚄𝚂𝚂")
def jubatus_gmm_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Jubatus online GMM (RPC-free).
    Params: comp (int), tol (float)
    """
    comp = params["comp"]
    tol = params["tol"]
    x = params["x"]  # [n, d]

    jl.seval("using Jubatus: GMM, update!")
    jl.comp = comp
    jl.tol = tol
    jl.x = x
    jl.seval("""
        gmm = GMM(comp=comp, tol=tol)
        for _ in 1:100
            update!(gmm, x)
        end
        weights = get_weights(gmm)
        means = get_means(gmm)
        covs = get_covs(gmm)
    """)
    weights = jl.weights
    means = jl.means
    covs = jl.covs

    return dict(weights=weights, means=means, covs=covs, comp=comp)


@register("𝚂𝚅𝙼")
def jubatus_svm_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Jubatus online SVM (RPC-free).
    Params: C (float), kernel (str)
    """
    C = params["C"]
    kernel = params["kernel"]
    x = params["x"]  # [n, d]
    y = params["y"]  # [n]

    jl.seval("using Jubatus: SVM, update!")
    jl.C = C
    jl.kernel = kernel
    jl.x = x
    jl.y = y
    jl.seval("""
        svm = SVM(C=C, kernel=Symbol(kernel))
        for i in 1:length(y)
            update!(svm, x[i,:], y[i])
        end
        support = get_support(svm)
        dual_coef = get_dual_coef(svm)
    """)
    support = jl.support
    dual_coef = jl.dual_coef

    return dict(support=support, dual_coef=dual_coef, C=C, kernel=kernel)


# ----------------------------------------------------------
# 4.  Fused spell
# ----------------------------------------------------------
_SPELL = "(𝕁𝕌𝔹𝔸𝚃𝚄𝚂 ⊗ 𝙺𝙼𝙴𝙰𝙽𝚂 ⊗ 𝙶𝙰𝚄𝚂𝚂 ⊗ 𝚂𝚅𝙼)(model=fv_converter, k=5, comp=3, C=1.0, kernel=rbf)"


# ----------------------------------------------------------
# 5.  Factory – identical API to fql_rime
# ----------------------------------------------------------
def make_jubatus(
    X: jax.Array,  # [n, d] – training data (injected static)
    y: jax.Array,  # [n]    – target (injected static)
    model: str = "fv_converter",
    k: int = 5,
    comp: int = 3,
    C: float = 1.0,
    kernel: str = "rbf",
    batch_size: int = 32,
):
    spell = "(𝕁𝕌𝔹𝔸𝚃𝚄𝚂 ⊗ 𝙺𝙼𝙴𝙰𝙽𝚂 ⊗ 𝙶𝙰𝚄𝚂𝚂 ⊗ 𝚂𝚅𝙼)(model={}, k={}, comp={}, C={}, kernel={}, batch_size={})".format(
        model, k, comp, C, kernel, batch_size
    )
    step_fn = compile_spell(spell)

    # bind static data into params (zero-copy)
    def bound_step(key, state):
        return step_fn(key, state, {
            "X": X,
            "y": y,
            "model": model,
            "k": k,
            "comp": comp,
            "C": C,
            "kernel": kernel,
            "batch_size": batch_size,
        })

    # initial state – empty (Jubatus fills it)
    state = dict(
        X=X,
        y=y,
        dummy=jnp.zeros(1),  # placeholder
    )

    return jax.jit(bound_step), state
