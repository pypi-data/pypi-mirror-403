# src/synthfuse/meta/rollback.py
from typing import NamedTuple
import jax
import jax.numpy as jnp
from flax import struct
from synthfuse.alchemj.registry import register

@struct.dataclass
class RollbackState:
    x: jax.Array
    loss: jax.Array
    checkpoint_x: jax.Array      # saved safe state
    checkpoint_loss: jax.Array
    diverged: bool = False

@register("⟲")
def rollback_step(
    key: jax.Array,
    state: RollbackState,
    params: dict
) -> RollbackState:
    """
    ⟲: Rollback to checkpoint if current state is invalid.
    
    Should be placed AFTER a risky step and AFTER ℛ (to read .diverged).
    """
    # Detect current divergence
    current_diverged = (
        jnp.any(jnp.isnan(state.x)) |
        jnp.isnan(state.loss) |
        jnp.any(jnp.isinf(state.x)) |
        jnp.isinf(state.loss)
    )

    # Restore if needed
    safe_x = jnp.where(current_diverged, state.checkpoint_x, state.x)
    safe_loss = jnp.where(current_diverged, state.checkpoint_loss, state.loss)

    # Update checkpoint if current is safe
    new_checkpoint_x = jnp.where(current_diverged, state.checkpoint_x, state.x)
    new_checkpoint_loss = jnp.where(current_diverged, state.checkpoint_loss, state.loss)

    return RollbackState(
        x=safe_x,
        loss=safe_loss,
        checkpoint_x=new_checkpoint_x,
        checkpoint_loss=new_checkpoint_loss,
        diverged=bool(current_diverged)
    )

# Helper: initialize rollback state
def init_rollback_state(base_state: NamedTuple) -> RollbackState:
    return RollbackState(
        x=base_state.x,
        loss=base_state.loss,
        checkpoint_x=base_state.x,
        checkpoint_loss=base_state.loss
    )
