from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.geometry import Point2D


class HoleFeature(BaseModel):
    feature_id: str
    center: Point2D
    diameter_mm: float
    classification: Literal["clearance", "tapped", "reamed", "press_fit", "unknown"] = "unknown"
    confidence: float = Field(ge=0.0, le=1.0, default=0.85)


class PocketFeature(BaseModel):
    feature_id: str
    area_mm2: float
    perimeter_mm: float
    depth_estimate_mm: float | None = None
    vertices: list[Point2D]


class ContourFeature(BaseModel):
    feature_id: str
    perimeter_mm: float
    is_outer_profile: bool
    vertices: list[Point2D]


class RadiusFeature(BaseModel):
    feature_id: str
    radius_mm: float
    arc_length_mm: float
    center: Point2D


class FeatureSet(BaseModel):
    holes: list[HoleFeature] = Field(default_factory=list)
    pockets: list[PocketFeature] = Field(default_factory=list)
    contours: list[ContourFeature] = Field(default_factory=list)
    radii: list[RadiusFeature] = Field(default_factory=list)
    open_profiles: list[ContourFeature] = Field(default_factory=list)
    total_feature_count: int = 0
    complexity_score: float = Field(ge=0.0, le=100.0, default=0.0)
