"""
META-Fusion – Meta-Learning + Few-Shot + Multi-Task
Symbols: 𝙼𝙰𝙼𝙻, 𝙵𝙴𝚆𝚂𝙷𝙾𝚃, 𝙼𝚄𝙻𝚃𝙸
"""
@register("𝙼𝙰𝙼𝙻")
def maml_step(key, state, params):
    return maml_adapt(state["support"], params["lr"])

@register("𝙵𝙴𝚆𝚂𝙷𝙾𝚃")
def fewshot_step(key, state, params):
    return prototypical_network(state["query"], params["n_way"])

@register("𝙼𝚄𝙻𝚃𝙸")
def multi_step(key, state, params):
    return multi_task_loss(state["tasks"], params["weights"])

spell = "(𝙼𝙰𝙼𝙻 ⊗ 𝙵𝙴𝚆𝚂𝙷𝙾𝚃 ⊗ 𝙼𝚄𝙻𝚃𝙸)(lr=0.01, n_way=5, weights=[1,1,1])"
