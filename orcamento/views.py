from django.shortcuts import render
from django.views.generic import ListView
from orcamento.models import Orcamento
from orcamento.forms import OrcamentoForms, OrcamentoItemsForms


class ListaOrcamento(ListView):
    template_name = 'orcamento/pagina-inicial-orcamento.html'
    model = Orcamento


def cadastrarorcamento(request):
    template_name = 'orcamento/formularios/formulario-cadastrar-orcamento.html'
    orcamento_instance = Orcamento()
    form = OrcamentoForms(request.POST or None, instance=orcamento_instance)
    formset = OrcamentoItemsForms(request.POST or None, instance=orcamento_instance)

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            orcamento = form.save()
            formset.save()
            template_name = 'orcamento/tabela/linhas-tabela-orcamento.html'

            context = {'object': orcamento}
            return render(request, template_name, context)

    context = {'form': form, 'formset': formset}
    return render(request, template_name, context)


def adicionarlinhas(request):
    template_name = 'orcamento/formularios/linhas-formulario-orcamento.html'
    form = OrcamentoForms()
    context = {'itemsorcamento': form}
    return render(request, template_name, context)
