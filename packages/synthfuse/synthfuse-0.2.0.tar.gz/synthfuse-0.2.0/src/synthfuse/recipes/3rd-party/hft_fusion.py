"""
HFT-Fusion – High-Frequency Trading via ML-HFT + JAX
ML-HFT operators exposed as Synth-Fuse primitives:
𝙷𝙵𝚃 (tick data), 𝚃𝙸𝙲𝙺 (order-book), 𝙱𝙾𝙾𝙺 (trade signal)
Original: https://github.com/bradleyboyuyang/ML-HFT
Converted to single Synth-Fuse spell:
(𝙷𝙵𝚃 ⊗ 𝚃𝙸𝙲𝙺 ⊗ 𝙱𝙾𝙾𝙺)(window=100, threshold=0.01, latency=1e-6)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  ML-HFT via PythonCall (zero-copy)
# ----------------------------------------------------------
# pip install ml-hft juliacall python-call
try:
    from juliacall import Main as jl
except ImportError as e:
    raise RuntimeError("pip install ml-hft juliacall python-call") from e


# ----------------------------------------------------------
# 2.  Registered primitives (JAX-safe wrappers)
# ----------------------------------------------------------
@register("𝙷𝙵𝚃")
def hft_tick_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    ML-HFT tick data processing (any exchange).
    Params: window (int), threshold (float), latency (float)
    Returns: tick features (JAX array)
    """
    window = params["window"]
    threshold = params["threshold"]
    latency = params["latency"]
    ticks = params["ticks"]  # JAX array [n, 5] (price, volume, time, bid, ask)

    # call ML-HFT via Julia (zero-copy – arrays stay in memory)
    jl.seval("using MLHFT")
    jl.window = window
    jl.threshold = threshold
    jl.latency = latency
    jl.ticks = ticks
    jl.seval("""
        using MLHFT: process_ticks
        features = process_ticks(ticks, window=window, threshold=threshold, latency=latency)
    """)
    features = jl.features  # PyTree (JAX array)

    return dict(features=features, window=window, threshold=threshold, latency=latency)


@register("𝚃𝙸𝙲𝙺")
def tick_order_book_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    ML-HFT order-book reconstruction (LOB).
    Params: levels (int), spread (float)
    Returns: order-book tensor (JAX array)
    """
    levels = params["levels"]
    spread = params["spread"]
    features = state["features"]  # from 𝙷𝙵𝚃 step

    # call ML-HFT via Julia (zero-copy)
    jl.seval("using MLHFT: reconstruct_lob")
    jl.levels = levels
    jl.spread = spread
    jl.features = features
    jl.seval("""
        using MLHFT: reconstruct_lob
        lob = reconstruct_lob(features, levels=levels, spread=spread)
    """)
    lob = jl.lob  # PyTree (JAX array)

    return dict(lob=lob, levels=levels, spread=spread)


@register("𝙱𝙾𝙾𝙺")
def hft_trade_signal_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    ML-HFT trade signal generation (any strategy).
    Params: signal (str), confidence (float)
    Returns: trade signal (JAX array)
    """
    signal = params["signal"]
    confidence = params["confidence"]
    lob = state["lob"]  # from 𝚃𝙸𝙲𝙺 step

    # call ML-HFT via Julia (zero-copy)
    jl.seval("using MLHFT: generate_signal")
    jl.signal = signal
    jl.confidence = confidence
    jl.lob = lob
    jl.seval("""
        using MLHFT: generate_signal
        trade = generate_signal(lob, signal=signal, confidence=confidence)
    """)
    trade = jl.trade  # PyTree (JAX array)

    return dict(trade=trade, signal=signal, confidence=confidence)


# ----------------------------------------------------------
# 4.  Fused spell
# ----------------------------------------------------------
_SPELL = "(𝙷𝙵𝚃 ⊗ 𝚃𝙸𝙲𝙺 ⊗ 𝙱𝙾𝙾𝙺)(window=100, threshold=0.01, latency=1e-6, levels=10, spread=0.01, signal=ma_cross, confidence=0.95)"


# ----------------------------------------------------------
# 5.  Factory – identical API to fql_rime
# ----------------------------------------------------------
def make_hft(
    ticks: jax.Array,  # [n, 5] – tick data (injected static)
    window: int = 100,
    threshold: float = 0.01,
    latency: float = 1e-6,
    levels: int = 10,
    spread: float = 0.01,
    signal: str = "ma_cross",
    confidence: float = 0.95,
):
    spell = "(𝙷𝙵𝚃 ⊗ 𝚃𝙸𝙲𝙺 ⊗ 𝙱𝙾𝙾𝙺)(window={}, threshold={}, latency={}, levels={}, spread={}, signal={}, confidence={})".format(
        window, threshold, latency, levels, spread, signal, confidence
    )
    step_fn = compile_spell(spell)

    # bind static tick data into params (zero-copy)
    def bound_step(key, state):
        return step_fn(key, state, {
            "ticks": ticks,
            "window": window,
            "threshold": threshold,
            "latency": latency,
            "levels": levels,
            "spread": spread,
            "signal": signal,
            "confidence": confidence,
        })

    # initial state – empty (ML-HFT fills it)
    state = dict(
        ticks=ticks,
        dummy=jnp.zeros(1),  # placeholder
    )

    return jax.jit(bound_step), state
