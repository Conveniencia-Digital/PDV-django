from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Max, Min, Sum
from django.db.models.functions import TruncDate, TruncHour, TruncMonth

from django.utils import timezone
from django.utils.dateparse import parse_date

from financeiro.services import decimal_to_float, money
from orcamento.models import ItemsOrcamento, Orcamento


ZERO = Decimal("0.00")
STATUS_RECEITA = {
    Orcamento.FINALIZADO,
    Orcamento.FINALIZADO_ENTREGUE,
    Orcamento.GARANTIA_ENCERRADA,
}
STATUS_CANCELADO = {
    Orcamento.CANCELADO,
    Orcamento.CANCELADO_ENTREGUE,
}


@dataclass(frozen=True)
class PeriodoOrcamento:
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


def resolver_periodo_orcamento(params):
    inicio = params.get('inicio') or params.get('data_inicio')
    fim = params.get('fim') or params.get('data_fim')
    periodo = params.get('periodo')
    hoje = timezone.localdate()

    aliases = {
        'today': 'hoje',
        'yesterday': 'ontem',
        'last_7_days': '7dias',
        'current_month': 'este_mes',
        'previous_month': 'mes_passado',
        'current_year': 'este_ano',
    }
    periodo = aliases.get(periodo, periodo)

    if not inicio and not fim and not periodo:
        periodo = 'hoje'

    if periodo == 'hoje':
        return PeriodoOrcamento('hoje', 'Hoje', hoje, hoje)
    if periodo == 'ontem':
        data = hoje - timedelta(days=1)
        return PeriodoOrcamento('ontem', 'Ontem', data, data)
    if periodo == '7dias':
        return PeriodoOrcamento('7dias', 'Últimos 7 dias', hoje - timedelta(days=6), hoje)
    if periodo == 'este_mes':
        return PeriodoOrcamento('este_mes', 'Este mês', hoje.replace(day=1), hoje)
    if periodo == 'mes_passado':
        start, end = _mes_passado(hoje)
        return PeriodoOrcamento('mes_passado', 'Mês passado', start, end)
    if periodo == 'este_ano':
        return PeriodoOrcamento('este_ano', 'Este ano', hoje.replace(month=1, day=1), hoje)
    if periodo == 'todas':
        return PeriodoOrcamento('todas', 'Todo período', all_data=True)

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

    return PeriodoOrcamento('personalizado', 'Período personalizado', inicio_date, fim_date)


def aplicar_filtro_periodo(queryset, request):
    inicio = request.GET.get('inicio')
    fim = request.GET.get('fim')
    periodo = request.GET.get('periodo')

    if not inicio and not fim and not periodo:
        periodo = 'hoje'

    periodo_resolvido = resolver_periodo_orcamento(request.GET)
    if not periodo_resolvido.all_data:
        ini, fim_dt = inicio_fim_dia(periodo_resolvido.start)
        if periodo_resolvido.start != periodo_resolvido.end:
            fim_dt = timezone.make_aware(datetime.combine(periodo_resolvido.end, datetime.max.time()))
        queryset = queryset.filter(data_criacao__range=(ini, fim_dt))

    return queryset, inicio, fim, periodo


def metricas_orcamento(queryset):
    total_orcamentos = sum(
        (Decimal(o.total() or 0) for o in queryset),
        Decimal('0.00'),
    )

    total_descontos = sum(
        (
            Decimal(o.desconto) if o.desconto else Decimal('0.00')
            for o in queryset
        ),
        Decimal('0.00'),
    )

    custo_mercadoria = sum(
        (Decimal(o.custo_total() or 0) for o in queryset),
        Decimal('0.00'),
    )

    lucro_total = sum(
        (
            Decimal(o.total() or 0)
            - Decimal(o.custo_total() or 0)
            - (Decimal(o.desconto) if o.desconto else Decimal('0.00'))
        )
        for o in queryset
    )

    qtd_orcamentos = queryset.count() if hasattr(queryset, 'count') else len(queryset)

    base_margem = total_orcamentos - total_descontos
    margem = (
        (lucro_total / base_margem) * 100
        if base_margem > 0
        else Decimal('0.00')
    )

    return {
        'total_orcamentos': total_orcamentos,
        'lucro_total': lucro_total,
        'qtd_orcamentos': qtd_orcamentos,
        'total_descontos': total_descontos.quantize(Decimal('0.01')),
        'custo_mercadoria': custo_mercadoria.quantize(Decimal('0.01')),
        'margem_lucro_orcamentos': margem.quantize(Decimal('0.01')),
    }


def build_orcamento_dashboard_charts(user, params):
    periodo = resolver_periodo_orcamento(params)
    revenue_chart = receita_orcamento_por_periodo(user, periodo)
    item_ranking = ranking_itens_orcamento(user, periodo)
    chart_height = max(320, min(720, 42 * max(len(item_ranking), 1)))

    return {
        'orcamento_chart_period': periodo,
        'orcamento_revenue_has_data': any(value > 0 for value in revenue_chart['values']),
        'orcamento_items_has_data': bool(item_ranking),
        'orcamento_item_ranking': item_ranking,
        'orcamento_items_chart_height': chart_height,
        'orcamento_charts': {
            'revenue': revenue_chart,
            'items': {
                'labels': [item['name'] for item in item_ranking],
                'revenues': [decimal_to_float(item['revenue']) for item in item_ranking],
                'quantities': [item['quantity'] for item in item_ranking],
            },
        },
    }


def receita_orcamento_por_periodo(user, periodo):
    periodo = _normalizar_periodo_total(user, periodo)
    if periodo.all_data and not periodo.start:
        return {'labels': [], 'values': [], 'grouping': 'empty'}

    if periodo.days == 1:
        rows = _receita_orcamento_agrupada(user, periodo, TruncHour)
        totals = {hour: ZERO for hour in range(24)}
        for row in rows:
            bucket = row['period']
            hour = timezone.localtime(bucket).hour if isinstance(bucket, datetime) else bucket.hour
            totals[hour] = totals.get(hour, ZERO) + money(row['amount'])
        return {
            'labels': [f'{hour:02d}:00' for hour in range(24)],
            'values': [decimal_to_float(totals.get(hour, ZERO)) for hour in range(24)],
            'grouping': 'hour',
        }

    if periodo.days > 120:
        rows = _receita_orcamento_agrupada(user, periodo, TruncMonth)
        buckets = _month_buckets(periodo.start, periodo.end)
        totals = {bucket: ZERO for bucket in buckets}
        for row in rows:
            bucket = _as_date(row['period']).replace(day=1)
            totals[bucket] = totals.get(bucket, ZERO) + money(row['amount'])
        return {
            'labels': [bucket.strftime('%m/%Y') for bucket in buckets],
            'values': [decimal_to_float(totals.get(bucket, ZERO)) for bucket in buckets],
            'grouping': 'month',
        }

    rows = _receita_orcamento_agrupada(user, periodo, TruncDate)
    buckets = _day_buckets(periodo.start, periodo.end)
    totals = {bucket: ZERO for bucket in buckets}
    for row in rows:
        bucket = _as_date(row['period'])
        totals[bucket] = totals.get(bucket, ZERO) + money(row['amount'])
    return {
        'labels': [bucket.strftime('%d/%m') for bucket in buckets],
        'values': [decimal_to_float(totals.get(bucket, ZERO)) for bucket in buckets],
        'grouping': 'day',
    }


def ranking_itens_orcamento(user, periodo, limit=12):
    gross_expression = _item_total_expression()
    queryset = _items_orcamento_periodo(user, periodo).exclude(orcamento__status__in=STATUS_CANCELADO)

    service_rows = (
        queryset
        .filter(servico__isnull=False)
        .values('servico_id', 'servico__servico')
        .annotate(
            quantity=Sum('quantidade'),
            revenue=Sum(gross_expression),
            transactions=Count('orcamento_id', distinct=True),
        )
    )
    part_rows = (
        queryset
        .filter(peca__isnull=False)
        .values('peca_id', 'peca__nome_peca')
        .annotate(
            quantity=Sum('quantidade'),
            revenue=Sum(gross_expression),
            transactions=Count('orcamento_id', distinct=True),
        )
    )

    ranking = [
        {
            'kind': 'Serviço',
            'name': row['servico__servico'] or 'Serviço sem nome',
            'quantity': row['quantity'] or 0,
            'revenue': money(row['revenue']),
            'transactions': row['transactions'],
        }
        for row in service_rows
    ]
    ranking.extend(
        {
            'kind': 'Peça',
            'name': row['peca__nome_peca'] or 'Peça sem nome',
            'quantity': row['quantity'] or 0,
            'revenue': money(row['revenue']),
            'transactions': row['transactions'],
        }
        for row in part_rows
    )
    ranking.sort(key=lambda item: (-item['quantity'], -item['revenue'], item['name']))
    return ranking[:limit]


def _receita_orcamento_agrupada(user, periodo, trunc_function):
    gross_expression = _item_total_expression()
    rows = (
        _items_orcamento_periodo(user, periodo)
        .filter(orcamento__status__in=STATUS_RECEITA)
        .annotate(period=trunc_function('orcamento__data_criacao'))
        .values('period', 'orcamento_id', 'orcamento__desconto', 'orcamento__card_final_amount')
        .annotate(gross=Sum(gross_expression))
        .order_by('period')
    )

    return [
        {
            'period': row['period'],
            'amount': _valor_orcamento(row['gross'], row['orcamento__desconto'], row['orcamento__card_final_amount']),
        }
        for row in rows
    ]


def _valor_orcamento(gross, desconto, card_final_amount):
    if card_final_amount is not None:
        return money(card_final_amount)
    return max(money(gross) - money(desconto), ZERO)


def _items_orcamento_periodo(user, periodo):
    queryset = ItemsOrcamento.objects.filter(orcamento__usuario=user)
    if periodo.all_data:
        return queryset
    return queryset.filter(orcamento__data_criacao__date__range=(periodo.start, periodo.end))


def _normalizar_periodo_total(user, periodo):
    if not periodo.all_data:
        return periodo

    bounds = Orcamento.objects.filter(usuario=user).aggregate(
        start=Min('data_criacao'),
        end=Max('data_criacao'),
    )
    if not bounds['start'] or not bounds['end']:
        return PeriodoOrcamento('todas', 'Todo período', all_data=True)
    return PeriodoOrcamento(
        'todas',
        'Todo período',
        timezone.localtime(bounds['start']).date(),
        timezone.localtime(bounds['end']).date(),
    )


def _item_total_expression():
    return ExpressionWrapper(
        F('preco_orcamento') * F('quantidade'),
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


def _as_date(value):
    if isinstance(value, datetime):
        return timezone.localtime(value).date()
    return value
