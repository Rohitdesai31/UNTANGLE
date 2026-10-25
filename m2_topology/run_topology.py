import json

from m2_topology.graph_builder import build_graph_from_files
from m2_topology.topology_validator import validate_topology


BASE_DIR = "fixtures"


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)



import json

from m2_topology.graph_builder import build_graph_from_files
from m2_topology.topology_validator import validate_topology

BASE_DIR = "fixtures"


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


if __name__ == "__main__":
    symbols_path = f"{BASE_DIR}/symbols.json"
    lines_path = f"{BASE_DIR}/lines.json"
    associations_path = f"{BASE_DIR}/associations.json"
    io_list_path = f"{BASE_DIR}/io_list.json"

    output_path = f"{BASE_DIR}/graph_full.json"

    graph = build_graph_from_files(
        symbols_path=symbols_path,
        lines_path=lines_path,
        associations_path=associations_path,
        output_path=output_path,
        io_list_path=io_list_path,
    )

    validation = validate_topology(graph)
    graph["validation"] = validation

    save_json(graph, output_path)

    print("Graph construction completed.")
    print(f"Nodes: {len(graph['nodes'])}")
    print(f"Edges: {len(graph['edges'])}")
    print(f"Topology valid: {graph['validation']['valid']}")
    print(f"Topology errors: {len(graph['validation']['errors'])}")
    print(f"Topology warnings: {len(graph['validation']['warnings'])}")
    print(f"Output: {output_path}")
