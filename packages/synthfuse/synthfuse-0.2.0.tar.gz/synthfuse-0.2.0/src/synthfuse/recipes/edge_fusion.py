"""
EDGE-Fusion – TinyML + Compression + On-Device
Symbols: 𝚃𝙸𝙽𝚈, 𝙲𝙾𝙼𝙿𝚁𝙴𝚂𝚂, 𝙾𝙽𝙳𝙴𝚅
"""
@register("𝚃𝙸𝙽𝚈")
def tiny_step(key, state, params):
    return tflite_convert(state["model"], params["quantise"])

@register("𝙲𝙾𝙼𝙿𝚁𝙴𝚂𝚂")
def compress_step(key, state, params):
    return prune_and_quantise(state["weights"], params["sparsity"])

@register("𝙾𝙽𝙳𝙴𝚅")
def ondev_step(key, state, params):
    return on_device_train(state["data"], params["epochs"])

spell = "(𝚃𝙸𝙽𝚈 ⊗ 𝙲𝙾𝙼𝙿𝚁𝙴𝚂𝚂 ⊗ 𝙾𝙽𝙳𝙴𝚅)(quantise=True, sparsity=0.8, epochs=1)"
