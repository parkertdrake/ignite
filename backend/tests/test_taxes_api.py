"""End-to-end tax computation over the API, against seeded 2025 data."""
import pytest


def _budget_with_income(client, earners, pretax_401k=0):
    budget = client.post("/api/budgets", json={"name": "2025"}).json()
    for index, gross in enumerate(earners):
        client.post(
            f"/api/budgets/{budget['id']}/earnings",
            json={"person": f"P{index}", "gross_annual": gross},
        )
    if pretax_401k:
        client.post(
            f"/api/budgets/{budget['id']}/savings",
            json={"person": "P0", "account": "401k",
                  "amount_annual": pretax_401k, "pretax": True},
        )
    return budget


def test_config_options_lists_years_and_states(seeded_client):
    options = seeded_client.get("/api/tax-config/options").json()
    assert 2025 in options["years"]
    assert set(options["states"]) == {"IL", "WA"}


def test_federal_and_fica_no_state(seeded_client):
    budget = _budget_with_income(seeded_client, [150000, 150000], pretax_401k=30000)
    taxes = seeded_client.get(f"/api/budgets/{budget['id']}/taxes").json()

    # taxable = 300k - 30k pretax - 30k std deduction = 240k.
    assert taxes["federal_taxable"] == pytest.approx(240000)
    assert taxes["federal_income"] == pytest.approx(2385 + 8772 + 24145 + 7992)
    assert taxes["social_security"] == pytest.approx(2 * 150000 * 0.062)
    assert taxes["medicare"] == pytest.approx(300000 * 0.0145 + 50000 * 0.009)
    assert taxes["state_income"] == 0.0


def test_pretax_savings_reduce_federal_tax(seeded_client):
    without = _budget_with_income(seeded_client, [200000])
    with_pretax = _budget_with_income(seeded_client, [200000], pretax_401k=23500)
    tax_without = seeded_client.get(f"/api/budgets/{without['id']}/taxes").json()
    tax_with = seeded_client.get(f"/api/budgets/{with_pretax['id']}/taxes").json()

    assert tax_with["federal_taxable"] == pytest.approx(
        tax_without["federal_taxable"] - 23500
    )
    assert tax_with["federal_income"] < tax_without["federal_income"]
    # FICA is on gross wages — pretax 401k does not reduce it.
    assert tax_with["social_security"] == pytest.approx(tax_without["social_security"])


def test_illinois_flat_tax_with_exemption(seeded_client):
    budget = _budget_with_income(seeded_client, [100000, 100000])
    seeded_client.patch(
        f"/api/budgets/{budget['id']}/tax-config", json={"state": "IL"}
    )
    taxes = seeded_client.get(f"/api/budgets/{budget['id']}/taxes").json()
    # IL: 200k - (2 earners * $2,775 exemption) = 194,450 @ 4.95%.
    assert taxes["state_taxable"] == pytest.approx(194450)
    assert taxes["state_income"] == pytest.approx(194450 * 0.0495)


def test_washington_has_no_state_tax(seeded_client):
    budget = _budget_with_income(seeded_client, [200000])
    seeded_client.patch(
        f"/api/budgets/{budget['id']}/tax-config", json={"state": "WA"}
    )
    taxes = seeded_client.get(f"/api/budgets/{budget['id']}/taxes").json()
    assert taxes["state_income"] == 0.0


def test_taxes_fold_into_budget_summary(seeded_client):
    budget = _budget_with_income(seeded_client, [150000, 150000], pretax_401k=30000)
    detail = seeded_client.get(f"/api/budgets/{budget['id']}").json()
    summary = detail["summary"]
    annual_total = seeded_client.get(
        f"/api/budgets/{budget['id']}/taxes"
    ).json()["total_annual"]

    assert summary["taxes"] == pytest.approx(annual_total / 12)
    assert summary["net"] == pytest.approx(
        summary["income"] - summary["savings"] - summary["taxes"] - summary["spending"]
    )


def test_config_defaults_to_latest_year(seeded_client):
    # No tax_year set on the budget → engine resolves to the latest seeded year.
    budget = _budget_with_income(seeded_client, [100000])
    taxes = seeded_client.get(f"/api/budgets/{budget['id']}/taxes").json()
    assert taxes["year"] == 2025
