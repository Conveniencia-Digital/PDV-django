from django import template
from django.shortcuts import render

from venda.models import Vendas

register = template.Library()



@register.simple_tag
def total_vendas(request):#vendas = Vendas.objects.all()
    valor_total = sum(venda.total() for venda in Vendas.objects.filter(usuario=request.user))
    return valor_total



@register.simple_tag
def qtd_vendas(request):
    qtd_vendas = Vendas.objects.filter(usuario=request.user).count()
    return qtd_vendas


@register.simple_tag
def lucro_total_vendas(request):
    vendas = Vendas.objects.filter(usuario=request.user)
    total_lucro = sum(v.lucro_total() for v in vendas)
    return total_lucro


@register.simple_tag
def margem_lucro_total_vendas(request):
    vendas = Vendas.objects.filter(usuario=request.user)
    total_lucro_vendas = sum(p.lucro_total() for p in vendas)
    total_vendas = sum(p.total() for p in vendas)

    if total_vendas == 0:
        return 0
    
    margem_percentual_vendas = (total_lucro_vendas / total_vendas) * 100
    return round(margem_percentual_vendas, 2)
