"""
ROBO-Fusion – RL + Planning + Sim
Symbols: 𝚁𝙻, 𝙿𝙻𝙰𝙽, 𝙼𝚄𝙹𝙾
"""
@register("𝚁𝙻")
def rl_step(key, state, params):
    return ppo_update(state["trajectory"], params["clip"])

@register("𝙿𝙻𝙰𝙽")
def plan_step(key, state, params):
    return motion_plan(state["scene"], params["goal"])

@register("𝙼𝚄𝙹𝙾")
def mujoco_step(key, state, params):
    return mujoco_step(state["sim"], params["action"])

spell = "(𝚁𝙻 ⊗ 𝙿𝙻𝙰𝙽 ⊗ 𝙼𝚄𝙹𝙾)(clip=0.2, goal=goal, action=action)"
