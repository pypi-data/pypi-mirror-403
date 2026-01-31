# src/synthfuse/meta/safe_macro.py
"""
SAFE(f): Unified safety macro for robust fusion pipelines.
Usage: safe_step = SAFE(base_step, clip_norm=5.0, max_iter=1000, lr=0.01)
"""

import jax
import jax.numpy as jnp
from flax import struct
from typing import Callable, NamedTuple

# Import primitives (assumes they're implemented as above)
from .regulator import RegulatorState, regulator_step
from .rollback import RollbackState, init_rollback_state
from .gradient_clip import fuse_with_clip  # combinator-style


@struct.dataclass
class SafeState:
    """
    Unified state that chains ℛ → ∇̃ → ⟲ metadata.
    Compatible with any base state that has .x and .loss.
    """
    x: jax.Array
    loss: jax.Array
    # ℛ fields
    step_count: int = 0
    grad_norm: float = 0.0
    diverged: bool = False
    halted: bool = False
    # ⟲ fields
    checkpoint_x: jax.Array = None
    checkpoint_loss: jax.Array = None


def init_safe_state(base_state: NamedTuple) -> SafeState:
    """Initialize from any base state (e.g., from ISO, RIME, etc.)"""
    x = base_state.x
    loss = base_state.loss
    return SafeState(
        x=x,
        loss=loss,
        checkpoint_x=x,
        checkpoint_loss=loss
    )


def SAFE(
    base_step: Callable,
    clip_norm: float = 1.0,
    lr: float = 0.01,
    max_iter: int = 10_000,
    grad_clip_monitor: float = 10.0,  # for ℛ
    halt_on_nan: bool = True,
    convergence_tol: float = 1e-6
) -> Callable:
    """
    Returns a new step function: SAFE(f) = ℛ ⊗ ∇̃(f) ⊗ ⟲
    
    Args:
        base_step: original step function (key, state, params) → state
        clip_norm: max L2 norm for gradient clipping (∇̃)
        lr: learning rate for clipped update
        max_iter: hard iteration cap (ℛ)
        grad_clip_monitor: threshold for ℛ to flag instability
    """
    # Wrap base_step with gradient clipping
    clipped_step = fuse_with_clip(base_step, clip_norm=clip_norm, lr=lr)

    def safe_step(key: jax.Array, state: SafeState, params: dict):
        # 1. Apply regulator (ℛ) — monitor current state
        reg_params = {
            "grad_clip": grad_clip_monitor,
            "max_iter": max_iter,
            "halt_on_nan": halt_on_nan,
            "convergence_tol": convergence_tol
        }
        reg_state = RegulatorState(
            x=state.x,
            loss=state.loss,
            step_count=state.step_count,
            grad_norm=state.grad_norm,
            diverged=state.diverged,
            halted=state.halted
        )
        reg_out = regulator_step(key, reg_state, reg_params)

        # Early halt if needed
        if reg_out.halted:
            return state._replace(
                step_count=reg_out.step_count,
                halted=True
            )

        # 2. Run clipped base step (∇̃)
        temp_state = type('', (), {'x': reg_out.x, 'loss': reg_out.loss})()
        clipped_out = clipped_step(key, temp_state, params)
        new_x = clipped_out.x
        new_loss = clipped_out.loss
        new_grad_norm = getattr(clipped_out, 'grad_norm', reg_out.grad_norm)

        # 3. Prepare for rollback (⟲)
        current_diverged = (
            jnp.any(jnp.isnan(new_x)) |
            jnp.isnan(new_loss) |
            jnp.any(jnp.isinf(new_x)) |
            jnp.isinf(new_loss)
        )

        # Restore if diverged
        safe_x = jnp.where(current_diverged, state.checkpoint_x, new_x)
        safe_loss = jnp.where(current_diverged, state.checkpoint_loss, new_loss)

        # Update checkpoint only if safe
        updated_checkpoint_x = jnp.where(current_diverged, state.checkpoint_x, new_x)
        updated_checkpoint_loss = jnp.where(current_diverged, state.checkpoint_loss, new_loss)

        return SafeState(
            x=safe_x,
            loss=safe_loss,
            step_count=reg_out.step_count,
            grad_norm=float(new_grad_norm),
            diverged=bool(current_diverged),
            halted=False,
            checkpoint_x=updated_checkpoint_x,
            checkpoint_loss=updated_checkpoint_loss
        )

    return safe_step
