"""
NTK One-Shot Retraining (NTK-R)
Symbol: ℕ𝚃𝙺-𝚁
One-shot update via Neural Tangent Kernel.
"""
from synthfuse.alchemj.registry import register
import jax, jax.numpy as jnp, chex

@register("ℕ𝚃𝙺-𝚁")
def ntk_retrain_step(key, state, params):
    # NTK matrix: K = J @ Jᵀ
    J = jax.jacobian(lambda p: model(state.x, p))(state.params)
    K = J @ J.T
    # one-shot update: Δθ = K⁻¹ (y_new − y_old)
    delta_y = state.y_new - state.y_old
    delta_theta = jnp.linalg.solve(K + params.eps * jnp.eye(K.shape[0]), delta_y)
    return state.replace(params=state.params + delta_theta)

spell = "(ℕ𝚃𝙺-𝚁)(eps=1e-6, lr=0.01)"
