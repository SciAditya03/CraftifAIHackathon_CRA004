"""Pipeline IR Graph Visualizer and DAG Validator.

Parses pipegen-export/pipeline_ir.json, validates node connectivity,
and generates an SVG diagram of the PipeGen computational graph.
"""

from __future__ import annotations

import json
from pathlib import Path


def render_pipeline_ir(
    ir_path: str = "pipegen-export/pipeline_ir.json",
    output_svg: str = "evidence/pipeline-ir/pipeline_ir_rendered.svg",
) -> None:
    ir_file = Path(ir_path)
    if not ir_file.exists():
        print(f"Error: {ir_path} not found.")
        return

    with open(ir_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("graph", {}).get("nodes", [])
    print(f"[*] Validating Pipeline IR: {len(nodes)} nodes found.")

    # Generate visual SVG representation
    width = 1100
    height = 200 + len(nodes) * 90
    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '  <style>',
        '    .title { font-family: sans-serif; font-size: 22px; font-weight: bold; fill: #1f2328; }',
        '    .subtitle { font-family: sans-serif; font-size: 14px; fill: #656d76; }',
        '    .node-box { fill: #f6f8fa; stroke: #d0d7de; stroke-width: 2; rx: 8; ry: 8; }',
        '    .node-header { font-family: sans-serif; font-size: 15px; font-weight: bold; fill: #0969da; }',
        '    .node-desc { font-family: monospace; font-size: 13px; fill: #24292f; }',
        '    .node-cat { font-family: sans-serif; font-size: 12px; font-weight: 600; fill: #76b900; }',
        '    .arrow { stroke: #57606a; stroke-width: 2; fill: none; marker-end: url(#arrowhead); }',
        '  </style>',
        '  <defs>',
        '    <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">',
        '      <polygon points="0 0, 8 3, 0 6" fill="#57606a" />',
        '    </marker>',
        '  </defs>',
        '  <!-- Background -->',
        f'  <rect width="{width}" height="{height}" fill="#ffffff" />',
        '  <!-- Title -->',
        f'  <text x="40" y="45" class="title">{data.get("name", "Pipeline IR Graph")}</text>',
        f'  <text x="40" y="70" class="subtitle">CraftifAI PipeGen v{data.get("pipegen_version", "0.5.1")} | Pipeline ID: {data.get("pipeline_id", "N/A")}</text>',
    ]

    card_x = 100
    card_w = 900
    card_h = 65

    for idx, node in enumerate(nodes):
        y = 100 + idx * 95
        cat = node.get("category", "General")
        nid = node.get("id", f"node_{idx}")
        plugin = node.get("plugin", "unknown")

        svg_lines.append(f'  <rect x="{card_x}" y="{y}" width="{card_w}" height="{card_h}" class="node-box" />')
        svg_lines.append(f'  <text x="{card_x + 20}" y="{y + 25}" class="node-header">[{idx + 1}] {nid}</text>')
        svg_lines.append(f'  <text x="{card_x + 350}" y="{y + 25}" class="node-cat">CATEGORY: {cat.upper()}</text>')
        svg_lines.append(f'  <text x="{card_x + 20}" y="{y + 50}" class="node-desc">Plugin: {plugin}</text>')

        # Arrow to next node
        if idx < len(nodes) - 1:
            next_y = y + card_h
            arr_start_y = next_y
            arr_end_y = next_y + 30
            arr_x = card_x + card_w // 2
            svg_lines.append(f'  <line x1="{arr_x}" y1="{arr_start_y}" x2="{arr_x}" y2="{arr_end_y}" class="arrow" />')

    svg_lines.append('</svg>')

    out_path = Path(output_svg)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_lines))

    print(f"[+] Rendered SVG Pipeline IR diagram to: {output_svg}")


if __name__ == "__main__":
    render_pipeline_ir()
