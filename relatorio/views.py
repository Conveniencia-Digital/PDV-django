from django.views.generic import TemplateView


class Relatorios(TemplateView):
    template_name = 'relatorio/pagina-inicial-relatorio.html'
