"""
UNTANGLE - Phase 4
Step 2: Process Simplification

Creates graph_simple.json from the validated graph_full.json.

Preservation rules:
- Every preserved IO tag stays
- Every preserved major equipment stays
- Every preserved process connection stays
- Flow direction stays
- Duty/standby information stays
- Important branches and merges stay
"""


def simplify_graph(graph):
    simple_graph = {
        "nodes": [],
        "edges": [],
        "simplification_log": [],
        "preservation": graph.get("preservation", {}),
    }

    # ========================================================
    # 1. KEEP PRESERVED NODES
    # ========================================================

    for node in graph.get("nodes", []):

        if node.get("preserve", False):

            simple_graph["nodes"].append(
                node.copy()
            )

        else:

            simple_graph["simplification_log"].append(
                {
                    "type": "node",
                    "node": node.get("id"),
                    "tag": node.get("tag"),
                    "reason": "unnecessary detail",
                }
            )

    # ========================================================
    # 2. GET PRESERVED NODE IDS
    # ========================================================

    preserved_ids = {
        node["id"]
        for node in simple_graph["nodes"]
    }

    # ========================================================
    # 3. KEEP PRESERVED PROCESS CONNECTIONS
    # ========================================================

    for edge in graph.get("edges", []):

        source = edge.get("source")
        target = edge.get("target")

        # Connection must have both endpoints present.
        endpoints_exist = (
            source in preserved_ids
            and target in preserved_ids
        )

        # Connection itself must be explicitly preserved.
        connection_preserved = edge.get(
            "preserve",
            True
        )

        if endpoints_exist and connection_preserved:

            simple_graph["edges"].append(
                edge.copy()
            )

        else:

            simple_graph["simplification_log"].append(
                {
                    "type": "edge",
                    "edge": edge.get("id"),
                    "source": source,
                    "target": target,
                    "reason": "connection removed because "
                              "its endpoint was not preserved",
                }
            )

    # ========================================================
    # 4. PRESERVE IMPORTANT GRAPH INFORMATION
    # ========================================================

    if "pump_patterns" in graph:
        simple_graph["pump_patterns"] = [
            pattern.copy()
            for pattern in graph.get(
                "pump_patterns",
                []
            )
        ]

    if "junctions" in graph:
        simple_graph["junctions"] = [
            junction.copy()
            for junction in graph.get(
                "junctions",
                []
            )
        ]

    # ========================================================
    # 5. COPY RELEVANT METADATA
    # ========================================================

    simple_graph["metadata"] = {
        "source": "graph_full.json",
        "graph_type": graph.get(
            "metadata",
            {}
        ).get(
            "graph_type",
            "directed"
        ),
        "node_count": len(
            simple_graph["nodes"]
        ),
        "edge_count": len(
            simple_graph["edges"]
        ),
        "original_node_count": len(
            graph.get("nodes", [])
        ),
        "original_edge_count": len(
            graph.get("edges", [])
        ),
    }

    return simple_graph