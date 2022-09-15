from django.shortcuts import render
from django.views.generic import ListView
from orcamento.models import Orcamento
from orcamento.forms import OrcamentoForms, OrcamentoItemsForms, ItemsOrcamentoFormset


class ListaOrcamento(ListView):
    template_name = 'orcamento/pagina-inicial-orcamento.html'
    model = Orcamento


def cadastrarorcamento(request):
    template_name = 'orcamento/formularios/formulario-cadastrar-orcamento.html'
    orcamento_instance = Orcamento()

    form = OrcamentoItemsForms(request.POST or None, instance=orcamento_instance)
    formset = ItemsOrcamentoFormset(request.POST or None, instance=orcamento_instance)

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
    form = OrcamentoItemsForms()
    context = {'orcamentoitemsform': form}
    return render(request, template_name, context)
