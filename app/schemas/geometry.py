from pydantic import BaseModel, Field


class Point2D(BaseModel):
    x: float
    y: float


class BoundingBox(BaseModel):
    min_x: float = 0.0
    min_y: float = 0.0
    max_x: float = 0.0
    max_y: float = 0.0

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y


class LineEntity(BaseModel):
    start: Point2D
    end: Point2D
    length: float
    layer: str = "0"


class ArcEntity(BaseModel):
    center: Point2D
    radius: float
    start_angle_deg: float
    end_angle_deg: float
    arc_length: float
    layer: str = "0"
    clockwise: bool = False


class CircleEntity(BaseModel):
    center: Point2D
    radius: float
    diameter: float
    circumference: float
    layer: str = "0"


class PolylineEntity(BaseModel):
    vertices: list[Point2D]
    is_closed: bool
    perimeter: float
    area: float | None = None
    layer: str = "0"


class RawGeometry(BaseModel):
    source_file: str
    dxf_version: str
    entity_count: int
    lines: list[LineEntity] = Field(default_factory=list)
    arcs: list[ArcEntity] = Field(default_factory=list)
    circles: list[CircleEntity] = Field(default_factory=list)
    polylines: list[PolylineEntity] = Field(default_factory=list)
    bounding_box: BoundingBox
    units: str = "unknown"


class GeometrySummary(BaseModel):
    total_entities: int
    line_count: int
    arc_count: int
    circle_count: int
    polyline_count: int
    bounding_box: BoundingBox
    estimated_stock_size_mm: tuple[float, float, float]
