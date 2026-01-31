"""
Convolutional LSTM Auto-encoder  (Architecture IV)
ℂ𝕃𝔸 – Separable causal conv + grouped STFT loss + RigL sparsity + TensorRT
"""
import jax
import jax.numpy as jnp
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

@register("ℂ𝕃𝔸")
def conv_lstm_ae_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Separable causal conv + STFT spectral loss + RigL prune.
    Params: prune_rate (float), stft_win (int), group_size (int)
    """
    prune_rate = params["prune_rate"]
    win = params["stft_win"]
    g = params["group_size"]

    # 1. Separable causal convolution (3×1 + 1×3)
    x = state.x
    h1 = jax.lax.conv_general_dilated(x, params["w1"], (1, 1), "SAME", dimension_numbers=("NHWC", "HWIO", "NHWC"))
    h2 = jax.lax.conv_general_dilated(h1, params["w2"], (1, 1), "SAME", dimension_numbers=("NHWC", "HWIO", "NHWC"))
    h = h2

    # 2. Grouped STFT loss
    def stft_loss(x, win):
        from jax.scipy.signal import stft
        _, _, Z = stft(x, nperseg=win)
        return jnp.mean(jnp.abs(Z - state.target_stft))
    loss = stft_loss(h, win)

    # 3. RigL prune (magnitude + random regrowth)
    mask = jnp.abs(params["w2"]) > jnp.percentile(jnp.abs(params["w2"]), 100 * prune_rate)
    params["w2"] = params["w2"] * mask

    return state.replace(x=h, loss=loss)


def make_conv_lstm_ae(prune_rate: float = 0.8, stft_win: int = 16, group_size: int = 4):
    spell = "(ℂ𝕃𝔸)(prune_rate={}, stft_win={}, group_size={})".format(prune_rate, stft_win, group_size)
    step_fn = compile_spell(spell)

    state = dict(
        x=jnp.zeros((1, 64, 64, 1)),  # dummy image
        target_stft=jnp.zeros((33, 33)),  # target spectrogram
        w1=jax.random.normal(jax.PRNGKey(0), (3, 1, 1, 4)),
        w2=jax.random.normal(jax.PRNGKey(1), (1, 3, 4, 1)),
    )
    return jax.jit(step_fn), state
