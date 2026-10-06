from __future__ import annotations

import json
from pathlib import Path

from shared.schemas import (
    Association,
    Audit,
    Graph,
    IOItem,
    Line,
    Mapping,
    OCRResult,
    Page,
    Symbol,
)


FIXTURES_DIR = Path("fixtures")


def load_json(filename: str):
    path = FIXTURES_DIR / filename

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_pages() -> None:
    data = load_json("pages.json")

    for item in data:
        Page.model_validate(item)

    print("PASS  pages.json")


def validate_symbols() -> None:
    data = load_json("symbols.json")

    for item in data:
        Symbol.model_validate(item)

    print("PASS  symbols.json")


def validate_ocr() -> None:
    data = load_json("ocr.json")

    for item in data:
        OCRResult.model_validate(item)

    print("PASS  ocr.json")


def validate_lines() -> None:
    data = load_json("lines.json")

    for item in data:
        Line.model_validate(item)

    print("PASS  lines.json")


def validate_io_list() -> None:
    data = load_json("io_list.json")

    for item in data:
        IOItem.model_validate(item)

    print("PASS  io_list.json")


def validate_associations() -> None:
    data = load_json("associations.json")

    for item in data:
        Association.model_validate(item)

    print("PASS  associations.json")


def validate_graph() -> None:
    data = load_json("graph.json")

    Graph.model_validate(data)

    print("PASS  graph.json")


def validate_graph_simple() -> None:
    data = load_json("graph_simple.json")

    Graph.model_validate(data)

    print("PASS  graph_simple.json")


def validate_mapping() -> None:
    data = load_json("mapping.json")

    for item in data:
        Mapping.model_validate(item)

    print("PASS  mapping.json")


def validate_audit() -> None:
    data = load_json("audit.json")

    Audit.model_validate(data)

    print("PASS  audit.json")


def main() -> None:
    print()
    print("UNTANGLE FIXTURE VALIDATION")
    print("=" * 35)

    validate_pages()
    validate_symbols()
    validate_ocr()
    validate_lines()
    validate_io_list()
    validate_associations()
    validate_graph()
    validate_graph_simple()
    validate_mapping()
    validate_audit()

    print("=" * 35)
    print("ALL JSON FIXTURES ARE VALID")
    print()


if __name__ == "__main__":
    main()