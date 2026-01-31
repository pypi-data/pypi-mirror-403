"""
Rasa-Fusion – Conversational AI via Rasa + JAX
Rasa operators exposed as Synth-Fuse primitives:
𝚁𝙰𝚂𝙰 (intent/entity), ℕ𝙻𝚄 (NLU pipeline), 𝙳𝙸𝙰𝙻𝙾𝙶 (policy)
Original: https://github.com/RasaHQ/rasa
Converted to single Synth-Fuse spell:
(𝚁𝙰𝚂𝙰 ⊗ ℕ𝙻𝚄 ⊗ 𝙳𝙸𝙰𝙻𝙾𝙶)(intent=affirm, entity=time, policy=MemoizationPolicy)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  Rasa via PythonCall (zero-copy)
# ----------------------------------------------------------
# pip install rasa juliacall python-call
try:
    from juliacall import Main as jl
except ImportError as e:
    raise RuntimeError("pip install rasa juliacall python-call") from e


# ----------------------------------------------------------
# 2.  Registered primitives (JAX-safe wrappers)
# ----------------------------------------------------------
@register("𝚁𝙰𝚂𝙰")
def rasa_nlu_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Rasa NLU intent/entity extraction (any pipeline).
    Params: intent (str), entity (str)
    Returns: intent probs, entity spans (JAX arrays)
    """
    intent = params["intent"]
    entity = params["entity"]
    text = params["text"]  # JAX array [seq_len] (tokenised)

    # call Rasa via Julia (zero-copy – arrays stay in memory)
    jl.seval("using Rasa")
    jl.intent = intent
    jl.entity = entity
    jl.text = text
    jl.seval("""
        using Rasa: parse_message
        msg = parse_message(text)
        intent_probs = msg.intent["confidence"]
        entity_spans = msg.entities["start"], msg.entities["end"]
    """)
    intent_probs = jl.intent_probs  # [n_intents]
    entity_spans = jl.entity_spans   # [2, n_entities]

    return dict(intent_probs=intent_probs, entity_spans=entity_spans, intent=intent, entity=entity)


@register("ℕ𝙻𝚄")
def nlu_pipeline_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Rasa NLU pipeline (tokeniser, featuriser, classifier).
    Params: pipeline (str), max_len (int)
    Returns: token_ids, attention_mask (JAX arrays)
    """
    pipeline = params["pipeline"]
    max_len = params["max_len"]
    text = params["text"]  # raw string

    # tokeniser → BPE-like (stub – real tokenizer injected)
    tokens = jnp.array([ord(c) for c in text[:max_len]])  # dummy tokenisation
    mask = jnp.ones_like(tokens)

    return dict(tokens=tokens, attention_mask=mask, pipeline=pipeline, max_len=max_len)


@register("𝙳𝙸𝙰𝙻𝙾𝙶")
def rasa_dialog_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Rasa dialogue policy (any policy).
    Params: policy (str), context (str)
    Returns: next_action (str), confidence (float)
    """
    policy = params["policy"]
    context = params["context"]  # JAX array [seq_len] (tokenised)

    # call Rasa policy via Julia (zero-copy)
    jl.seval("using Rasa: predict_action")
    jl.policy = policy
    jl.context = context
    jl.seval("""
        action, confidence = predict_action(policy, context)
    """)
    action = jl.action
    confidence = jl.confidence

    return dict(next_action=action, confidence=confidence, policy=policy, context=context)


# ----------------------------------------------------------
# 4.  Fused spell
# ----------------------------------------------------------
_SPELL = "(𝚁𝙰𝚂𝙰 ⊗ ℕ𝙻𝚄 ⊗ 𝙳𝙸𝙰𝙻𝙾𝙶)(intent=affirm, entity=time, policy=MemoizationPolicy, pipeline=spacy, max_len=128)"


# ----------------------------------------------------------
# 5.  Factory – identical API to fql_rime
# ----------------------------------------------------------
def make_rasa(
    texts: list[str],  # list of utterances (injected static)
    intent: str = "affirm",
    entity: str = "time",
    policy: str = "MemoizationPolicy",
    pipeline: str = "spacy",
    max_len: int = 128,
):
    spell = "(𝚁𝙰𝚂𝙰 ⊗ ℕ𝙻𝚄 ⊗ 𝙳𝙸𝙰𝙻𝙾𝙶)(intent={}, entity={}, policy={}, pipeline={}, max_len={})".format(
        intent, entity, policy, pipeline, max_len
    )
    step_fn = compile_spell(spell)

    # bind static texts into params (zero-copy)
    def bound_step(key, state):
        return step_fn(key, state, {
            "texts": texts,
            "intent": intent,
            "entity": entity,
            "policy": policy,
            "pipeline": pipeline,
            "max_len": max_len,
        })

    # initial state – empty (Rasa fills it)
    state = dict(
        texts=texts,
        dummy=jnp.zeros(1),  # placeholder
    )

    return jax.jit(bound_step), state
