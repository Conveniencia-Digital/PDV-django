from django import template
from django.db.models.aggregates import Sum

from peca.models import Pecas

register = template.Library()


@register.simple_tag
def preco_venda(self):
    i = 0
    total = Pecas.objects.filter(usuario=self.request.user).aggregate(total=Sum('preco_peca'))
 
    for i in total.values():
        if i == None:
            return(0.00)
    return i


@register.simple_tag
def preco_custo(self):
    i = 0
    tot_custo = Pecas.objects.filter(usuario=self.request.user).aggregate(tot_custo=Sum('preco_de_custo'))
    for i in tot_custo.values():
        if i == None:
            return(0.00)
    return i


@register.simple_tag
def total_peca(self):
    tot = Pecas.objects.filter(usuario=self.request.user).count()
    if tot == None:
        return 0
    else:
        return tot
        
@register.simple_tag
def calculo():
    calc = preco_venda() - preco_custo()
    return calc 



