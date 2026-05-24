import shutil
from pathlib import Path

from app.config import Settings
from app.schemas.job import JobCreate, JobStatus
from app.services.ai_analyzer import AIAnalyzer
from app.services.dxf_parser import DXFParser
from app.services.feature_extractor import FeatureExtractor
from app.services.gcode_generator import GCodeGenerator
from app.services.pdf_generator import PDFGenerator
from app.services.quote_engine import QuoteEngine
from app.storage.job_store import JobStore


class Pipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = JobStore(settings.jobs_dir)

    def run(self, job_id: str, source_file: Path, request: JobCreate) -> None:
        try:
            job_dir = self.store.job_dir(job_id)
            input_path = job_dir / "input.dxf"
            shutil.copyfile(source_file, input_path)

            self.store.set_status(job_id, JobStatus.PARSING)
            geometry = DXFParser().parse(input_path)
            self.store.save_json(job_id, "geometry.json", geometry.model_dump(mode="json"))

            self.store.set_status(job_id, JobStatus.EXTRACTING)
            extractor = FeatureExtractor()
            features = extractor.extract(geometry)
            summary = extractor.summarize_geometry(geometry)
            self.store.save_json(job_id, "features.json", features.model_dump(mode="json"))

            self.store.set_status(job_id, JobStatus.ANALYZING)
            ai_notes = AIAnalyzer(self.settings.anthropic_api_key).analyze(summary, features, request.use_ai)
            self.store.save_json(job_id, "analysis.json", {"ai_notes": ai_notes})

            self.store.set_status(job_id, JobStatus.QUOTING)
            quote = QuoteEngine().calculate(job_id, request, summary, features, self.settings.inr_to_usd_rate)
            self.store.save_json(job_id, "quote.json", quote.model_dump(mode="json"))
            PDFGenerator().generate(job_dir / "quote.pdf", quote, features, ai_notes)

            self.store.set_status(job_id, JobStatus.GENERATING)
            program = GCodeGenerator().generate(job_id, request, features, quote.estimated_machining_time_min)
            (job_dir / "program.nc").write_text(program.program_text, encoding="utf-8")
            self.store.save_json(job_id, "program.json", program.model_dump(mode="json"))

            job = self.store.set_status(job_id, JobStatus.COMPLETE)
            job.geometry_summary = summary
            job.features = features
            job.ai_notes = ai_notes
            job.quote = quote
            job.gcode_summary = program.summary
            self.store.save_response(job)
        except Exception as exc:
            self.store.set_status(job_id, JobStatus.FAILED, str(exc))
