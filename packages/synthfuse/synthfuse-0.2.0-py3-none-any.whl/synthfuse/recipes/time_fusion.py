"""
TIME-Fusion – Deep + Classical + Causal
Symbols: 𝚃𝙸𝙼𝙴, 𝙲𝙰𝚄𝚂𝙰𝙻, 𝙿𝚁𝙾𝙿𝙷𝙴𝚃
"""
@register("𝚃𝙸𝙼𝙴")
def time_step(key, state, params):
    return temporal_fusion_transformer(state["series"], params["horizon"])

@register("𝙲𝙰𝚄𝚂𝙰𝙻")
def causal_step(key, state, params):
    return dowhy_estimate(state["graph"], params["treatment"])

@register("𝙿𝚁𝙾𝙿𝙷𝙴𝚃")
def prophet_step(key, state, params):
    return prophet_forecast(state["df"], params["seasonality"])

spell = "(𝚃𝙸𝙼𝙴 ⊗ 𝙲𝙰𝚄𝚂𝙰𝙻 ⊗ 𝙿𝚁𝙾𝙿𝙷𝙴𝚃)(horizon=30, treatment='price', seasonality=True)"
