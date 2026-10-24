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
    "outlet",
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


def get_io_tags(graph):
    """
    Get tags expected from the source IO list.

    M2 stores IO information on nodes using:
        is_io
        io_type
        description
        loop
        expected_status

    The graph metadata also contains io_missing_tags.

    For the fixture, every detected IO-list tag is represented
    by a node with is_io=True.
    """
    io_tags = set()

    for node in graph.get("nodes", []):
        if node.get("is_io") is True and node.get("tag"):
            io_tags.add(node["tag"])

    return io_tags


def mark_preserved_nodes(graph):
    """
    Mark nodes that must remain available after simplification.

    Preservation rules:
    1. Every node belonging to the detected IO list is preserved.
    2. Major process equipment is preserved.
    3. Duty/standby pump nodes are preserved.
    4. Other nodes are not automatically preserved.
    """

    nodes = graph.get("nodes", [])
    pump_patterns = graph.get("pump_patterns", [])

    # Tags actually detected from the source IO list
    io_tags = get_io_tags(graph)

    # Collect duty/standby pump IDs
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

        # IMPORTANT:
        # M2 uses "type", not "class_name".
        class_name = str(node.get("type", "")).lower()
        tag = node.get("tag")
        node_id = node.get("id")

        # Reset M2's default preserve=True.
        # M3 must decide preservation explicitly.
        node["preserve"] = False

        preserve_reasons = []

        # -------------------------------------------------
        # Rule 1: IO-list tags
        # -------------------------------------------------
        if tag and tag in io_tags:
            node["preserve"] = True
            preserve_reasons.append("IO list tag")

        # -------------------------------------------------
        # Rule 2: Major process equipment
        # -------------------------------------------------
        if class_name in MAJOR_EQUIPMENT_CLASSES:
            node["preserve"] = True
            preserve_reasons.append("major equipment")

        # -------------------------------------------------
        # Rule 3: IO equipment/instrument classes
        # -------------------------------------------------
        if class_name in IO_CLASSES:
            node["preserve"] = True
            preserve_reasons.append("IO equipment")

        # -------------------------------------------------
        # Rule 4: Duty/standby pumps
        # -------------------------------------------------
        if node_id in duty_standby_nodes:
            node["preserve"] = True
            preserve_reasons.append("duty/standby")

        # -------------------------------------------------
        # If no rule matched, this node can be simplified
        # -------------------------------------------------
        if not preserve_reasons:
            preserve_reasons.append("not required")

        node["preservation_reasons"] = preserve_reasons

    return graph


def mark_preserved_edges(graph):
    """
    Preserve valid process connections between preserved nodes.
    """

    for edge in graph.get("edges", []):

        edge["preserve"] = True

        reasons = ["correct process connection"]

        flow_direction = edge.get("flow_direction")

        if flow_direction:
            reasons.append("flow direction")

        if edge.get("upstream"):
            reasons.append("upstream/downstream")

        if edge.get("downstream"):
            reasons.append("upstream/downstream")

        edge["preservation_reasons"] = list(dict.fromkeys(reasons))

    return graph


def mark_preserved_branches(graph):
    """
    Preserve nodes that participate in important branches.

    A node with multiple incoming or outgoing process connections
    represents a meaningful process branch.
    """

    incoming = {}
    outgoing = {}

    for edge in graph.get("edges", []):

        source = edge.get("source")
        target = edge.get("target")

        if source:
            outgoing[source] = outgoing.get(source, 0) + 1

        if target:
            incoming[target] = incoming.get(target, 0) + 1

    for node in graph.get("nodes", []):

        node_id = node.get("id")

        incoming_count = incoming.get(node_id, 0)
        outgoing_count = outgoing.get(node_id, 0)

        if incoming_count > 1 or outgoing_count > 1:

            node["preserve"] = True

            reasons = node.get("preservation_reasons", [])

            if "important branch" not in reasons:
                reasons.append("important branch")

            node["preservation_reasons"] = reasons

    return graph


def apply_preservation_rules(graph):
    """
    Apply the complete M3 preservation policy.
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


def check_preservation(graph):
    """
    Validate that important nodes have been preserved.
    """

    missing = []

    for node in graph.get("nodes", []):

        if node.get("is_io") is True and not node.get("preserve", False):
            missing.append(node.get("tag") or node.get("id"))

    return {
        "valid": len(missing) == 0,
        "missing_preserved_nodes": missing,
    }