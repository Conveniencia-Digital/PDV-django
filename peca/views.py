from django.shortcuts import render
from django.views.generic import ListView
from django.db.models.aggregates import Sum
from peca.models import Pecas
from peca.forms import PecasForms


class Peca(ListView):
    model = Pecas
    template_name = 'peca/pagina-inicial-pecas.html'


def cadastrarpeca(request):
    template_name = 'peca/formularios/formulario-cadastrar-peca.html'
    form = PecasForms(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            peca = form.save()
            template_name = 'peca/tabela/linhas-tabela-peca.html'
            context = {'object': peca}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)


def editarpeca(request, pk):
    template_name = 'peca/formularios/formulario-editar-peca.html'
    instance = Pecas.objects.get(pk=pk)
    form = PecasForms(request.POST or None, instance=instance)

    if request.method == 'POST':
        if form.is_valid():
            produto = form.save()
            template_name = 'peca/tabela/linhas-tabela-peca.html'

            context = {'object': produto}
            return render(request, template_name, context)

    context = {'form': form, 'object': instance}
    return render(request, template_name, context)


def apagarpeca(request, pk):
    template_name = 'peca/tabela/tabela-peca.html'
    objeto = Pecas.objects.get(pk=pk)
    objeto.delete()
    return render(request, template_name)


def relatoriopeca(request):
    template_name = 'peca/informacao-peca.html'
    preco_venda = Pecas.objects.all().aggregate(preco_pecas=Sum('preco_peca'))
    preco_custo = Pecas.objects.all().aggregate(preco_custo=Sum('preco_de_custo'))
    total = Pecas.objects.all().count

    for i in preco_venda.values():
        preco_venda = i
    
    for c in preco_custo.values():
        preco_custo = c

    lucro = preco_venda - preco_custo    

    context = {'preco_venda': preco_venda, 'preco_custo': preco_custo, 'lucro': lucro, 'total': total}
    return render(request, template_name, context)

