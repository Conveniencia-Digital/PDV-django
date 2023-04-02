from django import template
from django.db.models.aggregates import Sum, Count
from orcamento.models import ItemsOrcamento, Orcamento

register = template.Library()


@register.simple_tag
def valor_total(request):
    total_orcamento = sum(valor.total() for valor in Orcamento.objects.filter(usuario=request.user))
    return total_orcamento



@register.simple_tag
def qtd_orcamento(request):
    qtd = Orcamento.objects.filter(usuario=request.user).count()
    return qtd
    
