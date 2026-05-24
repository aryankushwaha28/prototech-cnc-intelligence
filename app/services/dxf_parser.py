import math
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("XDG_CACHE_HOME", str(Path(".cache").resolve()))
import ezdxf

from app.exceptions import DXFParseError, EmptyGeometryError
from app.schemas.geometry import (
    ArcEntity,
    BoundingBox,
    CircleEntity,
    LineEntity,
    Point2D,
    PolylineEntity,
    RawGeometry,
)


def _distance(a: Point2D, b: Point2D) -> float:
    return math.hypot(b.x - a.x, b.y - a.y)


def _poly_area(points: list[Point2D]) -> float:
    if len(points) < 3:
        return 0.0
    total = 0.0
    for index, point in enumerate(points):
        nxt = points[(index + 1) % len(points)]
        total += point.x * nxt.y - nxt.x * point.y
    return abs(total) / 2.0


def _poly_perimeter(points: list[Point2D], closed: bool) -> float:
    if len(points) < 2:
        return 0.0
    total = sum(_distance(points[i], points[i + 1]) for i in range(len(points) - 1))
    if closed:
        total += _distance(points[-1], points[0])
    return total


def _units(doc: Any) -> str:
    code = int(doc.header.get("$INSUNITS", 0) or 0)
    return {1: "inch", 4: "mm"}.get(code, "unknown")


class DXFParser:
    def parse(self, path: str | Path) -> RawGeometry:
        source = Path(path)
        try:
            doc = ezdxf.readfile(source)
        except Exception as exc:
            raise DXFParseError("File appears to be corrupted or not a valid DXF.") from exc

        lines: list[LineEntity] = []
        arcs: list[ArcEntity] = []
        circles: list[CircleEntity] = []
        polylines: list[PolylineEntity] = []
        points: list[Point2D] = []

        for entity in doc.modelspace():
            kind = entity.dxftype()
            layer = getattr(entity.dxf, "layer", "0")
            if kind == "LINE":
                start = Point2D(x=float(entity.dxf.start.x), y=float(entity.dxf.start.y))
                end = Point2D(x=float(entity.dxf.end.x), y=float(entity.dxf.end.y))
                lines.append(LineEntity(start=start, end=end, length=_distance(start, end), layer=layer))
                points.extend([start, end])
            elif kind == "ARC":
                radius = float(entity.dxf.radius)
                start_angle = float(entity.dxf.start_angle)
                end_angle = float(entity.dxf.end_angle)
                sweep = (end_angle - start_angle) % 360
                center = Point2D(x=float(entity.dxf.center.x), y=float(entity.dxf.center.y))
                arcs.append(
                    ArcEntity(
                        center=center,
                        radius=radius,
                        start_angle_deg=start_angle,
                        end_angle_deg=end_angle,
                        arc_length=(math.tau * radius) * (sweep / 360.0),
                        layer=layer,
                        clockwise=False,
                    )
                )
                points.extend(
                    [
                        Point2D(x=center.x - radius, y=center.y - radius),
                        Point2D(x=center.x + radius, y=center.y + radius),
                    ]
                )
            elif kind == "CIRCLE":
                center = Point2D(x=float(entity.dxf.center.x), y=float(entity.dxf.center.y))
                radius = float(entity.dxf.radius)
                circles.append(
                    CircleEntity(
                        center=center,
                        radius=radius,
                        diameter=radius * 2,
                        circumference=math.tau * radius,
                        layer=layer,
                    )
                )
                points.extend(
                    [
                        Point2D(x=center.x - radius, y=center.y - radius),
                        Point2D(x=center.x + radius, y=center.y + radius),
                    ]
                )
            elif kind in {"LWPOLYLINE", "POLYLINE"}:
                poly_entity = entity
                if kind == "LWPOLYLINE":
                    vertices = [Point2D(x=float(p[0]), y=float(p[1])) for p in poly_entity.get_points()]  # type: ignore[attr-defined]
                    closed = bool(poly_entity.closed)  # type: ignore[attr-defined]
                else:
                    vertices = [Point2D(x=float(v.dxf.location.x), y=float(v.dxf.location.y)) for v in poly_entity.vertices]  # type: ignore[attr-defined]
                    closed = bool(poly_entity.is_closed)  # type: ignore[attr-defined]
                polylines.append(
                    PolylineEntity(
                        vertices=vertices,
                        is_closed=closed,
                        perimeter=_poly_perimeter(vertices, closed),
                        area=_poly_area(vertices) if closed else None,
                        layer=layer,
                    )
                )
                points.extend(vertices)

        entity_count = len(lines) + len(arcs) + len(circles) + len(polylines)
        if entity_count == 0 or not points:
            raise EmptyGeometryError()

        bbox = BoundingBox(
            min_x=min(point.x for point in points),
            min_y=min(point.y for point in points),
            max_x=max(point.x for point in points),
            max_y=max(point.y for point in points),
        )
        return RawGeometry(
            source_file=source.name,
            dxf_version=doc.dxfversion,
            entity_count=entity_count,
            lines=lines,
            arcs=arcs,
            circles=circles,
            polylines=polylines,
            bounding_box=bbox,
            units=_units(doc),
        )
