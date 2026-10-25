
from m2_topology.multipage import (
    get_page_id,
    assign_global_ids,
    detect_duplicate_tags,
    build_page_references,
    detect_continuation_lines,
    build_cross_page_connections,
)


def test_page_id_normalization():
    assert get_page_id({"page": "page-2"}) == 2
    assert get_page_id({"page": 3}) == 3


def test_global_ids_are_page_specific():
    symbols = [
        {"id": "SYM-001", "page": 1},
        {"id": "SYM-001", "page": 2},
    ]

    result = assign_global_ids(symbols, "SYM")

    assert result[0]["global_id"] == "P1-SYM-SYM-001"
    assert result[1]["global_id"] == "P2-SYM-SYM-001"
    assert result[0]["global_id"] != result[1]["global_id"]


def test_duplicate_tags_are_detected():
    symbols = [
        {"id": "S1", "global_id": "P1-SYM-S1", "tag": "P-101"},
        {"id": "S2", "global_id": "P2-SYM-S2", "tag": "P-101"},
        {"id": "S3", "global_id": "P2-SYM-S3", "tag": "V-101"},
    ]

    duplicates = detect_duplicate_tags(symbols)

    assert "P-101" in duplicates
    assert len(duplicates["P-101"]) == 2
    assert "V-101" not in duplicates


def test_page_references_are_created():
    pages = [
        {"page": 1, "next_page": 2},
        {"page": 2, "previous_page": 1},
    ]

    references = build_page_references(pages)

    assert len(references) == 2
    assert references[0]["source_page"] == 1
    assert references[0]["target_page"] == 2
    assert references[0]["type"] == "next_page"


def test_continuation_lines_are_detected():
    lines = [
        {
            "id": "L1",
            "global_id": "P1-LINE-L1",
            "page": 1,
            "continuation_id": "CONT-10",
        }
    ]

    result = detect_continuation_lines(lines)

    assert len(result) == 1
    assert result[0]["line_id"] == "P1-LINE-L1"
    assert result[0]["continuation_id"] == "CONT-10"


def test_cross_page_connection():
    symbols = [
        {
            "id": "S1",
            "global_id": "P1-SYM-S1",
            "page": 1,
        },
        {
            "id": "S2",
            "global_id": "P2-SYM-S2",
            "page": 2,
        },
    ]

    lines = [
        {
            "id": "L1",
            "global_id": "P1-LINE-L1",
            "page": 1,
            "source": "P1-SYM-S1",
            "target": "P2-SYM-S2",
        }
    ]

    result = build_cross_page_connections(lines, symbols)

    assert len(result) == 1
    assert result[0]["source"] == "P1-SYM-S1"
    assert result[0]["target"] == "P2-SYM-S2"
    assert result[0]["source_page"] == 1
    assert result[0]["target_page"] == 2
    assert result[0]["cross_page"] is True



def test_duplicate_local_ids_do_not_resolve_to_wrong_page():
    symbols = [
        {"id": "S1", "page": 1, "global_id": "P1-SYM-S1"},
        {"id": "S1", "page": 2, "global_id": "P2-SYM-S1"},
    ]

    # A local ID alone is ambiguous across pages.
    result = build_cross_page_connections(
        [{"id": "L1", "page": 1, "source": "S1", "target": "S1"}],
        symbols,
    )

    # Ambiguous references must not create a potentially incorrect edge.
    assert result == []


def test_unresolved_endpoints_are_not_connected():
    symbols = [
        {"id": "S1", "page": 1, "global_id": "P1-SYM-S1"},
    ]

    lines = [
        {
            "id": "L1",
            "page": 1,
            "source": "S1",
            "target": "MISSING-SYMBOL",
        }
    ]

    result = build_cross_page_connections(lines, symbols)

    assert result == []


def test_numeric_string_page_references_are_normalized():
    pages = [
        {"page": 1, "next_page": "2"},
        {"page": "page-2", "previous_page": 1},
    ]

    references = build_page_references(pages)

    assert references[0]["source_page"] == 1
    assert references[0]["target_page"] == 2
    assert references[1]["source_page"] == 2
    assert references[1]["target_page"] == 1
