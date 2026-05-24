from pathlib import Path

from app.schemas.features import FeatureSet
from app.schemas.quote import QuoteResult


class PDFGenerator:
    def generate(self, path: str | Path, quote: QuoteResult, features: FeatureSet, ai_notes: str | None) -> None:
        target = Path(path)
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

            styles = getSampleStyleSheet()
            doc = SimpleDocTemplate(str(target), pagesize=A4, title=f"ProtoTech Quote {quote.job_id}")
            cost = quote.cost_breakdown
            rows = [
                ["Line Item", "Amount"],
                ["Material", f"INR {cost.material_cost_inr:,.2f}"],
                ["Machining", f"INR {cost.machining_cost_inr:,.2f}"],
                ["Tooling / setup", f"INR {cost.tooling_setup_inr:,.2f}"],
                ["Margin", f"INR {cost.margin_inr:,.2f}"],
                ["Total", f"INR {cost.total_for_quantity_inr:,.2f} / USD {cost.total_usd:,.2f}"],
            ]
            table = Table(rows, colWidths=[260, 180])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ]
                )
            )
            story = [
                Paragraph("ProtoTech CNC Intelligence", styles["Title"]),
                Paragraph(f"Quote ID: {quote.job_id}", styles["Normal"]),
                Paragraph(f"Material: {quote.material} | Quantity: {quote.quantity}", styles["Normal"]),
                Spacer(1, 12),
                table,
                Spacer(1, 12),
                Paragraph(
                    f"Features: {len(features.holes)} holes, {len(features.contours)} contours, "
                    f"{len(features.pockets)} pockets, {len(features.radii)} radii",
                    styles["Normal"],
                ),
                Paragraph(f"Estimated machining time: {quote.estimated_machining_time_min:.2f} minutes", styles["Normal"]),
                Spacer(1, 12),
                Paragraph("Warnings", styles["Heading2"]),
                *[Paragraph(warning, styles["Normal"]) for warning in quote.warnings],
            ]
            if ai_notes:
                story.extend([Spacer(1, 12), Paragraph("AI Analysis", styles["Heading2"]), Paragraph(ai_notes, styles["Normal"])])
            doc.build(story)
        except Exception:
            self._fallback_pdf(target, quote)

    def _fallback_pdf(self, path: Path, quote: QuoteResult) -> None:
        text = (
            "ProtoTech CNC Intelligence\n"
            f"Quote ID: {quote.job_id}\n"
            f"Material: {quote.material}\n"
            f"Total INR: {quote.cost_breakdown.total_for_quantity_inr:.2f}\n"
            "Simulator validation required before production machining.\n"
        )
        stream = f"BT /F1 12 Tf 72 760 Td ({text.replace(chr(10), ') Tj T* (')}) Tj ET"
        pdf = (
            "%PDF-1.4\n"
            "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
            "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
            "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
            "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
            f"5 0 obj << /Length {len(stream)} >> stream\n{stream}\nendstream endobj\n"
            "trailer << /Root 1 0 R >>\n%%EOF\n"
        )
        path.write_bytes(pdf.encode("latin-1", errors="ignore"))
