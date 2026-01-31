"""
MLJ-Fusion – Julia MLJ via PythonCall + JAX
Julia-MLJ operators exposed as Synth-Fuse primitives:
𝕄𝕃𝕁 (model), 𝕋𝕌ℕ𝔼 (hyper-param tuning), 𝕍𝔸𝕃 (cross-validation)
Original: https://github.com/JuliaAI/MLJ.jl
Converted to single Synth-Fuse spell:
(𝕄𝕃𝕁 ⊗ 𝕋𝕌ℕ𝔼 ⊗ 𝕍𝔸𝕃)(model=rf, tune=grid, folds=5)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  Julia-MLJ via PythonCall (zero-copy)
# ----------------------------------------------------------
# pip install juliacall mlj python-call
try:
    from juliacall import Main as jl
except ImportError as e:
    raise RuntimeError("pip install juliacall mlj python-call") from e

# ----------------------------------------------------------
# 2.  Registered primitives (JAX-safe wrappers)
# ----------------------------------------------------------
@register("𝕄𝕃𝕁")
def mlj_model_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Julia-MLJ model fit/predict (any model).
    Params: model (str), epochs (int)
    Returns: fitted model + predictions (still PyTree)
    """
    model_name = params["model"]
    epochs = params["epochs"]
    X = params["X"]  # [n, d]
    y = params["y"]  # [n]

    # call Julia (zero-copy – arrays stay in memory)
    jl.seval("using MLJ")
    jl.X = X
    jl.y = y
    jl.model_name = model_name
    jl.epochs = epochs
    jl.seval("""
        model = eval(Meta.parse(model_name))
        mach = machine(model, X, y)
        fit!(mach, epochs=epochs)
        y_pred = predict(mach, X)
    """)
    return dict(model=jl.mach, y_pred=jl.y_pred)


@register("𝕋𝕌ℕ𝔼")
def mlj_tune_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Julia-MLJ hyper-parameter tuning (any strategy).
    Params: tune (str), n_trials (int)
    """
    tune = params["tune"]
    n_trials = params["n_trials"]
    X = params["X"]
    y = params["y"]

    jl.seval("using MLJTuning")
    jl.tune = tune
    jl.n_trials = n_trials
    jl.seval("""
        tuned = evaluate(eval(Meta.parse(tune)), model, X, y, resampling=Holdout(), measure=rms, n_trials=n_trials)
    """)
    return dict(best_params=jl.tuned.best_params, best_score=jl.tuned.best_score)


@register("𝕍𝔸𝕃")
def mlj_val_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    Julia-MLJ cross-validation (any resampling strategy).
    Params: folds (int), measure (str)
    """
    folds = params["folds"]
    measure = params["measure"]
    X = params["X"]
    y = params["y"]

    jl.seval("using MLJ")
    jl.folds = folds
    jl.measure = measure
    jl.seval("""
        cv = evaluate(model, X, y, resampling=CV(nfolds=folds), measure=eval(Meta.parse(measure)))
    """)
    return dict(cv_scores=jl.cv.measurements, cv_mean=jl.cv.mean)


# ----------------------------------------------------------
# 4.  Fused spell
# ----------------------------------------------------------
_SPELL = "(𝕄𝕃𝕁 ⊗ 𝕋𝕌ℕ𝔼 ⊗ 𝕍𝔸𝕃)(model=rf, tune=grid, folds=5, epochs=10, n_trials=20, measure=rms)"


# ----------------------------------------------------------
# 5.  Factory – identical API to fql_rime
# ----------------------------------------------------------
def make_mlj(
    X: jax.Array,  # [n, d] – training data (injected static)
    y: jax.Array,  # [n]    – target (injected static)
    model: str = "rf",
    epochs: int = 10,
    tune: str = "grid",
    n_trials: int = 20,
    folds: int = 5,
    measure: str = "rms",
):
    spell = "(𝕄𝕃𝕁 ⊗ 𝕋𝕌ℕ𝔼 ⊗ 𝕍𝔸𝕃)(model={}, epochs={}, tune={}, n_trials={}, folds={}, measure={})".format(
        model, epochs, tune, n_trials, folds, measure
    )
    step_fn = compile_spell(spell)

    # bind static data into params (zero-copy)
    def bound_step(key, state):
        return step_fn(key, state, {
            "X": X,
            "y": y,
            "model": model,
            "epochs": epochs,
            "tune": tune,
            "n_trials": n_trials,
            "folds": folds,
            "measure": measure,
        })

    # initial state – empty (Julia fills it)
    state = dict(
        X=X,
        y=y,
        dummy=jnp.zeros(1),  # placeholder
    )

    return jax.jit(bound_step), state
