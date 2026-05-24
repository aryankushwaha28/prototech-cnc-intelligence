from datetime import UTC, datetime

from app.schemas.features import FeatureSet
from app.schemas.gcode import GCodeProgram, GCodeSummary
from app.schemas.job import JobCreate


class GCodeGenerator:
    def generate(self, job_id: str, request: JobCreate, features: FeatureSet, cycle_time_min: float) -> GCodeProgram:
        lines: list[str] = [
            "%",
            f"O{abs(hash(job_id)) % 9999:04d} (PROTOTECH CNC INTELLIGENCE - JOB {job_id})",
            f"(DATE: {datetime.now(UTC).date().isoformat()})",
            f"(MATERIAL: {request.material})",
            "(SIMULATOR VALIDATION REQUIRED - NOT PRODUCTION CERTIFIED)",
            "G21 G90 G17 G40 G49 G80",
            "G28 G91 Z0.0",
            "G28 G91 X0.0 Y0.0",
            "G90",
            "T01 M06",
            "G43 H01",
            "S2500 M03",
            "G00 Z5.0",
        ]
        for contour in features.contours + features.open_profiles:
            if not contour.vertices:
                continue
            first = contour.vertices[0]
            lines.append(f"(--- CONTOUR {contour.feature_id} ---)")
            lines.append(f"G00 X{first.x:.3f} Y{first.y:.3f}")
            lines.append("G01 Z-1.000 F120.0")
            for point in contour.vertices[1:]:
                lines.append(f"G01 X{point.x:.3f} Y{point.y:.3f} F300.0")
            if contour.is_outer_profile:
                lines.append(f"G01 X{first.x:.3f} Y{first.y:.3f} F300.0")
            lines.append("G00 Z5.0")

        if features.radii:
            lines.append("(--- RADII / ARCS FROM DXF ---)")
        for radius in features.radii:
            lines.append(f"(RADIUS {radius.feature_id}: R{radius.radius_mm:.3f}, ARC {radius.arc_length_mm:.3f}MM)")

        if features.holes:
            lines.append("(--- HOLES ---)")
            for hole in features.holes:
                lines.append(f"G81 X{hole.center.x:.3f} Y{hole.center.y:.3f} Z-5.000 R2.000 F120.0")
            lines.append("G80")

        lines.extend(["G28 G91 Z0.0", "M05", "M30", "%"])
        text = "\n".join(lines) + "\n"
        return GCodeProgram(
            job_id=job_id,
            program_text=text,
            summary=GCodeSummary(
                line_count=len(lines),
                contour_count=len(features.contours) + len(features.open_profiles),
                hole_count=len(features.holes),
                estimated_cycle_time_min=round(cycle_time_min, 2),
            ),
        )
