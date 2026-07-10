"""Budget cash-flow (Sankey) endpoint: nodes, links, and edge cases."""


def _make_budget(client, name="2026"):
    return client.post("/api/budgets", json={"name": name}).json()


def _add_earning(client, budget_id, person, gross_annual):
    return client.post(
        f"/api/budgets/{budget_id}/earnings",
        json={"person": person, "gross_annual": gross_annual},
    )


def _add_saving(client, budget_id, person, account, amount_annual, pretax):
    return client.post(
        f"/api/budgets/{budget_id}/savings",
        json={
            "person": person,
            "account": account,
            "amount_annual": amount_annual,
            "period": "yearly",
            "pretax": pretax,
        },
    )


def _add_expense(client, budget_id, item, amount_annual):
    return client.post(
        f"/api/budgets/{budget_id}/expenses",
        json={"item": item, "amount_annual": amount_annual, "payer_type": "joint_fixed"},
    )


def _flow(client, budget_id):
    return client.get(f"/api/budgets/{budget_id}/flow").json()


def _link(flow, source, target):
    for link in flow["links"]:
        if link["source"] == source and link["target"] == target:
            return link
    return None


def test_flow_missing_budget_404(client):
    assert client.get("/api/budgets/999/flow").status_code == 404


def test_empty_budget_has_no_nodes(client):
    budget = _make_budget(client)
    flow = _flow(client, budget["id"])
    assert flow["nodes"] == []
    assert flow["links"] == []


def test_person_income_flows_into_household(client):
    budget = _make_budget(client)
    _add_earning(client, budget["id"], "Parker", 120000)
    _add_earning(client, budget["id"], "Sam", 60000)
    flow = _flow(client, budget["id"])

    node_ids = {node["id"] for node in flow["nodes"]}
    assert {"person:Parker", "person:Sam", "household"} <= node_ids
    assert _link(flow, "person:Parker", "household")["value"] == 10000
    assert _link(flow, "person:Sam", "household")["value"] == 5000


def test_savings_split_pretax_and_posttax(client):
    budget = _make_budget(client)
    _add_earning(client, budget["id"], "Parker", 240000)
    _add_saving(client, budget["id"], "Parker", "401k", 24000, pretax=True)
    _add_saving(client, budget["id"], "Parker", "Brokerage", 12000, pretax=False)
    flow = _flow(client, budget["id"])

    assert _link(flow, "household", "pretax_savings")["value"] == 2000
    assert _link(flow, "household", "posttax_savings")["value"] == 1000
    tones = {node["id"]: node["tone"] for node in flow["nodes"]}
    assert tones["pretax_savings"] == "savings"
    assert tones["posttax_savings"] == "savings"


def test_unallocated_remainder_becomes_net_outflow(client):
    # No tax data under plain client, no savings/spending → whole income is net.
    budget = _make_budget(client)
    _add_earning(client, budget["id"], "Parker", 120000)
    flow = _flow(client, budget["id"])
    assert _link(flow, "household", "net")["value"] == 10000


def test_overallocation_adds_deficit_inflow(client):
    budget = _make_budget(client)
    _add_earning(client, budget["id"], "Parker", 12000)  # 1000/mo
    _add_expense(client, budget["id"], "Rent", 24000)  # 2000/mo — over budget
    flow = _flow(client, budget["id"])

    assert _link(flow, "deficit", "household")["value"] == 1000
    assert _link(flow, "household", "net") is None
    assert any(node["id"] == "deficit" for node in flow["nodes"])
