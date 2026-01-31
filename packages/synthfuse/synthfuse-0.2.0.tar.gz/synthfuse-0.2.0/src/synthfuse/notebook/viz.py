# synthfuse/notebook/viz.py
import subprocess
import tempfile
from IPython.display import HTML

def render_spell_viz(spell: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        subprocess.run(["sfviz", f'"{spell}"', "-f", "html", "-o", f.name])
        with open(f.name) as html_file:
            return html_file.read()
