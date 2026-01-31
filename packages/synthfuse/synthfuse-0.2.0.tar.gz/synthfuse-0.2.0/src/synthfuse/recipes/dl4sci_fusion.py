"""
DL4Sci-Fusion – SciML + PINNs + Surrogates
Symbols: 𝕊ℂ𝕀𝙼𝙻, ℙ𝙸𝙽𝙽, 𝚂𝚄𝚁𝚁𝙾𝙶𝙰𝚃𝙴
"""
@register("𝕊ℂ𝕀𝙼𝙻")
def sciml_step(key, state, params):
    return jl.eval("using ModelingToolkit; solve(step, Tsit5())")

@register("ℙ𝙸𝙽𝙽")
def pinn_step(key, state, params):
    return physics_residual(params["eq"], state["u"])

@register("𝚂𝚄𝚁𝚁𝙾𝙶𝙰𝚃𝙴")
def surrogate_step(key, state, params):
    return mlp_surrogate(state["x"], params["bounds"])

spell = "(𝕊ℂ𝕀𝙼𝙻 ⊗ ℙ𝙸𝙽𝙽 ⊗ 𝚂𝚄𝚁𝚁𝙾𝙶𝙰𝚃𝙴)(eq=navier_stokes, bounds=[-1,1])"
