from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


MONEY_QUANT = Decimal("0.01")
PERCENT_QUANT = Decimal("0.01")


def quantize_money(value):
    return Decimal(value).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def quantize_percent(value):
    return Decimal(value).quantize(PERCENT_QUANT, rounding=ROUND_HALF_UP)


def calculate_sale_price_from_margin(cost, margin):
    cost = Decimal(cost or 0)
    margin = Decimal(margin or 0)
    if margin >= 100:
        raise ValueError("A margem de lucro deve ser menor que 100%.")
    return quantize_money(cost / (Decimal("1") - (margin / Decimal("100"))))


def calculate_profit_margin(cost, sale_price):
    cost = Decimal(cost or 0)
    sale_price = Decimal(sale_price or 0)
    if sale_price <= cost or sale_price <= 0:
        return Decimal("0.00")
    margin = (Decimal("1") - (cost / sale_price)) * Decimal("100")
    return quantize_percent(margin)


def decimals_are_close(first, second, tolerance=Decimal("0.01")):
    try:
        return abs(Decimal(first or 0) - Decimal(second or 0)) <= tolerance
    except (InvalidOperation, TypeError, ValueError):
        return False
