"""Budget API + single-active invariant tests (SQLite-backed)."""


def test_create_first_budget_auto_activates(client):
    response = client.post("/api/budgets", json={"name": "2026"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "2026"
    assert body["status"] == "active"
    assert body["id"] > 0


def test_second_budget_is_inactive_by_default(client):
    client.post("/api/budgets", json={"name": "2026"})
    response = client.post("/api/budgets", json={"name": "2025"})
    assert response.status_code == 201
    assert response.json()["status"] == "inactive"


def test_list_returns_newest_first(client):
    client.post("/api/budgets", json={"name": "2026"})
    client.post("/api/budgets", json={"name": "2025"})
    budgets = client.get("/api/budgets").json()
    assert [budget["name"] for budget in budgets] == ["2025", "2026"]


def test_activate_demotes_previous_active(client):
    first = client.post("/api/budgets", json={"name": "2026"}).json()
    second = client.post("/api/budgets", json={"name": "2025"}).json()
    assert first["status"] == "active"
    assert second["status"] == "inactive"

    activated = client.post(f"/api/budgets/{second['id']}/activate").json()
    assert activated["status"] == "active"

    by_id = {budget["id"]: budget for budget in client.get("/api/budgets").json()}
    assert by_id[first["id"]]["status"] == "inactive"
    assert by_id[second["id"]]["status"] == "active"


def test_activate_missing_budget_404(client):
    response = client.post("/api/budgets/999/activate")
    assert response.status_code == 404


def test_get_missing_budget_404(client):
    response = client.get("/api/budgets/999")
    assert response.status_code == 404


def test_delete_budget(client):
    budget = client.post("/api/budgets", json={"name": "2026"}).json()
    assert client.delete(f"/api/budgets/{budget['id']}").status_code == 204
    assert client.get(f"/api/budgets/{budget['id']}").status_code == 404
    assert client.get("/api/budgets").json() == []


def test_delete_missing_budget_404(client):
    assert client.delete("/api/budgets/999").status_code == 404


def test_delete_budget_removes_its_earnings(client):
    budget = client.post("/api/budgets", json={"name": "2026"}).json()
    client.post(
        f"/api/budgets/{budget['id']}/earnings",
        json={"person": "Parker", "gross_annual": 100000},
    )
    client.delete(f"/api/budgets/{budget['id']}")
    # Recreate a budget; its earnings must be empty (old rows gone, not leaked).
    fresh = client.post("/api/budgets", json={"name": "2027"}).json()
    assert client.get(f"/api/budgets/{fresh['id']}/earnings").json() == []


def test_clone_budget_duplicates_earnings_and_name(client):
    source = client.post("/api/budgets", json={"name": "2026"}).json()
    client.post(
        f"/api/budgets/{source['id']}/earnings",
        json={"person": "Parker", "gross_annual": 238000},
    )
    client.post(
        f"/api/budgets/{source['id']}/earnings",
        json={"person": "Mythri", "gross_annual": 191360},
    )

    cloned = client.post(f"/api/budgets/{source['id']}/copy", json={"name": "2026 copy"})
    assert cloned.status_code == 201
    clone_body = cloned.json()
    assert clone_body["name"] == "2026 copy"
    assert clone_body["status"] == "inactive"
    assert clone_body["id"] != source["id"]
    assert round(clone_body["summary"]["income"], 2) == 35780.0

    clone_earnings = client.get(f"/api/budgets/{clone_body['id']}/earnings").json()
    assert {earning["person"] for earning in clone_earnings} == {"Parker", "Mythri"}

    # Clone is independent: editing it does not touch the source.
    client.patch(
        f"/api/budgets/{clone_body['id']}/earnings/{clone_earnings[0]['id']}",
        json={"gross_annual": 1},
    )
    source_earnings = client.get(f"/api/budgets/{source['id']}/earnings").json()
    assert all(earning["gross_annual"] > 1 for earning in source_earnings)


def test_clone_missing_budget_404(client):
    assert client.post("/api/budgets/999/copy", json={"name": "x"}).status_code == 404


def test_create_rejects_blank_name(client):
    response = client.post("/api/budgets", json={"name": ""})
    assert response.status_code == 422
