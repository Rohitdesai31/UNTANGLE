"""
UNTANGLE - M3 Process Simplification Runner
"""

import json

from m3_simplify.preservation import apply_preservation_rules
from m3_simplify.simplify import simplify_graph
from m3_simplify.layout import calculate_layout
from m3_simplify.routing import route_edges
from m3_simplify.svg_generator import generate_svg, create_mapping
from m3_simplify.audit import create_audit


BASE_DIR = "fixtures"


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


if __name__ == "__main__":

    # --------------------------------
    # 1. Load full graph
    # --------------------------------
    graph_path = f"{BASE_DIR}/graph_full.json"
    original_graph = load_json(graph_path)

    marked_graph = apply_preservation_rules(original_graph)

    # --------------------------------
    # 4. Simplify graph
    # --------------------------------
    simple_graph = simplify_graph(
        marked_graph
    )

    # --------------------------------
    # 5. Calculate layout
    # --------------------------------
    simple_graph = calculate_layout(
        simple_graph
    )

    # --------------------------------
    # 6. Route connections
    # --------------------------------
    simple_graph = route_edges(
        simple_graph
    )

    # --------------------------------
    # 7. Save simplified graph
    # --------------------------------
    save_json(
        simple_graph,
        f"{BASE_DIR}/graph_simple.json"
    )

    # --------------------------------
    # 8. Generate SVG
    # --------------------------------
    generate_svg(
        simple_graph,
        f"{BASE_DIR}/sketch.svg"
    )

    # --------------------------------
    # 9. Create mapping
    # --------------------------------
    mapping = create_mapping(
        simple_graph
    )

    save_json(
        mapping,
        f"{BASE_DIR}/mapping.json"
    )

    # --------------------------------
    # 10. Create audit
    # --------------------------------
    audit = create_audit(
        marked_graph,
        simple_graph
    )

    save_json(
        audit,
        f"{BASE_DIR}/audit.json"
    )

    # --------------------------------
    # 11. Print result
    # --------------------------------
    print("M3 simplification completed.")
    print(f"Nodes: {len(simple_graph['nodes'])}")
    print(f"Edges: {len(simple_graph['edges'])}")
    print(f"Audit: {audit['overall']}")
    print(f"Output: {BASE_DIR}/graph_simple.json")
    print(f"Output: {BASE_DIR}/sketch.svg")
    print(f"Output: {BASE_DIR}/mapping.json")
    print(f"Output: {BASE_DIR}/audit.json")