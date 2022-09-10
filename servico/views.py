from django.shortcuts import render
from django.views.generic import ListView

from servico.models import Servico
from servico.forms import ServicoForms


class ListaServicos(ListView):
    model = Servico
    template_name = 'servico/pagina-inicial-servico.html'


def cadastrarservico(request):
    template_name = 'servico/formularios/formulario-cadastrar-servico.html'
    form = ServicoForms(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            servico = form.save()
            template_name = 'servico/tabela/linhas-tabela-servico.html'

            context = {'object': servico}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)


def editarservico(request, pk):
    template_name = 'servico/formularios/formulario-editar-servico.html'
    instance = Servico.objects.get(pk=pk)
    form = ServicoForms(request.POST or None, instance=instance)

    if request.method == 'POST':
        if form.is_valid():
            servico = form.save()
            template_name = 'servico/tabela/linhas-tabela-servico.html'
            context = {'object': servico}

            return render(request, template_name, context)
    
    context = {'form': form, 'object': instance}
    return render(request, template_name, context)



def apagarservico(request, pk):
    template_name = 'servico/tabela/tabela-servico.html'
    obj = Servico.objects.get(pk=pk)
    obj.delete()
    return render(request, template_name)
