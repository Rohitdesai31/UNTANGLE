"""
UNTANGLE - Topology Graph Builder

Harshada responsibility:
P&ID symbols + process lines + associations + IO list
                    â†“
              graph_full.json

Requirements:
- NetworkX directed graph
- Preserve equipment and IO information
- Build only validated process associations
- Keep unresolved process lines for validation
- Support junction and pump-pattern information
"""

import json
from pathlib import Path

import networkx as nx

from m2_topology.junction_detection import detect_junctions
from m2_topology.flow_direction import determine_flow_direction
from m2_topology.pump_patterns import detect_pump_patterns


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# IO INDEX
# ============================================================

def build_io_index(io_list):
    """
    Create:
        tag -> IO information
    """
    io_index = {}

    for item in io_list:
        tag = item.get("tag")

        if not tag:
            continue

        io_index[tag] = {
            "io_type": item.get("type"),
            "description": item.get("description"),
            "loop": item.get("loop"),
            "expected_status": item.get("expected_status"),
        }

    return io_index


# ============================================================
# NODE BUILDING
# ============================================================

def build_nodes(symbols, io_list):
    """
    Convert M1 symbols into graph nodes.

    Every detected symbol becomes a node.
    IO information is attached when its tag exists
    in the IO list.
    """

    io_index = build_io_index(io_list)

    nodes = []

    for symbol in symbols:
        symbol_id = symbol.get("id")

        if not symbol_id:
            continue

        tag = symbol.get("tag")

        node = {
            "id": symbol_id,
            "tag": tag,
            "type": symbol.get("class_name"),
            "page": symbol.get("page"),
            "bbox": symbol.get("bbox"),
            "confidence": symbol.get("confidence"),
            "is_io": False,
            "preserve": True,
        }

        # ----------------------------------------------------
        # Attach IO information
        # ----------------------------------------------------

        if tag in io_index:
            io_data = io_index[tag]

            node["is_io"] = True
            node["io_type"] = io_data.get("io_type")
            node["description"] = io_data.get("description")
            node["loop"] = io_data.get("loop")
            node["expected_status"] = io_data.get("expected_status")

        nodes.append(node)

    return nodes


# ============================================================
# PROCESS CONNECTION EXTRACTION
# ============================================================

def build_process_connections(lines, associations):
    """
    Build process-line connection information from
    connects_from / connects_to associations.

    Instrument lines are intentionally excluded.
    Preserve multiple associations for each process line.
    """

    process_line_ids = {
        line.get("id")
        for line in lines
        if line.get("id") and line.get("line_type") == "process"
    }

    connections = {}

    for association in associations:
        line_id = association.get("source_id")

        if line_id not in process_line_ids:
            continue

        relation = association.get("relation")
        symbol_id = association.get("target_id")

        if relation not in {"connects_from", "connects_to"}:
            continue

        if not symbol_id:
            continue

        connections.setdefault(
            line_id,
            {
                "source": [],
                "target": [],
            },
        )

        key = "source" if relation == "connects_from" else "target"

        if symbol_id not in connections[line_id][key]:
            connections[line_id][key].append(symbol_id)

    return connections


# ============================================================
# EDGE BUILDING
# ============================================================

def build_edges(lines, associations, node_ids):
    """
    Create process edges only when a line has exactly
    one known source and one known target.

    Missing, ambiguous, or invalid endpoints are reported
    with reasons. Branches must be handled by topology/
    junction logic without inventing connections.
    """

    process_connections = build_process_connections(
        lines,
        associations,
    )

    edges = []
    unresolved_lines = []
    unresolved_reasons = {}

    # Prevent duplicate unresolved line IDs.
    unresolved_line_ids = set()

    def mark_unresolved(line_id, reason):
        """Record an unresolved line and its reason."""
        if line_id is None:
            return

        if line_id not in unresolved_line_ids:
            unresolved_lines.append(line_id)
            unresolved_line_ids.add(line_id)

        unresolved_reasons.setdefault(line_id, []).append(reason)

    for line in lines:

        # Only process lines are handled here.
        if line.get("line_type") != "process":
            continue

        line_id = line.get("id")

        # A process line without an ID cannot be tracked reliably.
        if not line_id:
            continue

        connection = process_connections.get(
            line_id,
            {
                "source": [],
                "target": [],
            },
        )

        sources = connection.get("source") or []
        targets = connection.get("target") or []

        # Support both lists and older single-ID values.
        if not isinstance(sources, list):
            sources = [sources]

        if not isinstance(targets, list):
            targets = [targets]

        # Remove empty and duplicate endpoint IDs.
        sources = list(dict.fromkeys(
            source for source in sources if source
        ))
        targets = list(dict.fromkeys(
            target for target in targets if target
        ))

        # Missing endpoint associations.
        if not sources and not targets:
            mark_unresolved(
                line_id,
                "Missing both source and target associations",
            )
            continue

        if not sources:
            mark_unresolved(
                line_id,
                "Missing source association",
            )
            continue

        if not targets:
            mark_unresolved(
                line_id,
                "Missing target association",
            )
            continue

        # Multiple endpoints may indicate a branch or ambiguity.
        # Do not create all-to-all connections automatically.
        if len(sources) > 1 or len(targets) > 1:
            mark_unresolved(
                line_id,
                "Multiple sources or targets; topology resolution required",
            )
            continue

        source = sources[0]
        target = targets[0]

        # Validate endpoint IDs against known graph nodes.
        invalid_endpoints = []

        if source not in node_ids:
            invalid_endpoints.append(f"source '{source}'")

        if target not in node_ids:
            invalid_endpoints.append(f"target '{target}'")

        if invalid_endpoints:
            mark_unresolved(
                line_id,
                "Endpoint not found in node IDs: "
                + ", ".join(invalid_endpoints),
            )
            continue

        # Prevent a self-loop caused by an invalid association.
        if source == target:
            mark_unresolved(
                line_id,
                "Source and target refer to the same node",
            )
            continue

        # Create an edge only when endpoint references are valid.
        edges.append(
            {
                "id": f"EDGE-{len(edges) + 1:03d}",
                "source": source,
                "target": target,
                "line_id": line_id,
                "line_type": "process",
                "page": line.get("page"),
                "confidence": line.get("confidence"),
                "validated": False,
                "validation_status": "needs_connection_validation",
            }
        )

    return edges, unresolved_lines, unresolved_reasons


# ============================================================
# NETWORKX GRAPH
# ============================================================

def create_networkx_graph(nodes, edges):
    """
    Create the directed process graph using NetworkX.
    """

    graph = nx.DiGraph()

    for node in nodes:
        graph.add_node(
            node["id"],
            **node,
        )

    for edge in edges:
        graph.add_edge(
            edge["source"],
            edge["target"],
            **edge,
        )

    return graph


# ============================================================
# EDGE VALIDATION
# ============================================================


def validate_edges(edges, node_ids):
    """
    Validate node references only.

    This does not prove physical connectivity.
    """

    for edge in edges:
        source_exists = edge.get("source") in node_ids
        target_exists = edge.get("target") in node_ids

        edge["endpoint_ids_valid"] = (
            source_exists and target_exists
        )

        # Physical connection validation requires additional
        # geometric or independently validated evidence.
        edge["validated"] = False

        if not edge["endpoint_ids_valid"]:
            edge["validation_status"] = "invalid_node_reference"
        elif edge.get("validation_status") is None:
            edge["validation_status"] = (
                "needs_connection_validation"
            )

    return edges

# ============================================================
# IO VALIDATION
# ============================================================

def validate_io(nodes, io_list):
    """
    Compare expected IO tags with detected graph nodes.
    """

    expected_tags = {
        item.get("tag")
        for item in io_list
        if item.get("tag")
    }

    detected_tags = {
        node.get("tag")
        for node in nodes
        if node.get("tag")
    }

    found_tags = expected_tags & detected_tags
    missing_tags = expected_tags - detected_tags

    return {
        "expected_count": len(expected_tags),
        "found_count": len(found_tags),
        "missing_count": len(missing_tags),
        "missing_tags": sorted(missing_tags),
    }


# ============================================================
# MAIN GRAPH BUILDER
# ============================================================
# ============================================================
# MAIN GRAPH BUILDER
# ============================================================

def build_graph(
    symbols,
    lines,
    associations,
    io_list,
):
    """
    Complete Phase 3 Step 1 graph construction.

    Input:
        symbols
        lines
        associations
        io_list

    Output:
        graph_full-compatible dictionary
    """

    # --------------------------------------------------------
    # 1. Build nodes
    # --------------------------------------------------------

    nodes = build_nodes(symbols, io_list)

    node_ids = {
        node["id"]
        for node in nodes
    }

    # --------------------------------------------------------
    # 2. Build process edges
    # CHANGE: Receive all three values from build_edges().
    # --------------------------------------------------------

    (
        edges,
        unresolved_process_lines,
        unresolved_reasons,
    ) = build_edges(
        lines,
        associations,
        node_ids,
    )

    print("Detected symbols:", len(symbols))
    print("Graph nodes:", len(nodes))
    print(
        "Process lines:",
        sum(1 for line in lines if line.get("line_type") == "process"),
    )
    print("Created edges:", len(edges))
    print("Unresolved process lines:", unresolved_process_lines)

    # --------------------------------------------------------
    # 3. Identify unclassified lines
    # --------------------------------------------------------

    unclassified_lines = [
        line.get("id")
        for line in lines
        if line.get("id")
        and line.get("line_type") not in {"process", "instrument"}
    ]

    # --------------------------------------------------------
    # 4. Validate edge endpoint IDs
    # --------------------------------------------------------

    edges = validate_edges(edges, node_ids)

    # --------------------------------------------------------
    # 5. Determine flow direction
    # --------------------------------------------------------

    flow_graph = {
        "nodes": nodes,
        "edges": edges,
    }

    flow_graph = determine_flow_direction(
        flow_graph,
        lines=lines,
    )

    nodes = flow_graph["nodes"]
    edges = flow_graph["edges"]

    # --------------------------------------------------------
    # 6. Create NetworkX directed graph
    # --------------------------------------------------------

    nx_graph = create_networkx_graph(
        nodes,
        edges,
    )

    # --------------------------------------------------------
    # 7. Detect junctions
    # --------------------------------------------------------

    junctions = detect_junctions(lines)

    # --------------------------------------------------------
    # 8. Detect pump patterns
    # --------------------------------------------------------

    pattern_graph = {
        "nodes": nodes,
        "edges": edges,
    }

    pump_patterns = detect_pump_patterns(pattern_graph)

    # --------------------------------------------------------
    # 9. Validate IO tags
    # --------------------------------------------------------

    io_validation = validate_io(nodes, io_list)

    # --------------------------------------------------------
    # 10. Create final graph object
    # --------------------------------------------------------

    graph = {
        "nodes": nodes,
        "edges": edges,
        "junctions": junctions,
        "pump_patterns": pump_patterns,

        "metadata": {
            "node_count": len(nodes),
            "edge_count": len(edges),

            "networkx_node_count": nx_graph.number_of_nodes(),
            "networkx_edge_count": nx_graph.number_of_edges(),

            "source": "M1",
            "graph_type": "directed",

            "io_expected_count": io_validation["expected_count"],
            "io_found_count": io_validation["found_count"],
            "io_missing_count": io_validation["missing_count"],
            "io_missing_tags": io_validation["missing_tags"],

            # Existing: unresolved process line IDs
            "unresolved_process_lines": unresolved_process_lines,

            # NEW: reason for each unresolved process line
            "unresolved_process_line_reasons": unresolved_reasons,

            # Existing: lines not classified as process/instrument
            "unclassified_lines": unclassified_lines,
        },
    }

    return graph

# ============================================================
# BUILD FROM FILES
# ============================================================

def build_graph_from_files(
    symbols_path,
    lines_path,
    associations_path,
    io_list_path,
    output_path=None,
):
    """
    Read M1 outputs and create graph_full.json.
    """

    symbols = load_json(symbols_path)
    lines = load_json(lines_path)
    associations = load_json(associations_path)
    io_list = load_json(io_list_path)

    graph = build_graph(
        symbols=symbols,
        lines=lines,
        associations=associations,
        io_list=io_list,
    )

    if output_path:
        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                graph,
                file,
                indent=2,
            )

    return graph
