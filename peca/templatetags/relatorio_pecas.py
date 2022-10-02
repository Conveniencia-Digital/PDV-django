from django import template
from django.db.models.aggregates import Sum, Count
from peca.models import Pecas

register = template.Library()


@register.simple_tag
def total_peca():
    i = 0
    total = Pecas.objects.all().aggregate(total=Sum('preco_peca'))
    for i in total.values():
        print(i)
    return i
