"""Savings CRUD, pretax filtering, and summary contribution."""


def _make_budget(client, name="2026"):
    return client.post("/api/budgets", json={"name": name}).json()


def _add_saving(client, budget_id, person, account, amount_annual, pretax):
    return client.post(
        f"/api/budgets/{budget_id}/savings",
        json={
            "person": person,
            "account": account,
            "amount_annual": amount_annual,
            "pretax": pretax,
        },
    )


def test_create_and_list_savings(client):
    budget = _make_budget(client)
    created = _add_saving(client, budget["id"], "Parker", "401k", 23496, True)
    assert created.status_code == 201
    body = created.json()
    assert body["account"] == "401k"
    assert body["amount_annual"] == 23496.0
    assert body["period"] == "yearly"
    assert body["pretax"] is True

    listed = client.get(f"/api/budgets/{budget['id']}/savings").json()
    assert len(listed) == 1


def test_period_defaults_and_updates(client):
    budget = _make_budget(client)
    saving = _add_saving(client, budget["id"], "Parker", "401k", 23496, True).json()
    assert saving["period"] == "yearly"
    updated = client.patch(
        f"/api/budgets/{budget['id']}/savings/{saving['id']}",
        json={"period": "monthly"},
    ).json()
    assert updated["period"] == "monthly"


def test_period_can_be_set_on_create(client):
    budget = _make_budget(client)
    response = client.post(
        f"/api/budgets/{budget['id']}/savings",
        json={
            "person": "Parker",
            "account": "401k",
            "amount_annual": 23496,
            "period": "monthly",
            "pretax": True,
        },
    )
    assert response.json()["period"] == "monthly"


def test_pretax_filter(client):
    budget = _make_budget(client)
    _add_saving(client, budget["id"], "Parker", "401k", 23496, True)
    _add_saving(client, budget["id"], "Parker", "Brokerage", 6000, False)

    pretax = client.get(f"/api/budgets/{budget['id']}/savings?pretax=true").json()
    posttax = client.get(f"/api/budgets/{budget['id']}/savings?pretax=false").json()
    assert [item["account"] for item in pretax] == ["401k"]
    assert [item["account"] for item in posttax] == ["Brokerage"]


def test_savings_feed_summary(client):
    budget = _make_budget(client)
    # 23496 + 2400 = 25896 / 12 = 2158 monthly.
    _add_saving(client, budget["id"], "Parker", "401k", 23496, True)
    _add_saving(client, budget["id"], "Mythri", "HSA", 2400, True)
    summary = client.get(f"/api/budgets/{budget['id']}").json()["summary"]
    assert summary["savings"] == 2158.0
    # No income yet, so net = -savings.
    assert summary["net"] == -2158.0


def test_update_saving(client):
    budget = _make_budget(client)
    saving = _add_saving(client, budget["id"], "Parker", "401k", 12000, True).json()
    updated = client.patch(
        f"/api/budgets/{budget['id']}/savings/{saving['id']}",
        json={"amount_annual": 23496},
    ).json()
    assert updated["amount_annual"] == 23496.0
    assert updated["account"] == "401k"


def test_delete_saving(client):
    budget = _make_budget(client)
    saving = _add_saving(client, budget["id"], "Parker", "401k", 12000, True).json()
    assert (
        client.delete(f"/api/budgets/{budget['id']}/savings/{saving['id']}").status_code == 204
    )
    assert client.get(f"/api/budgets/{budget['id']}/savings").json() == []


def test_savings_on_missing_budget_404(client):
    assert client.get("/api/budgets/999/savings").status_code == 404


def test_clone_copies_savings(client):
    budget = _make_budget(client)
    _add_saving(client, budget["id"], "Parker", "401k", 23496, True)
    clone = client.post(f"/api/budgets/{budget['id']}/copy", json={"name": "copy"}).json()
    clone_savings = client.get(f"/api/budgets/{clone['id']}/savings").json()
    assert len(clone_savings) == 1
    assert clone_savings[0]["account"] == "401k"


def test_create_saving_rejects_negative(client):
    budget = _make_budget(client)
    response = _add_saving(client, budget["id"], "Parker", "401k", -1, True)
    assert response.status_code == 422
