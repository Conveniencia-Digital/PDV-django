from django.shortcuts import render, redirect
from django.views.generic import ListView
from orcamento.models import Orcamento
from orcamento.forms import OrcamentoForms, OrcamentoItemsForms, ItemsOrcamentoFormset


class ListaOrcamento(ListView):
    template_name = 'orcamento/pagina-inicial-orcamento.html'
    model = Orcamento


def cadastrarorcamento(request):
    template_name = 'orcamento/formularios/formulario-cadastrar-orcamento.html'
    orcamento_instance = Orcamento()

    form = OrcamentoForms(request.POST or None, instance=orcamento_instance, prefix='main')
    formset = ItemsOrcamentoFormset(request.POST or None, instance=orcamento_instance, prefix='items')

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('orcamento:orcamento')

    context = {'form': form, 'formset': formset}
    return render(request, template_name, context)


def adicionarlinhas(request):
    template_name = 'orcamento/formularios/linhas-formulario-orcamento.html'
    form = OrcamentoItemsForms()
    context = {'orcamento_items_form': form}
    return render(request, template_name, context)
