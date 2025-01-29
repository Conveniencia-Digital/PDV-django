from django import template

from cliente.models import Cliente

register = template.Library()


@register.simple_tag
def total_clientes():
    total = Cliente.objects.all().count()
    if total == 0:
        return '0'
    return total     