from django.shortcuts import render
from django.views.generic import ListView
from orcamento.models import Orcamento
from orcamento.forms import OrcamentoForms


class ListaOrcamento(ListView):
    template_name = 'orcamento/pagina-inicial-orcamento.html'
    model = Orcamento


def cadastrarorcamento(request):
    template_name = 'orcamento/formularios/formulario-cadastrar-orcamento.html'
    form = OrcamentoForms(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            orcamento = form.save()
            template_name = 'orcamento/tabela/linhas-tabela-orcamento.html'

            context = {'object': orcamento}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)
