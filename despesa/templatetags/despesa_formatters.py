from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


def _decimal_value(value):
    if value in (None, ''):
        return Decimal('0.00')

    try:
        return Decimal(str(value)).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0.00')


def _format_brazilian_decimal(value):
    amount = _decimal_value(value)
    sign = '-' if amount < 0 else ''
    formatted = f'{abs(amount):,.2f}'
    return sign + formatted.replace(',', 'X').replace('.', ',').replace('X', '.')


@register.filter
def brl(value):
    return f'R$ {_format_brazilian_decimal(value)}'


@register.filter
def br_percent(value):
    return f'{_format_brazilian_decimal(value)}%'
