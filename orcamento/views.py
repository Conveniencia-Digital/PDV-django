from django.shortcuts import render, redirect
from django.views.generic import ListView
from orcamento.models import ItemsOrcamento
from orcamento.forms import ItemsOrcamentoForms, ItemsOrcamentoFormset


class ListaOrcamento(ListView):
    template_name = 'orcamento/pagina-inicial-orcamento.html'
    model = ItemsOrcamento


def cadastrarorcamento(request):
    template_name = 'orcamento/formularios/formulario-cadastrar-orcamento.html'
    #orcamento_instance = Orcamento()

    form = ItemsOrcamentoForms(request.POST or None)
    formset = ItemsOrcamentoFormset(request.POST or None)

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()

            return redirect('orcamento:orcamento')

    context = {'form': form, 'formset': formset}
    return render(request, template_name, context)


def adicionarlinhas(request):
    template_name = 'orcamento/formularios/linhas-formulario-orcamento.html'
    form = ItemsOrcamentoForms()
    context = {'items_orcamento_form': form}
    return render(request, template_name, context)
