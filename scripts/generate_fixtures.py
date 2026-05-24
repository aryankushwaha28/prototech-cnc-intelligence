import os
from pathlib import Path
from typing import Any

os.environ.setdefault("XDG_CACHE_HOME", str(Path(".cache").resolve()))
import ezdxf


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def save(doc: Any, name: str) -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    doc.header["$INSUNITS"] = 4
    doc.saveas(FIXTURES / name)


def simple_plate() -> None:
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (120, 0), (120, 80), (0, 80)], close=True)
    for x in (20, 100):
        for y in (20, 60):
            msp.add_circle((x, y), 4)
    save(doc, "simple_plate.dxf")


def contour_part() -> None:
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (90, 0), (110, 25), (80, 60), (20, 55), (-10, 25)], close=True)
    msp.add_lwpolyline([(25, 18), (55, 18), (55, 38), (25, 38)], close=True)
    msp.add_arc((80, 20), 12, 25, 165)
    msp.add_circle((15, 15), 3)
    save(doc, "contour_part.dxf")


def turning_profile() -> None:
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (40, 0), (40, 18), (75, 18), (75, 30), (110, 30)], close=False)
    msp.add_arc((40, 18), 8, 270, 360)
    save(doc, "turning_profile.dxf")


def invalid_file() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    (FIXTURES / "invalid.dxf").write_text("this is not a dxf", encoding="utf-8")


if __name__ == "__main__":
    simple_plate()
    contour_part()
    turning_profile()
    invalid_file()
    print(f"Generated fixtures in {FIXTURES}")
