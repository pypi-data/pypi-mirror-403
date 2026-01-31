"""
GRAPH-Fusion – PyG + DGL + Combinatorial
Symbols: 𝔾ℝ𝔸𝙿𝙷, ℂ𝙾𝙼𝙱, 𝙺𝙽𝙾𝚆
"""
@register("𝔾ℝ𝔸𝙿𝙷")
def graph_step(key, state, params):
    return pyg_gnn(state["graph"], params["layers"])

@register("ℂ𝙾𝙼𝙱")
def comb_step(key, state, params):
    return ortools_solve(state["problem"], params["method"])

@register("𝙺𝙽𝙾𝚆")
def know_step(key, state, params):
    return kg_embed(state["triples"], params["dim"])

spell = "(𝔾ℝ𝔸𝙿𝙷 ⊗ ℂ𝙾𝙼𝙱 ⊗ 𝙺𝙽𝙾𝚆)(layers=3, method=branch_bound, dim=64)"
