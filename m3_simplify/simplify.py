"""
UNTANGLE - Phase 4
Step 2: Process Simplification

Creates a simplified graph while preserving:
- Major equipment
- IO-list instruments
- Important branches
- Process connectivity
- Flow direction
- Duty/standby information
- Original node/edge traceability
"""


def _is_preserved(node):
    return node.get("preserve", False) is True


def _can_bridge_hidden_node(node_id, nodes_by_id, incoming, outgoing):
    node = nodes_by_id.get(node_id)

    if not node:
        return False

    if _is_preserved(node):
        return False

    return (
        len(incoming.get(node_id, [])) == 1
        and len(outgoing.get(node_id, [])) == 1
    )


def _find_bridged_connections(graph, preserved_ids):

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    nodes_by_id = {
        node.get("id"): node
        for node in nodes
        if node.get("id")
    }

    incoming = {}
    outgoing = {}

    for edge in edges:

        if edge.get("preserve", True) is False:
            continue

        source = edge.get("source")
        target = edge.get("target")

        if not source or not target:
            continue

        outgoing.setdefault(source, []).append(edge)
        incoming.setdefault(target, []).append(edge)

    bridged = []
    used_original_edges = set()

    for source_id in preserved_ids:

        for first_edge in outgoing.get(source_id, []):

            current_edge = first_edge
            current_node = current_edge.get("target")

            path_edges = [first_edge]
            visited_hidden = set()

            while (
                current_node not in preserved_ids
                and current_node not in visited_hidden
            ):

                visited_hidden.add(current_node)

                if not _can_bridge_hidden_node(
                    current_node,
                    nodes_by_id,
                    incoming,
                    outgoing,
                ):
                    break

                next_edges = outgoing.get(current_node, [])

                if len(next_edges) != 1:
                    break

                next_edge = next_edges[0]

                path_edges.append(next_edge)
                current_node = next_edge.get("target")

            if (
                current_node in preserved_ids
                and current_node != source_id
                and len(path_edges) >= 2
            ):

                bridge_id = (
                    f"BRIDGE-{len(bridged) + 1:03d}"
                )

                # Preserve actual flow direction.
                path_directions = {
                    edge.get("flow_direction")
                    for edge in path_edges
                    if edge.get("flow_direction")
                }

                if len(path_directions) == 1:
                    bridge_flow_direction = path_directions.pop()
                else:
                    bridge_flow_direction = "unknown"

                bridge_edge = {
                    "id": bridge_id,
                    "source": source_id,
                    "target": current_node,

                    "original_edge_ids": [
                        edge.get("id")
                        for edge in path_edges
                        if edge.get("id")
                    ],

                    "original_line_ids": [
                        edge.get("line_id")
                        for edge in path_edges
                        if edge.get("line_id")
                    ],

                    "flow_direction": bridge_flow_direction,

                    "preserve": True,

                    "generated_by": "m3_connectivity_bridge",

                    "simplification_reason": (
                        "hidden intermediate process detail"
                    ),
                }

                bridged.append(bridge_edge)

                for edge in path_edges:

                    if edge.get("id"):
                        used_original_edges.add(
                            edge.get("id")
                        )

    return bridged, used_original_edges


def simplify_graph(graph):

    simple_graph = {
        "nodes": [],
        "edges": [],
        "simplification_log": [],
        "preservation": graph.get(
            "preservation",
            {}
        ),
    }

    # ========================================================
    # 1. KEEP PRESERVED NODES
    # ========================================================

    for node in graph.get("nodes", []):

        if _is_preserved(node):

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
    # 3. KEEP DIRECT CONNECTIONS
    # ========================================================

    direct_edges = []

    for edge in graph.get("edges", []):

        source = edge.get("source")
        target = edge.get("target")

        endpoints_exist = (
            source in preserved_ids
            and target in preserved_ids
        )

        connection_preserved = edge.get(
            "preserve",
            True
        )

        if endpoints_exist and connection_preserved:

            direct_edges.append(
                edge.copy()
            )

        else:

            simple_graph["simplification_log"].append(
                {
                    "type": "edge",
                    "edge": edge.get("id"),
                    "source": source,
                    "target": target,
                    "reason": (
                        "connection hidden because "
                        "an intermediate endpoint "
                        "was simplified"
                    ),
                }
            )

    # ========================================================
    # 4. BRIDGE SAFE HIDDEN PROCESS DETAILS
    # ========================================================

    bridged_edges, bridged_original_ids = (
        _find_bridged_connections(
            graph,
            preserved_ids,
        )
    )

    existing_pairs = {
        (
            edge.get("source"),
            edge.get("target"),
        )
        for edge in direct_edges
    }

    for bridge in bridged_edges:

        pair = (
            bridge.get("source"),
            bridge.get("target"),
        )

        if pair not in existing_pairs:

            simple_graph["edges"].append(
                bridge
            )

            existing_pairs.add(pair)

            simple_graph["simplification_log"].append(
                {
                    "type": "edge_bridge",
                    "edge": bridge.get("id"),
                    "source": bridge.get("source"),
                    "target": bridge.get("target"),
                    "original_edges": bridge.get(
                        "original_edge_ids",
                        [],
                    ),
                    "reason": (
                        "preserved process connectivity "
                        "through hidden intermediate detail"
                    ),
                }
            )

    # Add original direct edges.
    for edge in direct_edges:

        if edge.get("id") not in {
            item.get("id")
            for item in simple_graph["edges"]
        }:

            simple_graph["edges"].append(
                edge
            )

    # ========================================================
    # 5. PRESERVE IMPORTANT GRAPH INFORMATION
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
    # 6. COPY RELEVANT METADATA
    # ========================================================

    simple_graph["metadata"] = {

        "source": graph.get(
            "metadata",
            {}
        ).get(
            "source",
            "graph_full.json",
        ),

        "graph_type": graph.get(
            "metadata",
            {}
        ).get(
            "graph_type",
            "directed",
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

        "connectivity_bridges": len(
            bridged_edges
        ),
    }

    return simple_graph