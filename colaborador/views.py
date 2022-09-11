from django.shortcuts import render
from django.views.generic import ListView

from colaborador.models import Colaborador
from colaborador.forms import ColaboradorForms


class ListaColaborador(ListView):
    model = Colaborador
    template_name = 'colaborador/pagina-inicial-colaborador.html'


def cadastrarcolaborador(request):
    template_name = 'colaborador/formularios/formulario-cadastrar-colaborador.html'
    form = ColaboradorForms(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            colaborador = form.save()
            template_name = 'colaborador/tabela/linhas-tabela-colaborador.html'

            context = {'object': colaborador}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)


def editarcolaborador(request, pk):
    template_name = 'colaborador/formularios/formulario-editar-colaborador.html'
    instance = Colaborador.objects.get(pk=pk)
    form = ColaboradorForms(request.POST or None, instance=instance)

    if request.method == 'POST':
        if form.is_valid():
            colaborador = form.save()
            template_name = 'colaborador/tabela/linhas-tabela-colaborador.html'
            context = {'object': colaborador}

            return render(request, template_name, context)

    context = {'form': form, 'object': instance}
    return render(request, template_name, context)


def apagarcolaborador(request, pk):
    template_name = 'colaborador/tabela/tabela-colaborador.html'
    obj = Colaborador.objects.get(pk=pk)
    obj.delete()
    return render(request, template_name)
