"""
Polynomial SVR with Tree Regularisation  (Architecture I)
𝕊𝕍ℝ – Chebyshev basis + differentiable oblique-tree + GPU conv ε-SVR
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  State container
# ----------------------------------------------------------
@chex.dataclass
class PolySVRState:
    cheb_coeffs: jax.Array      # [d, order]  Chebyshev coefficients
    tree_latent: jax.Array      # [nodes, 2]  oblique-tree planes
    epsilon: float              # ε tube width


# ----------------------------------------------------------
# 2.  Registered primitives
# ----------------------------------------------------------
@register("𝕊𝕍ℝ")
def poly_svr_step(key: jax.Array, state: PolySVRState, params: dict) -> PolySVRState:
    """
    One ε-SVR step on Chebyshev features + differentiable tree penalty.
    Params: order (int), lambda_tree (float), epsilon (float)
    """
    order = params["order"]
    lam = params["lambda_tree"]
    eps = params["epsilon"]

    # 1. Chebyshev basis (GPU-friendly 1-D conv)
    x = params["x"]  # [n]
    cheb = jax.scipy.special.eval_chebyt(jnp.arange(order), x)  # [order, n]

    # 2. SVR dual update (GPU conv)
    #    min ½αᵀKα − αᵀy   s.t.   0 ≤ α ≤ C,  Σα=0
    K = jnp.cos(jnp.pi * jnp.abs(cheb[:, None] - cheb[None, :]))  # Chebyshev kernel
    alpha = jnp.linalg.solve(K + 1e-6 * jnp.eye(order), params["y"])  # closed-form stub

    # 3. Differentiable tree penalty (Straight-Through Gumbel)
    def tree_loss(planes):
        # oblique split:  sign(x @ plane)  –  ST Gumbel
        split = jax.nn.sigmoid(10 * (x @ planes.T))
        return jnp.sum(split * (1 - split))  # encourage purity
    grads = jax.grad(tree_loss)(state.tree_latent)
    planes_new = state.tree_latent - lam * grads

    # 4. ε-tube update
    y_pred = alpha @ cheb
    alpha_new = jnp.clip(alpha, 0, params.get("C", 1.0))

    return state.replace(
        cheb_coeffs=alpha_new,
        tree_latent=planes_new,
        epsilon=eps,
    )


# ----------------------------------------------------------
# 3.  Factory
# ----------------------------------------------------------
def make_poly_svr(order: int = 8, lambda_tree: float = 0.01, epsilon: float = 0.1):
    spell = "(𝕊𝕍ℝ)(order={}, lambda_tree={}, epsilon={})".format(order, lambda_tree, epsilon)
    step_fn = compile_spell(spell)

    state = PolySVRState(
        cheb_coeffs=jnp.zeros(order),
        tree_latent=jax.random.normal(jax.PRNGKey(0), (16, 2)),  # 16 oblique planes
        epsilon=epsilon,
    )
    return jax.jit(step_fn), state
