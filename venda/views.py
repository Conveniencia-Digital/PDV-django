from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import DetailView, ListView

from produto.models import Produto
from venda.forms import ItemsVendaForm, VendasForm, VendasItemsFormset
from venda.models import ItemsVenda, Vendas


class ListaVendas(ListView):
    template_name = 'vendas/pagina-inicial-vendas.html'
    model = Vendas

    def get_queryset(self):
        return Vendas.objects.filter(usuario=self.request.user)


@login_required
def cadastrarvendas(request):
    template_name = 'vendas/formularios/formulario-cadastrar-vendas.html'
    venda_instance = Vendas()

    form = VendasForm(request.POST or None, user=request.user, initial={
                      'usuario': request.user}, instance=venda_instance, prefix='main')
    formset = VendasItemsFormset(request.POST or None, instance=venda_instance,
                                 prefix='items', form_kwargs={'user': request.user})

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            template_name = 'vendas/tabela/linhas-tabela-vendas.html'
            vendas = form.save()
            items_venda = formset.save()

            context = {'object': vendas, 'items': items_venda}
            return render(request, template_name, context)

    context = {'form': form, 'formset': formset}
    return render(request, template_name, context)


@login_required
def buscarpreco(request):
    template_name = 'vendas/formularios/preco-produto.html'
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


@login_required
def addform(request):
    template_name = 'vendas/formularios/addform.html'
    form = ItemsVendaForm(user=request.user)
    context = {'itemsvendaform': form}
    return render(request, template_name, context)


@login_required
def apagaritemvenda(request, pk):
    item_orcamento = ItemsVenda.objects.get(pk=pk)
    if item_orcamento.usuario == request.user:
        item_orcamento.delete()
        return None
    else:
        raise PermissionError


class DetalheVendas(DetailView):
    template_name = 'vendas/detalhe-venda.html'
    model = Vendas

    def get_queryset(self):
        return Vendas.objects.filter(usuario=self.request.user)


@login_required
def editarvendas(request, pk):
    template_name = 'vendas/formularios/formulario-editar-vendas.html'
    venda_instance = Vendas.objects.get(pk=pk)

    form = VendasForm(request.POST or None, user=request.user, initial={
                      'usuario': request.user}, instance=venda_instance, prefix='main')
    formset = VendasItemsFormset(request.POST or None, form_kwargs={
                                 'user': request.user}, instance=venda_instance, prefix='items')

    if venda_instance.usuario != request.user:
        raise PermissionError

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():

            template_name = 'vendas/tabela/linhas-tabela-vendas.html'
            vendas = form.save()
            items_venda = formset.save()
            context = {'object': vendas, 'items': items_venda}
            return render(request, template_name, context)
        else:
            print(form.errors)
            print(formset.errors)

    context = {'object': venda_instance, 'form': form, 'formset': formset}
    return render(request, template_name, context)


def valor_total_vendas(request):
    template_name = 'vendas/relatorios/relatorio-venda.html'
    vendas = Vendas.objects.filter(usuario=request.user).count()
    valor_total = sum(venda.total() for venda in Vendas.objects.filter(usuario=request.user))
    context = {'vendas': vendas, 'valor_total': valor_total}
    return render(request, template_name, context)
