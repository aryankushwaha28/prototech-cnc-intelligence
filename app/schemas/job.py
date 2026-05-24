from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.features import FeatureSet
from app.schemas.gcode import GCodeSummary
from app.schemas.geometry import GeometrySummary
from app.schemas.quote import QuoteResult


class JobStatus(str, Enum):
    QUEUED = "queued"
    PARSING = "parsing"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    QUOTING = "quoting"
    GENERATING = "generating"
    COMPLETE = "complete"
    FAILED = "failed"


class JobCreate(BaseModel):
    material: Literal["aluminum_6061", "mild_steel", "stainless_304", "brass_360"]
    quantity: int = Field(ge=1, le=10000)
    machine_rate_inr: float = Field(default=800.0, ge=100.0)
    margin_pct: float = Field(default=20.0, ge=0.0, le=80.0)
    use_ai: bool = True


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    completed_at: datetime | None = None
    error: str | None = None
    geometry_summary: GeometrySummary | None = None
    features: FeatureSet | None = None
    ai_notes: str | None = None
    quote: QuoteResult | None = None
    gcode_summary: GCodeSummary | None = None


class JobAccepted(BaseModel):
    job_id: str
    status: JobStatus
    poll_url: str
