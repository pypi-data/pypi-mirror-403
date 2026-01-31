"""
Neural Tool-Embedding Protocol (NTEP)
ϕ : software → τ⊕σ  (task-vector ⊕ signature-vector)
Impulse protocol:  ϕ⁻¹(τ) → executable impulse → desktop / API / MCP
Includes phase-locking for multi-tool coherence.
"""
import jax
import jax.numpy as jnp
import chex
import hashlib
from typing import Any, Callable
from synthfuse.alchemj import compile_spell

PyTree = Any


# ------------------------------------------------------------------
# 1.  Embedding space
# ------------------------------------------------------------------
TOOL_DIM = 512   # fixed latent dim (can be 64/128/…)

@chex.dataclass
class ToolEmbed:
    tau: jax.Array      # task context vector  [TOOL_DIM]
    sigma: jax.Array    # signature hash vector [TOOL_DIM]
    meta: dict          # human metadata (name, version, hash)


# ------------------------------------------------------------------
# 2.  Phi encoder  (software → embed)
# ------------------------------------------------------------------
def phi(tool_source: str, docstring: str) -> ToolEmbed:
    """
    Deterministic embedding from source+doc:
      tau = TF-IDF style weighted bag-of-tokens (learned projection)
      sigma = SHA256(source) → deterministic vector
    """
    # stub: random projection for demo; replace with small transformer
    key1, key2 = jax.random.split(jax.random.PRNGKey(abs(hash(tool_source)) % 2**31))
    tau = jax.random.normal(key1, (TOOL_DIM,))
    # deterministic sigma from SHA256
    h = hashlib.sha256(tool_source.encode()).digest()
    sigma = jnp.frombuffer(h, dtype=jnp.uint8)[:TOOL_DIM] / 255.0
    return ToolEmbed(tau=tau, sigma=sigma, meta={"source_len": len(tool_source)})


# ------------------------------------------------------------------
# 3.  Impulse protocol  (embed → executable impulse)
# ------------------------------------------------------------------
@chex.dataclass
class Impulse:
    vector: jax.Array          # latent command [TOOL_DIM]
    amplitude: float           // confidence / temperature
    registry_id: str           // which tool to invoke


def impulse(embed: ToolEmbed, context_vector: jax.Array, temp: float = 1.0) -> Impulse:
    """
    Compute impulse vector = τ ⊕ context  (concat + project)
    amplitude = cos-sim(τ, context) / temp
    """
    concat = jnp.concatenate([embed.tau, context_vector])
    # simple linear probe → impulse vector
    W = jax.lax.stop_gradient(jnp.eye(TOOL_DIM * 2)[:TOOL_DIM, :])  # learned W stub
    vector = W @ concat
    sim = jnp.dot(embed.tau, context_vector) / (jnp.linalg.norm(embed.tau) * jnp.linalg.norm(context_vector) + 1e-8)
    return Impulse(vector=vector, amplitude=sim / temp, registry_id=hashlib.md5(embed.sigma.tobytes()).hexdigest()[:8])


# ------------------------------------------------------------------
# 4.  Phase-locking for multi-tool coherence
# ------------------------------------------------------------------
def phase_lock(embeds: list[ToolEmbed], context: jax.Array, lock_strength: float = 0.9) -> jax.Array:
    """
    Returns a single **coherent** impulse vector by locking phases:
      1. compute relative phase = angle between each τ and context
      2. rotate all τ toward context by lock_strength
      3. mean pool
    """
    vectors = jnp.stack([e.tau for e in embeds])
    phases = jnp.sign(jnp.einsum("td,d->t", vectors, context))
    locked = vectors + lock_strength * (phases[:, None] * context[None, :] - vectors)
    return jnp.mean(locked, axis=0)


# ------------------------------------------------------------------
# 5.  Desktop execution bridge (mock)
# ------------------------------------------------------------------
EXECUTABLE_REGISTRY: dict[str, Callable] = {}  # populates at import


def register_desktop(name: str, fn: Callable):
    EXECUTABLE_REGISTRY[name] = fn


# mock tools
register_desktop("calc", lambda x: x + 1)
register_desktop("twice", lambda x: 2 * x)
register_desktop("neg", lambda x: -x)


def execute(imp: Impulse, payload: PyTree) -> PyTree:
    """
    Dispatch to desktop / API / MCP by registry_id match
    Returns (result, meta)
    """
    # find closest key (hamming on sigma hash)
    keys = list(EXECUTABLE_REGISTRY.keys())
    idx = jnp.argmin(jnp.array([jnp.sum(jnp.abs(jnp.uint8(list(k.encode())) - jnp.uint8(list(imp.registry_id[:len(k)]))) for k in keys]))
    tool_fn = EXECUTABLE_REGISTRY[keys[idx]]
    result = tool_fn(payload)
    return result, {"tool": keys[idx], "amplitude": imp.amplitude}


# ------------------------------------------------------------------
# 6.  End-to-end NTEP step (for inclusion in ALCHEM-J spell)
# ------------------------------------------------------------------
@jax.jit
def ntep_step(key: jax.Array, x: dict, params: dict) -> dict:
    """
    x = dict(source: str, context: array, payload: pytree)
    params = dict(temp, lock_strength)
    """
    embed = phi(x["source"], x.get("doc", ""))
    context = x["context"]
    temp = params.get("temp", 1.0)
    lock = params.get("lock_strength", 0.9)

    # multi-tool?  if list → phase-lock, else solo
    if isinstance(context, list):
        coherent = phase_lock([embed], context, lock)  # stub list of 1
    else:
        coherent = embed.tau

    imp = impulse(embed, coherent, temp)
    result, meta = execute(imp, x["payload"])

    return dict(result=result, meta=meta, embed=embed)


# ------------------------------------------------------------------
# 7.  Public factory  (returns JIT step + init state)
# ------------------------------------------------------------------
def make_ntep(tool_source: str, context_dim: int = TOOL_DIM) -> tuple[Callable, dict]:
    """
    Returns (step_fn, init_x) ready for Synth-Fuse pipeline
    """
    embed = phi(tool_source, "NTEP distilled tool")
    init_x = dict(
        source=tool_source,
        context=jnp.zeros(context_dim),
        payload=jnp.zeros(10),  # dummy payload
    )
    return jax.jit(ntep_step), init_x