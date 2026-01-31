"""
Shimmy-Fusion – Gym → JAX Bridge via Shimmy + Zero-Copy
Shimmy operators exposed as Synth-Fuse primitives:
𝚂𝙷𝙸𝙼𝙼𝚈 (wrapper), 𝙴𝙽𝚅 (vectorised env), 𝚆𝚁𝙰𝙿 (Gym→JAX bridge)
Original: https://github.com/deskiziarecords/shimmy
Converted to single Synth-Fuse spell:
(𝚂𝙷𝙸𝙼𝙼𝚈 ⊗ 𝙴𝙽𝚅 ⊗ 𝚆𝚁𝙰𝙿)(env=CartPole-v1, vectorise=True, zero_copy=True)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  Shimmy via PythonCall (zero-copy)
# ----------------------------------------------------------
# pip install shimmy juliacall python-call
try:
    from juliacall import Main as jl
except ImportError as e:
    raise RuntimeError("pip install shimmy juliacall python-call") from e


# ----------------------------------------------------------
# 2.  Registered primitives (JAX-safe wrappers)
# ----------------------------------------------------------
@register("𝚂𝙷𝙸𝙼𝙼𝚈")
def shimmy_wrap_step(key, state, params):
    """
    Shimmy wrapper (any Gym env → zero-copy JAX).
    Params: env_id (str), vectorise (bool)
    Returns: vectorised env handle (PyTree)
    """
    env_id = params["env_id"]
    vectorise = params["vectorise"]
    jl.seval("using Shimmy")
    jl.env_id = env_id
    jl.vectorise = vectorise
    jl.seval("""
        using Shimmy: wrap_env, vectorise_env
        env = wrap_env(env_id)
        vec_env = vectorise ? vectorise_env(env) : env
    """)
    vec_env = jl.vec_env  # PyTree (JAX array)

    return dict(vec_env=vec_env, env_id=env_id, vectorise=vectorise)


@register("𝙴𝙽𝚅")
def env_vectorised_step(key, state, params):
    """
    Vectorised environment step (batched).
    Params: actions (JAX array)
    Returns: obs, reward, done, info (JAX arrays)
    """
    actions = params["actions"]  # JAX array [batch, act_dim]
    vec_env = state["vec_env"]  # from 𝚂𝙷𝙸𝙼𝙼𝚈 step

    # call Shimmy via Julia (zero-copy)
    jl.seval("using Shimmy: step!")
    jl.actions = actions
    jl.vec_env = vec_env
    jl.seval("""
        using Shimmy: step!
        obs, reward, done, info = step!(vec_env, actions)
    """)
    obs = jl.obs
    reward = jl.reward
    done = jl.done
    info = jl.info  # PyTree (JAX arrays)

    return dict(obs=obs, reward=reward, done=done, info=info, actions=actions)


@register("𝚆𝚁𝙰𝙿")
def shimmy_wrap_step(key, state, params):
    """
    Shimmy wrap (Gym → JAX zero-copy bridge).
    Params: zero_copy (bool), buffer_size (int)
    Returns: zero-copy buffer (JAX array)
    """
    zero_copy = params["zero_copy"]
    buffer_size = params["buffer_size"]
    buffer = state["buffer"]  # JAX array [n]

    # call Shimmy via Julia (zero-copy)
    jl.seval("using Shimmy: zero_copy_bridge")
    jl.zero_copy = zero_copy
    jl.buffer_size = buffer_size
    jl.buffer = buffer
    jl.seval("""
        using Shimmy: zero_copy_bridge
        zc_buffer = zero_copy_bridge(buffer, buffer_size=buffer_size, zero_copy=zero_copy)
    """)
    zc_buffer = jl.zc_buffer  # PyTree (JAX array)

    return dict(zc_buffer=zc_buffer, zero_copy=zero_copy, buffer_size=buffer_size)


# ----------------------------------------------------------
# 4.  Fused spell
# ----------------------------------------------------------
_SPELL = "(𝚂𝙷𝙸𝙼𝙼𝚈 ⊗ 𝙴𝙽𝚅 ⊗ 𝚆𝚁𝙰𝙿)(env=CartPole-v1, vectorise=True, zero_copy=True, buffer_size=4096)"


# ----------------------------------------------------------
# 5.  Factory – identical API to fql_rime
# ----------------------------------------------------------
def make_shimmy(
    env_id: str = "CartPole-v1",
    vectorise: bool = True,
    zero_copy: bool = True,
    buffer_size: int = 4096,
):
    spell = "(𝚂𝙷𝙸𝙼𝙼𝚈 ⊗ 𝙴𝙽𝚅 ⊗ 𝚆𝚁𝙰𝙿)(env={}, vectorise={}, zero_copy={}, buffer_size={})".format(
        env_id, vectorise, zero_copy, buffer_size
    )
    step_fn = compile_spell(spell)

    # build static env handle (injected)
    def bound_step(key, state):
        return step_fn(key, state, {
            "env_id": env_id,
            "vectorise": vectorise,
            "zero_copy": zero_copy,
            "buffer_size": buffer_size,
        })

    # initial state – empty (Shimmy fills it)
    state = dict(
        buffer=jnp.zeros(buffer_size),  # dummy buffer
        dummy=jnp.zeros(1),  # placeholder
    )

    return jax.jit(bound_step), state
