from __future__ import annotations

from pathlib import Path


BASE_INTERMEDIATE_DIR = Path("data/intermediate")

REQUIRED_M1_OUTPUTS = {
    "symbols": "symbols.json",
    "lines": "lines.json",
    "associations": "associations.json",
    "io_list": "io_list.json",
}


class M1OutputService:
    """
    M4 integration boundary for outputs produced by M1.

    M1 owns creation of these files.
    M4 only discovers and validates their presence.
    """

    @staticmethod
    def get_output_paths(job_id: str) -> dict[str, Path]:
        job_dir = BASE_INTERMEDIATE_DIR / job_id

        return {
            name: job_dir / filename
            for name, filename in REQUIRED_M1_OUTPUTS.items()
        }

    def outputs_available(self, job_id: str) -> bool:
        paths = self.get_output_paths(job_id)
        return all(path.exists() for path in paths.values())

    def get_missing_outputs(self, job_id: str) -> list[str]:
        paths = self.get_output_paths(job_id)

        return [
            name
            for name, path in paths.items()
            if not path.exists()
        ]

    def get_output_paths_if_ready(self, job_id: str) -> dict[str, Path]:
        paths = self.get_output_paths(job_id)
        missing = self.get_missing_outputs(job_id)

        if missing:
            raise FileNotFoundError(
                "M1 outputs are not ready. Missing: "
                + ", ".join(missing)
            )

        return paths


m1_output_service = M1OutputService()