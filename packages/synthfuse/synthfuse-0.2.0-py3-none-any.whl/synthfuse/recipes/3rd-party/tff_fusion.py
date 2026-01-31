"""
TFF-Fusion – TensorFlow Federated via TFF + JAX
TFF operators exposed as Synth-Fuse primitives:
𝔽𝔼𝔻𝔼ℝ𝔸𝕥𝔼𝔻 (federated compute), 𝔄𝔾𝔾ℝ𝔼𝔾𝔸𝕥𝔼 (aggregation), 𝕌ℙ𝔻𝔸𝕥𝔼 (client update)
Original: https://github.com/google-parfait/tensorflow-federated
Converted to single Synth-Fuse spell:
(𝔽𝔼𝔻𝔼ℝ𝔸𝕥𝔼𝔡 ⊗ 𝔄𝔾𝔾ℝ𝔼𝔾𝔸𝕥𝔼 ⊗ 𝕌ℙ𝔻𝔸𝕥𝔼)(n_clients=10, rounds=50, lr=0.1)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  TFF via PythonCall (zero-copy)
# ----------------------------------------------------------
# pip install tensorflow-federated juliacall python-call
try:
    from juliacall import Main as jl
except ImportError as e:
    raise RuntimeError("pip install tensorflow-federated juliacall python-call") from e


# ----------------------------------------------------------
# 2.  Registered primitives (JAX-safe wrappers)
# ----------------------------------------------------------
@register("𝔽𝔼𝔻𝔼ℝ𝔸𝕥𝔼𝔡")
def tff_federated_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    TFF federated compute (any aggregation strategy).
    Params: n_clients (int), strategy (str)
    Returns: federated state (PyTree)
    """
    n_clients = params["n_clients"]
    strategy = params["strategy"]
    local_models = state["local_models"]  # list of client states (JAX arrays)

    # call TFF via Julia (zero-copy – arrays stay in memory)
    jl.seval("using TensorFlowFederated")
    jl.n_clients = n_clients
    jl.strategy = strategy
    jl.local_models = local_models
    jl.seval("""
        using TensorFlowFederated: federated_computation, aggregate
        fed_state = federated_computation(local_models, strategy=strategy)
        global_model = aggregate(fed_state)
    """)
    global_model = jl.global_model  # PyTree

    return dict(global_model=global_model, n_clients=n_clients, strategy=strategy)


@register("𝔄𝔾𝔾ℝ𝔼𝔾𝔸𝕥𝔼")
def tff_aggregate_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    TFF aggregation (mean, median, secure-sum, etc.).
    Params: agg (str), clip_norm (float)
    Returns: aggregated gradients (PyTree)
    """
    agg = params["agg"]
    clip_norm = params["clip_norm"]
    grads = state["grads"]  # list of client grads (JAX arrays)

    jl.seval("using TensorFlowFederated: aggregate_gradients")
    jl.agg = agg
    jl.clip_norm = clip_norm
    jl.grads = grads
    jl.seval("""
        agg_grads = aggregate_gradients(grads, method=agg, clip_norm=clip_norm)
    """)
    agg_grads = jl.agg_grads  # PyTree

    return dict(agg_grads=agg_grads, agg=agg, clip_norm=clip_norm)


@register("𝕌ℙ𝔻𝔸𝕥𝔼")
def tff_update_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    TFF client update (local SGD).
    Params: lr (float), local_epochs (int)
    Returns: updated local models (PyTree)
    """
    lr = params["lr"]
    local_epochs = params["local_epochs"]
    local_model = state["local_model"]  # single client state
    grads = state["agg_grads"]  # from aggregation step

    # local SGD update (vectorised)
    new_model = local_model - lr * grads
    # simulate local epochs (stub – real TFF does multiple)
    for _ in range(local_epochs):
        new_model = new_model - lr * grads

    return dict(local_model=new_model, lr=lr, local_epochs=local_epochs)


# ----------------------------------------------------------
# 4.  Fused spell
# ----------------------------------------------------------
_SPELL = "(𝔽𝔼𝔻𝔼ℝ𝔸𝕥𝔼𝔡 ⊗ 𝔄𝔾𝔾ℝ𝔼𝔾𝔸𝕥𝔼 ⊗ 𝕌ℙ𝔻𝔸𝕥𝔼)(n_clients=10, rounds=50, lr=0.1, strategy=mean, agg=mean, clip_norm=1.0, local_epochs=1)"


# ----------------------------------------------------------
# 5.  Factory – identical API to fql_rime
# ----------------------------------------------------------
def make_tff(
    n_clients: int = 10,
    rounds: int = 50,
    lr: float = 0.1,
    strategy: str = "mean",
    agg: str = "mean",
    clip_norm: float = 1.0,
    local_epochs: int = 1,
):
    spell = "(𝔽𝔼𝔻𝔼ℝ𝔸𝕥𝔼𝔡 ⊗ 𝔄𝔾𝔾ℝ𝔼𝔾𝔸𝕥𝔼 ⊗ 𝕌ℙ𝔻𝔸𝕥𝔼)(n_clients={}, rounds={}, lr={}, strategy={}, agg={}, clip_norm={}, local_epochs={})".format(
        n_clients, rounds, lr, strategy, agg, clip_norm, local_epochs
    )
    step_fn = compile_spell(spell)

    # build initial client models (random init)
    key = jax.random.PRNGKey(42)
    local_models = [jax.random.normal(key, (10,)) for _ in range(n_clients)]  # stub weights

    state = dict(
        local_models=local_models,
        global_model=jax.random.normal(key, (10,)),  # global init
        round=0,
    )

    # bind static params
    def bound_step(key, state):
        return step_fn(key, state, {
            "n_clients": n_clients,
            "rounds": rounds,
            "lr": lr,
            "strategy": strategy,
            "agg": agg,
            "clip_norm": clip_norm,
            "local_epochs": local_epochs,
        })

    return jax.jit(bound_step), state
