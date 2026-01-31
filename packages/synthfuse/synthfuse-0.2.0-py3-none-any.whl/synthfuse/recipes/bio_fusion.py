"""
BIO-Fusion – AlphaFold + Evo + Single-cell
Symbols: 𝔸𝙻𝙿𝙷𝙰, 𝔼𝚅𝙾, 𝚂𝙲𝚁𝙽𝙰
Author: J. Roberto Jiménez
"""
@register("𝔸𝙻𝙿𝙷𝙰")
def alpha_step(key, state, params):
    return alphafold_predict(state["sequence"])

@register("𝔼𝚅𝙾")
def evo_step(key, state, params):
    return evo_gradients(state["tree"])

@register("𝚂𝙲𝚁𝙽𝙰")
def scrna_step(key, state, params):
    return scanpy_cluster(state["counts"])

spell = "(𝔸𝙻𝙿𝙷𝙰 ⊗ 𝔼𝚅𝙾 ⊗ 𝚂𝙲𝚁𝙽𝙰)(sequence=protein, tree=tree, counts=counts)"
