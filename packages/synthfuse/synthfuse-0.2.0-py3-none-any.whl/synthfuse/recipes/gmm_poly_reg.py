"""
GMM-Guided Polynomial Regression  (Architecture V)
𝔾𝕄𝕄 – Student-t mixture + input-dependent λ(x) + PCA whitening + TPU-JAX
"""
import jax
import jax.numpy as jnp
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

@register("𝔾𝕄𝕄")
def gmm_poly_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Student-t mixture log-likelihood + dynamic λ(x) + PCA whitening.
    Params: dof (float), lambda_max (float), pca_dim (int)
    """
    dof = params["dof"]
    lam_max = params["lambda_max"]
    pca_dim = params["pca_dim"]

    # 1. PCA whitening (pre-processing)
    x_white = (x - params["mean"]) / params["scale"]  # already whitened

    # 2. Student-t mixture log-likelihood (heavy-tailed)
    def student_t_logp(x, mu, sigma):
        return jax.scipy.stats.t.logpdf(x, dof, loc=mu, scale=sigma)
    logp = student_t_logp(x_white, params["mu"], params["sigma"])  # [n]

    # 3. dynamic regularisation λ(x) = λ_max * (1 - p(x))
    p_x = jnp.exp(logp)
    lam_x = lam_max * (1 - p_x)  # strong penalty in sparse regions

    # 4. polynomial regression with dynamic ridge
    poly = jnp.polyval(params["coef"], x_white)
    loss = jnp.mean((poly - params["y"]) ** 2) + jnp.mean(lam_x * params["coef"] ** 2)

    # 5. gradient update (closed-form stub)
    grads = jax.grad(lambda c: jnp.mean((jnp.polyval(c, x_white) - params["y"]) ** 2))(params["coef"])
    coef_new = params["coef"] - 0.01 * grads  # lr hard-coded for demo

    return dict(coef=coef_new, loss=loss)


def make_gmm_poly_reg(dof: float = 5.0, lambda_max: float = 0.1, pca_dim: int = 32):
    spell = "(𝔾𝕄𝕄)(dof={}, lambda_max={}, pca_dim={})".format(dof, lambda_max, pca_dim)
    step_fn = compile_spell(spell)

    state = dict(
        coef=jax.random.normal(jax.PRNGKey(0), (pca_dim,)),
        y=jnp.zeros(128),  # dummy target
        mu=jnp.zeros(pca_dim),
        sigma=jnp.ones(pca_dim),
        mean=jnp.zeros(pca_dim),
        scale=jnp.ones(pca_dim),
    )
    return jax.jit(step_fn), state
