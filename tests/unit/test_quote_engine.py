from app.schemas.job import JobCreate
from app.services.dxf_parser import DXFParser
from app.services.feature_extractor import FeatureExtractor
from app.services.quote_engine import QuoteEngine


def test_quote_quantity_scales(fixtures):
    geometry = DXFParser().parse(fixtures / "simple_plate.dxf")
    extractor = FeatureExtractor()
    features = extractor.extract(geometry)
    summary = extractor.summarize_geometry(geometry)
    one = QuoteEngine().calculate("j_test", JobCreate(material="aluminum_6061", quantity=1), summary, features, 83.5)
    ten = QuoteEngine().calculate("j_test", JobCreate(material="aluminum_6061", quantity=10), summary, features, 83.5)
    assert ten.cost_breakdown.total_for_quantity_inr == round(one.cost_breakdown.total_per_piece_inr * 10, 2)


def test_harder_material_longer_time(fixtures):
    geometry = DXFParser().parse(fixtures / "simple_plate.dxf")
    extractor = FeatureExtractor()
    features = extractor.extract(geometry)
    summary = extractor.summarize_geometry(geometry)
    al = QuoteEngine().calculate("j_test", JobCreate(material="aluminum_6061", quantity=1), summary, features, 83.5)
    ss = QuoteEngine().calculate("j_test", JobCreate(material="stainless_304", quantity=1), summary, features, 83.5)
    assert ss.estimated_machining_time_min > al.estimated_machining_time_min
