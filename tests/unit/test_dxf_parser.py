import pytest

from app.exceptions import DXFParseError
from app.services.dxf_parser import DXFParser


def test_parse_circles(fixtures):
    geometry = DXFParser().parse(fixtures / "simple_plate.dxf")
    assert len(geometry.circles) == 4
    assert geometry.bounding_box.max_x == 120


def test_parse_invalid_file(fixtures):
    with pytest.raises(DXFParseError):
        DXFParser().parse(fixtures / "invalid.dxf")
