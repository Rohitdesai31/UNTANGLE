from __future__ import annotations

from pathlib import Path


from fastapi import UploadFile

from shared.schemas import Job


BASE_UPLOAD_DIR = Path("data/uploads")

ALLOWED_PID_EXTENSIONS = {".pdf"}
ALLOWED_IO_EXTENSIONS = {".xlsx", ".xls"}

MAX_PID_SIZE = 50 * 1024 * 1024       # 50 MB
MAX_IO_SIZE = 10 * 1024 * 1024        # 10 MB


class UploadService:
    """Handles validation and storage of UNTANGLE input files."""

    @staticmethod
    def _validate_extension(
        filename: str | None,
        allowed_extensions: set[str],
        file_description: str,
    ) -> str:
        if not filename:
            raise ValueError(f"{file_description} filename is required.")

        extension = Path(filename).suffix.lower()

        if extension not in allowed_extensions:
            allowed = ", ".join(sorted(allowed_extensions))
            raise ValueError(
                f"Invalid {file_description} file type. "
                f"Allowed extensions: {allowed}"
            )

        return extension

    @staticmethod
    async def _save_file(
        upload_file: UploadFile,
        destination: Path,
        max_size: int,
    ) -> int:
        total_size = 0

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            with destination.open("wb") as output:
                while True:
                    chunk = await upload_file.read(1024 * 1024)

                    if not chunk:
                        break

                    total_size += len(chunk)

                    if total_size > max_size:
                        raise ValueError(
                            f"File '{upload_file.filename}' exceeds "
                            f"the maximum allowed size."
                        )

                    output.write(chunk)

        finally:
            await upload_file.close()

        return total_size

    async def save_job_files(
        self,
        job: Job,
        pid_file: UploadFile,
        io_file: UploadFile,
    ) -> dict:
        self._validate_extension(
            pid_file.filename,
            ALLOWED_PID_EXTENSIONS,
            "P&ID",
        )

        self._validate_extension(
            io_file.filename,
            ALLOWED_IO_EXTENSIONS,
            "IO list",
        )

        job_directory = BASE_UPLOAD_DIR / job.id
        job_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        pid_path = job_directory / "pid.pdf"
        io_path = job_directory / "io_list.xlsx"

        pid_size = await self._save_file(
            pid_file,
            pid_path,
            MAX_PID_SIZE,
        )

        try:
            io_size = await self._save_file(
                io_file,
                io_path,
                MAX_IO_SIZE,
            )
        except Exception:
            if pid_path.exists():
                pid_path.unlink()
            raise

        return {
            "job_id": job.id,
            "pid_file": {
                "filename": pid_file.filename,
                "path": str(pid_path),
                "size": pid_size,
            },
            "io_file": {
                "filename": io_file.filename,
                "path": str(io_path),
                "size": io_size,
            },
        }


upload_service = UploadService()