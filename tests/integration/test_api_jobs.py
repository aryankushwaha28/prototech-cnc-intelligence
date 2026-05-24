def test_full_pipeline_returns_complete(client, fixtures):
    with (fixtures / "simple_plate.dxf").open("rb") as handle:
        response = client.post(
            "/api/jobs",
            files={"file": ("simple_plate.dxf", handle, "application/dxf")},
            data={"material": "aluminum_6061", "quantity": "2", "use_ai": "false"},
        )
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    result = client.get(f"/api/jobs/{job_id}")
    assert result.status_code == 200
    data = result.json()
    assert data["status"] == "complete"
    assert data["quote"]["cost_breakdown"]["total_for_quantity_inr"] > 0

    pdf = client.get(f"/api/jobs/{job_id}/quote.pdf")
    assert pdf.status_code == 200
    assert len(pdf.content) > 100

    nc = client.get(f"/api/jobs/{job_id}/program.nc")
    assert nc.status_code == 200
    assert "G21" in nc.text


def test_wrong_extension_returns_400(client):
    response = client.post(
        "/api/jobs",
        files={"file": ("bad.txt", b"nope", "text/plain")},
        data={"material": "aluminum_6061", "quantity": "1"},
    )
    assert response.status_code == 400


def test_missing_job_returns_404(client):
    assert client.get("/api/jobs/not-real").status_code == 404
