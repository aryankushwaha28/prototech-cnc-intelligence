from app.schemas.job import JobCreate
from app.services.dxf_parser import DXFParser
from app.services.feature_extractor import FeatureExtractor
from app.services.gcode_generator import GCodeGenerator


def test_gcode_structure(fixtures):
    geometry = DXFParser().parse(fixtures / "simple_plate.dxf")
    features = FeatureExtractor().extract(geometry)
    program = GCodeGenerator().generate("j_test", JobCreate(material="aluminum_6061", quantity=1), features, 20)
    assert program.program_text.startswith("%\nO")
    assert "G21" in program.program_text
    assert "G81" in program.program_text
    assert program.program_text.rstrip().endswith("%")
