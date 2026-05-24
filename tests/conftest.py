from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBS_DIR", str(tmp_path / "jobs"))
    return TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def fixtures():
    from scripts.generate_fixtures import invalid_file, simple_plate, contour_part, turning_profile

    simple_plate()
    contour_part()
    turning_profile()
    invalid_file()
    return Path("tests/fixtures")
