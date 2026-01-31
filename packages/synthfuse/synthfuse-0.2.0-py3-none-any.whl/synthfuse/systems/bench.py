"""
Micro & emergent benchmark suite for Synth-Fuse
One command:  python -m synthfuse.systems.bench <recipe> [--dims 1000]
"""
import time
import argparse
import jax
import jax.numpy as jnp
from typing import Callable, Any
from synthfuse.alchemj import compile_spell
from synthfuse.recipes import get_recipe      # central recipe index

PyTree = Any


# ------------------------------------------------------------------
# 1.  Continuous optimisation
# ------------------------------------------------------------------
class Rastrigin:
    name = "Rastrigin"
    def __init__(self, dims: int):
        self.dims = dims
    def __call__(self, x: jax.Array) -> float:
        return 10 * self.dims + jnp.sum(x**2 - 10 * jnp.cos(2 * jnp.pi * x))
    def init(self, key: jax.Array, n: int) -> jax.Array:
        return jax.random.uniform(key, (n, self.dims), minval=-5.12, maxval=5.12)


class LunarLander:
    name = "LunarLanderContinuous"
    def __call__(self, x: jax.Array) -> float:
        # stub: real env would be wrapped with Brax
        return jnp.sum(x**2) + jnp.sum(jnp.sin(x))  # cheap proxy
    def init(self, key: jax.Array, n: int) -> jax.Array:
        return jax.random.normal(key, (n, 8))


# ------------------------------------------------------------------
# 2.  Combinatorial
# ------------------------------------------------------------------
class TSP:
    name = "TSP-200"
    def __init__(self, n: int = 200):
        self.n = n
        key = jax.random.PRNGKey(0)
        self.cities = jax.random.uniform(key, (n, 2))
    def __call__(self, tour: jax.Array) -> float:  # tour is permutation
        d = jnp.roll(tour, 1)
        dists = jnp.linalg.norm(self.cities[tour] - self.cities[d], axis=1)
        return jnp.sum(dists)
    def init(self, key: jax.Array, pop: int) -> jax.Array:
        return jax.vmap(lambda k: jax.random.permutation(k, self.n))(
            jax.random.split(key, pop)
        )


# ------------------------------------------------------------------
# 3.  Emergent behaviour probes
# ------------------------------------------------------------------
def decentralization_probe(step_fn: Callable, state: PyTree, steps: int) -> float:
    """
    Measures spontaneous drop in central coordination entropy.
    Returns ΔH = H_0 - H_final  (bits)
    """
    def entropy(x):
        p = jnp.abs(x) / jnp.sum(jnp.abs(x))
        p = jnp.where(p == 0, 1e-12, p)
        return -jnp.sum(p * jnp.log2(p))

    H0 = entropy(state)
    key = jax.random.PRNGKey(0)

    def body(carry, _):
        s, k = carry
        k1, k2 = jax.random.split(k)
        s = step_fn(k1, s, {})
        return (s, k2), None

    (state_final, _), _ = jax.lax.scan(body, (state, key), jnp.arange(steps))
    return entropy(state) - entropy(state_final)


# ------------------------------------------------------------------
# 4.  Runner
# ------------------------------------------------------------------
BENCHMARKS = {
    "rastrigin": Rastrigin,
    "lunar": LunarLander,
    "tsp": TSP,
}


def run_continuous(bench_cls, recipe: str, dims: int, pop: int, iters: int):
    bench = bench_cls(dims)
    step = compile_spell(recipe)
    key = jax.random.PRNGKey(42)
    pos = bench.init(key, pop)
    best = jnp.inf

    def scan_body(carry, _):
        p, k, b = carry
        k1, k2 = jax.random.split(k)
        # minimal spell expects PyTree: dict with 'pos'
        p = step(k1, dict(pos=p), {})
        p = jnp.clip(p, -10, 10)  # safety
        fit = jax.vmap(bench)(p)
        b = jnp.minimum(b, jnp.min(fit))
        return (p, k2, b), jnp.min(fit)

    (_, _, best), hist = jax.lax.scan(scan_body, (pos, key, best), jnp.arange(iters))
    return float(best), hist


def run_combinatorial(bench_cls, recipe: str, pop: int, iters: int):
    bench = bench_cls()
    step = compile_spell(recipe)
    key = jax.random.PRNGKey(0)
    pop = bench.init(key, pop)
    best = jnp.inf

    def body(carry, _):
        p, k, b = carry
        k1, k2 = jax.random.split(k)
        p = step(k1, dict(tour=p), {})
        fit = jax.vmap(bench)(p)
        b = jnp.minimum(b, jnp.min(fit))
        return (p, k2, b), jnp.min(fit)

    (_, _, best), hist = jax.lax.scan(body, (pop, key, best), jnp.arange(iters))
    return float(best), hist


def run_emergent(step_fn: Callable, state: PyTree, steps: int = 1000):
    delta_bits = decentralization_probe(step_fn, state, steps)
    return {"decentralization_gain_bits": float(delta_bits)}


# ------------------------------------------------------------------
# 5.  CLI
# ------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Synth-Fuse Benchmarks")
    ap.add_argument("recipe", help="Spell string or recipe name (e.g. fql_rime)")
    ap.add_argument("--dims", type=int, default=100, help="Problem dimension")
    ap.add_argument("--pop", type=int, default=128, help="Population size")
    ap.add_argument("--iters", type=int, default=1000, help="Iterations")
    ap.add_argument("--bench", choices=list(BENCHMARKS.keys()), default="rastrigin")
    ap.add_argument("--emergent", action="store_true", help="Run emergent probes")
    args = ap.parse_args()

    recipe = get_recipe(args.recipe) if args.recipe in get_recipe.list() else args.recipe

    if args.emergent:
        # build dummy swarm state for probe
        from alchemj.plugins.swarm import SwarmState
        key = jax.random.PRNGKey(1)
        state = SwarmState(
            pos=jax.random.normal(key, (args.pop, args.dims)),
            vel=jnp.zeros((args.pop, args.dims)),
            best_pos=jnp.zeros((args.pop, args.dims)),
            best_fitness=jnp.full(args.pop, jnp.inf),
            g_best_pos=jnp.zeros(args.dims),
        )
        step = compile_spell(recipe)
        metrics = run_emergent(step, state, args.iters)
        print(metrics)
        return

    cls = BENCHMARKS[args.bench]
    t0 = time.time()
    if args.bench == "tsp":
        best, hist = run_combinatorial(cls, recipe, args.pop, args.iters)
    else:
        best, hist = run_continuous(cls, recipe, args.dims, args.pop, args.iters)
    elapsed = time.time() - t0
    print(
        {
            "bench": args.bench,
            "dims": args.dims,
            "recipe": args.recipe,
            "best": best,
            "iters": args.iters,
            "time": elapsed,
            "ms_per_iter": elapsed / args.iters * 1000,
        }
    )


if __name__ == "__main__":
    main()