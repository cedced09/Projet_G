from decimal import ROUND_HALF_UP, Decimal


def euro_to_cents(value: Decimal | None) -> int | None:
    if value is None:
        return None
    quantized = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(quantized * 100)


def cents_to_euro(value: int | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(value) / Decimal(100)
