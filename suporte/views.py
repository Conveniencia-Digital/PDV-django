from django.shortcuts import render
from django.views.generic import TemplateView

# Create your views here.

class Suporte(TemplateView):
    template_name = 'suporte/suporte.html'
    