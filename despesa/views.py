from django.shortcuts import render
from django.views.generic import ListView
from despesa.models import Despesa
from despesa.forms import DespesaForms


class ListaDespesa(ListView):
    model = Despesa
    template_name = 'despesa/pagina-inicial-despesa.html'


def cadastrardespesa(request):
    template_name = 'despesa/formularios/formulario-cadastrar-despesa.html'
    form = DespesaForms(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            despesa = form.save()
            template_name = 'despesa/tabela/linhas-tabela-despesa.html'

            context = {'object': despesa}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)


def editardespesa(request, pk):
    template_name = 'despesa/formularios/formulario-editar-despesa.html'
    instance = Despesa.objects.get(pk=pk)
    form = DespesaForms(request.POST or None, instance=instance)

    if request.method == 'POST':
        if form.is_valid():
            despesa = form.save()
            template_name = 'despesa/tabela/linhas-tabela-despesa.html'
            context = {'object': despesa}

            return render(request, template_name, context)

    context = {'form': form, 'object': instance}
    return render(request, template_name, context)


def apagardespesa(request, pk):
    template_name = 'despesa/tabela/tabela-despesa.html'
    obj = Despesa.objects.get(pk=pk)
    obj.delete()
    return render(request, template_name)
