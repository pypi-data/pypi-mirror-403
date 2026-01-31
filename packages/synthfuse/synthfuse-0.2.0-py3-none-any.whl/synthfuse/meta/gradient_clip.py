# src/synthfuse/meta/gradient_clip.py
from typing import NamedTuple
import jax
import jax.numpy as jnp
from flax import struct
from synthfuse.alchemj.registry import register

@struct.dataclass
class ClippedState:
    x: jax.Array
    loss: jax.Array
    grad_norm: float = 0.0

@register("∇̃")
def clipped_step(
    key: jax.Array,
    state: NamedTuple,
    params: dict
) -> ClippedState:
    """
    ∇̃: Enforce gradient clipping on the update direction.
    
    Assumes the upstream step has a differentiable .loss w.r.t. .x.
    Computes grad, clips it, and applies a safe update.
    
    Parameters:
        clip_norm: float (default: 1.0)
        lr: learning rate (default: 0.01)
    """
    clip_norm = params.get("clip_norm", 1.0)
    lr = params.get("lr", 0.01)

    # Compute gradient of loss w.r.t. x
    def loss_fn(x):
        return state.loss  # assumes loss depends on x implicitly

    # But we need explicit dependency → so we require state to be compatible
    # Alternative: use implicit differentiation via custom_vjp (advanced)
    # For now, assume state has x and loss(x) is recomputable
    # → This is a limitation; real version would wrap a step function

    # ⚠️ Simpler design: ∇̃ wraps another step
    raise NotImplementedError(
        "∇̃ requires wrapping a base step. Use: fuse_with_clip(base_step, clip_norm=...)"
    )


# ✅ Better approach: decorator-style combinator
def fuse_with_clip(base_step, clip_norm: float = 1.0, lr: float = 0.01):
    """
    Returns a new step function that applies gradient-clipped updates.
    Usage: clipped_opt = fuse_with_clip(make_iso()[0], clip_norm=5.0)
    """
    def wrapped_step(key, state, params):
        # Recompute loss w.r.t. x (requires state.x to be the only variable)
        def loss_given_x(x):
            # Reconstruct temporary state
            temp_state = state._replace(x=x)
            # Assume base_step doesn't change loss without x update
            return temp_state.loss

        grad = jax.grad(loss_given_x)(state.x)
        grad_norm = jnp.linalg.norm(grad)
        clipped_grad = jnp.where(
            grad_norm > clip_norm,
            grad * (clip_norm / grad_norm),
            grad
        )
        new_x = state.x - lr * clipped_grad

        return state._replace(x=new_x, grad_norm=float(grad_norm))
    return wrapped_step
