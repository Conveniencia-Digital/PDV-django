from django import template
from django.db.models import Sum

from peca.models import Pecas

register = template.Library()


@register.simple_tag(takes_context=True)
def preco_venda(context):
    user = context['request'].user
    total = Pecas.objects.filter(usuario=user).aggregate(total=Sum('preco_peca'))['total']
    return total or 0.00


@register.simple_tag(takes_context=True)
def preco_custo(context):
    user = context['request'].user
    total = Pecas.objects.filter(usuario=user).aggregate(total=Sum('preco_de_custo'))['total']
    return total or 0.00


@register.simple_tag(takes_context=True)
def total_peca(context):
    user = context['request'].user
    return Pecas.objects.filter(usuario=user).count()


@register.simple_tag(takes_context=True)
def calculo(context):
    venda = preco_venda(context)
    custo = preco_custo(context)
    return venda - custo
