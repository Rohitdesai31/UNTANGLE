"""
UNTANGLE - Multi-page Topology

Handles:
1. Page references
2. Continuation lines
3. Global IDs
4. Duplicate tags
5. Cross-page connections
"""



def get_page_id(item):
    """Return the page number from an item."""

    page = item.get("page")

    if page is None:
        page = item.get("page_id")

    if page is None:
        page = item.get("page_number")

    if isinstance(page, str):
        if page.lower().startswith("page-"):
            page = page[5:]

        try:
            return int(page)
        except ValueError:
            return page

    return page


def make_global_id(prefix, local_id, page):
    """
    Create a unique ID across all pages.

    Example:
    SYM-001 on page 1 -> P1-SYM-001
    SYM-001 on page 2 -> P2-SYM-001
    """

    if local_id is None:
        return None

    return f"P{page}-{prefix}-{local_id}"


def assign_global_ids(items, prefix):
    """
    Assign globally unique IDs to symbols/lines from multiple pages.
    """

    result = []

    for item in items:
        item = item.copy()

        page = get_page_id(item)
        local_id = item.get("id")

        if page is not None and local_id is not None:
            item["local_id"] = local_id
            item["global_id"] = make_global_id(
                prefix,
                local_id,
                page
            )

        result.append(item)

    return result


def detect_duplicate_tags(symbols):
    """
    Detect duplicate equipment/instrument tags across pages.

    Duplicate tags are kept as separate global nodes.
    """

    tag_map = {}

    for symbol in symbols:
        tag = symbol.get("tag")

        if not tag:
            continue

        tag_map.setdefault(tag, []).append(
            symbol.get("global_id") or symbol.get("id")
        )

    duplicates = {
        tag: ids
        for tag, ids in tag_map.items()
        if len(ids) > 1
    }

    return duplicates



def build_page_references(pages):
    """
    Build page references using normalized page numbers.
    """

    references = []

    for page in pages:
        page_id = get_page_id(page)

        if page_id is None:
            continue

        for field, reference_type in [
            ("next_page", "next_page"),
            ("previous_page", "previous_page"),
            ("continuation_page", "continuation"),
        ]:
            target_page = page.get(field)

            if target_page is not None:
                target_page = get_page_id({"page": target_page})

                references.append({
                    "source_page": page_id,
                    "target_page": target_page,
                    "type": reference_type,
                })

        for target_page in page.get("references", []):
            target_page = get_page_id({"page": target_page})

            references.append({
                "source_page": page_id,
                "target_page": target_page,
                "type": "reference",
            })

    return references


def detect_continuation_lines(lines):
    """
    Detect lines that continue from one page to another.

    Supported fields:
    continuation
    continuation_id
    continues_from
    continues_to
    """

    continuation_lines = []

    for line in lines:
        page = get_page_id(line)
        line_id = line.get("global_id") or line.get("id")

        continuation = line.get("continuation")

        if continuation:
            continuation_lines.append({
                "line_id": line_id,
                "page": page,
                "continuation": continuation
            })

        if line.get("continuation_id"):
            continuation_lines.append({
                "line_id": line_id,
                "page": page,
                "continuation_id": line["continuation_id"]
            })

        if line.get("continues_from") is not None:
            continuation_lines.append({
                "line_id": line_id,
                "page": page,
                "continues_from": line["continues_from"]
            })

        if line.get("continues_to") is not None:
            continuation_lines.append({
                "line_id": line_id,
                "page": page,
                "continues_to": line["continues_to"]
            })

    return continuation_lines



def resolve_endpoint(endpoint, symbols):
    """
    Resolve an endpoint safely.
    Return None if it is missing or ambiguous.
    """

    if endpoint is None:
        return None

    # Exact global IDs should take priority.
    global_matches = [
        symbol for symbol in symbols
        if symbol.get("global_id") == endpoint
    ]

    if len(global_matches) == 1:
        return global_matches[0].get("global_id") or global_matches[0].get("id")

    if len(global_matches) > 1:
        return None

    # Local IDs and tags may be duplicated across pages.
    matches = [
        symbol for symbol in symbols
        if endpoint in {
            symbol.get("id"),
            symbol.get("local_id"),
            symbol.get("tag"),
        }
    ]

    if len(matches) != 1:
        return None

    return matches[0].get("global_id") or matches[0].get("id")


def build_cross_page_connections(lines, symbols):
    """
    Convert cross-page line references into global graph connections.
    """

    connections = []

    for line in lines:
        source = line.get("source")
        target = line.get("target")

        source_page = get_page_id(line)

        resolved_source = resolve_endpoint(
            source,
            symbols
        )

        resolved_target = resolve_endpoint(
            target,
            symbols
        )

        if resolved_source and resolved_target:
            target_page = None

            for symbol in symbols:
                symbol_id = symbol.get("global_id") or symbol.get("id")

                if symbol_id == resolved_target:
                    target_page = get_page_id(symbol)
                    break

            connections.append({
                "line_id": line.get("global_id") or line.get("id"),
                "source": resolved_source,
                "target": resolved_target,
                "source_page": source_page,
                "target_page": target_page,
                "cross_page": (
                    source_page is not None
                    and target_page is not None
                    and source_page != target_page
                )
            })

    return connections


def build_multipage_topology(pages, symbols, lines):
    """
    Build one global topology from all P&ID pages.
    """

    global_symbols = assign_global_ids(
        symbols,
        "SYM"
    )

    global_lines = assign_global_ids(
        lines,
        "LINE"
    )

    page_references = build_page_references(
        pages
    )

    continuation_lines = detect_continuation_lines(
        global_lines
    )

    duplicate_tags = detect_duplicate_tags(
        global_symbols
    )

    cross_page_connections = build_cross_page_connections(
        global_lines,
        global_symbols
    )

    return {
        "pages": pages,
        "symbols": global_symbols,
        "lines": global_lines,
        "page_references": page_references,
        "continuation_lines": continuation_lines,
        "duplicate_tags": duplicate_tags,
        "cross_page_connections": cross_page_connections,
        "global_topology": True
    }