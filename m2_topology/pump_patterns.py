"""
UNTANGLE - Pump Pattern Detection
Detect parallel and duty/standby pumps.
"""


def is_pump(node):
    node_type = str(node.get("type", "")).lower()
    tag = str(node.get("tag", "")).lower()

    return (
        "pump" in node_type
        or tag.startswith("p-")
        or tag.startswith("p_")
    )


def similar_pump_tags(tag_a, tag_b):
    """
    Check whether two pump tags represent the same pump family.

    Example:
    P-101A and P-101B -> True
    P-101A and P-102A -> False
    """

    if not tag_a or not tag_b:
        return False

    tag_a = str(tag_a).upper().strip()
    tag_b = str(tag_b).upper().strip()

    if not tag_a.startswith("P-") or not tag_b.startswith("P-"):
        return False

    base_a = tag_a[:-1] if tag_a[-1:].isalpha() else tag_a
    base_b = tag_b[:-1] if tag_b[-1:].isalpha() else tag_b

    return base_a == base_b


def detect_pump_patterns(graph):
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    incoming = {}
    outgoing = {}

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")

        if source and target:
            incoming.setdefault(target, []).append(edge)
            outgoing.setdefault(source, []).append(edge)

    pumps = [
        node
        for node in nodes
        if is_pump(node)
    ]

    pump_patterns = []

    # ----------------------------------------
    # Detect explicitly declared duty/standby
    # ----------------------------------------

    duty_groups = {}

    for pump in pumps:
        group = pump.get("duty_standby_group")

        if group:
            duty_groups.setdefault(group, []).append(pump)

    for group, group_pumps in duty_groups.items():

        if len(group_pumps) < 2:
            continue

        pump_patterns.append({
            "type": "duty_standby",
            "pump_ids": [
                pump["id"]
                for pump in group_pumps
            ],
            "pump_tags": [
                pump.get("tag")
                for pump in group_pumps
            ],
            "duty_standby_group": group,
        })

    # ----------------------------------------
    # Detect parallel / duty-standby pumps
    # ----------------------------------------

    for i in range(len(pumps)):
        for j in range(i + 1, len(pumps)):

            pump_a = pumps[i]
            pump_b = pumps[j]

            # Same equipment type
            same_type = (
                str(pump_a.get("type", "")).lower()
                == str(pump_b.get("type", "")).lower()
            )

            if not same_type:
                continue

            # Similar pump tags
            similar_tags = similar_pump_tags(
                pump_a.get("tag"),
                pump_b.get("tag")
            )

            if not similar_tags:
                continue

            # Find upstream connections
            a_in = {
                edge.get("upstream", edge.get("source"))
                for edge in incoming.get(pump_a["id"], [])
            }

            b_in = {
                edge.get("upstream", edge.get("source"))
                for edge in incoming.get(pump_b["id"], [])
            }

            # Find downstream connections
            a_out = {
                edge.get("downstream", edge.get("target"))
                for edge in outgoing.get(pump_a["id"], [])
            }

            b_out = {
                edge.get("downstream", edge.get("target"))
                for edge in outgoing.get(pump_b["id"], [])
            }

            same_upstream = bool(a_in & b_in)
            same_downstream = bool(a_out & b_out)

            # Duty/standby requires:
            # same type + similar tags + same upstream + same downstream
            if same_upstream and same_downstream:

                group_id = (
                    pump_a.get("duty_standby_group")
                    or pump_b.get("duty_standby_group")
                    or f"GROUP-{pump_a['id']}-{pump_b['id']}"
                )

                pump_patterns.append({
                    "type": "duty_standby",
                    "pump_ids": [
                        pump_a["id"],
                        pump_b["id"],
                    ],
                    "pump_tags": [
                        pump_a.get("tag"),
                        pump_b.get("tag"),
                    ],
                    "duty_standby_group": group_id,
                })

    return pump_patterns