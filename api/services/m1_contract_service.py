from __future__ import annotations

import json
from pathlib import Path


class M1ContractError(ValueError):
    """Raised when an M1 output does not satisfy the M4 contract."""


REQUIRED_FILES = {
    "symbols": "symbols.json",
    "lines": "lines.json",
    "associations": "associations.json",
    "io_list": "io_list.json",
}


class M1ContractService:
    """
    Validates the file contract between M1 and M4.

    M1 owns generation of these files.
    M4 only validates their structure and passes them onward.
    """

    @staticmethod
    def _load_json(path: Path, name: str) -> list | dict:
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as exc:
            raise M1ContractError(
                f"M1 output '{name}' contains invalid JSON."
            ) from exc
        except OSError as exc:
            raise M1ContractError(
                f"Unable to read M1 output '{name}': {exc}"
            ) from exc

        if not isinstance(data, (list, dict)):
            raise M1ContractError(
                f"M1 output '{name}' must contain a JSON array or object."
            )

        return data

    @staticmethod
    def _as_list(data: list | dict, name: str) -> list:
        if isinstance(data, list):
            return data

        # Allow an object only when it contains the expected collection.
        collection_keys = {
            "symbols": "symbols",
            "lines": "lines",
            "associations": "associations",
            "io_list": "io_list",
        }

        key = collection_keys[name]

        if key in data and isinstance(data[key], list):
            return data[key]

        raise M1ContractError(
            f"M1 output '{name}' must be a JSON array "
            f"or an object containing '{key}' as an array."
        )

    @staticmethod
    def _require_fields(
        item: dict,
        fields: set[str],
        name: str,
        index: int,
    ) -> None:
        missing = sorted(field for field in fields if field not in item)

        if missing:
            raise M1ContractError(
                f"M1 output '{name}' item {index} is missing "
                f"required field(s): {', '.join(missing)}."
            )

    def validate_job_outputs(self, job_id: str) -> dict:
        job_dir = Path("data/intermediate") / job_id

        missing_files = [
            filename
            for filename in REQUIRED_FILES.values()
            if not (job_dir / filename).exists()
        ]

        if missing_files:
            return {
                "ready": False,
                "job_id": job_id,
                "missing_files": missing_files,
                "errors": [],
            }

        paths = {
            name: job_dir / filename
            for name, filename in REQUIRED_FILES.items()
        }

        loaded = {
            name: self._load_json(path, name)
            for name, path in paths.items()
        }

        collections = {
            name: self._as_list(data, name)
            for name, data in loaded.items()
        }

        for index, item in enumerate(collections["symbols"]):
            if not isinstance(item, dict):
                raise M1ContractError(
                    f"M1 output 'symbols' item {index} must be an object."
                )

            self._require_fields(
                item,
                {"id", "class_name", "bbox"},
                "symbols",
                index,
            )

            if not isinstance(item["bbox"], list) or len(item["bbox"]) != 4:
                raise M1ContractError(
                    f"M1 output 'symbols' item {index} "
                    "must have bbox as [x1, y1, x2, y2]."
                )

        for index, item in enumerate(collections["lines"]):
            if not isinstance(item, dict):
                raise M1ContractError(
                    f"M1 output 'lines' item {index} must be an object."
                )

            self._require_fields(
                item,
                {"id", "points"},
                "lines",
                index,
            )

            if not isinstance(item["points"], list):
                raise M1ContractError(
                    f"M1 output 'lines' item {index} "
                    "must have points as a list."
                )

        for index, item in enumerate(collections["associations"]):
            if not isinstance(item, dict):
                raise M1ContractError(
                    f"M1 output 'associations' item {index} "
                    "must be an object."
                )

            self._require_fields(
                item,
                {"source_id", "target_id", "relation"},
                "associations",
                index,
            )

        for index, item in enumerate(collections["io_list"]):
            if not isinstance(item, dict):
                raise M1ContractError(
                    f"M1 output 'io_list' item {index} must be an object."
                )

            self._require_fields(
                item,
                {"tag", "type", "description", "loop", "expected_status"},
                "io_list",
                index,
            )

        return {
            "ready": True,
            "job_id": job_id,
            "missing_files": [],
            "errors": [],
            "counts": {
                "symbols": len(collections["symbols"]),
                "lines": len(collections["lines"]),
                "associations": len(collections["associations"]),
                "io_list": len(collections["io_list"]),
            },
            "paths": {
                name: str(path)
                for name, path in paths.items()
            },
        }


m1_contract_service = M1ContractService()