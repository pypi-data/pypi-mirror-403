"""
Pure-JAX RL primitives for ALCHEM-J registry
All functions obey:  StepFn(key, x, params) -> new_x
where x can be any PyTree (params, grads, buffers, …)
"""
import jax
import jax.numpy as jnp
import jax.random as jr
import optax
from alchemj.registry import register

# ------------------------------------------------------------------
# helper: tree utils
# ------------------------------------------------------------------
tree_map = jax.tree.map
tree_add = lambda t1, t2: tree_map(jnp.add, t1, t2)
tree_sub = lambda t1, t2: tree_map(jnp.subtract, t1, t2)
tree_scale = lambda t, s: tree_map(lambda x: x * s, t)

# ------------------------------------------------------------------
# ℝ  –  PPO clipped surrogate step  (actor-critic params PyTree)
# ------------------------------------------------------------------
@register("ℝ")
def ppo_step(key: jax.Array, x: dict, params: dict) -> dict:
    """
    Minimal single-step PPO update (no GAE, no batch dim).
    x = dict(pi_params, v_params, logp_old, adv, ret)
    params = dict(eps, lr, vf_coef, entropy_coef)
    """
    eps = params.get("eps", 0.2)
    lr = params.get("lr", 3e-4)
    vf_coef = params.get("vf_coef", 0.5)
    ent_coef = params.get("entropy_coef", 0.01)

    pi_params, v_params, logp_old, adv, ret = (
        x["pi_params"], x["v_params"], x["logp_old"], x["adv"], x["ret"]
    )

    # dummy network forward (user replaces with real apply_fn)
    def pi_logp_entropy(theta, obs):
        # linear policy stub: logits = obs @ theta
        logits = obs @ theta
        logp = jax.nn.log_softmax(logits)
        prob = jnp.exp(logp)
        entropy = -jnp.sum(prob * logp)
        return logp, entropy

    def v_forward(theta, obs):
        return obs @ theta  # linear value stub

    obs = x.get("obs", jnp.ones_like(adv))  # dummy obs

    # actor loss
    logp, entropy = pi_logp_entropy(pi_params, obs)
    ratio = jnp.exp(logp - logp_old)
    surr1 = ratio * adv
    surr2 = jnp.clip(ratio, 1.0 - eps, 1.0 + eps) * adv
    pi_loss = -jnp.minimum(surr1, surr2) - ent_coef * entropy

    # critic loss
    v_pred = v_forward(v_params, obs)
    vf_loss = 0.5 * jnp.mean((v_pred - ret) ** 2)

    total_loss = pi_loss + vf_coef * vf_loss

    # simple SGD step (user can swap in adam via optax)
    grad = jax.grad(lambda theta: total_loss)(pi_params)
    pi_params_new = tree_sub(pi_params, tree_scale(grad, lr))

    return dict(
        pi_params=pi_params_new,
        v_params=v_params,  # critic frozen for brevity
        logp_old=logp,
        adv=adv,
        ret=ret,
        obs=obs,
    )


# ------------------------------------------------------------------
# Deep-Q step (single state, no replay buffer)
# ------------------------------------------------------------------
@register("𝔻")
def dqn_step(key: jax.Array, x: dict, params: dict) -> dict:
    """
    x = dict(q_params, obs, action, reward, next_obs, done, gamma)
    params = dict(lr, grad_clip)
    """
    lr = params.get("lr", 1e-3)
    clip = params.get("grad_clip", 1.0)
    gamma = x["gamma"]

    def q_fn(theta, obs):
        # linear Q stub
        return obs @ theta

    q = q_fn(x["q_params"], x["obs"])
    q_next = q_fn(x["q_params"], x["next_obs"])
    target = x["reward"] + gamma * jnp.max(q_next) * (1 - x["done"])
    td_error = target - q[x["action"]]

    loss = 0.5 * td_error**2
    grad = jax.grad(lambda th: loss)(x["q_params"])
    if clip:
        grad = tree_map(lambda g: jnp.clip(g, -clip, clip), grad)
    q_params_new = tree_sub(x["q_params"], tree_scale(grad, lr))

    return dict(
        q_params=q_params_new,
        obs=x["next_obs"],
        action=x["action"],
        reward=x["reward"],
        next_obs=x["next_obs"],
        done=x["done"],
        gamma=gamma,
    )


# ------------------------------------------------------------------
// A2C step (actor-critic with entropy bonus)
// ------------------------------------------------------------------
@register("𝔸")
def a2c_step(key: jax.Array, x: dict, params: dict) -> dict:
    """
    x = dict(pi_params, v_params, obs, action, adv, ret, entropy_coef)
    params = dict(lr)
    """
    lr = params.get("lr", 7e-4)
    ent_coef = x.get("entropy_coef", 0.01)

    def pi_logp_entropy(theta, obs):
        logits = obs @ theta
        logp = jax.nn.log_softmax(logits)
        prob = jnp.exp(logp)
        entropy = -jnp.sum(prob * logp)
        return logp, entropy

    def v_forward(theta, obs):
        return obs @ theta

    obs, action, adv, ret = x["obs"], x["action"], x["adv"], x["ret"]

    logp, entropy = pi_logp_entropy(x["pi_params"], obs)
    pi_loss = -logp[action] * adv - ent_coef * entropy

    v_pred = v_forward(x["v_params"], obs)
    vf_loss = 0.5 * (v_pred - ret) ** 2

    total_loss = pi_loss + vf_loss

    pi_grad = jax.grad(lambda th: total_loss)(x["pi_params"])
    v_grad = jax.grad(lambda th: total_loss)(x["v_params"])

    pi_params_new = tree_sub(x["pi_params"], tree_scale(pi_grad, lr))
    v_params_new = tree_sub(x["v_params"], tree_scale(v_grad, lr))

    return dict(
        pi_params=pi_params_new,
        v_params=v_params_new,
        obs=obs,
        action=action,
        adv=adv,
        ret=ret,
        entropy_coef=ent_coef,
    )