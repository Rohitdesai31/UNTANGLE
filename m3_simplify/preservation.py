"""
UNTANGLE - Phase 4, Step 1
Preservation rules for process simplification.

Purpose:
    Decide which information from graph_full.json must survive
    the simplification stage.
"""


# ============================================================
# PRESERVATION RULES
# ============================================================

MAJOR_EQUIPMENT_CLASSES = {
    "tank",
    "pump",
    "reactor",
    "heater",
    "heat_exchanger",
    "compressor",
    "vessel",
    "column",
    "filter",
    "separator",
    "mixer",
    "blower",
}


IO_CLASSES = {
    "flow_transmitter",
    "flow_indicator_controller",
    "flow_indicator",
    "pressure_transmitter",
    "pressure_indicator",
    "temperature_transmitter",
    "temperature_indicator",
    "level_transmitter",
    "level_indicator",
    "control_valve",
    "flow_control_valve",
    "pressure_control_valve",
    "temperature_control_valve",
    "level_control_valve",
}


# ============================================================
# NODE PRESERVATION
# ============================================================

def mark_preserved_nodes(graph):
    """
    Mark every node according to preservation rules.

    Rules:
    1. Every IO-tagged node is preserved.
    2. Every major equipment node is preserved.
    3. Nodes participating in duty/standby groups are preserved.
    """

    nodes = graph.get("nodes", [])
    pump_patterns = graph.get("pump_patterns", [])

    duty_standby_nodes = set()

    for pattern in pump_patterns:
        pattern_type = pattern.get("pattern")

        if pattern_type in {
            "duty_standby",
            "duty-standby",
            "duty/standby",
        }:
            for pump_id in pattern.get("pump_ids", []):
                duty_standby_nodes.add(pump_id)

    for node in nodes:
        node_id = node.get("id")
        tag = node.get("tag")
        class_name = node.get("class_name", "").lower()

        preserve_reasons = []

        # ----------------------------------------------------
        # Rule 1: Every IO tag
        # ----------------------------------------------------
        if tag:
            node["preserve"] = True
            preserve_reasons.append("IO tag")

        # ----------------------------------------------------
        # Rule 2: Major equipment
        # ----------------------------------------------------
        if class_name in MAJOR_EQUIPMENT_CLASSES:
            node["preserve"] = True
            preserve_reasons.append("major equipment")

        # ----------------------------------------------------
        # Rule 3: IO equipment/instruments
        # ----------------------------------------------------
        if class_name in IO_CLASSES:
            node["preserve"] = True
            preserve_reasons.append("IO equipment")

        # ----------------------------------------------------
        # Rule 4: Duty / standby
        # ----------------------------------------------------
        if node_id in duty_standby_nodes:
            node["preserve"] = True
            preserve_reasons.append("duty/standby")

        # ----------------------------------------------------
        # Default
        # ----------------------------------------------------
        if not preserve_reasons:
            node["preserve"] = False
            preserve_reasons.append("not required")

        node["preservation_reasons"] = preserve_reasons

    return graph


# ============================================================
# EDGE PRESERVATION
# ============================================================

def mark_preserved_edges(graph):
    """
    Mark process connections that must remain in the
    simplified graph.

    Every validated process connection is preserved.
    Flow direction is also preserved.
    """

    edges = graph.get("edges", [])

    for edge in edges:
        edge["preserve"] = True

        reasons = [
            "correct process connection"
        ]

        # ----------------------------------------------------
        # Preserve flow direction
        # ----------------------------------------------------
        flow_direction = edge.get("flow_direction")

        if flow_direction:
            reasons.append("flow direction")

        if edge.get("upstream"):
            reasons.append("upstream/downstream")

        if edge.get("downstream"):
            reasons.append("upstream/downstream")

        edge["preservation_reasons"] = list(dict.fromkeys(reasons))

    return graph


# ============================================================
# BRANCH / MERGE PRESERVATION
# ============================================================

def mark_preserved_branches(graph):
    """
    Preserve important branches and merges.

    A node with more than one outgoing connection is a branch.
    A node with more than one incoming connection is a merge.
    """

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    incoming = {}
    outgoing = {}

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")

        if source:
            outgoing[source] = outgoing.get(source, 0) + 1

        if target:
            incoming[target] = incoming.get(target, 0) + 1

    for node in nodes:
        node_id = node.get("id")

        reasons = node.setdefault(
            "preservation_reasons",
            []
        )

        # ----------------------------------------------------
        # Branch
        # ----------------------------------------------------
        if outgoing.get(node_id, 0) > 1:
            node["preserve"] = True

            if "important branch" not in reasons:
                reasons.append("important branch")

        # ----------------------------------------------------
        # Merge
        # ----------------------------------------------------
        if incoming.get(node_id, 0) > 1:
            node["preserve"] = True

            if "important merge" not in reasons:
                reasons.append("important merge")

    return graph


# ============================================================
# MAIN PRESERVATION FUNCTION
# ============================================================

def apply_preservation_rules(graph):
    """
    Apply all Phase 4 preservation rules.

    Order:
        1. Nodes
        2. Connections
        3. Branches / merges
    """

    graph = mark_preserved_nodes(graph)
    graph = mark_preserved_edges(graph)
    graph = mark_preserved_branches(graph)

    graph["preservation"] = {
        "io_tags": True,
        "major_equipment": True,
        "correct_connections": True,
        "flow_direction": True,
        "duty_standby": True,
        "important_branches": True,
    }

    return graph


# ============================================================
# PRESERVATION CHECK
# ============================================================

def check_preservation(graph):
    """
    Verify that all required preservation rules are enabled
    and preserved nodes/connections are present.
    """

    errors = []

    preservation = graph.get("preservation", {})

    required_rules = [
        "io_tags",
        "major_equipment",
        "correct_connections",
        "flow_direction",
        "duty_standby",
        "important_branches",
    ]

    for rule in required_rules:
        if preservation.get(rule) is not True:
            errors.append(
                f"Preservation rule missing: {rule}"
            )

    for node in graph.get("nodes", []):
        if node.get("tag") and not node.get("preserve"):
            errors.append(
                f"IO tag was not preserved: {node.get('tag')}"
            )

    for edge in graph.get("edges", []):
        if not edge.get("preserve"):
            errors.append(
                "Process connection was not preserved: "
                f"{edge.get('source')} -> {edge.get('target')}"
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }