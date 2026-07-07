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


def test_create_rejects_blank_name(client):
    response = client.post("/api/budgets", json={"name": ""})
    assert response.status_code == 422
