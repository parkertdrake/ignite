"""Pure tax-math unit tests: bracket boundaries, flat tax, FICA caps."""
import pytest

from persistence.models import TaxParams
from services.tax_service import fica_tax, progressive_tax

FEDERAL_2025 = [
    (0, 0.10), (23850, 0.12), (96950, 0.22), (206700, 0.24),
    (394600, 0.32), (501050, 0.35), (751600, 0.37),
]


def test_zero_and_negative_taxable_is_zero():
    assert progressive_tax(0, FEDERAL_2025) == 0.0
    assert progressive_tax(-5000, FEDERAL_2025) == 0.0


def test_first_bracket_only():
    # Exactly at the top of the 10% bracket → all taxed at 10%.
    assert progressive_tax(23850, FEDERAL_2025) == pytest.approx(2385.0)


def test_bracket_boundary_second_floor():
    # At the 12% ceiling: 2385 (10%) + 73100 * 12%.
    assert progressive_tax(96950, FEDERAL_2025) == pytest.approx(2385 + 73100 * 0.12)


def test_progressive_across_four_brackets():
    # $240k taxable spans 10/12/22/24%.
    expected = 2385 + 8772 + 24145 + 7992
    assert progressive_tax(240000, FEDERAL_2025) == pytest.approx(expected)


def test_top_bracket():
    expected = (
        2385 + 8772 + 24145 + (394600 - 206700) * 0.24
        + (501050 - 394600) * 0.32 + (751600 - 501050) * 0.35
        + (800000 - 751600) * 0.37
    )
    assert progressive_tax(800000, FEDERAL_2025) == pytest.approx(expected)


def test_flat_tax_single_bracket():
    assert progressive_tax(100000, [(0, 0.0495)]) == pytest.approx(4950.0)


def test_no_brackets_is_zero_income_tax():
    # A no-income-tax state (WA) has no bracket rows.
    assert progressive_tax(100000, []) == 0.0


def _federal_params():
    return TaxParams(
        year=2025, jurisdiction="federal", filing_status="mfj",
        ss_wage_base=176100, ss_rate=0.062,
        medicare_rate=0.0145, medicare_addl_rate=0.009,
        medicare_addl_threshold=250000,
    )


def test_fica_below_caps():
    ss, medicare = fica_tax([150000, 150000], _federal_params())
    assert ss == pytest.approx(2 * 150000 * 0.062)
    # Medicare: 1.45% on all + 0.9% on wages over $250k (MFJ).
    assert medicare == pytest.approx(300000 * 0.0145 + 50000 * 0.009)


def test_social_security_caps_per_person():
    ss, _ = fica_tax([200000, 100000], _federal_params())
    assert ss == pytest.approx(176100 * 0.062 + 100000 * 0.062)


def test_no_additional_medicare_below_threshold():
    _, medicare = fica_tax([120000, 120000], _federal_params())
    assert medicare == pytest.approx(240000 * 0.0145)


def test_fica_zero_when_params_missing():
    empty = TaxParams(year=2025, jurisdiction="WA", filing_status="mfj")
    assert fica_tax([150000], empty) == (0.0, 0.0)
