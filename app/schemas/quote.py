from datetime import datetime

from pydantic import BaseModel


class MaterialSpec(BaseModel):
    name: str
    density_kg_m3: float
    cost_inr_per_kg: float
    machinability_factor: float
    feed_rate_mm_min: float


MATERIAL_DB: dict[str, MaterialSpec] = {
    "aluminum_6061": MaterialSpec(
        name="Aluminium 6061",
        density_kg_m3=2710,
        cost_inr_per_kg=280,
        machinability_factor=1.3,
        feed_rate_mm_min=800,
    ),
    "mild_steel": MaterialSpec(
        name="Mild Steel EN8",
        density_kg_m3=7850,
        cost_inr_per_kg=85,
        machinability_factor=1.0,
        feed_rate_mm_min=400,
    ),
    "stainless_304": MaterialSpec(
        name="SS 304",
        density_kg_m3=8000,
        cost_inr_per_kg=320,
        machinability_factor=0.7,
        feed_rate_mm_min=200,
    ),
    "brass_360": MaterialSpec(
        name="Brass 360",
        density_kg_m3=8500,
        cost_inr_per_kg=520,
        machinability_factor=1.4,
        feed_rate_mm_min=600,
    ),
}


class CostBreakdown(BaseModel):
    material_cost_inr: float
    machining_time_min: float
    machining_cost_inr: float
    tooling_setup_inr: float
    subtotal_inr: float
    margin_inr: float
    total_per_piece_inr: float
    total_for_quantity_inr: float
    total_usd: float


class QuoteResult(BaseModel):
    job_id: str
    material: str
    quantity: int
    stock_volume_mm3: float
    stock_weight_kg: float
    estimated_machining_time_min: float
    cost_breakdown: CostBreakdown
    warnings: list[str]
    generated_at: datetime
