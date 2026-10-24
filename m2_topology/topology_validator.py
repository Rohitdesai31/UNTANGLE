"""
UNTANGLE - Topology Validation

Validates:
1. Equipment connectivity
2. Disconnected nodes
3. Invalid connections
4. Missing equipment / IO
5. Unresolved process connections
6. Flow consistency / impossible flow
7. Branches and merges
8. Duplicate tags
9. Graph consistency
"""


PROCESS_TYPES = {
    "tank",
    "vessel",
    "pump",
    "reactor",
    "heat_exchanger",
    "valve",
    "flow_control_valve",
    "separator",
    "column",
    "compressor",
    "filter",
    "mixer",
}


def _node_id(node):
    return node.get("id") or node.get("global_id")


def _node_type(node):
    return str(
        node.get("type")
        or node.get("class_name")
        or ""
    ).lower().strip()


def _edge_source(edge):
    return (
        edge.get("source")
        or edge.get("upstream")
    )


def _edge_target(edge):
    return (
        edge.get("target")
        or edge.get("downstream")
    )


def _is_process_node(node):
    """
    Instruments are not required to be part of the process graph.
    Major process equipment is.
    """
    node_type = _node_type(node)
    tag = str(node.get("tag") or "").upper()

    if node.get("is_process_node") is True:
        return True

    if node_type in PROCESS_TYPES:
        return True

    prefixes = (
        "P-",
        "TK-",
        "T-",
        "V-",
        "R-",
        "HX-",
        "E-",
        "FCV-",
        "XV-",
        "CV-",
        "C-",
        "F-",
    )

    return tag.startswith(prefixes)


def _build_adjacency(nodes, edges):
    adjacency = {
        _node_id(node): set()
        for node in nodes
        if _node_id(node) is not None
    }

    for edge in edges:
        source = _edge_source(edge)
        target = _edge_target(edge)

        if source in adjacency and target in adjacency:
            adjacency[source].add(target)
            adjacency[target].add(source)

    return adjacency


def find_disconnected_nodes(graph):
    """
    Find process equipment having no valid process connection.
    """

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    process_nodes = [
        node for node in nodes
        if _is_process_node(node)
    ]

    adjacency = _build_adjacency(
        process_nodes,
        edges
    )

    disconnected = []

    for node in process_nodes:
        node_id = _node_id(node)

        if not adjacency.get(node_id):
            disconnected.append({
                "id": node_id,
                "tag": node.get("tag"),
                "type": _node_type(node),
                "reason": "no_process_connection",
            })

    return disconnected


def validate_connections(graph):
    """
    Every edge must connect two existing nodes.
    """

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    node_ids = {
        _node_id(node)
        for node in nodes
        if _node_id(node) is not None
    }

    invalid = []

    for edge in edges:
        source = _edge_source(edge)
        target = _edge_target(edge)

        if not source or not target:
            invalid.append({
                "edge_id": edge.get("id"),
                "source": source,
                "target": target,
                "reason": "missing_endpoint",
            })
            continue

        if source not in node_ids:
            invalid.append({
                "edge_id": edge.get("id"),
                "source": source,
                "target": target,
                "reason": "source_node_missing",
            })

        if target not in node_ids:
            invalid.append({
                "edge_id": edge.get("id"),
                "source": source,
                "target": target,
                "reason": "target_node_missing",
            })

        if source == target:
            invalid.append({
                "edge_id": edge.get("id"),
                "source": source,
                "target": target,
                "reason": "self_connection",
            })

    return invalid


def validate_unresolved_process_lines(graph):
    """
    Detect process lines that were found in the P&ID but whose
    endpoint could not be resolved to another equipment node.

    These are topology issues because the complete process
    connection is not known.
    """

    metadata = graph.get("metadata", {})

    unresolved_lines = metadata.get(
        "unresolved_process_lines",
        []
    )

    errors = []

    for line_id in unresolved_lines:
        errors.append({
            "line_id": line_id,
            "reason": "unresolved_process_connection",
        })

    return errors


def validate_flow(graph):
    """
    Validate directed process flow.

    Checks:
    - invalid upstream/downstream references
    - contradictory source/target direction
    """

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    node_ids = {
        _node_id(node)
        for node in nodes
        if _node_id(node) is not None
    }

    flow_errors = []

    for edge in edges:
        source = _edge_source(edge)
        target = _edge_target(edge)

        if source not in node_ids or target not in node_ids:
            continue

        upstream = edge.get("upstream")
        downstream = edge.get("downstream")

        if upstream is not None and upstream not in node_ids:
            flow_errors.append({
                "edge_id": edge.get("id"),
                "reason": "invalid_upstream",
                "upstream": upstream,
            })

        if downstream is not None and downstream not in node_ids:
            flow_errors.append({
                "edge_id": edge.get("id"),
                "reason": "invalid_downstream",
                "downstream": downstream,
            })

        if upstream and downstream:
            if upstream != source or downstream != target:
                flow_errors.append({
                    "edge_id": edge.get("id"),
                    "reason": "flow_direction_conflict",
                    "source": source,
                    "target": target,
                    "upstream": upstream,
                    "downstream": downstream,
                })

    return flow_errors


def validate_branches_and_merges(graph):
    """
    Validate branches and merges.

    Branch:
        one node -> multiple downstream nodes

    Merge:
        multiple upstream nodes -> one node
    """

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    node_ids = {
        _node_id(node)
        for node in nodes
        if _node_id(node) is not None
    }

    outgoing = {
        node_id: set()
        for node_id in node_ids
    }

    incoming = {
        node_id: set()
        for node_id in node_ids
    }

    for edge in edges:
        source = _edge_source(edge)
        target = _edge_target(edge)

        if source not in node_ids or target not in node_ids:
            continue

        outgoing[source].add(target)
        incoming[target].add(source)

    branches = []
    merges = []

    for node_id in node_ids:
        if len(outgoing[node_id]) > 1:
            branches.append({
                "node_id": node_id,
                "downstream": sorted(outgoing[node_id]),
            })

        if len(incoming[node_id]) > 1:
            merges.append({
                "node_id": node_id,
                "upstream": sorted(incoming[node_id]),
            })

    return {
        "branches": branches,
        "merges": merges,
    }


def find_duplicate_tags(graph):
    """
    Detect duplicate tags without merging the nodes.
    """

    nodes = graph.get("nodes", [])

    tag_map = {}

    for node in nodes:
        tag = node.get("tag")

        if not tag:
            continue

        tag = str(tag).strip()

        tag_map.setdefault(tag, []).append(
            _node_id(node)
        )

    return {
        tag: ids
        for tag, ids in tag_map.items()
        if len(ids) > 1
    }


def validate_missing_equipment(graph):
    """
    Validate missing equipment / IO.

    Missing information can come from:
    1. graph["expected_tags"]
    2. graph["metadata"]["expected_tags"]
    3. graph["metadata"]["io_missing_tags"]
    """

    nodes = graph.get("nodes", [])
    metadata = graph.get("metadata", {})

    expected_tags = (
        graph.get("expected_tags")
        or metadata.get("expected_tags")
        or []
    )

    found_tags = {
        str(node.get("tag")).strip()
        for node in nodes
        if node.get("tag")
    }

    missing = [
        str(tag).strip()
        for tag in expected_tags
        if str(tag).strip() not in found_tags
    ]

    metadata_missing = metadata.get(
        "io_missing_tags",
        []
    )

    for tag in metadata_missing:
        tag = str(tag).strip()

        if tag and tag not in missing:
            missing.append(tag)

    return missing


def validate_graph_consistency(graph):
    """
    Check basic graph consistency.
    """

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    errors = []

    node_ids = [
        _node_id(node)
        for node in nodes
    ]

    seen = set()

    for node_id in node_ids:
        if node_id is None:
            errors.append({
                "reason": "node_missing_id"
            })
            continue

        if node_id in seen:
            errors.append({
                "reason": "duplicate_node_id",
                "node_id": node_id,
            })

        seen.add(node_id)

    edge_pairs = set()

    for edge in edges:
        source = _edge_source(edge)
        target = _edge_target(edge)

        if source is None or target is None:
            continue

        pair = (source, target)

        if pair in edge_pairs:
            errors.append({
                "reason": "duplicate_edge",
                "source": source,
                "target": target,
            })

        edge_pairs.add(pair)

    return errors


def validate_topology(graph):
    """
    Run all topology validation checks.

    Returns:
        {
            "valid": bool,
            "errors": [...],
            "warnings": [...],
            ...
        }
    """

    disconnected_nodes = find_disconnected_nodes(graph)

    invalid_connections = validate_connections(graph)

    unresolved_process_lines = (
        validate_unresolved_process_lines(graph)
    )

    missing_equipment = validate_missing_equipment(graph)

    flow_errors = validate_flow(graph)

    branch_result = validate_branches_and_merges(graph)

    duplicate_tags = find_duplicate_tags(graph)

    consistency_errors = validate_graph_consistency(graph)

    errors = []

    errors.extend(invalid_connections)
    errors.extend(unresolved_process_lines)
    errors.extend(flow_errors)
    errors.extend(consistency_errors)


    warnings = []

    warnings.extend(disconnected_nodes)

    if missing_equipment:
        warnings.append({
            "reason": "missing_equipment",
            "tags": missing_equipment,
        })

    if duplicate_tags:
        warnings.append({
            "reason": "duplicate_tags",
            "tags": duplicate_tags,
        })

    unclassified_lines = graph.get("metadata", {}).get(
        "unclassified_lines", []
    )

    if unclassified_lines:
        warnings.append({
            "reason": "unclassified_lines",
            "line_ids": unclassified_lines,
        })

    return {

        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "disconnected_nodes": disconnected_nodes,
        "invalid_connections": invalid_connections,
        "unresolved_process_lines": unresolved_process_lines,
        "missing_equipment": missing_equipment,
        "flow_errors": flow_errors,
        "branches": branch_result["branches"],
        "merges": branch_result["merges"],
        "duplicate_tags": duplicate_tags,
        "consistency_errors": consistency_errors,
    }
