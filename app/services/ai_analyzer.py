import json
import logging
from typing import Any

from app.schemas.features import FeatureSet
from app.schemas.geometry import GeometrySummary

logger = logging.getLogger(__name__)


class AIAnalyzer:
    def __init__(self, api_key: str | None):
        self.api_key = api_key

    def analyze(self, summary: GeometrySummary, features: FeatureSet, use_ai: bool) -> str | None:
        if not use_ai or not self.api_key:
            return None
        try:
            from anthropic import Anthropic

            payload: dict[str, Any] = {
                "part_summary": {
                    "bounding_box_mm": [
                        summary.bounding_box.width,
                        summary.bounding_box.height,
                        summary.estimated_stock_size_mm[2],
                    ],
                    "entity_counts": {
                        "lines": summary.line_count,
                        "arcs": summary.arc_count,
                        "circles": summary.circle_count,
                        "polylines": summary.polyline_count,
                    },
                },
                "features": {
                    "holes": [{"dia_mm": h.diameter_mm} for h in features.holes[:20]],
                    "pockets": [{"area_mm2": p.area_mm2, "perimeter_mm": p.perimeter_mm} for p in features.pockets[:10]],
                    "contours": [{"perimeter_mm": c.perimeter_mm, "is_outer": c.is_outer_profile} for c in features.contours[:10]],
                    "radii": [{"r_mm": r.radius_mm} for r in features.radii[:20]],
                },
            }
            client = Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=400,
                temperature=0,
                system=(
                    "You are a CNC manufacturing analyst. Return only valid JSON with: "
                    "likely_process, feature_notes, complexity_adjustment, machinist_warnings, confidence."
                ),
                messages=[{"role": "user", "content": json.dumps(payload)}],
            )
            if not response.content:
                return None
            text = getattr(response.content[0], "text", None)
            return text if isinstance(text, str) else None
        except Exception as exc:
            logger.warning("ai_analysis_failed error=%s", exc)
            return None
