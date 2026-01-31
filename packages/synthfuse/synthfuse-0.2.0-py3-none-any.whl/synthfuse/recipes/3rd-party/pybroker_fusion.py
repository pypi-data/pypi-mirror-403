"""
PyBroker-Fusion – Algorithmic Trading via PyBroker + JAX
PyBroker operators exposed as Synth-Fuse primitives:
ℙ𝔹ℝ𝕆𝕂𝔼ℝ (strategy), 𝕊𝕋ℝ𝔸𝕋 (backtest), ℝ𝔼𝕋𝕌ℝℕ (portfolio return)
Original: https://github.com/edtechre/pybroker
Converted to single Synth-Fuse spell:
(ℙ𝔹ℝ𝕆𝕂𝔼ℝ ⊗ 𝕊𝕋ℝ𝔸𝕋 ⊗ ℝ𝔼𝕋𝕌ℝℕ)(strategy=ma_cross, lookback=20, risk_free=0.02)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  PyBroker via direct Python call (zero-copy)
# ----------------------------------------------------------
# pip install pybroker
import pybroker as pb
from pybroker import Strategy, ExecContext


# ----------------------------------------------------------
# 2.  Registered primitives (JAX-safe wrappers)
# ----------------------------------------------------------
@register("ℙ𝔹ℝ𝕆𝕂𝔼ℝ")
def pybroker_strategy_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    PyBroker strategy registration (any user function).
    Params: strategy (str), lookback (int), risk_free (float)
    Returns: signal array (JAX)
    """
    strategy_name = params["strategy"]
    lookback = params["lookback"]
    risk_free = params["risk_free"]
    prices = params["prices"]  # JAX array [T]

    # define strategy in PyBroker DSL
    def ma_cross(ctx: ExecContext):
        fast = ctx.indicator("ma_fast", lookback // 2)
        slow = ctx.indicator("ma_slow", lookback)
        if fast > slow:
            ctx.buy(shares=1.0)
        elif fast < slow:
            ctx.sell(shares=1.0)

    # run backtest (pure Python – no I/O inside step)
    strategy = Strategy(ma_cross)
    strategy.set_dates(start_date="2020-01-01", end_date="2022-01-01")
    strategy.add_indicator("ma_fast", lambda data: data.close.rolling(lookback // 2).mean())
    strategy.add_indicator("ma_slow", lambda data: data.close.rolling(lookback).mean())
    backtest = strategy.backtest(risk_free=risk_free)
    signal = backtest.signals  # pd.Series → numpy → JAX
    signal_jax = jnp.array(signal.values)

    return dict(signal=signal_jax, lookback=lookback, risk_free=risk_free)


@register("𝕊𝕋ℝ𝔸𝕋")
def pybroker_backtest_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    PyBroker backtest execution (portfolio P&L).
    Params: init_cash (float), fee (float)
    Returns: equity curve (JAX)
    """
    init_cash = params["init_cash"]
    fee = params["fee"]
    signal = state["signal"]

    # zero-fee equity curve (stub – real fee injected via param)
    equity = jnp.cumsum(signal) * init_cash * (1 - fee)
    return dict(equity=equity, init_cash=init_cash, fee=fee)


@register("ℝ𝔼𝕋𝕌ℝℕ")
def pybroker_return_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    PyBroker return calculation (Sharpe, CAGR, maxDD).
    Params: annualise (bool)
    Returns: metrics dict (JAX)
    """
    annualise = params["annualise"]
    equity = state["equity"]

    # Sharpe, CAGR, max drawdown (vectorised)
    ret = jnp.diff(equity) / equity[:-1]
    sharpe = jnp.mean(ret) / jnp.std(ret) * jnp.sqrt(252 if annualise else 1)
    cagr = (equity[-1] / equity[0]) ** (1 / (len(equity) / 252)) - 1 if annualise else equity[-1] / equity[0] - 1
    running_max = jnp.maximum.accumulate(equity)
    max_dd = jnp.max(running_max - equity) / running_max[-1]

    return dict(sharpe=sharpe, cagr=cagr, max_dd=max_dd, annualise=annualise)


# ----------------------------------------------------------
# 4.  Fused spell
# ----------------------------------------------------------
_SPELL = "(ℙ𝔹ℝ𝕆𝕂𝔼ℝ ⊗ 𝕊𝕋ℝ𝔸𝕋 ⊗ ℝ𝔼𝕋𝕌ℝℕ)(strategy=ma_cross, lookback=20, risk_free=0.02, init_cash=10000, fee=0.001, annualise=True)"


# ----------------------------------------------------------
# 5.  Factory – identical API to fql_rime
# ----------------------------------------------------------
def make_pybroker(
    prices: jax.Array,  # [T] – price series (injected static)
    strategy: str = "ma_cross",
    lookback: int = 20,
    risk_free: float = 0.02,
    init_cash: float = 10000,
    fee: float = 0.001,
    annualise: bool = True,
):
    spell = "(ℙ𝔹ℝ𝕆𝕂𝔼ℝ ⊗ 𝕊𝕋ℝ𝔸𝕋 ⊗ ℝ𝔼𝕋𝕌ℝℕ)(strategy={}, lookback={}, risk_free={}, init_cash={}, fee={}, annualise={})".format(
        strategy, lookback, risk_free, init_cash, fee, annualise
    )
    step_fn = compile_spell(spell)

    # bind static price series into params (zero-copy)
    def bound_step(key, state):
        return step_fn(key, state, {
            "prices": prices,
            "strategy": strategy,
            "lookback": lookback,
            "risk_free": risk_free,
            "init_cash": init_cash,
            "fee": fee,
            "annualise": annualise,
        })

    # initial state – empty (PyBroker fills it)
    state = dict(
        prices=prices,
        dummy=jnp.zeros(1),  # placeholder
    )

    return jax.jit(bound_step), state
