from django.contrib.auth.decorators import login_required
from django.db.models.aggregates import Sum
from django.shortcuts import render
from django.views.generic import DetailView, ListView

from peca.forms import PecasForms
from peca.models import Pecas


class Peca(ListView):
    model = Pecas
    template_name = 'peca/pagina-inicial-pecas.html'

    def get_queryset(self):
        return Pecas.objects.filter(usuario=self.request.user)


@login_required
def cadastrarpeca(request):
    template_name = 'peca/formularios/formulario-cadastrar-peca.html'
    form = PecasForms(request.POST or None, initial={'usuario': request.user}, user=request.user)

    if request.method == 'POST':
        if form.is_valid():
            peca = form.save()
            template_name = 'peca/tabela/linhas-tabela-peca.html'
            context = {'object': peca}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)


@login_required
def editarpeca(request, pk):
    template_name = 'peca/formularios/formulario-editar-peca.html'
    instance = Pecas.objects.get(pk=pk)
    form = PecasForms(request.POST or None, instance=instance, initial={'usuario': request.user}, user=request.user)
    if instance.usuario != request.user:
        raise PermissionError

    if request.method == 'POST':
        if form.is_valid():
            peca = form.save()
            template_name = 'peca/tabela/linhas-tabela-peca.html'
            context = {'object': peca}
            return render(request, template_name, context)

    context = {'form': form, 'object': instance}
    return render(request, template_name, context)


@login_required
def apagarpeca(request, pk):
    template_name = 'peca/tabela/tabela-peca.html'
    objeto = Pecas.objects.get(pk=pk)
    if objeto.usuario == request.user:
        objeto.delete()
    else:

        raise PermissionError
    return render(request, template_name)


def relatoriopeca(request):
    template_name = 'peca/informacao-peca.html'
    preco_venda = Pecas.objects.filter(usuario=request.user).aggregate(preco_pecas=Sum('preco_peca'))
    preco_custo = Pecas.objects.filter(usuario=request.user).aggregate(preco_custo=Sum('preco_de_custo'))
    total = Pecas.objects.filter(usuario=request.user).count

    for i in preco_venda.values():
        preco_venda = i

    for c in preco_custo.values():
        preco_custo = c

    lucro = preco_venda - preco_custo

    context = {'preco_venda': preco_venda, 'preco_custo': preco_custo, 'lucro': lucro, 'total': total}
    return render(request, template_name, context)


class DetalhePeca(DetailView):
    model = Pecas
    template_name = 'peca/offcanvas/detalhe-peca.html'

    def get_queryset(self):
        return Pecas.objects.filter(usuario=self.request.user)
