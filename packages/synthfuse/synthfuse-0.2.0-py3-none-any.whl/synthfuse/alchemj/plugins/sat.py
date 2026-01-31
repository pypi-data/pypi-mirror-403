
@register("ℤ𝕊")
def switchksat_step(key: jax.Array, x: jax.Array, params: dict) -> jax.Array:
    """Switch-k SAT solver step – returns satisfiability mask."""
    k = params.get("k", 3)
    # your pure-JAX implementation here
    return mask  # same shape as input
