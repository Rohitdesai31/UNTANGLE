from __future__ import annotations

import json
import shutil
from pathlib import Path

from shared.schemas import Audit, Graph, Mapping


BASE_OUTPUT_DIR = Path("data/outputs")
FIXTURE_DIR = Path("fixtures")


class PipelineService:
    def process_job(self, job_id: str) -> dict:
        output_dir = BASE_OUTPUT_DIR / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        fixture_files = [
            "graph.json",
            "graph_simple.json",
            "mapping.json",
            "audit.json",
        ]

        for filename in fixture_files:
            source = FIXTURE_DIR / filename
            destination = output_dir / filename

            if not source.exists():
                raise FileNotFoundError(
                    f"Required fixture not found: {source}"
                )

            shutil.copy2(source, destination)

        sketch_source = FIXTURE_DIR / "sketch.svg"
        sketch_destination = output_dir / "sketch.svg"

        if not sketch_source.exists():
            raise FileNotFoundError(
                f"Required fixture not found: {sketch_source}"
            )

        shutil.copy2(sketch_source, sketch_destination)

        graph = self._load_json(
            output_dir / "graph.json",
            Graph,
        )

        graph_simple = self._load_json(
            output_dir / "graph_simple.json",
            Graph,
        )

        mapping = self._load_mapping(
            output_dir / "mapping.json",
        )

        audit = self._load_json(
            output_dir / "audit.json",
            Audit,
        )

        return {
            "job_id": job_id,
            "status": "completed",
            "outputs": {
                "graph": str(output_dir / "graph.json"),
                "graph_simple": str(output_dir / "graph_simple.json"),
                "mapping": str(output_dir / "mapping.json"),
                "sketch": str(output_dir / "sketch.svg"),
                "audit": str(output_dir / "audit.json"),
            },
            "summary": {
                "graph_nodes": len(graph.nodes),
                "graph_edges": len(graph.edges),
                "simplified_nodes": len(graph_simple.nodes),
                "simplified_edges": len(graph_simple.edges),
                "mapping_count": len(mapping),
                "io_coverage": audit.io_coverage,
                "status": audit.status,
            },
        }

    @staticmethod
    def _load_json(path: Path, model):
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return model.model_validate(data)

    @staticmethod
    def _load_mapping(path: Path) -> list[Mapping]:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return [
            Mapping.model_validate(item)
            for item in data
        ]


pipeline_service = PipelineService()