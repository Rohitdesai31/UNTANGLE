"""
UNTANGLE - Phase 4
Step 3: Process Sketch Layout

Rules:
- Main process flows left -> right.
- Parallel equipment is placed on separate rows.
- Instrumentation is placed below its related equipment.
- Existing process order from the P&ID is respected.
- Minimal crossings are supported by separating parallel paths.
- Layout information is added without changing topology.
"""


def get_node_x(node):
    """
    Get the original x-position of a node.
    Used only to preserve the original process ordering.
    """

    if node.get("x") is not None:
        return node["x"]

    bbox = node.get("bbox", [])

    if bbox:
        return bbox[0]

    return 0


def is_process_edge(edge):
    """
    Determine whether an edge represents a process connection.

    If the edge explicitly specifies a line type, use it.
    Otherwise treat the graph edge as a process connection.
    """

    line_type = edge.get("line_type")

    if line_type:
        return line_type == "process"

    return True


def get_parallel_groups(graph):
    """
    Get parallel/duty-standby equipment groups.

    pump_patterns may contain entries such as:

    {
        "pattern": "duty_standby",
        "pump_ids": ["P1", "P2"]
    }

    Returns:
        [
            {"P1", "P2"}
        ]
    """

    groups = []

    for pattern in graph.get("pump_patterns", []):

        pump_ids = pattern.get("pump_ids", [])

        if len(pump_ids) >= 2:
            groups.append(set(pump_ids))

    return groups


def calculate_layout(graph):
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    # --------------------------------------------------
    # 1. Create node lookup
    # --------------------------------------------------

    node_map = {
        node["id"]: node
        for node in nodes
    }

    # --------------------------------------------------
    # 2. Find nodes participating in process connections
    # --------------------------------------------------

    process_ids = set()

    for edge in edges:

        if not is_process_edge(edge):
            continue

        source = edge.get("source")
        target = edge.get("target")

        if source in node_map:
            process_ids.add(source)

        if target in node_map:
            process_ids.add(target)

    # --------------------------------------------------
    # 3. Main process nodes
    # --------------------------------------------------

    process_nodes = [
        node
        for node in nodes
        if node["id"] in process_ids
    ]

    # Preserve original P&ID left-to-right order.
    process_nodes.sort(key=get_node_x)

    start_x = 150
    process_y = 180
    parallel_offset = 120
    horizontal_gap = 240

    # --------------------------------------------------
    # 4. Detect parallel equipment
    # --------------------------------------------------

    parallel_groups = get_parallel_groups(graph)

    parallel_node_ids = set()

    for group in parallel_groups:
        parallel_node_ids.update(group)

    # --------------------------------------------------
    # 5. Create logical process stages
    #
    # Parallel equipment occupies ONE process stage.
    # --------------------------------------------------

    stages = []
    assigned = set()

    for node in process_nodes:

        node_id = node["id"]

        if node_id in assigned:
            continue

        # Check whether this node belongs to a parallel group.
        matching_group = None

        for group in parallel_groups:

            if node_id in group:
                matching_group = group
                break

        # ----------------------------------------------
        # Parallel stage
        # ----------------------------------------------

        if matching_group:

            group_nodes = [
                n
                for n in process_nodes
                if n["id"] in matching_group
            ]

            group_nodes.sort(key=get_node_x)

            stages.append(group_nodes)

            for group_node in group_nodes:
                assigned.add(group_node["id"])

        # ----------------------------------------------
        # Normal process stage
        # ----------------------------------------------

        else:

            stages.append([node])
            assigned.add(node_id)

    # --------------------------------------------------
    # 6. Assign process layout
    # --------------------------------------------------

    for stage_index, stage in enumerate(stages):

        stage_x = start_x + stage_index * horizontal_gap

        # ----------------------------------------------
        # Normal equipment
        # ----------------------------------------------

        if len(stage) == 1:

            node = stage[0]

            node["layout"] = {
                "x": stage_x,
                "y": process_y,
                "row": "process",
            }

        # ----------------------------------------------
        # Parallel equipment
        # ----------------------------------------------

        else:

            middle = (len(stage) - 1) / 2

            for index, node in enumerate(stage):

                y = process_y + (
                    (index - middle) * parallel_offset
                )

                node["layout"] = {
                    "x": stage_x,
                    "y": y,
                    "row": "parallel",
                }

    # --------------------------------------------------
    # 7. Find instruments / non-process nodes
    # --------------------------------------------------

    instrument_nodes = [
        node
        for node in nodes
        if node["id"] not in process_ids
    ]

    # --------------------------------------------------
    # 8. Place instruments below related equipment
    # --------------------------------------------------

    instrument_y = 380

    for index, node in enumerate(instrument_nodes):

        related_process_node = None

        # Try to find an instrument connection.
        for edge in edges:

            source = edge.get("source")
            target = edge.get("target")

            if source == node["id"]:
                related_process_node = node_map.get(target)
                break

            if target == node["id"]:
                related_process_node = node_map.get(source)
                break

        # ----------------------------------------------
        # Instrument has a related process node
        # ----------------------------------------------

        if related_process_node:

            related_layout = related_process_node.get(
                "layout",
                {}
            )

            instrument_x = related_layout.get(
                "x",
                start_x + index * horizontal_gap
            )

        # ----------------------------------------------
        # No relationship found
        # ----------------------------------------------

        else:

            instrument_x = (
                start_x
                + index * horizontal_gap
            )

        node["layout"] = {
            "x": instrument_x,
            "y": instrument_y,
            "row": "instrument",
        }

    # --------------------------------------------------
    # 9. Store layout metadata
    # --------------------------------------------------

    graph["layout"] = {
        "direction": "left-to-right",
        "process_y": process_y,
        "instrument_y": instrument_y,
        "horizontal_gap": horizontal_gap,
        "parallel_offset": parallel_offset,
        "parallel_groups": [
            list(group)
            for group in parallel_groups
        ],
    }

    return graph