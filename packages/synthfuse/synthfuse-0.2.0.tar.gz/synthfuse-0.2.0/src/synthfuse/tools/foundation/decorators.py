from synthfuse.tools import jit, checkpoint, debug_transform

@jit(static_argnums=(0,))
def swarm_update(optimizer_state, positions, velocities):
    return optimizer_state.update(positions, velocities)

@checkpoint(preserve_rng_state=True)
def expensive_computation(x):
    return complex_transform(x)
