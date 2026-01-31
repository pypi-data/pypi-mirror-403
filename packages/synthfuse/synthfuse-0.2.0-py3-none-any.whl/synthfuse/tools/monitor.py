# tools/monitor.py
import time
import jax.numpy as jnp
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel

console = Console()

def compression_surrogate(z: jnp.ndarray, eps: float = 1e-6) -> float:
    """Same surrogate as in STCL loop."""
    return float(jnp.sum(jnp.log(1.0 + (z ** 2) / eps)))

class AlchemMonitor:
    """
    Real-time telemetry for the Orion-STCL loop.
    Tracks:
      - Semantic Gravity (Φ)
      - Compression Surrogate (C)
      - Free Energy (ℱ = Φ - β·C)
      - Thermodynamic parameters (β, σ)
    """
    def __init__(self, refresh_rate: float = 0.1, comp_eps: float = 1e-6):
        self.refresh_rate = refresh_rate
        self.comp_eps = comp_eps
        self.history = {"phi": [], "c": [], "fe": [], "beta": [], "sigma": []}

    def _create_dashboard(self, state):
        phi = float(state.concept_energy)
        c = compression_surrogate(state.representation, self.comp_eps)
        fe = phi - state.beta * c

        # Update history
        self.history["phi"].append(phi)
        self.history["c"].append(c)
        self.history["fe"].append(fe)
        self.history["beta"].append(state.beta)
        self.history["sigma"].append(state.sigma)

        # Simple trend arrows (only if we have history)
        def trend(values):
            if len(values) < 2:
                return "–"
            return "↑" if values[-1] > values[-2] else "↓"

        table = Table(title=f"SynthFuse Telemetry [Tick: {state.clock}]")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta", justify="right")
        table.add_column("Trend", style="green", justify="center")

        table.add_row("Semantic Gravity (Φ)", f"{phi:.4f}", trend(self.history["phi"]))
        table.add_row("Compression Cost (C̃)", f"{c:.4f}", trend(self.history["c"]))
        table.add_row("Free Energy (ℱ)", f"{fe:.4f}", trend(self.history["fe"]))
        table.add_row("Inv. Temp (β)", f"{state.beta:.4f}", trend(self.history["beta"]))
        table.add_row("Manifold Width (σ)", f"{state.sigma:.4f}", trend(self.history["sigma"]))

        return Panel.fit(table, title="Helios Dashboard", border_style="yellow")

    def stream(self, step_generator):
        """
        Consumes a generator of OrionSTCLState and renders live telemetry.
        """
        with Live(console=console, refresh_per_second=10, vertical_overflow="visible") as live:
            for state in step_generator:
                panel = self._create_dashboard(state)
                live.update(panel)
                if self.refresh_rate > 0:
                    time.sleep(self.refresh_rate)
# ------------------------------------------------------------------
# 6.  Public attachable wrapper
# ------------------------------------------------------------------
def monitor_loop(step_fn, init_state, n_steps: int, refresh_rate: float = 0.1):
    """
    Drop-in wrapper:
        step_fn, state = make_orion_stcl(...)
        monitor_loop(step_fn, state, n_steps=500)
    """
    monitor = AlchemMonitor(refresh_rate=refresh_rate)

    def _gen():
        st = init_state
        for i in range(n_steps):
            key = jax.random.PRNGKey(i)
            st = step_fn(st)  # stateless step
            yield st

    monitor.stream(_gen())


# ------------------------------------------------------------------
# 7.  Optional CSV dump
# ------------------------------------------------------------------
def to_csv(monitor: AlchemMonitor, path: Path):
    import pandas as pd
    df = pd.DataFrame(monitor.history)
    df.to_csv(path, index=False)
    
    def cli():
    import argparse, jax
    ap = argparse.ArgumentParser(description="Live Orion-STCL telemetry")
    ap.add_argument("--steps", type=int, default=500)
    ap.add_argument("--refresh", type=float, default=0.1)
    args = ap.parse_args()
    from synthfuse.systems.orion import make_orion_stcl
    step, state = make_orion_stcl(jax.random.normal(jax.PRNGKey(0), (64, 32)),
                                  jax.random.normal(jax.PRNGKey(1), (32,)),
                                  beta_init=0.8, sigma_init=1.2)
    monitor_loop(step, state, args.steps, args.refresh)