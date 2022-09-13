from django.shortcuts import render
from django.views.generic import TemplateView
# Create your views here.


class Configuracao(TemplateView):
    template_name = 'configuracao/pagina-inicial-configuracao.html'
