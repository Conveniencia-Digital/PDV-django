from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Max, Min, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone

from despesa.models import Despesa
from financeiro.models import LancamentoFinanceiro
from lanhouse.models import ItemsLanhouse, LanhouseModel
from orcamento.models import ItemsOrcamento, Orcamento
from peca.models import Pecas
from produto.models import Produto
from venda.models import ItemsVenda, Vendas


ZERO = Decimal("0.00")
FIADO_RECEBER = "Fiado a receber"
FIADO_PAGAR = "Fiado a pagar"
CASH_OVER_CATEGORY = "Sobra de Caixa"
CASH_SHORTAGE_CATEGORY = "Falta de Caixa"


@dataclass(frozen=True)
class Period:
    key: str
    label: str
    start: date
    end: date

    @property
    def days(self):
        return max((self.end - self.start).days + 1, 1)

    def previous(self):
        previous_end = self.start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=self.days - 1)
        return Period("previous", "Periodo anterior", previous_start, previous_end)


def money(value):
    return Decimal(value or ZERO).quantize(Decimal("0.01"))


def decimal_to_float(value):
    return float(money(value))


def growth_percent(current, previous):
    current = money(current)
    previous = money(previous)
    if previous == ZERO:
        return Decimal("100.00") if current > ZERO else ZERO
    return ((current - previous) / abs(previous) * Decimal("100")).quantize(Decimal("0.01"))


def resolve_period(params):
    today = timezone.localdate()
    start_param = params.get("inicio") or params.get("data_inicio")
    end_param = params.get("fim") or params.get("data_fim")
    key = _period_alias(params.get("periodo"))

    ranges = {
        "hoje": ("Hoje", today, today),
        "ontem": ("Ontem", today - timedelta(days=1), today - timedelta(days=1)),
        "7dias": ("Ultimos 7 dias", today - timedelta(days=6), today),
        "este_mes": ("Mes atual", today.replace(day=1), today),
        "mes_passado": _previous_month(today),
        "este_ano": ("Ano atual", today.replace(month=1, day=1), today),
        "todas": ("Todo periodo", today, today),
    }

    if not start_param and not end_param and not key:
        key = "hoje"

    if key == "personalizado" or (not key and (start_param or end_param)):
        start = _parse_date(start_param) or _parse_date(end_param) or today
        end = _parse_date(end_param) or start
        if start > end:
            start, end = end, start
        return Period("personalizado", "Periodo personalizado", start, end)

    label, start, end = ranges.get(key, ranges["hoje"])
    return Period(key, label, start, end)


def available_periods():
    return [
        ("hoje", "Hoje"),
        ("ontem", "Ontem"),
        ("7dias", "7 dias"),
        ("este_mes", "Este mes"),
        ("mes_passado", "Mes passado"),
        ("este_ano", "Este ano"),
        ("todas", "Todas"),
    ]


def build_financial_dashboard(user, params):
    period = _normalize_all_data_period(user, resolve_period(params))
    previous_period = period.previous()
    metrics_cache = {}

    def metrics_for(target_period):
        cache_key = (target_period.start, target_period.end)
        if cache_key not in metrics_cache:
            metrics_cache[cache_key] = _period_metrics(user, target_period)
        return metrics_cache[cache_key]

    selected = metrics_for(period)
    previous = metrics_for(previous_period)
    today = metrics_for(resolve_period({"periodo": "hoje"}))
    month = metrics_for(resolve_period({"periodo": "este_mes"}))
    year = metrics_for(resolve_period({"periodo": "este_ano"}))
    yesterday = metrics_for(resolve_period({"periodo": "ontem"}))
    last_7_days = metrics_for(resolve_period({"periodo": "7dias"}))
    previous_month = metrics_for(resolve_period({"periodo": "mes_passado"}))

    balance = selected["revenue"] - selected["expenses"]
    previous_balance = previous["revenue"] - previous["expenses"]
    profit = balance

    category_ranking = _expense_category_ranking(user, period)
    revenue_composition = _revenue_composition(user, period)
    revenue_expense_chart = _revenue_vs_expense_chart(user, period)
    profit_trend = _profit_trend(user, period)
    monthly_profit_trend = _monthly_profit_trend(user)

    return {
        "period": period,
        "periods": available_periods(),
        "filters": {
            "periodo": period.key,
            "inicio": params.get("inicio") or params.get("data_inicio") or "",
            "fim": params.get("fim") or params.get("data_fim") or "",
            "data_inicio": params.get("inicio") or params.get("data_inicio") or "",
            "data_fim": params.get("fim") or params.get("data_fim") or "",
        },
        "cards": [
            _card("Saldo de caixa", balance, previous_balance, "activity", "primary"),
            _card("Receita de hoje", today["revenue"], None, "trending-up", "success"),
            _card("Despesas de hoje", today["expenses"], None, "trending-down", "danger"),
            _card("Resultado de hoje", today["profit"], yesterday["profit"], "dollar-sign", _tone(today["profit"])),
            _card("Receita mensal", month["revenue"], previous_month["revenue"], "bar-chart-2", "success"),
            _card("Despesas mensais", month["expenses"], previous_month["expenses"], "layers", "danger"),
            _card("Resultado mensal", month["profit"], previous_month["profit"], "line-chart", _tone(month["profit"])),
            _card("Media diaria de receita", selected["revenue"] / period.days, None, "calendar", "info"),
            _card("Media diaria de despesas", selected["expenses"] / period.days, None, "calendar", "warning"),
        ],
        "summary": {
            "selected": selected,
            "today": today,
            "yesterday": yesterday,
            "last_7_days": last_7_days,
            "month": month,
            "previous_month": previous_month,
            "year": year,
            "balance": balance,
            "profit": profit,
            "growth": growth_percent(balance, previous_balance),
        },
        "category_ranking": category_ranking,
        "revenue_composition": revenue_composition,
        "charts": {
            "expense_ranking": {
                "labels": [item["category"] for item in category_ranking],
                "values": [decimal_to_float(item["amount"]) for item in category_ranking],
            },
            "revenue_vs_expenses": revenue_expense_chart,
            "profit_trend": profit_trend,
            "monthly_profit_trend": monthly_profit_trend,
            "revenue_composition": {
                "labels": [item["source"] for item in revenue_composition],
                "values": [decimal_to_float(item["amount"]) for item in revenue_composition],
            },
        },
        "indicators": _operational_indicators(selected, category_ranking, revenue_composition),
    }


def get_financial_period_metrics(user, period, include_cash_adjustments=True):
    return _period_metrics(user, period, include_cash_adjustments=include_cash_adjustments)


def _period_metrics(user, period, include_cash_adjustments=True):
    revenue_rows = _revenue_rows(user, period, include_cash_adjustments=include_cash_adjustments)
    expense_rows = _expense_rows(user, period, include_cash_adjustments=include_cash_adjustments)

    revenue = sum((row["amount"] for row in revenue_rows), ZERO)
    expenses = sum((row["amount"] for row in expense_rows), ZERO)
    revenue_count = sum(row.get("count", 1) for row in revenue_rows)
    expense_count = sum(row.get("count", 1) for row in expense_rows)

    return {
        "revenue": money(revenue),
        "expenses": money(expenses),
        "profit": money(revenue - expenses),
        "revenue_count": revenue_count,
        "expense_count": expense_count,
    }


def _revenue_rows(user, period, include_cash_adjustments=True):
    rows = []
    rows.extend(_line_item_revenue_rows(
        ItemsVenda.objects.filter(
            vendas__usuario=user,
            vendas__status=Vendas.ENTREGUE,
            vendas__data_criacao__date__range=(period.start, period.end),
        ),
        parent="vendas",
        source="Vendas",
        price_field="preco",
        final_amount_field="card_final_amount",
    ))
    rows.extend(_line_item_revenue_rows(
        ItemsLanhouse.objects.filter(
            lanhouse__usuario=user,
            lanhouse__data_criacao__date__range=(period.start, period.end),
        ),
        parent="lanhouse",
        source="Lan House",
        price_field="preco",
        final_amount_field="card_final_amount",
    ))
    rows.extend(_line_item_revenue_rows(
        ItemsOrcamento.objects.filter(
            orcamento__usuario=user,
            orcamento__status__in=[
                Orcamento.FINALIZADO,
                Orcamento.FINALIZADO_ENTREGUE,
                Orcamento.GARANTIA_ENCERRADA,
            ],
            orcamento__data_criacao__date__range=(period.start, period.end),
        ),
        parent="orcamento",
        source="Orcamentos",
        price_field="preco_orcamento",
        final_amount_field="card_final_amount",
    ))
    rows.extend(_financial_entry_rows(
        user,
        period,
        LancamentoFinanceiro.RECEITA,
        include_cash_adjustments=include_cash_adjustments,
    ))
    return rows


def _line_item_revenue_rows(queryset, parent, source, price_field, final_amount_field=None):
    gross_expression = ExpressionWrapper(
        F(price_field) * F("quantidade"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    values = [
        f"{parent}_id",
        f"{parent}__forma_pagamento",
        f"{parent}__valor_entrada",
        f"{parent}__desconto",
        f"{parent}__data_criacao",
    ]
    if final_amount_field:
        values.append(f"{parent}__{final_amount_field}")

    grouped = queryset.values(*values).annotate(gross=Sum(gross_expression))

    rows = []
    for item in grouped:
        gross = money(item["gross"])
        discount = money(item[f"{parent}__desconto"])
        final_amount = item.get(f"{parent}__{final_amount_field}") if final_amount_field else None
        total = money(final_amount) if final_amount is not None else max(gross - discount, ZERO)
        amount = _cash_impact(total, item[f"{parent}__forma_pagamento"], item[f"{parent}__valor_entrada"], FIADO_RECEBER)
        if amount > ZERO:
            rows.append({"source": source, "amount": amount, "count": 1})
    return rows


def _expense_rows(user, period, include_cash_adjustments=True):
    rows = []
    despesas = Despesa.objects.filter(
        usuario=user,
        data_cadastro__date__range=(period.start, period.end),
    ).select_related("categoria_despesa")
    if not include_cash_adjustments:
        despesas = despesas.exclude(categoria_despesa__nome_categoria_despesa=CASH_SHORTAGE_CATEGORY)

    for despesa in despesas:
        amount = _expense_cash_impact(
            despesa.preco_despesa,
            despesa.forma_pagamento,
            despesa.valor_entrada,
            despesa.tipo,
            despesa.fiado_pago,
        )
        if amount > ZERO:
            rows.append({
                "category": despesa.categoria_despesa.nome_categoria_despesa if despesa.categoria_despesa else "Outras",
                "amount": amount,
                "count": 1,
            })

    rows.extend(_financial_entry_rows(
        user,
        period,
        LancamentoFinanceiro.DESPESA,
        include_cash_adjustments=include_cash_adjustments,
    ))

    produtos = Produto.objects.filter(usuario=user, data_criacao__date__range=(period.start, period.end))
    rows.extend(_inventory_expense_rows(
        produtos,
        price_field="preco_de_custo",
    ))
    rows.extend(_zero_margin_product_expense_rows(produtos))
    rows.extend(_inventory_expense_rows(
        Pecas.objects.filter(usuario=user, data_criacao__date__range=(period.start, period.end)),
        price_field="preco_de_custo",
    ))
    return rows


def _financial_entry_rows(user, period, entry_type, include_cash_adjustments=True):
    queryset = (
        LancamentoFinanceiro.objects
        .filter(
            usuario=user,
            tipo=entry_type,
            data_lancamento__range=(period.start, period.end),
        )
        .select_related("categoria")
    )
    if not include_cash_adjustments:
        queryset = queryset.exclude(categoria__nome__in=[CASH_OVER_CATEGORY, CASH_SHORTAGE_CATEGORY])

    rows = []
    for entry in queryset:
        amount = money(entry.valor)
        if amount <= ZERO:
            continue
        if entry_type == LancamentoFinanceiro.RECEITA:
            rows.append({"source": entry.categoria.nome, "amount": amount, "count": 1})
        else:
            rows.append({"category": entry.categoria.nome, "amount": amount, "count": 1})
    return rows


def _inventory_expense_rows(queryset, price_field):
    gross_expression = ExpressionWrapper(
        F(price_field) * F("quantidade"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    grouped = queryset.values("id", "forma_pagamento", "valor_entrada").annotate(gross=Sum(gross_expression))

    rows = []
    for item in grouped:
        amount = _cash_impact(item["gross"], item["forma_pagamento"], item["valor_entrada"], FIADO_PAGAR)
        if amount > ZERO:
            rows.append({"category": "Estoque", "amount": amount, "count": 1})
    return rows


def _zero_margin_product_expense_rows(queryset):
    sold_out_products = list(
        queryset
        .filter(quantidade__lte=0, preco_de_custo=F("preco"), preco_de_custo__gt=ZERO)
        .values("id", "preco_de_custo", "forma_pagamento", "valor_entrada")
    )
    if not sold_out_products:
        return []

    product_ids = [item["id"] for item in sold_out_products]
    sold_quantities = {
        item["produto_id"]: item["total"] or 0
        for item in (
            ItemsVenda.objects
            .filter(produto_id__in=product_ids, vendas__status=Vendas.ENTREGUE)
            .values("produto_id")
            .annotate(total=Sum("quantidade"))
        )
    }

    rows = []
    for item in sold_out_products:
        quantity = sold_quantities.get(item["id"], 0)
        gross = money(item["preco_de_custo"]) * Decimal(max(quantity, 0))
        amount = _cash_impact(gross, item["forma_pagamento"], item["valor_entrada"], FIADO_PAGAR)
        if amount > ZERO:
            rows.append({"category": "Estoque", "amount": amount, "count": 1})
    return rows


def _cash_impact(total, payment_method, entry_value, credit_label):
    total = money(total)
    if payment_method == credit_label:
        return min(money(entry_value), total)
    return total


def _expense_cash_impact(total, payment_method, entry_value, expense_type, paid):
    total = money(total)
    entry = min(money(entry_value), total)

    if expense_type == Despesa.TIPO_DIVIDA and not paid:
        return ZERO
    if expense_type == Despesa.TIPO_DIVIDA:
        return total
    if payment_method == FIADO_PAGAR:
        return total if paid else entry
    return total


def _expense_category_ranking(user, period):
    rows = _expense_rows(user, period)
    totals = {}
    total_amount = ZERO
    for row in rows:
        category = row["category"] or "Outras"
        amount = money(row["amount"])
        totals[category] = totals.get(category, ZERO) + amount
        total_amount += amount

    ranking = []
    for category, amount in sorted(totals.items(), key=lambda item: item[1], reverse=True):
        participation = ZERO if total_amount == ZERO else (amount / total_amount * Decimal("100")).quantize(Decimal("0.01"))
        ranking.append({"category": category, "amount": money(amount), "percentage": participation})
    return ranking


def _revenue_composition(user, period):
    rows = _revenue_rows(user, period)
    totals = {}
    total_amount = ZERO
    for row in rows:
        source = row["source"]
        amount = money(row["amount"])
        totals[source] = totals.get(source, ZERO) + amount
        total_amount += amount

    composition = []
    for source, amount in sorted(totals.items(), key=lambda item: item[1], reverse=True):
        participation = ZERO if total_amount == ZERO else (amount / total_amount * Decimal("100")).quantize(Decimal("0.01"))
        composition.append({"source": source, "amount": money(amount), "percentage": participation})
    return composition


def _revenue_vs_expense_chart(user, period):
    revenue = _daily_totals(_revenue_daily_rows(user, period))
    expenses = _daily_totals(_expense_daily_rows(user, period))

    if period.days > 120:
        buckets = _month_buckets(period.start, period.end)
        label_for = lambda day: day.replace(day=1)
        format_label = lambda day: day.strftime("%m/%Y")
    elif period.days > 31:
        buckets = _week_buckets(period.start, period.end)
        label_for = _week_start
        format_label = lambda day: day.strftime("%d/%m")
    else:
        buckets = _day_buckets(period.start, period.end)
        label_for = lambda day: day
        format_label = lambda day: day.strftime("%d/%m")

    revenue_totals = {bucket: ZERO for bucket in buckets}
    expense_totals = {bucket: ZERO for bucket in buckets}
    for day, amount in revenue.items():
        revenue_totals[label_for(day)] = revenue_totals.get(label_for(day), ZERO) + amount
    for day, amount in expenses.items():
        expense_totals[label_for(day)] = expense_totals.get(label_for(day), ZERO) + amount

    return {
        "labels": [format_label(bucket) for bucket in buckets],
        "revenue": [decimal_to_float(revenue_totals.get(bucket, ZERO)) for bucket in buckets],
        "expenses": [decimal_to_float(expense_totals.get(bucket, ZERO)) for bucket in buckets],
    }


def _profit_trend(user, period):
    revenue = _daily_totals(_revenue_daily_rows(user, period))
    expenses = _daily_totals(_expense_daily_rows(user, period))
    days = _day_buckets(period.start, period.end)
    return {
        "labels": [day.strftime("%d/%m") for day in days],
        "values": [decimal_to_float(revenue.get(day, ZERO) - expenses.get(day, ZERO)) for day in days],
    }


def _monthly_profit_trend(user):
    today = timezone.localdate()
    start = (today.replace(day=1) - timedelta(days=365)).replace(day=1)
    period = Period("last_12_months", "Ultimos 12 meses", start, today)
    revenue = _monthly_totals(_revenue_monthly_rows(user, period))
    expenses = _monthly_totals(_expense_monthly_rows(user, period))
    months = _month_buckets(start, today)
    return {
        "labels": [month.strftime("%m/%Y") for month in months],
        "values": [decimal_to_float(revenue.get(month, ZERO) - expenses.get(month, ZERO)) for month in months],
    }


def _revenue_daily_rows(user, period):
    return _revenue_time_rows(user, period, TruncDate)


def _revenue_monthly_rows(user, period):
    return _revenue_time_rows(user, period, TruncMonth)


def _revenue_time_rows(user, period, trunc_function):
    rows = []
    rows.extend(_line_item_time_rows(
        ItemsVenda.objects.filter(vendas__usuario=user, vendas__status=Vendas.ENTREGUE, vendas__data_criacao__date__range=(period.start, period.end)),
        parent="vendas",
        price_field="preco",
        trunc_function=trunc_function,
        final_amount_field="card_final_amount",
    ))
    rows.extend(_line_item_time_rows(
        ItemsLanhouse.objects.filter(lanhouse__usuario=user, lanhouse__data_criacao__date__range=(period.start, period.end)),
        parent="lanhouse",
        price_field="preco",
        trunc_function=trunc_function,
        final_amount_field="card_final_amount",
    ))
    rows.extend(_line_item_time_rows(
        ItemsOrcamento.objects.filter(
            orcamento__usuario=user,
            orcamento__status__in=[Orcamento.FINALIZADO, Orcamento.FINALIZADO_ENTREGUE, Orcamento.GARANTIA_ENCERRADA],
            orcamento__data_criacao__date__range=(period.start, period.end),
        ),
        parent="orcamento",
        price_field="preco_orcamento",
        trunc_function=trunc_function,
        final_amount_field="card_final_amount",
    ))
    rows.extend(_financial_entry_time_rows(user, period, LancamentoFinanceiro.RECEITA, trunc_function))
    return rows


def _line_item_time_rows(queryset, parent, price_field, trunc_function, final_amount_field=None):
    gross_expression = ExpressionWrapper(
        F(price_field) * F("quantidade"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    values = [
        "period",
        f"{parent}_id",
        f"{parent}__forma_pagamento",
        f"{parent}__valor_entrada",
        f"{parent}__desconto",
    ]
    if final_amount_field:
        values.append(f"{parent}__{final_amount_field}")

    grouped = queryset.annotate(period=trunc_function(f"{parent}__data_criacao")).values(*values).annotate(gross=Sum(gross_expression))

    rows = []
    for item in grouped:
        gross = money(item["gross"])
        discount = money(item[f"{parent}__desconto"])
        final_amount = item.get(f"{parent}__{final_amount_field}") if final_amount_field else None
        total = money(final_amount) if final_amount is not None else max(gross - discount, ZERO)
        amount = _cash_impact(total, item[f"{parent}__forma_pagamento"], item[f"{parent}__valor_entrada"], FIADO_RECEBER)
        rows.append({"period": _as_date(item["period"]), "amount": amount})
    return rows


def _expense_daily_rows(user, period):
    return _expense_time_rows(user, period, TruncDate)


def _expense_monthly_rows(user, period):
    return _expense_time_rows(user, period, TruncMonth)


def _expense_time_rows(user, period, trunc_function):
    rows = []
    grouped_expenses = Despesa.objects.filter(
        usuario=user,
        data_cadastro__date__range=(period.start, period.end),
    ).annotate(period=trunc_function("data_cadastro")).values(
        "id",
        "period",
        "forma_pagamento",
        "valor_entrada",
        "tipo",
        "fiado_pago",
    ).annotate(total=Sum("preco_despesa"))

    for item in grouped_expenses:
        rows.append({
            "period": _as_date(item["period"]),
            "amount": _expense_cash_impact(
                item["total"],
                item["forma_pagamento"],
                item["valor_entrada"],
                item["tipo"],
                item["fiado_pago"],
            ),
        })

    produtos = Produto.objects.filter(usuario=user, data_criacao__date__range=(period.start, period.end))
    rows.extend(_inventory_time_rows(
        produtos,
        price_field="preco_de_custo",
        trunc_function=trunc_function,
    ))
    rows.extend(_zero_margin_product_time_rows(produtos, trunc_function))
    rows.extend(_inventory_time_rows(
        Pecas.objects.filter(usuario=user, data_criacao__date__range=(period.start, period.end)),
        price_field="preco_de_custo",
        trunc_function=trunc_function,
    ))
    rows.extend(_financial_entry_time_rows(user, period, LancamentoFinanceiro.DESPESA, trunc_function))
    return rows


def _financial_entry_time_rows(user, period, entry_type, trunc_function):
    grouped = (
        LancamentoFinanceiro.objects
        .filter(
            usuario=user,
            tipo=entry_type,
            data_lancamento__range=(period.start, period.end),
        )
        .values("data_lancamento")
        .annotate(amount=Sum("valor"))
    )
    rows = []
    for item in grouped:
        period_value = item["data_lancamento"]
        if trunc_function is TruncMonth:
            period_value = period_value.replace(day=1)
        rows.append({
            "period": _as_date(period_value),
            "amount": money(item["amount"]),
        })
    return rows


def _inventory_time_rows(queryset, price_field, trunc_function):
    gross_expression = ExpressionWrapper(
        F(price_field) * F("quantidade"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    grouped = queryset.annotate(period=trunc_function("data_criacao")).values(
        "id",
        "period",
        "forma_pagamento",
        "valor_entrada",
    ).annotate(gross=Sum(gross_expression))
    return [
        {
            "period": _as_date(item["period"]),
            "amount": _cash_impact(item["gross"], item["forma_pagamento"], item["valor_entrada"], FIADO_PAGAR),
        }
        for item in grouped
    ]


def _zero_margin_product_time_rows(queryset, trunc_function):
    sold_out_products = list(
        queryset
        .filter(quantidade__lte=0, preco_de_custo=F("preco"), preco_de_custo__gt=ZERO)
        .annotate(period=trunc_function("data_criacao"))
        .values("id", "period", "preco_de_custo", "forma_pagamento", "valor_entrada")
    )
    if not sold_out_products:
        return []

    product_ids = [item["id"] for item in sold_out_products]
    sold_quantities = {
        item["produto_id"]: item["total"] or 0
        for item in (
            ItemsVenda.objects
            .filter(produto_id__in=product_ids, vendas__status=Vendas.ENTREGUE)
            .values("produto_id")
            .annotate(total=Sum("quantidade"))
        )
    }

    rows = []
    for item in sold_out_products:
        quantity = sold_quantities.get(item["id"], 0)
        gross = money(item["preco_de_custo"]) * Decimal(max(quantity, 0))
        amount = _cash_impact(gross, item["forma_pagamento"], item["valor_entrada"], FIADO_PAGAR)
        if amount > ZERO:
            rows.append({
                "period": _as_date(item["period"]),
                "amount": amount,
            })
    return rows


def _daily_totals(rows):
    totals = {}
    for row in rows:
        totals[row["period"]] = totals.get(row["period"], ZERO) + money(row["amount"])
    return totals


def _monthly_totals(rows):
    totals = {}
    for row in rows:
        period = row["period"].replace(day=1)
        totals[period] = totals.get(period, ZERO) + money(row["amount"])
    return totals


def _operational_indicators(selected, category_ranking, revenue_composition):
    revenue_count = selected["revenue_count"]
    expense_count = selected["expense_count"]
    return {
        "revenue_count": revenue_count,
        "expense_count": expense_count,
        "average_ticket": ZERO if revenue_count == 0 else money(selected["revenue"] / revenue_count),
        "average_expense": ZERO if expense_count == 0 else money(selected["expenses"] / expense_count),
        "top_expense_category": category_ranking[0]["category"] if category_ranking else "Sem despesas",
        "top_revenue_source": revenue_composition[0]["source"] if revenue_composition else "Sem receitas",
    }


def _card(title, value, previous_value, icon, tone):
    change = money(value) - money(previous_value) if previous_value is not None else None
    return {
        "title": title,
        "value": money(value),
        "previous": money(previous_value) if previous_value is not None else None,
        "change": change,
        "growth": growth_percent(value, previous_value) if previous_value is not None else None,
        "icon": icon,
        "tone": tone,
    }


def _tone(value):
    return "success" if money(value) >= ZERO else "danger"


def _parse_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _period_alias(key):
    aliases = {
        "today": "hoje",
        "yesterday": "ontem",
        "last_7_days": "7dias",
        "current_month": "este_mes",
        "previous_month": "mes_passado",
        "current_year": "este_ano",
        "custom": "personalizado",
    }
    return aliases.get(key, key)


def _previous_month(today):
    first_day_current = today.replace(day=1)
    last_day_previous = first_day_current - timedelta(days=1)
    return "Mes anterior", last_day_previous.replace(day=1), last_day_previous


def _normalize_all_data_period(user, period):
    if period.key != "todas":
        return period

    dates = []
    for start, end in (
        _date_bounds(Vendas.objects.filter(usuario=user, status=Vendas.ENTREGUE), "data_criacao"),
        _date_bounds(LanhouseModel.objects.filter(usuario=user), "data_criacao"),
        _date_bounds(
            Orcamento.objects.filter(
                usuario=user,
                status__in=[
                    Orcamento.FINALIZADO,
                    Orcamento.FINALIZADO_ENTREGUE,
                    Orcamento.GARANTIA_ENCERRADA,
                ],
            ),
            "data_criacao",
        ),
        _date_bounds(Despesa.objects.filter(usuario=user), "data_cadastro"),
        _date_bounds(Produto.objects.filter(usuario=user), "data_criacao"),
        _date_bounds(Pecas.objects.filter(usuario=user), "data_criacao"),
        _date_bounds(LancamentoFinanceiro.objects.filter(usuario=user), "data_lancamento"),
    ):
        if start:
            dates.append(_as_date(start))
        if end:
            dates.append(_as_date(end))

    today = timezone.localdate()
    if not dates:
        return Period("todas", "Todo periodo", today, today)
    return Period("todas", "Todo periodo", min(dates), max(dates))


def _date_bounds(queryset, field_name):
    bounds = queryset.aggregate(start=Min(field_name), end=Max(field_name))
    return bounds["start"], bounds["end"]


def _day_buckets(start, end):
    buckets = []
    current = start
    while current <= end:
        buckets.append(current)
        current += timedelta(days=1)
    return buckets


def _week_buckets(start, end):
    buckets = []
    current = _week_start(start)
    while current <= end:
        buckets.append(current)
        current += timedelta(days=7)
    return buckets


def _month_buckets(start, end):
    buckets = []
    current = start.replace(day=1)
    end_month = end.replace(day=1)
    while current <= end_month:
        buckets.append(current)
        current = _next_month(current)
    return buckets


def _week_start(day):
    return day - timedelta(days=day.weekday())


def _next_month(day):
    if day.month == 12:
        return day.replace(year=day.year + 1, month=1)
    return day.replace(month=day.month + 1)


def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return value.date()
