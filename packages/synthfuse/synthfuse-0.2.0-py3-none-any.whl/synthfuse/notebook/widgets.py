# synthfuse/notebook/widgets.py
"""
Interactive widgets for Synth-fuse spells in Jupyter notebooks.
All widgets are optional and run outside JIT—safe for pure JAX execution.
"""

from typing import Dict, Any, Callable, Optional
from IPython.display import display
import ipywidgets as widgets

def spell_param_widget(
    spell_template: str,
    param_ranges: Dict[str, tuple],
    on_update: Callable[[str], None],
    default_params: Optional[Dict[str, Any]] = None
) -> widgets.VBox:
    """
    Create interactive sliders for spell parameters.
    
    Args:
        spell_template: e.g., "(𝕂𝟛𝔻 ⊗ ℤ𝕊𝕍ℝ ⊗ 𝔾ℝ𝔽)({params})"
        param_ranges: e.g., {"beta": (0.1, 2.0), "sigma": (0.01, 5.0)}
        on_update: callback(spell_str) when params change
        default_params: initial values
    
    Returns:
        VBox of sliders + live spell string display
    """
    default_params = default_params or {}
    sliders = {}
    outputs = {}

    def on_change(change):
        # Rebuild spell string
        current_vals = {name: slider.value for name, slider in sliders.items()}
        spell_str = spell_template.format(params=", ".join(f"{k}={v:.3f}" for k, v in current_vals.items()))
        outputs["spell_display"].value = f"<pre>{spell_str}</pre>"
        on_update(spell_str)

    for name, (min_val, max_val) in param_ranges.items():
        val = default_params.get(name, (min_val + max_val) / 2)
        slider = widgets.FloatSlider(
            value=val,
            min=min_val,
            max=max_val,
            step=(max_val - min_val) / 100,
            description=name,
            continuous_update=False  # avoid spamming updates
        )
        slider.observe(on_change, names="value")
        sliders[name] = slider

    # Initial spell
    init_vals = {name: s.value for name, s in sliders.items()}
    init_spell = spell_template.format(params=", ".join(f"{k}={v:.3f}" for k, v in init_vals.items()))
    spell_display = widgets.HTML(value=f"<pre>{init_spell}</pre>")
    outputs["spell_display"] = spell_display

    box = widgets.VBox([
        widgets.HTML("<h4>🎛️ Tune Spell Parameters</h4>"),
        spell_display,
        *sliders.values(),
        widgets.HTML("<em>Adjust sliders → spell updates below</em>")
    ])
    return box


def live_spell_runner(
    spell_template: str,
    param_ranges: Dict[str, tuple],
    run_fn: Callable[[str], Any],
    default_params: Optional[Dict[str, Any]] = None
):
    """
    High-level widget: tune + run spell in one flow.
    
    Example:
        live_spell_runner(
            "(𝕂𝟛𝔻 ⊗ ℤ𝕊𝕍ℝ)(beta={beta}, sigma={sigma})",
            {"beta": (0.1, 2.0), "sigma": (0.1, 3.0)},
            lambda s: run_spell_cell(s, steps=50, viz=True)
        )
    """
    output_area = widgets.Output()

    def on_spell_update(spell_str: str):
        with output_area:
            output_area.clear_output()
            try:
                run_fn(spell_str)
            except Exception as e:
                print(f"❌ Error: {e}")

    widget_box = spell_param_widget(spell_template, param_ranges, on_spell_update, default_params)
    full_ui = widgets.VBox([widget_box, output_area])
    display(full_ui)
