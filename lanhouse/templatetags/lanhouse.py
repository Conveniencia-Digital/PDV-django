from django import template

from lanhouse.models import LanhouseModel

register = template.Library()


@register.simple_tag
def valor_total(request):
    total_lanhouse = sum(valor.total() for valor in LanhouseModel.objects.filter(usuario=request.user))
    return total_lanhouse


@register.simple_tag
def qtd_lanhouse(request):
    qtd = LanhouseModel.objects.filter(usuario=request.user).count()
    return qtd
