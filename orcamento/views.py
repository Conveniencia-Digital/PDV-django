from django.shortcuts import render
from django.views.generic import ListView
from orcamento.models import Orcamento
from orcamento.forms import OrcamentoForms, ItemsOrcamentoForms, ItemsOrcamentoFormset
from peca.models import Pecas


class ListaOrcamento(ListView):
    template_name = 'orcamento/pagina-inicial-orcamento.html'
    model = Orcamento


def cadastrarorcamento(request):
    template_name = 'orcamento/formularios/formulario-cadastrar-orcamento.html'
    orcamento_instance = Orcamento()

    form = OrcamentoForms(request.POST or None, instance=orcamento_instance, prefix='main')
    formset = ItemsOrcamentoFormset(request.POST or None, instance=orcamento_instance, prefix='items')

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            template_name = 'orcamento/tabela/linhas-tabela-orcamento.html'
            orcamento = form.save()
            items_orcamento = formset.save()
            context = {'object': orcamento, 'items': items_orcamento}
            return render(request, template_name, context)

    context = {'form': form, 'formset': formset}
    return render(request, template_name, context)


def adicionarlinhas(request):
    template_name = 'orcamento/formularios/linhas-formulario-orcamento.html'
    form = ItemsOrcamentoForms()
    context = {'items_orcamento_form': form}
    return render(request, template_name, context)


def preco_peca(request):
    template_name = 'orcamento/formularios/preco-peca.html'
    url = request.get_full_path()
    print('url', url)
    print(url.split('-'))
    print('list', list(request.GET.values()))
    lista = list(request.GET.values())
    peca_pk = 0
    for i in lista:
        peca_pk = i
    peca = Pecas.objects.get(pk=peca_pk)
    context = {'peca': peca}
    return render(request, template_name, context)
