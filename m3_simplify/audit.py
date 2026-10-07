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

    # Actual IO tags detected in the source P&ID.
    source_io_tags = {
        node.get("tag")
        for node in original_nodes
        if (
            is_io_node(node)
            and node.get("tag")
        )
    }

    # IO tags actually found in simplified graph.
    simple_io_tags = {
        node.get("tag")
        for node in simple_nodes
        if (
            is_io_node(node)
            and node.get("tag")
        )
    }

    # IO tags expected by the original source graph.
    expected_io_tags = set(
        original_metadata.get(
            "io_expected_tags",
            []
        )
    )

    # If expected tags are unavailable, use actual source IO.
    if not expected_io_tags:
        expected_io_tags = set(source_io_tags)

    # IO tags that were missing from the original P&ID itself.
    source_missing_io_tags = set(
        original_metadata.get(
            "io_missing_tags",
            []
        )
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Source-missing IO is NOT treated as simplification loss.
    #
    # Example:
    # Expected by IO list = FT-999
    # But FT-999 was never present in source P&ID.
    #
    # Therefore it cannot be considered an IO removed by
    # simplification.
    # --------------------------------------------------------

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

    equipment_pass = (
        len(missing_equipment_ids) == 0
    )

    # ========================================================
    # 4. CONNECTION CHECK
    # ========================================================

    original_connections = {
        (
            edge.get("source"),
            edge.get("target"),
        )
        for edge in original_edges
        if (
            edge.get("preserve", True)
            and edge.get("source")
            and edge.get("target")
        )
    }

    simple_connections = {
        (
            edge.get("source"),
            edge.get("target"),
        )
        for edge in simple_edges
        if (
            edge.get("source")
            and edge.get("target")
        )
    }

    missing_connections = sorted(
        original_connections - simple_connections
    )

    connections_pass = (
        len(missing_connections) == 0
    )

    # ========================================================
    # 5. FLOW DIRECTION CHECK
    # ========================================================

    original_flow = {
        (
            edge.get("source"),
            edge.get("target"),
            edge.get("flow_direction"),
            edge.get("upstream"),
            edge.get("downstream"),
        )
        for edge in original_edges
        if edge.get("preserve", True)
    }

    simple_flow = {
        (
            edge.get("source"),
            edge.get("target"),
            edge.get("flow_direction"),
            edge.get("upstream"),
            edge.get("downstream"),
        )
        for edge in simple_edges
    }

    missing_flow = sorted(
        original_flow - simple_flow
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

    # IMPORTANT:
    # Source-level missing IO and unresolved source connections
    # are reported separately.
    #
    # They do NOT automatically mean that simplification lost
    # information.

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
            missing_equipment_ids
        ),

        "missing_equipment": [
            {
                "id": node_id
            }
            for node_id in missing_equipment_ids
        ],

        "missing_tags": missing_tags,

        "connections": (
            "PASS"
            if connections_pass
            else "FAIL"
        ),

        "missing_connections": [
            {
                "source": source,
                "target": target,
            }
            for source, target in missing_connections
        ],

        "flow_direction": (
            "PASS"
            if flow_direction_pass
            else "FAIL"
        ),

        "missing_flow_direction": [
            {
                "source": source,
                "target": target,
                "flow_direction": flow_direction,
                "upstream": upstream,
                "downstream": downstream,
            }
            for (
                source,
                target,
                flow_direction,
                upstream,
                downstream,
            ) in missing_flow
        ],

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