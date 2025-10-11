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


