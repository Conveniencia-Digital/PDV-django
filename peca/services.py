from decimal import Decimal

from peca.models import Pecas


ZERO = Decimal('0.00')


def build_peca_dashboard(user):
    pecas = Pecas.objects.filter(usuario=user)
    preco_custo = ZERO
    preco_venda = ZERO
    despesa_paga_total = ZERO
    despesa_a_pagar_total = ZERO

    for peca in pecas.only(
        'preco_de_custo',
        'preco_peca',
        'quantidade',
        'forma_pagamento',
        'valor_entrada',
    ):
        preco_custo += peca.precototal()
        preco_venda += peca.vendatotal()
        despesa_paga_total += peca.despesa_paga()
        despesa_a_pagar_total += peca.despesa_a_pagar()

    return {
        'total': pecas.count(),
        'preco_custo': preco_custo,
        'preco_venda': preco_venda,
        'lucro': preco_venda - preco_custo,
        'despesa_paga_total': despesa_paga_total,
        'despesa_a_pagar_total': despesa_a_pagar_total,
    }
