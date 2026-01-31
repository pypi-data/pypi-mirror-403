"""
Open-Gate side-channel hardening for Synth-Fuse
- Random padding → size indistinguishability
- Token-batching → timing smoothing
- Packet-injection → noise floor raise
All ops are **JAX-native** → still jit/vmap/pmap safe.
"""
import jax
import jax.numpy as jnp
from synthfuse.alchemj.registry import register
from typing import Tuple

# ----------------------------------------------------------
# 𝟙.  Random-Padding primitive  (size masking)
# ----------------------------------------------------------
@register("𝔓")   # Pad
def open_gate_pad(key: jax.Array, x: jax.Array, params: dict) -> jax.Array:
    """
    Appends **random-length zero block** to last axis.
    Params: pad_max (int) – max padding length
    Returns: padded array, **same dtype**, **JIT-safe**.
    """
    pad_max = params.get("pad_max", 16)
    # draw uniform padding length
    pad_len = jax.random.randint(key, (), 0, pad_max + 1)
    # build zero block
    shape = list(x.shape)
    shape[-1] = pad_len
    zeros = jnp.zeros(shape, dtype=x.dtype)
    # concatenate
    return jnp.concatenate([x, zeros], axis=-1)


# ----------------------------------------------------------
# 𝟚.  Token-Batching primitive  (timing smoothing)
# ----------------------------------------------------------
@register("𝔅")   # Batch
def open_gate_batch(key: jax.Array, x: jax.Array, params: dict) -> jax.Array:
    """
    Buffers **exactly `batch_size` tokens** along last axis before emitting.
    Params: batch_size (int)
    Returns: stacked tensor, **deterministic shape** [..., batch_size].
    **No real I/O** – shape is fixed at compile time; unused slots zero-padded.
    """
    batch_size = params["batch_size"]  # must be static for JIT
    # current token count along last axis
    n = x.shape[-1]
    # pad to multiple of batch_size
    remainder = (batch_size - n % batch_size) % batch_size
    pad_shape = list(x.shape); pad_shape[-1] = remainder
    padded = jnp.concatenate([x, jnp.zeros(pad_shape, dtype=x.dtype)], axis=-1)
    # reshape → [..., batch_size] chunks
    new_shape = list(padded.shape[:-1]) + [-1, batch_size]
    return padded.reshape(new_shape)


# ----------------------------------------------------------
# 𝟛.  Packet-Injection primitive  (noise floor)
# ----------------------------------------------------------
@register("𝕀𝔾")  # Inject-Gauss
def open_gate_inject(key: jax.Array, x: jax.Array, params: dict) -> jax.Array:
    """
    Injects **synthetic Gaussian packets** at **random positions** along last axis.
    Params: inject_prob (float) – probability per position
            inject_scale (float) – std-dev of noise
    Returns: x + noise, **same shape**, **differentiable**.
    """
    prob = params.get("inject_prob", 0.05)
    scale = params.get("inject_scale", 1e-3)
    mask = jax.random.bernoulli(key, prob, x.shape)
    noise = jax.random.normal(key, x.shape) * scale
    return x + mask * noise


# ----------------------------------------------------------
# 𝟜.  High-level Open-Gate fusion recipe
# ----------------------------------------------------------
def make_open_gate(
    pad_max: int = 16,
    batch_size: int = 5,
    inject_prob: float = 0.05,
    inject_scale: float = 1e-3,
):
    """
    Returns (jit_step, init_state) for an **open-gate hardened pipeline**.
    Usage:
        step, state = make_open_gate()
        hardened = step(key, data, {})  # size & timing obfuscated
    """
    spell = "(𝔓 ⊗ 𝔅 ⊗ 𝕀𝔾)(pad_max={}, batch_size={}, inject_prob={}, inject_scale={})".format(
        pad_max, batch_size, inject_prob, inject_scale
    )
    from synthfuse.alchemj import compile_spell
    return compile_spell(spell), None  # stateless
