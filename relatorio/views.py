from django.shortcuts import render
from django.views.generic import TemplateView
# Create your views here.


class Relatorios(TemplateView):
    template_name = 'relatorio/pagina-inicial-relatorio.html'
