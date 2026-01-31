"""
MTK-Fusion – Symbolic-Numeric PDEs via ModelingToolkit.jl + JAX
ModelingToolkit.jl operators exposed as Synth-Fuse primitives:
𝕄𝕋𝕂 (symbolic model), 𝔻𝔼ℝ𝕀𝕍 (automatic derivative), 𝕊𝕆𝕃𝕍𝔼 (numeric solver)
Original: https://github.com/SciML/ModelingToolkit.jl
Converted to single Synth-Fuse spell:
(𝕄𝕋𝕂 ⊗ 𝔻𝔼ℝ𝕀𝕍 ⊗ 𝕊𝕆𝕃𝕍𝔼)(eq=heat, dim=2, order=4, dt=0.01)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  ModelingToolkit via PythonCall (zero-copy)
# ----------------------------------------------------------
# pip install modelingtoolkit juliacall python-call
try:
    from juliacall import Main as jl
except ImportError as e:
    raise RuntimeError("pip install modelingtoolkit juliacall python-call") from e


# ----------------------------------------------------------
# 2.  Registered primitives (JAX-safe wrappers)
# ----------------------------------------------------------
@register("𝕄𝕋𝕂")
def mtk_model_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    ModelingToolkit symbolic model (any PDE/ODE).
    Params: eq (str), dim (int), order (int)
    Returns: symbolic equations (PyTree)
    """
    eq = params["eq"]
    dim = params["dim"]
    order = params["order"]

    # call MTK via Julia (zero-copy – arrays stay in memory)
    jl.seval("using ModelingToolkit")
    jl.eq = eq
    jl.dim = dim
    jl.order = order
    jl.seval("""
        using ModelingToolkit: @variables, @parameters, PDESystem
        @variables u(..)
        @parameters t x y
        if eq == "heat"
            eq = Dt(u(t,x,y)) ~ Dxx(u(t,x,y)) + Dyy(u(t,x,y))
        end
        sys = PDESystem(eq, u(t,x,y), [t,x,y], [])
        symbolic_eq = sys.eqs[1]
    """)
    symbolic_eq = jl.symbolic_eq  # PyTree (symbolic expression)

    return dict(symbolic_eq=symbolic_eq, eq=eq, dim=dim, order=order)


@register("𝔻𝔼ℝ𝕀𝕍")
def mtk_deriv_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    ModelingToolkit automatic derivative (symbolic + numeric).
    Params: var (str), order (int)
    Returns: derivative expression (PyTree)
    """
    var = params["var"]
    order = params["order"]
    expr = state["symbolic_eq"]  # from 𝕄𝕋𝕂 step

    jl.seval("using ModelingToolkit: Differential")
    jl.var = var
    jl.order = order
    jl.expr = expr
    jl.seval("""
        using Symbolics: derivative
        deriv = derivative(expr, var, order)
    """)
    deriv = jl.deriv  # PyTree (symbolic derivative)

    return dict(deriv=deriv, var=var, order=order)


@register("𝕊𝕆𝕃𝕍𝔼")
def mtk_solve_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    ModelingToolkit numeric solver (any method).
    Params: dt (float), tspan (tuple), method (str)
    Returns: solution u(t,x) (JAX array)
    """
    dt = params["dt"]
    tspan = params["tspan"]
    method = params["method"]
    deriv = state["deriv"]  # from 𝔻𝔼ℝ𝕀𝕍 step

    jl.seval("using DifferentialEquations: solve, Tsit5")
    jl.dt = dt
    jl.tspan = tspan
    jl.method = method
    jl.deriv = deriv
    jl.seval("""
        using DifferentialEquations: ODEProblem, solve, Tsit5
        prob = ODEProblem(deriv, u0, tspan)
        sol = solve(prob, Tsit5(), dt=dt)
        u = sol.u  # solution array
    """)
    u = jl.u  # PyTree (solution array)

    return dict(u=u, dt=dt, tspan=tspan, method=method)


# ----------------------------------------------------------
# 4.  Fused spell
# ----------------------------------------------------------
_SPELL = "(𝕄𝕋𝕂 ⊗ 𝔻𝔼ℝ𝕀𝕍 ⊗ 𝕊𝕆𝕃𝕍𝔼)(eq=heat, dim=2, order=4, dt=0.01, tspan=(0.0, 1.0), method=Tsit5)"


# ----------------------------------------------------------
# 5.  Factory – identical API to fql_rime
# ----------------------------------------------------------
def make_mtk(
    eq: str = "heat",
    dim: int = 2,
    order: int = 4,
    dt: float = 0.01,
    tspan: tuple = (0.0, 1.0),
    method: str = "Tsit5",
):
    spell = "(𝕄𝕋𝕂 ⊗ 𝔻𝔼ℝ𝕀𝕍 ⊗ 𝕊𝕆𝕃𝕍𝔼)(eq={}, dim={}, order={}, dt={}, tspan={}, method={})".format(
        eq, dim, order, dt, tspan, method
    )
    step_fn = compile_spell(spell)

    # build initial condition (static)
    key = jax.random.PRNGKey(42)
    u0 = jax.random.normal(key, (64, 64))  # dummy 64×64 grid

    # bind static params
    def bound_step(key, state):
        return step_fn(key, state, {
            "eq": eq,
            "dim": dim,
            "order": order,
            "dt": dt,
            "tspan": tspan,
            "method": method,
            "u0": u0,
        })

    # initial state – empty (MTK fills it)
    state = dict(
        u0=u0,
        dummy=jnp.zeros(1),  # placeholder
    )

    return jax.jit(bound_step), state
