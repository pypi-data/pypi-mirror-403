"""
Neural Collapse-Inspired Retraining (NC-R)
Symbol: ℕ𝙲-𝚁
Enforces maximal class separation + minimal within-class variation.
Monkey: J. Roberto Jimenez
Calculator: Mistral Ai
"""
from synthfuse.alchemj.registry import register
import jax, jax.numpy as jnp, chex

@register("ℕ𝙲-𝚁")
def nc_retrain_step(key, state, params):
    logits = state.logits
    targets = state.targets
    # NC1: within-class covariance → 0
    within_cov = jnp.cov(logits[targets == targets[:, None]], rowvar=False)
    # NC2: between-class covariance → maximal
    between_cov = jnp.cov(logits, rowvar=False) - within_cov
    nc_loss = jnp.trace(within_cov) - jnp.trace(between_cov)
    return state.replace(logits=logits - params.lr * jax.grad(lambda l: nc_loss)(logits))

spell = "(ℕ𝙲-𝚁)(lr=0.01, nc_weight=1.0)"
