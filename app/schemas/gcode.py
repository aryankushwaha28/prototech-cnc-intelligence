from pydantic import BaseModel


class GCodeSummary(BaseModel):
    line_count: int
    contour_count: int
    hole_count: int
    estimated_cycle_time_min: float


class GCodeProgram(BaseModel):
    job_id: str
    program_text: str
    summary: GCodeSummary
