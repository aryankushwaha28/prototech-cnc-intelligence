import ezdxf

from app.services.dxf_parser import DXFParser
from app.services.feature_extractor import FeatureExtractor


def test_features_from_simple_plate(fixtures):
    geometry = DXFParser().parse(fixtures / "simple_plate.dxf")
    features = FeatureExtractor().extract(geometry)
    assert len(features.holes) == 4
    assert len(features.contours) == 1
    assert features.total_feature_count >= 5
    assert 0 <= features.complexity_score <= 100


def test_line_entities_become_open_profiles(tmp_path):
    path = tmp_path / "line_part.dxf"
    doc = ezdxf.new("R2010")
    doc.modelspace().add_line((0, 0), (25, 0))
    doc.saveas(path)

    geometry = DXFParser().parse(path)
    features = FeatureExtractor().extract(geometry)

    assert len(features.open_profiles) == 1
    assert features.open_profiles[0].feature_id.startswith("L")
    assert features.open_profiles[0].perimeter_mm == 25
