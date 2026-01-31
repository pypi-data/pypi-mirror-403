from synthfuse.tools import PRNGManager

rng = PRNGManager(seed=42)

# Split for parallel operations
rngs = rng.split(10)  # 10 independent RNG keys

# Or use context manager for automatic splitting
with rng.fold() as sub_rng:
    noise = jax.random.normal(sub_rng.key, shape=(100, 100))
