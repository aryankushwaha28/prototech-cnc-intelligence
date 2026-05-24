import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.schemas.job import JobResponse, JobStatus


class JobStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def new_job_id(self) -> str:
        return f"j_{uuid4().hex[:12]}"

    def job_dir(self, job_id: str) -> Path:
        return self.root / job_id

    def create(self, job_id: str) -> JobResponse:
        self.job_dir(job_id).mkdir(parents=True, exist_ok=True)
        job = JobResponse(job_id=job_id, status=JobStatus.QUEUED, created_at=datetime.now(UTC))
        self.save_response(job)
        return job

    def save_json(self, job_id: str, name: str, data: object) -> None:
        path = self.job_dir(job_id) / name
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def load_json(self, job_id: str, name: str) -> dict:
        return json.loads((self.job_dir(job_id) / name).read_text(encoding="utf-8"))

    def save_response(self, job: JobResponse) -> None:
        self.save_json(job.job_id, "job.json", job.model_dump(mode="json"))

    def load_response(self, job_id: str) -> JobResponse | None:
        path = self.job_dir(job_id) / "job.json"
        if not path.exists():
            return None
        return JobResponse.model_validate_json(path.read_text(encoding="utf-8"))

    def set_status(self, job_id: str, status: JobStatus, error: str | None = None) -> JobResponse:
        job = self.load_response(job_id)
        if job is None:
            job = JobResponse(job_id=job_id, status=status, created_at=datetime.now(UTC))
        job.status = status
        job.error = error
        if status in {JobStatus.COMPLETE, JobStatus.FAILED}:
            job.completed_at = datetime.now(UTC)
        self.save_response(job)
        return job
