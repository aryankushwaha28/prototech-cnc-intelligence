import ezdxf
import pytest

from app.exceptions import DXFParseError, EmptyGeometryError
from app.services.dxf_parser import DXFParser


# ── 1. Circles ──
def test_parse_circles(fixtures):
    geometry = DXFParser().parse(fixtures / "simple_plate.dxf")
    assert len(geometry.circles) == 4
    assert geometry.bounding_box.max_x == 120


# ── 2. Invalid file ──
def test_parse_invalid_file(fixtures):
    with pytest.raises(DXFParseError):
        DXFParser().parse(fixtures / "invalid.dxf")


# ── 3. Contour part — mixed entities: arcs, circles, polylines ──
def test_parse_contour_part(fixtures):
    geometry = DXFParser().parse(fixtures / "contour_part.dxf")
    assert len(geometry.arcs) == 1
    assert len(geometry.circles) == 1
    assert len(geometry.polylines) == 2  # outer + pocket
    assert geometry.entity_count >= 4


# ── 4. Turning profile — open polyline + arc ──
def test_parse_turning_profile(fixtures):
    geometry = DXFParser().parse(fixtures / "turning_profile.dxf")
    assert len(geometry.polylines) == 1
    assert not geometry.polylines[0].is_closed  # open profile
    assert geometry.polylines[0].area is None     # open → no area
    assert len(geometry.arcs) == 1
    assert geometry.polylines[0].perimeter > 0


# ── 5. Empty DXF (no entities) ──
def test_parse_empty_dxf_raises_empty_geometry(fixtures):
    """A valid DXF with zero entities should raise EmptyGeometryError."""
    empty_path = fixtures / "empty.dxf"
    doc = ezdxf.new("R2010")
    doc.saveas(str(empty_path))
    with pytest.raises(EmptyGeometryError):
        DXFParser().parse(empty_path)
    empty_path.unlink()  # cleanup


# ── 6. Bounding box dimensions ──
def test_bounding_box(fixtures):
    geometry = DXFParser().parse(fixtures / "simple_plate.dxf")
    bbox = geometry.bounding_box
    assert bbox.min_x == 0
    assert bbox.min_y == 0
    assert bbox.width == 120
    assert bbox.height == 80


# ── 7. Metadata — units, version, entity count ──
def test_metadata(fixtures):
    geometry = DXFParser().parse(fixtures / "simple_plate.dxf")
    assert geometry.units == "mm"
    assert geometry.dxf_version == "AC1024"  # ezdxf internal code for R2010
    assert geometry.entity_count == 5  # 1 polyline + 4 circles
    assert geometry.source_file == "simple_plate.dxf"


def test_parse_spline_as_polyline(tmp_path):
    path = tmp_path / "spline_part.dxf"
    doc = ezdxf.new("R2000")
    doc.modelspace().add_spline(fit_points=[(0, 0), (15, 10), (30, 0)])
    doc.saveas(path)

    geometry = DXFParser().parse(path)

    assert len(geometry.polylines) == 1
    assert not geometry.polylines[0].is_closed
    assert len(geometry.polylines[0].vertices) > 2
