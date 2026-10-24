"""
UNTANGLE - Phase 4
Step 4: Clean Connection Routing

Creates simple orthogonal routes between laid-out nodes.

Rules:
- Preserve source -> target direction.
- Prefer horizontal routing for the main process.
- Use vertical routing when appropriate.
- Avoid unnecessary zero-length segments.
- Avoid unnecessary route crossings and overlaps.
- Allow outside corridors when the direct corridor conflicts.
- Keep routing independent from topology.
"""

# ============================================================
# BASIC ROUTE HELPERS
# ============================================================


def _remove_duplicate_points(points):
    """Remove consecutive duplicate points."""

    cleaned = []

    for point in points:
        if not cleaned or point != cleaned[-1]:
            cleaned.append(point)

    return cleaned


def _route_horizontal(
    source_x,
    source_y,
    target_x,
    target_y,
    middle_x,
):
    """
    Create a horizontal-first orthogonal route.

    Example:

        source ---------
                       |
                       |
                       -------- target
    """

    return _remove_duplicate_points(
        [
            [source_x, source_y],
            [middle_x, source_y],
            [middle_x, target_y],
            [target_x, target_y],
        ]
    )


def _route_vertical(
    source_x,
    source_y,
    target_x,
    target_y,
    middle_y,
):
    """
    Create a vertical-first orthogonal route.

    Example:

        source
          |
          |
          ---------------- target
    """

    return _remove_duplicate_points(
        [
            [source_x, source_y],
            [source_x, middle_y],
            [target_x, middle_y],
            [target_x, target_y],
        ]
    )


def _segments(route):
    """Convert route points into segments."""

    return [
        (route[index], route[index + 1])
        for index in range(len(route) - 1)
    ]


# ============================================================
# GEOMETRY HELPERS
# ============================================================


def _orientation(a, b, c):
    """
    Return orientation of three points.

    Returns:
        0 = collinear
        1 = clockwise
        2 = counter-clockwise
    """

    value = (
        (b[1] - a[1]) * (c[0] - b[0])
        - (b[0] - a[0]) * (c[1] - b[1])
    )

    if value == 0:
        return 0

    return 1 if value > 0 else 2


def _on_segment(a, b, c):
    """Check whether point b lies on segment a-c."""

    return (
        min(a[0], c[0]) <= b[0] <= max(a[0], c[0])
        and
        min(a[1], c[1]) <= b[1] <= max(a[1], c[1])
    )


def _is_horizontal(segment):
    """Return True if a segment is horizontal."""

    start, end = segment
    return start[1] == end[1]


def _is_vertical(segment):
    """Return True if a segment is vertical."""

    start, end = segment
    return start[0] == end[0]


def _segments_overlap(segment_a, segment_b):
    """
    Detect positive-length overlap between two segments.

    Endpoint touching alone is NOT considered overlap.

    Examples:

        [0,0] -> [100,0]
        [50,0] -> [150,0]

    These overlap from x=50 to x=100, so True.

    But:

        [0,0] -> [100,0]
        [100,0] -> [150,0]

    Only touch at an endpoint, so False.
    """

    a1, a2 = segment_a
    b1, b2 = segment_b

    # --------------------------------------------------------
    # Horizontal overlap
    # --------------------------------------------------------

    if _is_horizontal(segment_a) and _is_horizontal(segment_b):

        if a1[1] != b1[1]:
            return False

        left = max(
            min(a1[0], a2[0]),
            min(b1[0], b2[0]),
        )

        right = min(
            max(a1[0], a2[0]),
            max(b1[0], b2[0]),
        )

        return right > left

    # --------------------------------------------------------
    # Vertical overlap
    # --------------------------------------------------------

    if _is_vertical(segment_a) and _is_vertical(segment_b):

        if a1[0] != b1[0]:
            return False

        bottom = max(
            min(a1[1], a2[1]),
            min(b1[1], b2[1]),
        )

        top = min(
            max(a1[1], a2[1]),
            max(b1[1], b2[1]),
        )

        return top > bottom

    return False


def _segments_cross(segment_a, segment_b):
    """
    Detect a real crossing between two segments.

    Endpoint-only contact is NOT considered a crossing.

    Positive-length overlap is handled separately by
    _segments_overlap().
    """

    a1, a2 = segment_a
    b1, b2 = segment_b

    # Collinear segments are handled by _segments_overlap().
    if (
        _orientation(a1, a2, b1) == 0
        and _orientation(a1, a2, b2) == 0
    ):
        return False

    # --------------------------------------------------------
    # Horizontal vs vertical
    # --------------------------------------------------------

    if _is_horizontal(segment_a) and _is_vertical(segment_b):

        horizontal_y = a1[1]
        vertical_x = b1[0]

        horizontal_left = min(a1[0], a2[0])
        horizontal_right = max(a1[0], a2[0])

        vertical_bottom = min(b1[1], b2[1])
        vertical_top = max(b1[1], b2[1])

        if (
            horizontal_left < vertical_x < horizontal_right
            and
            vertical_bottom < horizontal_y < vertical_top
        ):
            return True

        return False

    # --------------------------------------------------------
    # Vertical vs horizontal
    # --------------------------------------------------------

    if _is_vertical(segment_a) and _is_horizontal(segment_b):

        return _segments_cross(
            segment_b,
            segment_a,
        )

    return False


def _shared_endpoint(segment_a, segment_b):
    """
    Check whether two segments only meet at an endpoint.

    This is allowed for normal node-to-node connections.

    Important:
    If the segments have a positive-length overlap, this function
    returns False because overlap is a real routing conflict.
    """

    # Positive-length overlap is NOT harmless.
    if _segments_overlap(segment_a, segment_b):
        return False

    endpoints_a = {
        tuple(segment_a[0]),
        tuple(segment_a[1]),
    }

    endpoints_b = {
        tuple(segment_b[0]),
        tuple(segment_b[1]),
    }

    shared = endpoints_a.intersection(endpoints_b)

    if not shared:
        return False

    # If the segments cross through the shared point rather than
    # simply ending there, it is not an ordinary endpoint join.
    if _segments_cross(segment_a, segment_b):
        return False

    return True


# ============================================================
# ROUTE CONFLICT
# ============================================================


def _route_conflict_score(route, existing_routes):
    """
    Calculate route conflict.

    Score:
        0   = clean route
        1   = harmless endpoint connection
        100 = crossing or overlapping route

    Lower is better.
    """

    score = 0

    for candidate_segment in _segments(route):

        for existing_route in existing_routes:

            for existing_segment in _segments(existing_route):

                # ------------------------------------------------
                # Positive-length overlap
                # ------------------------------------------------

                if _segments_overlap(
                    candidate_segment,
                    existing_segment,
                ):
                    score += 100
                    continue

                # ------------------------------------------------
                # Real crossing
                # ------------------------------------------------

                if _segments_cross(
                    candidate_segment,
                    existing_segment,
                ):
                    score += 100
                    continue

                # ------------------------------------------------
                # Harmless endpoint connection
                # ------------------------------------------------

                if _shared_endpoint(
                    candidate_segment,
                    existing_segment,
                ):
                    score += 1

    return score


def _route_length(route):
    """Calculate Manhattan route length."""

    length = 0

    for start, end in _segments(route):

        length += abs(end[0] - start[0])
        length += abs(end[1] - start[1])

    return length


def _route_bends(route):
    """Return number of bends in a route."""

    segments = _segments(route)

    if len(segments) <= 1:
        return 0

    bends = 0

    previous_horizontal = _is_horizontal(segments[0])

    for segment in segments[1:]:

        current_horizontal = _is_horizontal(segment)

        if current_horizontal != previous_horizontal:
            bends += 1

        previous_horizontal = current_horizontal

    return bends


# ============================================================
# CANDIDATE ROUTES
# ============================================================


def _candidate_horizontal_routes(
    source_x,
    source_y,
    target_x,
    target_y,
):
    """
    Generate horizontal-first routes.

    Includes:
    - normal middle corridor
    - inner corridors
    - outside-left corridor
    - outside-right corridor
    """

    distance = abs(target_x - source_x)

    if distance == 0:
        return []

    minimum_x = min(source_x, target_x)
    maximum_x = max(source_x, target_x)

    offset = max(
        60,
        distance * 0.25,
    )

    candidates_x = [
        # Normal corridor.
        (source_x + target_x) / 2,

        # Inner corridors.
        source_x + offset,
        target_x - offset,

        # Additional inner corridors.
        source_x + 120,
        target_x - 120,

        # Outside corridors.
        minimum_x - offset,
        maximum_x + offset,

        minimum_x - 120,
        maximum_x + 120,

        minimum_x - 180,
        maximum_x + 180,
    ]

    routes = []

    for middle_x in candidates_x:

        route = _route_horizontal(
            source_x,
            source_y,
            target_x,
            target_y,
            middle_x,
        )

        if route not in routes:
            routes.append(route)

    return routes


def _candidate_vertical_routes(
    source_x,
    source_y,
    target_x,
    target_y,
):
    """
    Generate vertical-first routes.

    Includes:
    - normal middle corridor
    - inner corridors
    - outside-top corridor
    - outside-bottom corridor

    These candidates are important because a vertical detour
    may be required to avoid a horizontal route conflict.
    """

    distance = abs(target_y - source_y)

    if distance == 0:
        return []

    minimum_y = min(source_y, target_y)
    maximum_y = max(source_y, target_y)

    offset = max(
        60,
        distance * 0.25,
    )

    candidates_y = [
        # Normal corridor.
        (source_y + target_y) / 2,

        # Inner corridors.
        source_y + offset,
        target_y - offset,

        # Additional inner corridors.
        source_y + 120,
        target_y - 120,

        # Outside corridors.
        minimum_y - offset,
        maximum_y + offset,

        minimum_y - 120,
        maximum_y + 120,

        minimum_y - 180,
        maximum_y + 180,
    ]

    routes = []

    for middle_y in candidates_y:

        route = _route_vertical(
            source_x,
            source_y,
            target_x,
            target_y,
            middle_y,
        )

        if route not in routes:
            routes.append(route)

    return routes


def _all_candidate_routes(
    source_x,
    source_y,
    target_x,
    target_y,
):
    """
    Generate BOTH horizontal-first and vertical-first candidates.

    This is important for crossing avoidance.

    Even when the main process is horizontal, a vertical-first
    outside corridor can be selected if every horizontal route
    conflicts with an existing route.
    """

    candidates = []

    horizontal_routes = _candidate_horizontal_routes(
        source_x,
        source_y,
        target_x,
        target_y,
    )

    vertical_routes = _candidate_vertical_routes(
        source_x,
        source_y,
        target_x,
        target_y,
    )

    for route in horizontal_routes:

        candidates.append(
            (
                "horizontal",
                route,
            )
        )

    for route in vertical_routes:

        candidates.append(
            (
                "vertical",
                route,
            )
        )

    # Remove duplicate routes.
    unique = []
    seen = set()

    for orientation, route in candidates:

        route_key = tuple(
            tuple(point)
            for point in route
        )

        if route_key in seen:
            continue

        seen.add(route_key)

        unique.append(
            (
                orientation,
                route,
            )
        )

    return unique


# ============================================================
# ROUTE CALCULATION
# ============================================================


def _calculate_route(
    source_x,
    source_y,
    target_x,
    target_y,
    existing_routes=None,
):
    """
    Select the cleanest orthogonal route.

    Priority:
        1. Avoid crossings and overlaps.
        2. Prefer horizontal routing for the main process.
        3. Prefer fewer bends.
        4. Prefer shorter routes.

    Important:
    A conflict-free vertical route is always preferred over
    a conflicting horizontal route.
    """

    if existing_routes is None:
        existing_routes = []

    dx = abs(target_x - source_x)
    dy = abs(target_y - source_y)

    # --------------------------------------------------------
    # Same position.
    # --------------------------------------------------------

    if dx == 0 and dy == 0:
        return [[source_x, source_y]]

    # --------------------------------------------------------
    # Direct horizontal connection.
    # --------------------------------------------------------

    if dy == 0:

        direct_route = [
            [source_x, source_y],
            [target_x, target_y],
        ]

        # If direct route conflicts, generate alternatives.
        direct_score = _route_conflict_score(
            direct_route,
            existing_routes,
        )

        if direct_score == 0:
            return direct_route

        candidates = []

        # Vertical detours can avoid an overlapping horizontal route.
        minimum_y = min(source_y, target_y)
        maximum_y = max(source_y, target_y)

        for middle_y in [
            source_y - 60,
            source_y + 60,
            minimum_y - 120,
            maximum_y + 120,
        ]:

            route = _route_vertical(
                source_x,
                source_y,
                target_x,
                target_y,
                middle_y,
            )

            candidates.append(route)

        candidates.append(direct_route)

        return min(
            candidates,
            key=lambda route: (
                _route_conflict_score(
                    route,
                    existing_routes,
                ),
                _route_bends(route),
                _route_length(route),
            ),
        )

    # --------------------------------------------------------
    # Direct vertical connection.
    # --------------------------------------------------------

    if dx == 0:

        direct_route = [
            [source_x, source_y],
            [target_x, target_y],
        ]

        direct_score = _route_conflict_score(
            direct_route,
            existing_routes,
        )

        if direct_score == 0:
            return direct_route

        candidates = []

        minimum_x = min(source_x, target_x)
        maximum_x = max(source_x, target_x)

        for middle_x in [
            source_x - 60,
            source_x + 60,
            minimum_x - 120,
            maximum_x + 120,
        ]:

            route = _route_horizontal(
                source_x,
                source_y,
                target_x,
                target_y,
                middle_x,
            )

            candidates.append(route)

        candidates.append(direct_route)

        return min(
            candidates,
            key=lambda route: (
                _route_conflict_score(
                    route,
                    existing_routes,
                ),
                _route_bends(route),
                _route_length(route),
            ),
        )

    # --------------------------------------------------------
    # General case.
    # --------------------------------------------------------

    candidates = _all_candidate_routes(
        source_x,
        source_y,
        target_x,
        target_y,
    )

    if not candidates:

        return [
            [source_x, source_y],
            [target_x, target_y],
        ]

    # Main process preference.
    horizontal_preferred = dx >= dy

    def route_sort_key(candidate):
        orientation, route = candidate

        conflict_score = _route_conflict_score(
            route,
            existing_routes,
        )

        # Horizontal process is preferred when possible.
        if horizontal_preferred:
            orientation_penalty = (
                0 if orientation == "horizontal" else 1
            )
        else:
            orientation_penalty = (
                0 if orientation == "vertical" else 1
            )

        return (
            conflict_score,
            orientation_penalty,
            _route_bends(route),
            _route_length(route),
        )

    best_orientation, best_route = min(
        candidates,
        key=route_sort_key,
    )

    return best_route


# ============================================================
# COUNT ROUTING CONFLICTS
# ============================================================


def _count_route_conflicts(routes):
    """
    Count actual crossing/overlap conflicts.

    Endpoint-only connections are allowed.
    """

    conflicts = 0

    for index in range(len(routes)):

        for other_index in range(
            index + 1,
            len(routes),
        ):

            route_a = routes[index]
            route_b = routes[other_index]

            for segment_a in _segments(route_a):

                for segment_b in _segments(route_b):

                    # Positive-length overlap.
                    if _segments_overlap(
                        segment_a,
                        segment_b,
                    ):
                        conflicts += 1
                        continue

                    # Real crossing.
                    if _segments_cross(
                        segment_a,
                        segment_b,
                    ):
                        conflicts += 1
                        continue

                    # Endpoint-only connection is allowed.
                    if _shared_endpoint(
                        segment_a,
                        segment_b,
                    ):
                        continue

    return conflicts


# ============================================================
# GRAPH ROUTING
# ============================================================


def route_edges(graph):
    """
    Add conflict-aware orthogonal routes to graph edges.

    Each edge receives:

        edge["route"]

    and:

        edge["routing"]
    """

    node_map = {
        node["id"]: node
        for node in graph.get("nodes", [])
    }

    routed_count = 0
    skipped_count = 0

    existing_routes = []

    for edge in graph.get("edges", []):

        source_id = edge.get("source")
        target_id = edge.get("target")

        source = node_map.get(source_id)
        target = node_map.get(target_id)

        # ----------------------------------------------------
        # Missing source/target node.
        # ----------------------------------------------------

        if not source or not target:

            skipped_count += 1
            continue

        source_layout = source.get(
            "layout",
            {},
        )

        target_layout = target.get(
            "layout",
            {},
        )

        # ----------------------------------------------------
        # Missing layout.
        # ----------------------------------------------------

        if (
            "x" not in source_layout
            or "y" not in source_layout
            or "x" not in target_layout
            or "y" not in target_layout
        ):

            skipped_count += 1
            continue

        x1 = source_layout["x"]
        y1 = source_layout["y"]

        x2 = target_layout["x"]
        y2 = target_layout["y"]

        # ----------------------------------------------------
        # Calculate conflict-aware route.
        # ----------------------------------------------------

        route = _calculate_route(
            x1,
            y1,
            x2,
            y2,
            existing_routes,
        )

        edge["route"] = route

        edge["routing"] = {
            "type": "orthogonal",
            "source": source_id,
            "target": target_id,
            "bends": _route_bends(route),
            "length": _route_length(route),
        }

        existing_routes.append(route)

        routed_count += 1

    # --------------------------------------------------------
    # Final conflict check.
    # --------------------------------------------------------

    crossing_conflicts = _count_route_conflicts(
        existing_routes
    )

    graph["routing"] = {
        "type": "orthogonal",
        "routed_edges": routed_count,
        "skipped_edges": skipped_count,
        "crossing_conflicts": crossing_conflicts,
    }

    return graph