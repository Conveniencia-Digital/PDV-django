from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from relatorio.services import build_profitability_report


class Relatorios(LoginRequiredMixin, TemplateView):
    template_name = 'relatorio/pagina-inicial-relatorio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_profitability_report(self.request.user, self.request.GET))
        return context
