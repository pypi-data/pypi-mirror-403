"""
FATE-Fusion – Federated AI via FATE + JAX
FATE operators exposed as Synth-Fuse primitives:
𝔽𝔸𝕋𝔼 (federated learning), 𝔽𝔼𝔻𝔼ℝ𝔸𝕥𝔼𝔡 (secure aggregation), 𝕊𝔼ℂ𝕌ℝ𝔼 (homomorphic encryption)
Original: https://github.com/FederatedAI/FATE
Converted to single Synth-Fuse spell:
(𝔽𝔸𝕋𝔼 ⊗ 𝔽𝔼𝔻𝔼ℝ𝔸𝕥𝔼𝔡 ⊗ 𝕊𝔼ℂ𝕌ℝ𝔼)(n_clients=10, rounds=50, lr=0.1, secure=True)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  FATE via PythonCall (zero-copy)
# ----------------------------------------------------------
# pip install fate-client juliacall python-call
try:
    from juliacall import Main as jl
except ImportError as e:
    raise RuntimeError("pip install fate-client juliacall python-call") from e


# ----------------------------------------------------------
# 2.  Registered primitives (JAX-safe wrappers)
# ----------------------------------------------------------
@register("𝔽𝔸𝕋𝔼")
def fate_federated_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    FATE federated learning (any algorithm).
    Params: n_clients (int), rounds (int), lr (float)
    Returns: federated state (PyTree)
    """
    n_clients = params["n_clients"]
    rounds = params["rounds"]
    lr = params["lr"]
    local_models = state["local_models"]  # list of client states (JAX arrays)

    # call FATE via Julia (zero-copy – arrays stay in memory)
    jl.seval("using FATE")
    jl.n_clients = n_clients
    jl.rounds = rounds
    jl.lr = lr
    jl.local_models = local_models
    jl.seval("""
        using FATE: federated_learning, secure_aggregation
        fed_state = federated_learning(local_models, rounds=rounds, lr=lr)
        global_model = secure_aggregation(fed_state)
    """)
    global_model = jl.global_model  # PyTree

    return dict(global_model=global_model, n_clients=n_clients, rounds=rounds, lr=lr)


@register("𝔽𝔼𝔻𝔼ℝ𝔸𝕥𝔼𝔡")
def fate_secure_agg_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    FATE secure aggregation (Paillier/SPDZ).
    Params: secure (bool), clip_norm (float)
    Returns: aggregated gradients (PyTree)
    """
    secure = params["secure"]
    clip_norm = params["clip_norm"]
    grads = state["grads"]  # list of client grads (JAX arrays)

    jl.seval("using FATE: secure_aggregation")
    jl.secure = secure
    jl.clip_norm = clip_norm
    jl.grads = grads
    jl.seval("""
        agg_grads = secure_aggregation(grads, secure=secure, clip_norm=clip_norm)
    """)
    agg_grads = jl.agg_grads  # PyTree

    return dict(agg_grads=agg_grads, secure=secure, clip_norm=clip_norm)


@register("𝕊𝔼ℂ𝕌ℝ𝔼")
def fate_secure_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    FATE homomorphic encryption (Paillier/SPDZ).
    Params: encrypt (bool), key_size (int)
    Returns: encrypted state (PyTree)
    """
    encrypt = params["encrypt"]
    key_size = params["key_size"]
    plaintext = state["plaintext"]  # JAX array

    jl.seval("using FATE: homomorphic_encrypt")
    jl.encrypt = encrypt
    jl.key_size = key_size
    jl.plaintext = plaintext
    jl.seval("""
        ciphertext = homomorphic_encrypt(plaintext, encrypt=encrypt, key_size=key_size)
    """)
    ciphertext = jl.ciphertext  # PyTree

    return dict(ciphertext=ciphertext, encrypt=encrypt, key_size=key_size)


# ----------------------------------------------------------
# 4.  Fused spell
# ----------------------------------------------------------
_SPELL = "(𝔽𝔸𝕋𝔼 ⊗ 𝔽𝔼𝔻𝔼ℝ𝔸𝕥𝔼𝔡 ⊗ 𝕊𝔼ℂ𝕌ℝ𝔼)(n_clients=10, rounds=50, lr=0.1, secure=True, clip_norm=1.0, encrypt=True, key_size=2048)"


# ----------------------------------------------------------
# 5.  Factory – identical API to fql_rime
# ----------------------------------------------------------
def make_fate(
    n_clients: int = 10,
    rounds: int = 50,
    lr: float = 0.1,
    secure: bool = True,
    clip_norm: float = 1.0,
    encrypt: bool = True,
    key_size: int = 2048,
):
    spell = "(𝔽𝔸𝕋𝔼 ⊗ 𝔽𝔼𝔻𝔼ℝ𝔸𝕥𝔼𝔡 ⊗ 𝕊𝔼ℂ𝕌ℝ𝔼)(n_clients={}, rounds={}, lr={}, secure={}, clip_norm={}, encrypt={}, key_size={})".format(
        n_clients, rounds, lr, secure, clip_norm, encrypt, key_size
    )
    step_fn = compile_spell(spell)

    # build initial client models (random init)
    key = jax.random.PRNGKey(42)
    local_models = [jax.random.normal(key, (10,)) for _ in range(n_clients)]  # stub weights

    state = dict(
        local_models=local_models,
        global_model=jax.random.normal(key, (10,)),  # global init
        plaintext=jax.random.normal(key, (10,)),  # dummy plaintext
        round=0,
    )

    # bind static params
    def bound_step(key, state):
        return step_fn(key, state, {
            "n_clients": n_clients,
            "rounds": rounds,
            "lr": lr,
            "secure": secure,
            "clip_norm": clip_norm,
            "encrypt": encrypt,
            "key_size": key_size,
        })

    return jax.jit(bound_step), state
