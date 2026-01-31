"""
SYN-Fusion – Synthetic + DP + GANs
Symbols: 𝚂𝚈𝙽, 𝔻ℙ, 𝙶𝙰𝙽
"""
@register("𝚂𝚈𝙽")
def syn_step(key, state, params):
    return gan_generate(state["noise"], params["dp_epsilon"])

@register("𝔻ℙ")
def dp_step(key, state, params):
    return dp_sanitize(state["raw"], params["epsilon"])

@register("𝙶𝙰𝙽")
def gan_step(key, state, params):
    return diffusion_sample(state["latent"], params["temp"])

spell = "(𝚂𝚈𝙽 ⊗ 𝔻ℙ ⊗ 𝙶𝙰𝙽)(dp_epsilon=1.0, temp=0.8)"
