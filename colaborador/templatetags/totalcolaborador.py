from django import template
from django.shortcuts import render
from django.db.models.aggregates import Count, Sum

from colaborador.models import Colaborador

register = template.Library()


@register.simple_tag
def total_colaborador():
    total = Colaborador.objects.all().count()
    if total == 0:
        return '0'
    return total 