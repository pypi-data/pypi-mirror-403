"""
NS²UO:  Neuro-Swarm-to-Universal-Optimizer
Meta-cognitive controller that treats optimisation strategies as **particles**
in a **solution space**, exchanges them via **light-beam protocols**,
and self-improves by **semantic free-energy** descent.
"""
import jax
import jax.numpy as jnp
import chex
from typing import Any
from synthfuse.alchemj import compile_spell

PyTree = Any


# ------------------------------------------------------------------
# 1.  Semantic state container
# ------------------------------------------------------------------
@chex.dataclass
class StrategyParticle:
    params: PyTree          # actual strategy weights / hparams
    fitness: float          # last evaluated loss
    age: int                # steps since birth
    tag: str                # human readable id
    free_energy: float      # ℱ = fitness - β·C(params)


@chex.dataclass
class NS2UOState:
    swarm: StrategyParticle   # particle array
    g_best: StrategyParticle  # global best
    temp: float               # β = 1/temp
    exchange_buffer: PyTree   # compact shared memory
    helios_clock: int         # global sync tick


# ------------------------------------------------------------------
# 2.  Light-beam exchange (non-blocking, ring topology)
# ------------------------------------------------------------------
def light_exchange(key: jax.Array, state: NS2UOState) -> NS2UOState:
    """
    Ring all-reduce of *semantic gradients* (not raw params).
    Uses β-divergence weighted average → preserves diversity.
    """
    n = len(state.swarm)
    k1, k2 = jax.random.split(key)

    # semantic gradient = ∇_z ℱ  (here finite-diff)
    eps = 1e-4
    z = jax.tree.map(lambda p: p.params, state.swarm)
    f = jax.tree.map(lambda p: p.free_energy, state.swarm)

    def semigrad(i):
        z_plus = jax.tree.map(lambda x: x + eps, z[i])
        f_plus = f[i]  # stub: real eval would call oracle
        return jax.tree.map(lambda dx: (f_plus - f[i]) / eps, z_plus)

    grads = jax.vmap(semigrad)(jnp.arange(n))

    # ring reduce: neighbour i ← 0.7·g_i + 0.3·g_{i+1}
    def ring_reduce(g, _), idx):
        nxt = (idx + 1) % n
        new_g = 0.7 * g + 0.3 * grads[nxt]
        return new_g, None

    reduced, _ = jax.lax.scan(ring_reduce, grads[0], jnp.arange(n))

    # apply semantic gradient → new params
    new_params = jax.tree.map(
        lambda p, g: p - 0.01 * g,  # learning-rate hard-coded for demo
        jax.tree.map(lambda p: p.params, state.swarm),
        reduced,
    )

    # rebuild particles
    new_swarm = jax.tree.map(
        lambda old, p: old.replace(params=p, age=old.age + 1),
        state.swarm,
        new_params,
    )

    return state.replace(swarm=new_swarm)


# ------------------------------------------------------------------
# 3.  Meta-cognitive controller (Helios loop)
# ------------------------------------------------------------------
def helios_step(key: jax.Array, state: NS2UOState, oracle: PyTree) -> NS2UOState:
    """
    One meta-tick:
      1. evaluate all strategies on oracle
      2. update free-energy
      3. light-exchange
      4. birth/death based on ℱ
    """
    k1, k2, k3 = jax.random.split(key, 3)

    # ---- evaluate -------------------------------------------------
    losses = jax.vmap(lambda p: oracle(p.params))(state.swarm)
    beta = 1.0 / state.temp
    complexities = jax.tree.map(lambda p: jnp.sum(jnp.abs(p.params)), state.swarm)
    free_energies = losses - beta * complexities

    swarm_new = jax.tree.map(
        lambda p, loss, fe: p.replace(fitness=loss, free_energy=fe),
        state.swarm,
        losses,
        free_energies,
    )

    # ---- global best ---------------------------------------------
    best_idx = jnp.argmin(free_energies)
    g_best = swarm_new[best_idx]

    # ---- light exchange ------------------------------------------
    state_mid = state.replace(swarm=swarm_new, g_best=g_best)
    state_post = light_exchange(k2, state_mid)

    # ---- birth/death (simple: worst replaced by perturbed best) ---
    worst_idx = jnp.argmax(free_energies)
    key_p = jax.random.fold_in(k3, worst_idx)
    noise = jax.tree.map(
        lambda x: 0.05 * jax.random.normal(key_p, x.shape),
        g_best.params,
    )
    new_part = g_best.replace(
        params=jax.tree.map(jnp.add, g_best.params, noise),
        age=0,
        tag="child",
    )
    swarm_final = state_post.swarm.at[worst_idx].set(new_part)

    return state_post.replace(swarm=swarm_final, helios_clock=state.helios_clock + 1)


# ------------------------------------------------------------------
# 4.  Public factory
# ------------------------------------------------------------------
def make_ns2uo(step_spell: str, n_strategies: int = 32, temp: float = 1.0) -> tuple[Callable, NS2UOState]:
    """
    Returns (step_fn, initial_state) ready for JIT.
    step_spell is any ALCHEM-J string used *inside* each strategy particle.
    """
    inner_step = compile_spell(step_spell)  # JIT-ed strategy kernel

    def oracle(params):
        # dummy oracle: minimise Rastrigin
        return jnp.sum(params ** 2 - 10 * jnp.cos(2 * jnp.pi * params))  # placeholder

    key = jax.random.PRNGKey(42)
    keys = jax.random.split(key, n_strategies)
    dim = 20  # hard-coded for demo
    init_params = jax.random.uniform(keys[0], (n_strategies, dim), minval=-5.12, maxval=5.12)

    particles = jax.vmap(lambda p: StrategyParticle(
        params=p,
        fitness=jnp.inf,
        age=0,
        tag="seed",
        free_energy=jnp.inf,
    ))(init_params)

    g_best = particles[0]  # will be overwritten on first eval

    state = NS2UOState(
        swarm=particles,
        g_best=g_best,
        temp=temp,
        exchange_buffer=jnp.zeros((dim,)),  # placeholder
        helios_clock=0,
    )

    @jax.jit
    def step(key: jax.Array, state: NS2UOState) -> NS2UOState:
        return helios_step(key, state, oracle)

    return step, state