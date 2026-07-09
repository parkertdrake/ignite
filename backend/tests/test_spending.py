"""Categories + expenses CRUD, summary spending, payer, and clone copy."""


def _make_budget(client, name="2026"):
    return client.post("/api/budgets", json={"name": name}).json()


def _add_category(client, budget_id, name):
    return client.post(f"/api/budgets/{budget_id}/categories", json={"name": name})


def _add_expense(client, budget_id, **fields):
    payload = {"item": "Rent", "amount_annual": 46200, "payer_type": "joint_fixed"}
    payload.update(fields)
    return client.post(f"/api/budgets/{budget_id}/expenses", json=payload)


def test_create_and_list_category(client):
    budget = _make_budget(client)
    created = _add_category(client, budget["id"], "Home")
    assert created.status_code == 201
    assert created.json()["name"] == "Home"
    listed = client.get(f"/api/budgets/{budget['id']}/categories").json()
    assert [category["name"] for category in listed] == ["Home"]


def test_category_create_is_idempotent(client):
    budget = _make_budget(client)
    first = _add_category(client, budget["id"], "Food").json()
    second = _add_category(client, budget["id"], "Food").json()
    assert first["id"] == second["id"]


def test_create_expense_with_category_and_payer(client):
    budget = _make_budget(client)
    category = _add_category(client, budget["id"], "Home").json()
    created = _add_expense(
        client, budget["id"], item="Rent", amount_annual=46200,
        category_id=category["id"], payer_type="joint_fixed",
    )
    assert created.status_code == 201
    body = created.json()
    assert body["item"] == "Rent"
    assert body["category_id"] == category["id"]
    assert body["payer_type"] == "joint_fixed"
    assert body["payer_person"] is None


def test_individual_expense_keeps_person(client):
    budget = _make_budget(client)
    body = _add_expense(
        client, budget["id"], item="Olympic Gym", amount_annual=2160,
        payer_type="individual", payer_person="Parker",
    ).json()
    assert body["payer_type"] == "individual"
    assert body["payer_person"] == "Parker"


def test_switching_to_joint_clears_person(client):
    budget = _make_budget(client)
    expense = _add_expense(
        client, budget["id"], payer_type="individual", payer_person="Parker"
    ).json()
    updated = client.patch(
        f"/api/budgets/{budget['id']}/expenses/{expense['id']}",
        json={"payer_type": "joint_variable"},
    ).json()
    assert updated["payer_type"] == "joint_variable"
    assert updated["payer_person"] is None


def test_period_toggle_and_monthly_derivation(client):
    budget = _make_budget(client)
    # $21.33/mo renters insurance entered yearly as 256.
    expense = _add_expense(
        client, budget["id"], item="Renters", amount_annual=256, period="yearly",
        payer_type="joint_fixed",
    ).json()
    assert expense["period"] == "yearly"
    assert expense["amount_annual"] == 256.0


def test_summary_folds_in_spending(client):
    budget = _make_budget(client)
    _add_expense(client, budget["id"], item="Rent", amount_annual=46200)
    detail = client.get(f"/api/budgets/{budget['id']}").json()
    assert detail["summary"]["spending"] == 46200 / 12
    assert detail["summary"]["net"] == -(46200 / 12)


def test_deleting_category_uncategorizes_expenses(client):
    budget = _make_budget(client)
    category = _add_category(client, budget["id"], "Home").json()
    expense = _add_expense(client, budget["id"], category_id=category["id"]).json()
    resp = client.delete(f"/api/budgets/{budget['id']}/categories/{category['id']}")
    assert resp.status_code == 204
    refetched = client.get(f"/api/budgets/{budget['id']}/expenses").json()[0]
    assert refetched["category_id"] is None


def test_clone_copies_categories_and_expenses(client):
    budget = _make_budget(client)
    category = _add_category(client, budget["id"], "Home").json()
    _add_expense(client, budget["id"], item="Rent", category_id=category["id"])
    clone = client.post(
        f"/api/budgets/{budget['id']}/copy", json={"name": "2027"}
    ).json()

    clone_categories = client.get(f"/api/budgets/{clone['id']}/categories").json()
    clone_expenses = client.get(f"/api/budgets/{clone['id']}/expenses").json()
    assert [category["name"] for category in clone_categories] == ["Home"]
    assert len(clone_expenses) == 1
    # Expense points at the clone's own category, not the source's.
    assert clone_expenses[0]["category_id"] == clone_categories[0]["id"]
    assert clone_categories[0]["id"] != category["id"]
