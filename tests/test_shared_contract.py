import json
from pathlib import Path

from shared.schemas import Audit, Graph, Line, OCRResult, Page, Symbol

ROOT = Path(__file__).resolve().parents[1]


def test_page_fixture_matches_contract():
    data = json.loads((ROOT / "fixtures" / "pages.json").read_text())
    pages = [Page.model_validate(item) for item in data["pages"]]
    assert pages[0].page_id == "P001"


def test_symbol_fixture_matches_contract():
    data = json.loads((ROOT / "fixtures" / "symbols.json").read_text())
    symbols = [Symbol.model_validate(item) for item in data["symbols"]]
    assert {s.id for s in symbols} == {"S001", "S002", "S003", "S004"}


def test_ocr_fixture_matches_contract():
    data = json.loads((ROOT / "fixtures" / "ocr.json").read_text())
    results = [OCRResult.model_validate(item) for item in data["ocr"]]
    assert any(x.text == "PT-101A" for x in results)


def test_line_fixture_matches_contract():
    data = json.loads((ROOT / "fixtures" / "lines.json").read_text())
    lines = [Line.model_validate(item) for item in data["lines"]]
    assert len(lines) == 3


def test_graph_fixture_matches_contract():
    data = json.loads((ROOT / "fixtures" / "graph.json").read_text())
    graph = Graph.model_validate(data)
    assert len(graph.nodes) == 4
    assert len(graph.edges) == 3


def test_audit_fixture_matches_contract():
    data = json.loads((ROOT / "fixtures" / "audit.json").read_text())
    audit = Audit.model_validate(data)
    assert audit.io_coverage == 100.0
    assert audit.status == "PASS"
