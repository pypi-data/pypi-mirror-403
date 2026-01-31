"""
HF-Fusion – Hugging-Face Transformers via Torch + JAX
HF operators exposed as Synth-Fuse primitives:
𝕋ℝ𝔸ℕ𝕊 (Transformer blocks), 𝔹ℙ𝔼 (tokeniser), 𝕄𝕃𝕄 (MLM head)
Original: https://github.com/huggingface/transformers
Converted to single Synth-Fuse spell:
(𝕋ℝ𝔸ℕ𝕊 ⊗ 𝔹ℙ𝔼 ⊗ 𝕄𝕃𝕄)(model=bert-base, max_len=128, temp=0.1)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  PyTorch ↔ JAX bridge (zero-copy via dlpack)
# ----------------------------------------------------------
# pip install transformers torch jax[dlpack] jaxlib
import torch
import transformers
from jax import dlpack


# ----------------------------------------------------------
# 2.  Registered primitives (JAX-safe wrappers)
# ----------------------------------------------------------
@register("𝕋ℝ𝔸ℕ𝕊")
def hf_transformer_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Hugging-Face Transformer forward pass (any model).
    Params: model (str), max_len (int)
    Returns: last-hidden-state (still PyTree)
    """
    model_name = params["model"]
    max_len = params["max_len"]
    input_ids = params["input_ids"]  # JAX array [batch, seq]

    # JAX → PyTorch (zero-copy)
    ids_torch = torch.from_dlpack(jax.dlpack.to_dlpack(input_ids))

    # load model (cached singleton)
    model = transformers.AutoModel.from_pretrained(model_name)
    model.eval()
    with torch.no_grad():
        out = model(input_ids=ids_torch)
        hidden = out.last_hidden_state  # [B, L, D]

    # PyTorch → JAX (zero-copy)
    hidden_jax = jax.dlpack.from_dlpack(hidden.detach().contiguous())

    return dict(hidden=hidden_jax, logits=None)  # logits added next


@register("𝔹ℙ𝔼")
def hf_bpe_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Hugging-Face BPE tokeniser (any tokenizer).
    Params: tokenizer (str), max_len (int)
    Returns: input_ids, attention_mask (JAX arrays)
    """
    tokenizer_name = params["tokenizer"]
    max_len = params["max_len"]
    texts = params["texts"]  # list[str]

    tok = transformers.AutoTokenizer.from_pretrained(tokenizer_name)
    encoded = tok(texts, truncation=True, padding="max_length", max_length=max_len, return_tensors="pt")
    ids = encoded.input_ids  # [B, L]
    mask = encoded.attention_mask  # [B, L]

    # PyTorch → JAX
    ids_jax = jax.dlpack.from_dlpack(ids.detach().contiguous())
    mask_jax = jax.dlpack.from_dlpack(mask.detach().contiguous())

    return dict(input_ids=ids_jax, attention_mask=mask_jax)


@register("𝕄𝕃𝕄")
def hf_mlm_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Hugging-Face MLM head (any masked-LM model).
    Params: temp (float) – temperature for sampling
    Returns: logits, loss
    """
    temp = params["temp"]
    hidden = state["hidden"]  # [B, L, D] from 𝕋ℝ𝔸ℕ𝕊 step
    model_name = params["model"]

    model = transformers.AutoModelForMaskedLM.from_pretrained(model_name)
    model.eval()
    with torch.no_grad():
        logits = model(inputs_embeds=torch.from_dlpack(jax.dlpack.to_dlpack(hidden))).logits
        logits_jax = jax.dlpack.from_dlpack(logits.detach().contiguous())

    # temperature-scaled loss
    loss = jax.nn.cross_entropy(logits_jax / temp, state["target_ids"])

    return dict(logits=logits_jax, loss=loss)


# ----------------------------------------------------------
# 4.  Fused spell
# ----------------------------------------------------------
_SPELL = "(𝕋ℝ𝔸ℕ𝕊 ⊗ 𝔹ℙ𝔼 ⊗ 𝕄𝕃𝕄)(model=bert-base, tokenizer=bert-base, max_len=128, temp=0.1)"


# ----------------------------------------------------------
# 5.  Factory – identical API to fql_rime
# ----------------------------------------------------------
def make_hf(
    texts: list[str],  # injected static
    model: str = "bert-base-uncased",
    max_len: int = 128,
    temp: float = 0.1,
):
    spell = "(𝕋ℝ𝔸ℕ𝕊 ⊗ 𝔹ℙ𝔼 ⊗ 𝕄𝕃𝕄)(model={}, tokenizer={}, max_len={}, temp={})".format(
        model, model, max_len, temp
    )
    step_fn = compile_spell(spell)

    # tokenise once (static input)
    tok = transformers.AutoTokenizer.from_pretrained(model)
    encoded = tok(texts, truncation=True, padding="max_length", max_length=max_len, return_tensors="pt")
    target_ids = jnp.array(encoded.input_ids)  # MLM targets (unchanged)

    # bind static inputs into params
    def bound_step(key, state):
        return step_fn(key, state, {
            "texts": texts,
            "model": model,
            "tokenizer": model,
            "max_len": max_len,
            "temp": temp,
            "target_ids": target_ids,
        })

    # initial state – empty (HF fills it)
    state = dict(
        texts=texts,
        target_ids=target_ids,
        dummy=jnp.zeros(1),  # placeholder
    )

    return jax.jit(bound_step), state
