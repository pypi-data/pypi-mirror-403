import jax
import jax.numpy as jnp
from alchemj.registry import alchemj

@alchemj.register("𝕀")
def iso_step(key, state, params, fitness_fn):
    """
    𝕀 (ISO): Intelligent Swarm Optimization Step.
    Uses a hybrid of inertia and gravitational attraction to the global best.
    """
    # 1. Update Velocity (Inertia + Cognitive + Social)
    r1, r2 = jax.random.uniform(key, (2, state.pos.shape[0]))
    new_vel = (params.w * state.vel + 
               params.c1 * r1 * (state.best_pos - state.pos) + 
               params.c2 * r2 * (state.g_best_pos - state.pos))
    
    # 2. Update Position
    new_pos = state.pos + new_vel
    
    # 3. Evaluate Fitness
    fitness = fitness_fn(new_pos)
    
    # 4. Update Personal Best
    is_better = fitness < state.best_fitness
    best_pos = jnp.where(is_better[:, None], new_pos, state.best_pos)
    best_fitness = jnp.where(is_better, fitness, state.best_fitness)
    
    return state.replace(
        pos=new_pos, 
        vel=new_vel, 
        best_pos=best_pos, 
        best_fitness=best_fitness
    )

@alchemj.register("𝕊")
def mrbmo_siege_step(key, state, params, fitness_fn):
    """
    𝕊 (Siege): Modified Red-Back Spider Optimization.
    Focuses on 'GoodNodesSet' to surround the global optima.
    """
    # Spider Siege Logic: Agents move in a non-linear spiral toward the best node
    # to maintain functional diversity in the tool-space.
    dist_to_best = jnp.abs(state.g_best_pos - state.pos)
    spiral_factor = jnp.exp(params.b * params.l) * jnp.cos(2 * jnp.pi * params.l)
    
    new_pos = dist_to_best * spiral_factor + state.g_best_pos
    
    # Clip to Manifold bounds
    new_pos = jnp.clip(new_pos, params.min_bound, params.max_bound)
    
    return state.replace(pos=new_pos, fitness=fitness_fn(new_pos))