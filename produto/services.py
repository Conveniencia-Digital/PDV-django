from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from produto.models import Produto


DECIMAL_ZERO = Decimal('0.00')


def _money_expression(field_name):
    return ExpressionWrapper(
        F(field_name) * F('quantidade'),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )


def _as_decimal(value):
    return value if value is not None else DECIMAL_ZERO


def _as_chart_number(value):
    return float(value or 0)


def _margin_percent(cost, price):
    cost = _as_decimal(cost)
    price = _as_decimal(price)
    if price <= 0:
        return DECIMAL_ZERO
    return ((price - cost) / price) * Decimal('100')


def _average_days_in_stock(products):
    today = timezone.localdate()
    ages = []
    for created_at in products.filter(quantidade__gt=0).values_list('data_criacao', flat=True):
        if not created_at:
            continue
        created_date = timezone.localtime(created_at).date()
        ages.append(max((today - created_date).days, 0))

    if not ages:
        return 0

    return round(sum(ages) / len(ages), 1)


def _stock_expense_totals(products):
    paid_total = DECIMAL_ZERO
    payable_total = DECIMAL_ZERO

    for produto in products.only(
        'preco_de_custo',
        'quantidade',
        'forma_pagamento',
        'valor_entrada',
    ):
        paid_total += produto.despesa_paga()
        payable_total += produto.despesa_a_pagar()

    return paid_total, payable_total


def build_produto_dashboard(user):
    produtos = Produto.objects.filter(usuario=user)
    sale_stock_expr = _money_expression('preco')
    cost_stock_expr = _money_expression('preco_de_custo')

    totals = produtos.aggregate(
        total_produtos=Count('id'),
        quantidade_total=Coalesce(Sum('quantidade'), 0),
        custo_total=Coalesce(Sum(cost_stock_expr), DECIMAL_ZERO),
        valor_venda_total=Coalesce(Sum(sale_stock_expr), DECIMAL_ZERO),
    )

    custo_total = _as_decimal(totals['custo_total'])
    valor_venda_total = _as_decimal(totals['valor_venda_total'])
    lucro_potencial = valor_venda_total - custo_total
    margem_media = DECIMAL_ZERO
    if valor_venda_total > 0:
        margem_media = (lucro_potencial / valor_venda_total) * Decimal('100')

    despesa_paga_total, despesa_a_pagar_total = _stock_expense_totals(produtos)

    categorias_qs = (
        produtos.values('categoria__nome', 'categoria_produtos')
        .annotate(
            produtos=Count('id'),
            unidades=Coalesce(Sum('quantidade'), 0),
            valor_venda=Coalesce(Sum(sale_stock_expr), DECIMAL_ZERO),
        )
        .order_by('-valor_venda', 'categoria__nome', 'categoria_produtos')[:10]
    )
    categorias = []
    for item in categorias_qs:
        nome = item['categoria__nome'] or item['categoria_produtos'] or 'Sem categoria'
        categorias.append({
            'nome': nome,
            'produtos': item['produtos'],
            'unidades': item['unidades'],
            'valor_venda': _as_decimal(item['valor_venda']),
        })

    produtos_margem = []
    for produto in produtos.only(
        'id',
        'nome_produto',
        'quantidade',
        'preco_de_custo',
        'preco',
        'categoria_produtos',
    ):
        margem = _margin_percent(produto.preco_de_custo, produto.preco)
        lucro_unitario = _as_decimal(produto.preco) - _as_decimal(produto.preco_de_custo)
        produtos_margem.append({
            'nome': produto.nome_produto,
            'categoria': produto.categoria_produtos or 'Sem categoria',
            'quantidade': produto.quantidade,
            'preco': _as_decimal(produto.preco),
            'lucro_unitario': lucro_unitario,
            'margem': margem,
            'lucro_potencial': lucro_unitario * Decimal(produto.quantidade or 0),
        })

    produtos_margem.sort(key=lambda item: (item['margem'], item['lucro_potencial']), reverse=True)
    produtos_margem = produtos_margem[:5]

    baixo_estoque_limite = 3
    sem_estoque = produtos.filter(quantidade__lte=0).count()
    baixo_estoque = produtos.filter(quantidade__gt=0, quantidade__lte=baixo_estoque_limite).count()

    charts = {
        'categorias': {
            'labels': [item['nome'] for item in categorias],
            'values': [_as_chart_number(item['valor_venda']) for item in categorias],
        },
        'margens': {
            'labels': [item['nome'] for item in produtos_margem],
            'values': [_as_chart_number(item['margem']) for item in produtos_margem],
        },
    }

    return {
        'produto_total_produtos': totals['total_produtos'],
        'produto_quantidade_total': totals['quantidade_total'] or 0,
        'produto_custo_total': custo_total,
        'produto_valor_venda_total': valor_venda_total,
        'produto_lucro_potencial': lucro_potencial,
        'produto_margem_media': margem_media,
        'produto_despesa_paga_total': despesa_paga_total,
        'produto_despesa_a_pagar_total': despesa_a_pagar_total,
        'produto_baixo_estoque': baixo_estoque,
        'produto_sem_estoque': sem_estoque,
        'produto_tempo_medio_estoque': _average_days_in_stock(produtos),
        'produto_categorias_ranking': categorias,
        'produto_margem_ranking': produtos_margem,
        'produto_category_has_data': bool(categorias),
        'produto_margin_has_data': bool(produtos_margem),
        'produto_category_chart_height': max(280, min(520, 48 * max(len(categorias), 1))),
        'produto_margin_chart_height': max(260, min(420, 52 * max(len(produtos_margem), 1))),
        'produto_charts': charts,
    }
