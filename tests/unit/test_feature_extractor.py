from app.services.dxf_parser import DXFParser
from app.services.feature_extractor import FeatureExtractor


def test_features_from_simple_plate(fixtures):
    geometry = DXFParser().parse(fixtures / "simple_plate.dxf")
    features = FeatureExtractor().extract(geometry)
    assert len(features.holes) == 4
    assert len(features.contours) == 1
    assert features.total_feature_count >= 5
    assert 0 <= features.complexity_score <= 100
