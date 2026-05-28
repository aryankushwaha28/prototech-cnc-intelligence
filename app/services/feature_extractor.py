from app.schemas.features import (
    ContourFeature,
    FeatureSet,
    HoleFeature,
    PocketFeature,
    RadiusFeature,
)
from app.schemas.geometry import GeometrySummary, RawGeometry


DEFAULT_2D_STOCK_THICKNESS_MM = 3.0


MIN_POCKET_PERIMETER_MM = 20.0


class FeatureExtractor:
    def extract(self, geometry: RawGeometry) -> FeatureSet:
        holes = [
            HoleFeature(
                feature_id=f"H{index + 1:03d}",
                center=circle.center,
                diameter_mm=round(circle.diameter, 3),
                classification="clearance" if circle.diameter <= 12 else "unknown",
            )
            for index, circle in enumerate(geometry.circles)
        ]

        closed = [poly for poly in geometry.polylines if poly.is_closed]
        largest_area = max((poly.area or 0.0 for poly in closed), default=0.0)
        contours: list[ContourFeature] = []
        pockets: list[PocketFeature] = []
        for index, poly in enumerate(closed):
            is_outer = bool(poly.area and poly.area == largest_area and largest_area > 0)
            contour = ContourFeature(
                feature_id=f"C{index + 1:03d}",
                perimeter_mm=round(poly.perimeter, 3),
                is_outer_profile=is_outer,
                vertices=poly.vertices,
            )
            contours.append(contour)
            if not is_outer and poly.area and poly.perimeter >= MIN_POCKET_PERIMETER_MM:
                pockets.append(
                    PocketFeature(
                        feature_id=f"P{len(pockets) + 1:03d}",
                        area_mm2=round(poly.area, 3),
                        perimeter_mm=round(poly.perimeter, 3),
                        depth_estimate_mm=5.0,
                        vertices=poly.vertices,
                    )
                )

        open_profiles = [
            ContourFeature(
                feature_id=f"O{index + 1:03d}",
                perimeter_mm=round(poly.perimeter, 3),
                is_outer_profile=False,
                vertices=poly.vertices,
            )
            for index, poly in enumerate(geometry.polylines)
            if not poly.is_closed
        ]
        radii = [
            RadiusFeature(
                feature_id=f"R{index + 1:03d}",
                radius_mm=round(arc.radius, 3),
                arc_length_mm=round(arc.arc_length, 3),
                center=arc.center,
            )
            for index, arc in enumerate(geometry.arcs)
        ]
        total = len(holes) + len(pockets) + len(contours) + len(radii) + len(open_profiles)
        complexity = min(100.0, total * 4.0 + len(geometry.lines) * 0.4 + sum(p.perimeter for p in closed) / 150.0)
        return FeatureSet(
            holes=holes,
            pockets=pockets,
            contours=contours,
            radii=radii,
            open_profiles=open_profiles,
            total_feature_count=total,
            complexity_score=round(complexity, 2),
        )

    def summarize_geometry(self, geometry: RawGeometry) -> GeometrySummary:
        bbox = geometry.bounding_box
        return GeometrySummary(
            total_entities=geometry.entity_count,
            line_count=len(geometry.lines),
            arc_count=len(geometry.arcs),
            circle_count=len(geometry.circles),
            polyline_count=len(geometry.polylines),
            bounding_box=bbox,
            estimated_stock_size_mm=(
                round(bbox.width + 5, 3),
                round(bbox.height + 5, 3),
                DEFAULT_2D_STOCK_THICKNESS_MM,
            ),
        )
