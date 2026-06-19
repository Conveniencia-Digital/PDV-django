from django import template
from peca.models import Pecas

register = template.Library()


def _dashboard_totals(user):
    preco_venda_total = 0
    preco_custo_total = 0
    for peca in Pecas.objects.filter(usuario=user).only('preco_peca', 'preco_de_custo', 'quantidade'):
        preco_venda_total += peca.vendatotal()
        preco_custo_total += peca.precototal()
    return preco_venda_total, preco_custo_total


@register.simple_tag
def preco_venda(self):
    preco_venda_total, _preco_custo_total = _dashboard_totals(self.request.user)
    return preco_venda_total


@register.simple_tag
def preco_custo(self):
    _preco_venda_total, preco_custo_total = _dashboard_totals(self.request.user)
    return preco_custo_total


@register.simple_tag
def total_peca(self):
    return Pecas.objects.filter(usuario=self.request.user).count()
        
@register.simple_tag
def calculo(self):
    preco_venda_total, preco_custo_total = _dashboard_totals(self.request.user)
    return preco_venda_total - preco_custo_total


