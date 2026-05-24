class ProtoTechError(Exception):
    code = "PROTOTECH_ERROR"
    http_status = 500
    hint = "Try another DXF or check the app logs."

    def __init__(self, message: str | None = None, *, hint: str | None = None):
        self.message = message or self.code
        self.hint = hint or self.hint
        super().__init__(self.message)


class DXFParseError(ProtoTechError):
    code = "DXF_PARSE_ERROR"
    http_status = 400
    hint = "Ensure the file was exported as a valid DXF."


class EmptyGeometryError(ProtoTechError):
    code = "EMPTY_GEOMETRY"
    http_status = 422
    hint = "The DXF did not contain supported LINE, ARC, CIRCLE, or POLYLINE entities."


class QuoteCalculationError(ProtoTechError):
    code = "QUOTE_CALC_ERROR"
    http_status = 500


class GCodeGenerationError(ProtoTechError):
    code = "GCODE_GEN_ERROR"
    http_status = 500


class AIAnalysisError(ProtoTechError):
    code = "AI_ANALYSIS_ERROR"
    http_status = 200
