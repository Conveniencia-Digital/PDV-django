from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Max, Min, Sum
from django.utils import timezone
from django.utils.dateparse import parse_date

from financeiro.services import decimal_to_float, money
from venda.models import ItemsVenda, Vendas


ZERO = Decimal("0.00")


@dataclass(frozen=True)
class PeriodoVendas:
    key: str
    label: str
    start: date = None
    end: date = None
    all_data: bool = False

    @property
    def days(self):
        if self.all_data or not self.start or not self.end:
            return 0
        return max((self.end - self.start).days + 1, 1)


def inicio_fim_dia(data):
    inicio = timezone.make_aware(datetime.combine(data, datetime.min.time()))
    fim = timezone.make_aware(datetime.combine(data, datetime.max.time()))
    return inicio, fim


def _mes_passado(hoje):
    primeiro_deste_mes = hoje.replace(day=1)
    ultimo_mes_passado = primeiro_deste_mes - timedelta(days=1)
    return ultimo_mes_passado.replace(day=1), ultimo_mes_passado


def resolver_periodo_vendas(params):
    inicio = params.get("inicio") or params.get("data_inicio")
    fim = params.get("fim") or params.get("data_fim")
    periodo = params.get("periodo")
    hoje = timezone.localdate()

    aliases = {
        "today": "hoje",
        "yesterday": "ontem",
        "last_7_days": "7dias",
        "current_month": "este_mes",
        "previous_month": "mes_passado",
        "current_year": "este_ano",
        "custom": "personalizado",
    }
    periodo = aliases.get(periodo, periodo)

    if not inicio and not fim and not periodo:
        periodo = "hoje"

    if periodo == "hoje":
        return PeriodoVendas("hoje", "Hoje", hoje, hoje)
    if periodo == "ontem":
        data = hoje - timedelta(days=1)
        return PeriodoVendas("ontem", "Ontem", data, data)
    if periodo == "7dias":
        return PeriodoVendas("7dias", "Ultimos 7 dias", hoje - timedelta(days=6), hoje)
    if periodo == "este_mes":
        return PeriodoVendas("este_mes", "Este mes", hoje.replace(day=1), hoje)
    if periodo == "mes_passado":
        start, end = _mes_passado(hoje)
        return PeriodoVendas("mes_passado", "Mes passado", start, end)
    if periodo == "este_ano":
        return PeriodoVendas("este_ano", "Este ano", hoje.replace(month=1, day=1), hoje)
    if periodo == "todas":
        return PeriodoVendas("todas", "Todo periodo", all_data=True)

    inicio_date = parse_date(inicio) if inicio else None
    fim_date = parse_date(fim) if fim else None

    if inicio_date and not fim_date:
        fim_date = inicio_date
    elif fim_date and not inicio_date:
        inicio_date = fim_date
    elif not inicio_date and not fim_date:
        inicio_date = fim_date = hoje

    if inicio_date > fim_date:
        inicio_date, fim_date = fim_date, inicio_date

    return PeriodoVendas("personalizado", "Periodo personalizado", inicio_date, fim_date)


def aplicar_filtro_periodo_vendas(queryset, params):
    inicio = params.get("inicio")
    fim = params.get("fim")
    periodo = params.get("periodo")

    if not inicio and not fim and not periodo:
        periodo = "hoje"

    periodo_resolvido = resolver_periodo_vendas(params)
    if not periodo_resolvido.all_data:
        ini, fim_dt = inicio_fim_dia(periodo_resolvido.start)
        if periodo_resolvido.start != periodo_resolvido.end:
            fim_dt = timezone.make_aware(datetime.combine(periodo_resolvido.end, datetime.max.time()))
        queryset = queryset.filter(data_criacao__range=(ini, fim_dt))

    return queryset, inicio, fim, periodo


def metricas_vendas(user, periodo):
    rows = _vendas_agregadas(user, periodo, somente_entregues=True)
    total_vendas = sum((row["total"] for row in rows), ZERO)
    total_bruto = sum((row["gross"] for row in rows), ZERO)
    total_descontos = sum((row["discount"] for row in rows), ZERO)
    custo_mercadoria = sum((row["cost"] for row in rows), ZERO)
    taxas_maquininha_absorvidas = sum((row["absorbed_card_fee"] for row in rows), ZERO)
    lucro_total = sum((row["profit"] for row in rows), ZERO)
    qtd_vendas = len(rows)
    quantidade_total_itens = sum((row["quantity"] for row in rows), 0)
    clientes_atendidos = len({row["client_id"] for row in rows if row["client_id"]})
    ticket_medio = total_vendas / qtd_vendas if qtd_vendas else ZERO
    margem = (lucro_total / total_vendas * Decimal("100")) if total_vendas > ZERO else ZERO
    total_a_receber = sum((row["receivable"] for row in rows), ZERO)
    status_counts = _status_counts(user, periodo)

    return {
        "total_vendas": money(total_vendas),
        "total_sem_desconto": money(total_bruto),
        "lucro_total": money(lucro_total),
        "qtd_vendas": qtd_vendas,
        "qtd_vendas_periodo": sum(status_counts.values()),
        "qtd_vendas_canceladas": status_counts.get(Vendas.CANCELADA, 0),
        "qtd_vendas_troca_garantia": status_counts.get(Vendas.TROCA, 0) + status_counts.get(Vendas.RETORNO_GARANTIA, 0),
        "total_descontos": money(total_descontos),
        "custo_mercadoria_vendida": money(custo_mercadoria),
        "cmv": money(custo_mercadoria),
        "taxas_maquininha_absorvidas": money(taxas_maquininha_absorvidas),
        "margem_lucro_total_vendas": money(margem),
        "ticket_medio_vendas": money(ticket_medio),
        "quantidade_total_itens_vendidos": quantidade_total_itens,
        "quantidade_total_clientes_atendidos": clientes_atendidos,
        "total_vendas_a_receber": money(total_a_receber),
    }


def build_vendas_dashboard(user, params):
    periodo = resolver_periodo_vendas(params)
    metricas = metricas_vendas(user, periodo)
    revenue_chart = receita_vendas_por_periodo(user, periodo)
    product_ranking = ranking_produtos_vendas(user, periodo)
    chart_height = max(320, min(720, 42 * max(len(product_ranking), 1)))
    inicio = params.get("inicio") or params.get("data_inicio") or ""
    fim = params.get("fim") or params.get("data_fim") or ""

    return {
        **metricas,
        "inicio": inicio,
        "fim": fim,
        "periodo": periodo.key,
        "periodo_vendas": periodo,
        "vendas_revenue_has_data": any(value > 0 for value in revenue_chart["values"]),
        "vendas_product_has_data": bool(product_ranking),
        "vendas_product_ranking": product_ranking,
        "vendas_product_chart_height": chart_height,
        "vendas_charts": {
            "revenue": revenue_chart,
            "products": {
                "labels": [item["product"] for item in product_ranking],
                "revenues": [decimal_to_float(item["revenue"]) for item in product_ranking],
                "quantities": [item["quantity"] for item in product_ranking],
            },
        },
    }


def receita_vendas_por_periodo(user, periodo):
    periodo = _normalizar_periodo_total(user, periodo)
    if periodo.all_data and not periodo.start:
        return {"labels": [], "values": [], "grouping": "empty"}

    rows = _vendas_agregadas(user, periodo, somente_entregues=True)

    if periodo.days == 1:
        totals = {hour: ZERO for hour in range(24)}
        for row in rows:
            hour = timezone.localtime(row["date"]).hour
            totals[hour] = totals.get(hour, ZERO) + row["total"]
        return {
            "labels": [f"{hour:02d}:00" for hour in range(24)],
            "values": [decimal_to_float(totals.get(hour, ZERO)) for hour in range(24)],
            "grouping": "hour",
        }

    if periodo.days > 120:
        buckets = _month_buckets(periodo.start, periodo.end)
        totals = {bucket: ZERO for bucket in buckets}
        for row in rows:
            bucket = timezone.localtime(row["date"]).date().replace(day=1)
            totals[bucket] = totals.get(bucket, ZERO) + row["total"]
        return {
            "labels": [bucket.strftime("%m/%Y") for bucket in buckets],
            "values": [decimal_to_float(totals.get(bucket, ZERO)) for bucket in buckets],
            "grouping": "month",
        }

    buckets = _day_buckets(periodo.start, periodo.end)
    totals = {bucket: ZERO for bucket in buckets}
    for row in rows:
        bucket = timezone.localtime(row["date"]).date()
        totals[bucket] = totals.get(bucket, ZERO) + row["total"]
    return {
        "labels": [bucket.strftime("%d/%m") for bucket in buckets],
        "values": [decimal_to_float(totals.get(bucket, ZERO)) for bucket in buckets],
        "grouping": "day",
    }


def ranking_produtos_vendas(user, periodo, limit=12):
    gross_expression = _item_total_expression()
    queryset = _items_venda_periodo(user, periodo).filter(vendas__status=Vendas.ENTREGUE)
    rows = (
        queryset
        .values("produto_id", "produto__nome_produto")
        .annotate(
            quantity=Sum("quantidade"),
            revenue=Sum(gross_expression),
            transactions=Count("vendas_id", distinct=True),
        )
        .order_by("-revenue", "produto__nome_produto")[:limit]
    )

    return [
        {
            "product": row["produto__nome_produto"] or "Produto sem nome",
            "quantity": row["quantity"] or 0,
            "revenue": money(row["revenue"]),
            "transactions": row["transactions"] or 0,
        }
        for row in rows
    ]


def _vendas_agregadas(user, periodo, somente_entregues=False):
    gross_expression = _item_total_expression()
    cost_expression = ExpressionWrapper(
        F("produto__preco_de_custo") * F("quantidade"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    queryset = _items_venda_periodo(user, periodo)
    if somente_entregues:
        queryset = queryset.filter(vendas__status=Vendas.ENTREGUE)

    rows = (
        queryset
        .values(
            "vendas_id",
            "vendas__data_criacao",
            "vendas__cliente_id",
            "vendas__status",
            "vendas__forma_pagamento",
            "vendas__valor_entrada",
            "vendas__desconto",
            "vendas__card_payment_type",
            "vendas__card_fee_amount",
            "vendas__pass_card_fee_to_customer",
            "vendas__card_final_amount",
        )
        .annotate(
            gross=Sum(gross_expression),
            cost=Sum(cost_expression),
            quantity=Sum("quantidade"),
        )
    )

    return [_normalizar_venda_agregada(row) for row in rows]


def _normalizar_venda_agregada(row):
    gross = money(row["gross"])
    discount = money(row["vendas__desconto"])
    card_final_amount = row["vendas__card_final_amount"]
    total = money(card_final_amount) if card_final_amount is not None else max(gross - discount, ZERO)
    cost = money(row["cost"])
    absorbed_card_fee = (
        money(row["vendas__card_fee_amount"])
        if row["vendas__card_payment_type"] and not row["vendas__pass_card_fee_to_customer"]
        else ZERO
    )
    receivable = ZERO
    if row["vendas__forma_pagamento"] == Vendas.FIADO:
        receivable = max(total - money(row["vendas__valor_entrada"]), ZERO)

    return {
        "id": row["vendas_id"],
        "date": row["vendas__data_criacao"],
        "client_id": row["vendas__cliente_id"],
        "status": row["vendas__status"],
        "gross": gross,
        "discount": discount,
        "total": total,
        "cost": cost,
        "absorbed_card_fee": absorbed_card_fee,
        "profit": total - cost - absorbed_card_fee,
        "quantity": row["quantity"] or 0,
        "receivable": receivable,
    }


def _items_venda_periodo(user, periodo):
    queryset = ItemsVenda.objects.filter(vendas__usuario=user)
    if periodo.all_data:
        return queryset
    return queryset.filter(vendas__data_criacao__date__range=(periodo.start, periodo.end))


def _status_counts(user, periodo):
    queryset = Vendas.objects.filter(usuario=user)
    if not periodo.all_data:
        queryset = queryset.filter(data_criacao__date__range=(periodo.start, periodo.end))
    return {
        row["status"]: row["count"]
        for row in queryset.values("status").annotate(count=Count("id"))
    }


def _normalizar_periodo_total(user, periodo):
    if not periodo.all_data:
        return periodo

    bounds = Vendas.objects.filter(usuario=user).aggregate(
        start=Min("data_criacao"),
        end=Max("data_criacao"),
    )
    if not bounds["start"] or not bounds["end"]:
        return PeriodoVendas("todas", "Todo periodo", all_data=True)
    return PeriodoVendas(
        "todas",
        "Todo periodo",
        timezone.localtime(bounds["start"]).date(),
        timezone.localtime(bounds["end"]).date(),
    )


def _item_total_expression():
    return ExpressionWrapper(
        F("preco") * F("quantidade"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )


def _day_buckets(start, end):
    buckets = []
    current = start
    while current <= end:
        buckets.append(current)
        current += timedelta(days=1)
    return buckets


def _month_buckets(start, end):
    buckets = []
    current = start.replace(day=1)
    end_month = end.replace(day=1)
    while current <= end_month:
        buckets.append(current)
        current = _next_month(current)
    return buckets


def _next_month(day):
    if day.month == 12:
        return day.replace(year=day.year + 1, month=1)
    return day.replace(month=day.month + 1)
