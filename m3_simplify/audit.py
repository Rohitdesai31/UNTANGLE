"""
UNTANGLE - Phase 4
Step 7: Audit

Verifies that simplification did not remove required information.

Checks:
- IO coverage
- Equipment preservation
- Process connections
- Flow direction
- Duty/standby
- Missing tags
- Overall simplification result

Important:
Source-graph validation problems are reported separately from
information lost during simplification.
"""


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


def get_node_class(node):
    return (
        node.get("class_name")
        or node.get("type")
        or ""
    ).lower()


def is_io_node(node):
    """Identify IO/instrumentation nodes."""

    if node.get("is_io") is True:
        return True

    return get_node_class(node) in IO_CLASSES


def _is_connection_preserved(
    source,
    target,
    simple_edges,
):
    """
    Check whether an original connection is represented
    directly or through an M3 connectivity bridge.
    """

    for edge in simple_edges:

        if (
            edge.get("source") == source
            and edge.get("target") == target
        ):
            return True

        original_edges = set(
            edge.get("original_edge_ids", [])
        )

        if not original_edges:
            continue

        return_value = False

        if (
            edge.get("generated_by")
            == "m3_connectivity_bridge"
        ):
            return_value = True

        if return_value:
            for original_edge_id in original_edges:
                if original_edge_id:
                    return True

    return False


def _bridge_preserves_path(
    original_edge,
    simple_edges,
):
    """
    Verify that an original edge is represented by a
    simplified bridge using original edge IDs.
    """

    original_edge_id = original_edge.get("id")

    if not original_edge_id:
        return False

    for edge in simple_edges:

        if (
            edge.get("generated_by")
            != "m3_connectivity_bridge"
        ):
            continue

        if original_edge_id in edge.get(
            "original_edge_ids",
            [],
        ):
            return True

    return False


def create_audit(original_graph, simplified_graph):

    original_nodes = original_graph.get("nodes", [])
    simple_nodes = simplified_graph.get("nodes", [])

    original_edges = original_graph.get("edges", [])
    simple_edges = simplified_graph.get("edges", [])

    original_metadata = original_graph.get("metadata", {})

    # ========================================================
    # 1. TAG CHECK
    # ========================================================

    original_tags = {
        node.get("tag")
        for node in original_nodes
        if node.get("tag")
    }

    simple_tags = {
        node.get("tag")
        for node in simple_nodes
        if node.get("tag")
    }

    missing_tags = sorted(
        original_tags - simple_tags
    )

    # ========================================================
    # 2. IO COVERAGE
    # ========================================================

    source_io_tags = {
        node.get("tag")
        for node in original_nodes
        if (
            is_io_node(node)
            and node.get("tag")
        )
    }

    simple_io_tags = {
        node.get("tag")
        for node in simple_nodes
        if (
            is_io_node(node)
            and node.get("tag")
        )
    }

    expected_io_tags = set(
        original_metadata.get(
            "io_expected_tags",
            []
        )
    )

    if not expected_io_tags:
        expected_io_tags = set(source_io_tags)

    source_missing_io_tags = set(
        original_metadata.get(
            "io_missing_tags",
            []
        )
    )

    auditable_source_io_tags = (
        expected_io_tags - source_missing_io_tags
    )

    found_io_tags = (
        simple_io_tags
        & auditable_source_io_tags
    )

    missing_io_tags = sorted(
        auditable_source_io_tags - found_io_tags
    )

    io_total = len(
        auditable_source_io_tags
    )

    io_found = len(
        found_io_tags
    )

    io_missing = len(
        missing_io_tags
    )

    if io_total > 0:
        io_coverage = (
            io_found / io_total
        ) * 100
    else:
        io_coverage = 100.0

    io_pass = (
        io_missing == 0
    )

    # ========================================================
    # 3. EQUIPMENT PRESERVATION
    # ========================================================

    original_node_ids = {
        node.get("id")
        for node in original_nodes
        if node.get("id")
    }

    simple_node_ids = {
        node.get("id")
        for node in simple_nodes
        if node.get("id")
    }

    missing_equipment_ids = sorted(
        original_node_ids - simple_node_ids
    )

    # Hidden intermediate nodes are intentionally removed.
    # Only nodes marked for preservation are required.
    required_node_ids = {
        node.get("id")
        for node in original_nodes
        if (
            node.get("id")
            and node.get("preserve", False)
        )
    }

    missing_required_nodes = sorted(
        required_node_ids - simple_node_ids
    )

    equipment_pass = (
        len(missing_required_nodes) == 0
    )

    # ========================================================
    # 4. CONNECTION CHECK
    # ========================================================

    original_connections = [
        edge
        for edge in original_edges
        if (
            edge.get("preserve", True)
            and edge.get("source")
            and edge.get("target")
        )
    ]

    missing_connections = []

    for edge in original_connections:

        source = edge.get("source")
        target = edge.get("target")

        # Direct simplified connection.
        direct_connection = any(
            simple_edge.get("source") == source
            and simple_edge.get("target") == target
            for simple_edge in simple_edges
        )

        if direct_connection:
            continue

        # Original edge may be represented by an M3 bridge.
        if _bridge_preserves_path(
            edge,
            simple_edges,
        ):
            continue

        # If both endpoints remain preserved but the
        # connection disappeared, report it.
        if (
            source in simple_node_ids
            and target in simple_node_ids
        ):
            missing_connections.append(
                {
                    "source": source,
                    "target": target,
                }
            )

    connections_pass = (
        len(missing_connections) == 0
    )

    # ========================================================
    # 5. FLOW DIRECTION CHECK
    # ========================================================

    missing_flow = []

    for edge in original_connections:

        original_edge_id = edge.get("id")

        # Direct edge.
        direct_match = False

        for simple_edge in simple_edges:

            if (
                simple_edge.get("source")
                == edge.get("source")
                and
                simple_edge.get("target")
                == edge.get("target")
            ):

                if (
                    simple_edge.get(
                        "flow_direction"
                    )
                    == edge.get(
                        "flow_direction"
                    )
                ):
                    direct_match = True
                    break

        if direct_match:
            continue

        # Bridge edge.
        bridge_match = False

        for simple_edge in simple_edges:

            if (
                simple_edge.get("generated_by")
                != "m3_connectivity_bridge"
            ):
                continue

            if (
                original_edge_id
                in simple_edge.get(
                    "original_edge_ids",
                    [],
                )
            ):

                bridge_direction = simple_edge.get(
                    "flow_direction"
                )

                original_direction = edge.get(
                    "flow_direction"
                )

                if (
                    bridge_direction
                    == original_direction
                ):
                    bridge_match = True
                    break

        if bridge_match:
            continue

        if (
            edge.get("source") in simple_node_ids
            and
            edge.get("target") in simple_node_ids
        ):
            missing_flow.append(
                {
                    "source": edge.get("source"),
                    "target": edge.get("target"),
                    "flow_direction": edge.get(
                        "flow_direction"
                    ),
                    "upstream": edge.get(
                        "upstream"
                    ),
                    "downstream": edge.get(
                        "downstream"
                    ),
                }
            )

    flow_direction_pass = (
        len(missing_flow) == 0
    )

    # ========================================================
    # 6. DUTY / STANDBY CHECK
    # ========================================================

    original_duty = {
        (
            node.get("tag"),
            node.get("duty_standby"),
            node.get("duty_standby_group"),
        )
        for node in original_nodes
        if (
            node.get("duty_standby")
            or node.get("duty_standby_group")
        )
    }

    simple_duty = {
        (
            node.get("tag"),
            node.get("duty_standby"),
            node.get("duty_standby_group"),
        )
        for node in simple_nodes
        if (
            node.get("duty_standby")
            or node.get("duty_standby_group")
        )
    }

    missing_duty = sorted(
        original_duty - simple_duty
    )

    duty_standby_pass = (
        len(missing_duty) == 0
    )

    # ========================================================
    # 7. SOURCE GRAPH VALIDATION
    # ========================================================

    source_validation = original_graph.get(
        "validation",
        {}
    )

    source_validation_errors = source_validation.get(
        "errors",
        []
    )

    source_validation_warnings = source_validation.get(
        "warnings",
        []
    )

    # ========================================================
    # 8. OVERALL SIMPLIFICATION RESULT
    # ========================================================

    overall_pass = (
        io_pass
        and equipment_pass
        and connections_pass
        and flow_direction_pass
        and duty_standby_pass
    )

    # ========================================================
    # 9. FINAL AUDIT
    # ========================================================

    return {
        "io_total": io_total,

        "io_found": io_found,

        "io_missing": io_missing,

        "io_coverage_percent": round(
            io_coverage,
            2
        ),

        "missing_io_tags": missing_io_tags,

        "source_io_total": len(
            source_io_tags
        ),

        "source_io_missing": len(
            source_missing_io_tags
        ),

        "source_missing_io_tags": sorted(
            source_missing_io_tags
        ),

        "equipment_total": len(
            original_nodes
        ),

        "equipment_found": len(
            simple_nodes
        ),

        "equipment_missing": len(
            missing_required_nodes
        ),

        "missing_equipment": [
            {
                "id": node_id
            }
            for node_id in missing_required_nodes
        ],

        "missing_tags": missing_tags,

        "connections": (
            "PASS"
            if connections_pass
            else "FAIL"
        ),

        "missing_connections": missing_connections,

        "flow_direction": (
            "PASS"
            if flow_direction_pass
            else "FAIL"
        ),

        "missing_flow_direction": missing_flow,

        "duty_standby": (
            "PASS"
            if duty_standby_pass
            else "FAIL"
        ),

        "missing_duty_standby": [
            {
                "tag": tag,
                "duty_standby": status,
                "duty_standby_group": group,
            }
            for (
                tag,
                status,
                group,
            ) in missing_duty
        ],

        "source_graph_validation": {
            "valid": source_validation.get(
                "valid",
                True
            ),
            "errors": source_validation_errors,
            "warnings": source_validation_warnings,
        },

        "overall": (
            "PASS"
            if overall_pass
            else "FAIL"
        ),
    }


# ============================================================
# COMPATIBILITY ALIAS
# ============================================================

def generate_audit(original_graph, simplified_graph):
    """
    Compatibility wrapper.

    Allows the audit to be called using either:
        create_audit(...)
    or:
        generate_audit(...)
    """

    return create_audit(
        original_graph,
        simplified_graph
    )