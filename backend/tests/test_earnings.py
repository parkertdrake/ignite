"""Earnings CRUD + budget summary (income) tests."""


def _make_budget(client, name="2026"):
    return client.post("/api/budgets", json={"name": name}).json()


def test_new_budget_summary_is_zero(client):
    budget = _make_budget(client)
    assert budget["summary"] == {
        "income": 0.0, "savings": 0.0, "taxes": 0.0, "spending": 0.0, "net": 0.0,
    }


def test_create_and_list_earnings(client):
    budget = _make_budget(client)
    created = client.post(
        f"/api/budgets/{budget['id']}/earnings",
        json={"person": "Parker", "gross_annual": 238000},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["person"] == "Parker"
    assert body["gross_annual"] == 238000.0

    listed = client.get(f"/api/budgets/{budget['id']}/earnings").json()
    assert len(listed) == 1


def test_summary_income_is_monthly_sum(client):
    budget = _make_budget(client)
    client.post(
        f"/api/budgets/{budget['id']}/earnings",
        json={"person": "Parker", "gross_annual": 238000},
    )
    client.post(
        f"/api/budgets/{budget['id']}/earnings",
        json={"person": "Mythri", "gross_annual": 191360},
    )
    summary = client.get(f"/api/budgets/{budget['id']}").json()["summary"]
    # (238000 + 191360) / 12
    assert round(summary["income"], 2) == 35780.0
    assert summary["net"] == summary["income"]


def test_update_earning(client):
    budget = _make_budget(client)
    earning = client.post(
        f"/api/budgets/{budget['id']}/earnings",
        json={"person": "Parker", "gross_annual": 100000},
    ).json()
    updated = client.patch(
        f"/api/budgets/{budget['id']}/earnings/{earning['id']}",
        json={"gross_annual": 120000},
    ).json()
    assert updated["gross_annual"] == 120000.0
    assert updated["person"] == "Parker"


def test_delete_earning(client):
    budget = _make_budget(client)
    earning = client.post(
        f"/api/budgets/{budget['id']}/earnings",
        json={"person": "Parker", "gross_annual": 100000},
    ).json()
    assert client.delete(f"/api/budgets/{budget['id']}/earnings/{earning['id']}").status_code == 204
    assert client.get(f"/api/budgets/{budget['id']}/earnings").json() == []


def test_earnings_on_missing_budget_404(client):
    assert client.get("/api/budgets/999/earnings").status_code == 404
    assert (
        client.post("/api/budgets/999/earnings", json={"person": "X", "gross_annual": 1}).status_code
        == 404
    )


def test_create_earning_rejects_negative(client):
    budget = _make_budget(client)
    response = client.post(
        f"/api/budgets/{budget['id']}/earnings",
        json={"person": "Parker", "gross_annual": -5},
    )
    assert response.status_code == 422
