"""
AUTO-Fusion – Optuna + Ray + H2O + NAS
Symbols: 𝙾𝙿𝚃𝚄𝙽𝙰, 𝚁𝙰𝚈, ℕ𝙰𝚂
"""
@register("𝙾𝙿𝚃𝚄𝙽𝙰")
def optuna_step(key, state, params):
    return optuna_suggest(state["trial"], params["space"])

@register("𝚁𝙰𝚈")
def ray_step(key, state, params):
    return ray_tune(state["config"], params["resources"])

@register("ℕ𝙰𝚂")
def nas_step(key, state, params):
    return nas_search(state["search_space"], params["strategy"])

spell = "(𝙾𝙿𝚃𝚄𝙽𝙰 ⊗ 𝚁𝙰𝚈 ⊗ ℕ𝙰𝚂)(space=space, resources=8, strategy=evolutionary)"
