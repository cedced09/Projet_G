from decimal import Decimal

from app.domain.value_objects import cents_to_euro, euro_to_cents


def test_euro_to_cents_uses_integer_cents() -> None:
    assert euro_to_cents(Decimal("3000000.00")) == 300000000
    assert euro_to_cents(Decimal("12.345")) == 1235


def test_cents_to_euro_returns_decimal() -> None:
    assert cents_to_euro(275000000) == Decimal("2750000")
