from django.shortcuts import render
from django.views.generic import ListView

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
