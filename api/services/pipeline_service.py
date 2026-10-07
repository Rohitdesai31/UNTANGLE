from __future__ import annotations

import json
import shutil
from pathlib import Path

from m2_topology.graph_builder import build_graph_from_files
from m2_topology.topology_validator import validate_topology

from m3_simplify.audit import create_audit
from m3_simplify.layout import calculate_layout
from m3_simplify.preservation import mark_preserved_nodes
from m3_simplify.routing import route_edges
from m3_simplify.simplify import simplify_graph
from m3_simplify.svg_generator import create_mapping, generate_svg


BASE_OUTPUT_DIR = Path("data/outputs")
BASE_INTERMEDIATE_DIR = Path("data/intermediate")
FIXTURE_DIR = Path("fixtures")


class PipelineService:
    def process_job(self, job_id: str) -> dict:
        output_dir = BASE_OUTPUT_DIR / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        input_dir = BASE_INTERMEDIATE_DIR / job_id

        symbols_path = self._resolve_input(
            input_dir / "symbols.json",
            FIXTURE_DIR / "symbols.json",
        )
        lines_path = self._resolve_input(
            input_dir / "lines.json",
            FIXTURE_DIR / "lines.json",
        )
        associations_path = self._resolve_input(
            input_dir / "associations.json",
            FIXTURE_DIR / "associations.json",
        )
        io_list_path = self._resolve_input(
            input_dir / "io_list.json",
            FIXTURE_DIR / "io_list.json",
        )

        # ---------------------------------------------------------
        # M2 — Topology construction
        # ---------------------------------------------------------
        graph = build_graph_from_files(
            symbols_path=str(symbols_path),
            lines_path=str(lines_path),
            associations_path=str(associations_path),
            io_list_path=str(io_list_path),
            output_path=str(output_dir / "graph.json"),
        )

        validation = validate_topology(graph)

        if not validation.get("valid", False):
            raise ValueError(
                f"Topology validation failed: "
                f"{validation.get('errors', [])}"
            )

        # ---------------------------------------------------------
        # M3 — Process simplification
        # ---------------------------------------------------------
        preserved_graph = mark_preserved_nodes(graph)

        simple_graph = simplify_graph(preserved_graph)
        simple_graph = calculate_layout(simple_graph)
        simple_graph = route_edges(simple_graph)

        simple_graph_path = output_dir / "graph_simple.json"
        with simple_graph_path.open("w", encoding="utf-8") as file:
            json.dump(simple_graph, file, indent=2)

        # ---------------------------------------------------------
        # M3 — SVG
        # ---------------------------------------------------------
        sketch_path = output_dir / "sketch.svg"
        generate_svg(simple_graph, str(sketch_path))

        # ---------------------------------------------------------
        # M3 — Mapping
        # ---------------------------------------------------------
        mapping = create_mapping(simple_graph)

        mapping_path = output_dir / "mapping.json"
        with mapping_path.open("w", encoding="utf-8") as file:
            json.dump(mapping, file, indent=2)

        # ---------------------------------------------------------
        # M3 — Audit
        # ---------------------------------------------------------
        audit = create_audit(graph, simple_graph)

        audit_path = output_dir / "audit.json"
        with audit_path.open("w", encoding="utf-8") as file:
            json.dump(audit, file, indent=2)

        # ---------------------------------------------------------
        # Final API response
        # ---------------------------------------------------------
        return {
            "job_id": job_id,
            "status": "completed",
            "outputs": {
                "graph": str(output_dir / "graph.json"),
                "graph_simple": str(output_dir / "graph_simple.json"),
                "mapping": str(mapping_path),
                "sketch": str(sketch_path),
                "audit": str(audit_path),
            },
            "summary": {
                "graph_nodes": len(graph.get("nodes", [])),
                "graph_edges": len(graph.get("edges", [])),
                "simplified_nodes": len(simple_graph.get("nodes", [])),
                "simplified_edges": len(simple_graph.get("edges", [])),
                "mapping_count": len(mapping.get("nodes", {})),
                "io_coverage": audit.get("io_coverage_percent", 0.0),
                "status": audit.get("overall", "FAIL"),
            },
        }

    @staticmethod
    def _resolve_input(primary: Path, fallback: Path) -> Path:
        """
        Use real M1 output when available.
        Fall back to the controlled fixture until M1 is integrated.
        """
        if primary.exists():
            return primary

        if fallback.exists():
            return fallback

        raise FileNotFoundError(
            f"Required pipeline input not found: "
            f"{primary} or {fallback}"
        )


pipeline_service = PipelineService()