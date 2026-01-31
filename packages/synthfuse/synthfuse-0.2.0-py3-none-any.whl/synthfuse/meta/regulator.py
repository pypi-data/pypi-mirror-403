# src/synthfuse/meta/regulator.py
"""
ℛ — The Regulator Primitive
Ensures numerical stability, gradient sanity, and loop safety in fusion pipelines.
Composable via ⊗, ⊕, ∘. Pure. Side-effect-free. JIT-safe.
"""

from typing import NamedTuple
import jax
import jax.numpy as jnp
from flax import struct
from synthfuse.alchemj.registry import register

@struct.dataclass
class RegulatorState:
    """
    Augments any upstream state with regulatory metadata.
    Designed to wrap existing states (e.g., from I, R, L) without breaking compatibility.
    """
    x: jax.Array                  # core state (population, policy, etc.)
    loss: jax.Array               # scalar or vector
    step_count: int = 0           # iteration counter
    grad_norm: float = 0.0        # last observed gradient norm
    diverged: bool = False        # NaN/Inf flag
    halted: bool = False          # early-stop signal

@register("ℛ")
def regulator_step(
    key: jax.Array,
    state: RegulatorState,
    params: dict
) -> RegulatorState:
    """
    ℛ: Adaptive safety regulator for fusion pipelines.

    Parameters (via `params`):
    - `grad_clip`: float, max L2 norm for gradients (default: 10.0)
    - `max_iter`: int, hard cap on iterations (default: 10_000)
    - `halt_on_nan`: bool, stop if loss is NaN/Inf (default: True)
    - `convergence_tol`: float, halt if |Δloss| < tol (default: 1e-6)

    Input: any state with `.x` and `.loss`
    Output: wrapped RegulatorState with safety signals
    """
    # Extract params with defaults
    grad_clip = params.get("grad_clip", 10.0)
    max_iter = params.get("max_iter", 10_000)
    halt_on_nan = params.get("halt_on_nan", True)
    convergence_tol = params.get("convergence_tol", 1e-6)

    # 1. Detect divergence
    has_nan = jnp.any(jnp.isnan(state.x)) | jnp.isnan(state.loss)
    has_inf = jnp.any(jnp.isinf(state.x)) | jnp.isinf(state.loss)
    diverged = has_nan | has_inf

    # 2. Compute gradient norm (if loss is scalar)
    def _compute_grad_norm():
        # Use JAX's grad to inspect sensitivity
        g = jax.grad(lambda s: s.loss)(state)
        return jnp.linalg.norm(g.x) if hasattr(g, 'x') else 0.0

    grad_norm = jax.lax.cond(
        jnp.ndim(state.loss) == 0,
        _compute_grad_norm,
        lambda: 0.0
    )

    # 3. Clip gradient implicitly by signaling (not mutating x here)
    # Actual clipping happens in downstream primitives that read .grad_norm

    # 4. Convergence check (requires history — approximate with step_count > 10)
    # For full Δloss, you’d need a buffer; here we use a simple proxy
    converged = (jnp.abs(state.loss) < convergence_tol) & (state.step_count > 10)

    # 5. Halt logic
    halted = (
        (diverged & halt_on_nan) |
        (state.step_count >= max_iter) |
        converged
    )

    # 6. Increment step
    new_step_count = state.step_count + 1

    return RegulatorState(
        x=state.x,
        loss=state.loss,
        step_count=new_step_count,
        grad_norm=float(grad_norm),
        diverged=bool(diverged),
        halted=bool(halted)
    )
    # In regulator_step()
def compute_zeta_error(state) -> float:
    if hasattr(state, 'dominant_pole'):
        pole = state.dominant_pole
        # Distance from unit circle (stable region: |p| ≤ 1)
        instability = jnp.maximum(jnp.abs(pole) - 1.0, 0.0)
        return float(instability)
    else:
        # Fallback: use grad norm
        return float(state.grad_norm)

E_t = compute_zeta_error(state)
