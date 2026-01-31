from synthfuse.tools import Timer, profile_jit

with Timer("forward_pass") as t:
    result = model.apply(params, x)
print(f"Execution time: {t.elapsed:.4f}s")

# JIT compilation profiling
profile_jit(my_function, jax.random.PRNGKey(0), sample_input)
