from django import template
from django.db.models.aggregates import Sum, Count
from orcamento.models import ItemsOrcamento, Orcamento

register = template.Library()


@register.simple_tag
def faturamento():
    s = Orcamento.objects.all().aggregate(som=Count('id'))
    s1 = ItemsOrcamento.objects.all()
    for i in s.values():
        s = i
    return s1
