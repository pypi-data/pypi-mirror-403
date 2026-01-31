"""
One-command spell visualiser:
  python -m synthfuse.tools.viz "𝕀 ⊗ 𝕃(alpha=1.5)"  →  spell.svg
Exports SVG / DOT / Mermaid / interactive HTML D3.
"""
import argparse
import json
from pathlib import Path
from typing import Any
from lark import Lark, Transformer
from synthfuse.alchemj import grammar

Graph = dict[str, Any]  # nodes, edges, meta


# ------------------------------------------------------------------
# 1.  Lark AST → graph
# ------------------------------------------------------------------
class AST2Graph(Transformer):
    def __init__(self):
        self._id = 0
        self._nodes = []
        self._edges = []

    def _uid(self):
        self._id += 1
        return f"n{self._id}"

    def prim(self, symbol, params):
        uid = self._uid()
        self._nodes.append(
            {"id": uid, "label": str(symbol), "type": "primitive", "params": params}
        )
        return uid

    def seq(self, left, right):
        uid = self._uid()
        self._nodes.append({"id": uid, "label": "⊗", "type": "combinator"})
        self._edges.extend([(left, uid), (uid, right)])
        return uid

    def par(self, left, right):
        uid = self._uid()
        self._nodes.append({"id": uid, "label": "⊕", "type": "combinator"})
        self._edges.extend([(left, uid), (uid, right)])
        return uid

    def guard(self, pred, op):
        uid = self._uid()
        self._nodes.append({"id": uid, "label": "∘", "type": "guard"})
        self._edges.extend([(pred, uid), (uid, op)])
        return uid

    def paren(self, child):
        return child  # transparent

    def build(self, spell: str) -> Graph:
        ast = Lark.open(grammar.__file__, parser="lalr").parse(spell)
        root = self.transform(ast)
        return {"nodes": self._nodes, "edges": self._edges, "root": root}


# ------------------------------------------------------------------
# 2.  SVG renderer (simple hierarchical)
# ------------------------------------------------------------------
def to_svg(graph: Graph, file: Path) -> Path:
    import svgwrite

    dwg = svgwrite.Drawing(str(file), size=("400", "300"))
    nodes = {n["id"]: n for n in graph["nodes"]}
    levels = _hierarchy(graph)  # id -> level
    max_level = max(levels.values())
    node_pos = {}
    # layout: level-order
    for lvl in range(max_level + 1):
        ids = [i for i, l in levels.items() if l == lvl]
        y = 50 + lvl * 80
        for k, node_id in enumerate(ids):
            x = 50 + k * 100
            node_pos[node_id] = (x, y)
    # draw edges
    for src, dst in graph["edges"]:
        dwg.add(
            dwg.line(
                start=node_pos[src],
                end=node_pos[dst],
                stroke=svgwrite.rgb(10, 10, 10, "%"),
                stroke_width=2,
            )
        )
    # draw nodes
    for node in graph["nodes"]:
        x, y = node_pos[node["id"]]
        color = "#81c784" if node["type"] == "primitive" else "#64b5f6"
        dwg.add(
            dwg.circle(
                center=(x, y),
                r=20,
                fill=color,
                stroke="#333",
                stroke_width=1.5,
            )
        )
        dwg.add(
            dwg.text(
                node["label"],
                insert=(x - 7, y + 5),
                font_size="14px",
                font_family="monospace",
                fill="white",
            )
        )
    dwg.save()
    return file


def _hierarchy(graph: Graph) -> dict[str, int]:
    # BFS from root
    from collections import deque

    levels = {}
    adj = {}
    for a, b in graph["edges"]:
        adj.setdefault(a, []).append(b)
    root = graph["root"]
    q = deque([(root, 0)])
    while q:
        node, lvl = q.popleft()
        levels[node] = lvl
        for child in adj.get(node, []):
            if child not in levels:
                q.append((child, lvl + 1))
    return levels


# ------------------------------------------------------------------
# 3.  DOT (Graphviz)
# ------------------------------------------------------------------
def to_dot(graph: Graph, file: Path) -> Path:
    lines = ["digraph G {"]
    for n in graph["nodes"]:
        shape = "ellipse" if n["type"] == "primitive" else "box"
        lines.append(f'  {n["id"]} [label="{n["label"]}", shape={shape}];')
    for src, dst in graph["edges"]:
        lines.append(f"  {src} -> {dst};")
    lines.append("}")
    file.write_text("\n".join(lines))
    return file


# ------------------------------------------------------------------
# 4.  Mermaid (markdown)
# ------------------------------------------------------------------
def to_mermaid(graph: Graph) -> str:
    lines = ["graph TD"]
    id2label = {n["id"]: n["label"] for n in graph["nodes"]}
    for src, dst in graph["edges"]:
        lines.append(f"    {src}-->{dst}")
    for n in graph["nodes"]:
        lines.append(f'    {n["id"]}["{n["label"]}"]')
    return "\n".join(lines)


# ------------------------------------------------------------------
# 5.  Interactive HTML (D3 force)
# ------------------------------------------------------------------
def to_html(graph: Graph, file: Path) -> Path:
    tmpl = """
<!DOCTYPE html>
<meta charset="utf-8">
<style>
  .node {{ fill: #81c784; stroke: #333; stroke-width: 1.5px; }}
  .link {{ stroke: #999; stroke-opacity: 0.6; }}
  text {{ font-family: monospace; font-size: 12px; pointer-events: none; }}
</style>
<body>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
  const graph = $DATA$;
  const width = 500, height = 300;
  const svg = d3.select("body").append("svg").attr("width", width).attr("height", height);
  const simulation = d3.forceSimulation(graph.nodes)
      .force("link", d3.forceLink(graph.edges).id(d => d.id))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2));
  const link = svg.append("g").selectAll("line")
      .data(graph.edges).enter().append("line").attr("class", "link");
  const node = svg.append("g").selectAll("g")
      .data(graph.nodes).enter().append("g");
  node.append("circle").attr("r", 20).attr("class", "node");
  node.append("text").attr("dx", -7).attr("dy", 5).text(d => d.label);
  simulation.on("tick", () => {
      link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
      node.attr("transform", d => `translate(${d.x},${d.y})`);
  });
</script>
"""
    file.write_text(tmpl.replace("$DATA$", json.dumps(graph)))
    return file


# ------------------------------------------------------------------
# 6.  CLI
# ------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Visualise ALCHEM-J spell")
    ap.add_argument("spell", help="spell string, e.g. '𝕀 ⊗ 𝕃(alpha=1.5)'")
    ap.add_argument("-o", "--out", type=Path, default=Path("spell"), help="output base name (no ext)")
    ap.add_argument("-f", "--format", choices=["svg", "dot", "mermaid", "html"], default="svg")
    args = ap.parse_args()

    graph = AST2Graph().build(args.spell)
    fmt = args.format
    file = args.out.with_suffix(f".{fmt}")
    if fmt == "svg":
        to_svg(graph, file)
    elif fmt == "dot":
        to_dot(graph, file)
    elif fmt == "mermaid":
        file.write_text(to_mermaid(graph))
    elif fmt == "html":
        to_html(graph, file)
    print(f"[ok] wrote {file}")


if __name__ == "__main__":
    main()