from django.shortcuts import render
from venda.forms import ItemsVendaForm, VendasItemsFormset
from django.views.generic import ListView
from produto.models import Produto
from venda.models import Vendas, ItemsVenda


class Sale(ListView):
    model = Vendas
    template_name = 'vendas/vendas.html'


def vendas(request):
    template_name = 'vendas/vendas-form.html'
    venda_instance = Vendas()

    form = ItemsVendaForm(request.POST or None, instance=venda_instance, prefix='main')
    formset = VendasItemsFormset(request.POST or None, instance=venda_instance, prefix='items')

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()

    context = {'form': form, 'formset': formset}
    return render(request, template_name, context)


def buscarpreco(request):
    template_name = 'vendas/preco-produto.html'
    url = request.get_full_path()
    print('url', url)
    print(url.split('-'))
    print('list', list(request.GET.values()))
    lista = list(request.GET.values())
    produto_pk = 0
    for i in lista:
        produto_pk = i
    produto = Produto.objects.get(pk=produto_pk)
    context = {'produto': produto}
    return render(request, template_name, context)


def addform(request):
    template_name = 'vendas/addform.html'
    form = ItemsVendaForm()
    context = {'itemsvendaform': form}
    return render(request, template_name, context)
