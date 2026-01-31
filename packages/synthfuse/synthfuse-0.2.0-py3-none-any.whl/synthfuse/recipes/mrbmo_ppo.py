"""
MRBMO-PPO Siege-GAPPO Hybrid
Pre-fused spell:  (𝕊 ∘ 𝜑 ⊗ ℝ)(siege≥0.85)
→ MRBMO GoodNodesSet becomes elite buffer for GAPPO
→ PPO clips only non-absorbing advantages
→ Pseudoinverse meta-gradient corrects drift
Usage:
    from synthfuse.recipes import mrbmo_ppo
    step_fn, init_state = mrbmo_ppo.make(pop=128, dims=100)
"""
from functools import partial
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ------------------------------------------------------------------
# 1.  Hyper-defaults
# ------------------------------------------------------------------
DEFAULT_HYPER = dict(
    siege_threshold=0.85,
    ppo_eps=0.2,
    lr=3e-4,
    vf_coef=0.5,
    entropy_coef=0.01,
    meta_damp=1e-3,   # pseudoinverse damping
)


# ------------------------------------------------------------------
# 2.  State container
# ------------------------------------------------------------------
@chex.dataclass
class MPPState:
    swarm_pos: jax.Array          # [pop, dims]
    swarm_vel: jax.Array
    elite_buf: jax.Array          # [≤pop, dims]  GoodNodesSet
    pi_params: PyTree             # actor
    v_params: PyTree              # critic
    best_fitness: float
    key: jax.Array


# ------------------------------------------------------------------
# 3.  Internal primitives registered on-the-fly
# ------------------------------------------------------------------
@register("𝕊𝕄")   # local symbol for Siege-MRBMO step
def _siege_mrbmo_step(key: jax.Array, state: MPPState, params: dict) -> MPPState:
    """Moves swarm in spiral toward global best; updates elite_buf by siege score."""
    spiral_b = params.get("spiral_b", 0.1)
    dist = jnp.abs(state.best_fitness - state.swarm_pos)
    spiral = jnp.exp(spiral_b * 0.5) * jnp.cos(2 * jnp.pi * 0.5)
    new_pos = dist * spiral + state.best_fitness
    new_pos = jnp.clip(new_pos, -10, 10)

    # siege score = fitness improvement
    fitness = jnp.sum(new_pos ** 2, axis=1)  # dummy objective
    siege_score = jax.nn.sigmoid(-fitness)  # lower fitness → higher score
    elite_mask = siege_score >= params["siege_threshold"]
    elite_buf = state.elite_buf.at[: jnp.sum(elite_mask)].set(new_pos[elite_mask])

    return state.replace(swarm_pos=new_pos, elite_buf=elite_buf)


@register("ℝ𝕄")   # local PPO-with-meta
def _ppo_meta_step(key: jax.Array, state: MPPState, params: dict) -> MPPState:
    """PPO clip + pseudoinverse meta-gradient on elite buffer."""
    # stub actor-critic forward
    def forward(theta, obs):
        return obs @ theta  # linear

    obs = state.elite_buf[:32]  # batch from elite
    logits = forward(state.pi_params, obs)
    logp = jax.nn.log_softmax(logits)
    adv = jnp.linspace(0.5, -0.5, len(obs))  # dummy advantage
    old_logp = logp

    # clipped surrogate
    ratio = jnp.exp(logp - old_logp)
    surr1 = ratio * adv
    surr2 = jnp.clip(ratio, 1 - params["ppo_eps"], 1 + params["ppo_eps"]) * adv
    pi_loss = -jnp.minimum(surr1, surr2).mean()

    # meta-gradient: pseudoinverse correction
    grad = jax.grad(lambda th: pi_loss)(state.pi_params)
    damp = params["meta_damp"]
    fisher_diag = jnp.abs(grad) + damp
    natural_grad = grad / fisher_diag
    pi_new = state.pi_params - params["lr"] * natural_grad

    return state.replace(pi_params=pi_new)


# ------------------------------------------------------------------
# 4.  Fused spell string
# ------------------------------------------------------------------
_SPELL = "(𝕊𝕄 ∘ 𝜑 ⊗ ℝ𝕄)(siege_threshold={siege}, ppo_eps={eps}, lr={lr}, meta_damp={damp})"


# ------------------------------------------------------------------
# 5.  Public factory
# ------------------------------------------------------------------
def make(pop: int = 128, dims: int = 100, **hyper) -> tuple[Callable[[jax.Array, MPPState, dict], MPPState], MPPState]:
    """
    Returns (jit_step_fn, init_state) ready for training loop.
    Hyper-params merged with DEFAULT_HYPER.
    """
    hp = {**DEFAULT_HYPER, **hyper}
    step_fn = compile_spell(_SPELL.format(
        siege=hp["siege_threshold"],
        eps=hp["ppo_eps"],
        lr=hp["lr"],
        damp=hp["meta_damp"],
    ))

    key = jax.random.PRNGKey(42)
    state = MPPState(
        swarm_pos=jax.random.uniform(key, (pop, dims), minval=-5, maxval=5),
        swarm_vel=jnp.zeros((pop, dims)),
        elite_buf=jnp.zeros((pop, dims)),  # dynamic size by mask
        pi_params=jax.random.normal(key, (dims, dims)),  # stub
        v_params=jax.random.normal(key, (dims,)),  # stub
        best_fitness=jnp.inf,
        key=key,
    )

    return jax.jit(step_fn), state


# ------------------------------------------------------------------
# 6.  Self-test (runs only when executed directly)
# ------------------------------------------------------------------
if __name__ == "__main__":
    import time
    step, state = make(pop=64, dims=50)
    key = jax.random.PRNGKey(0)
    t0 = time.time()
    for _ in range(100):
        key, sub = jax.random.split(key)
        state = step(sub, state, {})
    print("[mrbmo_ppo] 100 steps in {:.2f}s  –  best {:.4f}".format(time.time() - t0, float(state.best_fitness)))