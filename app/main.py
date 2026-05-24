import logging
import tempfile
from pathlib import Path
from typing import Literal, cast

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.schemas.job import JobAccepted, JobCreate, JobStatus
from app.storage.job_store import JobStore
from app.services.pipeline import Pipeline

settings = get_settings()
logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s - %(message)s")

app = FastAPI(title="ProtoTech CNC Intelligence", version="1.0.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return Path("app/templates/index.html").read_text(encoding="utf-8")


@app.post("/api/jobs", response_model=JobAccepted, status_code=202)
async def create_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    material: str = Form(...),
    quantity: int = Form(...),
    machine_rate_inr: float = Form(settings.default_machine_rate_inr),
    margin_pct: float = Form(settings.default_margin_pct),
    use_ai: bool = Form(True),
) -> JobAccepted:
    if not file.filename or not file.filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=400, detail={"error_code": "INVALID_FILE", "message": "Upload a .dxf file."})
    request = JobCreate(
        material=cast(Literal["aluminum_6061", "mild_steel", "stainless_304", "brass_360"], material),
        quantity=quantity,
        machine_rate_inr=machine_rate_inr,
        margin_pct=margin_pct,
        use_ai=use_ai,
    )
    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail={"error_code": "FILE_TOO_LARGE", "message": "DXF exceeds max upload size."})

    store = JobStore(settings.jobs_dir)
    job_id = store.new_job_id()
    store.create(job_id)
    temp_dir = Path(tempfile.gettempdir()) / "prototech_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    source = temp_dir / f"{job_id}.dxf"
    source.write_bytes(content)
    background_tasks.add_task(Pipeline(settings).run, job_id, source, request)
    return JobAccepted(job_id=job_id, status=JobStatus.QUEUED, poll_url=f"/api/jobs/{job_id}")


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = JobStore(settings.jobs_dir).load_response(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail={"error_code": "JOB_NOT_FOUND", "message": "Job not found."})
    return job


@app.get("/api/jobs/{job_id}/quote.pdf")
def get_quote(job_id: str):
    path = JobStore(settings.jobs_dir).job_dir(job_id) / "quote.pdf"
    if not path.exists():
        raise HTTPException(status_code=404, detail={"error_code": "QUOTE_NOT_READY", "message": "Quote PDF is not ready."})
    return FileResponse(path, media_type="application/pdf", filename=f"{job_id}_quote.pdf")


@app.get("/api/jobs/{job_id}/program.nc")
def get_program(job_id: str):
    path = JobStore(settings.jobs_dir).job_dir(job_id) / "program.nc"
    if not path.exists():
        raise HTTPException(status_code=404, detail={"error_code": "PROGRAM_NOT_READY", "message": "G-code program is not ready."})
    return FileResponse(path, media_type="text/plain", filename=f"{job_id}.nc")
