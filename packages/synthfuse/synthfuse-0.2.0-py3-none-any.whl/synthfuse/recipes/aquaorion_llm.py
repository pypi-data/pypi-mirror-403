"""
AquaOrion-LLM
AquaForte + Orion-RAG + LLM4DSE
Automated theorem proving & knowledge retrieval for AI-driven problem solving.
"""
import jax
import jax.numpy as jnp
import chex
from typing import Any
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ---------- external deps (pip install sl-gme) -------------
try:
    from sl_gme import AquaForteSession, OrionRAGIndex, LLM4DSEClient
except ImportError as e:
    raise RuntimeError("pip install sl-gme>=0.2.0") from e

# ----------------------------------------------------------
# 1.  State container
# ----------------------------------------------------------
@chex.dataclass
class AquaOrionLLMState:
    theorem_id: jax.Array          # int scalar
    logical_state: jax.Array       # AquaForte latent
    rag_context: jax.Array         # Orion-RAG embedding
    llm_hidden: jax.Array          # LLM4DSE hidden state
    step_counter: int


# ----------------------------------------------------------
# 2.  Registered primitives (JIT-safe wrappers)
# ----------------------------------------------------------
@register("𝔸𝔽")  # AquaForte
def aquaforte_step(key: jax.Array, state: AquaOrionLLMState, params: dict) -> AquaOrionLLMState:
    """Logical constraint solving – returns updated latent."""
    client = params["aquaforte_client"]        # injected at recipe build
    latent_new = client.solve_step(state.logical_state)  # pure JAX call
    return state.replace(logical_state=latent_new)


@register("𝕆ℝ")  # Orion-RAG
def orion_rag_step(key: jax.Array, state: AquaOrionLLMState, params: dict) -> AquaOrionLLMState:
    """Retrieve relevant theorems via Weierstrass field."""
    index = params["rag_index"]
    query = state.logical_state
    emb = index.retrieve(query, temperature=params.get("rag_temp", 0.7))
    return state.replace(rag_context=emb)


@register("𝕃𝟜𝔻")  # LLM4DSE
def llm4dse_step(key: jax.Array, state: AquaOrionLLMState, params: dict) -> AquaOrionLLMState:
    """Generate/refine hypothesis from (logic + rag)."""
    client = params["llm4dse_client"]
    concat = jnp.concatenate([state.logical_state, state.rag_context])
    hidden_new = client.generate_hidden(concat, max_len=params.get("max_len", 128))
    return state.replace(llm_hidden=hidden_new)


# ----------------------------------------------------------
# 3.  Fused spell
# ----------------------------------------------------------
_SPELL = "(𝔸𝔽 ⊗ 𝕆ℝ ⊗ 𝕃𝟜𝔻)(rag_temp=0.7, max_len=128)"


# ----------------------------------------------------------
# 4.  Public factory (like any recipe)
# ----------------------------------------------------------
def make_aquaorion_llm(
    model_name: str = "microsoft/DialoGPT-medium",
    index_path: str = "orion_rag_index",
    max_len: int = 128,
):
    """
    Returns (jit_step_fn, init_state) ready for Synth-Fuse pipeline.
    External clients are **injected as static params** – still JIT-safe.
    """
    step_fn = compile_spell(_SPELL)

    # build external clients (done once, outside JIT)
    af_client = AquaForteSession(model_name)
    rag_idx = OrionRAGIndex(index_path)
    llm_client = LLM4DSEClient(model_name)

    # initial state – all zeros, shapes known at compile time
    d = 768  # latent dim (matches model)
    state = AquaOrionLLMState(
        theorem_id=jnp.array(0),
        logical_state=jnp.zeros(d),
        rag_context=jnp.zeros(d),
        llm_hidden=jnp.zeros(d),
        step_counter=0,
    )

    # bind external objects into params (static)
    def bound_step(key, state):
        return step_fn(key, state, {
            "aquaforte_client": af_client,
            "rag_index": rag_idx,
            "llm4dse_client": llm_client,
            "rag_temp": 0.7,
            "max_len": max_len,
        })

    return jax.jit(bound_step), state


# ----------------------------------------------------------
# 5.  Micro-bench (theorem-proving accuracy proxy)
# ----------------------------------------------------------
if __name__ == "__main__":
    import time
    step, state = make_aquaorion_llm()
    key = jax.random.PRNGKey(42)
    t0 = time.time()
    for i in range(50):
        key, sub = jax.random.split(key)
        state = step(sub, state)
    print("[AquaOrion-LLM] 50 steps in {:.2f}s – theorem_id={}".format(
        time.time() - t0, int(state.theorem_id)))
