"""
CRYPTO-Fusion – MPC + FHE + ML
Symbols: 𝙼𝙿𝙲, 𝙵𝙷𝙴, 𝙲𝚁𝚈𝙿𝚃𝙾
"""
@register("𝙼𝙿𝙲")
def mpc_step(key, state, params):
    return mpc_aggregate(state["shares"], params["parties"])

@register("𝙵𝙷𝙴")
def fhe_step(key, state, params):
    return fhe_evaluate(state["ciphertext"], params["circuit"])

@register("𝙲𝚁𝚈𝙿𝚃𝙾")
def crypto_step(key, state, params):
    return concrete_ml_predict(state["encrypted_x"], params["model"])

spell = "(𝙼𝙿𝙲 ⊗ 𝙵𝙷𝙴 ⊗ 𝙲𝚁𝚈𝙿𝚃𝙾)(parties=3, circuit=add, model=lr)"
