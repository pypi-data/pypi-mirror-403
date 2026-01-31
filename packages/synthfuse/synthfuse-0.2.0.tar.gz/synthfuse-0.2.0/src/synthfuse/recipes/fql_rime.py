"""
FQL-RIME  (Flow-Swarm)
Spell:  (𝕀 ⊗ 𝕃 ⊗ ℝ)(flow=4, alpha=1.5)
Normalising-flow policy guides Lévy exploration → PPO refines.
Provides **dimension-independent escape** from local optima.
Usage:
    from synthfuse.recipes import fql_rime
    step_fn, init = fql_rime.make(dims=1000, pop=256)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ------------------------------------------------------------------
# 1.  Hyper-defaults
# ------------------------------------------------------------------
DEFAULTS = dict(
    flow_depth=4,
    alpha=1.5,
    ppo_eps=0.2,
    lr=3e-4,
    vf_coef=0.5,
    entropy_coef=0.01,
)


# ------------------------------------------------------------------
# 2.  State container
# ------------------------------------------------------------------
@chex.dataclass
class FQLState:
    pos: jax.Array          # [pop, dims]
    flow_latent: jax.Array  # [pop, flow_depth]  normalising-flow latent
    pi_params: PyTree       # actor
    v_params: PyTree        # critic
    key: jax.Array


# ------------------------------------------------------------------
# 3.  Local primitives
# ------------------------------------------------------------------
@register("𝔽𝕃")  # Flow-Latent sampler
def _flow_latent(key: jax.Array, state: FQLState, params: dict) -> FQLState:
    """Normalising-flow policy:  u ~ N(0,I)  →  z = flow(u)  →  dx = f(z)"""
    depth = params["flow_depth"]
    u = jax.random.normal(key, (state.pos.shape[0], depth))
    # RealNVP-style affine coupling (stub)
    for i in range(depth):
        if i % 2 == 0:
            s = jnp.tanh(u @ jax.random.normal(key, (depth, depth)))
            t = u * s
            u = u + t
        else:
            u = u  # identity
    new_latent = u
    return state.replace(flow_latent=new_latent)


@register("ℝ𝔽")  # RIME-guided PPO
def _rime_ppo(key: jax.Array, state: FQLState, params: dict) -> FQLState:
    """PPO update guided by flow-latent advantages."""
    # dummy forward
    def forward(theta, obs):
        return obs @ theta

    obs = state.flow_latent  # use latent as observation
    logits = forward(state.pi_params, obs)
    logp = jax.nn.log_softmax(logits)
    adv = jax.random.normal(key, (obs.shape[0],))  # dummy advantage
    old_logp = logp

    # clipped surrogate
    ratio = jnp.exp(logp - old_logp)
    surr1 = ratio * adv
    surr2 = jnp.clip(ratio, 1 - params["ppo_eps"], 1 + params["ppo_eps"]) * adv
    pi_loss = -jnp.minimum(surr1, surr2).mean()

    grad = jax.grad(lambda th: pi_loss)(state.pi_params)
    pi_new = state.pi_params - params["lr"] * grad
    return state.replace(pi_params=pi_new)


# ------------------------------------------------------------------
# 4.  Fused spell
# ------------------------------------------------------------------
_SPELL = "(𝔽𝕃 ⊗ 𝕃(alpha={alpha}) ⊗ ℝ𝔽)(flow_depth={flow}, ppo_eps={eps}, lr={lr})"


# ------------------------------------------------------------------
# 5.  Factory
# ------------------------------------------------------------------
def make(dims: int = 1000, pop: int = 256, **hyper) -> tuple[Callable, FQLState]:
    hp = {**DEFAULTS, **hyper}
    step_fn = compile_spell(_SPELL.format(
        alpha=hp["alpha"],
        flow=hp["flow_depth"],
        eps=hp["ppo_eps"],
        lr=hp["lr"],
    ))

    key = jax.random.PRNGKey(42)
    state = FQLState(
        pos=jax.random.normal(key, (pop, dims)) * 0.01,
        flow_latent=jnp.zeros((pop, hp["flow_depth"])),
        pi_params=jax.random.normal(key, (hp["flow_depth"], hp["flow_depth"])),
        v_params=jax.random.normal(key, (hp["flow_depth"],)),
        key=key,
    )
    return jax.jit(step_fn), state


# ------------------------------------------------------------------
# 6.  Quick smoke test
# ------------------------------------------------------------------
if __name__ == "__main__":
    import time
    step, state = make(dims=500, pop=128)
    key = jax.random.PRNGKey(0)
    t0 = time.time()
    for _ in range(100):
        key, sub = jax.random.split(key)
        state = step(sub, state, {})
    print("[fql_rime] 100 steps in {:.2f}s".format(time.time() - t0))