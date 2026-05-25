from datetime import UTC, datetime

from app.exceptions import QuoteCalculationError
from app.schemas.features import FeatureSet
from app.schemas.geometry import GeometrySummary
from app.schemas.job import JobCreate
from app.schemas.quote import MATERIAL_DB, CostBreakdown, QuoteResult


class QuoteEngine:
    def calculate(self, job_id: str, request: JobCreate, summary: GeometrySummary, features: FeatureSet, inr_to_usd: float) -> QuoteResult:
        material = MATERIAL_DB.get(request.material)
        if material is None:
            raise QuoteCalculationError("Unknown material.")

        x_mm, y_mm, z_mm = summary.estimated_stock_size_mm
        stock_volume_mm3 = max(x_mm * y_mm * z_mm, 1.0)
        stock_weight_kg = (stock_volume_mm3 / 1_000_000_000.0) * material.density_kg_m3
        material_cost = stock_weight_kg * material.cost_inr_per_kg

        contour_length = sum(c.perimeter_mm for c in features.contours + features.open_profiles)
        base_time = contour_length / material.feed_rate_mm_min if contour_length else 0.5
        feature_penalty = len(features.holes) * 0.8 + len(features.pockets) * 2.5 + len(features.radii) * 0.3
        complexity_factor = 1.0 + (features.complexity_score / 100.0) * 0.5
        setup_time = 5.0 + (features.complexity_score / 100.0) * 20.0
        total_time = ((base_time + feature_penalty) * complexity_factor * (1 / material.machinability_factor)) + setup_time
        machining_cost = (total_time / 60.0) * request.machine_rate_inr
        tooling = machining_cost * 0.08
        subtotal = material_cost + machining_cost + tooling
        margin = subtotal * (request.margin_pct / 100.0)
        total_per_piece = round(subtotal + margin, 2)
        total_quantity = total_per_piece * request.quantity

        warnings = ["Simulator validation required before production machining."]
        if any(hole.diameter_mm < 4 for hole in features.holes):
            warnings.append("Small holes under 4 mm may need conservative drilling feeds.")
        if features.complexity_score > 50:
            warnings.append("High geometric complexity may increase real setup and inspection time.")

        return QuoteResult(
            job_id=job_id,
            material=material.name,
            quantity=request.quantity,
            stock_volume_mm3=round(stock_volume_mm3, 3),
            stock_weight_kg=round(stock_weight_kg, 5),
            estimated_machining_time_min=round(total_time, 2),
            cost_breakdown=CostBreakdown(
                material_cost_inr=round(material_cost, 2),
                machining_time_min=round(total_time, 2),
                machining_cost_inr=round(machining_cost, 2),
                tooling_setup_inr=round(tooling, 2),
                subtotal_inr=round(subtotal, 2),
                margin_inr=round(margin, 2),
                total_per_piece_inr=total_per_piece,
                total_for_quantity_inr=round(total_quantity, 2),
                total_usd=round(total_quantity / inr_to_usd, 2),
            ),
            warnings=warnings,
            generated_at=datetime.now(UTC),
        )
